import importlib.util
import sys
from pathlib import Path

import pytest

SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"


def load_service_module(service: str, module: str = "main"):
    """Load a service module under a unique name.

    Several services expose a top-level ``main.py``; importing them by bare
    module name makes them shadow each other in ``sys.modules``.
    """
    qualified = f"{service.replace('-', '_')}_{module}"
    if qualified in sys.modules:
        return sys.modules[qualified]
    spec = importlib.util.spec_from_file_location(
        qualified, SERVICES_DIR / service / f"{module}.py"
    )
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = loaded
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture
def mock_system_state():
    return {
        "devices": {
            "light_1": {"state": "off", "estimated_watts": 10, "type": "light"},
            "hvac_1": {"state": "on", "estimated_watts": 800, "type": "hvac"},
        },
        "occupancy": False,
    }
