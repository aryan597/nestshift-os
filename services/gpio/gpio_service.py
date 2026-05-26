"""GPIO Service for NestShift OS.

Polls input pins, debounces state changes, publishes to sensor topics.
Subscribes to device command topics, executes GPIO writes.
Graceful degradation with Mock GPIO when RPi.GPIO unavailable.
"""

import asyncio
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiomqtt

# Try to import RPi.GPIO, fall back to mock if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    # Create mock GPIO module
    class MockGPIO:
        BCM = "BCM"
        BOARD = "BOARD"
        IN = "IN"
        OUT = "OUT"
        PUD_DOWN = "PUD_DOWN"
        PUD_UP = "PUD_UP"
        
        _pins = {}
        _modes = {}
        _callbacks = {}
        
        @classmethod
        def setmode(cls, mode):
            cls._modes["mode"] = mode
            
        @classmethod
        def setup(cls, pin, direction, pull_up_down=None, callback=None):
            cls._pins[pin] = {"direction": direction, "state": False}
            if callback:
                cls._callbacks[pin] = callback
                
        @classmethod
        def input(cls, pin):
            return cls._pins.get(pin, {}).get("state", False)
            
        @classmethod
        def output(cls, pin, value):
            cls._pins[pin]["state"] = value
            
        @classmethod
        def add_event_detect(cls, pin, edge, callback=None, bouncetime=0):
            cls._callbacks[pin] = callback
            
        @classmethod
        def cleanup(cls):
            cls._pins.clear()
            cls._callbacks.clear()
            
        @classmethod
        def set_pin_state(cls, pin, value):
            """For simulation mode testing."""
            cls._pins[pin]["state"] = value
            
        @classmethod
        def get_pin_state(cls, pin):
            return cls._pins.get(pin, {}).get("state", False)
    
    sys.modules['RPi'] = type(sys)('RPi')
    sys.modules['RPi.GPIO'] = MockGPIO()
    import RPi.GPIO as GPIO
    SIMULATION_MODE = True


# Default configuration
DEFAULT_MQTT_HOST = "localhost"
DEFAULT_MQTT_PORT = 1883
DEFAULT_POLL_INTERVAL_MS = 100
DEFAULT_DEBOUNCE_MS = 50
DEFAULT_HEARTBEAT_SEC = 10.0

# Forbidden topics that GPIO must never subscribe to
FORBIDDEN_TOPICS = ["nestshift/brain/", "nestshift/agents/"]


class GPIOService:
    """GPIO service for reading sensors and controlling devices."""
    
    def __init__(self, config_path: str = "config/hardware_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Service state
        self._running = False
        self._client: Optional[aiomqtt.Client] = None
        self._input_pins: dict[int, dict] = {}
        self._output_pins: dict[int, dict] = {}
        self._last_state: dict[int, bool] = {}
        self._last_change_time: dict[int, float] = {}
        
        # Simulation mode
        self._simulation_mode = not GPIO_AVAILABLE
        self._simulation_task: Optional[asyncio.Task] = None
        
        # Heartbeat
        self._start_time = time.time()
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # MQTT
        self.mqtt_host = self.config.get("mqtt", {}).get("broker", DEFAULT_MQTT_HOST)
        self.mqtt_port = self.config.get("mqtt", {}).get("port", DEFAULT_MQTT_PORT)
        
        # Assert safety invariant
        self._assert_safety_invariant()
        
        # Setup GPIO
        self._setup_gpio()
    
    def _load_config(self) -> dict:
        """Load hardware configuration from YAML."""
        config = {"gpio": {}, "zigbee": {}, "mqtt": {}}
        
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
        """Assert that GPIO config never references forbidden topics."""
        gpio_config = self.config.get("gpio", {}).get("pins", {})
        
        for pin_name, pin_config in gpio_config.items():
            topic = pin_config.get("topic", "")
            for forbidden in FORBIDDEN_TOPICS:
                if forbidden in topic:
                    raise ValueError(
                        f"Safety violation: GPIO pin '{pin_name}' references forbidden topic '{topic}'. "
                        f"GPIO must never subscribe to {FORBIDDEN_TOPICS}"
                    )
    
    def _setup_gpio(self):
        """Initialize GPIO pins from configuration."""
        if self._simulation_mode:
            print("🔌 GPIO running in simulation mode (no hardware)")
        else:
            GPIO.setmode(GPIO.BCM)
        
        gpio_config = self.config.get("gpio", {})
        pins = gpio_config.get("pins", {})
        
        for pin_name, pin_config in pins.items():
            pin = pin_config["pin"]
            pin_type = pin_config["type"]
            
            if pin_type == "input":
                pull = pin_config.get("pull", "up")
                pull_mode = GPIO.PUD_UP if pull == "up" else GPIO.PUD_DOWN
                
                try:
                    if not self._simulation_mode:
                        GPIO.setup(pin, GPIO.IN, pull_up_down=pull_mode)
                    self._input_pins[pin] = {
                        "name": pin_name,
                        "topic": pin_config["topic"],
                        "debounce_ms": pin_config.get("debounce_ms", DEFAULT_DEBOUNCE_MS),
                    }
                    self._last_state[pin] = False
                    self._last_change_time[pin] = 0
                    print(f"   Input pin {pin} ({pin_name}) -> {pin_config['topic']}")
                except Exception as e:
                    print(f"⚠️ Failed to setup input pin {pin}: {e}")
                    
            elif pin_type == "output":
                try:
                    if not self._simulation_mode:
                        GPIO.setup(pin, GPIO.OUT)
                    self._output_pins[pin] = {
                        "name": pin_name,
                        "topic": pin_config["topic"],
                    }
                    # Initialize output to off
                    if not self._simulation_mode:
                        GPIO.output(pin, False)
                    print(f"   Output pin {pin} ({pin_name}) <- {pin_config['topic']}")
                except Exception as e:
                    print(f"⚠️ Failed to setup output pin {pin}: {e}")
        
        self.poll_interval_ms = gpio_config.get("poll_interval_ms", DEFAULT_POLL_INTERVAL_MS)
    
    async def start(self):
        """Start GPIO service - connect to MQTT and begin polling."""
        self._running = True
        self._start_time = time.time()
        
        print(f"🔌 GPIO Service starting on {self.mqtt_host}:{self.mqtt_port}")
        
        try:
            async with aiomqtt.Client(self.mqtt_host, self.mqtt_port) as client:
                self._client = client
                
                # Subscribe to device command topics
                for pin, pin_config in self._output_pins.items():
                    topic = pin_config["topic"]
                    await client.subscribe(topic)
                    print(f"   Subscribed: {topic}")
                
                # Start heartbeat
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                # Start polling inputs or simulation
                if self._simulation_mode:
                    self._simulation_task = asyncio.create_task(self._simulation_loop())
                else:
                    await self._poll_inputs()
                    
        except Exception as e:
            print(f"❌ GPIO Service error: {e}")
        finally:
            self._running = False
            self.stop()
    
    async def _poll_inputs(self):
        """Poll input pins at configured interval."""
        while self._running:
            now = time.time() * 1000  # ms
            
            for pin, pin_config in self._input_pins.items():
                try:
                    # Read pin state
                    if self._simulation_mode:
                        state = GPIO.input(pin) if hasattr(GPIO, 'input') else False
                    else:
                        state = GPIO.input(pin)
                    
                    # Debounce check
                    if state != self._last_state.get(pin):
                        time_since_change = now - self._last_change_time.get(pin, 0)
                        if time_since_change >= pin_config["debounce_ms"]:
                            # State changed - publish
                            self._last_state[pin] = state
                            self._last_change_time[pin] = now
                            await self._publish_sensor(pin_config["topic"], state)
                            
                except Exception as e:
                    print(f"⚠️ Error reading pin {pin}: {e}")
            
            await asyncio.sleep(self.poll_interval_ms / 1000.0)
    
    async def _simulation_loop(self):
        """Simulation mode - fire random sensor events without hardware."""
        import random
        
        print("🎲 GPIO simulation mode - generating random sensor events")
        
        while self._running:
            try:
                # Pick a random input pin
                if self._input_pins:
                    pin = random.choice(list(self._input_pins.keys()))
                    pin_config = self._input_pins[pin]
                    
                    # Toggle state randomly
                    new_state = random.choice([True, False])
                    self._last_state[pin] = new_state
                    
                    # Publish sensor event
                    await self._publish_sensor(pin_config["topic"], new_state)
                    print(f"🎲 Simulated sensor {pin_config['topic']}: {new_state}")
                
                # Random interval 10-30 seconds
                await asyncio.sleep(random.uniform(10, 30))
                
            except Exception as e:
                print(f"⚠️ Simulation error: {e}")
    
    async def _publish_sensor(self, topic: str, state: bool):
        """Publish sensor state to MQTT."""
        if self._client is None:
            return
        
        # Determine payload based on topic
        if "motion" in topic:
            payload = {"state": state}
        elif "door" in topic:
            payload = {"state": "open" if state else "closed"}
        else:
            payload = {"state": state}
        
        try:
            await self._client.publish(topic, json.dumps(payload))
        except Exception as e:
            print(f"❌ Failed to publish sensor: {e}")
    
    async def _handle_device_command(self, topic: str, payload: dict):
        """Handle incoming device command."""
        # Extract pin from topic
        matching_pin = None
        for pin, pin_config in self._output_pins.items():
            if pin_config["topic"] == topic:
                matching_pin = pin
                break
        
        if matching_pin is None:
            return
        
        # Parse command
        try:
            new_state = payload.get("state", "off")
            value = True if new_state == "on" else False
            
            # Execute GPIO write
            if not self._simulation_mode:
                GPIO.output(matching_pin, value)
            
            print(f"🔌 Set pin {matching_pin} to {value}")
            
        except Exception as e:
            print(f"❌ Failed to set output pin: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat with GPIO status."""
        while self._running:
            await asyncio.sleep(DEFAULT_HEARTBEAT_SEC)
            if self._running:
                await self._send_heartbeat()
    
    async def _send_heartbeat(self):
        """Publish heartbeat status."""
        if self._client is None:
            return
        
        active_inputs = len([p for p in self._input_pins.keys() 
                           if self._last_state.get(p, False)])
        
        heartbeat = {
            "simulation_mode": self._simulation_mode,
            "input_pins": len(self._input_pins),
            "output_pins": len(self._output_pins),
            "active_inputs": active_inputs,
            "uptime_seconds": int(time.time() - self._start_time),
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            await self._client.publish("nestshift/gpio/status", json.dumps(heartbeat))
        except Exception as e:
            print(f"❌ Heartbeat failed: {e}")
    
    def stop(self):
        """Stop GPIO service."""
        self._running = False
        if not self._simulation_mode:
            GPIO.cleanup()
        print("🔌 GPIO Service stopped")


async def main():
    """Main entry point."""
    import yaml
    
    config_path = os.getenv("HARDWARE_CONFIG", "config/hardware_config.yaml")
    service = GPIOService(config_path)
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())