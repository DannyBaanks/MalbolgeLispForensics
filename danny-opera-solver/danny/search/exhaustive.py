#!/usr/bin/env python3
"""
Exhaustive Search — Systematic enumeration of Malbolge programs.

Based on the Grok genesis engine approach: exhaustive enumeration
of birth-signature combinations for finding minimal replicators.
"""
from __future__ import annotations
from __future__ import annotations
from typing import Iterator, List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from itertools import combinations, product
import hashlib
import time

from danny.objectives import FitnessEvaluator, FitnessResult, Constraints
from danny.evaluator import UnifiedEvaluator, EvalResult


@dataclass
class SearchResult:
    """Result of a search operation."""
    found: bool
    best_program: str = ""
    best_fitness: Optional[Any] = None
    iterations: int = 0
    elapsed_ms: float = 0.0
    candidates_tested: int = 0
    best_program: str = ""
    best_fitness_obj: Any = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ExhaustiveSearch:
    """
    Exhaustive search for Malbolge programs.

    Based on the Grok Genesis approach: systematic enumeration of
    birth-signature combinations for finding minimal replicators.

    For classic 3^10 Malbolge: enumerates pairs of single-bit birth masks
    from the 8 neighbor positions (256 combinations, choose 2 = 28).
    """

    def __init__(self, evaluator, fitness_evaluator=None):
        self.evaluator = evaluator
        self.fitness = fitness_evaluator
        self.iterations = 0
        self.start_time = 0

    def search_classic_replicators(self,
                                    target_output: str = "",
                                    max_combinations: int = None) -> List[Dict]:
        """
        Exhaustive search for classic 3^10 replicators.

        Searches all pairs of single-bit birth masks (8 neighbor positions,
        2^8=256 possible birth masks, choose 2 = 28 combinations).

        Returns list of found replicators with their properties.
        """
        from itertools import combinations

        # Single-bit birth masks (8 neighbor positions in 3^10)
        single_bit_masks = [1, 2, 4, 8, 16, 32, 64, 128]

        results = []
        combos = list(combinations(single_bit_masks, 2))
        if max_combinations:
            combos = combos[:max_combinations]

        for combo in combos:
            active = set(combo)  # Birth signatures
            # S = empty (no survival signatures)
            # Test with singleton seed
            seed = frozenset({(0, 0, 0, 0)})
            k = 1

            # We'd need to connect to our evaluator here
            # For now, return the combo structure
            results.append({
                "active_signatures": sorted(combo),
                "survival": [],
                "seed": [(0, 0, 0, 0)],
                "k": 1,
            })

        return results

    def search_birth_pairs(self,
                           survival: frozenset = frozenset(),
                           max_combinations: int = None) -> List[Dict]:
        """
        Exhaustive search over birth signature pairs.

        Based on Grok Genesis: search over pairs of single-bit birth masks
        from 8 neighbor positions.
        """
        single_bit_masks = [1, 2, 4, 8, 16, 32, 64, 128]
        combos = list(combinations(single_bit_masks, 2))

        if max_combinations:
            combos = combos[:max_combinations]

        results = []
        for a, b in combos:
            yield {"birth": (a, b), "survival": sorted(survival)}

    def search_birth_survival_pairs(self,
                                    max_birth_bits: int = 2,
                                    max_survival_bits: int = 0) -> List[Dict]:
        """
        Exhaustive search over birth and survival signature combinations.

        Based on Meta Genesis: exhaustive search over subsets of single-bit
        birth/survival masks.
        """
        single_bit_masks = [1, 2, 4, 8, 16, 32, 64, 128]

        from itertools import combinations, product

        birth_combos = list(combinations([1,2,4,8,16,32,64,128], 2))
        survival_combos = [frozenset()] + [frozenset(c) for c in combinations([1,2,4,8,16,32,64,128], 1)]

        for birth in birth_combos:
            for surv in survival_combos:
                yield {"birth": birth, "survival": surv}

    def search_birth_signatures_exhaustive(self,
                                           max_birth_signatures: int = 3,
                                           max_survival_signatures: int = 1) -> Iterator[Dict]:
        """
        Exhaustive search over birth and survival signature combinations.

        Based on Meta Genesis exhaustive search over single-bit mask subsets.
        """
        from itertools import combinations, chain

        single_bit_masks = [1, 2, 4, 8, 16, 32, 64, 128]

        # Generate all birth signature combinations
        birth_combos = []
        for r in range(1, max_birth_signatures + 1):
            birth_combos.extend(combinations([1,2,4,8,16,32,64,128], r))

        # Generate all survival combinations
        survival_combos = [frozenset()]
        for r in range(1, max_survival_signatures + 1):
            survival_combos.extend(frozenset(c) for c in combinations([1,2,4,8,16,32,64,128], r))

        for birth in birth_combos:
            for surv in survival_combos:
                yield {
                    "birth": birth,
                    "survival": surv,
                    "birth_masks": list(birth),
                    "survival_masks": list(surv),
                }

    def search_with_evaluator(self,
                              search_space: Iterator[Dict],
                              evaluator,
                              fitness_fn,
                              max_iterations: int = 10000) -> List[Dict]:
        """
        Run exhaustive search with evaluator and fitness function.

        Yields best results found.
        """
        best = None
        best_fitness = float('-inf')
        count = 0

        for candidate in search_space:
            # Convert candidate to program
            program = self._candidate_to_program(candidate)

            # Evaluate
            result = self.evaluator.run(candidate_program, max_steps=10000)

            # Compute fitness
            fitness = fitness_fn(result)

            if fitness > best_fitness:
                best_fitness = fitness
                best = {
                    "candidate": candidate,
                    "fitness": fitness,
                    "result": result,
                }
                yield {
                    "candidate": candidate,
                    "fitness": fitness,
                    "result": result,
                }

            if count >= max_iterations:
                break

        return

    def _candidate_to_program(self, candidate: Dict) -> bytes:
        """Convert candidate spec to Malbolge program bytes."""
        # This would be implemented based on the specific search strategy
        # For now, return a placeholder
        return b""


@dataclass
class ExhaustiveSearchConfig:
    """Configuration for exhaustive search."""
    max_birth_signatures: int = 3
    max_survival_signatures: int = 1
    max_combinations: Optional[int] = None
    timeout_seconds: int = 300
    seed: int = 42


class ExhaustiveSearchEngine:
    """
    Main exhaustive search engine for Malbolge program discovery.

    Implements multiple search strategies:
    1. Oriented opposite birth pairs (Grok style)
    2. Exhaustive birth/survival pairs (Meta style)
    3. Full signature space enumeration
    """

    def __init__(self, evaluator, fitness_fn=None, config=None):
        self.evaluator = evaluator
        self.config = config or ExhaustiveSearchConfig()
        self.fitness_fn = fitness_fn

    def run_oriented_pairs_search(self) -> List[Dict]:
        """
        Search for oriented opposite birth pairs (Grok style).

        Tests all 4 axis-aligned opposite birth pairs:
        X: (2,4), Y: (8,16), Z: (32,64), T: (128,256) [in 3^10: 2,4 / 8,16 / 32,64 / 128,256]
        """
        # In 3^10 (59049), neighbor offsets map to bits 1..8
        # Birth toward +X: bit 1 (neighbor at -X)
        # Birth toward -X: bit 2 (neighbor at +X)
        # etc.
        pairs = [
            (2, 4),   # X axis: birth toward +X and -X
            (8, 16),  # Y axis
            (32, 64), # Z axis
            (128, 256), # T axis
        ]

        results = []
        for i, (pos, neg) in enumerate(pairs):
            active = frozenset([pos, neg])
            # This would be evaluated against the substrate
            yield {
                "axis": ["X", "Y", "Z", "T"][i],
                "live_sigs": sorted([pos, neg]),
                "seed": [(0, 0, 0, 0)],
                "k": 1,
            }

    def run_exhaustive_birth_pairs(self, survival: frozenset = frozenset()):
        """
        Exhaustive search over all pairs of single-bit birth masks.

        There are C(8,2) = 28 combinations of 2 birth masks from 8 neighbors.
        """
        from itertools import combinations

        single_bit_masks = [1, 2, 4, 8, 16, 32, 64, 128]

        for a, b in combinations(single_bit_masks, 2):
            yield {
                "birth": (a, b),
                "survival": frozenset(),
                "live_sigs": frozenset([a, b]),
            }

    def run_full_exhaustive(self, max_birth=3, max_survival=1):
        """
        Full exhaustive search over birth/survival combinations.
        """
        from itertools import combinations, chain

        single_bit_masks = [1, 2, 4, 8, 16, 32, 64, 128]

        birth_combos = []
        for r in range(1, self.config.max_birth_signatures + 1):
            birth_combos.extend(combinations([1,2,4,8,16,32,64,128], r))

        survival_combos = [frozenset()]
        for r in range(1, self.config.max_survival_signatures + 1):
            survival_combos.extend(frozenset(c) for c in combinations([1,2,4,8,16,32,64,128], r))

        for birth in birth_combos:
            for surv in survival_combos:
                yield {
                    "birth": birth,
                    "survival": surv,
                    "live_sigs": frozenset(birth) | surv,
                }


if __name__ == "__main__":
    # Quick test
    from danny.evaluator import UnifiedEvaluator

    evaluator = UnifiedEvaluator()
    search = ExhaustiveSearch(evaluator)

    print("Testing oriented pairs search...")
    for result in search.run_oriented_pairs_search():
        print(f"  {result}")

    print("\nTesting exhaustive birth pairs...")
    count = 0
    for candidate in search.run_exhaustive_birth_pairs():
        count += 1
        if count <= 5:
            print(f"  {candidate}")
    print(f"Total combinations: {count}")