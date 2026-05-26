"""Spike-Timing Dependent Plasticity (STDP) Lear implementation.

STDP learning rule:
  Pre before post (Δt > 0): Δw = a_plus * exp(-Δt / tau_plus)  (potentiation)
  Post before pre (Δt < 0): Δw = -a_minus * exp(Δt / tau_minus) (depression)
  Clamp weight to [w_min, w_max]
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class STDParameters:
    """Parameters for STDP learning."""
    a_plus: float = 0.01      # Learning rate for potentiation
    a_minus: float = 0.012    # Learning rate for depression
    tau_plus_ms: float = 20.0 # Time constant for potentiation (ms)
    tau_minus_ms: float = 20.0 # Time constant for depression (ms)
    w_min: float = 0.0        # Minimum synapse weight
    w_max: float = 1.0        # Maximum synapse weight


class STDPLearner:
    """Spike-Timing Dependent Plasticity learner."""
    
    def __init__(self, params: Optional[STDParameters] = None):
        self.params = params or STDParameters()
    
    def compute_weight_change(self, delta_t_ms: float) -> float:
        """Compute weight change based on spike timing difference.
        
        Args:
            delta_t_ms: Time difference between pre- and post-synaptic spikes
                        Positive = pre before post (potentiation)
                        Negative = post before pre (depression)
                        
        Returns:
            Weight change (positive = strengthen, negative = weaken)
        """
        a_plus = self.params.a_plus
        a_minus = self.params.a_minus
        tau_plus = self.params.tau_plus_ms
        tau_minus = self.params.tau_minus_ms
        
        if delta_t_ms > 0:
            # Pre before post: potentiation (strengthen)
            # Δw = a_plus * exp(-Δt / tau_plus)
            dw = a_plus * math.exp(-delta_t_ms / tau_plus)
        else:
            # Post before pre: depression (weaken)
            # Δw = -a_minus * exp(Δt / tau_minus)
            dw = -a_minus * math.exp(delta_t_ms / tau_minus)
        
        return dw
    
    def update_weight(self, current_weight: float, delta_t_ms: float) -> float:
        """Update synapse weight using STDP rule.
        
        Args:
            current_weight: Current synapse weight
            delta_t_ms: Time difference between pre- and post-synaptic spikes
            
        Returns:
            New weight clamped to [w_min, w_max]
        """
        dw = self.compute_weight_change(delta_t_ms)
        new_weight = current_weight + dw
        
        # Clamp to [w_min, w_max]
        return max(self.params.w_min, min(self.params.w_max, new_weight))
    
    def potentate(self, current_weight: float, delta_t_ms: float = 10.0) -> float:
        """Apply potentiation (strengthening) to synapse.
        
        Used for Hebbian teaching: when post fires after pre,
        we strengthen the connection.
        
        Args:
            current_weight: Current synapse weight
            delta_t_ms: Time since pre-synaptic spike (ms), default 10ms
            
        Returns:
            New potentiated weight
        """
        # Positive delta_t -> potentiation
        return self.update_weight(current_weight, delta_t_ms)
    
    def depress(self, current_weight: float, delta_t_ms: float = -10.0) -> float:
        """Apply depression (weakening) to synapse.
        
        Used when post fires before pre (anti-Hebbian).
        
        Args:
            current_weight: Current synapse weight
            delta_t_ms: Negative time since post-synaptic spike (ms)
            
        Returns:
            New depressed weight
        """
        # Negative delta_t -> depression
        return self.update_weight(current_weight, delta_t_ms)
    
    @staticmethod
    def hebbian_factor(delta_t_ms: float, tau: float = 20.0) -> float:
        """Compute simple Hebbian factor: exp(-|Δt|/tau).
        
        Simplified version for quick checks.
        
        Args:
            delta_t_ms: Spike timing difference
            tau: Time constant
            
        Returns:
            Factor in range [0, 1]
        """
        return math.exp(-abs(delta_t_ms) / tau)