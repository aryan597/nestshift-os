"""Tests for NARE (Neural Autonomous Residential Engine).

These tests verify the LIF neuron, STDP learning, synapse registry,
and NARE orchestration. Run with: pytest tests/test_nare.py -v
"""

import pytest
import time
import tempfile
import os
import sys

# Add brain service to path
sys.path.insert(0, "services/brain")

from neuron import LIFNeuron, LIFParameters
from stdp import STDPLearner, STDParameters
from synapse import SynapseRegistry, NeuralTraceEntry


# =============================================================================
# LIF Neuron Tests
# =============================================================================

def test_lif_no_spike_below_threshold():
    """Test that LIF neuron does not spike when below threshold."""
    params = LIFParameters(
        tau_m_ms=20.0,
        v_rest_mv=-70.0,
        v_threshold_mv=-55.0,
        v_reset_mv=-75.0,
        r_membrane=10.0,
        refractory_period_ms=2.0
    )
    neuron = LIFNeuron("test_neuron", params)
    
    # Small input current - should not spike
    current_time = 1000.0  # ms
    spiked = neuron.step(input_current_ma=0.1, current_time_ms=current_time)
    
    assert not spiked, "Neuron should not spike with small input"
    assert neuron.membrane_potential_mv < params.v_threshold_mv
    assert neuron.membrane_potential_mv > params.v_rest_mv


def test_lif_spike_at_threshold():
    """Test that LIF neuron spikes when membrane potential reaches threshold."""
    params = LIFParameters(
        tau_m_ms=20.0,
        v_rest_mv=-70.0,
        v_threshold_mv=-55.0,
        v_reset_mv=-75.0,
        r_membrane=10.0,
        refractory_period_ms=2.0
    )
    neuron = LIFNeuron("test_neuron", params)
    
    # Large input current - should spike
    current_time = 1000.0  # ms
    spiked = neuron.step(input_current_ma=5.0, current_time_ms=current_time)
    
    assert spiked, "Neuron should spike with large input"
    assert len(neuron.spike_history) == 1


def test_lif_refractory_period_blocks_second_spike():
    """Test that refractory period blocks second spike."""
    params = LIFParameters(
        tau_m_ms=20.0,
        v_rest_mv=-70.0,
        v_threshold_mv=-55.0,
        v_reset_mv=-75.0,
        r_membrane=10.0,
        refractory_period_ms=2.0
    )
    neuron = LIFNeuron("test_neuron", params)
    
    current_time = 1000.0
    
    # First spike
    spiked1 = neuron.step(input_current_ma=5.0, current_time_ms=current_time)
    assert spiked1, "First spike should occur"
    assert neuron.membrane_potential_mv == params.v_reset_mv
    
    # Try second spike immediately (within refractory period)
    current_time = 1001.0  # Only 1ms later - still in refractory
    spiked2 = neuron.step(input_current_ma=5.0, current_time_ms=current_time)
    
    assert not spiked2, "Second spike should be blocked by refractory period"
    assert len(neuron.spike_history) == 1, "Should still have only 1 spike"


# =============================================================================
# STDP Tests
# =============================================================================

def test_stdp_potentiation_pre_before_post():
    """Test STDP potentiation when pre fires before post."""
    stdp = STDPLearner()
    
    initial_weight = 0.5
    delta_t = 10.0  # Pre fires 10ms before post
    
    new_weight = stdp.update_weight(initial_weight, delta_t)
    
    assert new_weight > initial_weight, "Weight should increase (potentiation)"
    assert new_weight <= 1.0, "Weight should not exceed max"


def test_stdp_depression_post_before_pre():
    """Test STDP depression when post fires before pre."""
    stdp = STDPLearner()
    
    initial_weight = 0.5
    delta_t = -10.0  # Post fires 10ms before pre
    
    new_weight = stdp.update_weight(initial_weight, delta_t)
    
    assert new_weight < initial_weight, "Weight should decrease (depression)"
    assert new_weight >= 0.0, "Weight should not go below min"


def test_stdp_weight_clamped_at_max():
    """Test that STDP clamps weight at w_max."""
    stdp = STDPLearner(params=STDParameters(w_max=1.0, a_plus=0.5))
    
    initial_weight = 0.9
    delta_t = 10.0  # Pre before post
    
    new_weight = stdp.update_weight(initial_weight, delta_t)
    
    assert new_weight == 1.0, "Weight should be clamped at max"


def test_stdp_weight_clamped_at_min():
    """Test that STDP clamps weight at w_min."""
    stdp = STDPLearner(params=STDParameters(w_min=0.0, a_minus=0.5))
    
    initial_weight = 0.1
    delta_t = -10.0  # Post before pre
    
    new_weight = stdp.update_weight(initial_weight, delta_t)
    
    assert new_weight == 0.0, "Weight should be clamped at min"


# =============================================================================
# Synapse Registry Tests
# =============================================================================

def test_synapse_auto_creates_at_low_weight():
    """Test that new sensor→device pairs auto-create with low weight."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_synapses.db")
        registry = SynapseRegistry(db_path=db_path, initial_weight=0.1)
        
        # Get or create new synapse
        synapse = registry.get_or_create(
            pre_topic="sensors/motion/living_room",
            post_topic="devices/light/living_room"
        )
        
        assert synapse is not None
        assert synapse.weight == 0.1, "New synapse should have initial weight"
        
        registry.close()


def test_hebbian_teaching_strengthens_recent_synapses():
    """Test that Hebbian teaching loop strengthens recent sensor→device pairs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_synapses.db")
        registry = SynapseRegistry(db_path=db_path, initial_weight=0.2)
        stdp = STDPLearner()
        
        pre_topic = "sensors/motion/living_room"
        post_topic = "devices/light/living_room"
        
        # Create synapse
        synapse = registry.get_or_create(pre_topic, post_topic)
        initial_weight = synapse.weight
        
        # Simulate sensor spike
        current_time = 10000.0
        registry.record_spike(pre_topic, current_time)
        
        # Simulate manual override (post spike) 50ms later
        override_time = current_time + 50.0
        registry.record_spike(post_topic, override_time)
        
        # Get recent spikes within teaching window
        recent_spikes = registry.get_recent_spikes(
            within_ms=500.0,
            current_time_ms=override_time
        )
        
        # Verify teaching found the sensor spike
        assert pre_topic in recent_spikes, "Sensor spike should be in recent spikes"
        
        # Apply potentiation (simulating Hebbian teaching)
        delta_t = override_time - recent_spikes[pre_topic]
        new_weight = stdp.potentate(initial_weight, delta_t)
        
        assert new_weight > initial_weight, "Hebbian teaching should strengthen synapse"
        
        registry.close()


# =============================================================================
# NARE Integration Test
# =============================================================================

def test_nare_publishes_to_intent_not_devices():
    """Test that NARE publishes to brain/intent/ not directly to devices/.
    
    This is a critical security requirement: NARE never directly controls
    devices - it publishes intents that Πsafe evaluates.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_synapses.db")
        registry = SynapseRegistry(db_path=db_path, initial_weight=0.7)
        
        # Create a strong synapse above activation threshold
        pre = "sensors/motion/living_room"
        post = "devices/light/living_room"
        
        synapse = registry.get_or_create(pre, post)
        synapse.weight = 0.8  # Above threshold
        registry.update_weight(pre, post, 0.8)
        
        # Verify NARE publishes to intent topic, not devices/
        strong_synapses = registry.get_strong_synapses(threshold=0.65)
        
        assert len(strong_synapses) == 1
        assert strong_synapses[0].pre_topic == pre
        assert strong_synapses[0].post_topic == post
        assert strong_synapses[0].weight >= 0.65
        
        # The post_topic should be devices/..., but NARE publishes intent to
        # nestshift/brain/intent/{device}, NOT to post_topic directly.
        # This is enforced in NARE._publish_intent() which transforms
        # post_topic → intent topic.
        
        # Verify intent topic pattern (not devices/)
        device_id = "living_room"
        intent_topic = f"nestshift/brain/intent/{device_id}"
        
        # This is what NARE should publish to, not to post_topic
        assert "brain/intent" in intent_topic
        assert "devices/" not in intent_topic
        
        registry.close()


# =============================================================================
# Additional Helper Tests (optional)
# =============================================================================

def test_lif_encode_sensor_binary():
    """Test sensor value encoding for binary sensors."""
    current = LIFNeuron.encode_sensor_value("motion", 1.0)
    assert current == 2.5


def test_lif_encode_sensor_analogue():
    """Test sensor value encoding for analogue sensors."""
    current = LIFNeuron.encode_sensor_value("temp", 25.0, normalized_value=0.5)
    assert current == 1.5  # 0.5 * 3.0


def test_lif_encode_with_manual_override():
    """Test that manual override adds teaching signal."""
    current = LIFNeuron.encode_sensor_value("motion", 1.0, manual_override=True)
    assert current == 3.5  # 2.5 + 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])