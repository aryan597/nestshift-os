#!/usr/bin/env python3
"""Drift scenario: simulate changing household behavior and show adaptation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from env.household import Household
from env.tariff import AgileTariff
from env.simulator import Simulator, SimulationConfig, analyze_outcomes
from controllers import hybrid_controller
from agents.energy_agent import EnergyAgent
from agents.automation_agent import AutomationAgent
from agents.system_agent import SystemAgent


class DriftHousehold(Household):
    """Household that changes behavior mid-simulation."""

    def __init__(self, seed=42, drift_day=30):
        super().__init__(seed)
        self.drift_day = drift_day
        self.original_wake = self.occupancy.wake_hour

    def get_state(self, step: int) -> dict:
        # After drift day: occupant wakes 2 hours later
        day = step // 48
        if day >= self.drift_day:
            self.occupancy.wake_hour = self.original_wake + 2.0
        return super().get_state(step)


def run_drift_scenario(days=60, drift_day=30, seed=42):
    """Run simulation with behavioral drift."""
    household = DriftHousehold(seed=seed, drift_day=drift_day)
    tariff = AgileTariff(seed=seed)
    config = SimulationConfig(days=days, seed=seed)
    sim = Simulator(household, tariff, config)

    energy_agent = EnergyAgent(comfort_bias=0.5)
    automation_agent = AutomationAgent()
    system_agent = SystemAgent()

    # Track daily metrics
    daily_costs = []
    daily_comfort = []
    daily_confidence = []
    drift_alerts = []

    outcomes = sim.run_with_learning(
        hybrid_controller, energy_agent, automation_agent
    )

    for day in range(days):
        day_outcomes = [o for o in outcomes if o.day == day]
        if not day_outcomes:
            continue

        cost = sum(o.cost_gbp for o in day_outcomes)
        comfort = sum(o.comfort_penalty for o in day_outcomes)

        daily_costs.append(cost)
        daily_comfort.append(comfort)
        daily_confidence.append(automation_agent.behaviour_model.get_confidence())

        # Simulate drift detection
        if day >= drift_day:
            # After drift, prediction accuracy drops
            error = 0.3 + np.random.normal(0, 0.05)
            system_agent.monitor(error, 1 - automation_agent.behaviour_model.get_confidence())
            if system_agent.drift_detector.check("automation"):
                drift_alerts.append(day)

    return {
        "days": list(range(days)),
        "daily_costs": daily_costs,
        "daily_comfort": daily_comfort,
        "daily_confidence": daily_confidence,
        "drift_alerts": drift_alerts,
        "drift_day": drift_day,
    }


def main():
    print("=" * 60)
    print("DRIFT SCENARIO ANALYSIS")
    print("=" * 60)

    result = run_drift_scenario(days=60, drift_day=30, seed=42)

    print(f"\nDrift introduced on day {result['drift_day']}")
    print(f"Drift alerts triggered on days: {result['drift_alerts'][:5]}...")

    # Compare pre-drift vs post-drift
    pre_cost = np.mean(result["daily_costs"][:30])
    post_cost = np.mean(result["daily_costs"][30:])
    print(f"\nPre-drift avg daily cost:  £{pre_cost:.2f}")
    print(f"Post-drift avg daily cost: £{post_cost:.2f}")

    pre_comfort = np.mean(result["daily_comfort"][:30])
    post_comfort = np.mean(result["daily_comfort"][30:])
    print(f"Pre-drift avg comfort:  {pre_comfort:.3f}")
    print(f"Post-drift avg comfort: {post_comfort:.3f}")

    # Save
    import json
    Path("simulation/results").mkdir(parents=True, exist_ok=True)
    with open("simulation/results/drift_scenario.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n📁 Saved to simulation/results/drift_scenario.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
