"""Zigbee Service for NestShift OS.

Bridges Zigbee2MQTT ↔ NestShift topic schema.
Transforms Zigbee payloads to NestShift format and vice versa.
Graceful degradation to stub mode when broker unavailable.
"""

import asyncio
import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiomqtt


# Default configuration
DEFAULT_MQTT_HOST = "localhost"
DEFAULT_MQTT_PORT = 1883
DEFAULT_HEARTBEAT_SEC = 10.0

# Forbidden topics that Zigbee must never subscribe to
FORBIDDEN_TOPICS = ["nestshift/brain/", "nestshift/agents/"]

# Topic schemas
ZIGBEE_SENSOR_TOPIC_RE = re.compile(r"zigbee2mqtt/([^/]+)")
NESTSHIFT_SENSORS_TOPIC = "nestshift/sensors/{type}/{location}"
NESTSHIFT_DEVICES_TOPIC = "nestshift/devices/{type}/{name}/set"


class ZigbeeService:
    """Zigbee to NestShift MQTT bridge."""
    
    def __init__(self, config_path: str = "config/hardware_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Service state
        self._running = False
        self._client: Optional[aiomqtt.Client] = None
        self._stub_mode = False
        
        # Zigbee to NestShift device mappings
        self._device_map: dict[str, dict] = {}
        self._reverse_map: dict[str, str] = {}  # nestshift_topic -> zigbee topic
        
        # Simulation for stub mode
        self._simulation_task: Optional[asyncio.Task] = None
        
        # Heartbeat
        self._start_time = time.time()
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # MQTT
        self.mqtt_host = self.config.get("mqtt", {}).get("broker", DEFAULT_MQTT_HOST)
        self.mqtt_port = self.config.get("mqtt", {}).get("port", DEFAULT_MQTT_PORT)
        
        # Assert safety invariant
        self._assert_safety_invariant()
        
        # Load device mappings
        self._load_device_mappings()
    
    def _load_config(self) -> dict:
        """Load hardware configuration from YAML."""
        config = {"zigbee": {}, "mqtt": {}}
        
        if Path(self.config_path).exists():
            try:
                import yaml
                with open(self.config_path) as f:
                    loaded = yaml.safe_load(f)
                    if loaded:
                        config.update(loaded)
            except ImportError:
                print("⚠️ PyYAML not installed, using defaults")
        
        return config
    
    def _assert_safety_invariant(self):
        """Assert that Zigbee config never references forbidden topics."""
        # Check device mappings don't point to forbidden topics
        for device in self.config.get("zigbee", {}).get("devices", []):
            topic = device.get("nestshift_topic", "")
            for forbidden in FORBIDDEN_TOPICS:
                if forbidden in topic:
                    raise ValueError(
                        f"Safety violation: Zigbee device '{device.get('friendly_name')}' "
                        f"references forbidden topic '{topic}'. "
                        f"Zigbee must never subscribe to {FORBIDDEN_TOPICS}"
                    )
    
    def _load_device_mappings(self):
        """Load Zigbee device mappings from config."""
        devices = self.config.get("zigbee", {}).get("devices", [])
        
        for device in devices:
            friendly_name = device["friendly_name"]
            device_type = device["type"]
            nestshift_topic = device["nestshift_topic"]
            
            self._device_map[friendly_name] = {
                "type": device_type,
                "room": device.get("room"),
                "location": device.get("location"),
                "name": device.get("name"),
                "nestshift_topic": nestshift_topic,
                "zigbee_command_topic": device.get("zigbee_command_topic"),
            }
            
            # Build reverse map
            self._reverse_map[nestshift_topic] = friendly_name
            
            print(f"   Mapped {friendly_name} ({device_type}) -> {nestshift_topic}")
    
    def _transform_zigbee_to_nestshift(self, friendly_name: str, 
                                       payload: dict) -> dict:
        """Transform Zigbee2MQTT payload to NestShift sensor format."""
        device = self._device_map.get(friendly_name, {})
        device_type = device.get("type", "unknown")
        
        if device_type == "motion":
            # {"occupancy": true/false} -> {"state": true/false}
            return {"state": payload.get("occupancy", False)}
        
        elif device_type == "temperature":
            # {"temperature": 21.5} -> {"value": 21.5, "unit": "C"}
            return {
                "value": payload.get("temperature", 0),
                "unit": "C"
            }
        
        elif device_type == "door":
            # {"contact": true/false} -> {"state": "open"/"closed"}
            contact = payload.get("contact", True)
            return {"state": "open" if contact else "closed"}
        
        elif device_type == "switch":
            # {"state": "ON"/"OFF"} -> handled differently for sensors
            return {"state": payload.get("state", "OFF").lower()}
        
        return payload
    
    def _transform_nestshift_to_zigbee(self, friendly_name: str,
                                       payload: dict) -> dict:
        """Transform NestShift device command to Zigbee2MQTT format."""
        device = self._device_map.get(friendly_name, {})
        device_type = device.get("type", "unknown")
        
        command = {}
        
        if device_type == "switch":
            # {"state": "on"/"off"} -> {"state": "ON"/"OFF"}
            state = payload.get("state", "off")
            command["state"] = "ON" if state == "on" else "OFF"
            
        elif device_type == "light":
            # {"state": "on"/"off", "brightness": 0-255} -> {"state": "ON/OFF", "brightness": 0-255}
            state = payload.get("state", "off")
            command["state"] = "ON" if state == "on" else "OFF"
            if "brightness" in payload:
                command["brightness"] = payload["brightness"]
        
        return command
    
    async def start(self):
        """Start Zigbee service - connect to MQTT and bridge."""
        self._running = True
        self._start_time = time.time()
        
        print(f"📡 Zigbee Service starting on {self.mqtt_host}:{self.mqtt_port}")
        
        try:
            async with aiomqtt.Client(self.mqtt_host, self.mqtt_port) as client:
                self._client = client
                
                # Subscribe to Zigbee2MQTT topics
                await client.subscribe("zigbee2mqtt/#")
                
                # Subscribe to NestShift device commands
                for nestshift_topic in self._reverse_map.keys():
                    if nestshift_topic.startswith("nestshift/devices/"):
                        await client.subscribe(nestshift_topic)
                        print(f"   Subscribed: {nestshift_topic}")
                
                # Start heartbeat
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                # Start processing messages
                await self._process_messages()
                
        except aiomqtt.MQTTConnectError:
            print("⚠️ Cannot connect to MQTT broker - running in stub mode")
            await self._run_stub_mode()
        except Exception as e:
            print(f"❌ Zigbee Service error: {e}")
        finally:
            self._running = False
            self.stop()
    
    async def _run_stub_mode(self):
        """Run in stub mode - generate simulated sensor events."""
        self._stub_mode = True
        print("🎲 Zigbee stub mode - generating simulated sensor events")
        
        self._running = True
        self._start_time = time.time()
        
        # Send heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Start simulation loop
        self._simulation_task = asyncio.create_task(self._simulation_loop())
        
        # Wait until stopped
        while self._running:
            await asyncio.sleep(0.5)
    
    async def _simulation_loop(self):
        """Generate realistic simulated Zigbee sensor events."""
        import random
        
        print("📡 Generating simulated sensor events...")
        
        while self._running:
            try:
                # Pick a random device
                if self._device_map:
                    friendly_name = random.choice(list(self._device_map.keys()))
                    device = self._device_map[friendly_name]
                    device_type = device.get("type")
                    
                    # Generate realistic payload
                    if device_type == "motion":
                        # Motion in morning/evening more likely
                        hour = datetime.now().hour
                        if 6 <= hour <= 9 or 18 <= hour <= 22:
                            # Higher chance of motion
                            state = random.choice([True, True, False])
                        else:
                            state = random.choice([True, False, False, False])
                        payload = {"occupancy": state}
                        
                    elif device_type == "temperature":
                        # Temperature drifts 18-23C through the day
                        base_temp = 20.0
                        hour = datetime.now().hour
                        # Cold at night, warm in day
                        offset = (hour - 6) * 0.3 if 6 <= hour <= 20 else -5
                        temp = base_temp + offset + random.uniform(-0.5, 0.5)
                        payload = {"temperature": round(temp, 1)}
                        
                    elif device_type == "door":
                        # Door mostly closed
                        state = random.choice([False, False, False, True])
                        payload = {"contact": state}
                        
                    else:
                        payload = {}
                    
                    # Transform and publish
                    nestshift_payload = self._transform_zigbee_to_nestshift(
                        friendly_name, payload
                    )
                    nestshift_topic = device["nestshift_topic"]
                    
                    if self._client:
                        await self._client.publish(
                            nestshift_topic, 
                            json.dumps(nestshift_payload)
                        )
                        print(f"🎲 Stub {friendly_name} -> {nestshift_topic}: {nestshift_payload}")
                
                # Random interval 15-45 seconds
                await asyncio.sleep(random.uniform(15, 45))
                
            except Exception as e:
                print(f"⚠️ Stub simulation error: {e}")
    
    async def _process_messages(self):
        """Process incoming MQTT messages."""
        async for message in self._client.messages:
            topic = message.topic.value
            
            try:
                payload = json.loads(message.payload.decode())
            except json.JSONDecodeError:
                continue
            
            # Route to appropriate handler
            if topic.startswith("zigbee2mqtt/"):
                await self._handle_zigbee_message(topic, payload)
            elif topic.startswith("nestshift/devices/"):
                await self._handle_nestshift_command(topic, payload)
    
    async def _handle_zigbee_message(self, topic: str, payload: dict):
        """Handle incoming Zigbee2MQTT message - transform to NestShift."""
        # Extract friendly name
        match = ZIGBEE_SENSOR_TOPIC_RE.match(topic)
        if not match:
            return
        
        friendly_name = match.group(1)
        
        # Check if we have this device mapped
        if friendly_name not in self._device_map:
            return
        
        # Transform to NestShift format
        nestshift_payload = self._transform_zigbee_to_nestshift(
            friendly_name, payload
        )
        nestshift_topic = self._device_map[friendly_name]["nestshift_topic"]
        
        # Publish to NestShift
        if self._client:
            await self._client.publish(nestshift_topic, json.dumps(nestshift_payload))
            print(f"📡 {friendly_name} -> {nestshift_topic}: {nestshift_payload}")
    
    async def _handle_nestshift_command(self, topic: str, payload: dict):
        """Handle NestShift device command - transform to Zigbee and forward."""
        # Find matching Zigbee device
        for friendly_name, device in self._device_map.items():
            if device["nestshift_topic"] == topic:
                zigbee_topic = device.get("zigbee_command_topic")
                if not zigbee_topic:
                    continue
                
                # Transform to Zigbee format
                zigbee_payload = self._transform_nestshift_to_zigbee(
                    friendly_name, payload
                )
                
                # Publish to Zigbee2MQTT
                if self._client:
                    await self._client.publish(
                        zigbee_topic, json.dumps(zigbee_payload)
                    )
                    print(f"📡 {topic} -> {friendly_name}: {zigbee_payload}")
                
                break
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat with Zigbee status."""
        while self._running:
            await asyncio.sleep(DEFAULT_HEARTBEAT_SEC)
            if self._running:
                await self._send_heartbeat()
    
    async def _send_heartbeat(self):
        """Publish heartbeat status."""
        if self._client is None and not self._stub_mode:
            return
        
        heartbeat = {
            "stub_mode": self._stub_mode,
            "devices_mapped": len(self._device_map),
            "uptime_seconds": int(time.time() - self._start_time),
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            if self._client:
                await self._client.publish(
                    "nestshift/zigbee/status", json.dumps(heartbeat)
                )
        except Exception as e:
            print(f"❌ Heartbeat failed: {e}")
    
    def stop(self):
        """Stop Zigbee service."""
        self._running = False
        print("📡 Zigbee Service stopped")


async def main():
    """Main entry point."""
    config_path = os.getenv("HARDWARE_CONFIG", "config/hardware_config.yaml")
    service = ZigbeeService(config_path)
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())