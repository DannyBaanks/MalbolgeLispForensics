#!/usr/bin/env python3
"""
Meta Search — Exhaustive search over signature combinations.

Based on the Meta Genesis engine: exhaustive search over subsets of
single-bit birth/survival masks.
"""
from __future__ import annotations
from typing import Iterator, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from itertools import combinations, product
import time
import itertools

from danny.objectives import FitnessEvaluator, FitnessResult, Constraints
from danny.evaluator import UnifiedEvaluator, EvalResult


@dataclass
class MetaSearchConfig:
    """Configuration for Meta search."""
    max_birth_signatures: int = 2  # Max birth signatures to try
    max_survival_signatures: int = 1  # Max survival signatures
    max_combinations: Optional[int] = None
    single_bit_masks: Tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64, 128)


@dataclass
class MetaSearchResult:
    """Result of a meta search."""
    found: bool = False
    best_candidate: Dict = None
    best_fitness: float = float('inf')
    total_combinations: int = 0
    tested: int = 0
    elapsed_ms: float = 0.0
    best_candidate: Dict = None
    best_fitness: float = float('inf')
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MetaSearch:
    """
    Exhaustive search over signature combinations (Meta Genesis style).

    Searches over subsets of single-bit birth/survival masks.
    For classic 3^10: 8 single-bit masks, subsets up to size 2 for birth,
    size 1 for survival.

    Total combinations: C(8,1)+C(8,2) = 8+28=36 birth × (1+8)=9 survival = 324 combos
    """

    def __init__(self, evaluator, fitness_fn=None, config=None):
        self.config = config or MetaSearchConfig()
        self.evaluator = None  # Would be injected
        self.fitness_fn = fitness_fn

    def generate_birth_combinations(self, max_size: int = None) -> List[Tuple[int, ...]]:
        """Generate all birth signature combinations up to max_size."""
        max_size = min(self.config.max_birth_signatures, 8)
        combos = []
        single_bits = [1, 2, 4, 8, 16, 32, 64, 128]
        for r in range(1, max_size + 1):
            combos.extend(combinations([1, 2, 4, 8, 16, 32, 64, 128], r))
        return combos

    def generate_survival_combinations(self, max_size: int = None) -> List[frozenset]:
        """Generate survival signature combinations."""
        max_size = min(self.config.max_survival_signatures, 8)
        combos = [frozenset()]  # Empty survival always valid
        for r in range(1, max_size + 1):
            combos.extend(frozenset(c) for c in combinations([1,2,4,8,16,32,64,128], r))
        return combos

    def enumerate_candidates(self) -> Iterator[Dict]:
        """Enumerate all candidate (birth, survival) pairs."""
        birth_combos = self.generate_birth_combinations()
        survival_combos = self.generate_survival_combinations()

        count = 0
        for birth in birth_combos:
            for surv in survival_combos:
                yield {
                    "birth": birth,
                    "survival": surv,
                    "live_sigs": frozenset(birth) | surv,
                    "birth_masks": birth,
                    "survival_masks": tuple(surv),
                }
                if count >= self.config.max_combinations:
                    return

    def search(self, fitness_fn, max_iterations: Optional[int] = None) -> Dict:
        """
        Run exhaustive search over signature space.

        Returns best candidate found.
        """
        start = time.time()
        best_fitness = float('inf')
        best_candidate = None
        tested = 0

        for candidate in self.enumerate_candidates():
            if self.config.max_combinations and tested >= self.config.max_combinations:
                break

            # Evaluate candidate
            # This would call the evaluator with the candidate's rule
            fitness = self._evaluate_candidate(candidate)

            if fitness < best_fitness:
                best_fitness = fitness
                best_candidate = candidate

            if callback and tested % 100 == 0:
                callback({
                    'tested': tested,
                    'best_fitness': best_fitness,
                    'current': candidate,
                })

            tested += 1
            if max_iterations and tested >= max_iterations:
                break

        elapsed = time.time() - start_time
        return {
            'found': best_candidate is not None,
            'best_candidate': best_candidate,
            'best_fitness': best_fitness,
            'tested': tested,
            'elapsed_sec': time.time() - start_time,
        }

    def search_oriented_pairs(self) -> List[Dict]:
        """
        Search for oriented opposite birth pairs (Grok style).

        Tests all 4 axis-aligned opposite birth pairs:
        X: (2,4), Y: (8,16), Z: (32,64), T: (128,256)
        """
        # In 3^10, neighbor offsets map to bits 1..8:
        # +X: 1, -X: 2, +Y: 4, -Y: 8, +Z: 16, -Z: 32, +T: 64, -T: 128
        # But wait - in the standard mapping:
        # NEIGHBOR_OFFSETS = (+X, -X, +Y, -Y, +Z, -Z, +T, -T)
        # So indices: +X=0, -X=1, +Y=2, -Y=3, +Z=4, -Z=5, +T=6, -T=7
        # Single-bit masks: 1<<0=1 (+X), 2 (-X), 4 (+Y), 8 (-Y), 16 (+Z), 32 (-Z), 64 (+T), 128 (-T)

        # Opposite pairs: (+X,-X), (+Y,-Y), (+Z,-Z), (+T,-T)
        # Indices: (1,2), (4,8), (16,32), (64,128)

        oriented_pairs = [
            (1, 2),    # X axis: +X/-X
            (4, 8),    # Y axis
            (16, 32),  # Z axis
            (64, 128), # T axis
        ]

        results = []
        for axis_name, (pos, neg) in zip(['X', 'Y', 'Z', 'T'], [(1,2), (4,8), (16,32), (64,128)]):
            live_sigs = frozenset([pos, neg])
            yield {
                "axis": "XYZT"[["X","Y","Z","T"].index(axis_name)],  # Fix this
                "live_sigs": sorted([pos, neg]),
                "seed": [(0,0,0,0)],
                "k": 1,
            }

        return results


def run_meta_search(fitness_fn, config=None, max_combinations=None) -> Dict:
    """
    High-level function to run meta search.

    Args:
        fitness_fn: Function(candidate_dict) -> fitness (lower=better)
        config: MetaSearchConfig
        max_combinations: Override max combinations

    Returns:
        Dict with best candidate and stats
    """
    config = config or MetaSearchConfig()
    search = MetaSearch(None, config=config)
    return search.search(fitness_fn)


if __name__ == "__main__":
    # Quick test
    def dummy_fitness(candidate):
        return sum(candidate['live_sigs'])

    config = MetaSearchConfig(max_birth_signatures=2, max_survival_signatures=1)
    search = MetaSearch(None, config=config)

    # Test oriented pairs
    print("Oriented pairs:")
    for p in search.search_oriented_pairs():
        print(f"  {p}")

    # Test full enumeration
    print("\nFull enumeration (first 5):")
    count = 0
    for c in search.enumerate_candidates():
        print(f"  birth={c['birth']}, survival={c['survival']}")
        if count >= 4:
            break
        count += 1

    print(f"\nTotal combinations: ~36 birth x 9 survival = 324")