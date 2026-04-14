"""
NestShift Safety Filter — Πsafe
Implements immutable hardware safety constraints.
NO AI agent or user command can bypass these rules.
These values are hardcoded intentionally.
"""

SAFETY_RULES = {
    "hvac_max_temp_c": 26.0,
    "hvac_min_temp_c": 16.0,
    "max_simultaneous_high_power": 3,
    "high_power_threshold_watts": 1000,
    "max_single_device_watts": 3000,
    "max_temp_delta_per_minute": 5.0, # Sensor coherence
}

class SafetyViolation(Exception):
    def __init__(self, rule: str, requested: any, limit: any, reason: str = ""):
        self.rule = rule
        self.requested = requested
        self.limit = limit
        self.reason = reason
        super().__init__(
            f"Safety violation [{rule}]: requested={requested}, limit={limit}. {reason}"
        )

def validate_sensor_reading(sensor_id: str, value: float, last_value: float, timestamp_delta_sec: float) -> bool:
    """
    Checks for 'impossible' sensor jumps (Coherence Check).
    """
    if last_value is None or timestamp_delta_sec <= 0:
        return True
    
    # Check for temperature spikes
    if "temp" in sensor_id.lower():
        delta = abs(value - last_value)
        rate_per_min = (delta / timestamp_delta_sec) * 60
        if rate_per_min > SAFETY_RULES["max_temp_delta_per_minute"]:
            return False
            
    return True

def validate_action(action: dict, system_state: dict) -> dict:
    """
    Validates and potentially modifies an action before execution.
    Returns the (possibly modified) safe action.
    """
    action_type = action.get("action")
    params = action.get("params", {})
    device_id = action.get("device_id")

    # Rule 1: HVAC temperature bounds
    if action_type == "set_temperature":
        requested_temp = float(params.get("temperature", 20))
        if requested_temp > SAFETY_RULES["hvac_max_temp_c"]:
            params["temperature"] = SAFETY_RULES["hvac_max_temp_c"]
            action["safety_clamped"] = True
            action["clamped_reason"] = "Exceeded max safe temperature"
        elif requested_temp < SAFETY_RULES["hvac_min_temp_c"]:
            params["temperature"] = SAFETY_RULES["hvac_min_temp_c"]
            action["safety_clamped"] = True
            action["clamped_reason"] = "Below min safe temperature"
        action["params"] = params

    # Rule 2: Critical Device Blocklist (Inhibitory Control)
    # Some devices should NEVER be turned on by the AI Brain alone (e.g. Ovens)
    critical_devices = ["oven", "stove", "power_tool"]
    device_type = system_state.get("devices", {}).get(device_id, {}).get("type", "")
    if action_type == "turn_on" and device_type in critical_devices:
        if action.get("source") == "brain":
            raise SafetyViolation("critical_device_inhibition", device_id, "OFF", "Brain cannot activate high-risk heating appliances.")

    # Rule 3: High power device limit
    if action_type == "turn_on":
        device_info = system_state.get("devices", {}).get(device_id, {})
        device_watts = device_info.get("estimated_watts", 0)
        
        active_high_power = sum(
            1 for d in system_state.get("devices", {}).values()
            if d.get("state") == "on" 
            and d.get("estimated_watts", 0) > SAFETY_RULES["high_power_threshold_watts"]
        )

        if device_watts > SAFETY_RULES["high_power_threshold_watts"] and active_high_power >= SAFETY_RULES["max_simultaneous_high_power"]:
             raise SafetyViolation("grid_overload_prevention", active_high_power + 1, SAFETY_RULES["max_simultaneous_high_power"], "Too many high-power devices.")

    return action
