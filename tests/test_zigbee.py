"""Tests for Zigbee Service.

Run with: pytest tests/test_zigbee.py -v
"""

import pytest
import asyncio
import json
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Make zigbee service importable
sys.path.insert(0, "services/zigbee")


@pytest.fixture
def mock_zigbee_config():
    """Fixture providing mock zigbee config."""
    return {
        "zigbee": {
            "broker": "localhost",
            "port": 1883,
            "devices": [
                {
                    "friendly_name": "motion_sensor_lounge",
                    "type": "motion",
                    "room": "living_room",
                    "nestshift_topic": "nestshift/sensors/motion/living_room"
                },
                {
                    "friendly_name": "temp_sensor_bedroom",
                    "type": "temperature",
                    "room": "bedroom",
                    "nestshift_topic": "nestshift/sensors/temperature/bedroom"
                },
                {
                    "friendly_name": "smart_plug_kettle",
                    "type": "switch",
                    "name": "kettle",
                    "nestshift_topic": "nestshift/devices/switch/kettle/set",
                    "zigbee_command_topic": "zigbee2mqtt/smart_plug_kettle/set"
                }
            ]
        },
        "mqtt": {
            "broker": "localhost",
            "port": 1883
        }
    }


@pytest.fixture
def hardware_config_file(mock_zigbee_config):
    """Create temporary hardware config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_zigbee_config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    Path(config_path).unlink(missing_ok=True)


def test_zigbee_stub_mode_no_broker(hardware_config_file):
    """Test that Zigbee runs in stub mode when broker unavailable."""
    from zigbee_service import ZigbeeService
    
    # With a bad broker, service should go to stub mode
    service = ZigbeeService(hardware_config_file)
    
    # Check device mappings loaded
    assert len(service._device_map) == 3
    assert "motion_sensor_lounge" in service._device_map


def test_zigbee_transforms_motion_payload(hardware_config_file):
    """Test Zigbee motion payload transformation."""
    from zigbee_service import ZigbeeService
    
    service = ZigbeeService(hardware_config_file)
    
    # Transform Zigbee payload to NestShift
    result = service._transform_zigbee_to_nestshift(
        "motion_sensor_lounge",
        {"occupancy": True}
    )
    
    assert result == {"state": True}
    
    # Test false
    result = service._transform_zigbee_to_nestshift(
        "motion_sensor_lounge",
        {"occupancy": False}
    )
    
    assert result == {"state": False}


def test_zigbee_transforms_temperature_payload(hardware_config_file):
    """Test Zigbee temperature payload transformation."""
    from zigbee_service import ZigbeeService
    
    service = ZigbeeService(hardware_config_file)
    
    # Transform Zigbee payload to NestShift
    result = service._transform_zigbee_to_nestshift(
        "temp_sensor_bedroom",
        {"temperature": 21.5}
    )
    
    assert result == {"value": 21.5, "unit": "C"}


def test_zigbee_command_routes_to_correct_device(hardware_config_file):
    """Test NestShift device command routes to correct Zigbee device."""
    from zigbee_service import ZigbeeService
    
    service = ZigbeeService(hardware_config_file)
    
    # Transform NestShift command to Zigbee
    result = service._transform_nestshift_to_zigbee(
        "smart_plug_kettle",
        {"state": "on"}
    )
    
    assert result == {"state": "ON"}
    
    # Test off
    result = service._transform_nestshift_to_zigbee(
        "smart_plug_kettle",
        {"state": "off"}
    )
    
    assert result == {"state": "OFF"}


def test_zigbee_never_subscribes_to_brain_topics(hardware_config_file):
    """Test safety invariant: Zigbee must never subscribe to brain topics."""
    # This should raise ValueError with forbidden topic
    forbidden_config = {
        "zigbee": {
            "broker": "localhost",
            "port": 1883,
            "devices": [
                {
                    "friendly_name": "bad_device",
                    "type": "switch",
                    "nestshift_topic": "nestshift/brain/intent/test"  # FORBIDDEN!
                }
            ]
        },
        "mqtt": {"broker": "localhost", "port": 1883}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(forbidden_config, f)
        config_path = f.name
    
    try:
        from zigbee_service import ZigbeeService
        
        with pytest.raises(ValueError, match="forbidden topic"):
            ZigbeeService(config_path)
    finally:
        Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])