import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import aiomqtt
import numpy as np
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain-nare")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
BRAIN_STORAGE = os.getenv("BRAIN_STORAGE", "/opt/nestshift/brain_state.json")

class NeuronConfig(BaseModel):
    threshold: float = 1.0
    leak_factor: float = 0.95
    refractory_period: float = 2.0  # Seconds
    base_weight: float = 0.1

class LIFNeuron:
    """Leaky Integrate-and-Fire (LIF) Neuron Model"""
    def __init__(self, id: str, config: NeuronConfig):
        self.id = id
        self.v = 0.0  # Membrane Potential
        self.config = config
        self.last_spike_time = 0.0
        self.last_update_time = time.time()

    def update(self):
        """Apply leak based on elapsed time"""
        now = time.time()
        dt = now - self.last_update_time
        # Leak proportional to time
        self.v *= (self.config.leak_factor ** dt)
        self.last_update_time = now

    def input(self, charge: float) -> bool:
        """Add charge and check for spike"""
        self.update()
        
        # Check refractory period
        if time.time() - self.last_spike_time < self.config.refractory_period:
            return False

        self.v += charge
        if self.v >= self.config.threshold:
            self.spike()
            return True
        return False

    def spike(self):
        """Fire and reset"""
        logger.debug(f"Neuron {self.id} FIRED!")
        self.v = 0.0
        self.last_spike_time = time.time()

class Synapse:
    """Connection between two neurons with Hebbian Learning (STDP)"""
    def __init__(self, pre_id: str, post_id: str, weight: float = 0.1):
        self.pre_id = pre_id
        self.post_id = post_id
        self.weight = weight
        self.last_pre_spike = 0.0

    def learn(self, post_spike_time: float):
        """Neurons that fire together, wire together"""
        dt = post_spike_time - self.last_pre_spike
        if 0 < dt < 5.0:  # If Pre fired shortly before Post
            # Strengthen synapse
            self.weight = min(1.0, self.weight + 0.05 * (1.0 / (1.0 + dt)))
            logger.info(f"Synapse {self.pre_id} -> {self.post_id} strengthened: {self.weight:.2f}")

class NeuralCore:
    def __init__(self):
        self.neurons: Dict[str, LIFNeuron] = {}
        self.synapses: Dict[str, List[Synapse]] = {}  # pre_id -> [Synapses]
        self.config = NeuronConfig()
        self.load_state()

    def get_or_create_neuron(self, neuron_id: str) -> LIFNeuron:
        if neuron_id not in self.neurons:
            self.neurons[neuron_id] = LIFNeuron(neuron_id, self.config)
        return self.neurons[neuron_id]

    def process_spike(self, sensor_id: str) -> List[str]:
        """Process an input spike and return triggered action IDs"""
        triggered_actions = []
        
        # 1. Update the 'Pre' neuron (Sensor)
        pre_neuron = self.get_or_create_neuron(sensor_id)
        pre_neuron.spike() # Force sensor neurons to spike on input
        
        # 2. Update Synapses and 'Post' neurons (Devices)
        if sensor_id in self.synapses:
            for synapse in self.synapses[sensor_id]:
                synapse.last_pre_spike = time.time()
                post_neuron = self.get_or_create_neuron(synapse.post_id)
                if post_neuron.input(synapse.weight):
                    triggered_actions.append(synapse.post_id)
        
        return triggered_actions

    def record_manual_action(self, sensor_id: str, action_id: str):
        """Hebbian Learning: User manually did something after a sensor fired"""
        # Ensure synapse exists
        if sensor_id not in self.synapses:
            self.synapses[sensor_id] = []
        
        existing = next((s for s in self.synapses[sensor_id] if s.post_id == action_id), None)
        if not existing:
            existing = Synapse(sensor_id, action_id)
            self.synapses[sensor_id].append(existing)
            logger.info(f"New Synapse formed: {sensor_id} -> {action_id}")
        
        existing.learn(time.time())
        self.save_state()

    def save_state(self):
        state = {
            "synapses": [
                {"pre": s.pre_id, "post": s.post_id, "weight": s.weight}
                for pre in self.synapses.values() for s in pre
            ]
        }
        try:
            os.makedirs(os.path.dirname(BRAIN_STORAGE), exist_ok=True)
            with open(BRAIN_STORAGE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Failed to save brain state: {e}")

    def load_state(self):
        if os.path.exists(BRAIN_STORAGE):
            try:
                with open(BRAIN_STORAGE, "r") as f:
                    state = json.load(f)
                    for s in state.get("synapses", []):
                        if s["pre"] not in self.synapses:
                            self.synapses[s["pre"]] = []
                        self.synapses[s["pre"]].append(Synapse(s["pre"], s["post"], s["weight"]))
                logger.info(f"Loaded {len(state.get('synapses', []))} synapses from storage")
            except Exception as e:
                logger.error(f"Failed to load brain state: {e}")

async def main():
    logger.info("NestShift Neural Core (NARE) starting")
    core = NeuralCore()
    last_sensor_spikes = {} # sensor_id -> timestamp

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        # Subscribe to all sensor readings and device states
        await client.subscribe("nestshift/sensors/+/reading")
        await client.subscribe("nestshift/devices/+/state")
        
        logger.info("Connected to MQTT broker")

        async for message in client.messages:
            topic = str(message.topic)
            payload = json.loads(message.payload.decode())

            if topic.startswith("nestshift/sensors/"):
                sensor_id = topic.split("/")[2]
                # Filter for binary/trigger sensors for now (Motion, Door)
                if payload.get("type") in ["motion", "door", "button"]:
                    if payload.get("value") == 1 or payload.get("value") is True:
                        last_sensor_spikes[sensor_id] = time.time()
                        actions = core.process_spike(sensor_id)
                        
                        for action_id in actions:
                            await client.publish(
                                f"nestshift/agents/brain/action",
                                json.dumps({
                                    "device_id": action_id,
                                    "action": "turn_on",
                                    "source": "brain",
                                    "explanation": f"Neuron {sensor_id} triggered {action_id} based on learned synapse strength."
                                })
                            )

            elif topic.startswith("nestshift/devices/"):
                device_id = topic.split("/")[2]
                # Check for manual actions (source != brain) to learn
                if payload.get("source") != "brain" and payload.get("state") == "on":
                    # Find which sensor fired recently to associate with this manual action
                    now = time.time()
                    for sensor_id, last_time in last_sensor_spikes.items():
                        if now - last_time < 10.0: # 10 second window for Hebbian learning
                            core.record_manual_action(sensor_id, device_id)

if __name__ == "__main__":
    asyncio.run(main())
