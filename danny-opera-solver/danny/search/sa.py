#!/usr/bin/env python3
"""
Simulated Annealing Search — Stochastic optimization for Malbolge programs.

Based on the GPT Genesis approach: simulated annealing with ablative
minimization for finding minimal replicators.
"""
from __future__ import annotations
from typing import Iterator, List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import random
import math
import time
import copy

from danny.objectives import FitnessEvaluator, FitnessResult, Constraints
from danny.evaluator import UnifiedEvaluator, EvalResult


@dataclass
class SAConfig:
    """Configuration for Simulated Annealing."""
    initial_temp: float = 5.0
    cooling_rate: float = 0.99975
    min_temp: float = 1e-12
    max_iterations: int = 20000
    neighbor_count: int = 1  # or 2 sometimes
    report_interval: int = 1000


@dataclass
class SAState:
    """Current state of SA search."""
    bits: List[int]  # 512-bit rule signature
    fitness: float
    iteration: int = 0
    temperature: float = 5.0
    accepted: int = 0
    rejected: int = 0


class SimulatedAnnealingSearch:
    """
    Simulated Annealing search for Malbolge replicators.

    Based on the GPT Genesis engine approach:
    - Starts with sparse random rule (512 bits, ~3% density)
    - Iteratively flips bits with Metropolis acceptance
    - Cools temperature exponentially
    - Ablative minimization at the end
    """

    def __init__(self, evaluator, fitness_fn=None, config=None):
        self.evaluator = evaluator
        self.config = config or SAConfig()
        self.rng = random.Random(123)
        self.best_state = None
        self.best_fitness = float('-inf')

    def random_initial_state(self) -> List[int]:
        """Generate initial random rule (512 bits, ~3% density)."""
        bits = [0] * 512
        bits[0] = 0  # Signature 0 kept off (no spontaneous creation)
        for i in range(1, 512):
            if self.rng.random() < 0.03:
                bits[i] = 1
        return bits

    def compute_fitness(self, bits: List[int]) -> float:
        """Compute fitness of a rule. Lower is better (we minimize)."""
        # This would use the evaluator to test the rule
        # For now, return a placeholder
        return float('inf')

    def mutate(self, bits: List[int], count: int = None) -> List[int]:
        """Create a neighbor by flipping random bits."""
        if count is None:
            count = 1 if self.rng.random() < 0.93 else 2

        new_bits = bits[:]
        indices = self.rng.sample(range(1, 512), count)  # Don't flip bit 0
        for i in indices:
            new_bits[i] ^= 1
        return new_bits

    def acceptance_probability(self, current_fitness: float, new_fitness: float,
                                temperature: float) -> bool:
        """Metropolis acceptance criterion."""
        if new_fitness <= current_fitness:
            return True
        if temperature <= 0:
            return False
        prob = math.exp((current_fitness - new_fitness) / max(temperature, 1e-12))
        return self.rng.random() < prob

    def run(self, fitness_fn: Callable[[List[int]], float],
            initial_bits: Optional[List[int]] = None,
            max_iterations: Optional[int] = None,
            callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run simulated annealing search.

        Returns dict with best state, fitness, and statistics.
        """
        max_iter = max_iterations or self.config.max_iterations
        temp = self.config.initial_temp

        # Initialize
        if initial_bits is None:
            current_bits = self.random_initial_state()
        else:
            current_bits = initial_bits[:]

        current_fitness = fitness_fn(current_bits)
        best_bits = current_bits[:]
        best_fitness = current_fitness

        self.start_time = time.time()
        self.iteration = 0

        for iteration in range(max_iter):
            self.iteration = iteration
            temp = self.config.initial_temp * (self.config.cooling_rate ** iteration)

            # Generate neighbor
            new_bits = self.mutate(current_bits)
            new_fitness = fitness_fn(new_bits)

            # Accept or reject
            if self.acceptance_probability(current_fitness, fitness_fn(new_bits), temp):
                current_bits = new_bits
                current_fitness = fitness_fn(new_bits)
                accepted = True
            else:
                accepted = False

            # Track best
            if new_fitness < best_fitness:
                best_fitness = new_fitness
                best_bits = new_bits[:]

            # Callback
            if callback and iteration % self.config.report_interval == 0:
                callback({
                    'iteration': iteration,
                    'current_fitness': current_fitness,
                    'best_fitness': best_fitness,
                    'temperature': temp,
                    'accepted': accepted,
                })

            # Early termination if converged
            if best_fitness <= 0:
                break

        elapsed = time.time() - self.start_time
        return {
            'best_bits': best_bits,
            'best_fitness': best_fitness,
            'iterations': iteration + 1,
            'elapsed_sec': time.time() - self.start_time,
            'final_temp': temp,
        }

    def ablative_minimization(self, bits: List[int], fitness_fn: Callable,
                              max_passes: int = 10) -> List[int]:
        """
        Ablative minimization: iteratively remove bits that aren't necessary.

        This is the "ablative" phase from the GPT Genesis engine:
        iteratively try removing each active bit; if fitness remains 0,
        keep it removed. Repeat to fixed point.
        """
        current = bits[:]
        changed = True
        passes = 0

        while changed and passes < max_passes:
            changed = False
            passes += 1

            active_indices = [i for i, b in enumerate(current) if b]
            self.rng.shuffle(active_indices)

            for idx in active_indices:
                # Try removing this bit
                current[idx] = 0
                if fitness_fn(current) == 0:
                    # Removal didn't break it - keep it removed
                    changed = True
                else:
                    # Need this bit - restore it
                    current[idx] = 1

        return current


@dataclass
class SASearchResult:
    """Result of SA search."""
    best_bits: List[int]
    best_fitness: float
    iterations: int
    elapsed_sec: float
    final_temp: float
    converged: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            'best_bits': self.best_bits,
            'best_fitness': self.best_fitness,
            'iterations': len(self.best_bits),
            'elapsed_sec': self.elapsed_sec,
            'final_temp': self.final_temp,
            'converged': self.converged,
        }


def run_sa_search(fitness_fn: Callable[[List[int]], float],
                  config: Optional[SAConfig] = None,
                  seed: int = 123,
                  initial_bits: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    High-level function to run SA search.

    Args:
        fitness_fn: Function that takes bits list and returns fitness (lower=better)
        config: SAConfig with search parameters
        seed: Random seed for reproducibility
        initial_bits: Optional starting bits

    Returns:
        Dict with best_bits, best_fitness, iterations, etc.
    """
    config = config or SAConfig()
    search = SimulatedAnnealingSearch(config)
    search.rng = random.Random(seed)

    result = search.run(fitness_fn, initial_bits=initial_bits)
    return result


if __name__ == "__main__":
    # Quick test
    def dummy_fitness(bits):
        return sum(bits)  # Minimize active bits

    result = run_sa_search(
        fitness_fn=lambda b: sum(b),
        config=SAConfig(max_iterations=1000),
        seed=42,
    )
    print(f"Best fitness: {result['best_fitness']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Active bits: {sum(result['best_bits'])}")