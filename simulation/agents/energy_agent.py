"""Energy Agent for simulation.

Tariff-aware load scheduling with demand forecasting.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque


class DemandForecaster:
    """Simple time-series forecaster using exponential smoothing."""

    def __init__(self, horizon_steps: int = 48):
        self.horizon = horizon_steps
        self.history = deque(maxlen=336)  # 7 days of half-hours
        self.alpha = 0.3  # Smoothing factor
        self.level = None

    def update(self, consumption: float):
        self.history.append(consumption)
        if self.level is None:
            self.level = consumption
        else:
            self.level = self.alpha * consumption + (1 - self.alpha) * self.level

    def forecast(self, steps: int = 48) -> List[float]:
        if self.level is None:
            return [0.5] * steps

        if len(self.history) >= 48:
            recent = list(self.history)[-48:]
            pattern = np.array(recent)
            base = np.mean(pattern)
            if base > 0:
                pattern_ratio = pattern / base
            else:
                pattern_ratio = np.ones(48)

            forecast = []
            for i in range(steps):
                idx = i % 48
                forecast.append(self.level * pattern_ratio[idx])
            return forecast

        return [self.level] * steps


class LoadScheduler:
    """Schedules shiftable loads to minimize cost using lookahead."""

    def __init__(self):
        self.scheduled_tasks = {}  # device -> (start_step, end_step) in absolute steps
        self.daily_completed = set()  # Track which devices ran today

    def reset_daily(self):
        self.daily_completed.clear()

    def schedule_day_ahead(self, device, prices: List[float], day: int,
                           demand_events: List[str]) -> Optional[int]:
        """Find cheapest start time for device in the next 24h."""
        if device.name not in demand_events:
            return None

        if device.name in self.daily_completed:
            return None

        window_size = int(device.runtime_hours * 2)
        best_start = None
        best_cost = float('inf')

        for start in range(48 - window_size + 1):
            hour = start / 2
            if not device.is_available(int(hour)):
                continue

            window_cost = sum(prices[start:start + window_size])
            if window_cost < best_cost:
                best_cost = window_cost
                best_start = start

        if best_start is not None:
            abs_start = day * 48 + best_start
            abs_end = abs_start + window_size
            self.scheduled_tasks[device.name] = (abs_start, abs_end)

        return best_start

    def is_scheduled_to_run(self, device_name: str, step: int) -> bool:
        if device_name not in self.scheduled_tasks:
            return False
        start, end = self.scheduled_tasks[device_name]
        return start <= step < end

    def mark_completed(self, device_name: str):
        self.daily_completed.add(device_name)

    def check_and_update(self, step: int):
        """Clean up completed tasks and reset daily tracking."""
        step_of_day = step % 48
        if step_of_day == 0:
            self.reset_daily()
            # Remove old tasks
            to_remove = []
            for name, (start, end) in self.scheduled_tasks.items():
                if end <= step:
                    to_remove.append(name)
            for name in to_remove:
                del self.scheduled_tasks[name]


class EnergyAgent:
    """Energy optimization agent with predictive scheduling."""

    def __init__(self, comfort_bias: float = 0.5, risk_aversion: float = 0.1):
        self.forecaster = DemandForecaster()
        self.scheduler = LoadScheduler()
        self.comfort_bias = comfort_bias
        self.risk_aversion = risk_aversion
        self.total_cost = 0.0
        self.total_savings = 0.0
        self.forecast_errors = []
        self.hvac_preheat_triggered = 0
        self.day_ahead_scheduled = False

    def act(self, state: dict, prices: List[float]) -> Dict[str, any]:
        """Generate control actions for this step."""
        step = state["step"]
        step_of_day = state["step_of_day"]
        hour = state["hour"]
        occupied = state["occupied"]
        temperature = state["temperature"]
        target_temp = state["target_temp"]
        demand_events = state["demand_events"]
        devices = state["devices"]
        day = state["day"]

        actions = {}

        # Day-ahead scheduling at start of each day
        if step_of_day == 0:
            self.scheduler.check_and_update(step)
            self.day_ahead_scheduled = False

        if not self.day_ahead_scheduled and step_of_day < 2:
            for name, device in devices.items():
                if device.device_type.value == "shiftable":
                    self.scheduler.schedule_day_ahead(
                        device, prices, day, demand_events
                    )
            self.day_ahead_scheduled = True

        # HVAC: predictive control with price awareness
        temp_diff = target_temp - temperature
        hvac_needed = abs(temp_diff) > 0.3

        if hvac_needed:
            current_price = prices[step_of_day]
            price_percentile = sum(1 for p in prices if p < current_price) / len(prices)

            # Look ahead for price spikes
            future_prices = prices[step_of_day:min(step_of_day + 8, 48)]
            upcoming_peak = any(p > current_price * 1.3 for p in future_prices) if future_prices else False

            # Risk-aware: avoid scheduling during high volatility
            price_volatility = np.std(prices) if len(prices) > 1 else 0
            risk_penalty = self.risk_aversion * price_volatility

            if price_percentile < 0.20 and upcoming_peak and temp_diff > 0:
                # Cheap now, expensive soon, need heat -> pre-heat
                actions["hvac_on"] = True
                self.hvac_preheat_triggered += 1
            elif current_price + risk_penalty > np.percentile(prices, 80) and not occupied:
                # Expensive and unoccupied -> tolerate drift
                actions["hvac_on"] = False
            else:
                actions["hvac_on"] = temp_diff > 0
        else:
            actions["hvac_on"] = False

        # Execute scheduled shiftable loads
        for name, device in devices.items():
            if device.device_type.value == "shiftable":
                if self.scheduler.is_scheduled_to_run(name, step):
                    actions[name] = True
                elif name in demand_events and device.is_available(int(hour)):
                    # Fallback: run now if not scheduled but needed
                    if name not in self.scheduler.scheduled_tasks:
                        actions[name] = True

        # Background loads always on
        actions["fridge"] = True
        actions["standby"] = True

        # Lights based on occupancy and time
        if occupied and (hour < 8 or hour > 17):
            actions["lights"] = True
        else:
            actions["lights"] = False

        return actions

    def observe(self, state: dict, outcome: dict, prices: List[float]):
        """Observe outcome and update models."""
        energy = outcome["energy_kwh"]
        step_of_day = state["step_of_day"]
        current_price = prices[step_of_day]
        cost = energy * current_price

        self.total_cost += cost
        self.forecaster.update(energy)

        if len(self.forecaster.history) > 1:
            pred = self.forecaster.forecast(1)[0]
            error = abs(pred - energy)
            self.forecast_errors.append(error)

    def get_metrics(self) -> dict:
        mae = np.mean(self.forecast_errors) if self.forecast_errors else 0
        return {
            "total_cost": self.total_cost,
            "forecast_mae": mae,
            "preheat_events": self.hvac_preheat_triggered,
        }
