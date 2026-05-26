"""NARE (Neural Autonomous Residential Engine) Orchestrator."""

import asyncio
import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiomqtt

from neuron import LIFNeuron, LIFParameters
from stdp import STDPLearner, STDParameters
from synapse import SynapseRegistry, NeuralTraceEntry, DEFAULT_PRUNE_THRESHOLD


# Configuration defaults
DEFAULT_MQTT_HOST = "localhost"
DEFAULT_MQTT_PORT = 1883
DEFAULT_ACTIVATION_THRESHOLD = 0.65
DEFAULT_HEARTBEAT_SEC = 5.0
DEFAULT_TEACHING_WINDOW_MS = 500.0


class NARE:
    """Neural Autonomous Residential Engine - Main orchestrator."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
        # Load parameters from config or use defaults
        self._load_parameters()
        
        # Initialize components
        self.synapse_registry = SynapseRegistry(
            db_path=self.config.get("db_path", "brain/synapses.db"),
            initial_weight=self.config.get("initial_weight", 0.1),
            prune_threshold=self.config.get("prune_threshold", DEFAULT_PRUNE_THRESHOLD),
            prune_days=self.config.get("prune_days", 30),
            persist_interval_sec=self.config.get("persist_interval_sec", 60),
        )
        self.stdp = STDPLearner(
            params=STDParameters(
                a_plus=self.config.get("a_plus", 0.01),
                a_minus=self.config.get("a_minus", 0.012),
                tau_plus_ms=self.config.get("tau_plus_ms", 20.0),
                tau_minus_ms=self.config.get("tau_minus_ms", 20.0),
                w_min=self.config.get("w_min", 0.0),
                w_max=self.config.get("w_max", 1.0),
            )
        )
        
        # Neuron cache: topic -> LIFNeuron
        self._neurons: dict[str, LIFNeuron] = {}
        
        # Track spikes for heartbeat stats
        self._spike_timestamps: list[float] = []
        self._autonomous_actions_today = 0
        self._day_start = datetime.now().date()
        
        # MQTT client (initialized on start)
        self._client: Optional[aiomqtt.Client] = None
        self._running = False
        self._start_time = time.time()
        
        # Heartbeat timer
        self._heartbeat_timer: Optional[asyncio.Task] = None
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def _load_parameters(self):
        """Load parameters from config or set defaults."""
        lif_params = self.config.get("lif", {})
        self.lif_params = LIFParameters(
            tau_m_ms=lif_params.get("tau_m_ms", 20.0),
            v_rest_mv=lif_params.get("v_rest_mv", -70.0),
            v_threshold_mv=lif_params.get("v_threshold_mv", -55.0),
            v_reset_mv=lif_params.get("v_reset_mv", -75.0),
            r_membrane=lif_params.get("r_membrane", 10.0),
            refractory_period_ms=lif_params.get("refractory_period_ms", 2.0),
        )
        
        self.activation_threshold = self.config.get("activation_threshold", 0.65)
        self.heartbeat_interval_sec = self.config.get("heartbeat_interval_sec", 5.0)
        self.teaching_window_ms = self.config.get("teaching_window_ms", 500.0)
        
        self.mqtt_host = self.config.get("mqtt_host", DEFAULT_MQTT_HOST)
        self.mqtt_port = self.config.get("mqtt_port", DEFAULT_MQTT_PORT)
    
    def get_neuron(self, topic: str) -> LIFNeuron:
        """Get or create neuron for a sensor topic."""
        with self._lock:
            if topic not in self._neurons:
                self._neurons[topic] = LIFNeuron(topic, self.lif_params)
            return self._neurons[topic]
    
    def _extract_sensor_info(self, topic: str, payload: dict) -> tuple[str, float, Optional[float]]:
        """Extract sensor type and value from MQTT message.
        
        Returns:
            (sensor_type, raw_value, normalized_value)
        """
        # Parse topic: sensors/<type>/<location> e.g., sensors/motion/living_room
        parts = topic.split("/")
        sensor_type = parts[1] if len(parts) > 1 else "unknown"
        
        # Extract values from payload
        raw_value = payload.get("value", payload.get("state", 0))
        normalized_value = payload.get("normalized", payload.get("normalized_value"))
        
        return sensor_type, raw_value, normalized_value
    
    def _extract_device_from_topic(self, topic: str) -> Optional[str]:
        """Extract device ID from topic.
        
        Topics: nestshift/devices/<device_id>/command
        Returns: device_id
        """
        # Match: nestshift/devices/light/living_room/command
        match = re.match(r"nestshift/devices/([^/]+)", topic)
        if match:
            return match.group(1)
        return None
    
    async def _handle_sensor_message(self, topic: str, payload: dict):
        """Process incoming sensor message.
        
        1. Encode value as current, step LIF neuron
        2. If spike: check all synapses where this is pre_topic
        3. If synapse weight > 0.65: publish intent
        4. Apply STDP update, append to neural_trace
        """
        current_time_ms = time.time() * 1000
        
        # Get sensor info
        sensor_type, raw_value, normalized_value = self._extract_sensor_info(topic, payload)
        
        # Get or create neuron
        neuron = self.get_neuron(topic)
        
        # Encode as current and step
        input_current = LIFNeuron.encode_sensor_value(
            sensor_type, raw_value, normalized_value, manual_override=False
        )
        spiked = neuron.step(input_current, current_time_ms)
        
        # Record spike timestamp
        if spiked:
            self._spike_timestamps.append(current_time_ms)
            self.synapse_registry.record_spike(topic, current_time_ms)
        
        # If neuron spiked, check synapses and potentially act
        if spiked:
            await self._process_spike(topic, neuron, current_time_ms)
    
    async def _process_spike(self, sensor_topic: str, neuron: LIFNeuron, 
                           spike_time_ms: float):
        """Process a neuron spike: check synapses and publish intent if strong."""
        # Get all synapses from this sensor
        synapses = self.synapse_registry.get_synapses_from_sensor(sensor_topic)
        
        for synapse in synapses:
            if synapse.weight >= self.activation_threshold:
                # Strong enough connection - publish intent
                await self._publish_intent(
                    synapse.post_topic,
                    sensor_topic,
                    synapse.weight,
                    spike_time_ms,
                    neuron.membrane_potential_mv,
                    trigger="autonomous"
                )
                
                # Update STDP (post occurred after pre - potentiation)
                delta_t = 10.0  # Assume slight delay for now
                new_weight = self.stdp.update_weight(synapse.weight, delta_t)
                self.synapse_registry.update_weight(
                    synapse.pre_topic, synapse.post_topic, new_weight
                )
                
                # Log to neural trace
                self._add_neural_trace(
                    pre_topic=sensor_topic,
                    post_topic=synapse.post_topic,
                    pre_spike_time_ms=spike_time_ms,
                    post_spike_time_ms=spike_time_ms + delta_t,
                    synapse_weight=new_weight,
                    delta_t_ms=delta_t,
                    action_taken="intent_published",
                    trigger="autonomous",
                    membrane_potential_mv=neuron.membrane_potential_mv
                )
                
                self._autonomous_actions_today += 1
    
    async def _publish_intent(self, device_topic: str, sensor_topic: str,
                            synapse_weight: float, spike_time_ms: float,
                            membrane_potential: float, trigger: str):
        """Publish intent to brain/intent/ topic (NOT directly to devices/)."""
        if self._client is None:
            return
        
        # Extract device ID and create intent topic
        device_id = self._extract_device_from_topic(device_topic)
        intent_topic = f"nestshift/brain/intent/{device_id}"
        
        payload = {
            "sensor": sensor_topic,
            "device": device_id,
            "confidence": synapse_weight,
            "timestamp_ms": spike_time_ms,
            "membrane_potential_mv": membrane_potential,
            "trigger": trigger,
        }
        
        try:
            await self._client.publish(intent_topic, json.dumps(payload))
            print(f"📤 Intent published: {sensor_topic} → {device_id} (weight: {synapse_weight:.2f})")
        except Exception as e:
            print(f"❌ Failed to publish intent: {e}")
    
    def _add_neural_trace(self, pre_topic: str, post_topic: str,
                         pre_spike_time_ms: Optional[float],
                         post_spike_time_ms: Optional[float],
                         synapse_weight: float, delta_t_ms: Optional[float],
                         action_taken: str, trigger: str,
                         membrane_potential_mv: float):
        """Add entry to neural trace for XAI."""
        entry = NeuralTraceEntry(
            timestamp=datetime.now().isoformat(),
            pre_topic=pre_topic,
            post_topic=post_topic,
            pre_spike_time_ms=pre_spike_time_ms,
            post_spike_time_ms=post_spike_time_ms,
            synapse_weight=synapse_weight,
            delta_t_ms=delta_t_ms,
            action_taken=action_taken,
            trigger=trigger,
            membrane_potential_mv=membrane_potential_mv,
        )
        self.synapse_registry.add_neural_trace(entry)
    
    async def _handle_manual_override(self, topic: str, payload: dict):
        """Handle manual override (Hebbian teaching loop).
        
        When user manually controls a device, strengthen recent sensor→device connections.
        Find neurons that spiked in last 500ms, apply potentiation.
        """
        current_time_ms = time.time() * 1000
        
        # Extract device from topic: nestshift/brain/manual_override/light/living_room
        parts = topic.split("/")
        device_id = parts[-1] if parts else "unknown"
        device_topic = f"nestshift/devices/{device_id}/command"
        
        # Record this as a "post spike" for teaching
        self.synapse_registry.record_spike(device_topic, current_time_ms)
        
        # Find recent sensor spikes (pre) that happened before this override
        recent_spikes = self.synapse_registry.get_recent_spikes(
            within_ms=self.teaching_window_ms,
            current_time_ms=current_time_ms
        )
        
        # Get all synapses for this device
        synapses = self.synapse_registry.get_synapses_from_sensor(device_topic)
        if not synapses:
            # Also check for any synapse pointing to this device
            synapses = [s for s in self.synapse_registry.get_all_synapses() 
                       if s.post_topic == device_topic]
        
        # Strengthen synapses where pre spiked recently
        for synapse in synapses:
            if synapse.pre_topic in recent_spikes:
                pre_time = recent_spikes[synapse.pre_topic]
                delta_t = current_time_ms - pre_time
                
                # Apply potentiation
                new_weight = self.stdp.potentate(synapse.weight, delta_t)
                self.synapse_registry.update_weight(
                    synapse.pre_topic, synapse.post_topic, new_weight
                )
                
                print(f"🧠 Synapse strengthened: {synapse.pre_topic}→{synapse.post_topic}, "
                      f"weight: {new_weight:.3f} (Δt={delta_t:.1f}ms)")
                
                # Log to neural trace
                self._add_neural_trace(
                    pre_topic=synapse.pre_topic,
                    post_topic=synapse.post_topic,
                    pre_spike_time_ms=pre_time,
                    post_spike_time_ms=current_time_ms,
                    synapse_weight=new_weight,
                    delta_t_ms=delta_t,
                    action_taken="teaching_potentiation",
                    trigger="manual_override",
                    membrane_potential_mv=self.lif_params.v_rest_mv
                )
    
    async def _send_heartbeat(self):
        """Send heartbeat with brain status."""
        if self._client is None:
            return
        
        now = time.time()
        current_time_ms = now * 1000
        
        # Check if day changed
        if datetime.now().date() > self._day_start:
            self._autonomous_actions_today = 0
            self._day_start = datetime.now().date()
        
        # Count spikes in last minute
        one_minute_ago = current_time_ms - 60000
        spikes_last_minute = len([t for t in self._spike_timestamps if t > one_minute_ago])
        
        stats = self.synapse_registry.get_stats()
        
        heartbeat = {
            "active_neurons": len(self._neurons),
            "total_synapses": stats["total_synapses"],
            "strong_synapses": stats["strong_synapses"],
            "spikes_last_minute": spikes_last_minute,
            "autonomous_actions_today": self._autonomous_actions_today,
            "uptime_seconds": int(now - self._start_time),
        }
        
        try:
            await self._client.publish("nestshift/brain/status", json.dumps(heartbeat))
        except Exception as e:
            print(f"❌ Heartbeat failed: {e}")
    
    async def _heartbeat_loop(self):
        """Periodic heartbeat task."""
        while self._running:
            await asyncio.sleep(self.heartbeat_interval_sec)
            if self._running:
                await self._send_heartbeat()
    
    async def start(self):
        """Start NARE - connect to MQTT and subscribe to topics."""
        self._running = True
        self._start_time = time.time()
        
        try:
            async with aiomqtt.Client(self.mqtt_host, self.mqtt_port) as client:
                self._client = client
                
                # Subscribe to sensor topics
                await client.subscribe("nestshift/sensors/#")
                
                # Subscribe to manual overrides for teaching
                await client.subscribe("nestshift/brain/manual_override/#")
                
                print(f"🧠 NARE started - listening on {self.mqtt_host}:{self.mqtt_port}")
                print("   Topics: nestshift/sensors/#, nestshift/brain/manual_override/#")
                
                # Start heartbeat
                self._heartbeat_timer = asyncio.create_task(self._heartbeat_loop())
                
                # Process messages
                async for message in client.messages:
                    topic = message.topic.value
                    try:
                        payload = json.loads(message.payload.decode())
                    except json.JSONDecodeError:
                        payload = {"raw": message.payload.decode()}
                    
                    # Route to appropriate handler
                    if topic.startswith("nestshift/sensors/"):
                        await self._handle_sensor_message(topic, payload)
                    elif topic.startswith("nestshift/brain/manual_override/"):
                        await self._handle_manual_override(topic, payload)
                    
                    # Ensure periodic persistence
                    self.synapse_registry._persist_if_needed()
                    
        except Exception as e:
            print(f"❌ NARE error: {e}")
        finally:
            self._running = False
            if self._heartbeat_timer:
                self._heartbeat_timer.cancel()
            self.synapse_registry.close()
    
    def stop(self):
        """Stop NARE."""
        self._running = False
        self.synapse_registry.close()
        print("🧠 NARE stopped")
    
    def get_stats(self) -> dict:
        """Get current NARE statistics."""
        synapse_stats = self.synapse_registry.get_stats()
        current_time_ms = time.time() * 1000
        spikes_last_minute = len([t for t in self._spike_timestamps 
                                  if t > current_time_ms - 60000])
        
        return {
            "active_neurons": len(self._neurons),
            "total_synapses": synapse_stats["total_synapses"],
            "strong_synapses": synapse_stats["strong_synapses"],
            "spikes_last_minute": spikes_last_minute,
            "autonomous_actions_today": self._autonomous_actions_today,
            "uptime_seconds": int(time.time() - self._start_time),
            **synapse_stats
        }


async def main():
    """Main entry point."""
    # Load config from file if exists
    config = {}
    config_path = "config/brain_config.yaml"
    if Path(config_path).exists():
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except ImportError:
            print("⚠️ PyYAML not installed, using defaults")
    
    nare = NARE(config)
    await nare.start()


if __name__ == "__main__":
    asyncio.run(main())