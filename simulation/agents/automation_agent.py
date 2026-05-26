"""Automation Agent for simulation.

Learns occupant behavior patterns and proposes autonomous actions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class BehaviourModel:
    """Hour-of-day behavioral pattern model."""

    def __init__(self, confidence_threshold: float = 0.75,
                 min_events: int = 72):
        self.patterns = defaultdict(lambda: defaultdict(int))
        self.total_events = 0
        self.confidence_threshold = confidence_threshold
        self.min_events = min_events
        self.hourly_counts = defaultdict(int)

    def record(self, hour: int, device: str, action: str):
        key = f"{device}:{action}"
        self.patterns[hour][key] += 1
        self.total_events += 1
        self.hourly_counts[hour] += 1

    def predict(self, hour: int) -> Optional[Dict]:
        if self.total_events < self.min_events:
            return None

        hour_patterns = self.patterns[hour]
        if not hour_patterns:
            return None

        total = sum(hour_patterns.values())
        best_action = None
        best_prob = 0.0

        for action, count in hour_patterns.items():
            prob = count / total
            if prob > best_prob and prob >= self.confidence_threshold:
                best_prob = prob
                best_action = action

        if best_action:
            device, action = best_action.split(":")
            return {
                "device": device,
                "action": action,
                "confidence": best_prob,
                "hour": hour,
            }

        return None

    def get_confidence(self) -> float:
        if self.total_events < self.min_events:
            return 0.0
        return min(1.0, self.total_events / 2000)


class RuleEngine:
    """Safety rule engine."""

    def validate(self, action: dict, state: dict) -> bool:
        device = action.get("device", "")

        # HVAC bounds
        if device == "hvac" and action.get("action") == "set_temp":
            temp = action.get("value", 20)
            if not (16 <= temp <= 26):
                return False

        # Don't turn off security if occupied
        if device in ["security", "alarm"] and action.get("action") == "turn_off":
            if state.get("occupied", False):
                return False

        # Max 3 high-power devices
        if action.get("action") in ["turn_on", "start"]:
            running = state.get("high_power_count", 0)
            if running >= 3 and device in ["ev_charger", "water_heater", "hvac"]:
                return False

        return True


class AutomationAgent:
    """Autonomous behavior learning agent."""

    def __init__(self):
        self.behaviour_model = BehaviourModel()
        self.rule_engine = RuleEngine()
        self.autonomous_actions_taken = 0
        self.blocked_actions = 0
        self.user_overrides = 0

    def learn(self, state: dict, user_action: dict):
        """Learn from observed user actions."""
        hour = int(state["hour"])
        device = user_action.get("device", "")
        action = user_action.get("action", "")
        if device and action:
            self.behaviour_model.record(hour, device, action)

    def act(self, state: dict) -> Optional[Dict]:
        """Propose autonomous action if confident."""
        hour = int(state["hour"])
        prediction = self.behaviour_model.predict(hour)

        if prediction is None:
            return None

        action = {
            "device": prediction["device"],
            "action": prediction["action"],
            "confidence": prediction["confidence"],
            "source": "autonomous",
        }

        if self.rule_engine.validate(action, state):
            self.autonomous_actions_taken += 1
            return action
        else:
            self.blocked_actions += 1
            return None

    def get_metrics(self) -> dict:
        conf = self.behaviour_model.get_confidence()
        total = self.autonomous_actions_taken + self.blocked_actions
        success_rate = (self.autonomous_actions_taken / total) if total > 0 else 0
        return {
            "confidence": conf,
            "autonomous_actions": self.autonomous_actions_taken,
            "blocked_actions": self.blocked_actions,
            "success_rate": success_rate,
            "total_events": self.behaviour_model.total_events,
        }
