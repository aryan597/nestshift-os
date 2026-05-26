"""Leaky Integrate-and-Fire (LIF) Neuron implementation.

Uses Euler integration: τ_m · dV/dt = -(V - V_rest) + R_m · I(t)
Spike when V >= v_threshold → reset to v_reset, enforce refractory.
Event-driven only — step() is called on MQTT message arrival.
"""

from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class LIFParameters:
    """Parameters for LIF neuron."""
    tau_m_ms: float = 20.0       # Membrane time constant (ms)
    v_rest_mv: float = -70.0     # Resting potential (mV)
    v_threshold_mv: float = -55.0 # Spike threshold (mV)
    v_reset_mv: float = -75.0    # Reset potential after spike (mV)
    r_membrane: float = 10.0     # Membrane resistance (MΩ)
    refractory_period_ms: float = 2.0  # Refractory period (ms)


class LIFNeuron:
    """Leaky Integrate-and-Fire neuron with event-driven updates."""
    
    def __init__(self, neuron_id: str, params: Optional[LIFParameters] = None):
        self.neuron_id = neuron_id
        self.params = params or LIFParameters()
        
        # State
        self.membrane_potential_mv = self.params.v_rest_mv
        self.last_spike_time_ms: Optional[float] = None
        self.spike_history: list[dict] = []  # For XAI trace
        self._in_refractory = False
        self._refractory_end_ms: float = 0.0
    
    def step(self, input_current_ma: float, current_time_ms: float) -> bool:
        """Process input current and update membrane potential.
        
        Event-driven Euler integration: For each input event, we simulate
        a burst of time steps (dt=0.1ms) to allow the neuron to respond
        to the input before returning.
        
        Euler: τ_m · dV/dt = -(V - V_rest) + R_m · I(t)
        Rearranged: V_new = V + (dt/tau_m) * (-(V - V_rest) + R_m * I)
        
        Args:
            input_current_ma: Input current in mA
            current_time_ms: Current simulation time in ms
            
        Returns:
            True if neuron spiked, False otherwise
        """
        tau_m = self.params.tau_m_ms
        v_rest = self.params.v_rest_mv
        r_m = self.params.r_membrane
        v_threshold = self.params.v_threshold_mv
        
        # Event-driven: simulate multiple small time steps
        # 200 steps of 0.1ms = 20ms of simulation per event (one tau)
        dt = 0.1
        num_steps = 200
        
        for _ in range(num_steps):
            # Check refractory period
            if self._in_refractory and current_time_ms < self._refractory_end_ms:
                return False
            elif self._in_refractory:
                self._in_refractory = False
            
            # Euler integration: V_new = V + (dt/tau_m) * (-(V - V_rest) + R_m * I)
            v_current = self.membrane_potential_mv
            dV = (dt / tau_m) * (-(v_current - v_rest) + r_m * input_current_ma)
            self.membrane_potential_mv = v_current + dV
            
            # Check for spike
            if self.membrane_potential_mv >= v_threshold:
                # Spike! Reset and enter refractory
                self.spike_history.append({
                    "timestamp_ms": current_time_ms,
                    "membrane_potential_mv": self.membrane_potential_mv,
                    "input_current_ma": input_current_ma,
                })
                self.last_spike_time_ms = current_time_ms
                self.membrane_potential_mv = self.params.v_reset_mv
                self._in_refractory = True
                self._refractory_end_ms = current_time_ms + self.params.refractory_period_ms
                return True
        
        return False
    
    @staticmethod
    def encode_sensor_value(sensor_type: str, value: float, 
                          normalized_value: Optional[float] = None,
                          manual_override: bool = False) -> float:
        """Encode sensor reading as input current.
        
        Binary (motion/door): I = 2.5 on event
        Analogue (temp/energy): I = normalised_value * 3.0
        Manual override: I += 1.0 per override (teaching signal)
        
        Args:
            sensor_type: Type of sensor (motion, door, temp, energy, etc.)
            value: Raw sensor value
            normalized_value: Optional normalized value (0-1) for analogue sensors
            manual_override: Whether this is a manual override (teaching signal)
            
        Returns:
            Input current in mA
        """
        current = 0.0
        
        if sensor_type in ("motion", "door", "contact"):
            # Binary sensor - on event
            if value != 0:
                current = 2.5
        elif sensor_type in ("temp", "temperature", "energy", "power", "humidity"):
            # Analogue sensor - use normalized value
            if normalized_value is not None:
                current = normalized_value * 3.0
            else:
                # Fallback: assume value is already 0-1 normalized
                current = min(max(value, 0.0), 1.0) * 3.0
        else:
            # Generic: treat as binary on/off
            if value:
                current = 2.5
        
        # Add teaching signal for manual override
        if manual_override:
            current += 1.0
        
        return current
    
    def get_state(self) -> dict:
        """Get current neuron state for debugging/monitoring."""
        return {
            "neuron_id": self.neuron_id,
            "membrane_potential_mv": round(self.membrane_potential_mv, 2),
            "last_spike_time_ms": self.last_spike_time_ms,
            "in_refractory": self._in_refractory,
            "spike_count": len(self.spike_history),
        }