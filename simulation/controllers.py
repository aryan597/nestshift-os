"""Control policies / baselines for comparison.
"""

import numpy as np
from typing import Dict, List


def no_optimization_controller(state: dict, prices: List[float], *args) -> dict:
    """Naive baseline: run everything immediately when needed."""
    hour = state["hour"]
    occupied = state["occupied"]
    demand_events = state["demand_events"]
    devices = state["devices"]

    actions = {}

    # HVAC: always maintain target tightly
    temp = state["temperature"]
    target = state["target_temp"]
    actions["hvac_on"] = abs(target - temp) > 0.3

    # Shiftable loads: run immediately if needed
    for name, device in devices.items():
        if device.device_type.value == "shiftable":
            actions[name] = name in demand_events and device.is_available(int(hour))

    # Background
    actions["fridge"] = True
    actions["standby"] = True

    # Lights
    actions["lights"] = occupied and (hour < 8 or hour > 17)

    return actions


def rule_based_controller(state: dict, prices: List[float], *args) -> dict:
    """Static rule-based HEMS baseline.
    
    Simple static rules with no price forecasting:
    - No EV charging 4pm-8pm
    - No washer/dishwasher during peak hours (5-8pm)
    - HVAC deferred when unoccupied (wider tolerance)
    """
    hour = state["hour"]
    occupied = state["occupied"]
    demand_events = state["demand_events"]
    devices = state["devices"]

    actions = {}

    # HVAC: maintain temp, but allow more drift when unoccupied
    temp = state["temperature"]
    target = state["target_temp"]
    if occupied:
        actions["hvac_on"] = abs(target - temp) > 0.5
    else:
        actions["hvac_on"] = abs(target - temp) > 2.0

    # Shiftable loads: avoid peak hours (static, no price awareness)
    peak_hours = [17, 18, 19, 20]  # 5-8pm
    is_peak = int(hour) in peak_hours

    for name, device in devices.items():
        if device.device_type.value == "shiftable":
            if name in demand_events:
                if is_peak:
                    actions[name] = False  # Defer
                else:
                    actions[name] = device.is_available(int(hour))
            else:
                actions[name] = False

    actions["fridge"] = True
    actions["standby"] = True
    actions["lights"] = occupied and (hour < 8 or hour > 17)

    return actions


def proposed_controller(state: dict, prices: List[float],
                        energy_agent=None, automation_agent=None) -> dict:
    """Proposed multi-agent controller."""
    if energy_agent:
        return energy_agent.act(state, prices)
    return rule_based_controller(state, prices)


def hybrid_controller(state: dict, prices: List[float],
                      energy_agent=None, automation_agent=None) -> dict:
    """Hybrid: energy agent + automation agent with rule fusion."""
    # Start with energy agent decision
    if energy_agent:
        actions = energy_agent.act(state, prices)
    else:
        actions = rule_based_controller(state, prices)

    # Override with automation if confident
    if automation_agent:
        auto_action = automation_agent.act(state)
        if auto_action and auto_action.get("confidence", 0) > 0.75:
            device = auto_action["device"]
            action_type = auto_action["action"]
            if action_type in ["turn_on", "start"]:
                actions[device] = True
            elif action_type in ["turn_off", "stop"]:
                actions[device] = False

    return actions
