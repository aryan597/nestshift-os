"""System Agent for simulation.

Monitors drift and system health.
"""

import numpy as np
from typing import Dict, List
from collections import deque


class DriftDetector:
    """Detects model performance degradation."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.errors = {
            "energy": deque(maxlen=window_size),
            "automation": deque(maxlen=window_size),
        }
        self.thresholds = {"energy": 0.15, "automation": 0.25}
        self.drift_events = []

    def record(self, agent: str, error: float):
        self.errors[agent].append(error)

    def check(self, agent: str) -> bool:
        if len(self.errors[agent]) < 20:
            return False
        mean_error = np.mean(list(self.errors[agent]))
        return mean_error > self.thresholds[agent]

    def get_status(self) -> Dict[str, bool]:
        return {
            "energy_drift": self.check("energy"),
            "automation_drift": self.check("automation"),
            "energy_error": np.mean(list(self.errors["energy"])) if self.errors["energy"] else 0,
            "automation_error": np.mean(list(self.errors["automation"])) if self.errors["automation"] else 0,
        }


class SystemAgent:
    """System-level monitoring and lifecycle management."""

    def __init__(self):
        self.drift_detector = DriftDetector()
        self.retrain_count = 0
        self.health_checks = 0

    def monitor(self, energy_error: float, automation_error: float) -> dict:
        self.drift_detector.record("energy", energy_error)
        self.drift_detector.record("automation", automation_error)
        self.health_checks += 1

        status = self.drift_detector.get_status()

        if status["energy_drift"] or status["automation_drift"]:
            self.retrain_count += 1
            return {
                "drift_detected": True,
                "retrain_triggered": True,
                **status,
            }

        return {
            "drift_detected": False,
            "retrain_triggered": False,
            **status,
        }

    def get_metrics(self) -> dict:
        return {
            "retrain_count": self.retrain_count,
            "health_checks": self.health_checks,
            **self.drift_detector.get_status(),
        }
