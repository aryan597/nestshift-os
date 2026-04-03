import sys

sys.path.insert(0, "services/system-agent")
from main import DriftDetector


def test_no_drift_below_threshold():
    dd = DriftDetector()
    for _ in range(100):
        dd.record_prediction_error("energy", 0.10)
    assert dd.check_drift("energy") is False


def test_drift_detected_above_threshold():
    dd = DriftDetector()
    for _ in range(100):
        dd.record_prediction_error("energy", 0.20)
    assert dd.check_drift("energy") is True


def test_empty_agent_no_drift():
    dd = DriftDetector()
    assert dd.check_drift("energy") is False


def test_separate_agent_windows():
    dd = DriftDetector()
    for _ in range(100):
        dd.record_prediction_error("energy", 0.20)
    for _ in range(100):
        dd.record_prediction_error("automation", 0.10)
    assert dd.check_drift("energy") is True
    assert dd.check_drift("automation") is False
