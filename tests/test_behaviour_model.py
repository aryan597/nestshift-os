from datetime import datetime, timedelta

from conftest import load_service_module

automation_agent = load_service_module("automation-agent")
BehaviourModel = automation_agent.BehaviourModel
RuleEngine = automation_agent.RuleEngine


def test_cold_start_confidence_zero():
    bm = BehaviourModel()
    assert bm.get_pattern_confidence() == 0.0


def test_confidence_increases_with_events():
    bm = BehaviourModel()
    for i in range(100):
        bm.record_event("light_1", "turn_on", datetime.now())
    assert bm.get_pattern_confidence() > 0.0


def test_no_prediction_below_confidence_threshold():
    bm = BehaviourModel()
    result = bm.predict_next_action(9, {})
    assert result is None


def test_rule_engine_blocks_dangerous_hvac():
    re = RuleEngine()
    action = {"action": "set_temperature", "params": {"temperature": 40}}
    state = {"occupancy": False, "devices": {}}
    assert re.validate_action(action, state) is False
