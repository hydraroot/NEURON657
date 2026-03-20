#!/usr/bin/env python3
"""
NEURON657 - General-Purpose Cognitive Architecture

Copyright (c) 2026 Walter Diego Spaltro

NEURON657 is dual-licensed:

1. Open Source License:
   This program is licensed under the GNU Affero General Public License v3.0 (AGPLv3).
   You may use, modify, and distribute this software under the terms of the AGPL.
   If you run this software as part of a service, you must make the source code available.

2. Commercial License:
   A commercial license is available for use in proprietary software or environments
   where AGPL requirements cannot be met (e.g., closed-source applications, SaaS).

   The commercial license allows:
   - Use in closed-source products
   - No obligation to disclose source code
   - Integration into commercial environments

For commercial licensing inquiries:
Contact: wds657@hotmail.com

---

Author: Walter Diego Spaltro
Project: NEURON657
Version: 13.2

Description:
NEURON657 is a cognitive architecture for adaptive decision-making based on
internal state dynamics (uncertainty, prediction error, and meta-cognitive evaluation).

Behavior emerges from the interaction of modular subsystems including:
world model, memory, strategy selection, and planning.

---

Note:
This implementation is provided as a reference architecture.
Contributions are welcome under the terms defined in the repository (CLA required).
"""

import os
import sys
import math
import time
import json
import pickle
import zlib
import lzma
import bz2
import random
import struct
import hashlib
import logging
import warnings
import threading
import itertools
import concurrent.futures
import io
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any, Union, BinaryIO, Callable, Set
from dataclasses import dataclass, field, asdict, FrozenInstanceError
from collections import OrderedDict, defaultdict, deque
from contextlib import contextmanager
from heapq import nlargest
import shutil
import csv
import asyncio
import inspect
import signal
import importlib.util
import websockets
import traceback
from functools import lru_cache
from abc import ABC, abstractmethod

# ============================================
# LOGGING CONFIGURATION
# ============================================
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ============================================
# REPRODUCIBLE RANDOM - Seeded Instance
# ============================================
_rng = random.Random()

def set_random_seed(seed: int) -> None:
    _rng.seed(seed)
    logger.debug("Random seed set to %s", seed)

# ============================================
# CORE ENUMS - Formal Definitions
# ============================================

class CognitiveMode(Enum):
    AUTONOMOUS = "autonomous"
    REASONING = "reasoning"
    ASSISTANT = "assistant"
    SIMULATION = "simulation"
    INTEGRATED = "integrated"
    ADAPTIVE = "adaptive"
    SAFE_RECOVERY = "safe_recovery"
    META_LEARNING = "meta_learning"

class SystemStatus(Enum):
    STABLE = "stable"
    DEGRADED = "degraded"
    RECOVERY = "recovery"
    LEARNING = "learning"
    MAINTENANCE = "maintenance"

class TransitionType(Enum):
    MODE_CHANGE = "mode_change"
    STATUS_CHANGE = "status_change"
    STRATEGY_UPDATE = "strategy_update"
    METRICS_UPDATE = "metrics_update"
    ROLLBACK = "rollback"
    HEARTBEAT = "heartbeat"

# ============================================
# HDC VECTOR - Type Safe
# ============================================

class HDCVector:
    __slots__ = ('_vector', '_dimensions', '_hash')
    def __init__(self, vector: List[int]):
        if not isinstance(vector, list):
            raise TypeError(f"HDCVector requires list, got {type(vector)}")
        for i, val in enumerate(vector):
            if not isinstance(val, int):
                raise TypeError(f"HDCVector element at index {i} must be int, got {type(val)}")
        self._vector = vector.copy()
        self._dimensions = len(vector)
        self._hash = hash(tuple(vector))
    def __len__(self) -> int:
        return self._dimensions
    def __getitem__(self, index: Union[int, slice]) -> Union[int, List[int]]:
        if isinstance(index, slice):
            return self._vector[index]
        return self._vector[index]
    def __iter__(self):
        return iter(self._vector)
    def __repr__(self) -> str:
        return f"HDCVector(dimensions={self._dimensions})"
    def __hash__(self) -> int:
        return self._hash
    def __eq__(self, other) -> bool:
        if not isinstance(other, HDCVector):
            return False
        return self._vector == other._vector
    def to_list(self) -> List[int]:
        return self._vector.copy()
    @property
    def dimensions(self) -> int:
        return self._dimensions

# ============================================
# METRICS MANAGER - Immutable Snapshots
# ============================================

@dataclass(frozen=True)
class MetricsSnapshot:
    timestamp: float
    avg_confidence: float
    error_rate_1min: float
    avg_decision_time_ms: float
    stm_utilization: float
    cache_hit_rate: float
    memory_pressure: float
    failure_risk: float
    operation_success_rate: float
    pattern_count: int
    uptime_seconds: float
    ltm_pattern_count: int
    # new in v13.0
    free_energy: float = 0.0
    prediction_error: float = 0.0
    model_uncertainty: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "timestamp": self.timestamp,
            "avg_confidence": self.avg_confidence,
            "error_rate_1min": self.error_rate_1min,
            "avg_decision_time_ms": self.avg_decision_time_ms,
            "stm_utilization": self.stm_utilization,
            "cache_hit_rate": self.cache_hit_rate,
            "memory_pressure": self.memory_pressure,
            "failure_risk": self.failure_risk,
            "operation_success_rate": self.operation_success_rate,
            "pattern_count": float(self.pattern_count),
            "uptime_seconds": self.uptime_seconds,
            "ltm_pattern_count": float(self.ltm_pattern_count),
            "free_energy": self.free_energy,
            "prediction_error": self.prediction_error,
            "model_uncertainty": self.model_uncertainty
        }
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'MetricsSnapshot':
        return cls(
            timestamp=data["timestamp"],
            avg_confidence=data["avg_confidence"],
            error_rate_1min=data["error_rate_1min"],
            avg_decision_time_ms=data["avg_decision_time_ms"],
            stm_utilization=data["stm_utilization"],
            cache_hit_rate=data["cache_hit_rate"],
            memory_pressure=data["memory_pressure"],
            failure_risk=data["failure_risk"],
            operation_success_rate=data["operation_success_rate"],
            pattern_count=int(data["pattern_count"]),
            uptime_seconds=data["uptime_seconds"],
            ltm_pattern_count=int(data["ltm_pattern_count"]),
            free_energy=data.get("free_energy", 0.0),
            prediction_error=data.get("prediction_error", 0.0),
            model_uncertainty=data.get("model_uncertainty", 0.0)
        )
    @classmethod
    def empty(cls) -> 'MetricsSnapshot':
        return cls(
            timestamp=time.time(),
            avg_confidence=0.5,
            error_rate_1min=0.0,
            avg_decision_time_ms=0.0,
            stm_utilization=0.0,
            cache_hit_rate=0.0,
            memory_pressure=0.0,
            failure_risk=0.0,
            operation_success_rate=1.0,
            pattern_count=0,
            uptime_seconds=0.0,
            ltm_pattern_count=0
        )

class IMetricsCollector:
    def current(self) -> MetricsSnapshot:
        raise NotImplementedError
    def history(self, limit: Optional[int] = None) -> List[MetricsSnapshot]:
        raise NotImplementedError
    def update(self, **kwargs) -> MetricsSnapshot:
        raise NotImplementedError

class MetricsManager(IMetricsCollector):
    def __init__(self, max_history: int = 1000):
        self._history: deque = deque(maxlen=max_history)
        self._max_history = max_history
        self._current = MetricsSnapshot.empty()
        self._lock = threading.RLock()
        self._display_cache: Dict[str, str] = {}
        self._cache_time = 0
        logger.info("MetricsManager initialized with immutable snapshots")
    def update(self, **kwargs) -> MetricsSnapshot:
        with self._lock:
            valid_fields = {
                "avg_confidence", "error_rate_1min", "avg_decision_time_ms",
                "stm_utilization", "cache_hit_rate", "memory_pressure",
                "failure_risk", "operation_success_rate", "pattern_count",
                "uptime_seconds", "ltm_pattern_count", "free_energy",
                "prediction_error", "model_uncertainty"
            }
            prefix_map = {
                "confidence": "avg_confidence",
                "error_rate": "error_rate_1min",
                "decision_time": "avg_decision_time_ms",
                "memory_pressure": "memory_pressure"
            }
            current_dict = self._current.to_dict()
            for key, value in kwargs.items():
                if key in prefix_map:
                    key = prefix_map[key]
                if key not in valid_fields:
                    logger.warning(f"Ignoring unknown metric: {key}")
                    continue
                try:
                    if key in ["pattern_count", "ltm_pattern_count"]:
                        num_value = float(int(value))
                    else:
                        num_value = float(value)
                    if key in ["avg_confidence", "error_rate_1min", "stm_utilization",
                              "cache_hit_rate", "memory_pressure", "failure_risk",
                              "operation_success_rate"]:
                        num_value = max(0.0, min(1.0, num_value))
                    current_dict[key] = num_value
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid value for {key}: {value} - {e}")
                    continue
            snapshot = MetricsSnapshot(
                timestamp=time.time(),
                avg_confidence=current_dict["avg_confidence"],
                error_rate_1min=current_dict["error_rate_1min"],
                avg_decision_time_ms=current_dict["avg_decision_time_ms"],
                stm_utilization=current_dict["stm_utilization"],
                cache_hit_rate=current_dict["cache_hit_rate"],
                memory_pressure=current_dict["memory_pressure"],
                failure_risk=current_dict["failure_risk"],
                operation_success_rate=current_dict["operation_success_rate"],
                pattern_count=int(current_dict["pattern_count"]),
                uptime_seconds=current_dict["uptime_seconds"],
                ltm_pattern_count=int(current_dict["ltm_pattern_count"]),
                free_energy=current_dict.get("free_energy", 0.0),
                prediction_error=current_dict.get("prediction_error", 0.0),
                model_uncertainty=current_dict.get("model_uncertainty", 0.0)
            )
            self._history.append(snapshot)
            self._current = snapshot
            self._display_cache.clear()
            return snapshot
    def current(self) -> MetricsSnapshot:
        with self._lock:
            return self._current
    def history(self, limit: Optional[int] = None) -> List[MetricsSnapshot]:
        with self._lock:
            history_list = list(self._history)
            if limit is None:
                return history_list
            return history_list[-limit:]
    def get_for_decision(self, metric_names: List[str]) -> Dict[str, float]:
        with self._lock:
            current_dict = self._current.to_dict()
            return {name: current_dict.get(name, 0.0) for name in metric_names}
    def generate_display_metrics(self) -> Dict[str, str]:
        with self._lock:
            if self._display_cache and time.time() - self._cache_time < 1:
                return self._display_cache.copy()
            m = self._current
            display = {
                "avg_confidence": f"{m.avg_confidence:.1%}",
                "error_rate_1min": f"{m.error_rate_1min:.1%}",
                "stm_utilization": f"{m.stm_utilization:.1%}",
                "cache_hit_rate": f"{m.cache_hit_rate:.1%}",
                "memory_pressure": f"{m.memory_pressure:.1%}",
                "failure_risk": f"{m.failure_risk:.1%}",
                "operation_success_rate": f"{m.operation_success_rate:.1%}",
                "avg_decision_time_ms": f"{m.avg_decision_time_ms:.1f}ms",
                "uptime_seconds": self._format_uptime(m.uptime_seconds),
                "pattern_count": str(m.pattern_count),
                "ltm_pattern_count": str(m.ltm_pattern_count),
                "history_size": str(len(self._history)),
                "free_energy": f"{m.free_energy:.3f}",
                "prediction_error": f"{m.prediction_error:.3f}",
                "model_uncertainty": f"{m.model_uncertainty:.3f}"
            }
            self._display_cache = display
            self._cache_time = time.time()
            return display.copy()
    def _format_uptime(self, seconds: float) -> str:
        hours = seconds / 3600
        if hours > 24:
            days = hours / 24
            return f"{days:.1f}d"
        elif hours > 1:
            return f"{hours:.1f}h"
        else:
            return f"{seconds:.0f}s"
    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            return self._current
    def health_check(self) -> Dict[str, Any]:
        with self._lock:
            m = self._current
            issues = []
            recommendations = []
            if m.avg_confidence < 0.3:
                issues.append("Low confidence")
                recommendations.append("Switch to META_LEARNING mode")
            if m.error_rate_1min > 0.2:
                issues.append("High error rate")
                recommendations.append("Switch to SAFE_RECOVERY mode")
            if m.stm_utilization > 0.8:
                issues.append("High memory pressure")
                recommendations.append("Clean STM or increase capacity")
            if m.cache_hit_rate < 0.3:
                issues.append("Low cache efficiency")
                recommendations.append("Rebuild cache or adjust strategy")
            if m.failure_risk > 0.7:
                issues.append("High failure risk")
                recommendations.append("Perform preventive maintenance")
            if m.free_energy > 5.0:   # reduced from 10.0 to 5.0
                issues.append("High free energy")
                recommendations.append("Increase exploration or update world model")
            if any(issue in ["High error rate", "Low confidence", "High failure risk", "High free energy"] 
                   for issue in issues):
                overall = "DEGRADED"
            elif issues:
                overall = "WARNING"
            else:
                overall = "HEALTHY"
            return {
                "timestamp": time.time(),
                "overall": overall,
                "issues": issues,
                "recommendations": recommendations
            }
    def get_trend(self, metric_name: str, window_seconds: int = 300) -> Dict[str, Any]:
        with self._lock:
            cutoff = time.time() - window_seconds
            relevant = [s for s in self._history if s.timestamp > cutoff]
            if not relevant:
                return {"available": False, "message": "No data in window"}
            values = []
            for snap in relevant:
                try:
                    values.append(getattr(snap, metric_name))
                except AttributeError:
                    dict_val = snap.to_dict().get(metric_name)
                    if dict_val is not None:
                        values.append(dict_val)
            if not values:
                return {"available": False, "message": f"Metric {metric_name} not found"}
            return {
                "available": True,
                "current": values[-1],
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "trend": "up" if values[-1] > values[0] else "down",
                "samples": len(values),
                "window_seconds": window_seconds
            }
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "metrics_tracked": len(MetricsSnapshot.__annotations__),
                "history_size": len(self._history),
                "numeric_metrics": self._current.to_dict(),
                "health_status": self.health_check()
            }

# ============================================
# COGNITIVE STATE - Immutable Value Object
# ============================================

@dataclass(frozen=True)
class CognitiveState:
    state_id: str = field(default_factory=lambda: f"state_{time.time_ns()}_{hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]}")
    version: str = "v13.2"   # updated version
    mode: CognitiveMode = CognitiveMode.AUTONOMOUS
    status: SystemStatus = SystemStatus.STABLE
    active_goal: Optional[str] = None
    confidence_level: float = 0.5
    active_pattern_hashes: Tuple[str, ...] = field(default_factory=tuple)
    active_context: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    attention_stack: Tuple[str, ...] = field(default_factory=tuple)
    ltm_pattern_count: int = 0
    stm_utilization: float = 0.0
    cache_hit_rate: float = 0.0
    current_strategy: str = "hybrid"
    strategy_confidence: Tuple[Tuple[str, float], ...] = field(
        default_factory=lambda: (("hybrid", 0.5), ("byte", 0.3), ("hdv", 0.3), ("semantic", 0.3))
    )
    creation_timestamp: float = field(default_factory=time.time)
    last_activity_timestamp: float = field(default_factory=time.time)
    uptime_cycles: int = 0
    error_rate_1min: float = 0.0
    avg_decision_time_ms: float = 0.0
    # new in v13.0
    free_energy: float = 0.0

    def __post_init__(self):
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueError(f"Confidence must be in [0,1], got {self.confidence_level}")
        if not (0.0 <= self.stm_utilization <= 1.0):
            raise ValueError(f"STM utilization must be in [0,1], got {self.stm_utilization}")
        if not (0.0 <= self.cache_hit_rate <= 1.0):
            raise ValueError(f"Cache hit rate must be in [0,1], got {self.cache_hit_rate}")
        if not (0.0 <= self.error_rate_1min <= 1.0):
            raise ValueError(f"Error rate must be in [0,1], got {self.error_rate_1min}")

    def with_updates(self, **changes) -> 'CognitiveState':
        valid_fields = {
            'mode', 'status', 'active_goal', 'confidence_level',
            'active_pattern_hashes', 'active_context', 'attention_stack',
            'ltm_pattern_count', 'stm_utilization', 'cache_hit_rate',
            'current_strategy', 'strategy_confidence', 'last_activity_timestamp',
            'uptime_cycles', 'error_rate_1min', 'avg_decision_time_ms',
            'free_energy'
        }
        for key in changes:
            if key not in valid_fields:
                raise ValueError(f"Cannot update field: {key}")
        if 'active_pattern_hashes' in changes:
            val = changes['active_pattern_hashes']
            if isinstance(val, set):
                changes['active_pattern_hashes'] = tuple(sorted(val))
            elif isinstance(val, list):
                changes['active_pattern_hashes'] = tuple(val)
        if 'active_context' in changes:
            val = changes['active_context']
            if isinstance(val, dict):
                changes['active_context'] = tuple(sorted(val.items()))
            elif isinstance(val, list):
                changes['active_context'] = tuple(val)
        if 'attention_stack' in changes:
            val = changes['attention_stack']
            if isinstance(val, list):
                changes['attention_stack'] = tuple(val)
        if 'strategy_confidence' in changes:
            val = changes['strategy_confidence']
            if isinstance(val, dict):
                changes['strategy_confidence'] = tuple(sorted(val.items()))
        current_dict = {
            'state_id': f"state_{time.time_ns()}_{hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]}",
            'version': self.version,
            'mode': self.mode,
            'status': self.status,
            'active_goal': self.active_goal,
            'confidence_level': self.confidence_level,
            'active_pattern_hashes': self.active_pattern_hashes,
            'active_context': self.active_context,
            'attention_stack': self.attention_stack,
            'ltm_pattern_count': self.ltm_pattern_count,
            'stm_utilization': self.stm_utilization,
            'cache_hit_rate': self.cache_hit_rate,
            'current_strategy': self.current_strategy,
            'strategy_confidence': self.strategy_confidence,
            'creation_timestamp': self.creation_timestamp,
            'last_activity_timestamp': time.time(),
            'uptime_cycles': self.uptime_cycles + 1,
            'error_rate_1min': self.error_rate_1min,
            'avg_decision_time_ms': self.avg_decision_time_ms,
            'free_energy': self.free_energy
        }
        current_dict.update(changes)
        return CognitiveState(**current_dict)

    def snapshot_serializable(self) -> Dict[str, Any]:
        data = {
            'state_id': self.state_id,
            'version': self.version,
            'mode': self.mode.value,
            'status': self.status.value,
            'active_goal': self.active_goal,
            'confidence_level': self.confidence_level,
            'active_pattern_hashes': list(self.active_pattern_hashes),
            'active_context': dict(self.active_context),
            'attention_stack': list(self.attention_stack),
            'ltm_pattern_count': self.ltm_pattern_count,
            'stm_utilization': self.stm_utilization,
            'cache_hit_rate': self.cache_hit_rate,
            'current_strategy': self.current_strategy,
            'strategy_confidence': dict(self.strategy_confidence),
            'creation_timestamp': self.creation_timestamp,
            'last_activity_timestamp': self.last_activity_timestamp,
            'uptime_cycles': self.uptime_cycles,
            'error_rate_1min': self.error_rate_1min,
            'avg_decision_time_ms': self.avg_decision_time_ms,
            'free_energy': self.free_energy
        }
        return data

    @classmethod
    def from_serializable(cls, data: Dict[str, Any]) -> 'CognitiveState':
        if 'active_pattern_hashes' in data:
            data['active_pattern_hashes'] = tuple(data['active_pattern_hashes'])
        if 'active_context' in data:
            if isinstance(data['active_context'], dict):
                data['active_context'] = tuple(sorted(data['active_context'].items()))
        if 'attention_stack' in data:
            data['attention_stack'] = tuple(data['attention_stack'])
        if 'strategy_confidence' in data:
            if isinstance(data['strategy_confidence'], dict):
                data['strategy_confidence'] = tuple(sorted(data['strategy_confidence'].items()))
        if 'mode' in data and isinstance(data['mode'], str):
            data['mode'] = CognitiveMode(data['mode'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = SystemStatus(data['status'])
        return cls(**data)

    def __hash__(self) -> int:
        return hash((
            self.state_id, self.version, self.mode, self.status,
            self.active_goal, self.confidence_level,
            self.active_pattern_hashes, self.active_context,
            self.attention_stack, self.ltm_pattern_count,
            self.stm_utilization, self.cache_hit_rate,
            self.current_strategy, self.strategy_confidence,
            self.creation_timestamp, self.last_activity_timestamp,
            self.uptime_cycles, self.error_rate_1min,
            self.avg_decision_time_ms, self.free_energy
        ))

    def diff(self, other: 'CognitiveState') -> Dict[str, Tuple[Any, Any]]:
        changes = {}
        for field in [
            'mode', 'status', 'active_goal', 'confidence_level',
            'ltm_pattern_count', 'stm_utilization', 'cache_hit_rate',
            'current_strategy', 'error_rate_1min', 'avg_decision_time_ms',
            'free_energy'
        ]:
            val1 = getattr(self, field)
            val2 = getattr(other, field)
            if val1 != val2:
                changes[field] = (val1, val2)
        if self.active_pattern_hashes != other.active_pattern_hashes:
            changes['active_pattern_hashes'] = (self.active_pattern_hashes, other.active_pattern_hashes)
        if self.active_context != other.active_context:
            changes['active_context'] = (self.active_context, other.active_context)
        if self.attention_stack != other.attention_stack:
            changes['attention_stack'] = (self.attention_stack, other.attention_stack)
        if self.strategy_confidence != other.strategy_confidence:
            changes['strategy_confidence'] = (self.strategy_confidence, other.strategy_confidence)
        return changes

# ============================================
# STATE TRANSITION - Formal Log Entry
# ============================================

@dataclass(frozen=True)
class StateTransition:
    timestamp: float
    transition_type: TransitionType
    from_state: CognitiveState
    to_state: CognitiveState
    reason: str
    author: str = "system"
    transition_id: str = field(default_factory=lambda: f"tr_{time.time_ns()}_{hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:6]}")
    parent_transition_id: Optional[str] = None
    metrics_snapshot: Optional[MetricsSnapshot] = None

    def changes(self) -> Dict[str, Tuple[Any, Any]]:
        return self.from_state.diff(self.to_state)

    def is_significant(self) -> bool:
        return self.transition_type in [
            TransitionType.MODE_CHANGE,
            TransitionType.STATUS_CHANGE,
            TransitionType.ROLLBACK
        ] or bool(self.changes())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'schema_version': '13.2',
            'transition_id': self.transition_id,
            'timestamp': self.timestamp,
            'transition_type': self.transition_type.value,
            'from_state': self.from_state.snapshot_serializable(),
            'to_state': self.to_state.snapshot_serializable(),
            'reason': self.reason,
            'author': self.author,
            'parent_transition_id': self.parent_transition_id,
            'metrics_snapshot': self.metrics_snapshot.to_dict() if self.metrics_snapshot else None,
            'changes': {
                k: [v[0].value if hasattr(v[0], 'value') else v[0],
                    v[1].value if hasattr(v[1], 'value') else v[1]]
                for k, v in self.changes().items()
            }
        }

    @classmethod
    def from_states(cls, from_state: CognitiveState, to_state: CognitiveState,
                   reason: str = "", transition_type: Optional[TransitionType] = None,
                   metrics: Optional[MetricsSnapshot] = None) -> 'StateTransition':
        diff = from_state.diff(to_state)
        if not diff and transition_type is None:
            transition_type = TransitionType.HEARTBEAT
        elif transition_type is None:
            if 'mode' in diff:
                transition_type = TransitionType.MODE_CHANGE
            elif 'status' in diff:
                transition_type = TransitionType.STATUS_CHANGE
            elif 'current_strategy' in diff or 'strategy_confidence' in diff:
                transition_type = TransitionType.STRATEGY_UPDATE
            else:
                transition_type = TransitionType.METRICS_UPDATE
        return cls(
            timestamp=time.time(),
            transition_type=transition_type,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            metrics_snapshot=metrics
        )

# ============================================
# EXPLAINABLE DECISION - Deterministic
# ============================================

class Explanation:
    def __init__(self, decision_class: str, confidence: float,
                 factors: List[Tuple[str, float]], strategy: str,
                 source: str = "cognitive"):
        self.decision_class = decision_class
        self.confidence = confidence
        self.factors = factors
        self.strategy = strategy
        self.source = source
        self.timestamp = time.time()
        self.schema_version = "13.2"
    def summary(self) -> str:
        templates = {
            "CONFIDENT": f"High confidence decision ({self.confidence:.0%}) based on strong pattern similarity and learning history.",
            "WEAK_MATCH": f"Tentative match ({self.confidence:.0%}) with moderate similarity evidence and learning influence.",
            "NO_MEMORY": f"No reliable memory match found ({self.confidence:.0%}); new pattern detected, using learning priors.",
            "UNKNOWN": f"Decision processed with {self.confidence:.0%} confidence using integrated learning."
        }
        base = templates.get(self.decision_class, templates["UNKNOWN"])
        learning_factors = [f for f in self.factors if f[0].startswith("learning_")]
        if learning_factors:
            base += f" Learning contribution: {learning_factors[0][1]:.0%} weight."
        if self.factors:
            factor_texts = []
            for factor_name, value in self.factors[:3]:
                if factor_name.startswith("learning_"):
                    continue
                factor_templates = {
                    "pattern_similarity": f"pattern similarity {value:.0%}",
                    "memory_stability": f"memory stability {value:.0%}",
                    "semantic_alignment": f"semantic tag overlap {value:.0%}",
                    "access_frequency": f"access frequency {value:.0f}",
                    "temporal_recency": f"temporal recency {value:.0%}",
                    "expected_free_energy": f"expected free energy reduction {value:.2f}"
                }
                factor_texts.append(factor_templates.get(factor_name, f"{factor_name} {value:.0%}"))
            if factor_texts:
                return f"{base} Contributing factors: {'; '.join(factor_texts)}. Strategy: {self.strategy}."
        return f"{base} Strategy: {self.strategy}."
    def to_dict(self) -> Dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'timestamp': self.timestamp,
            'decision_class': self.decision_class,
            'confidence': self.confidence,
            'factors': [(f, v) for f, v in self.factors],
            'strategy': self.strategy,
            'source': self.source
        }

class ExplainableDecision:
    def __init__(self):
        self._history: deque = deque(maxlen=100)
        self._max_history = 100
        self.factor_explanations = {
            "similarity": "pattern similarity score of {value:.0%}",
            "stability": "memory stability factor of {value:.0%}",
            "access_frequency": "frequent access pattern ({value:.0f} accesses)",
            "temporal_recency": "recent memory activation ({value:.0%} recency)",
            "semantic_alignment": "semantic tag overlap ({value:.0%} match)",
            "associative_strength": "strong associative links ({value:.0%} strength)",
            "learning_confidence": "learning-based confidence ({value:.0%} from history)",
            "learning_weight": "learning influence weight ({value:.0%})",
            "expected_free_energy": "expected free energy reduction ({value:.2f})"
        }
        logger.info("ExplainableDecision initialized (deterministic with learning)")
    def explain(self, decision: Dict) -> Explanation:
        decision_class = decision.get("decision_class", "UNKNOWN")
        confidence = decision.get("confidence", 0.0)
        strategy = decision.get("strategy", "unknown")
        source = decision.get("source", "cognitive")
        factors = self._extract_factors(decision)
        if "learning_confidence" in decision:
            factors.append(("learning_confidence", decision["learning_confidence"]))
        if "learning_weight" in decision:
            factors.append(("learning_weight", decision["learning_weight"]))
        if "expected_free_energy" in decision:
            factors.append(("expected_free_energy", decision["expected_free_energy"]))
        explanation = Explanation(decision_class, confidence, factors, strategy, source)
        self._history.append(explanation)
        return explanation
    def _extract_factors(self, decision: Dict) -> List[Tuple[str, float]]:
        factors = []
        factor_mapping = {
            "similarity": ("pattern_similarity", 1.0),
            "stability": ("memory_stability", 1.0),
            "access_count": ("access_frequency", 0.01),
            "predictive_weight": ("associative_strength", 1.0),
            "tag_overlap": ("semantic_alignment", 1.0)
        }
        for key, (factor_name, scale) in factor_mapping.items():
            if key in decision:
                value = decision[key]
                if isinstance(value, (int, float)):
                    factors.append((factor_name, value * scale))
        if "last_access" in decision and "first_access" in decision:
            current_time = time.time()
            age = current_time - decision["last_access"]
            max_age = current_time - decision["first_access"]
            if max_age > 0:
                recency = 1.0 - (age / max_age)
                factors.append(("temporal_recency", recency))
        factors.sort(key=lambda x: x[1], reverse=True)
        return factors
    def explain_complex(self, decision: Dict, depth: int = 2) -> Dict[str, Any]:
        base = self.explain(decision)
        detailed = {
            "summary": base.summary(),
            "confidence": base.confidence,
            "decision_class": base.decision_class,
            "factors": base.factors,
            "reasoning_chain": [],
            "alternative_considerations": [],
            "learning_used": decision.get("learning_used", False),
            "learning_confidence": decision.get("learning_confidence", 0.0),
            "schema_version": "13.2"
        }
        if "analysis" in decision:
            for analysis in decision.get("analysis", []):
                detailed["reasoning_chain"].append({
                    "strategy": analysis.get("strategy"),
                    "similarity": analysis.get("similarity"),
                    "confidence": analysis.get("confidence"),
                    "learning_score": analysis.get("learning_score")
                })
        if base.confidence < 0.5:
            detailed["alternative_considerations"] = [
                "Consider broadening search parameters",
                "Evaluate pattern from different modalities",
                "Check temporal associations for context",
                "Assess semantic tag expansions",
                "Review learning history for similar contexts"
            ]
        if base.decision_class == "NO_MEMORY":
            detailed["recommendations"] = [
                "Store as new pattern for future reference",
                "Create semantic tags for better categorization",
                "Establish initial associations with related patterns",
                "Learning system will adapt based on future outcomes"
            ]
        return detailed
    def get_explanation_history(self, limit: Optional[int] = 20) -> List[Dict[str, Any]]:
        if limit is None:
            return [e.to_dict() for e in self._history]
        n = max(0, min(limit, len(self._history)))
        if n == 0:
            return []
        return [e.to_dict() for e in list(self._history)[-n:]]

# ============================================
# META LEARNER - Measurable Adaptation WITH INTEGRATED DECISION MAKING
# ============================================

@dataclass
class StrategyProfile:
    name: str
    base_confidence: float
    success_rate: float = 0.5
    avg_duration: float = 1.0
    usage_count: int = 0
    last_used: float = 0.0
    context_matches: int = 0
    total_score: float = 0.0
    # new in v13.0
    avg_free_energy_reduction: float = 0.0   # average reduction in free energy when used

    @property
    def current_confidence(self) -> float:
        return 0.3 + 0.7 * self.success_rate
    def update(self, success: bool, duration: float, context_score: float, alpha: float = 0.1, free_energy_reduction: float = 0.0):
        self.success_rate = (1 - alpha) * self.success_rate + alpha * (1.0 if success else 0.0)
        self.avg_duration = (1 - alpha) * self.avg_duration + alpha * duration
        self.usage_count += 1
        self.last_used = time.time()
        self.context_matches += 1 if context_score > 0.5 else 0
        self.total_score += context_score
        self.avg_free_energy_reduction = (1 - alpha) * self.avg_free_energy_reduction + alpha * free_energy_reduction
    def score_for_context(self, context: Dict[str, float]) -> float:
        base = self.current_confidence
        if 'memory_pressure' in context:
            pressure = context['memory_pressure']
            if self.name == 'byte':
                base += 0.1 * (1 - pressure)
            elif self.name == 'hdv':
                base -= 0.05 * pressure
            elif self.name == 'semantic' and pressure > 0.7:
                base += 0.05
        if 'pattern_size' in context:
            size = context['pattern_size']
            if self.name == 'semantic' and size > 1000:
                base += 0.1
            elif self.name == 'byte' and size < 100:
                base += 0.1
        if 'error_rate' in context:
            error_rate = context['error_rate']
            if self.name == 'byte' and error_rate > 0.2:
                base += 0.2
        # bonus if strategy historically reduces free energy
        base += self.avg_free_energy_reduction * 0.2
        return max(0.0, min(1.0, base))

class MetaLearner:
    def __init__(self, adaptation_rate: float = 0.1):
        self.adaptation_rate = adaptation_rate
        self.strategy_performance = defaultdict(list)
        self.context_patterns = defaultdict(list)
        self.recommendation_cache = OrderedDict()
        self.profiles: Dict[str, StrategyProfile] = {
            'byte': StrategyProfile('byte', 0.5),
            'hdv': StrategyProfile('hdv', 0.5),
            'semantic': StrategyProfile('semantic', 0.5),
            'hybrid': StrategyProfile('hybrid', 0.6)
        }
        self.strategy_profiles = {
            "byte": {
                "strengths": ["exact_matches", "binary_data"],
                "weaknesses": ["semantic_similarity", "noisy_data"],
                "cost": 1.0
            },
            "hdv": {
                "strengths": ["semantic_similarity", "noisy_data", "pattern_variations"],
                "weaknesses": ["exact_matches", "small_patterns"],
                "cost": 1.5
            },
            "semantic": {
                "strengths": ["tag_based", "categorical", "contextual"],
                "weaknesses": ["binary_data", "untagged_patterns"],
                "cost": 0.8
            },
            "hybrid": {
                "strengths": ["balanced", "robust", "comprehensive"],
                "weaknesses": ["high_cost", "complexity"],
                "cost": 2.0
            }
        }
        self._recommendation_history: List[Tuple[float, str, float, Dict]] = []
        self.learning_weight = 0.7
        self.recency_decay = 1800
        self.learning_thread = threading.Thread(
            target=self._background_learning,
            daemon=True,
            name="MetaLearner"
        )
        self.learning_thread.start()
        logger.info(f"MetaLearner initialized with integrated learning (weight={self.learning_weight})")
    def record_performance(self, strategy: str, context: Dict,
                          performance: Dict) -> None:
        key = self._context_to_key(context)
        score = self._calculate_performance_score(performance)
        free_energy_reduction = performance.get('free_energy_reduction', 0.0)
        if strategy in self.profiles:
            old_success_rate = self.profiles[strategy].success_rate
            success = performance.get('success', score > 0.6)
            duration = performance.get('duration', 1.0)
            self.profiles[strategy].update(success, duration, score, self.adaptation_rate, free_energy_reduction)
            new_success_rate = self.profiles[strategy].success_rate
            if abs(new_success_rate - old_success_rate) > 0.05:
                logger.debug(f"Significant performance change for '{strategy}' "
                             f"({old_success_rate:.3f} → {new_success_rate:.3f}): "
                             f"invalidating recommendation cache")
                self.recommendation_cache.clear()
        self.strategy_performance[strategy].append({
            "score": score,
            "context_key": key,
            "context": context.copy(),
            "timestamp": time.time(),
            "details": performance,
            "free_energy_reduction": free_energy_reduction
        })
        if len(self.strategy_performance[strategy]) > 1000:
            self.strategy_performance[strategy].pop(0)
        self.context_patterns[key].append({
            "strategy": strategy,
            "score": score,
            "timestamp": time.time()
        })
        logger.debug(f"Recorded performance: {strategy} score={score:.3f} fe_red={free_energy_reduction:.3f}")
    def recommend_strategy(self, context: Dict) -> str:
        context_key = self._context_to_key(context)
        if context_key in self.recommendation_cache:
            entry = self.recommendation_cache[context_key]
            if time.time() - entry["timestamp"] < 300:
                self.recommendation_cache.move_to_end(context_key)
                logger.debug(f"Cache hit for context {context_key}: {entry['strategy']}")
                return entry["strategy"]
        context_profile = self._analyze_context(context)
        strategy_scores = {}
        learning_scores = {}
        heuristic_scores = {}
        for strategy_name, profile in self.profiles.items():
            heuristic_score = profile.score_for_context(context_profile)
            learning_score = self._get_learning_score(strategy_name, context_profile)
            combined_score = (self.learning_weight * learning_score + 
                            (1 - self.learning_weight) * heuristic_score)
            strategy_scores[strategy_name] = max(0.0, min(1.0, combined_score))
            learning_scores[strategy_name] = learning_score
            heuristic_scores[strategy_name] = heuristic_score
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
        self.recommendation_cache[context_key] = {
            "strategy": best_strategy,
            "score": strategy_scores[best_strategy],
            "learning_score": learning_scores[best_strategy],
            "heuristic_score": heuristic_scores[best_strategy],
            "timestamp": time.time(),
            "context_profile": context_profile,
            "learning_weight": self.learning_weight
        }
        if len(self.recommendation_cache) > 1000:
            self.recommendation_cache.popitem(last=False)
        self._recommendation_history.append((
            time.time(),
            best_strategy,
            strategy_scores[best_strategy],
            context_profile
        ))
        logger.debug(f"MetaLearner recommended: {best_strategy} (learning={learning_scores[best_strategy]:.3f}, heuristic={heuristic_scores[best_strategy]:.3f})")
        return best_strategy
    def get_strategy_confidence(self, strategy: str, context: Dict) -> float:
        if strategy not in self.profiles:
            return 0.5
        profile = self.profiles[strategy]
        context_profile = self._analyze_context(context)
        base = profile.current_confidence
        learning_score = self._get_learning_score(strategy, context_profile)
        return 0.6 * learning_score + 0.4 * base
    def get_learning_contribution(self, strategy: str, context: Dict) -> Dict[str, float]:
        context_profile = self._analyze_context(context)
        learning_score = self._get_learning_score(strategy, context_profile)
        heuristic_score = self.profiles[strategy].score_for_context(context_profile)
        return {
            "learning_score": learning_score,
            "heuristic_score": heuristic_score,
            "combined_score": self.learning_weight * learning_score + (1 - self.learning_weight) * heuristic_score,
            "learning_weight": self.learning_weight,
            "learning_contribution": learning_score * self.learning_weight,
            "heuristic_contribution": heuristic_score * (1 - self.learning_weight)
        }
    def _get_learning_score(self, strategy: str, context: Dict) -> float:
        if strategy not in self.strategy_performance:
            return 0.5
        records = self.strategy_performance[strategy]
        if not records:
            return 0.5
        cutoff = time.time() - 3600
        recent = [r for r in records if r["timestamp"] > cutoff]
        if not recent:
            recent = records[-50:]
        total_weight = 0
        weighted_sum = 0
        current_time = time.time()
        for record in recent:
            age = current_time - record["timestamp"]
            weight = math.exp(-age / self.recency_decay)
            context_similarity = self._context_similarity(
                context, record.get("context", {})
            )
            weight *= (0.7 + 0.3 * context_similarity)
            weighted_sum += record["score"] * weight
            total_weight += weight
        if total_weight == 0:
            return 0.5
        return weighted_sum / total_weight
    def _context_similarity(self, context1: Dict, context2: Dict) -> float:
        if not context1 or not context2:
            return 0.5
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.5
        similarities = []
        for key in common_keys:
            val1 = context1.get(key, 0)
            val2 = context2.get(key, 0)
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                max_val = max(abs(val1), abs(val2), 1)
                diff = abs(val1 - val2) / max_val
                similarities.append(1.0 - min(1.0, diff))
            else:
                similarities.append(1.0 if val1 == val2 else 0.0)
        return sum(similarities) / len(similarities) if similarities else 0.5
    def _context_to_key(self, context: Dict) -> str:
        features = []
        if "pattern_size" in context:
            size = context["pattern_size"]
            if size < 100:
                features.append("small")
            elif size < 1000:
                features.append("medium")
            else:
                features.append("large")
        if "pattern_tags" in context:
            tags = context["pattern_tags"]
            if tags:
                features.append("tagged")
            else:
                features.append("untagged")
        if "memory_pressure" in context:
            pressure = context["memory_pressure"]
            if pressure > 0.7:
                features.append("high_pressure")
            elif pressure > 0.3:
                features.append("medium_pressure")
            else:
                features.append("low_pressure")
        if "mode" in context:
            if hasattr(context["mode"], 'value'):
                features.append(f"mode_{context['mode'].value}")
            else:
                features.append(f"mode_{context['mode']}")
        if "error_rate" in context:
            error = context["error_rate"]
            if error > 0.2:
                features.append("high_error")
            elif error > 0.1:
                features.append("medium_error")
            else:
                features.append("low_error")
        return "_".join(sorted(features))
    def _analyze_context(self, context: Dict) -> Dict[str, float]:
        profile = defaultdict(float)
        if "pattern_size" in context:
            size = context["pattern_size"]
            if size < 100:
                profile["small_patterns"] = 1.0
            elif size > 1000:
                profile["large_patterns"] = 1.0
        if "pattern_tags" in context:
            tags = context["pattern_tags"]
            if tags:
                profile["tagged_patterns"] = 1.0
                if len(tags) > 5:
                    profile["well_tagged"] = 1.0
        if "memory_pressure" in context:
            profile["memory_constrained"] = context["memory_pressure"]
        if "error_rate" in context:
            profile["high_error"] = context["error_rate"]
        hour = datetime.now().hour
        if 6 <= hour < 12:
            profile["morning"] = 1.0
        elif 12 <= hour < 18:
            profile["afternoon"] = 1.0
        elif 18 <= hour < 24:
            profile["evening"] = 1.0
        else:
            profile["night"] = 1.0
        return dict(profile)
    def _calculate_performance_score(self, performance: Dict) -> float:
        score = 0.0
        if "confidence" in performance:
            score += performance["confidence"] * 0.4
        if "duration" in performance:
            duration_norm = 1.0 / (1.0 + performance["duration"])
            score += duration_norm * 0.3
        if "decision_class" in performance:
            if performance["decision_class"] == "CONFIDENT":
                score += 0.2
            elif performance["decision_class"] == "WEAK_MATCH":
                score += 0.1
        if "results_found" in performance:
            results_norm = min(1.0, performance["results_found"] / 10.0)
            score += results_norm * 0.1
        # bonus for free energy reduction
        if "free_energy_reduction" in performance:
            fe_red = max(0, min(1, performance["free_energy_reduction"] / 10.0))  # normalize
            score += fe_red * 0.2
        return max(0.0, min(1.0, score))
    def _background_learning(self):
        while True:
            time.sleep(300)
            try:
                self._update_strategy_profiles()
                self._clean_old_records()
                self._adjust_learning_weight()
            except Exception as e:
                logger.warning(
                    f"Background learning failed: {e}\n{traceback.format_exc()}"
                )
    def _update_strategy_profiles(self):
        for strategy, records in self.strategy_performance.items():
            if records and strategy in self.profiles:
                recent = records[-100:]
                if recent:
                    avg_score = sum(r["score"] for r in recent) / len(recent)
                    profile = self.profiles[strategy]
                    profile.base_confidence = 0.3 + 0.4 * avg_score
                    if strategy in self.strategy_profiles:
                        current_cost = self.strategy_profiles[strategy]["cost"]
                        if avg_score > 0.7:
                            new_cost = current_cost * 0.95
                        elif avg_score < 0.3:
                            new_cost = current_cost * 1.05
                        else:
                            new_cost = current_cost
                        self.strategy_profiles[strategy]["cost"] = max(0.5, min(3.0, new_cost))
    def _adjust_learning_weight(self):
        total_predictions = len(self._recommendation_history)
        if total_predictions < 100:
            return
        recent_predictions = self._recommendation_history[-50:]
        if not recent_predictions:
            return
        confidence_scores = [p[2] for p in recent_predictions]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        self.learning_weight = 0.5 + 0.4 * avg_confidence
        logger.debug(f"Adjusted learning weight to {self.learning_weight:.3f}")
    def _clean_old_records(self):
        cutoff = time.time() - 7 * 86400
        for strategy in list(self.strategy_performance.keys()):
            self.strategy_performance[strategy] = [
                r for r in self.strategy_performance[strategy]
                if r["timestamp"] > cutoff
            ]
    def get_profile_stats(self) -> Dict[str, Dict[str, float]]:
        return {
            name: {
                'success_rate': p.success_rate,
                'avg_duration': p.avg_duration,
                'usage_count': p.usage_count,
                'current_confidence': p.current_confidence,
                'context_matches': p.context_matches,
                'avg_score': p.total_score / max(1, p.usage_count),
                'avg_free_energy_reduction': p.avg_free_energy_reduction
            }
            for name, p in self.profiles.items()
        }
    def adaptation_report(self) -> Dict[str, Any]:
        report = {
            'adaptation_rate': self.adaptation_rate,
            'learning_weight': self.learning_weight,
            'profiles': {},
            'recommendations': len(self._recommendation_history)
        }
        for name, profile in self.profiles.items():
            report['profiles'][name] = {
                'delta': profile.success_rate - profile.base_confidence,
                'final_success_rate': profile.success_rate,
                'usage': profile.usage_count,
                'context_matches': profile.context_matches,
                'avg_free_energy_reduction': profile.avg_free_energy_reduction
            }
        return report
    def get_learning_insights(self) -> Dict[str, Any]:
        insights = {
            "best_performing": [],
            "worst_performing": [],
            "context_specializations": {},
            "learning_effectiveness": self.learning_weight
        }
        performance = []
        for strategy, records in self.strategy_performance.items():
            if records:
                avg_score = sum(r["score"] for r in records[-100:]) / min(100, len(records))
                performance.append((strategy, avg_score))
        performance.sort(key=lambda x: x[1], reverse=True)
        insights["best_performing"] = performance[:2]
        insights["worst_performing"] = performance[-2:] if len(performance) >= 2 else []
        for context_key, records in self.context_patterns.items():
            if records:
                strategy_scores = defaultdict(list)
                for r in records[-50:]:
                    strategy_scores[r["strategy"]].append(r["score"])
                best_for_context = max(
                    [(s, sum(sc) / len(sc)) for s, sc in strategy_scores.items()],
                    key=lambda x: x[1]
                )
                insights["context_specializations"][context_key] = {
                    "best_strategy": best_for_context[0],
                    "avg_score": best_for_context[1]
                }
        return insights
    def save_learning_state(self, filepath: str = "meta_learner_state.json") -> bool:
        try:
            state = {
                "schema_version": "13.2",
                "saved_at": time.time(),
                "learning_weight": self.learning_weight,
                "recency_decay": self.recency_decay,
                "adaptation_rate": self.adaptation_rate,
                "profiles": {
                    name: {
                        "base_confidence": p.base_confidence,
                        "success_rate": p.success_rate,
                        "avg_duration": p.avg_duration,
                        "usage_count": p.usage_count,
                        "context_matches": p.context_matches,
                        "total_score": p.total_score,
                        "last_used": p.last_used,
                        "avg_free_energy_reduction": p.avg_free_energy_reduction
                    }
                    for name, p in self.profiles.items()
                },
                "strategy_profiles_costs": {
                    name: data.get("cost", 1.0)
                    for name, data in self.strategy_profiles.items()
                },
                "strategy_performance": {
                    strategy: records[-200:]
                    for strategy, records in self.strategy_performance.items()
                },
                "context_patterns": {
                    key: patterns[-100:]
                    for key, patterns in self.context_patterns.items()
                }
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, default=str)
            total_saved = sum(len(v) for v in self.strategy_performance.values())
            logger.info(f"MetaLearner state saved to '{filepath}' ({total_saved} records)")
            return True
        except Exception as e:
            logger.error(f"Failed to save learning state: {e}\n{traceback.format_exc()}")
            return False
    def load_learning_state(self, filepath: str = "meta_learner_state.json") -> bool:
        if not os.path.exists(filepath):
            logger.info(f"No saved learning state found at '{filepath}', starting fresh.")
            return False
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            schema = state.get("schema_version", "unknown")
            saved_at = state.get("saved_at", 0)
            age_hours = (time.time() - saved_at) / 3600
            logger.info(f"Loading MetaLearner state (schema={schema}, age={age_hours:.1f}h)")
            self.learning_weight = float(state.get("learning_weight", self.learning_weight))
            self.recency_decay = float(state.get("recency_decay", self.recency_decay))
            for name, pdata in state.get("profiles", {}).items():
                if name in self.profiles:
                    p = self.profiles[name]
                    p.base_confidence = float(pdata.get("base_confidence", p.base_confidence))
                    p.success_rate = float(pdata.get("success_rate", p.success_rate))
                    p.avg_duration = float(pdata.get("avg_duration", p.avg_duration))
                    p.usage_count = int(pdata.get("usage_count", p.usage_count))
                    p.context_matches = int(pdata.get("context_matches", p.context_matches))
                    p.total_score = float(pdata.get("total_score", p.total_score))
                    p.last_used = float(pdata.get("last_used", p.last_used))
                    p.avg_free_energy_reduction = float(pdata.get("avg_free_energy_reduction", 0.0))
            for name, cost in state.get("strategy_profiles_costs", {}).items():
                if name in self.strategy_profiles:
                    self.strategy_profiles[name]["cost"] = float(cost)
            for strategy, records in state.get("strategy_performance", {}).items():
                self.strategy_performance[strategy] = records
            for key, patterns in state.get("context_patterns", {}).items():
                self.context_patterns[key] = patterns
            self.recommendation_cache.clear()
            total_records = sum(len(v) for v in self.strategy_performance.values())
            logger.info(f"MetaLearner state loaded: {total_records} performance records, "
                        f"learning_weight={self.learning_weight:.3f}")
            return True
        except Exception as e:
            logger.error(f"Failed to load learning state from '{filepath}': {e}\n{traceback.format_exc()}")
            return False
    def stats(self) -> Dict[str, Any]:
        strategy_stats = {}
        for strategy, records in self.strategy_performance.items():
            if records:
                recent = records[-100:]
                avg_score = sum(r["score"] for r in recent) / len(recent) if recent else 0
                strategy_stats[strategy] = {
                    "avg_score": avg_score,
                    "total_records": len(records),
                    "recent_records": len(recent),
                    "current_cost": self.strategy_profiles.get(strategy, {}).get("cost", 1.0),
                    "profile": {
                        "success_rate": self.profiles[strategy].success_rate,
                        "usage_count": self.profiles[strategy].usage_count,
                        "avg_free_energy_reduction": self.profiles[strategy].avg_free_energy_reduction
                    } if strategy in self.profiles else {}
                }
        return {
            "strategy_stats": strategy_stats,
            "recommendation_cache_size": len(self.recommendation_cache),
            "context_patterns_learned": len(self.context_patterns),
            "learning_rate": self.adaptation_rate,
            "learning_weight": self.learning_weight,
            "adaptation_report": self.adaptation_report(),
            "learning_insights": self.get_learning_insights()
        }

# ============================================
# STATE MANAGER - Pure Dependency Injection WITH INTEGRATED LEARNING
# ============================================

class CognitiveStateManager:
    STRATEGY_SWITCH_THRESHOLD = 0.15
    def __init__(
        self,
        metrics_collector: IMetricsCollector,
        meta_learner: MetaLearner,
        explainer: ExplainableDecision,
        initial_state: Optional[CognitiveState] = None,
        snapshot_system: Optional['IncrementalSnapshot'] = None,
        exploration_rate: float = 0.1   # new parameter for ε-greedy exploration
    ):
        self.metrics = metrics_collector
        self.meta_learner = meta_learner
        self.explainer = explainer
        self.snapshot_system = snapshot_system
        self._current = initial_state or CognitiveState()
        self._history: deque = deque(maxlen=100)
        self._transitions: deque = deque(maxlen=500)
        self.mode_policies = self._init_mode_policies()
        self.exploration_rate = exploration_rate
        logger.info(f"CognitiveStateManager initialized with DI, integrated learning, and exploration rate {exploration_rate}")
    def _init_mode_policies(self) -> Dict[str, Dict]:
        return {
            "AUTONOMOUS": {
                "on_high_error": "SAFE_RECOVERY",
                "on_low_confidence": "META_LEARNING",
                "requires": ["confidence_level > 0.7", "error_rate_1min < 0.1"]
            },
            "SAFE_RECOVERY": {
                "on_recovery_complete": "AUTONOMOUS",
                "max_duration": 300,
                "requires": []
            },
            "META_LEARNING": {
                "on_learning_complete": "AUTONOMOUS",
                "sample_size_required": 100,
                "requires": ["uptime_cycles > 10"]
            }
        }
    def decide_mode_transition(self, metrics: Optional[MetricsSnapshot] = None) -> Optional[CognitiveMode]:
        try:
            if metrics is None:
                metrics = self.metrics.current()
            if metrics.error_rate_1min > 0.2:
                logger.warning(f"High error rate detected ({metrics.error_rate_1min:.1%}), switching to SAFE_RECOVERY")
                return CognitiveMode.SAFE_RECOVERY
            if metrics.avg_confidence < 0.3:
                logger.info(f"Low confidence detected ({metrics.avg_confidence:.1%}), switching to META_LEARNING")
                return CognitiveMode.META_LEARNING
            # new: high free energy might trigger meta-learning (threshold reduced to 5.0)
            if metrics.free_energy > 5.0:
                logger.info(f"High free energy ({metrics.free_energy:.2f}), switching to META_LEARNING")
                return CognitiveMode.META_LEARNING
            current_mode = self._current.mode
            policy = self.mode_policies.get(current_mode.value, {})
            if current_mode == CognitiveMode.SAFE_RECOVERY:
                recovery_time = time.time() - self._get_mode_start_time(current_mode)
                if recovery_time > policy.get('max_duration', 300):
                    logger.info(f"Recovery completed, returning to AUTONOMOUS mode")
                    return CognitiveMode.AUTONOMOUS
            return None
        except Exception as e:
            logger.error(f"Error in mode transition decision: {e}")
            return None
    def _reevaluate_strategy(self, operation_context: Dict) -> Optional[str]:
        current_strategy = self._current.current_strategy
        context_for_meta = {
            "pattern_size": operation_context.get("pattern_size", 0),
            "pattern_tags": operation_context.get("pattern_tags", []),
            "memory_pressure": self._current.stm_utilization,
            "mode": self._current.mode.value,
            "error_rate": self._current.error_rate_1min,
            "confidence": self._current.confidence_level,
            "free_energy": self._current.free_energy
        }
        current_score = self.meta_learner.get_strategy_confidence(current_strategy, context_for_meta)
        best_strategy = current_strategy
        best_score = current_score
        scores = {}
        for strategy_name in self.meta_learner.profiles.keys():
            if strategy_name == current_strategy:
                scores[strategy_name] = current_score
                continue
            score = self.meta_learner.get_strategy_confidence(strategy_name, context_for_meta)
            scores[strategy_name] = score
            if score > best_score:
                best_score = score
                best_strategy = strategy_name
        if best_strategy != current_strategy and (best_score - current_score) > self.STRATEGY_SWITCH_THRESHOLD:
            logger.info(f"Learning triggered strategy re-evaluation: switching from {current_strategy} ({current_score:.3f}) to {best_strategy} ({best_score:.3f})")
            return best_strategy
        return None
    def decide_cognitive_strategy(self, operation_context: Dict) -> Dict[str, Any]:
        current_mode = self._current.mode
        context_for_meta = {
            "pattern_size": operation_context.get("pattern_size", 0),
            "pattern_tags": operation_context.get("pattern_tags", []),
            "memory_pressure": self._current.stm_utilization,
            "mode": current_mode.value,
            "error_rate": self._current.error_rate_1min,
            "confidence": self._current.confidence_level,
            "free_energy": self._current.free_energy
        }
        if current_mode == CognitiveMode.SAFE_RECOVERY:
            recommended = "byte"
            learning_confidence = 1.0
            learning_used = False
            logger.debug(f"Safe mode: forcing byte strategy")
        else:
            # Base recommendation from meta-learner
            base_recommended = self.meta_learner.recommend_strategy(context_for_meta)
            all_confidences = {}
            for strategy in self.meta_learner.profiles.keys():
                all_confidences[strategy] = self.meta_learner.get_strategy_confidence(strategy, context_for_meta)
            current_strategy = self._current.current_strategy
            current_confidence = all_confidences.get(current_strategy, 0.5)
            best_strategy = max(all_confidences.items(), key=lambda x: x[1])
            best_strategy_name, best_confidence = best_strategy

            # Exploration: with probability exploration_rate, choose a random strategy (excluding current if desired)
            if random.random() < self.exploration_rate:
                # Choose a random strategy from available (excluding safe mode forced ones)
                available = list(self.meta_learner.profiles.keys())
                # Optionally, avoid the current strategy to promote exploration
                # Here we simply pick a random one, could also weight by confidence
                recommended = random.choice(available)
                logger.info(f"Exploration: randomly selected {recommended} instead of {best_strategy_name}")
                learning_confidence = all_confidences.get(recommended, 0.5)
                learning_used = True
            else:
                if (best_strategy_name != current_strategy and 
                    (best_confidence - current_confidence) > self.STRATEGY_SWITCH_THRESHOLD):
                    recommended = best_strategy_name
                    logger.info(f"Learning triggered immediate strategy switch: {current_strategy} ({current_confidence:.3f}) -> {best_strategy_name} ({best_confidence:.3f})")
                else:
                    recommended = current_strategy
                learning_confidence = all_confidences.get(recommended, 0.5)
                learning_used = True

        if learning_used:
            confidence = 0.7 * learning_confidence + 0.3 * self._current.confidence_level
            learning_weight = 0.7
        else:
            confidence = self._current.confidence_level
            learning_weight = 0.0

        decision_data = {
            "strategy": recommended,
            "context": operation_context,
            "confidence": confidence,
            "decision_class": "CONFIDENT" if confidence > 0.7 else "WEAK_MATCH",
            "learning_used": learning_used,
            "learning_confidence": learning_confidence if learning_used else 0.0,
            "learning_weight": learning_weight
        }
        if learning_used:
            try:
                learning_contribution = self.meta_learner.get_learning_contribution(
                    recommended, context_for_meta
                )
                decision_data["learning_score"] = learning_contribution.get("learning_score", 0.0)
                decision_data["heuristic_score"] = learning_contribution.get("heuristic_score", 0.0)
            except:
                pass
        explanation = self.explainer.explain(decision_data)
        if current_mode != CognitiveMode.SAFE_RECOVERY:
            self._update_strategy_confidence(recommended)
        logger.debug(f"Strategy decision: {recommended} (mode: {current_mode.value}, "
                    f"confidence: {confidence:.2f}, learning: {learning_used})")
        return {
            "strategy": recommended,
            "reason": explanation.summary(),
            "confidence": confidence,
            "mode": current_mode.value,
            "learning_used": learning_used,
            "learning_confidence": learning_confidence if learning_used else 0.0,
            "learning_weight": learning_weight
        }
    def _update_strategy_confidence(self, used_strategy: str):
        strategy_dict = dict(self._current.strategy_confidence)
        current = strategy_dict.get(used_strategy, 0.5)
        strategy_dict[used_strategy] = min(1.0, current + 0.01)
        for strategy in strategy_dict:
            if strategy != used_strategy:
                strategy_dict[strategy] = max(0.1, strategy_dict[strategy] - 0.002)
        self.transition(
            reason=f"strategy_confidence_update_{used_strategy}",
            strategy_confidence=tuple(sorted(strategy_dict.items()))
        )
    def transition(self, reason: str = "", **state_changes) -> StateTransition:
        metrics = self.metrics.current()
        auto_mode = self.decide_mode_transition(metrics)
        if auto_mode and 'mode' not in state_changes:
            state_changes['mode'] = auto_mode
        if 'error_rate_1min' not in state_changes:
            state_changes['error_rate_1min'] = metrics.error_rate_1min
        if 'stm_utilization' not in state_changes:
            state_changes['stm_utilization'] = metrics.stm_utilization
        if 'cache_hit_rate' not in state_changes:
            state_changes['cache_hit_rate'] = metrics.cache_hit_rate
        if 'ltm_pattern_count' not in state_changes:
            state_changes['ltm_pattern_count'] = metrics.ltm_pattern_count
        if 'avg_decision_time_ms' not in state_changes:
            state_changes['avg_decision_time_ms'] = metrics.avg_decision_time_ms
        if 'free_energy' not in state_changes:
            state_changes['free_energy'] = metrics.free_energy
        state_changes['last_activity_timestamp'] = time.time()
        state_changes['uptime_cycles'] = self._current.uptime_cycles + 1
        if state_changes.get('mode') == CognitiveMode.SAFE_RECOVERY:
            state_changes['current_strategy'] = 'byte'
            logger.info("Entering SAFE_RECOVERY mode - forcing byte strategy")
        new_state = self._current.with_updates(**state_changes)
        transition = StateTransition.from_states(
            from_state=self._current,
            to_state=new_state,
            reason=reason,
            metrics=metrics
        )
        self._history.append(self._current)
        self._transitions.append(transition)
        self._current = new_state
        if transition.is_significant() and self.snapshot_system:
            self._trigger_snapshot(transition)
        logger.debug(f"State transition: {transition.transition_type.value}")
        return transition
    def _trigger_snapshot(self, transition: StateTransition):
        try:
            self.snapshot_system.create_incremental(
                changes=[transition.to_dict()],
                description=f"State transition: {transition.transition_type.value}"
            )
        except Exception as e:
            logger.error(f"Failed to trigger snapshot: {e}")
    def _get_mode_start_time(self, mode: CognitiveMode) -> float:
        for transition in reversed(self._transitions):
            if (transition.transition_type == TransitionType.MODE_CHANGE and
                transition.to_state.mode == mode):
                return transition.timestamp
        return time.time()
    def rollback_to_state(self, target_state_id: str) -> Optional[StateTransition]:
        target = None
        for state in self._history:
            if state.state_id == target_state_id:
                target = state
                break
        if not target:
            logger.error(f"Target state not found: {target_state_id}")
            return None
        transition = StateTransition(
            timestamp=time.time(),
            transition_type=TransitionType.ROLLBACK,
            from_state=self._current,
            to_state=target,
            reason=f"Rollback to {target_state_id}",
            metrics_snapshot=self.metrics.current()
        )
        self._transitions.append(transition)
        self._current = target
        logger.info(f"Rolled back to state: {target_state_id}")
        return transition
    def current(self) -> CognitiveState:
        return self._current
    def history(self, limit: Optional[int] = None) -> List[CognitiveState]:
        all_states = [self._current] + list(self._history)
        if limit is None:
            return all_states
        return all_states[-limit:]
    def transitions(self, limit: Optional[int] = None) -> List[StateTransition]:
        trans_list = list(self._transitions)
        if limit is None:
            return trans_list
        return trans_list[-limit:]
    def get_state_summary(self) -> Dict[str, Any]:
        return {
            "state_id": self._current.state_id,
            "mode": self._current.mode.value,
            "status": self._current.status.value,
            "confidence": self._current.confidence_level,
            "active_patterns": len(self._current.active_pattern_hashes),
            "strategy": self._current.current_strategy,
            "uptime_cycles": self._current.uptime_cycles,
            "change_log_size": len(self._transitions),
            "free_energy": self._current.free_energy
        }

# ============================================
# DISTRIBUTED SEARCH CACHE (Preserved)
# ============================================

class RestrictedUnpickler(pickle.Unpickler):
    ALLOWED_CLASSES = {
        'builtins': {'dict', 'list', 'tuple', 'set', 'str', 'int', 'float', 'bool', 'bytes', 'NoneType'},
        'collections': {'OrderedDict', 'defaultdict', 'deque'},
        'datetime': {'datetime', 'date', 'time'},
        'typing': {'Dict', 'List', 'Tuple', 'Set'},
    }
    def find_class(self, module, name):
        if module in self.ALLOWED_CLASSES and name in self.ALLOWED_CLASSES[module]:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Class {module}.{name} is not allowed")

class DistributedSearchCache:
    def __init__(self, primary_size: int = 10000, secondary_dir: str = "cache/level2"):
        self.primary_cache = OrderedDict()
        self.primary_size = primary_size
        self.secondary_dir = secondary_dir
        self.access_patterns = defaultdict(int)
        self.hit_stats = defaultdict(int)
        self.miss_stats = defaultdict(int)
        os.makedirs(secondary_dir, exist_ok=True)
        self.cleaner_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="CacheCleaner"
        )
        self.cleaner_thread.start()
        logger.info(f"DistributedSearchCache initialized (primary: {primary_size}, secondary: {secondary_dir})")
    def get_with_ttl(self, key: str, ttl: int = 3600) -> Optional[Any]:
        entry = self.primary_cache.get(key)
        if not entry:
            return None
        if "timestamp" not in entry:
            return None
        if time.time() - entry["timestamp"] < ttl:
            if "value" in entry:
                return entry["value"]
            elif "data" in entry:
                return entry["data"]
            return None
        self.delete(key)
        return None
    def set_with_ttl(self, key: str, data: Any, ttl: int = 300,
                    priority: int = 1) -> bool:
        entry = {
            "value": data,
            "timestamp": time.time(),
            "ttl": ttl,
            "priority": priority,
            "access_count": 0
        }
        if len(self.primary_cache) < self.primary_size or priority > 5:
            self._store_primary(key, entry)
            return True
        else:
            return self._store_secondary(key, entry)
    def _store_primary(self, key: str, entry: Dict):
        if len(self.primary_cache) >= self.primary_size:
            evict_key = self._select_eviction_candidate()
            if evict_key:
                evicted = self.primary_cache[evict_key]
                self._store_secondary(evict_key, evicted)
                del self.primary_cache[evict_key]
        self.primary_cache[key] = entry
    def _store_secondary(self, key: str, entry: Dict) -> bool:
        try:
            secondary_path = os.path.join(self.secondary_dir, f"{key}.cache")
            with open(secondary_path, 'wb') as f:
                pickle.dump(entry, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            logger.warning(f"Failed to store in secondary cache: {e}")
            return False
    def _select_eviction_candidate(self) -> Optional[str]:
        if not self.primary_cache:
            return None
        best_score = float('inf')
        best_key = None
        current_time = time.time()
        for key, entry in self.primary_cache.items():
            age = current_time - entry["timestamp"]
            access_ratio = entry.get("access_count", 0) / max(1, age)
            priority = entry.get("priority", 1)
            score = (
                (1.0 / (priority + 0.1)) * 0.4 +
                (age / 3600) * 0.3 +
                (1.0 / (access_ratio + 0.1)) * 0.3
            )
            if score < best_score:
                best_score = score
                best_key = key
        return best_key
    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            self._clean_expired()
            self._compact_secondary()
    def _clean_expired(self):
        current_time = time.time()
        to_remove = []
        for key, entry in list(self.primary_cache.items()):
            if current_time - entry["timestamp"] > entry.get("ttl", 300):
                to_remove.append(key)
        for key in to_remove:
            del self.primary_cache[key]
        if os.path.exists(self.secondary_dir):
            for filename in os.listdir(self.secondary_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.secondary_dir, filename)
                    try:
                        with open(filepath, 'rb') as f:
                            unpickler = RestrictedUnpickler(f)
                            entry = unpickler.load()
                            if current_time - entry["timestamp"] > entry.get("ttl", 300):
                                os.remove(filepath)
                    except Exception:
                        try:
                            os.remove(filepath)
                        except:
                            pass
    def _compact_secondary(self):
        if not os.path.exists(self.secondary_dir):
            return
        files = []
        for filename in os.listdir(self.secondary_dir):
            if filename.endswith('.cache'):
                filepath = os.path.join(self.secondary_dir, filename)
                mtime = os.path.getmtime(filepath)
                files.append((mtime, filepath, filename))
        files.sort()
        if len(files) > 1000:
            for _, filepath, _ in files[:-1000]:
                try:
                    os.remove(filepath)
                except Exception:
                    pass
    def delete(self, key: str):
        if key in self.primary_cache:
            del self.primary_cache[key]
        secondary_path = os.path.join(self.secondary_dir, f"{key}.cache")
        if os.path.exists(secondary_path):
            try:
                os.remove(secondary_path)
            except Exception:
                pass
    def clear(self):
        self.primary_cache.clear()
        if os.path.exists(self.secondary_dir):
            for filename in os.listdir(self.secondary_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.secondary_dir, filename)
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
    def stats(self) -> Dict[str, Any]:
        total_hits = sum(self.hit_stats.values())
        total_misses = sum(self.miss_stats.values())
        total_accesses = total_hits + total_misses
        hit_rate = total_hits / total_accesses if total_accesses > 0 else 0
        return {
            "primary_size": len(self.primary_cache),
            "primary_capacity": self.primary_size,
            "secondary_files": len(os.listdir(self.secondary_dir)) if os.path.exists(self.secondary_dir) else 0,
            "hit_stats": dict(self.hit_stats),
            "miss_stats": dict(self.miss_stats),
            "total_accesses": total_accesses,
            "hit_rate": f"{hit_rate:.1%}",
            "top_accessed": sorted(
                [(k, v) for k, v in self.access_patterns.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

# ============================================
# EMBEDDING PRECOMPUTER (Preserved)
# ============================================

class HyperdimensionalEncoder:
    pass

class EnhancedPattern:
    def __init__(self, data: bytes = b'', tags: List[str] = None, modality: str = "default"):
        self.data = data
        self.tags = tags or []
        self.modality = modality
        self.created_at = time.time()
        self.access_count = 0
        self.lifecycle_stage = "active"
        self.pattern_entropy = 0.0
    def hash(self) -> str:
        return hashlib.sha256(self.data).hexdigest()
    def hyperdimensional_vector(self) -> Optional[HDCVector]:
        if not self.data:
            return None
        vector = [hashlib.sha256(self.data).digest()[i % 32] for i in range(1000)]
        return HDCVector(vector)
    def similarity(self, other: 'EnhancedPattern') -> float:
        if not self.data or not other.data:
            return 0.0
        common_bytes = sum(1 for a, b in zip(self.data, other.data) if a == b)
        return common_bytes / max(len(self.data), len(other.data))
    def drift(self, amount: float) -> 'EnhancedPattern':
        drifted = EnhancedPattern(
            data=self.data,
            tags=self.tags.copy(),
            modality=self.modality
        )
        return drifted

class EmbeddingPrecomputer:
    def __init__(self, cache: DistributedSearchCache, common_tags: Optional[Set[str]] = None):
        self.cache = cache
        self.common_tags = common_tags or {"important", "frequent", "critical", "recent", "pattern"}
        self.precomputed = {}
        self.tag_frequencies = defaultdict(int)
        self.last_precompute = 0
        self.precompute_interval = 300
        self.precompute_thread = threading.Thread(
            target=self._background_precompute,
            daemon=True,
            name="Precomputer"
        )
        self.precompute_thread.start()
        logger.info("EmbeddingPrecomputer initialized with cache integration")
    def warmup_cache(self, patterns: List[EnhancedPattern],
                    encoder: HyperdimensionalEncoder):
        current_time = time.time()
        if current_time - self.last_precompute < self.precompute_interval:
            return
        logger.info("Starting embedding precomputation warmup...")
        start_time = time.time()
        for pattern in patterns:
            for tag in pattern.tags:
                self.tag_frequencies[tag] += 1
        top_tags = sorted(
            self.tag_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )[:50]
        common_tag_set = {tag for tag, _ in top_tags}
        common_tag_set.update(self.common_tags)
        precomputed_count = 0
        for pattern in patterns:
            pattern_tags = set(pattern.tags)
            if pattern_tags.intersection(common_tag_set):
                try:
                    hdv = pattern.hyperdimensional_vector()
                    if hdv is not None:
                        cache_key = f"embedding_{pattern.hash()}"
                        self.cache.set_with_ttl(
                            cache_key,
                            hdv,
                            ttl=3600,
                            priority=3
                        )
                        precomputed_count += 1
                except Exception as e:
                    logger.debug(f"Failed to precompute embedding: {e}")
        self.last_precompute = current_time
        duration = time.time() - start_time
        logger.info(f"Precomputed {precomputed_count} embeddings in {duration:.2f}s")
    def get_precomputed(self, pattern_hash: str) -> Optional[HDCVector]:
        cache_key = f"embedding_{pattern_hash}"
        return self.cache.get_with_ttl(cache_key, ttl=3600)
    def _background_precompute(self):
        while True:
            time.sleep(self.precompute_interval)
            try:
                cache_stats = self.cache.stats()
                hit_rate = cache_stats.get("hit_rate", "0%")
                logger.debug(f"Precomputation cycle - Cache hit rate: {hit_rate}")
            except Exception as e:
                logger.warning(f"Background precomputation failed: {e}")
    def stats(self) -> Dict[str, Any]:
        cache_stats = self.cache.stats()
        return {
            "tag_frequencies": dict(sorted(
                self.tag_frequencies.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]),
            "last_precompute": self.last_precompute,
            "cache_integration": {
                "hit_rate": cache_stats.get("hit_rate", "0%"),
                "primary_size": cache_stats.get("primary_size", 0)
            }
        }

# ============================================
# ADAPTIVE COMPRESSOR (Preserved)
# ============================================

class AdaptiveCompressor:
    COMPRESSORS = {
        "text": {
            "func": zlib.compress,
            "decompress": zlib.decompress,
            "level": 6,
            "header": b"TXT"
        },
        "binary": {
            "func": lzma.compress,
            "decompress": lzma.decompress,
            "level": 2,
            "header": b"BIN"
        },
        "sparse": {
            "func": bz2.compress,
            "decompress": bz2.decompress,
            "level": 4,
            "header": b"SPR"
        },
        "already_compressed": {
            "func": lambda x: x,
            "decompress": lambda x: x,
            "header": b"CMP"
        }
    }
    def __init__(self):
        self.compression_stats = defaultdict(int)
        self.size_reduction = defaultdict(float)
        self.detection_cache = {}
        logger.info("AdaptiveCompressor initialized")
    def detect_type(self, data: bytes) -> str:
        if len(data) < 100:
            return "already_compressed"
        data_hash = hashlib.md5(data).hexdigest()[:16]
        if data_hash in self.detection_cache:
            return self.detection_cache[data_hash]
        if data.startswith(b"CMP") or data.startswith(b"TXT") or \
           data.startswith(b"BIN") or data.startswith(b"SPR"):
            return "already_compressed"
        total_bytes = len(data)
        printable = sum(1 for b in data if 32 <= b <= 126)
        printable_ratio = printable / total_bytes
        zero_bytes = sum(1 for b in data if b == 0)
        zero_ratio = zero_bytes / total_bytes
        if len(data) > 100:
            byte_counts = defaultdict(int)
            for byte in data[:1000]:
                byte_counts[byte] += 1
            entropy = 0.0
            for count in byte_counts.values():
                p = count / 1000
                if p > 0:
                    entropy -= p * math.log2(p)
            entropy_normalized = entropy / 8.0
        else:
            entropy_normalized = 0.5
        if printable_ratio > 0.7:
            data_type = "text"
        elif zero_ratio > 0.3:
            data_type = "sparse"
        elif entropy_normalized > 0.7:
            data_type = "binary"
        else:
            data_type = "already_compressed"
        self.detection_cache[data_hash] = data_type
        if len(self.detection_cache) > 10000:
            keys = list(self.detection_cache.keys())
            for key in keys[:1000]:
                del self.detection_cache[key]
        return data_type
    def compress(self, data: bytes) -> bytes:
        if not data:
            return data
        data_type = self.detect_type(data)
        if data_type == "already_compressed":
            return data
        compressor = self.COMPRESSORS[data_type]
        try:
            start_time = time.time()
            if data_type == "text":
                compressed = compressor["func"](data, level=compressor["level"])
            elif data_type == "binary":
                compressed = compressor["func"](data, preset=compressor["level"])
            elif data_type == "sparse":
                compressed = compressor["func"](data, compresslevel=compressor["level"])
            else:
                compressed = data
            compression_time = time.time() - start_time
            if len(compressed) < len(data):
                checksum = hashlib.sha256(compressed).digest()[:4]
                result = compressor["header"] + checksum + compressed
                self.compression_stats[data_type] += 1
                reduction = (len(data) - len(result)) / len(data)
                self.size_reduction[data_type] = (
                    self.size_reduction.get(data_type, 0) * 0.9 + reduction * 0.1
                )
                logger.debug(f"Compressed {len(data)} -> {len(result)} bytes "
                           f"({reduction:.1%}) using {data_type} in {compression_time:.3f}s")
                return result
            else:
                return data
        except Exception as e:
            logger.warning(f"Compression failed for {data_type}: {e}")
            return data
    def decompress(self, data: bytes) -> bytes:
        if not data:
            return data
        for data_type, compressor in self.COMPRESSORS.items():
            if data.startswith(compressor["header"]):
                if len(data) < len(compressor["header"]) + 4:
                    raise ValueError(f"Invalid compressed data format for {data_type}")
                checksum = data[len(compressor["header"]):len(compressor["header"]) + 4]
                compressed = data[len(compressor["header"]) + 4:]
                expected = hashlib.sha256(compressed).digest()[:4]
                if checksum != expected:
                    raise ValueError(f"Checksum verification failed for {data_type}")
                try:
                    return compressor["decompress"](compressed)
                except Exception as e:
                    raise ValueError(f"Decompression failed for {data_type}: {e}")
        return data
    def stats(self) -> Dict[str, Any]:
        total_compressions = sum(self.compression_stats.values())
        stats = {
            "total_compressions": total_compressions,
            "by_type": dict(self.compression_stats),
            "avg_reduction_by_type": {
                k: f"{v*100:.1f}%" for k, v in self.size_reduction.items()
            },
            "detection_cache_size": len(self.detection_cache),
        }
        if total_compressions > 0:
            stats["overall_avg_reduction"] = sum(
                self.size_reduction.get(k, 0) * (self.compression_stats.get(k, 0) / total_compressions)
                for k in self.COMPRESSORS.keys()
            ) * 100
        return stats

# ============================================
# INCREMENTAL SNAPSHOT SYSTEM (Preserved)
# ============================================

class IncrementalSnapshot:
    def __init__(self, base_dir: str = "snapshots"):
        self.base_dir = base_dir
        self.base_snapshot = None
        self.delta_log = []
        self.last_full_snapshot = 0
        self.snapshot_interval = 3600
        self.delta_interval = 300
        os.makedirs(base_dir, exist_ok=True)
        self.snapshot_thread = threading.Thread(
            target=self._background_snapshot,
            daemon=True,
            name="SnapshotManager"
        )
        self.snapshot_thread.start()
        logger.info(f"IncrementalSnapshot initialized (dir: {base_dir})")
    def create_incremental(self, changes: List[Dict],
                          description: str = "") -> str:
        snapshot_id = f"delta_{time.time_ns()}"
        delta = {
            "id": snapshot_id,
            "timestamp": time.time(),
            "description": description,
            "changes": changes,
            "base_snapshot": self.base_snapshot,
            "change_count": len(changes)
        }
        compressed_changes = self._compress_changes(changes)
        delta["compressed_changes"] = compressed_changes
        delta["compression_ratio"] = len(str(changes)) / len(compressed_changes) if compressed_changes else 1.0
        self.delta_log.append(delta)
        self._save_delta(delta)
        logger.info(f"Created incremental snapshot {snapshot_id} with {len(changes)} changes")
        return snapshot_id
    def _compress_changes(self, changes: List[Dict]) -> bytes:
        try:
            serialized = pickle.dumps(changes, protocol=pickle.HIGHEST_PROTOCOL)
            if len(serialized) > 1000:
                compressed = zlib.compress(serialized, level=3)
                if len(compressed) < len(serialized):
                    return compressed
            return serialized
        except Exception as e:
            logger.warning(f"Change compression failed: {e}")
            return b""
    def _save_delta(self, delta: Dict):
        try:
            delta_file = os.path.join(self.base_dir, f"{delta['id']}.delta")
            with open(delta_file, 'wb') as f:
                pickle.dump(delta, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            logger.error(f"Failed to save delta: {e}")
    def create_full_snapshot(self, system_state: Dict,
                           description: str = "") -> str:
        snapshot_id = f"full_{time.time_ns()}"
        snapshot = {
            "id": snapshot_id,
            "timestamp": time.time(),
            "description": description,
            "system_state": system_state,
            "delta_count": len(self.delta_log),
            "schema_version": "13.2"
        }
        compressed_state = self._compress_state(system_state)
        snapshot["compressed_state"] = compressed_state
        snapshot_file = os.path.join(self.base_dir, f"{snapshot_id}.snap")
        try:
            with open(snapshot_file, 'wb') as f:
                pickle.dump(snapshot, f, protocol=pickle.HIGHEST_PROTOCOL)
            self.base_snapshot = snapshot_id
            self.last_full_snapshot = time.time()
            self.delta_log.clear()
            logger.info(f"Created full snapshot {snapshot_id}")
            self._cleanup_old_snapshots()
            return snapshot_id
        except Exception as e:
            logger.error(f"Failed to create full snapshot: {e}")
            return ""
    def _compress_state(self, state: Dict) -> bytes:
        try:
            serialized = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
            if len(serialized) > 10000:
                compressed = lzma.compress(serialized, preset=2)
                if len(compressed) < len(serialized):
                    return compressed
            return serialized
        except Exception as e:
            logger.warning(f"State compression failed: {e}")
            return b""
    def restore_to_point(self, target_time: float) -> bool:
        full_snapshots = self._list_full_snapshots()
        base_snapshot = None
        for snapshot in sorted(full_snapshots, key=lambda x: x["timestamp"], reverse=True):
            if snapshot["timestamp"] <= target_time:
                base_snapshot = snapshot
                break
        if not base_snapshot:
            logger.error("No suitable base snapshot found")
            return False
        base_state = self._load_snapshot(base_snapshot["id"])
        if not base_state:
            return False
        deltas = self._get_deltas_between(base_snapshot["timestamp"], target_time)
        for delta in deltas:
            if not self._apply_delta(base_state, delta):
                logger.warning(f"Failed to apply delta {delta['id']}")
        logger.info(f"Restored to {target_time} using {base_snapshot['id']} and {len(deltas)} deltas")
        return True
    def _list_full_snapshots(self) -> List[Dict]:
        snapshots = []
        for filename in os.listdir(self.base_dir):
            if filename.endswith('.snap'):
                filepath = os.path.join(self.base_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        unpickler = RestrictedUnpickler(f)
                        snapshot = unpickler.load()
                        snapshots.append({
                            "id": snapshot["id"],
                            "timestamp": snapshot["timestamp"],
                            "description": snapshot.get("description", ""),
                            "size": os.path.getsize(filepath)
                        })
                except Exception as e:
                    logger.warning(f"Failed to read snapshot {filename}: {e}")
        return snapshots
    def _get_deltas_between(self, start_time: float, end_time: float) -> List[Dict]:
        deltas = []
        for filename in os.listdir(self.base_dir):
            if filename.endswith('.delta'):
                filepath = os.path.join(self.base_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        unpickler = RestrictedUnpickler(f)
                        delta = unpickler.load()
                        if start_time <= delta["timestamp"] <= end_time:
                            deltas.append(delta)
                except Exception as e:
                    logger.warning(f"Failed to read delta {filename}: {e}")
        deltas.sort(key=lambda x: x["timestamp"])
        return deltas
    def _apply_delta(self, state: Dict, delta: Dict) -> bool:
        try:
            if "changes" not in delta:
                logger.warning(f"Delta {delta.get('id')} has no changes field")
                return False
            changes = delta["changes"]
            for change in changes:
                if not self._apply_state_change(state, change):
                    logger.warning(f"Failed to apply change: {change.get('change_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply delta: {e}")
            return False
    def _apply_state_change(self, state: Dict, change: Dict) -> bool:
        try:
            path = change.get("path", "")
            if isinstance(path, str):
                path_parts = path.split(".")
            else:
                path_parts = path
            new_value = change.get("new_value")
            current = state
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            last_part = path_parts[-1]
            current[last_part] = new_value
            return True
        except Exception as e:
            logger.error(f"Failed to apply state change: {e}")
            return False
    def _load_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        snapshot_file = os.path.join(self.base_dir, f"{snapshot_id}.snap")
        if not os.path.exists(snapshot_file):
            return None
        try:
            with open(snapshot_file, 'rb') as f:
                unpickler = RestrictedUnpickler(f)
                snapshot = unpickler.load()
                if "compressed_state" in snapshot:
                    state_data = lzma.decompress(snapshot["compressed_state"])
                    unpickler = RestrictedUnpickler(io.BytesIO(state_data))
                    return unpickler.load()
                else:
                    return snapshot.get("system_state", {})
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            return None
    def _background_snapshot(self):
        while True:
            time.sleep(self.delta_interval)
            try:
                current_time = time.time()
                if current_time - self.last_full_snapshot > self.snapshot_interval:
                    logger.info("Full snapshot interval reached")
            except Exception as e:
                logger.warning(f"Background snapshot failed: {e}")
    def _cleanup_old_snapshots(self):
        try:
            snapshots = self._list_full_snapshots()
            if len(snapshots) > 10:
                snapshots.sort(key=lambda x: x["timestamp"])
                to_remove = snapshots[:-10]
                for snapshot in to_remove:
                    filepath = os.path.join(self.base_dir, f"{snapshot['id']}.snap")
                    try:
                        os.remove(filepath)
                        logger.info(f"Removed old snapshot: {snapshot['id']}")
                    except Exception as e:
                        logger.warning(f"Failed to remove snapshot {snapshot['id']}: {e}")
            all_deltas = []
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.delta'):
                    filepath = os.path.join(self.base_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    all_deltas.append((mtime, filepath))
            all_deltas.sort()
            if len(all_deltas) > 100:
                for _, filepath in all_deltas[:-100]:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Snapshot cleanup failed: {e}")
    def stats(self) -> Dict[str, Any]:
        full_snapshots = self._list_full_snapshots()
        delta_files = [f for f in os.listdir(self.base_dir) if f.endswith('.delta')]
        total_size = 0
        for filename in os.listdir(self.base_dir):
            filepath = os.path.join(self.base_dir, filename)
            total_size += os.path.getsize(filepath) if os.path.exists(filepath) else 0
        return {
            "full_snapshots": len(full_snapshots),
            "deltas": len(delta_files),
            "total_size_mb": total_size / (1024 * 1024),
            "base_snapshot": self.base_snapshot,
            "delta_log_size": len(self.delta_log),
            "last_full_snapshot": self.last_full_snapshot,
            "next_full_snapshot": self.last_full_snapshot + self.snapshot_interval - time.time()
        }

# ============================================
# PATTERN POOL (Preserved)
# ============================================

class PatternPool:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.pool = OrderedDict()
        self.access_count = defaultdict(int)
        self.temporal_access = defaultdict(list)
        self.hit_stats = defaultdict(int)
        self.miss_stats = defaultdict(int)
        self.rebalancer_thread = threading.Thread(
            target=self._rebalance_loop,
            daemon=True,
            name="PatternPoolRebalancer"
        )
        self.rebalancer_thread.start()
        logger.info(f"PatternPool initialized (max_size: {max_size})")
    def get(self, pattern_hash: str, pattern: Optional[EnhancedPattern] = None) -> Optional[EnhancedPattern]:
        current_time = time.time()
        if pattern_hash in self.pool:
            entry = self.pool[pattern_hash]
            entry["last_access"] = current_time
            entry["access_count"] += 1
            self.access_count[pattern_hash] += 1
            self.temporal_access[pattern_hash].append(current_time)
            self.pool.move_to_end(pattern_hash)
            self.hit_stats["pool"] += 1
            return entry["pattern"]
        if pattern is not None:
            self._add_to_pool(pattern_hash, pattern, current_time)
            self.miss_stats["added"] += 1
            return pattern
        self.miss_stats["not_found"] += 1
        return None
    def _add_to_pool(self, pattern_hash: str, pattern: EnhancedPattern,
                    timestamp: float):
        if len(self.pool) >= self.max_size:
            self._evict_pattern()
        self.pool[pattern_hash] = {
            "pattern": pattern,
            "first_access": timestamp,
            "last_access": timestamp,
            "access_count": 1,
            "size": len(pattern.data) if hasattr(pattern, 'data') else 0
        }
        self.access_count[pattern_hash] = 1
        self.temporal_access[pattern_hash] = [timestamp]
    def _evict_pattern(self):
        if not self.pool:
            return
        best_score = float('inf')
        best_key = None
        current_time = time.time()
        for key, entry in self.pool.items():
            age = current_time - entry["first_access"]
            recency = current_time - entry["last_access"]
            frequency = entry["access_count"]
            score = (
                (recency / 3600) * 0.4 +
                (1.0 / (frequency + 1)) * 0.3 +
                (age / 86400) * 0.2 +
                (entry["size"] / 100000) * 0.1
            )
            if score < best_score:
                best_score = score
                best_key = key
        if best_key:
            del self.pool[best_key]
            self.hit_stats["evicted"] += 1
    def _rebalance_loop(self):
        while True:
            time.sleep(300)
            try:
                self._rebalance_pool()
                self._clean_old_access_data()
            except Exception as e:
                logger.warning(f"Pool rebalancing failed: {e}")
    def _rebalance_pool(self):
        if not self.access_count:
            return
        avg_frequency = sum(self.access_count.values()) / len(self.access_count)
        current_time = time.time()
        to_remove = []
        for pattern_hash, entry in list(self.pool.items()):
            frequency = self.access_count.get(pattern_hash, 0)
            recency = current_time - entry["last_access"]
            if frequency < avg_frequency * 0.1 and recency > 3600:
                to_remove.append(pattern_hash)
        for pattern_hash in to_remove:
            del self.pool[pattern_hash]
    def _clean_old_access_data(self):
        current_time = time.time()
        cutoff = current_time - 7 * 86400
        for pattern_hash in list(self.temporal_access.keys()):
            self.temporal_access[pattern_hash] = [
                t for t in self.temporal_access[pattern_hash]
                if t > cutoff
            ]
            if not self.temporal_access[pattern_hash]:
                del self.temporal_access[pattern_hash]
        if len(self.access_count) > 10000:
            pool_keys = set(self.pool.keys())
            recent_cutoff = current_time - 86400
            recent_patterns = set()
            for pattern_hash, timestamps in self.temporal_access.items():
                if any(t > recent_cutoff for t in timestamps):
                    recent_patterns.add(pattern_hash)
            keys_to_keep = pool_keys.union(recent_patterns)
            for key in list(self.access_count.keys()):
                if key not in keys_to_keep:
                    del self.access_count[key]
    def stats(self) -> Dict[str, Any]:
        if not self.pool:
            return {
                "pool_size": 0,
                "max_size": self.max_size,
                "hit_rate": 0.0
            }
        total_accesses = sum(self.access_count.values())
        total_hits = sum(self.hit_stats.values())
        total_misses = sum(self.miss_stats.values())
        total_operations = total_hits + total_misses
        hit_rate = total_hits / total_operations if total_operations > 0 else 0.0
        pool_size_bytes = sum(entry["size"] for entry in self.pool.values())
        top_patterns = sorted(
            [(k, v) for k, v in self.access_count.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        return {
            "pool_size": len(self.pool),
            "max_size": self.max_size,
            "pool_size_mb": pool_size_bytes / (1024 * 1024),
            "hit_rate": f"{hit_rate:.1%}",
            "hit_stats": dict(self.hit_stats),
            "miss_stats": dict(self.miss_stats),
            "total_patterns_tracked": len(self.access_count),
            "top_frequent_patterns": top_patterns,
            "avg_access_frequency": total_accesses / max(1, len(self.access_count))
        }

# ============================================
# GRANULAR RECOVERY SYSTEM (Preserved)
# ============================================

class GranularRecovery:
    COMPONENTS = ["stm", "ltm", "index", "associations", "config", "acs"]
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self.component_backups = defaultdict(list)
        self.recovery_history = deque(maxlen=100)
        os.makedirs(backup_dir, exist_ok=True)
        self._load_backup_index()
        logger.info(f"GranularRecovery initialized (dir: {backup_dir})")
    def backup_component(self, component: str, data: Any,
                        description: str = "") -> str:
        if component not in self.COMPONENTS:
            raise ValueError(f"Invalid component: {component}")
        backup_id = f"{component}_{time.time_ns()}"
        backup_file = os.path.join(self.backup_dir, f"{backup_id}.bak")
        try:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            compressed = zlib.compress(serialized, level=5)
            metadata = {
                "component": component,
                "timestamp": time.time(),
                "description": description,
                "data_size": len(serialized),
                "compressed_size": len(compressed),
                "compression_ratio": len(serialized) / len(compressed) if len(compressed) > 0 else 1.0,
                "checksum": hashlib.sha256(compressed).hexdigest(),
                "schema_version": "13.2"
            }
            with open(backup_file, 'wb') as f:
                f.write(pickle.dumps(metadata, protocol=pickle.HIGHEST_PROTOCOL))
                f.write(compressed)
            self.component_backups[component].append({
                "id": backup_id,
                "timestamp": metadata["timestamp"],
                "description": description,
                "file": backup_file,
                "size": os.path.getsize(backup_file)
            })
            self._save_backup_index()
            logger.info(f"Created backup {backup_id} for component {component}")
            self._cleanup_old_backups(component)
            return backup_id
        except Exception as e:
            logger.error(f"Failed to backup component {component}: {e}")
            return ""
    def recover_component(self, component: str, backup_id: Optional[str] = None) -> Optional[Any]:
        if component not in self.COMPONENTS:
            raise ValueError(f"Invalid component: {component}")
        if backup_id is None:
            if component not in self.component_backups or not self.component_backups[component]:
                logger.error(f"No backups available for component {component}")
                return None
            backup_info = self.component_backups[component][-1]
            backup_id = backup_info["id"]
        else:
            backup_info = None
            for info in self.component_backups.get(component, []):
                if info["id"] == backup_id:
                    backup_info = info
                    break
            if not backup_info:
                logger.error(f"Backup {backup_id} not found for component {component}")
                return None
        try:
            backup_file = backup_info["file"]
            with open(backup_file, 'rb') as f:
                unpickler = RestrictedUnpickler(f)
                metadata = unpickler.load()
                compressed_data = f.read()
                expected_checksum = metadata["checksum"]
                actual_checksum = hashlib.sha256(compressed_data).hexdigest()
                if expected_checksum != actual_checksum:
                    raise ValueError(f"Checksum verification failed for backup {backup_id}")
                decompressed = zlib.decompress(compressed_data)
                unpickler = RestrictedUnpickler(io.BytesIO(decompressed))
                data = unpickler.load()
            self.recovery_history.append({
                "timestamp": time.time(),
                "component": component,
                "backup_id": backup_id,
                "backup_timestamp": metadata["timestamp"],
                "success": True
            })
            logger.info(f"Recovered component {component} from backup {backup_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to recover component {component} from backup {backup_id}: {e}")
            self.recovery_history.append({
                "timestamp": time.time(),
                "component": component,
                "backup_id": backup_id if backup_id else "latest",
                "success": False,
                "error": str(e)
            })
            return None
    def _load_backup_index(self):
        index_file = os.path.join(self.backup_dir, "backup_index.json")
        if not os.path.exists(index_file):
            return
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            for component, backups in index_data.items():
                if component in self.COMPONENTS:
                    self.component_backups[component] = backups
            logger.info(f"Loaded backup index with {sum(len(v) for v in self.component_backups.values())} backups")
        except Exception as e:
            logger.warning(f"Failed to load backup index: {e}")
    def _save_backup_index(self):
        index_file = os.path.join(self.backup_dir, "backup_index.json")
        try:
            index_data = {}
            for component, backups in self.component_backups.items():
                index_data[component] = []
                for backup in backups:
                    backup_copy = backup.copy()
                    for key, value in backup_copy.items():
                        if isinstance(value, (int, float)):
                            backup_copy[key] = value
                        elif isinstance(value, str):
                            backup_copy[key] = value
                        else:
                            backup_copy[key] = str(value)
                    index_data[component].append(backup_copy)
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup index: {e}")
    def _cleanup_old_backups(self, component: str):
        if component not in self.component_backups:
            return
        backups = self.component_backups[component]
        if len(backups) > 10:
            backups.sort(key=lambda x: x["timestamp"])
            to_delete = backups[:-10]
            for backup in to_delete:
                try:
                    if os.path.exists(backup["file"]):
                        os.remove(backup["file"])
                except Exception as e:
                    logger.warning(f"Failed to delete old backup {backup['id']}: {e}")
            self.component_backups[component] = backups[-10:]
            self._save_backup_index()
    def stats(self) -> Dict[str, Any]:
        total_backups = sum(len(v) for v in self.component_backups.values())
        successful_recoveries = sum(1 for r in self.recovery_history if r.get("success", False))
        total_recoveries = len(self.recovery_history)
        success_rate = successful_recoveries / total_recoveries if total_recoveries > 0 else 0.0
        backup_sizes = defaultdict(int)
        for component, backups in self.component_backups.items():
            for backup in backups:
                backup_sizes[component] += backup.get("size", 0)
        return {
            "total_backups": total_backups,
            "backups_by_component": {k: len(v) for k, v in self.component_backups.items()},
            "backup_sizes_mb": {k: v / (1024 * 1024) for k, v in backup_sizes.items()},
            "total_backup_size_mb": sum(backup_sizes.values()) / (1024 * 1024),
            "recovery_history_size": len(self.recovery_history),
            "recovery_success_rate": f"{success_rate:.1%}",
            "recent_recoveries": list(self.recovery_history)[-10] if self.recovery_history else []
        }

# ============================================
# REAL-TIME DASHBOARD (Preserved)
# ============================================

class RealTimeDashboard:
    def _run_server_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        loop.run_until_complete(self._start_server())
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.metrics_stream = deque(maxlen=1000)
        self.alert_rules = {}
        self.active_connections = set()
        self.dashboard_state = {}
        self.server = None
        self.last_alert_time = {}
        self._init_default_alerts()
        self.server_thread = threading.Thread(
            target=self._run_server_thread,
            daemon=True,
            name="DashboardServer"
        )
        self.server_thread.start()
        logger.info(f"RealTimeDashboard initialized (ws://{host}:{port})")
    def _init_default_alerts(self):
        self.alert_rules = {
            "high_memory_pressure": {
                "condition": lambda metrics: metrics.get("stm_utilization", 0) > 0.8,
                "message": "High memory pressure detected",
                "severity": "high",
                "cooldown": 300
            },
            "low_confidence": {
                "condition": lambda metrics: metrics.get("avg_confidence", 0.5) < 0.3,
                "message": "Low confidence in cognitive decisions",
                "severity": "medium",
                "cooldown": 600
            },
            "high_error_rate": {
                "condition": lambda metrics: metrics.get("error_rate_1min", 0) > 0.1,
                "message": "High operation error rate",
                "severity": "high",
                "cooldown": 300
            },
            "cache_inefficiency": {
                "condition": lambda metrics: metrics.get("cache_hit_rate", 0.0) < 0.3,
                "message": "Cache hit rate below threshold",
                "severity": "low",
                "cooldown": 900
            },
            "low_learning_impact": {
                "condition": lambda metrics: metrics.get("learning_weight", 0.7) < 0.4,
                "message": "Learning system has low impact on decisions",
                "severity": "medium",
                "cooldown": 1800
            },
            "high_free_energy": {
                "condition": lambda metrics: metrics.get("free_energy", 0) > 5.0,   # threshold reduced
                "message": "High free energy detected",
                "severity": "high",
                "cooldown": 600
            }
        }
    async def _start_server(self):
        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port
            )
            logger.info(f"Dashboard WebSocket server started on ws://{self.host}:{self.port}")
            await self.server.wait_closed()
        except Exception as e:
            logger.error(f"Failed to start dashboard server: {e}")
    async def _handle_connection(self, websocket, path):
        self.active_connections.add(websocket)
        client_id = id(websocket)
        try:
            logger.info(f"Dashboard client connected: {client_id}")
            await self._send_initial_state(websocket)
            async for message in websocket:
                if message == "ping":
                    await websocket.send("pong")
                elif message.startswith("request:"):
                    await self._handle_client_request(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Dashboard client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Dashboard connection error: {e}")
        finally:
            self.active_connections.remove(websocket)
    async def _send_initial_state(self, websocket):
        initial_state = {
            "type": "initial_state",
            "timestamp": time.time(),
            "system": {
                "version": "13.2",
                "start_time": time.time(),
                "status": "running"
            },
            "metrics": self._get_current_metrics(),
            "alerts": self._check_alerts()
        }
        await websocket.send(json.dumps(initial_state))
    async def _handle_client_request(self, websocket, message):
        try:
            request = json.loads(message[8:])
            request_type = request.get("type")
            if request_type == "historical_metrics":
                historical = {
                    "type": "historical_metrics",
                    "metrics": list(self.metrics_stream)[-100:]
                }
                await websocket.send(json.dumps(historical))
            elif request_type == "component_detail":
                component = request.get("component")
                detail = self._get_component_detail(component)
                response = {
                    "type": "component_detail",
                    "component": component,
                    "detail": detail
                }
                await websocket.send(json.dumps(response))
            elif request_type == "learning_insights":
                response = {
                    "type": "learning_insights",
                    "message": "Learning insights available through system API"
                }
                await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"Failed to handle client request: {e}")
    def update_metrics(self, metrics: Dict[str, Any]):
        timestamp = time.time()
        metric_entry = {
            "timestamp": timestamp,
            "metrics": metrics
        }
        self.metrics_stream.append(metric_entry)
        alerts = self._check_alerts()
        update = {
            "type": "metrics_update",
            "timestamp": timestamp,
            "metrics": metrics,
            "alerts": alerts
        }
        self._broadcast_update(update)
        self.dashboard_state = {
            "last_update": timestamp,
            "current_metrics": metrics,
            "active_alerts": alerts
        }
    def _check_alerts(self) -> List[Dict[str, Any]]:
        if not self.metrics_stream:
            return []
        current_metrics = self.metrics_stream[-1]["metrics"]
        current_time = time.time()
        active_alerts = []
        for alert_name, rule in self.alert_rules.items():
            last_alert = self.last_alert_time.get(alert_name, 0)
            if current_time - last_alert < rule["cooldown"]:
                continue
            try:
                if rule["condition"](current_metrics):
                    alert = {
                        "name": alert_name,
                        "message": rule["message"],
                        "severity": rule["severity"],
                        "timestamp": current_time,
                        "metrics": current_metrics
                    }
                    active_alerts.append(alert)
                    self.last_alert_time[alert_name] = current_time
                    logger.warning(f"ALERT [{rule['severity'].upper()}]: {rule['message']}")
            except Exception:
                continue
        return active_alerts
    def _broadcast_update(self, update: Dict[str, Any]):
        if not self.active_connections:
            return
        update_json = json.dumps(update)
        def broadcast():
            for websocket in list(self.active_connections):
                try:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send(update_json),
                        asyncio.get_event_loop()
                    )
                except Exception as e:
                    logger.debug(f"Failed to send update to client: {e}")
        threading.Thread(target=broadcast, daemon=True).start()
    def _get_current_metrics(self) -> Dict[str, Any]:
        if not self.metrics_stream:
            return {"status": "no_metrics_yet"}
        return self.metrics_stream[-1]["metrics"]
    def _get_component_detail(self, component: str) -> Dict[str, Any]:
        return {
            "component": component,
            "status": "unknown",
            "last_updated": time.time(),
            "note": "Component detail retrieval not fully implemented"
        }
    def stats(self) -> Dict[str, Any]:
        return {
            "active_connections": len(self.active_connections),
            "metrics_stream_size": len(self.metrics_stream),
            "alert_rules_count": len(self.alert_rules),
            "active_alerts_count": len(self.dashboard_state.get("active_alerts", [])),
            "server_running": self.server is not None,
            "server_address": f"ws://{self.host}:{self.port}",
            "last_update": self.dashboard_state.get("last_update", 0)
        }

# ============================================
# EXTENDED INSTRUCTION SET (Preserved)
# ============================================

class ExtendedInstructionSet:
    def __init__(self, core: 'Neuron657CoreV13'):
        self.core = core
        self.operation_stats = defaultdict(int)
        logger.info("ExtendedInstructionSet initialized")
    def CLUSTER(self, patterns: List[EnhancedPattern], k: int = 5) -> Dict[str, Any]:
        self.operation_stats["CLUSTER"] += 1
        start_time = time.time()
        try:
            if not patterns:
                return {
                    "ok": False,
                    "error": "No patterns provided",
                    "clusters": [],
                    "duration": time.time() - start_time
                }
            feature_vectors = []
            pattern_info = []
            for pattern in patterns:
                hdv = pattern.hyperdimensional_vector()
                if hdv is not None:
                    features = hdv.to_list()
                else:
                    features = self._extract_pattern_features(pattern)
                feature_vectors.append(features)
                pattern_info.append({
                    "hash": pattern.hash(),
                    "tags": pattern.tags,
                    "modality": pattern.modality
                })
            clusters = self._simple_clustering(feature_vectors, pattern_info, k)
            duration = time.time() - start_time
            return {
                "ok": True,
                "clusters": clusters,
                "pattern_count": len(patterns),
                "cluster_count": len(clusters),
                "duration": duration
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"CLUSTER operation failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "duration": duration
            }
    def _extract_pattern_features(self, pattern: EnhancedPattern) -> List[float]:
        features = []
        if hasattr(pattern, 'data') and pattern.data:
            data = pattern.data if isinstance(pattern.data, bytes) else bytes(pattern.data)
            features.append(len(data))
            features.append(sum(data) / len(data) if len(data) > 0 else 0)
            features.append(hashlib.sha256(data).digest()[0])
        if hasattr(pattern, 'tags'):
            features.append(len(pattern.tags))
            tag_hash = hash("|".join(sorted(pattern.tags))) % 1000
            features.append(tag_hash)
        modality_map = {"default": 0, "text": 1, "image": 2, "audio": 3, "custom": 4}
        modality = pattern.modality if hasattr(pattern, 'modality') else "default"
        features.append(modality_map.get(modality, 5))
        return features
    def _simple_clustering(self, feature_vectors: List[List[float]],
                          pattern_info: List[Dict], k: int) -> List[Dict]:
        if len(feature_vectors) <= k:
            clusters = []
            for i, (features, info) in enumerate(zip(feature_vectors, pattern_info)):
                clusters.append({
                    "cluster_id": i,
                    "patterns": [info],
                    "centroid": features,
                    "size": 1
                })
            return clusters
        MAX_ITERATIONS = 20
        centroids = [list(v) for v in feature_vectors[:k]]
        assignments = [-1] * len(feature_vectors)
        def _euclidean(a: List[float], b: List[float]) -> float:
            if len(a) != len(b):
                return float('inf')
            return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
        for iteration in range(MAX_ITERATIONS):
            new_assignments = []
            for features in feature_vectors:
                distances = [_euclidean(features, c) for c in centroids]
                new_assignments.append(distances.index(min(distances)))
            if new_assignments == assignments:
                logger.debug(f"K-means converged at iteration {iteration + 1}")
                break
            assignments = new_assignments
            for cluster_id in range(k):
                cluster_members = [
                    feature_vectors[i]
                    for i, a in enumerate(assignments)
                    if a == cluster_id
                ]
                if cluster_members:
                    dim = len(cluster_members[0])
                    centroids[cluster_id] = [
                        sum(vec[d] for vec in cluster_members) / len(cluster_members)
                        for d in range(dim)
                    ]
        clusters = []
        for cluster_id in range(k):
            cluster_patterns = [
                pattern_info[i]
                for i, a in enumerate(assignments)
                if a == cluster_id
            ]
            if cluster_patterns:
                clusters.append({
                    "cluster_id": cluster_id,
                    "patterns": cluster_patterns,
                    "centroid": centroids[cluster_id],
                    "size": len(cluster_patterns)
                })
        return clusters
    def ANALOGY(self, A: EnhancedPattern, B: EnhancedPattern,
                C: EnhancedPattern) -> Dict[str, Any]:
        self.operation_stats["ANALOGY"] += 1
        start_time = time.time()
        try:
            vector_A = A.hyperdimensional_vector()
            vector_B = B.hyperdimensional_vector()
            vector_C = C.hyperdimensional_vector()
            if not all([vector_A, vector_B, vector_C]):
                return {
                    "ok": False,
                    "error": "Could not create vector representations",
                    "duration": time.time() - start_time
                }
            list_A = vector_A.to_list()
            list_B = vector_B.to_list()
            list_C = vector_C.to_list()
            if len(list_A) != len(list_B) or len(list_A) != len(list_C):
                return {
                    "ok": False,
                    "error": "Vector dimension mismatch",
                    "duration": time.time() - start_time
                }
            analogy_vector = []
            for a, b, c in zip(list_A, list_B, list_C):
                value = c + (b - a)
                analogy_vector.append(value)
            analogy_hdv = HDCVector(analogy_vector)
            duration = time.time() - start_time
            return {
                "ok": True,
                "analogy_vector": analogy_vector[:10],
                "operation": "A:B :: C:?",
                "duration": duration
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"ANALOGY operation failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "duration": duration
            }
    def EVOLVE(self, pattern: EnhancedPattern,
               generations: int = 3) -> Dict[str, Any]:
        self.operation_stats["EVOLVE"] += 1
        start_time = time.time()
        try:
            if generations <= 0:
                return {
                    "ok": False,
                    "error": "Generations must be positive",
                    "duration": time.time() - start_time
                }
            evolution_path = []
            current_pattern = pattern
            for gen in range(generations):
                drift_amount = 0.1 * (1.0 - gen / generations)
                drifted = current_pattern.drift(drift_amount)
                mutated = self._apply_controlled_mutation(drifted, gen)
                evolution_path.append({
                    "generation": gen,
                    "hash": mutated.hash()[:8],
                    "drift_amount": drift_amount,
                    "similarity_to_original": current_pattern.similarity(pattern) if hasattr(current_pattern, 'similarity') else 0.0
                })
                current_pattern = mutated
            duration = time.time() - start_time
            return {
                "ok": True,
                "original_hash": pattern.hash()[:8],
                "final_hash": current_pattern.hash()[:8],
                "generations": generations,
                "evolution_path": evolution_path,
                "duration": duration
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"EVOLVE operation failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "duration": duration
            }
    def _apply_controlled_mutation(self, pattern: EnhancedPattern,
                                  generation: int) -> EnhancedPattern:
        if hasattr(pattern, 'data') and pattern.data:
            data_bytes = pattern.data
            mutated = EnhancedPattern(
                data=data_bytes,
                tags=pattern.tags.copy() if hasattr(pattern, 'tags') else [],
                modality=pattern.modality if hasattr(pattern, 'modality') else "default"
            )
            return mutated
        else:
            return EnhancedPattern(
                data=b'',
                tags=pattern.tags.copy() if hasattr(pattern, 'tags') else [],
                modality=pattern.modality if hasattr(pattern, 'modality') else "default"
            )
    def EXPLAIN(self, pattern: EnhancedPattern,
                depth: int = 2) -> Dict[str, Any]:
        self.operation_stats["EXPLAIN"] += 1
        start_time = time.time()
        try:
            pattern_hash = pattern.hash()
            pattern_info = {
                "hash": pattern_hash[:8],
                "tags": pattern.tags if hasattr(pattern, 'tags') else [],
                "modality": pattern.modality if hasattr(pattern, 'modality') else "default",
                "size": len(pattern.data) if hasattr(pattern, 'data') else 0
            }
            associations = []
            if hasattr(self.core, 'memory') and hasattr(self.core.memory, 'similarity_index'):
                try:
                    associations = self.core.memory.similarity_index.get_associations(
                        pattern_hash, limit=5
                    )
                except Exception:
                    pass
            context = self._gather_pattern_context(pattern, depth)
            duration = time.time() - start_time
            return {
                "ok": True,
                "pattern": pattern_info,
                "associations": associations,
                "context": context,
                "depth": depth,
                "duration": duration
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"EXPLAIN operation failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "duration": duration
            }
    def _gather_pattern_context(self, pattern: EnhancedPattern,
                               depth: int) -> Dict[str, Any]:
        context = {
            "basic_info": {
                "created": getattr(pattern, 'created_at', time.time()),
                "access_count": getattr(pattern, 'access_count', 0),
                "lifecycle_stage": getattr(pattern, 'lifecycle_stage', 'unknown')
            },
            "semantic_context": {
                "tags": pattern.tags if hasattr(pattern, 'tags') else [],
                "tag_categories": self._categorize_tags(pattern.tags if hasattr(pattern, 'tags') else [])
            },
            "structural_context": {
                "size": len(pattern.data) if hasattr(pattern, 'data') else 0,
                "entropy": getattr(pattern, 'pattern_entropy', 0.0)
            }
        }
        return context
    def _categorize_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        categories = {
            "type": [],
            "purpose": [],
            "attribute": [],
            "context": [],
            "other": []
        }
        type_keywords = ["image", "text", "audio", "data", "pattern", "file"]
        purpose_keywords = ["analysis", "storage", "processing", "search", "backup"]
        attribute_keywords = ["large", "small", "important", "temporary", "permanent"]
        context_keywords = ["work", "personal", "project", "test", "production"]
        for tag in tags:
            tag_lower = tag.lower()
            if any(keyword in tag_lower for keyword in type_keywords):
                categories["type"].append(tag)
            elif any(keyword in tag_lower for keyword in purpose_keywords):
                categories["purpose"].append(tag)
            elif any(keyword in tag_lower for keyword in attribute_keywords):
                categories["attribute"].append(tag)
            elif any(keyword in tag_lower for keyword in context_keywords):
                categories["context"].append(tag)
            else:
                categories["other"].append(tag)
        return {k: v for k, v in categories.items() if v}
    def stats(self) -> Dict[str, Any]:
        return {
            "operation_stats": dict(self.operation_stats),
            "total_operations": sum(self.operation_stats.values())
        }

# ============================================
# SPECIALIZED WORKERS SYSTEM (Preserved)
# ============================================

class SpecializedWorkers:
    WORKER_TYPES = {
        "io": 2,
        "compute": 4,
        "search": 3,
        "ml": 1,
        "maintenance": 1
    }
    def __init__(self):
        self.worker_pools = {}
        self.task_queues = defaultdict(deque)
        self.task_results = {}
        self.worker_stats = defaultdict(lambda: defaultdict(int))
        for worker_type, count in self.WORKER_TYPES.items():
            self.worker_pools[worker_type] = concurrent.futures.ThreadPoolExecutor(
                max_workers=count,
                thread_name_prefix=f"worker_{worker_type}"
            )
        self.dispatcher_thread = threading.Thread(
            target=self._dispatch_tasks,
            daemon=True,
            name="TaskDispatcher"
        )
        self.dispatcher_thread.start()
        logger.info(f"Specialized workers initialized: {self.WORKER_TYPES}")
    def submit_task(self, task_type: str, task_id: str,
                   function: Callable, *args, **kwargs) -> str:
        worker_type = self._map_task_to_worker(task_type)
        task = {
            "id": task_id,
            "type": task_type,
            "worker_type": worker_type,
            "function": function,
            "args": args,
            "kwargs": kwargs,
            "submitted": time.time(),
            "status": "queued"
        }
        self.task_queues[worker_type].append(task)
        self.worker_stats[worker_type]["submitted"] += 1
        logger.debug(f"Task {task_id} submitted to {worker_type} queue")
        return task_id
    def _map_task_to_worker(self, task_type: str) -> str:
        task_mapping = {
            "read": "io",
            "write": "io",
            "search": "search",
            "similarity": "search",
            "hdv_encode": "compute",
            "hdv_decode": "compute",
            "ml_inference": "ml",
            "training": "ml",
            "compression": "compute",
            "decompression": "compute",
            "cleanup": "maintenance",
            "backup": "maintenance",
            "snapshot": "maintenance"
        }
        return task_mapping.get(task_type, "compute")
    def _dispatch_tasks(self):
        while True:
            try:
                for worker_type, queue in self.task_queues.items():
                    if queue:
                        task = queue.popleft()
                        future = self.worker_pools[worker_type].submit(
                            self._execute_task, task
                        )
                        self.task_results[task["id"]] = {
                            "future": future,
                            "task": task,
                            "submitted": time.time()
                        }
                        self.worker_stats[worker_type]["dispatched"] += 1
                self._cleanup_old_results()
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Task dispatcher error: {e}")
                time.sleep(1)
    def _execute_task(self, task: Dict) -> Any:
        task_id = task["id"]
        worker_type = task["worker_type"]
        try:
            task["status"] = "running"
            task["started"] = time.time()
            result = task["function"](*task["args"], **task["kwargs"])
            task["status"] = "completed"
            task["completed"] = time.time()
            task["duration"] = task["completed"] - task["started"]
            self.worker_stats[worker_type]["completed"] += 1
            self.worker_stats[worker_type]["total_duration"] += task["duration"]
            logger.debug(f"Task {task_id} completed in {task['duration']:.3f}s")
            return result
        except Exception as e:
            task["status"] = "failed"
            task["completed"] = time.time()
            task["error"] = str(e)
            if "started" in task:
                task["duration"] = task["completed"] - task["started"]
            self.worker_stats[worker_type]["failed"] += 1
            logger.error(f"Task {task_id} failed: {e}")
            raise
    def _cleanup_old_results(self):
        current_time = time.time()
        cleanup_cutoff = current_time - 300
        task_ids_to_remove = []
        for task_id, task_info in self.task_results.items():
            if task_info["submitted"] < cleanup_cutoff:
                if task_info["future"].done():
                    task_ids_to_remove.append(task_id)
        for task_id in task_ids_to_remove:
            del self.task_results[task_id]
    def shutdown(self):
        for worker_type, pool in self.worker_pools.items():
            pool.shutdown(wait=True)
        logger.info("Specialized workers shutdown complete")
    def stats(self) -> Dict[str, Any]:
        stats = {}
        for worker_type in self.WORKER_TYPES.keys():
            pool_stats = dict(self.worker_stats[worker_type])
            completed = pool_stats.get("completed", 0)
            total_duration = pool_stats.get("total_duration", 0)
            if completed > 0:
                pool_stats["avg_duration"] = total_duration / completed
            pool_stats["queue_length"] = len(self.task_queues[worker_type])
            if worker_type in self.worker_pools:
                pool = self.worker_pools[worker_type]
                pool_stats["active_threads"] = pool._max_workers
            stats[worker_type] = pool_stats
        total_submitted = sum(s.get("submitted", 0) for s in stats.values())
        total_completed = sum(s.get("completed", 0) for s in stats.values())
        total_failed = sum(s.get("failed", 0) for s in stats.values())
        overall_stats = {
            "total_submitted": total_submitted,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "completion_rate": total_completed / total_submitted if total_submitted > 0 else 0,
            "worker_types": list(self.WORKER_TYPES.keys()),
            "active_tasks": len(self.task_results)
        }
        return {
            "overall": overall_stats,
            "by_worker_type": stats
        }

# ============================================
# FAILURE PREDICTOR (Preserved)
# ============================================

class FailurePredictor:
    def __init__(self):
        self.error_patterns = defaultdict(list)
        self.failure_history = deque(maxlen=100)
        self.prediction_model = None
        self.prediction_threshold = 0.7
        self._init_prediction_model()
        logger.info("FailurePredictor initialized")
    def _init_prediction_model(self):
        self.prediction_rules = [
            {
                "condition": lambda errors: len(errors) > 10,
                "weight": 0.3,
                "message": "High error frequency"
            },
            {
                "condition": lambda errors: any("memory" in str(e).lower() for e in errors),
                "weight": 0.4,
                "message": "Memory-related errors"
            },
            {
                "condition": lambda errors: any("timeout" in str(e).lower() for e in errors),
                "weight": 0.3,
                "message": "Timeout errors"
            },
            {
                "condition": lambda errors: any("integrity" in str(e).lower() for e in errors),
                "weight": 0.5,
                "message": "Integrity errors"
            }
        ]
    def record_error(self, error: Exception, context: Dict = None):
        error_entry = {
            "timestamp": time.time(),
            "error": str(error),
            "type": type(error).__name__,
            "context": context or {}
        }
        self.error_patterns[type(error).__name__].append(error_entry)
        cutoff = time.time() - 86400
        for error_type in list(self.error_patterns.keys()):
            self.error_patterns[error_type] = [
                e for e in self.error_patterns[error_type]
                if e["timestamp"] > cutoff
            ]
            if not self.error_patterns[error_type]:
                del self.error_patterns[error_type]
        logger.debug(f"Recorded error: {type(error).__name__}: {error}")
    def predict_failure(self, recent_errors: List[Dict] = None) -> float:
        errors_to_analyze = recent_errors or []
        for error_list in self.error_patterns.values():
            errors_to_analyze.extend(error_list[-10:])
        if not errors_to_analyze:
            return 0.0
        total_weight = 0.0
        matched_weight = 0.0
        for rule in self.prediction_rules:
            total_weight += rule["weight"]
            if rule["condition"](errors_to_analyze):
                matched_weight += rule["weight"]
        probability = matched_weight / total_weight if total_weight > 0 else 0.0
        error_count = len(errors_to_analyze)
        frequency_factor = min(1.0, error_count / 50.0)
        probability = 0.7 * probability + 0.3 * frequency_factor
        self.failure_history.append({
            "timestamp": time.time(),
            "probability": probability,
            "error_count": error_count,
            "error_types": list(set(e["type"] for e in errors_to_analyze))
        })
        return probability
    def get_failure_risk_assessment(self) -> Dict[str, Any]:
        current_probability = self.predict_failure([])
        error_analysis = {}
        for error_type, errors in self.error_patterns.items():
            if errors:
                recent_errors = [e for e in errors if time.time() - e["timestamp"] < 3600]
                error_analysis[error_type] = {
                    "total": len(errors),
                    "recent": len(recent_errors),
                    "last_occurrence": errors[-1]["timestamp"] if errors else 0
                }
        historical = list(self.failure_history)[-10:] if self.failure_history else []
        risk_level = "low"
        if current_probability > 0.7:
            risk_level = "high"
        elif current_probability > 0.4:
            risk_level = "medium"
        return {
            "current_risk": {
                "probability": current_probability,
                "level": risk_level,
                "threshold": self.prediction_threshold
            },
            "error_analysis": error_analysis,
            "historical_predictions": historical,
            "prediction_rules": [
                {
                    "message": r["message"],
                    "weight": r["weight"]
                }
                for r in self.prediction_rules
            ]
        }
    def get_recommendations(self) -> List[str]:
        recommendations = []
        risk_assessment = self.get_failure_risk_assessment()
        if risk_assessment["current_risk"]["level"] == "high":
            recommendations.extend([
                "Perform immediate system maintenance",
                "Check memory integrity",
                "Review recent error logs",
                "Consider rolling back to last stable state"
            ])
        elif risk_assessment["current_risk"]["level"] == "medium":
            recommendations.extend([
                "Schedule maintenance soon",
                "Monitor error rates closely",
                "Backup critical components",
                "Review system configuration"
            ])
        error_analysis = risk_assessment["error_analysis"]
        if "MemoryError" in error_analysis or "MemoryFullError" in error_analysis:
            recommendations.append("Increase memory allocation or clean up unused patterns")
        if "TimeoutError" in error_analysis:
            recommendations.append("Adjust operation timeouts or optimize slow operations")
        if "IntegrityError" in error_analysis:
            recommendations.append("Run integrity checks and repair corrupted data")
        return list(set(recommendations))
    def stats(self) -> Dict[str, Any]:
        risk_assessment = self.get_failure_risk_assessment()
        total_errors = sum(len(errors) for errors in self.error_patterns.values())
        return {
            "current_risk": risk_assessment["current_risk"],
            "total_errors_tracked": total_errors,
            "error_types_tracked": len(self.error_patterns),
            "historical_predictions_count": len(self.failure_history),
            "recommendations": self.get_recommendations()
        }

# ============================================
# NEW MODULES FOR v13.0 - Free Energy Based Self-Modeling (IMPROVED)
# ============================================

class SelfModel:
    """
    SelfModel tracks the system's own behavior: strategy effectiveness,
    decision latency, failure patterns, cognitive cost, and reasoning history.
    It provides aggregated insights to the MetaLearner and Planner.
    Extended in v13.0 to track free energy and prediction errors.
    """
    def __init__(self, max_history: int = 1000):
        self._history = deque(maxlen=max_history)          # reasoning episodes
        self._strategy_stats = defaultdict(lambda: {
            'count': 0, 'successes': 0, 'total_latency': 0.0,
            'failures': 0, 'contexts': defaultdict(int),
            'total_free_energy_reduction': 0.0,
            'total_prediction_error': 0.0,
            'total_cost': 0.0      # added to compute average cost
        })
        self._free_energy_history = deque(maxlen=max_history)
        self._prediction_error_history = deque(maxlen=max_history)
        self._lock = threading.RLock()
        logger.info("SelfModel initialized (v13.1)")

    def record_reasoning(self, strategy: str, context: Dict, latency: float,
                         success: bool, cost: float, details: Dict = None,
                         free_energy_reduction: float = 0.0,
                         prediction_error: float = 0.0):
        """
        Record a reasoning episode.
        :param strategy: strategy used
        :param context: context dict (e.g., pattern_size, memory_pressure)
        :param latency: decision time in seconds
        :param success: whether the outcome was successful
        :param cost: estimated cognitive cost (from EnergyManager)
        :param details: optional extra info
        :param free_energy_reduction: how much free energy was reduced by this action
        :param prediction_error: prediction error of world model before/after
        """
        with self._lock:
            episode = {
                'timestamp': time.time(),
                'strategy': strategy,
                'context': context.copy(),
                'latency': latency,
                'success': success,
                'cost': cost,
                'details': details or {},
                'free_energy_reduction': free_energy_reduction,
                'prediction_error': prediction_error
            }
            self._history.append(episode)
            self._free_energy_history.append(free_energy_reduction)
            self._prediction_error_history.append(prediction_error)

            stats = self._strategy_stats[strategy]
            stats['count'] += 1
            stats['total_latency'] += latency
            stats['total_cost'] += cost
            if success:
                stats['successes'] += 1
            else:
                stats['failures'] += 1
            # compress context to a key for histogram
            ctx_key = self._context_to_key(context)
            stats['contexts'][ctx_key] += 1
            stats['total_free_energy_reduction'] += free_energy_reduction
            stats['total_prediction_error'] += prediction_error

    def get_strategy_effectiveness(self, strategy: str, context: Dict = None) -> float:
        """
        Return success rate for a strategy, optionally filtered by context.
        """
        with self._lock:
            if strategy not in self._strategy_stats:
                return 0.5
            stats = self._strategy_stats[strategy]
            if context is None:
                # overall success rate
                if stats['count'] == 0:
                    return 0.5
                return stats['successes'] / stats['count']
            # context-specific
            ctx_key = self._context_to_key(context)
            # we need per-context counts – for simplicity, scan history
            total = 0
            successes = 0
            for ep in self._history:
                if ep['strategy'] == strategy and self._context_to_key(ep['context']) == ctx_key:
                    total += 1
                    if ep['success']:
                        successes += 1
            return successes / total if total > 0 else 0.5

    def get_average_latency(self, strategy: str = None) -> float:
        with self._lock:
            if strategy:
                if strategy not in self._strategy_stats:
                    return 0.0
                stats = self._strategy_stats[strategy]
                return stats['total_latency'] / stats['count'] if stats['count'] > 0 else 0.0
            # overall average
            total = sum(s['total_latency'] for s in self._strategy_stats.values())
            count = sum(s['count'] for s in self._strategy_stats.values())
            return total / count if count > 0 else 0.0

    def get_average_cost(self, strategy: str = None) -> float:
        """
        Return average cognitive cost for a strategy or overall.
        """
        with self._lock:
            if strategy:
                if strategy not in self._strategy_stats:
                    return 1.0
                stats = self._strategy_stats[strategy]
                return stats['total_cost'] / stats['count'] if stats['count'] > 0 else 1.0
            total_cost = sum(s['total_cost'] for s in self._strategy_stats.values())
            count = sum(s['count'] for s in self._strategy_stats.values())
            return total_cost / count if count > 0 else 1.0

    def get_average_free_energy_reduction(self, strategy: str = None) -> float:
        with self._lock:
            if strategy:
                if strategy not in self._strategy_stats:
                    return 0.0
                stats = self._strategy_stats[strategy]
                return stats['total_free_energy_reduction'] / stats['count'] if stats['count'] > 0 else 0.0
            total = sum(s['total_free_energy_reduction'] for s in self._strategy_stats.values())
            count = sum(s['count'] for s in self._strategy_stats.values())
            return total / count if count > 0 else 0.0

    def get_failure_patterns(self, min_occurrences: int = 3) -> List[Dict]:
        """
        Detect recurring failure patterns based on context.
        Returns a list of contexts where failures are frequent.
        """
        with self._lock:
            # aggregate failures by context key
            failures_by_ctx = defaultdict(lambda: {'total': 0, 'failures': 0})
            for ep in self._history:
                key = self._context_to_key(ep['context'])
                failures_by_ctx[key]['total'] += 1
                if not ep['success']:
                    failures_by_ctx[key]['failures'] += 1
            patterns = []
            for key, vals in failures_by_ctx.items():
                if vals['total'] >= min_occurrences and vals['failures'] / vals['total'] > 0.3:
                    patterns.append({
                        'context_key': key,
                        'failure_rate': vals['failures'] / vals['total'],
                        'occurrences': vals['total']
                    })
            return patterns

    def get_recent_history(self, limit: int = 100) -> List[Dict]:
        with self._lock:
            return list(self._history)[-limit:]

    def _context_to_key(self, ctx: Dict) -> str:
        # Improved: filter out keys that might accidentally include strategy, and round floats
        parts = []
        for k, v in sorted(ctx.items()):
            if k == 'strategy':  # never include strategy in context key
                continue
            if isinstance(v, float):
                # round to 2 decimals to avoid long strings
                parts.append(f"{k}:{v:.2f}")
            elif isinstance(v, (int, str)):
                parts.append(f"{k}:{v}")
            # ignore other types
        return "_".join(parts)

    def stats(self) -> Dict:
        with self._lock:
            return {
                'history_size': len(self._history),
                'strategies_tracked': list(self._strategy_stats.keys()),
                'average_latency': self.get_average_latency(),
                'average_cost': self.get_average_cost(),
                'average_free_energy_reduction': self.get_average_free_energy_reduction(),
                'failure_patterns': self.get_failure_patterns(),
                'free_energy_history_length': len(self._free_energy_history),
                'prediction_error_history_length': len(self._prediction_error_history)
            }


class WorldModel:
    """
    WorldModel stores environmental patterns, learns state transitions,
    and predicts outcomes of actions. It uses a graph of cognitive states
    and transitions induced by reasoning strategies.
    Extended in v13.0 to compute prediction error and uncertainty.
    """
    def __init__(self, max_states: int = 1000):
        self._states = {}               # state_id -> EnhancedPattern (or hash)
        self._transitions = defaultdict(list)  # (from_state_id, action) -> list of (to_state_id, count, outcomes)
        self._max_states = max_states
        self._lock = threading.RLock()
        self._prediction_errors = deque(maxlen=1000)  # store last prediction errors
        logger.info("WorldModel initialized (v13.0)")

    def observe_transition(self, from_state: CognitiveState, action: str,
                           to_state: CognitiveState, outcome: Dict):
        """
        Record a transition caused by an action (reasoning strategy).
        The outcome dict should contain at least 'confidence' and 'success'.
        Also compute prediction error if a prediction existed.
        """
        with self._lock:
            from_id = from_state.state_id
            to_id = to_state.state_id
            # ensure states are stored (as pattern hashes for simplicity)
            if from_id not in self._states:
                self._states[from_id] = from_state.snapshot_serializable()
            if to_id not in self._states:
                self._states[to_id] = to_state.snapshot_serializable()

            key = (from_id, action)
            transitions = self._transitions[key]
            # compute prediction error if we have previous transitions
            pred_error = 0.0
            if transitions:
                # simple prediction: most common next state
                next_state_counts = defaultdict(int)
                for t in transitions:
                    next_state_counts[t['to_state']] += 1
                most_common = max(next_state_counts.items(), key=lambda x: x[1])[0]
                if most_common != to_id:
                    pred_error = 1.0  # misprediction
                else:
                    pred_error = 0.0
                # also could compute confidence error
            else:
                pred_error = 1.0  # no prior info

            self._prediction_errors.append(pred_error)

            transitions.append({
                'to_state': to_id,
                'timestamp': time.time(),
                'outcome': outcome,
                'prediction_error': pred_error
            })
            # limit list size
            if len(transitions) > 100:
                self._transitions[key] = transitions[-100:]

    def predict_outcome(self, from_state: CognitiveState, action: str) -> Dict:
        """
        Predict the most likely outcome (next state and expected metrics)
        given current state and action.
        Returns dict with keys: 'next_state_id', 'confidence', 'success_probability',
        'uncertainty', 'prediction_error_estimate'.
        """
        with self._lock:
            from_id = from_state.state_id
            key = (from_id, action)
            transitions = self._transitions.get(key, [])
            if not transitions:
                # fallback – use generic outcome based on action profile
                return {
                    'next_state_id': None,
                    'confidence': 0.5,
                    'success_probability': 0.5,
                    'uncertainty': 1.0,
                    'prediction_error_estimate': 1.0
                }
            # aggregate recent transitions
            recent = transitions[-50:]
            # count frequencies of next states
            next_state_counts = defaultdict(int)
            total = 0
            sum_confidence = 0.0
            successes = 0
            sum_pred_error = 0.0
            for t in recent:
                next_state_counts[t['to_state']] += 1
                total += 1
                sum_confidence += t['outcome'].get('confidence', 0.5)
                if t['outcome'].get('success', False):
                    successes += 1
                sum_pred_error += t.get('prediction_error', 0.0)
            most_common_next = max(next_state_counts.items(), key=lambda x: x[1])[0]
            prob = next_state_counts[most_common_next] / total
            # entropy as uncertainty
            entropy = 0.0
            for count in next_state_counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)
            max_entropy = math.log2(len(next_state_counts)) if next_state_counts else 1.0
            uncertainty = entropy / max_entropy if max_entropy > 0 else 1.0
            avg_pred_error = sum_pred_error / total
            return {
                'next_state_id': most_common_next,
                'confidence': sum_confidence / total,
                'success_probability': successes / total,
                'uncertainty': uncertainty,
                'prediction_error_estimate': avg_pred_error
            }

    def get_similar_states(self, state: CognitiveState, top_k: int = 5) -> List[str]:
        """
        Find states similar to the given one (by context/pattern).
        For now, use simple heuristic: same mode/status.
        """
        with self._lock:
            candidates = []
            for sid, sdata in self._states.items():
                if sdata.get('mode') == state.mode.value and sdata.get('status') == state.status.value:
                    candidates.append(sid)
            return candidates[:top_k]

    def get_average_prediction_error(self, window: int = 100) -> float:
        with self._lock:
            if not self._prediction_errors:
                return 0.0
            recent = list(self._prediction_errors)[-window:]
            return sum(recent) / len(recent)

    def stats(self) -> Dict:
        with self._lock:
            return {
                'states': len(self._states),
                'transitions': sum(len(v) for v in self._transitions.values()),
                'unique_actions': len(set(k[1] for k in self._transitions.keys())),
                'avg_prediction_error': self.get_average_prediction_error(),
                'prediction_error_history': len(self._prediction_errors)
            }


class CognitivePlanner:
    """
    CognitivePlanner simulates alternative reasoning strategies,
    estimates expected outcomes, and recommends the best action.
    Extended in v13.0 to use expected free energy as primary criterion.
    Now supports multi-step planning via simulate_deep, and MCTS.
    """
    def __init__(self, world_model: WorldModel, self_model: SelfModel,
                 energy_manager: 'EnergyManager', identity_memory: 'IdentityMemory',
                 max_depth: int = 3, use_mcts: bool = True,
                 mcts_simulations: int = 100, mcts_exploration: float = 1.4):
        self.world = world_model
        self.self_model = self_model
        self.energy = energy_manager
        self.identity = identity_memory
        self.max_depth = max_depth
        self.use_mcts = use_mcts
        if use_mcts:
            self.mcts = MCTSPlanner(
                world_model=world_model,
                energy_manager=energy_manager,
                identity_memory=identity_memory,
                max_depth=max_depth,
                num_simulations=mcts_simulations,
                exploration_constant=mcts_exploration
            )
        else:
            self.mcts = None
        self._lock = threading.RLock()
        logger.info("CognitivePlanner initialized (v13.1 with MCTS)")

    def plan_strategy(self, current_state: CognitiveState,
                      available_strategies: List[str],
                      context: Dict, depth: int = 1) -> Dict:
        """
        Simulate each strategy (or sequence) and return the best one based on expected free energy.
        If depth > 1 and MCTS is enabled, uses MCTS to find best sequence.
        Returns dict: {'strategy': str, 'expected_confidence': float,
                       'expected_success': float, 'cost': float, 'depth': int,
                       'expected_free_energy': float, 'plan': list (optional)}
        """
        if depth == 1 or not self.use_mcts:
            # Original one-step planning (same as before)
            best = None
            best_fe = float('inf')
            results = []
            for strategy in available_strategies:
                cost = self.energy.estimate_strategy_cost(strategy, context)
                if not self.energy.can_afford(cost * depth):
                    continue
                outcome = self.world.predict_outcome(current_state, strategy)
                effectiveness = self.self_model.get_strategy_effectiveness(strategy, context)
                expected_success = outcome.get('success_probability', 0.5) * 0.6 + effectiveness * 0.4
                expected_confidence = outcome.get('confidence', 0.5)
                uncertainty = outcome.get('uncertainty', 1.0)
                pred_error_est = outcome.get('prediction_error_estimate', 1.0)
                norm_cost = cost / (self.energy._max_budget + 1e-6)
                inconsistency = self.identity.get_inconsistency(current_state.free_energy) if self.identity else 0.0
                expected_free_energy = self.energy.compute_free_energy(pred_error_est, uncertainty, norm_cost, inconsistency)
                res = {
                    'strategy': strategy,
                    'expected_confidence': expected_confidence,
                    'expected_success': expected_success,
                    'cost': cost,
                    'expected_free_energy': expected_free_energy,
                    'uncertainty': uncertainty,
                    'prediction_error_estimate': pred_error_est,
                    'depth': 1
                }
                results.append(res)
                if expected_free_energy < best_fe:
                    best_fe = expected_free_energy
                    best = res
            if best is None:
                cheapest = min(available_strategies,
                               key=lambda s: self.energy.estimate_strategy_cost(s, context))
                return {
                    'strategy': cheapest,
                    'expected_confidence': 0.5,
                    'expected_success': 0.5,
                    'cost': self.energy.estimate_strategy_cost(cheapest, context),
                    'expected_free_energy': float('inf'),
                    'fallback': True
                }
            return best
        else:
            # Use MCTS for multi-step planning
            if self.mcts is None:
                logger.error("MCTS not initialized but use_mcts=True")
                return self.plan_strategy(current_state, available_strategies, context, depth=1)
            best_action, best_plan, expected_outcome = self.mcts.search(
                current_state, available_strategies, context
            )
            if best_action is None:
                cheapest = min(available_strategies,
                               key=lambda s: self.energy.estimate_strategy_cost(s, context))
                return {
                    'strategy': cheapest,
                    'expected_confidence': 0.5,
                    'expected_success': 0.5,
                    'cost': self.energy.estimate_strategy_cost(cheapest, context),
                    'expected_free_energy': float('inf'),
                    'fallback': True
                }
            outcome = self.world.predict_outcome(current_state, best_action)
            effectiveness = self.self_model.get_strategy_effectiveness(best_action, context)
            expected_success = outcome.get('success_probability', 0.5) * 0.6 + effectiveness * 0.4
            expected_confidence = outcome.get('confidence', 0.5)
            cost = self.energy.estimate_strategy_cost(best_action, context)
            expected_free_energy = expected_outcome.get('expected_free_energy', outcome.get('prediction_error_estimate', 1.0))
            return {
                'strategy': best_action,
                'expected_confidence': expected_confidence,
                'expected_success': expected_success,
                'cost': cost,
                'expected_free_energy': expected_free_energy,
                'plan': best_plan,
                'depth': depth
            }

    def simulate_deep(self, current_state: CognitiveState,
                      strategy_sequence: List[str],
                      context: Dict) -> Dict:
        """
        Simulate a sequence of strategies (plan) and return cumulative outcome.
        Computes total expected free energy for the sequence.
        Returns dict with final metrics and step-by-step outcomes.
        """
        cumulative_fe = 0.0
        cumulative_confidence = 1.0
        cumulative_success = 1.0
        total_cost = 0.0
        state = current_state
        step_outcomes = []
        for i, strategy in enumerate(strategy_sequence):
            outcome = self.world.predict_outcome(state, strategy)
            step_outcomes.append(outcome)
            cumulative_confidence *= outcome.get('confidence', 0.5)
            cumulative_success *= outcome.get('success_probability', 0.5)
            cost = self.energy.estimate_strategy_cost(strategy, context)
            total_cost += cost
            # free energy for this step
            fe_prediction = outcome.get('prediction_error_estimate', 1.0)
            fe_uncertainty = outcome.get('uncertainty', 1.0)
            fe_cost = cost / (self.energy._max_budget + 1e-6)
            cumulative_fe += fe_prediction + fe_uncertainty + fe_cost
            # update state (simulated) – for simplicity we don't change state
        return {
            'final_confidence': cumulative_confidence,
            'final_success_prob': cumulative_success,
            'total_cost': total_cost,
            'total_expected_free_energy': cumulative_fe,
            'sequence': strategy_sequence,
            'step_outcomes': step_outcomes
        }


class EnergyManager:
    """
    EnergyManager models cognitive energy: estimates costs and enforces budgets.
    It controls how deep the system can reason.
    Extended in v13.0 to compute free energy and control reasoning depth.
    """
    def __init__(self, initial_budget: float = 100.0, refill_rate: float = 1.0):
        self._budget = initial_budget
        self._max_budget = initial_budget
        self._refill_rate = refill_rate          # per second
        self._last_update = time.time()
        self._lock = threading.RLock()
        self._cost_models = {
            'byte': {'base': 1.0, 'per_byte': 0.001},
            'hdv': {'base': 2.0, 'per_dim': 0.0005},
            'semantic': {'base': 1.5, 'per_tag': 0.1},
            'hybrid': {'base': 3.0, 'factor': 1.0},
        }
        # free energy components (weights)
        self.weights = {
            'prediction_error': 1.0,
            'uncertainty': 0.5,
            'cost': 0.2,
            'inconsistency': 0.3
        }
        self.current_free_energy = 0.0
        logger.info("EnergyManager initialized (v13.0)")

    def _refill(self):
        now = time.time()
        elapsed = now - self._last_update
        self._budget = min(self._max_budget, self._budget + elapsed * self._refill_rate)
        self._last_update = now

    def estimate_strategy_cost(self, strategy: str, context: Dict) -> float:
        """
        Estimate cost of applying a strategy given context.
        """
        model = self._cost_models.get(strategy, {'base': 1.0})
        cost = model['base']
        if strategy == 'byte':
            size = context.get('pattern_size', 0)
            cost += size * model.get('per_byte', 0)
        elif strategy == 'hdv':
            dims = context.get('hdv_dimensions', 1000)
            cost += dims * model.get('per_dim', 0)
        elif strategy == 'semantic':
            tags = context.get('pattern_tags', [])
            cost += len(tags) * model.get('per_tag', 0)
        return cost

    def can_afford(self, cost: float) -> bool:
        with self._lock:
            self._refill()
            return self._budget >= cost

    def spend(self, cost: float) -> bool:
        with self._lock:
            self._refill()
            if self._budget >= cost:
                self._budget -= cost
                return True
            return False

    def get_available_energy(self) -> float:
        with self._lock:
            self._refill()
            return self._budget

    def set_budget(self, new_budget: float):
        with self._lock:
            self._max_budget = new_budget
            self._budget = min(self._budget, new_budget)

    def compute_free_energy(self, prediction_error: float, uncertainty: float,
                            cost: float, inconsistency: float = 0.0) -> float:
        """
        Compute free energy as weighted sum of components.
        Note: cost should be a normalized value (e.g., average cost / max_budget)
        """
        return (self.weights['prediction_error'] * prediction_error +
                self.weights['uncertainty'] * uncertainty +
                self.weights['cost'] * cost +
                self.weights['inconsistency'] * inconsistency)

    def update_free_energy(self, world_model: WorldModel, self_model: SelfModel,
                           identity_memory: 'IdentityMemory'):
        """
        Update current free energy based on system state.
        """
        pred_error = world_model.get_average_prediction_error()
        # uncertainty: average uncertainty from world model? For simplicity use 1 - average confidence
        # but we can compute from world model's transitions.
        # We'll approximate with 1 - avg_confidence
        avg_confidence = 0.5  # placeholder, should come from metrics
        uncertainty = 1.0 - avg_confidence
        # cost: recent average cost from self model (normalized)
        avg_cost = self_model.get_average_cost() / self._max_budget
        # inconsistency: from identity memory? placeholder
        inconsistency = 0.0
        self.current_free_energy = self.compute_free_energy(pred_error, uncertainty, avg_cost, inconsistency)
        return self.current_free_energy

    def get_reasoning_depth(self, base_depth: int = 3) -> int:
        """
        Dynamically adjust reasoning depth based on available energy and free energy.
        """
        with self._lock:
            self._refill()
            if self._budget < 10:
                return 1
            elif self._budget < 30:
                return 2
            elif self.current_free_energy > 5.0:
                return min(base_depth + 1, 5)  # deeper reasoning if high free energy
            else:
                return base_depth

    def stats(self) -> Dict:
        with self._lock:
            self._refill()
            return {
                'budget': self._budget,
                'max_budget': self._max_budget,
                'refill_rate': self._refill_rate,
                'current_free_energy': self.current_free_energy,
                'weights': self.weights
            }


class IdentityMemory:
    """
    IdentityMemory stores long-term beliefs, goals, and historical decisions.
    It provides continuity across sessions.
    Extended in v13.0 to store free energy targets and consistency checks.
    """
    def __init__(self, storage_path: str = "identity_memory.json"):
        self.storage_path = storage_path
        self._goals = []               # list of goal dicts
        self._beliefs = {}              # key -> belief (any)
        self._decision_history = deque(maxlen=10000)
        self._free_energy_target = 5.0  # desired free energy level
        self._lock = threading.RLock()
        self._load()
        logger.info("IdentityMemory initialized (v13.0)")

    def add_goal(self, goal: str, priority: float = 1.0, deadline: float = None):
        with self._lock:
            self._goals.append({
                'id': hashlib.md5(f"{goal}{time.time()}".encode()).hexdigest()[:8],
                'goal': goal,
                'priority': priority,
                'created': time.time(),
                'deadline': deadline,
                'active': True
            })
            self._save()

    def get_active_goals(self) -> List[Dict]:
        with self._lock:
            now = time.time()
            return [g for g in self._goals if g.get('active', True) and
                    (g.get('deadline') is None or g['deadline'] > now)]

    def update_belief(self, key: str, value: Any):
        with self._lock:
            self._beliefs[key] = value
            self._save()

    def get_belief(self, key: str, default=None) -> Any:
        with self._lock:
            return self._beliefs.get(key, default)

    def record_decision(self, decision: Dict):
        """
        Record a significant decision (e.g., strategy change, goal achievement).
        """
        with self._lock:
            self._decision_history.append({
                'timestamp': time.time(),
                'decision': decision
            })
            self._save()

    def get_long_term_trend(self, metric: str, window_days: int = 7) -> Dict:
        """
        Compute trend for a metric from decision history.
        """
        cutoff = time.time() - window_days * 86400
        relevant = [d for d in self._decision_history if d['timestamp'] > cutoff]
        values = [d['decision'].get(metric, 0) for d in relevant if metric in d['decision']]
        if not values:
            return {'available': False}
        return {
            'available': True,
            'current': values[-1] if values else 0,
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }

    def get_inconsistency(self, current_free_energy: float) -> float:
        """
        Compute inconsistency between current free energy and long-term target.
        """
        return abs(current_free_energy - self._free_energy_target) / (self._free_energy_target + 1e-6)

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self._goals = data.get('goals', [])
                    self._beliefs = data.get('beliefs', {})
                    self._free_energy_target = data.get('free_energy_target', 5.0)
                    logger.info("IdentityMemory loaded from %s", self.storage_path)
            except Exception as e:
                logger.error("Failed to load identity memory: %s", e)

    def _save(self):
        try:
            data = {
                'goals': self._goals[-100:],
                'beliefs': self._beliefs,
                'free_energy_target': self._free_energy_target
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save identity memory: %s", e)

    def stats(self) -> Dict:
        with self._lock:
            return {
                'goals': len(self._goals),
                'active_goals': len(self.get_active_goals()),
                'beliefs': len(self._beliefs),
                'decision_history': len(self._decision_history),
                'free_energy_target': self._free_energy_target
            }


# ============================================
# MCTS PLANNER - Monte Carlo Tree Search for Multi-Step Planning
# ============================================

class MCTSNode:
    __slots__ = ('state', 'parent', 'children', 'visits', 'value', 'action', 'prior')
    def __init__(self, state, parent=None, action=None, prior=1.0):
        self.state = state          # CognitiveState object
        self.parent = parent
        self.children = {}           # action -> MCTSNode
        self.visits = 0
        self.value = 0.0             # total reward (sum of -free_energy)
        self.action = action
        self.prior = prior

    def is_fully_expanded(self, available_actions):
        return len(self.children) == len(available_actions)

    def best_child(self, c, available_actions):
        best = None
        best_score = -float('inf')
        for action, child in self.children.items():
            if child.visits == 0:
                ucb = float('inf')
            else:
                q = child.value / child.visits
                ucb = q + c * (self.visits ** 0.5) / (1 + child.visits) * child.prior
            if ucb > best_score:
                best_score = ucb
                best = child
        return best


class MCTSPlanner:
    def __init__(self, world_model, energy_manager, identity_memory,
                 max_depth=5, num_simulations=100, exploration_constant=1.4):
        self.world_model = world_model
        self.energy_manager = energy_manager
        self.identity_memory = identity_memory
        self.max_depth = max_depth
        self.num_simulations = num_simulations
        self.c = exploration_constant

    def search(self, current_state, available_actions, context):
        root = MCTSNode(state=current_state)
        for _ in range(self.num_simulations):
            node = root
            depth = 0
            # Selection
            while node.is_fully_expanded(available_actions) and node.children:
                node = node.best_child(self.c, available_actions)
                depth += 1
                if depth >= self.max_depth:
                    break

            # Expansion (if depth not reached and node not fully expanded)
            if depth < self.max_depth and not node.is_fully_expanded(available_actions):
                unexpanded = [a for a in available_actions if a not in node.children]
                action = random.choice(unexpanded)
                outcome = self.world_model.predict_outcome(node.state, action)
                next_state_id = outcome.get('next_state_id')
                if next_state_id is None:
                    continue
                next_state_dict = self.world_model._states.get(next_state_id)
                if next_state_dict is None:
                    continue
                next_state = CognitiveState.from_serializable(next_state_dict)
                reward = -self._compute_expected_free_energy(node.state, action, outcome, context)

                child = MCTSNode(state=next_state, parent=node, action=action, prior=1.0)
                node.children[action] = child
                node = child
                depth += 1
                total_reward = reward

                # Simulation (rollout) with random actions
                sim_state = next_state
                for d in range(depth, self.max_depth):
                    sim_action = random.choice(available_actions)
                    sim_outcome = self.world_model.predict_outcome(sim_state, sim_action)
                    sim_next_id = sim_outcome.get('next_state_id')
                    if sim_next_id is None:
                        break
                    sim_next_dict = self.world_model._states.get(sim_next_id)
                    if sim_next_dict is None:
                        break
                    sim_next_state = CognitiveState.from_serializable(sim_next_dict)
                    sim_reward = -self._compute_expected_free_energy(sim_state, sim_action, sim_outcome, context)
                    total_reward += sim_reward
                    sim_state = sim_next_state

                # Backpropagation
                while node is not None:
                    node.visits += 1
                    node.value += total_reward
                    node = node.parent
            else:
                # Leaf node – no expansion possible (depth limit reached or no actions)
                # We could use a heuristic value, but we skip backpropagation in this simple version.
                pass

        # Choose best action from root (by highest visits)
        best_action = None
        best_visits = -1
        best_child = None
        for action, child in root.children.items():
            if child.visits > best_visits:
                best_visits = child.visits
                best_action = action
                best_child = child

        if best_action is None:
            best_action = available_actions[0] if available_actions else None
            best_child = None

        # Build best plan (greedy following highest visits)
        plan = [best_action] if best_action else []
        node = best_child
        while node and node.children:
            next_child = max(node.children.values(), key=lambda c: c.visits)
            plan.append(next_child.action)
            node = next_child

        expected_outcome = {}
        if best_child and best_child.visits > 0:
            expected_outcome['expected_free_energy'] = -best_child.value / best_child.visits

        return best_action, plan, expected_outcome

    def _compute_expected_free_energy(self, from_state, action, outcome, context):
        prediction_error = outcome.get('prediction_error_estimate', 1.0)
        uncertainty = outcome.get('uncertainty', 1.0)
        cost = self.energy_manager.estimate_strategy_cost(action, context)
        norm_cost = cost / (self.energy_manager._max_budget + 1e-6)
        current_free_energy = from_state.free_energy if hasattr(from_state, 'free_energy') else 0.0
        inconsistency = self.identity_memory.get_inconsistency(current_free_energy) if self.identity_memory else 0.0
        return self.energy_manager.compute_free_energy(prediction_error, uncertainty, norm_cost, inconsistency)


# ============================================
# NEW MODULES - EXTENDED ARCHITECTURE (v13.2)
# ============================================

# Interfaces (abstract base classes) for loose coupling
class IWorldModel(ABC):
    @abstractmethod
    def update(self, state, action, next_state, outcome):
        pass
    @abstractmethod
    def predict(self, state, action):
        pass

class IEpisodicMemory(ABC):
    @abstractmethod
    def store(self, episode):
        pass
    @abstractmethod
    def sample(self, n):
        pass
    @abstractmethod
    def retrieve_similar(self, query_state, k):
        pass

class IGoalManager(ABC):
    @abstractmethod
    def add_goal(self, goal, priority, deadline):
        pass
    @abstractmethod
    def get_active_goals(self):
        pass
    @abstractmethod
    def update_progress(self, goal_id, progress):
        pass

class IIntentionSystem(ABC):
    @abstractmethod
    def set_intention(self, goal):
        pass
    @abstractmethod
    def get_current_intention(self):
        pass

class IAttentionSystem(ABC):
    @abstractmethod
    def select_relevant(self, state):
        pass

class IUncertaintyEstimator(ABC):
    @abstractmethod
    def estimate(self, state, action):
        pass

class ICuriosityModule(ABC):
    @abstractmethod
    def compute_intrinsic_reward(self, state, action, next_state):
        pass

class IMetaCognitionModule(ABC):
    @abstractmethod
    def update(self, decision, outcome):
        pass
    @abstractmethod
    def get_self_assessment(self):
        pass

class IStrategySelector(ABC):
    @abstractmethod
    def select_strategy(self, context):
        pass

class ITheoryOfMind(ABC):
    @abstractmethod
    def predict_other(self, agent_id, state):
        pass


# Concrete implementations (simplified but functional)
class FactoredWorldModel(IWorldModel):
    """
    Factorized predictive model: maintains separate simple predictors for each state variable.
    Uses running averages per (state_var, action).
    """
    def __init__(self):
        self.data = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'sum': 0.0}))  # (var, action) -> stats
        self.var_names = ['confidence_level', 'free_energy', 'error_rate_1min', 'stm_utilization']
        self._states = {}  # for compatibility with original WorldModel (not used)
    def update(self, state: CognitiveState, action: str, next_state: CognitiveState, outcome: Dict):
        state_dict = state.snapshot_serializable()
        next_dict = next_state.snapshot_serializable()
        for var in self.var_names:
            if var in state_dict and var in next_dict:
                old_val = state_dict[var]
                new_val = next_dict[var]
                delta = new_val - old_val
                key = (var, action)
                self.data[var][action]['count'] += 1
                self.data[var][action]['sum'] += delta
    def predict(self, state: CognitiveState, action: str) -> Dict[str, Any]:
        state_dict = state.snapshot_serializable()
        pred = {}
        for var in self.var_names:
            if var in state_dict:
                base = state_dict[var]
                stats = self.data[var].get(action, {'count': 0, 'sum': 0.0})
                if stats['count'] > 0:
                    avg_delta = stats['sum'] / stats['count']
                    pred[var] = base + avg_delta
                else:
                    pred[var] = base  # no change predicted
        # Add other fields unchanged
        for k, v in state_dict.items():
            if k not in pred:
                pred[k] = v
        return pred
    # Compatibility method for wrapped_transition
    def observe_transition(self, from_state, action, to_state, outcome):
        self.update(from_state, action, to_state, outcome)


class EpisodicMemory(IEpisodicMemory):
    def __init__(self, max_size=10000):
        self.memory = deque(maxlen=max_size)
    def store(self, episode):
        self.memory.append(episode)
    def sample(self, n):
        return random.sample(self.memory, min(n, len(self.memory)))
    def retrieve_similar(self, query_state, k):
        # Simple: return last k episodes
        return list(self.memory)[-k:]


class GoalManager(IGoalManager):
    def __init__(self):
        self.goals = []
        self.next_id = 0
    def add_goal(self, goal: str, priority: float = 1.0, deadline: float = None):
        g = {
            'id': self.next_id,
            'goal': goal,
            'priority': priority,
            'deadline': deadline,
            'active': True,
            'progress': 0.0
        }
        self.next_id += 1
        self.goals.append(g)
        return g['id']
    def get_active_goals(self):
        now = time.time()
        return [g for g in self.goals if g['active'] and (g['deadline'] is None or g['deadline'] > now)]
    def update_progress(self, goal_id, progress):
        for g in self.goals:
            if g['id'] == goal_id:
                g['progress'] = progress
                if progress >= 1.0:
                    g['active'] = False
                break


class IntentionSystem(IIntentionSystem):
    def __init__(self):
        self.current_intention = None
    def set_intention(self, goal):
        self.current_intention = goal
    def get_current_intention(self):
        return self.current_intention


class AttentionSystem(IAttentionSystem):
    def __init__(self):
        # Simple salience based on free energy and uncertainty
        pass
    def select_relevant(self, state: CognitiveState) -> Dict:
        # Return a filtered state dict with only high-salience variables
        state_dict = state.snapshot_serializable()
        relevant = {}
        # Example: always include confidence and free_energy
        relevant['confidence_level'] = state_dict.get('confidence_level', 0.5)
        relevant['free_energy'] = state_dict.get('free_energy', 0.0)
        if state_dict.get('error_rate_1min', 0) > 0.1:
            relevant['error_rate_1min'] = state_dict['error_rate_1min']
        if state_dict.get('stm_utilization', 0) > 0.7:
            relevant['stm_utilization'] = state_dict['stm_utilization']
        return relevant


class UncertaintyEstimator(IUncertaintyEstimator):
    def __init__(self, world_model: IWorldModel):
        self.world_model = world_model
    def estimate(self, state: CognitiveState, action: str) -> float:
        # Simple uncertainty based on variance of predictions across variables
        pred = self.world_model.predict(state, action)
        # Compute variance of predicted changes (if we had multiple samples, we'd use variance)
        # For simplicity, return a heuristic based on number of observations
        total_obs = 0
        for var in ['confidence_level', 'free_energy']:
            stats = self.world_model.data[var].get(action, {'count': 0})
            total_obs += stats['count']
        if total_obs < 5:
            return 1.0
        else:
            return 1.0 / (total_obs**0.5)


class CuriosityModule(ICuriosityModule):
    def __init__(self, uncertainty_estimator: IUncertaintyEstimator):
        self.uncertainty_estimator = uncertainty_estimator
    def compute_intrinsic_reward(self, state: CognitiveState, action: str, next_state: CognitiveState) -> float:
        # Intrinsic reward = prediction error + uncertainty reduction
        uncertainty_before = self.uncertainty_estimator.estimate(state, action)
        uncertainty_after = self.uncertainty_estimator.estimate(next_state, action)
        prediction_error = abs(state.free_energy - next_state.free_energy)  # simplistic
        return prediction_error + max(0, uncertainty_before - uncertainty_after)


class MetaCognitionModule(IMetaCognitionModule):
    def __init__(self):
        self.prediction_accuracy = deque(maxlen=100)
        self.planning_success = deque(maxlen=100)
        self.decision_stability = deque(maxlen=100)
    def update(self, decision: Dict, outcome: Dict):
        # decision: from state_manager.decide_cognitive_strategy
        # outcome: result dict from process_input
        success = outcome.get('ok', False)
        self.planning_success.append(1 if success else 0)
        if 'expected_free_energy' in decision and 'free_energy' in outcome.get('metrics_used', {}):
            pred_fe = decision['expected_free_energy']
            actual_fe = outcome['metrics_used']['free_energy']
            error = abs(pred_fe - actual_fe)
            self.prediction_accuracy.append(max(0, 1 - error/10))  # normalize
        if len(self.decision_stability) > 0:
            # track if same strategy repeated
            pass
    def get_self_assessment(self) -> Dict:
        return {
            'avg_prediction_accuracy': sum(self.prediction_accuracy)/len(self.prediction_accuracy) if self.prediction_accuracy else 0.5,
            'planning_success_rate': sum(self.planning_success)/len(self.planning_success) if self.planning_success else 0.5,
        }


class StrategySelector(IStrategySelector):
    def __init__(self, strategies: List[str] = None):
        self.strategies = strategies or ['reactive', 'planning', 'exploration']
    def select_strategy(self, context: Dict) -> str:
        # Simple rule: if free energy > threshold, explore; else if uncertainty high, plan; else reactive
        fe = context.get('free_energy', 0.0)
        unc = context.get('uncertainty', 0.0)
        if fe > 5.0:
            return 'exploration'
        elif unc > 0.7:
            return 'planning'
        else:
            return 'reactive'


class TheoryOfMind(ITheoryOfMind):
    def __init__(self):
        self.agent_models = {}  # agent_id -> simple predictor
    def predict_other(self, agent_id: str, state: CognitiveState) -> Dict:
        # Dummy: assume other agent maintains same mode
        return {'mode': state.mode, 'action': 'default'}


# ============================================
# CORE SYSTEM v13.2 - With Extended Modules
# ============================================

class Neuron657CoreV13:
    """
    Main Neuron657 Core v13.2 - Formal Architecture with Integrated Learning
    and Free Energy Minimization, plus extended modular components.
    All dependencies injected via constructor.
    """
    def __init__(
        self,
        filepath: str = "neuron657_memory.bin",
        total_size: int = 4 * 1024 * 1024,
        metrics_manager: Optional[MetricsManager] = None,
        meta_learner: Optional[MetaLearner] = None,
        explainer: Optional[ExplainableDecision] = None,
        search_cache: Optional[DistributedSearchCache] = None,
        compressor: Optional[AdaptiveCompressor] = None,
        snapshot_system: Optional[IncrementalSnapshot] = None,
        recovery_system: Optional[GranularRecovery] = None,
        pattern_pool: Optional[PatternPool] = None,
        workers: Optional[SpecializedWorkers] = None,
        dashboard: Optional[RealTimeDashboard] = None,
        failure_predictor: Optional[FailurePredictor] = None,
        initial_state: Optional[CognitiveState] = None,
        exploration_rate: float = 0.1,
        # New extended modules (all optional)
        world_model_ext: Optional[IWorldModel] = None,
        episodic_memory: Optional[IEpisodicMemory] = None,
        goal_manager: Optional[IGoalManager] = None,
        intention_system: Optional[IIntentionSystem] = None,
        attention_system: Optional[IAttentionSystem] = None,
        uncertainty_estimator: Optional[IUncertaintyEstimator] = None,
        curiosity_module: Optional[ICuriosityModule] = None,
        metacognition_module: Optional[IMetaCognitionModule] = None,
        strategy_selector: Optional[IStrategySelector] = None,
        theory_of_mind: Optional[ITheoryOfMind] = None
    ):
        self.filepath = filepath
        self.total_size = total_size
        self.version = "13.2"
        self.start_time = time.time()
        self._learner_state_file = "meta_learner_state_v13.json"
        self._init_logging()
        self.metrics = metrics_manager or MetricsManager()
        self.meta_learner = meta_learner or MetaLearner()
        self.explainer = explainer or ExplainableDecision()
        self.search_cache = search_cache or DistributedSearchCache()
        self.compressor = compressor or AdaptiveCompressor()
        self.snapshot_system = snapshot_system or IncrementalSnapshot()
        self.recovery_system = recovery_system or GranularRecovery()
        self.pattern_pool = pattern_pool or PatternPool()
        self.workers = workers or SpecializedWorkers()
        self.dashboard = dashboard or RealTimeDashboard()
        self.failure_predictor = failure_predictor or FailurePredictor()
        self.embedding_precomputer = EmbeddingPrecomputer(self.search_cache)

        # New modules (core modules remain)
        self.self_model = SelfModel()
        self.world_model = WorldModel()  # original world model (kept for planning)
        self.energy_manager = EnergyManager()
        self.identity_memory = IdentityMemory()

        # Extended modules (store separately, do NOT replace core world_model)
        self.world_model_ext = world_model_ext
        self.episodic_memory = episodic_memory
        self.goal_manager = goal_manager
        self.intention_system = intention_system
        self.attention_system = attention_system
        self.uncertainty_estimator = uncertainty_estimator
        self.curiosity_module = curiosity_module
        self.metacognition_module = metacognition_module
        self.strategy_selector = strategy_selector
        self.theory_of_mind = theory_of_mind

        self.planner = CognitivePlanner(
            world_model=self.world_model,  # always use original world model for planning
            self_model=self.self_model,
            energy_manager=self.energy_manager,
            identity_memory=self.identity_memory,
            max_depth=3,
            use_mcts=True,
            mcts_simulations=100,
            mcts_exploration=1.4
        )

        self.state_manager = CognitiveStateManager(
            metrics_collector=self.metrics,
            meta_learner=self.meta_learner,
            explainer=self.explainer,
            initial_state=initial_state,
            snapshot_system=self.snapshot_system,
            exploration_rate=exploration_rate
        )

        self.extended_nip = ExtendedInstructionSet(self)

        loaded = self.meta_learner.load_learning_state(self._learner_state_file)
        if loaded:
            logger.info("Resumed from persisted MetaLearner state — learning history restored.")

        self._integrate_new_modules()
        logger.info(f"Neuron657CoreV13.2 initialized with extended modules")
        self._start_background_services()

    def _init_logging(self):
        pass

    def _integrate_new_modules(self):
        """
        Establish bidirectional links between new and existing modules.
        """
        # Record transitions in WorldModel (original) whenever state changes
        original_transition = self.state_manager.transition
        def wrapped_transition(reason="", **state_changes):
            from_state = self.state_manager.current()
            transition = original_transition(reason=reason, **state_changes)
            to_state = self.state_manager.current()
            action = state_changes.get('current_strategy', from_state.current_strategy)
            outcome = {
                'confidence': to_state.confidence_level,
                'success': to_state.error_rate_1min < from_state.error_rate_1min,
                'duration': to_state.avg_decision_time_ms,
                'free_energy': to_state.free_energy
            }
            # Update original world model
            self.world_model.observe_transition(from_state, action, to_state, outcome)
            # If extended world model exists, also update it
            if self.world_model_ext is not None:
                self.world_model_ext.update(from_state, action, to_state, outcome)
            # Store episode if episodic memory exists
            if self.episodic_memory is not None:
                episode = {
                    'from_state': from_state.snapshot_serializable(),
                    'action': action,
                    'to_state': to_state.snapshot_serializable(),
                    'outcome': outcome,
                    'timestamp': time.time()
                }
                self.episodic_memory.store(episode)
            # Update goal progress if applicable
            if self.goal_manager is not None and from_state.active_goal:
                # simplistic progress = improvement in free energy
                progress = max(0, from_state.free_energy - to_state.free_energy) / 10.0
                self.goal_manager.update_progress(from_state.active_goal, progress)
            return transition
        self.state_manager.transition = wrapped_transition

        # Also record reasoning episodes in SelfModel and meta-cognition
        original_decide = self.state_manager.decide_cognitive_strategy
        def wrapped_decide(operation_context):
            start = time.time()
            decision = original_decide(operation_context)
            latency = time.time() - start
            cost = self.energy_manager.estimate_strategy_cost(
                decision['strategy'], operation_context
            )
            success = decision.get('confidence', 0) > 0.6
            free_energy_reduction = 0.0  # will be updated later
            prediction_error = self.world_model.get_average_prediction_error()
            self.self_model.record_reasoning(
                strategy=decision['strategy'],
                context=operation_context,
                latency=latency,
                success=success,
                cost=cost,
                details={'decision': decision},
                free_energy_reduction=free_energy_reduction,
                prediction_error=prediction_error
            )
            self.energy_manager.spend(cost)
            return decision
        self.state_manager.decide_cognitive_strategy = wrapped_decide

    def _start_background_services(self):
        self.metrics_collector = threading.Thread(
            target=self._collect_metrics_loop,
            daemon=True,
            name="MetricsCollector"
        )
        self.metrics_collector.start()
        self.system_monitor = threading.Thread(
            target=self._monitor_system_loop,
            daemon=True,
            name="SystemMonitor"
        )
        self.system_monitor.start()
        logger.info("Background services started")

    def _collect_metrics_loop(self):
        while True:
            try:
                metrics = self._collect_all_metrics()
                self.dashboard.update_metrics(metrics)
                # Update free energy in metrics using correct cost (average from self_model)
                pred_error = self.world_model.get_average_prediction_error()
                avg_confidence = self.state_manager.current().confidence_level
                uncertainty = 1.0 - avg_confidence
                avg_cost = self.self_model.get_average_cost() / self.energy_manager._max_budget
                inconsistency = self.identity_memory.get_inconsistency(self.energy_manager.current_free_energy)
                free_energy = self.energy_manager.compute_free_energy(pred_error, uncertainty, avg_cost, inconsistency)
                self.energy_manager.current_free_energy = free_energy

                self.metrics.update(
                    avg_confidence=metrics.get('cognitive_state', {}).get('confidence_level', 0.5),
                    error_rate_1min=metrics.get('cognitive_state', {}).get('error_rate_1min', 0.0),
                    stm_utilization=metrics.get('cognitive_state', {}).get('stm_utilization', 0.0),
                    cache_hit_rate=metrics.get('cognitive_state', {}).get('cache_hit_rate', 0.0),
                    ltm_pattern_count=metrics.get('cognitive_state', {}).get('ltm_pattern_count', 0),
                    uptime_seconds=time.time() - self.start_time,
                    free_energy=free_energy,
                    prediction_error=pred_error,
                    model_uncertainty=uncertainty
                )
                current_state = self.state_manager.current()
                context = {
                    "memory_pressure": self.metrics.current().stm_utilization,
                    "pattern_count": self.metrics.current().ltm_pattern_count,
                    "cache_hit_rate": self.metrics.current().cache_hit_rate,
                    "avg_confidence": self.metrics.current().avg_confidence,
                    "mode": current_state.mode.value,
                    "strategy": current_state.current_strategy,
                    "free_energy": free_energy
                }
                performance = {
                    "confidence": self.metrics.current().avg_confidence,
                    "duration": 1.0,
                    "decision_class": "CONFIDENT" if self.metrics.current().avg_confidence > 0.7 else "WEAK_MATCH",
                    "success": self.metrics.current().error_rate_1min < 0.1,
                    "free_energy_reduction": 0.0
                }
                self.meta_learner.record_performance(
                    current_state.current_strategy,
                    context,
                    performance
                )
                better_strategy = self.state_manager._reevaluate_strategy(context)
                if better_strategy and better_strategy != current_state.current_strategy:
                    logger.info(f"Background learning triggered strategy change to {better_strategy}")
                    self.state_manager.transition(
                        reason="background_learning_adaptation",
                        current_strategy=better_strategy,
                        confidence_level=self.meta_learner.get_strategy_confidence(better_strategy, context)
                    )
                time.sleep(5)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(10)

    def _collect_all_metrics(self) -> Dict[str, Any]:
        raw_data = {
            "timestamp": time.time(),
            "system": {
                "version": self.version,
                "uptime": time.time() - self.start_time,
                "status": "running"
            },
            "cognitive_state": self.state_manager.current().snapshot_serializable(),
            "cache_stats": self.search_cache.stats(),
            "compression_stats": self.compressor.stats(),
            "meta_learning_stats": self.meta_learner.stats(),
            "pattern_pool_stats": self.pattern_pool.stats(),
            "recovery_stats": self.recovery_system.stats(),
            "worker_stats": self.workers.stats(),
            "snapshot_stats": self.snapshot_system.stats(),
            "failure_prediction_stats": self.failure_predictor.stats(),
            "extended_instructions_stats": self.extended_nip.stats(),
            "dashboard_stats": self.dashboard.stats(),
            "learning_weight": getattr(self.meta_learner, 'learning_weight', 0.7),
            "self_model": self.self_model.stats(),
            "world_model": self.world_model.stats(),
            "energy_manager": self.energy_manager.stats(),
            "identity_memory": self.identity_memory.stats(),
            # Extended modules stats (if present)
            "episodic_memory_size": len(self.episodic_memory.memory) if self.episodic_memory else 0,
            "goal_manager": self.goal_manager.get_active_goals() if self.goal_manager else [],
            "metacognition": self.metacognition_module.get_self_assessment() if self.metacognition_module else {}
        }
        return raw_data

    def _monitor_system_loop(self):
        while True:
            try:
                health_status = self._check_system_health()
                if health_status.get("needs_maintenance", False):
                    self._perform_maintenance()
                failure_risk = self.failure_predictor.predict_failure()
                if failure_risk > 0.7:
                    logger.warning(f"High failure risk detected: {failure_risk:.1%}")
                    if failure_risk > 0.9:
                        self.state_manager.transition(
                            reason="high_failure_risk",
                            mode=CognitiveMode.SAFE_RECOVERY,
                            status=SystemStatus.RECOVERY
                        )
                if self.energy_manager.current_free_energy > 5.0:
                    logger.info(f"High free energy ({self.energy_manager.current_free_energy:.2f}), triggering meta-learning")
                    self.state_manager.transition(
                        reason="high_free_energy",
                        mode=CognitiveMode.META_LEARNING
                    )
                time.sleep(60)
            except Exception as e:
                logger.error(f"System monitor error: {e}")
                time.sleep(120)

    def _check_system_health(self) -> Dict[str, Any]:
        health = {
            "timestamp": time.time(),
            "overall": "healthy",
            "components": {},
            "needs_maintenance": False,
            "issues": []
        }
        metrics = self.metrics.current()
        if metrics.cache_hit_rate < 0.3:
            health["components"]["cache"] = "degraded"
            health["issues"].append(f"Low cache hit rate: {metrics.cache_hit_rate:.1%}")
            health["needs_maintenance"] = True
        else:
            health["components"]["cache"] = "healthy"
        if metrics.stm_utilization > 0.8:
            health["components"]["stm"] = "high_pressure"
            health["issues"].append(f"High STM memory pressure: {metrics.stm_utilization:.1%}")
            health["needs_maintenance"] = True
        else:
            health["components"]["stm"] = "healthy"
        if metrics.avg_confidence < 0.3:
            health["components"]["confidence"] = "low"
            health["issues"].append(f"Low confidence: {metrics.avg_confidence:.1%}")
        if metrics.error_rate_1min > 0.1:
            health["components"]["error_rate"] = "high"
            health["issues"].append(f"High error rate: {metrics.error_rate_1min:.1%}")
        worker_stats = self.workers.stats()
        avg_queue = sum(
            s.get("queue_length", 0)
            for s in worker_stats.get("by_worker_type", {}).values()
        ) / max(1, len(worker_stats.get("by_worker_type", {})))
        if avg_queue > 10:
            health["components"]["workers"] = "high_load"
            health["issues"].append(f"High worker queue length: {avg_queue:.1f}")
            health["needs_maintenance"] = True
        else:
            health["components"]["workers"] = "healthy"
        learning_weight = getattr(self.meta_learner, 'learning_weight', 0.7)
        if learning_weight < 0.4:
            health["components"]["learning"] = "ineffective"
            health["issues"].append(f"Low learning impact: weight={learning_weight:.2f}")
        if metrics.free_energy > 5.0:
            health["components"]["free_energy"] = "high"
            health["issues"].append(f"High free energy: {metrics.free_energy:.2f}")
            health["needs_maintenance"] = True
        degraded_components = [status for status in health["components"].values()
                             if status in ["degraded", "high_pressure", "high_load", "ineffective", "high"]]
        if degraded_components:
            health["overall"] = "degraded"
        elif health["issues"]:
            health["overall"] = "warning"
        return health

    def _perform_maintenance(self):
        logger.info("Performing system maintenance...")
        start_time = time.time()
        maintenance_tasks = []
        if hasattr(self, 'search_cache'):
            if self.metrics.current().cache_hit_rate < 0.3:
                self.search_cache.clear()
                maintenance_tasks.append("cache_rebuild")
        duration = time.time() - start_time
        logger.info(f"Maintenance completed: {maintenance_tasks} in {duration:.2f}s")

    def process_input(self, input_data: Any, context: Dict = None) -> Dict[str, Any]:
        if not isinstance(input_data, dict):
            raise TypeError(
                f"input_data must be a dict, got {type(input_data).__name__}"
            )
        start_time = time.time()
        try:
            context = context or {}

            # 1. Use IdentityMemory to retrieve long-term goals
            goals = self.identity_memory.get_active_goals()
            if goals:
                context['active_goals'] = [g['goal'] for g in goals]

            # 2. Use goal manager to get active goals
            if self.goal_manager:
                active_goals = self.goal_manager.get_active_goals()
                if active_goals:
                    # For simplicity, use highest priority goal
                    top_goal = max(active_goals, key=lambda g: g['priority'])
                    context['active_goal'] = top_goal['goal']

            # 3. Use intention system to maintain current intention
            if self.intention_system:
                intention = self.intention_system.get_current_intention()
                if intention:
                    context['intention'] = intention

            # 4. Use attention system to filter context
            if self.attention_system:
                state = self.state_manager.current()
                filtered_state = self.attention_system.select_relevant(state)
                context['attention'] = filtered_state

            # 5. Use strategy selector to decide high-level mode (if not already set)
            if self.strategy_selector:
                sel_context = {
                    'free_energy': self.energy_manager.current_free_energy,
                    'uncertainty': 1.0 - self.state_manager.current().confidence_level
                }
                high_level = self.strategy_selector.select_strategy(sel_context)
                context['high_level_strategy'] = high_level

            # 6. Use planner to choose strategy based on free energy
            available = list(self.meta_learner.profiles.keys())
            depth = self.energy_manager.get_reasoning_depth()
            plan = self.planner.plan_strategy(
                self.state_manager.current(),
                available,
                context,
                depth=depth
            )
            context['planner_recommendation'] = plan['strategy']
            context['expected_free_energy'] = plan.get('expected_free_energy', float('inf'))

            # 7. Proceed with normal decision (which may incorporate exploration)
            operation_context = context
            strategy_decision = self.state_manager.decide_cognitive_strategy(operation_context)

            # Add planner info to decision
            strategy_decision['planner_used'] = True
            strategy_decision['expected_free_energy'] = plan.get('expected_free_energy', 0.0)
            strategy_decision['plan_depth'] = depth

            # 8. Update state
            current_free_energy = self.energy_manager.current_free_energy
            self.state_manager.transition(
                reason="process_input",
                active_goal="process_input",
                confidence_level=strategy_decision["confidence"],
                current_strategy=strategy_decision["strategy"],
                free_energy=current_free_energy
            )

            duration = time.time() - start_time
            self.metrics.update(avg_decision_time_ms=duration * 1000)

            # Record decision in IdentityMemory if significant
            if strategy_decision.get('learning_used', False) or strategy_decision['strategy'] != self.state_manager.current().current_strategy:
                self.identity_memory.record_decision({
                    'input_type': input_data.get('type') if isinstance(input_data, dict) else 'unknown',
                    'strategy': strategy_decision['strategy'],
                    'confidence': strategy_decision['confidence'],
                    'learning_used': strategy_decision.get('learning_used', False),
                    'duration': duration,
                    'free_energy': current_free_energy,
                    'plan_depth': depth
                })

            # 9. Update meta-cognition module
            if self.metacognition_module:
                outcome = {
                    'ok': True,
                    'free_energy': current_free_energy,
                    'confidence': strategy_decision['confidence']
                }
                self.metacognition_module.update(strategy_decision, outcome)

            result = {
                "ok": True,
                "input_processed": True,
                "strategy": strategy_decision["strategy"],
                "explanation": strategy_decision["reason"],
                "confidence": strategy_decision["confidence"],
                "state_id": self.state_manager.current().state_id,
                "duration": duration,
                "learning_used": strategy_decision.get("learning_used", False),
                "learning_confidence": strategy_decision.get("learning_confidence", 0.0),
                "metrics_used": {
                    "confidence": strategy_decision["confidence"],
                    "mode": self.state_manager.current().mode.value,
                    "learning_weight": strategy_decision.get("learning_weight", 0.0),
                    "free_energy": current_free_energy
                },
                "energy_remaining": self.energy_manager.get_available_energy(),
                "planner": {
                    "strategy": plan['strategy'],
                    "expected_free_energy": plan.get('expected_free_energy', 0.0),
                    "depth": depth
                }
            }
            return result
        except Exception as e:
            logger.error(f"Input processing failed: {e}")
            self.failure_predictor.record_error(e, {"operation": "process_input"})
            return {
                "ok": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def get_system_status(self) -> Dict[str, Any]:
        health = self._check_system_health()
        metrics = self._collect_all_metrics()
        learning_insights = {}
        if hasattr(self.meta_learner, 'get_learning_insights'):
            learning_insights = self.meta_learner.get_learning_insights()
        status = {
            "system": {
                "version": self.version,
                "uptime": time.time() - self.start_time,
                "status": "running",
                "health": health["overall"]
            },
            "cognitive_state": self.state_manager.current().snapshot_serializable(),
            "metrics": metrics,
            "health": health,
            "learning": {
                "weight": getattr(self.meta_learner, 'learning_weight', 0.7),
                "insights": learning_insights,
                "profiles": self.meta_learner.get_profile_stats()
            },
            "self_model": self.self_model.stats(),
            "world_model": self.world_model.stats(),
            "energy_manager": self.energy_manager.stats(),
            "identity_memory": self.identity_memory.stats(),
            "planner": {"available": True},
            "components": {
                "enhancements": [
                    "CognitiveStateManager",
                    "MetricsManager",
                    "DistributedSearchCache",
                    "EmbeddingPrecomputer",
                    "AdaptiveCompressor",
                    "ExplainableDecision",
                    "MetaLearner",
                    "IncrementalSnapshot",
                    "PatternPool",
                    "GranularRecovery",
                    "RealTimeDashboard",
                    "ExtendedInstructionSet",
                    "SpecializedWorkers",
                    "FailurePredictor",
                    "SelfModel",
                    "WorldModel",
                    "CognitivePlanner",
                    "EnergyManager",
                    "IdentityMemory",
                    "FactoredWorldModel",
                    "EpisodicMemory",
                    "GoalManager",
                    "IntentionSystem",
                    "AttentionSystem",
                    "UncertaintyEstimator",
                    "CuriosityModule",
                    "MetaCognitionModule",
                    "StrategySelector",
                    "TheoryOfMind"
                ]
            },
            "dashboard": {
                "url": f"ws://{self.dashboard.host}:{self.dashboard.port}",
                "active_connections": len(self.dashboard.active_connections)
            }
        }
        return status

    def shutdown(self):
        logger.info("Shutting down Neuron657CoreV13.2...")
        if hasattr(self, 'meta_learner'):
            saved = self.meta_learner.save_learning_state(self._learner_state_file)
            if saved:
                logger.info(f"MetaLearner state persisted to '{self._learner_state_file}'")
            else:
                logger.warning("Could not persist MetaLearner state")
        if hasattr(self, 'identity_memory'):
            self.identity_memory._save()
        if hasattr(self, 'dashboard') and self.dashboard is not None:
            try:
                ws_server = getattr(self.dashboard, 'server', None)
                if ws_server is not None:
                    ws_server.close()
                    logger.info("WebSocket dashboard server closed")
                active = getattr(self.dashboard, 'active_connections', set())
                for ws in list(active):
                    try:
                        loop = asyncio.new_event_loop()
                        loop.run_until_complete(ws.close())
                        loop.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Could not cleanly close WebSocket server: {e}")
        if hasattr(self, 'workers'):
            self.workers.shutdown()
        if hasattr(self, 'snapshot_system'):
            self._create_shutdown_snapshot()
        if hasattr(self, 'recovery_system'):
            self._backup_critical_components()
        logger.info("Neuron657CoreV13.2 shutdown complete")

    def _create_shutdown_snapshot(self):
        try:
            system_state = self.get_system_status()
            snapshot_id = self.snapshot_system.create_full_snapshot(
                system_state,
                "Shutdown snapshot"
            )
            logger.info(f"Created shutdown snapshot: {snapshot_id}")
        except Exception as e:
            logger.error(f"Failed to create shutdown snapshot: {e}")

    def _backup_critical_components(self):
        try:
            config = {
                "version": self.version,
                "filepath": self.filepath,
                "total_size": self.total_size,
                "timestamp": time.time(),
                "cognitive_state": self.state_manager.current().snapshot_serializable(),
                "learning_weight": getattr(self.meta_learner, 'learning_weight', 0.7),
                "meta_learner_state_file": self._learner_state_file,
                "free_energy_target": self.identity_memory._free_energy_target,
                "exploration_rate": self.state_manager.exploration_rate
            }
            backup_id = self.recovery_system.backup_component(
                "config",
                config,
                "Pre-shutdown configuration backup"
            )
            if backup_id:
                logger.info(f"Critical components backed up: {backup_id}")
            else:
                logger.warning("Failed to backup critical components")
        except Exception as e:
            logger.error(f"Failed to backup critical components: {e}")


# ============================================
# PUBLIC API
# ============================================

__all__ = [
    "CognitiveState",
    "MetaLearner",
    "ExplainableDecision",
    "Neuron657CoreV13",
    "SelfModel",
    "WorldModel",
    "CognitivePlanner",
    "EnergyManager",
    "IdentityMemory",
    "set_random_seed",
    "FactoredWorldModel",
    "EpisodicMemory",
    "GoalManager",
    "IntentionSystem",
    "AttentionSystem",
    "UncertaintyEstimator",
    "CuriosityModule",
    "MetaCognitionModule",
    "StrategySelector",
    "TheoryOfMind"
]

NeuronEngine = Neuron657CoreV13

# ============================================
# TEST FUNCTION (UPDATED)
# ============================================

def test_system_v13():
    logging.basicConfig(level=logging.INFO)
    # Create extended modules
    fwm = FactoredWorldModel()
    em = EpisodicMemory()
    gm = GoalManager()
    its = IntentionSystem()
    att = AttentionSystem()
    ue = UncertaintyEstimator(fwm)
    cm = CuriosityModule(ue)
    mc = MetaCognitionModule()
    ss = StrategySelector()
    tom = TheoryOfMind()

    # Create system with extended modules
    system = Neuron657CoreV13(
        exploration_rate=0.2,
        world_model_ext=fwm,
        episodic_memory=em,
        goal_manager=gm,
        intention_system=its,
        attention_system=att,
        uncertainty_estimator=ue,
        curiosity_module=cm,
        metacognition_module=mc,
        strategy_selector=ss,
        theory_of_mind=tom
    )
    # Set a goal
    system.identity_memory.add_goal("maintain free energy below 5", priority=0.9)
    system.goal_manager.add_goal("improve prediction accuracy", priority=0.8)

    # Process some inputs with diverse contexts
    contexts = [
        {"pattern_size": 50, "pattern_tags": [], "memory_pressure": 0.2},
        {"pattern_size": 10, "pattern_tags": [], "memory_pressure": 0.1},
        {"pattern_size": 2000, "pattern_tags": ["image", "large"], "memory_pressure": 0.8},
        {"pattern_size": 500, "pattern_tags": ["text"], "memory_pressure": 0.5},
        {"pattern_size": 100, "pattern_tags": ["important"], "memory_pressure": 0.3},
    ]
    for i in range(10):
        ctx = contexts[i % len(contexts)]
        result = system.process_input({"type": "test", "data": f"input_{i}"}, ctx)
        print(f"Cycle {i:2d}: {result['strategy']} (conf={result['confidence']:.2f}, FE={result['metrics_used']['free_energy']:.2f}, depth={result['planner']['depth']})")
    status = system.get_system_status()
    print("SelfModel stats:", status['self_model'])
    print("Energy stats:", status['energy_manager'])
    print("MetaCognition:", status['metrics'].get('metacognition', {}))
    system.shutdown()

if __name__ == "__main__":
    test_system_v13()