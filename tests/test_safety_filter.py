"""Tests for the safety filter — these must always pass."""

import pytest
import sys

sys.path.insert(0, "services/api")
from safety_filter import validate_action, SafetyViolation, SAFETY_RULES


def make_state(devices=None):
    return {"devices": devices or {}}


def test_hvac_clamps_above_max():
    action = {"action": "set_temperature", "params": {"temperature": 35}}
    result = validate_action(action, make_state())
    assert result["params"]["temperature"] == SAFETY_RULES["hvac_max_temp_c"]
    assert result["safety_clamped"] is True


def test_hvac_clamps_below_min():
    action = {"action": "set_temperature", "params": {"temperature": 5}}
    result = validate_action(action, make_state())
    assert result["params"]["temperature"] == SAFETY_RULES["hvac_min_temp_c"]


def test_hvac_passes_valid_temp():
    action = {"action": "set_temperature", "params": {"temperature": 21}}
    result = validate_action(action, make_state())
    assert result["params"]["temperature"] == 21
    assert "safety_clamped" not in result


def test_exceeds_max_wattage_raises():
    state = make_state({"dev1": {"estimated_watts": 5000, "state": "off"}})
    action = {"action": "turn_on", "device_id": "dev1"}
    with pytest.raises(SafetyViolation) as exc:
        validate_action(action, state)
    assert exc.value.rule == "max_device_watts"


def test_high_power_limit():
    devices = {f"dev{i}": {"estimated_watts": 1500, "state": "on"} for i in range(3)}
    devices["dev_new"] = {"estimated_watts": 1500, "state": "off"}
    state = make_state(devices)
    action = {"action": "turn_on", "device_id": "dev_new"}
    with pytest.raises(SafetyViolation) as exc:
        validate_action(action, state)
    assert exc.value.rule == "max_simultaneous_high_power"


def test_normal_device_turn_on_passes():
    state = make_state({"dev1": {"estimated_watts": 10, "state": "off"}})
    action = {"action": "turn_on", "device_id": "dev1"}
    result = validate_action(action, state)
    assert result["action"] == "turn_on"
