"""Synapse Registry with SQLite persistence and 30-day pruning.

Synapse connects pre_topic (sensor) → post_topic (device actuator)
  weight starts at 0.1 for new pairs, persisted in SQLite
  neural_trace: list of activation dicts (full audit log)
  Auto-create on first observation of new sensor/device pair
  Prune weight < 0.01 after 30 days inactive
  Persist weights to SQLite every 60 seconds
"""

import sqlite3
import threading
import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from collections import deque


# Default configuration
DEFAULT_INITIAL_WEIGHT = 0.1
DEFAULT_PRUNE_THRESHOLD = 0.01
DEFAULT_PRUNE_DAYS = 30
DEFAULT_PERSIST_INTERVAL_SEC = 60


@dataclass
class Synapse:
    """A synapse connection from sensor (pre) to device (post)."""
    pre_topic: str           # Sensor topic e.g., sensors/motion/living_room
    post_topic: str          # Device topic e.g., devices/light/living_room
    weight: float = DEFAULT_INITIAL_WEIGHT
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active_at: str = field(default_factory=lambda: datetime.now().isoformat())
    spike_count: int = 0
    
    @property
    def synapse_id(self) -> str:
        return f"{self.pre_topic}|{self.post_topic}"


@dataclass
class NeuralTraceEntry:
    """Single neural trace entry for XAI audit log."""
    timestamp: str
    pre_topic: str
    post_topic: str
    pre_spike_time_ms: Optional[float]
    post_spike_time_ms: Optional[float]
    synapse_weight: float
    delta_t_ms: Optional[float]
    action_taken: str
    trigger: str  # 'autonomous' or 'manual_override'
    membrane_potential_mv: float


class SynapseRegistry:
    """Registry managing all sensor→device synapses with persistence."""
    
    def __init__(self, db_path: str = "brain/synapses.db",
                 initial_weight: float = DEFAULT_INITIAL_WEIGHT,
                 prune_threshold: float = DEFAULT_PRUNE_THRESHOLD,
                 prune_days: int = DEFAULT_PRUNE_DAYS,
                 persist_interval_sec: int = DEFAULT_PERSIST_INTERVAL_SEC):
        self.db_path = db_path
        self.initial_weight = initial_weight
        self.prune_threshold = prune_threshold
        self.prune_days = prune_days
        self.persist_interval_sec = persist_interval_sec
        
        # In-memory cache of synapses
        self._synapses: dict[str, Synapse] = {}
        
        # Neural trace for XAI (full audit log)
        self._neural_trace: deque = deque(maxlen=10000)
        
        # Track recently spiked neurons for teaching
        self._recent_spikes: dict[str, float] = {}  # neuron_id -> timestamp_ms
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Persistence timer
        self._last_persist_time = time.time()
        self._persist_dirty = False
        
        # Ensure DB directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize DB
        self._init_db()
        
        # Load persisted synapses
        self._load_synapses()
    
    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Synapses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS synapses (
                pre_topic TEXT NOT NULL,
                post_topic TEXT NOT NULL,
                weight REAL NOT NULL,
                created_at TEXT NOT NULL,
                last_active_at TEXT NOT NULL,
                spike_count INTEGER DEFAULT 0,
                PRIMARY KEY (pre_topic, post_topic)
            )
        """)
        
        # Neural trace table for XAI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS neural_trace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pre_topic TEXT NOT NULL,
                post_topic TEXT NOT NULL,
                pre_spike_time_ms REAL,
                post_spike_time_ms REAL,
                synapse_weight REAL NOT NULL,
                delta_t_ms REAL,
                action_taken TEXT NOT NULL,
                trigger TEXT NOT NULL,
                membrane_potential_mv REAL NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_synapses(self):
        """Load synapses from SQLite into memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT pre_topic, post_topic, weight, created_at, last_active_at, spike_count FROM synapses")
        
        for row in cursor.fetchall():
            synapse = Synapse(
                pre_topic=row[0],
                post_topic=row[1],
                weight=row[2],
                created_at=row[3],
                last_active_at=row[4],
                spike_count=row[5],
            )
            self._synapses[synapse.synapse_id] = synapse
        
        conn.close()
    
    def _persist_if_needed(self):
        """Persist to SQLite if dirty and interval elapsed."""
        now = time.time()
        if not self._persist_dirty and (now - self._last_persist_time) < self.persist_interval_sec:
            return
        
        if self._persist_dirty:
            self._persist_synapses()
            self._last_persist_time = now
            self._persist_dirty = False
    
    def _persist_synapses(self):
        """Write all synapses to SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for synapse in self._synapses.values():
            cursor.execute("""
                INSERT OR REPLACE INTO synapses 
                (pre_topic, post_topic, weight, created_at, last_active_at, spike_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (synapse.pre_topic, synapse.post_topic, synapse.weight,
                  synapse.created_at, synapse.last_active_at, synapse.spike_count))
        
        conn.commit()
        conn.close()
    
    def get_or_create(self, pre_topic: str, post_topic: str) -> Synapse:
        """Get existing synapse or create new one.
        
        Auto-creates on first observation of new sensor/device pair.
        Initial weight is 0.1 for new synapses.
        """
        with self._lock:
            synapse_id = f"{pre_topic}|{post_topic}"
            
            if synapse_id in self._synapses:
                synapse = self._synapses[synapse_id]
                synapse.last_active_at = datetime.now().isoformat()
                self._persist_dirty = True
                return synapse
            
            # Create new synapse
            synapse = Synapse(
                pre_topic=pre_topic,
                post_topic=post_topic,
                weight=self.initial_weight,
            )
            self._synapses[synapse_id] = synapse
            self._persist_dirty = True
            
            return synapse
    
    def update_weight(self, pre_topic: str, post_topic: str, new_weight: float):
        """Update synapse weight and mark dirty."""
        with self._lock:
            synapse_id = f"{pre_topic}|{post_topic}"
            if synapse_id in self._synapses:
                self._synapses[synapse_id].weight = new_weight
                self._synapses[synapse_id].last_active_at = datetime.now().isoformat()
                self._synapses[synapse_id].spike_count += 1
                self._persist_dirty = True
    
    def get_synapse(self, pre_topic: str, post_topic: str) -> Optional[Synapse]:
        """Get synapse by topics."""
        with self._lock:
            synapse_id = f"{pre_topic}|{post_topic}"
            return self._synapses.get(synapse_id)
    
    def get_synapses_from_sensor(self, pre_topic: str) -> list[Synapse]:
        """Get all synapses where this sensor is the pre-topic."""
        with self._lock:
            return [s for s in self._synapses.values() if s.pre_topic == pre_topic]
    
    def get_strong_synapses(self, threshold: float = 0.65) -> list[Synapse]:
        """Get all synapses above activation threshold."""
        with self._lock:
            return [s for s in self._synapses.values() if s.weight >= threshold]
    
    def get_all_synapses(self) -> list[Synapse]:
        """Get all synapses."""
        with self._lock:
            return list(self._synapses.values())
    
    def add_neural_trace(self, entry: NeuralTraceEntry):
        """Add entry to neural trace (audit log)."""
        with self._lock:
            self._neural_trace.append(entry)
            
            # Also persist to DB
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO neural_trace 
                (timestamp, pre_topic, post_topic, pre_spike_time_ms, post_spike_time_ms,
                 synapse_weight, delta_t_ms, action_taken, trigger, membrane_potential_mv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry.timestamp, entry.pre_topic, entry.post_topic, entry.pre_spike_time_ms,
                  entry.post_spike_time_ms, entry.synapse_weight, entry.delta_t_ms,
                  entry.action_taken, entry.trigger, entry.membrane_potential_mv))
            conn.commit()
            conn.close()
    
    def get_neural_trace(self, limit: int = 100) -> list[dict]:
        """Get recent neural trace entries."""
        with self._lock:
            entries = list(self._neural_trace)[-limit:]
            return [asdict(e) for e in entries]
    
    def record_spike(self, neuron_id: str, timestamp_ms: float):
        """Record a neuron spike for teaching calculations."""
        with self._lock:
            self._recent_spikes[neuron_id] = timestamp_ms
    
    def get_recent_spikes(self, within_ms: float = 500.0, 
                         current_time_ms: float = None) -> dict[str, float]:
        """Get neurons that spiked within the last X ms."""
        if current_time_ms is None:
            current_time_ms = time.time() * 1000
        
        with self._lock:
            return {
                nid: ts for nid, ts in self._recent_spikes.items()
                if (current_time_ms - ts) <= within_ms
            }
    
    def prune_old_synapses(self) -> int:
        """Remove synapses with weight < 0.01 after 30 days inactive.
        
        Returns:
            Number of synapses pruned
        """
        with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(days=self.prune_days)
            pruned = []
            
            for synapse_id, synapse in self._synapses.items():
                last_active = datetime.fromisoformat(synapse.last_active_at)
                if last_active < cutoff and synapse.weight < self.prune_threshold:
                    pruned.append(synapse_id)
            
            for sid in pruned:
                del self._synapses[sid]
            
            if pruned:
                # Rebuild DB without pruned synapses
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for sid in pruned:
                    parts = sid.split("|")
                    cursor.execute(
                        "DELETE FROM synapses WHERE pre_topic = ? AND post_topic = ?",
                        (parts[0], parts[1])
                    )
                conn.commit()
                conn.close()
                self._persist_dirty = True
            
            return len(pruned)
    
    def get_stats(self) -> dict:
        """Get registry statistics."""
        with self._lock:
            synapses = list(self._synapses.values())
            total = len(synapses)
            strong = len([s for s in synapses if s.weight >= 0.65])
            weak = len([s for s in synapses if s.weight < 0.01])
            
            return {
                "total_synapses": total,
                "strong_synapses": strong,
                "weak_synapses": weak,
                "active_today": len([s for s in synapses 
                                    if datetime.fromisoformat(s.last_active_at).date() == datetime.now().date()]),
            }
    
    def close(self):
        """Ensure final persistence and close."""
        if self._persist_dirty:
            self._persist_synapses()
        # Close any DB connections if needed