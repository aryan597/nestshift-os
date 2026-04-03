import pytest


@pytest.fixture
def mock_system_state():
    return {
        "devices": {
            "light_1": {"state": "off", "estimated_watts": 10, "type": "light"},
            "hvac_1": {"state": "on", "estimated_watts": 800, "type": "hvac"},
        },
        "occupancy": False,
    }
