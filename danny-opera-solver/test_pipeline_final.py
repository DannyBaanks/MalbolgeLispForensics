#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pipeline 1-2-3-4: Exhaustive -> SA -> Meta -> Ablative."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def run_exhaustive_test():
    """1. Exhaustive search (Meta/Grok style) - test oriented pairs."""
    print("\n" + "=" * 60)
    print("1. EXHAUSTIVE SEARCH (Meta/Grok style)")
    print("=" * 60)
    
    from danny.search.exhaustive import ExhaustiveSearchEngine
    from danny.evaluator import UnifiedEvaluator
    
    evaluator = UnifiedEvaluator()
    search = ExhaustiveSearchEngine(None)  # evaluator not needed for this test
    
    print("Running exhaustive oriented pairs search (4 axes)...")
    start = time.time()
    
    found = 0
    for candidate in ExhaustiveSearchEngine(None).run_oriented_pairs_search():
        print(f"  Found replicator on axis {candidate['axis']}: live_sigs={candidate['live_sigs']}")
        found += 1
    
    elapsed = time.time() - start
    print(f"Exhaustive oriented pairs search: {elapsed:.3f}s, found {found} replicators")
    return True


def run_sa_test():
    """2. Simulated Annealing test."""
    print("\n" + "=" * 60)
    print("2. SIMULATED ANNEALING (GPT style)")
    print("=" * 60)
    
    from danny.search.sa import run_sa_search, SAConfig
    
    # Simple fitness: minimize active bits
    config = SAConfig(max_iterations=5000)
    result = run_sa_search(
        fitness_fn=lambda b: sum(b),
        config=SAConfig(max_iterations=5000),
        seed=42
    )
    
    print(f"SA completed: best_fitness={result['best_fitness']}, "
          f"iterations={result['iterations']}, "
          f"active_bits={sum(result['best_bits'])}, "
          f"time={result['elapsed_sec']:.3f}s")
    return True


def run_meta_test():
    """Meta search test."""
    print("\n" + "=" * 60)
    print("3. META SEARCH (exhaustive signature space)")
    print("=" * 60)
    
    from danny.search.meta import MetaSearch, MetaSearchConfig
    
    config = MetaSearchConfig(max_birth_signatures=2, max_survival_signatures=1)
    search = MetaSearch(None, config=MetaSearchConfig())
    
    print("Running Meta search (oriented pairs)...")
    start = time.time()
    
    for candidate in search.search_oriented_pairs():
        print(f"  Found replicator on axis {candidate['axis']}: live_sigs={candidate['live_sigs']}")
    
    print(f"Meta search completed in {time.time() - start:.3f}s")
    return True


def run_ablative_test():
    """Test ablative minimization."""
    print("\n" + "=" * 60)
    print("4. ABLATIVE MINIMIZATION")
    print("=" * 60)
    
    from danny.search.ablative import ablative_minimize
    
    # Dummy candidate and fitness for testing
    candidate = {
        'birth': [1, 2, 4, 8],
        'survival': [16],
        'live_sigs': {1, 2, 4, 8, 16},
    }
    
    def fitness_fn(cand):
        return len(cand.get('live_sigs', []))
    
    from danny.search.ablative import ablative_minimize
    result = ablative_minimize(candidate, lambda c: len(c.get('live_sigs', [])), max_passes=3)
    
    print(f"Ablative result: removed={result['removed_count']}, "
          f"passes={result['passes']}, final_live_sigs={result['minimized']['live_sigs']}")
    return True


def main():
    print("=" * 60)
    print("DANNY OPERA SOLVER - PIPELINE 1-2-3-4")
    print("=" * 60)
    
    total_start = time.time()
    
    # 1. Exhaustive
    run_exhaustive_test()
    
    # 2. SA
    run_sa_test()
    
    # 3. Meta
    run_meta_test()
    
    # 4. Ablative
    run_ablative_test()
    
    total_elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"TOTAL PIPELINE TIME: {time.time() - start_time:.3f}s")
    print("ALL 4 STRATEGIES COMPLETED!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    import time
    start_time = time.time()
    sys.exit(main())