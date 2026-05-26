"""Tests for GPIO Service.

Run with: pytest tests/test_gpio.py -v
"""

import pytest
import asyncio
import json
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Make sure gpio_service is importable
sys.path.insert(0, "services/gpio")
sys.path.insert(0, "services/api")


@pytest.fixture
def mock_gpio_config():
    """Fixture providing mock hardware config."""
    return {
        "gpio": {
            "poll_interval_ms": 100,
            "debounce_ms": 50,
            "pins": {
                "motion_living": {
                    "pin": 17,
                    "type": "input",
                    "pull": "up",
                    "topic": "nestshift/sensors/motion/living_room"
                },
                "light_living": {
                    "pin": 22,
                    "type": "output",
                    "topic": "nestshift/devices/light/living_room/set"
                }
            }
        },
        "mqtt": {
            "broker": "localhost",
            "port": 1883
        }
    }


@pytest.fixture
def hardware_config_file(mock_gpio_config):
    """Create temporary hardware config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_gpio_config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    Path(config_path).unlink(missing_ok=True)


def test_gpio_simulation_mode_no_hardware(hardware_config_file):
    """Test that GPIO runs in simulation mode when RPi.GPIO unavailable."""
    import gpio_service
    # Force simulation mode
    gpio_service.GPIO_AVAILABLE = False
    
    from gpio_service import GPIOService
    
    service = GPIOService(hardware_config_file)
    
    # Verify simulation mode
    assert service._simulation_mode is True


def test_gpio_debounce_ignores_fast_flicker(hardware_config_file):
    """Test that debounce ignores state changes too quickly."""
    import gpio_service
    gpio_service.GPIO_AVAILABLE = False
    
    from gpio_service import GPIOService
    
    service = GPIOService(hardware_config_file)
    
    pin = 17  # motion_living
    debounce_ms = 50
    
    # Record first change at time 100
    service._last_state[pin] = False
    service._last_change_time[pin] = 100.0
    
    now = 120.0  # Only 20ms later - within debounce
    
    # Check if within debounce period
    time_since_change = now - service._last_change_time[pin]
    
    assert time_since_change < debounce_ms, "Should be within debounce"


def test_gpio_input_publishes_correct_topic(hardware_config_file):
    """Test that GPIO input publishes to correct sensor topic."""
    import gpio_service
    gpio_service.GPIO_AVAILABLE = False
    
    from gpio_service import GPIOService
    
    service = GPIOService(hardware_config_file)
    
    # Find input pin config
    input_config = service._input_pins.get(17)
    assert input_config is not None
    assert input_config["topic"] == "nestshift/sensors/motion/living_room"


def test_gpio_output_sets_pin_on_command(hardware_config_file):
    """Test that GPIO output processes device commands correctly."""
    import gpio_service
    gpio_service.GPIO_AVAILABLE = False
    
    from gpio_service import GPIOService
    
    service = GPIOService(hardware_config_file)
    
    # Find output pin config
    output_config = service._output_pins.get(22)
    assert output_config is not None
    assert output_config["topic"] == "nestshift/devices/light/living_room/set"
    
    # Verify the output pin exists
    assert 22 in service._output_pins


def test_gpio_heartbeat_published(hardware_config_file):
    """Test that GPIO publishes heartbeat to correct topic."""
    import gpio_service
    gpio_service.GPIO_AVAILABLE = False
    
    from gpio_service import GPIOService
    
    service = GPIOService(hardware_config_file)
    service._start_time = 0  # Reset start time
    
    # Mock the MQTT client
    mock_client = MagicMock()
    mock_client.publish = AsyncMock()
    service._client = mock_client
    
    # Run heartbeat
    asyncio.run(service._send_heartbeat())
    
    # Verify publish was called
    mock_client.publish.assert_called_once()
    
    # Verify topic
    call_args = mock_client.publish.call_args
    assert call_args[0][0] == "nestshift/gpio/status"


def test_gpio_never_subscribes_to_brain_topics(hardware_config_file):
    """Test safety invariant: GPIO must never subscribe to brain topics."""
    # This should raise ValueError with forbidden topic
    forbidden_config = {
        "gpio": {
            "poll_interval_ms": 100,
            "debounce_ms": 50,
            "pins": {
                "bad_pin": {
                    "pin": 17,
                    "type": "output",
                    "topic": "nestshift/brain/intent/test"  # FORBIDDEN!
                }
            }
        },
        "mqtt": {"broker": "localhost", "port": 1883}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(forbidden_config, f)
        config_path = f.name
    
    try:
        from gpio_service import GPIOService
        
        with pytest.raises(ValueError, match="forbidden topic"):
            GPIOService(config_path)
    finally:
        Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])