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
}


class SafetyViolation(Exception):
    def __init__(self, rule: str, requested: any, limit: any):
        self.rule = rule
        self.requested = requested
        self.limit = limit
        super().__init__(
            f"Safety violation [{rule}]: requested={requested}, limit={limit}"
        )


def validate_action(action: dict, system_state: dict) -> dict:
    """
    Validates and potentially modifies an action before execution.
    Returns the (possibly modified) safe action.
    Raises SafetyViolation if action cannot be made safe.
    """
    action_type = action.get("action")
    params = action.get("params", {})

    # Rule 1: HVAC temperature bounds
    if action_type == "set_temperature":
        requested_temp = float(params.get("temperature", 20))
        if requested_temp > SAFETY_RULES["hvac_max_temp_c"]:
            # Clamp rather than reject
            params["temperature"] = SAFETY_RULES["hvac_max_temp_c"]
            action["params"] = params
            action["safety_clamped"] = True
        if requested_temp < SAFETY_RULES["hvac_min_temp_c"]:
            params["temperature"] = SAFETY_RULES["hvac_min_temp_c"]
            action["params"] = params
            action["safety_clamped"] = True

    # Rule 2: Never exceed max device wattage
    if action_type == "turn_on":
        device_watts = (
            system_state.get("devices", {})
            .get(action.get("device_id"), {})
            .get("estimated_watts", 0)
        )
        if device_watts > SAFETY_RULES["max_single_device_watts"]:
            raise SafetyViolation(
                "max_device_watts",
                device_watts,
                SAFETY_RULES["max_single_device_watts"],
            )

    # Rule 3: High power device limit
    if action_type == "turn_on":
        active_high_power = sum(
            1
            for d in system_state.get("devices", {}).values()
            if d.get("state") == "on"
            and d.get("estimated_watts", 0) > SAFETY_RULES["high_power_threshold_watts"]
        )
        device_watts = (
            system_state.get("devices", {})
            .get(action.get("device_id"), {})
            .get("estimated_watts", 0)
        )
        if (
            device_watts > SAFETY_RULES["high_power_threshold_watts"]
            and active_high_power >= SAFETY_RULES["max_simultaneous_high_power"]
        ):
            raise SafetyViolation(
                "max_simultaneous_high_power",
                active_high_power + 1,
                SAFETY_RULES["max_simultaneous_high_power"],
            )

    return action
