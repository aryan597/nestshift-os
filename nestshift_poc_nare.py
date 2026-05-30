#!/usr/bin/env python3
"""
NestShift OS -- NARE Brain Proof-of-Concept
============================================
Demonstrates the Neural Autonomous Residential Engine learning sensor-device
associations via STDP (spike-timing-dependent plasticity) on a synthetic
"day in the life" event stream.

Outputs:
    nare_learning_curve.png   -- Synapse weight evolution over time
    nare_synapse_map.json     -- Final learned connections and weights
    nare_spike_raster.png     -- Neuron spike raster plot
    nare_neural_trace.json    -- Explainability trace (XAI)
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "poc_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT / "services" / "brain"))

# Import NARE components directly
from nare import NARE
from neuron import LIFNeuron, LIFParameters
from synapse import SynapseRegistry
from stdp import STDPLearner, STDParameters


class FakeMQTTClient:
    """Mock MQTT client that records publishes instead of sending."""
    def __init__(self):
        self.published = []

    async def publish(self, topic, payload):
        self.published.append({"topic": topic, "payload": payload, "time": time.time()})

    async def subscribe(self, topic):
        pass

    def __aenter__(self):
        return self

    def __aexit__(self, *args):
        pass

    def messages(self):
        return []


class NAREPoC:
    def __init__(self):
        self.nare = NARE(config={
            "db_path": str(OUTPUT_DIR / "synapses_poc.db"),
            "initial_weight": 0.05,
            "prune_threshold": 0.02,
            "activation_threshold": 0.55,
            "heartbeat_interval_sec": 9999,  # disable for PoC
        })
        self.nare._client = FakeMQTTClient()
        self.history = []

    def inject_sensor_event(self, topic, payload, timestamp_ms):
        """Manually feed a sensor event into NARE."""
        neuron = self.nare.get_neuron(topic)
        sensor_type, raw_value, normalized_value = self.nare._extract_sensor_info(topic, payload)
        input_current = LIFNeuron.encode_sensor_value(
            sensor_type, raw_value, normalized_value, manual_override=False
        )
        spiked = neuron.step(input_current, timestamp_ms)

        if spiked:
            self.nare._spike_timestamps.append(timestamp_ms)
            self.nare.synapse_registry.record_spike(topic, timestamp_ms)

        # After spike, check synapses (synchronous for demo)
        if spiked:
            synapses = self.nare.synapse_registry.get_synapses_from_sensor(topic)
            for synapse in synapses:
                if synapse.weight >= self.nare.activation_threshold:
                    # Publish intent (mock)
                    self.nare._client.published.append({
                        "topic": f"nestshift/brain/intent/{synapse.post_topic}",
                        "payload": json.dumps({"weight": synapse.weight}),
                        "time": time.time(),
                    })
                    # STDP update
                    delta_t = 10.0
                    new_weight = self.nare.stdp.update_weight(synapse.weight, delta_t)
                    self.nare.synapse_registry.update_weight(topic, synapse.post_topic, new_weight)

        self.history.append({
            "time_ms": timestamp_ms,
            "topic": topic,
            "spiked": spiked,
            "membrane_potential_mv": neuron.membrane_potential_mv,
        })
        return spiked

    def inject_manual_override(self, device_topic, timestamp_ms):
        """Simulate user pressing a physical switch. Direct STDP update."""
        self.nare.synapse_registry.record_spike(device_topic, timestamp_ms)
        recent = self.nare.synapse_registry.get_recent_spikes(
            within_ms=self.nare.teaching_window_ms,
            current_time_ms=timestamp_ms,
        )
        synapses = [s for s in self.nare.synapse_registry.get_all_synapses()
                    if s.post_topic == device_topic]
        for synapse in synapses:
            if synapse.pre_topic in recent:
                pre_time = recent[synapse.pre_topic]
                delta_t = timestamp_ms - pre_time
                old_weight = synapse.weight
                new_weight = self.nare.stdp.potentate(synapse.weight, delta_t)
                self.nare.synapse_registry.update_weight(
                    synapse.pre_topic, synapse.post_topic, new_weight
                )
                print(f"  [STDP] {synapse.pre_topic} -> {synapse.post_topic}: "
                      f"{old_weight:.3f} -> {new_weight:.3f} (dw={new_weight-old_weight:.4f}, dt={delta_t:.0f}ms)")

    def get_synapse_evolution(self):
        """Return list of all synapses with their current weights."""
        return [
            {"pre": s.pre_topic, "post": s.post_topic, "weight": s.weight}
            for s in self.nare.synapse_registry.get_all_synapses()
        ]


def run_scenario():
    """Run a synthetic 24-hour scenario."""
    print("=" * 70)
    print("NARE BRAIN -- PROOF-OF-CONCEPT SIMULATION")
    print("Demonstrating Hebbian learning in a smart home environment")
    print("=" * 70)

    poc = NAREPoC()
    base_time = time.time() * 1000

    # Pre-seed weak synapses with CORRECT post_topic matching override handler
    # _handle_manual_override builds device_topic as f"nestshift/devices/{device_id}/command"
    poc.nare.synapse_registry.get_or_create("sensors/motion/hallway", "nestshift/devices/light/hallway/command")
    poc.nare.synapse_registry.get_or_create("sensors/motion/living_room", "nestshift/devices/light/living_room/command")
    poc.nare.synapse_registry.get_or_create("sensors/temp/bedroom", "nestshift/devices/hvac/bedroom/command")

    # HACK for PoC demo: lower activation threshold so weak synapses learn
    poc.nare.activation_threshold = 0.15
    # Increase STDP learning rate for visible weight changes in short demo
    poc.nare.stdp.params.a_plus = 0.15
    poc.nare.stdp.params.a_minus = 0.10
    poc.nare.stdp.params.tau_plus_ms = 50.0  # wider window
    print(f"[NARE] Demo config: activation_threshold={poc.nare.activation_threshold}, a_plus={poc.nare.stdp.params.a_plus}")

    scenario = [
        (0,      "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (100,    "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (500,    "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (600,    "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (2000,   "sensors/motion/living_room",   {"value": 1, "normalized": 1.0}),
        (2100,   "nestshift/devices/light/living_room/command", "OVERRIDE_ON"),
        (2500,   "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (2600,   "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (5000,   "sensors/temp/bedroom",         {"value": 18.5, "normalized": 0.45}),
        (7000,   "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (7100,   "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (7200,   "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (7300,   "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (8000,   "sensors/motion/living_room",   {"value": 1, "normalized": 1.0}),
        (8100,   "nestshift/devices/light/living_room/command", "OVERRIDE_ON"),
        (9000,   "sensors/temp/bedroom",         {"value": 19.2, "normalized": 0.52}),
        (12000,  "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (12100,  "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (15000,  "sensors/temp/bedroom",         {"value": 20.1, "normalized": 0.60}),
        (18000,  "sensors/motion/living_room",   {"value": 1, "normalized": 1.0}),
        (18100,  "nestshift/devices/light/living_room/command", "OVERRIDE_ON"),
        (20000,  "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (20100,  "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (25000,  "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (25100,  "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
        (28000,  "sensors/motion/living_room",   {"value": 1, "normalized": 1.0}),
        (28100,  "nestshift/devices/light/living_room/command", "OVERRIDE_ON"),
        (30000,  "sensors/temp/bedroom",         {"value": 21.5, "normalized": 0.75}),
        (36000,  "sensors/motion/hallway",       {"value": 1, "normalized": 1.0}),
        (36100,  "nestshift/devices/light/hallway/command",   "OVERRIDE_ON"),
    ]

    weight_history = {
        "sensors/motion/hallway->nestshift/devices/light/hallway/command": [],
        "sensors/motion/living_room->nestshift/devices/light/living_room/command": [],
        "sensors/temp/bedroom->nestshift/devices/hvac/bedroom/command": [],
    }

    spike_log = []

    for offset, topic, payload in scenario:
        t = base_time + offset
        if payload == "OVERRIDE_ON":
            poc.inject_manual_override(topic, t)
            print(f"[t+{offset:>5}ms] USER OVERRIDE: {topic}")
        else:
            spiked = poc.inject_sensor_event(topic, payload, t)
            spike_log.append({"time": offset, "topic": topic, "spiked": spiked})
            if spiked:
                print(f"[t+{offset:>5}ms] SPIKE: {topic}  (V={poc.nare.get_neuron(topic).membrane_potential_mv:.1f}mV)")

        # Record weights
        for syn in poc.nare.synapse_registry.get_all_synapses():
            key = f"{syn.pre_topic}->{syn.post_topic}"
            if key in weight_history:
                weight_history[key].append((offset, syn.weight))

    # -----------------------------------------------------------------------
    # Final state
    # -----------------------------------------------------------------------
    final_synapses = poc.get_synapse_evolution()
    print()
    print("=" * 70)
    print("FINAL LEARNED SYNAPSES")
    print("=" * 70)
    for s in final_synapses:
        status = "AUTONOMOUS" if s["weight"] >= 0.55 else "LEARNING"
        print(f"  {s['pre']:<35} -> {s['post']:<35}  weight={s['weight']:.3f}  [{status}]")
    print()

    # -----------------------------------------------------------------------
    # Plot 1: Synapse weight evolution
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    colours = {"sensors/motion/hallway->devices/light/hallway": "#00d4aa",
               "sensors/motion/living_room->devices/light/living_room": "#ff6b6b",
               "sensors/temp/bedroom->devices/hvac/bedroom": "#4ecdc4"}

    for key, vals in weight_history.items():
        if vals:
            xs, ys = zip(*vals)
            label = key.replace("sensors/", "").replace("devices/", "").replace("->", " → ")
            ax.plot(xs, ys, label=label, color=colours.get(key, "white"), linewidth=2)

    ax.axhline(0.55, color="yellow", linestyle="--", alpha=0.7, label="Autonomy threshold")
    ax.set_xlabel("Simulation Time (ms)", color="white")
    ax.set_ylabel("Synaptic Weight", color="white")
    ax.set_title("NARE Brain: Hebbian Learning Curve (STDP)", fontsize=14, fontweight="bold", color="white")
    ax.legend(loc="lower right", facecolor="#1a1a1a", edgecolor="#333", labelcolor="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    path = OUTPUT_DIR / "nare_learning_curve.png"
    fig.savefig(path, dpi=300, facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Synapse learning curve: {path}")

    # -----------------------------------------------------------------------
    # Plot 2: Spike raster
    # -----------------------------------------------------------------------
    spike_df = [s for s in spike_log if s["spiked"]]
    topics = sorted(set(s["topic"] for s in spike_df))
    topic_idx = {t: i for i, t in enumerate(topics)}

    fig, ax = plt.subplots(figsize=(12, 4))
    for s in spike_df:
        ax.scatter(s["time"], topic_idx[s["topic"]], color="#00d4aa", s=40, zorder=3)

    ax.set_yticks(range(len(topics)))
    ax.set_yticklabels([t.replace("sensors/", "") for t in topics], color="white")
    ax.set_xlabel("Time (ms)", color="white")
    ax.set_title("NARE Neuron Spike Raster", fontsize=13, fontweight="bold", color="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white", axis="x")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    path2 = OUTPUT_DIR / "nare_spike_raster.png"
    fig.savefig(path2, dpi=300, facecolor="#1a1a1a")
    plt.close(fig)
    print(f"[PLOT] Spike raster: {path2}")

    # -----------------------------------------------------------------------
    # Save JSON outputs
    # -----------------------------------------------------------------------
    synapse_path = OUTPUT_DIR / "nare_synapse_map.json"
    with open(synapse_path, "w") as f:
        json.dump({
            "synapses": final_synapses,
            "autonomous_count": sum(1 for s in final_synapses if s["weight"] >= 0.55),
            "learning_count": sum(1 for s in final_synapses if s["weight"] < 0.55),
            "simulation_events": len(scenario),
        }, f, indent=2)
    print(f"[JSON] Synapse map: {synapse_path}")

    trace_path = OUTPUT_DIR / "nare_neural_trace.json"
    with open(trace_path, "w") as f:
        json.dump({
            "trace_entries": [e for e in poc.nare.synapse_registry._neural_trace],
            "total_intents_published": len(poc.nare._client.published),
            "published_topics": list(set(p["topic"] for p in poc.nare._client.published)),
        }, f, indent=2, default=str)
    print(f"[JSON] Neural trace: {trace_path}")

    print()
    print("=" * 70)
    print("NARE PoC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_scenario()
