#!/usr/bin/env python3
"""
Ablative Minimization — Iterative reduction to minimal form.

Based on the GPT Genesis ablative minimization phase:
iteratively remove elements that aren't necessary for the target behavior.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable, Set, FrozenSet
from dataclasses import dataclass
import random
import time


@dataclass
class AblativeConfig:
    """Configuration for ablative minimization."""
    max_passes: int = 10
    shuffle_order: bool = True
    early_stop: bool = True
    min_improvement: float = 0.0


@dataclass
class AblationResult:
    """Result of ablative minimization."""
    original: Any
    minimized: Any
    removed: int
    passes: int
    fitness_before: float
    fitness_after: float
    history: List[Dict]


class AblativeMinimizer:
    """
    Ablative minimization for reducing solutions to minimal form.

    Iteratively tries to remove components; if fitness doesn't degrade,
    keeps the removal. Repeats until fixed point or max passes.

    Based on the GPT Genesis ablative minimization phase.
    """

    def __init__(self, fitness_fn, config=None):
        self.fitness_fn = fitness_fn
        self.config = config or type('Config', (), {
            'max_passes': 10,
            'shuffle_order': True,
            'early_stop': True,
            'min_improvement': 0.0,
        })()
        self.rng = random.Random(42)

    def minimize(self, candidate: Dict, fitness_fn: Callable) -> Dict:
        """
        Perform ablative minimization on a candidate.

        Args:
            candidate: Dictionary with 'birth', 'survival', 'live_sigs' etc.
            fitness_fn: Function that takes candidate and returns fitness (lower=better)

        Returns minimized candidate dict.
        """
        # Get current fitness
        current_fitness = self.fitness_fn(candidate)
        current = {
            'birth': list(candidate.get('birth', [])),
            'survival': list(candidate.get('survival', [])),
            'live_sigs': set(candidate.get('live_sigs', [])),
        }

        passes = 0
        changed = True
        history = []

        while passes < self.config.max_passes and changed:
            changed = False
            passes += 1

            # Get all active signatures
            active = list(current['live_sigs'])
            if self.config.shuffle_order:
                self.rng.shuffle(active)

            removed_this_pass = 0

            for sig in active:
                # Try removing this signature
                test_live = current['live_sigs'] - {sig}
                test_candidate = {
                    'live_sigs': test_live,
                    'birth': [s for s in current['birth'] if s in test_live],
                    'survival': [s for s in current['survival'] if s in test_live],
                }

                # Evaluate
                test_fitness = self.fitness_fn(test_candidate)

                # If fitness doesn't get worse (or improves), accept removal
                if test_fitness <= current_fitness + self.config.min_improvement:
                    current['live_sigs'] = test_live
                    current['birth'] = [s for s in current['birth'] if s in test_live]
                    current['survival'] = [s for s in current['survival'] if s in test_live]
                    changed = True

                    history.append({
                        'pass': passes,
                        'removed': sig,
                        'fitness_before': current_fitness,
                        'fitness_after': fitness_fn(test_candidate),
                    })

                    current_fitness = fitness_fn(test_candidate)

        return {
            'minimized': {
                'birth': sorted(current['birth']),
                'survival': sorted(current['survival']),
                'live_sigs': sorted(current['live_sigs']),
            },
            'original_fitness': self.fitness_fn(candidate) if hasattr(candidate, 'get') else self.fitness_fn(candidate),
            'final_fitness': self.fitness_fn({
                'birth': sorted(current['birth']),
                'survival': sorted(current['survival']),
                'live_sigs': current['live_sigs'],
            }),
            'removed_count': len(candidate.get('live_sigs', [])) - len(current['live_sigs']),
            'passes': passes,
            'history': history,
        }

    def iterative_deepening(self, candidate: Dict, fitness_fn: Callable,
                            max_depth: int = 10) -> List[Dict]:
        """
        Iterative deepening ablation: progressively more aggressive removal.

        Returns list of increasingly minimized candidates.
        """
        results = []
        current = candidate

        for depth in range(1, max_depth + 1):
            # Create config with increasing aggressiveness
            config = type('Config', (), {
                'max_passes': depth,
                'shuffle_order': True,
                'min_improvement': 0.0,
            })()

            minimizer = AblativeMinimizer(self.fitness_fn, config)
            result = minimizer.minimize(candidate, fitness_fn)

            results.append({
                'depth': depth,
                'minimized': result['minimized'],
                'removed': result['removed_count'],
                'fitness': result['fitness_after'],
            })

            # If no more can be removed, stop
            if result['removed_count'] == 0:
                break

        return results


def ablative_minimize(candidate: Dict, fitness_fn: Callable,
                      max_passes: int = 10,
                      shuffle: bool = True) -> Dict:
    """
    Convenience function for single ablative minimization pass.

    Args:
        candidate: Dict with 'birth', 'survival', 'live_sigs'
        fitness_fn: Function(candidate) -> fitness (lower=better)
        max_passes: Maximum number of passes
        shuffle: Whether to shuffle removal order

    Returns:
        Minimized candidate dict with history
    """
    minimizer = AblativeMinimizer(
        fitness_fn,
        type('Config', (), {'max_passes': 10, 'shuffle_order': shuffle, 'min_improvement': 0.0})()
    )
    return minimizer.minimize(candidate, fitness_fn)


def iterative_ablation(candidate: Dict, fitness_fn: Callable,
                       max_depth: int = 5) -> List[Dict]:
    """
    Iterative deepening ablation.

    Returns list of progressively more minimized candidates.
    """
    results = []
    current = candidate

    for depth in range(1, max_depth + 1):
        result = ablative_minimize(current, fitness_fn, max_passes=depth)
        results.append({
            'depth': depth,
            'minimized': result['minimized'],
            'removed': result['removed_count'],
            'fitness_before': result['fitness_before'],
            'fitness_after': result['fitness_after'],
        })
        current = result['minimized']

        if result['removed_count'] == 0:
            break

    return results


def ablate_program(program_bytes: bytes, fitness_fn: Callable,
                   max_passes: int = 10) -> bytes:
    """
    Ablative minimization for raw Malbolge program bytes.

    Iteratively tries to remove bytes from the program while
    maintaining fitness.
    """
    current = bytearray(program_bytes)
    best_fitness = fitness_fn(bytes(current))
    passes = 0
    changed = True

    while passes < 10 and changed:
        changed = False
        passes += 1

        # Try removing each byte
        indices = list(range(len(current)))
        random.shuffle(indices)

        for idx in indices:
            # Try removing this byte
            test = current[:idx] + current[idx+1:]
            test_fitness = fitness_fn(bytes(test))

            if test_fitness <= fitness_fn(bytes(current)):
                # Removal didn't hurt - keep it removed
                current = test
                changed = True
                break  # Restart from beginning

    return bytes(current)


if __name__ == "__main__":
    # Quick test
    def dummy_fitness(candidate):
        live = len(candidate.get('live_sigs', []))
        return live  # Minimize live signatures

    candidate = {
        'birth': [1, 2, 4],
        'survival': [8],
        'live_sigs': {1, 2, 4, 8},
    }

    result = ablative_minimize(candidate, dummy_fitness, max_passes=3)
    print(f"Removed: {result['removed_count']}")
    print(f"Final live_sigs: {result['minimized']['live_sigs']}")
    print(f"Passes: {result['passes']}")