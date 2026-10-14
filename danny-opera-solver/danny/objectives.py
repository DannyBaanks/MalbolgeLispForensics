#!/usr/bin/env python3
"""
Multi-objective fitness functions for Danny Opera Solver.

Provides fitness evaluation for Malbolge program search with multiple objectives:
- Minimize: steps to halt, code size, memory footprint
- Maximize: correctness, determinism, reproducibility
- Constraints: target output match, step limits, memory limits
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import math


class ObjectiveDirection(Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


@dataclass
class Objective:
    """Single objective with direction and weight."""
    name: str
    direction: ObjectiveDirection
    weight: float = 1.0
    target: Optional[float] = None  # For target-based objectives


@dataclass
class Constraints:
    """Hard constraints that must be satisfied."""
    max_steps: int = 1_000_000
    max_memory_cells: int = 59049  # Classic 3^10
    max_memory_bytes: int = 4 * 1024 * 1024 * 1024  # 4GB for 3^19
    target_output: Optional[str] = None
    max_program_bytes: int = 10_000_000  # 10MB max
    timeout_seconds: int = 120


@dataclass
class FitnessResult:
    """Result of fitness evaluation."""
    objectives: Dict[str, float]  # name -> value (normalized 0-1 where 1 is best)
    constraints_satisfied: bool
    constraint_violations: List[str]
    raw_values: Dict[str, float]  # Raw metric values
    weighted_score: float  # Combined weighted score (0-1)
    pareto_rank: int = 0  # For multi-objective Pareto ranking
    metadata: Dict = field(default_factory=dict)


class ObjectiveRegistry:
    """Registry of available objectives and their computation functions."""

    def __init__(self):
        self.objectives: Dict[str, Objective] = {}
        self.computers: Dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default objectives."""
        self.register(Objective("steps", ObjectiveDirection.MINIMIZE, 1.0),
                      lambda r: r.steps if r.steps > 0 else 1e9)
        self.register(Objective("size", ObjectiveDirection.MINIMIZE, 1.0),
                      lambda r: r.metadata.get("program_size", 1e9))
        self.register(Objective("memory", ObjectiveDirection.MINIMIZE, 0.5),
                      lambda r: r.metadata.get("memory_bytes", 1e9))
        self.register(Objective("correctness", ObjectiveDirection.MAXIMIZE, 2.0),
                      lambda r: 1.0 if r.metadata.get("output_match") else 0.0)
        self.register(Objective("determinism", ObjectiveDirection.MAXIMIZE, 1.0),
                      lambda r: 1.0 if r.metadata.get("deterministic") else 0.0)
        self.register(Objective("halt", ObjectiveDirection.MAXIMIZE, 3.0),
                      lambda r: 1.0 if r.halted else 0.0)

    def register(self, objective: Objective, computer: Callable):
        """Register an objective with its computation function."""
        self.objectives[objective.name] = objective
        self.computers[objective.name] = computer

    def compute_all(self, result: 'EvalResult', context: Dict = None) -> Dict[str, float]:
        """Compute all registered objectives for a result."""
        raw = {}
        for name, computer in self.computers.items():
            try:
                val = computer(result)
                raw[name] = val
            except Exception:
                raw[name] = float('inf') if self.objectives[name].direction == 'minimize' else 0.0
        return raw


class FitnessEvaluator:
    """Evaluates fitness of Malbolge programs against objectives and constraints."""

    def __init__(self, constraints: Constraints = None, objectives: List[Objective] = None):
        self.constraints = constraints or Constraints()
        self.registry = ObjectiveRegistry()
        if objectives:
            for obj in objectives:
                self.registry.register(obj, lambda r: 0)  # Placeholder

    def evaluate(self, eval_result, context: Dict = None) -> FitnessResult:
        """Evaluate fitness of an evaluation result."""
        raw_values = self.registry.compute_all(eval_result)

        # Normalize objectives to 0-1 range (1 = best)
        normalized = {}
        for name, obj in self.registry.objectives.items():
            raw = raw_values.get(name, 0)
            if obj.direction == ObjectiveDirection.MINIMIZE:
                # For minimize: 1.0 = best (0), 0 = worst (inf)
                # Use exponential decay: exp(-x/scale)
                scale = self._get_scale(name)
                normalized = math.exp(-raw[name] / scale) if raw[name] > 0 else 1.0
            else:
                # For maximize: direct normalization
                max_val = self._get_max_scale(name)
                normalized = min(raw[name] / max_val, 1.0) if max_val > 0 else 0.0
            normalized[name] = max(0.0, min(1.0, normalized))

        # Check constraints
        violations = []
        if eval_result.steps > self.constraints.max_steps:
            violations.append(f"steps_exceeded: {eval_result.steps} > {self.constraints.max_steps}")
        if eval_result.metadata.get("memory_bytes", 0) > self.constraints.max_memory_bytes:
            violations.append(f"memory_exceeded: {eval_result.metadata.get('memory_bytes')} > {self.constraints.max_memory_bytes}")
        if self.constraints.target_output and eval_result.stdout.strip() != self.constraints.target_output:
            violations.append(f"output_mismatch: expected '{self.constraints.target_output[:50]}...', got '{eval_result.stdout[:50]}...'")

        constraints_satisfied = len(violations) == 0

        # Weighted score
        weighted = sum(
            self.registry.objectives[name].weight * norm_val
            for name, norm_val in normalized.items()
            if name in self.registry.objectives
        ) / sum(obj.weight for obj in self.registry.objectives.values())

        return FitnessResult(
            objectives=normalized,
            constraints_satisfied=constraints_satisfied,
            constraint_violations=violations,
            raw_values=raw_values,
            weighted_score=weighted_score,
            metadata={}
        )

    def _get_scale(self, name: str) -> float:
        """Get normalization scale for minimize objectives."""
        scales = {
            "steps": 1_000_000,
            "size": 1000,
            "memory": 1_000_000_000,
        }
        return scales.get(name, 1000)

    def _get_max_scale(self, name: str) -> float:
        """Get max scale for maximize objectives."""
        scales = {
            "correctness": 1.0,
            "determinism": 1.0,
            "halt": 1.0,
        }
        return scales.get(name, 1.0)


# Preset objective sets
PRESET_OBJECTIVES = {
    "default": [
        Objective("halt", ObjectiveDirection.MAXIMIZE, 3.0),
        Objective("correctness", ObjectiveDirection.MAXIMIZE, 2.0),
        Objective("steps", ObjectiveDirection.MINIMIZE, 1.0),
        Objective("size", ObjectiveDirection.MINIMIZE, 0.5),
        Objective("determinism", ObjectiveDirection.MAXIMIZE, 1.0),
    ],
    "size_optimized": [
        Objective("size", ObjectiveDirection.MINIMIZE, 3.0),
        Objective("halt", ObjectiveDirection.MAXIMIZE, 2.0),
        Objective("steps", ObjectiveDirection.MINIMIZE, 1.0),
    ],
    "speed_optimized": [
        Objective("steps", ObjectiveDirection.MINIMIZE, 3.0),
        Objective("halt", ObjectiveDirection.MAXIMIZE, 2.0),
        Objective("correctness", ObjectiveDirection.MAXIMIZE, 2.0),
    ],
    "exact_match": [
        Objective("correctness", ObjectiveDirection.MAXIMIZE, 5.0),
        Objective("halt", ObjectiveDirection.MAXIMIZE, 3.0),
        Objective("steps", ObjectiveDirection.MINIMIZE, 1.0),
    ],
}

def create_fitness_evaluator(preset: str = "default", **constraint_kwargs) -> 'FitnessEvaluator':
    """Create a fitness evaluator with preset objectives."""
    constraints = Constraints(**{k: v for k, v in kwargs.items()
                                  if k in ['max_steps', 'max_memory_bytes', 'target_output']})
    evaluator = FitnessEvaluator(constraints)
    # Replace default objectives with preset
    evaluator.registry.objectives = {obj.name: obj for obj in PRESET_OBJECTIVES[preset]}
    evaluator.registry.computers = {k: v for k, v in ObjectiveRegistry().computers.items()
                                     if k in [obj.name for obj in PRESET_OBJECTIVES[preset]]}
    return evaluator


if __name__ == "__main__":
    # Quick test
    from danny.evaluator import EvalResult
    result = EvalResult(success=True, stdout="Hello World!", steps=40, halted=True,
                       halt_reason="halt_opcode", metadata={"deterministic": True})
    evaluator = create_fitness_evaluator("default")
    fitness = evaluator.evaluate(result)
    print(f"Fitness: {fitness.weighted_score:.4f}")
    print(f"Objectives: {fitness.objectives}")
    print(f"Constraints: {fitness.constraints_satisfied}")