#!/usr/bin/env python3
"""
Danny Opera Solver — CLI entry point.

Usage:
    danny solve --spec specimen.danny
    danny normalize --spec specimen.danny --output normalized.txt
    danny verify --specimen specimen.mal --manifest manifest.json
    danny search --spec specimen.danny --strategy exhaustive
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from danny.dsl import parse_dannyscript_file, DannySpec
from danny.evaluator import UnifiedEvaluator
from danny.objectives import FitnessEvaluator, create_fitness_evaluator
from danny.search.exhaustive import ExhaustiveSearch, ExhaustiveSearchConfig
from danny.search.sa import SimulatedAnnealingSearch, SAConfig
from danny.search.meta import MetaSearch, MetaSearchConfig
from danny.search.ablative import ablative_minimize
from danny.verify.walbolge import WalbolgeVerifier
from danny.verify.autobolge import AutobolgeVerifier
from danny.objectives import FitnessEvaluator, create_fitness_evaluator
from danny.evaluator import UnifiedEvaluator


def cmd_solve(args):
    """Solve a DannyScript specification."""
    spec = parse_dannyscript_file(Path(args.spec))

    evaluator = UnifiedEvaluator()
    fitness = create_fitness_evaluator(args.preset or "default")

    # For now, just show the parsed spec
    print(f"Target: {spec.target}")
    print(f"Constraints: {spec.constraints}")
    print(f"Objectives: {spec.objectives}")
    print(f"Config: {spec.config}")

    # TODO: Implement actual search based on spec
    print(f"\n[TODO] Implement search for: {spec.target}")


def cmd_normalize(args):
    """Normalize a Malbolge program to mnemonics."""
    from danny.search.ablative import ablative_minimize
    from danny.evaluator import UnifiedEvaluator

    # This would use bolge19 --normalize equivalent
    print(f"Normalizing {args.specimen} -> {args.output}")
    print("[TODO] Implement normalization with bolge19")


def cmd_verify(args):
    """Verify a specimen with Walbolge and/or Autobolge."""
    from danny.verify.walbolge import WalbolgeVerifier
    from danny.verify.autobolge import AutobolgeVerifier

    specimen = Path(args.specimen)
    if not specimen.exists():
        print(f"Specimen not found: {specimen}")
        return 1

    print(f"Verifying {specimen}...")

    # Walbolge roundtrip
    if args.walbolge:
        print("\n--- Walbolge Roundtrip ---")
        walbolge = WalbolgeVerifier()
        result = walbolge.verify_specimen(
            str(specimen),
            manifest=args.manifest,
            words_dir=args.words_dir,
        )
        print(f"  Roundtrip: {result.get('roundtrip_perfect', 'N/A')}")
        print(f"  Text match: {result.get('text_match', 'N/A')}")

    # Autobolge
    if args.autobolge:
        print("\n--- Autobolge Validation ---")
        autobolge = AutobolgeVerifier()
        with open(args.specimen, 'r', encoding='ascii') as f:
            text = f.read().strip()
        result = autobolge.run(text)
        print(f"  Output: {result.get('output', 'N/A')[:100]}")
        print(f"  Steps: {result.get('steps', 'N/A')}")
        print(f"  Halted: {result.get('halted', 'N/A')}")


def cmd_search(args):
    """Run search with specified strategy."""
    from danny.search.exhaustive import ExhaustiveSearch, ExhaustiveSearchConfig
    from danny.search.sa import SimulatedAnnealingSearch, SAConfig
    from danny.search.meta import MetaSearch, MetaSearchConfig
    from danny.evaluator import UnifiedEvaluator
    from danny.objectives import create_fitness_evaluator

    spec = parse_dannyscript_file(Path(args.spec))
    evaluator = UnifiedEvaluator()
    fitness = create_fitness_evaluator(args.preset or "default")

    if args.strategy == "exhaustive":
        config = ExhaustiveSearchConfig()
        search = ExhaustiveSearch(UnifiedEvaluator())
        # TODO: implement based on spec
        print(f"Exhaustive search for: {spec.target}")
    elif args.strategy == "sa":
        config = SAConfig()
        search = SimulatedAnnealingSearch(None, config=SAConfig())
        print("SA search [TODO]")
    elif args.strategy == "meta":
        config = MetaSearchConfig()
        search = MetaSearch(None, config=MetaSearchConfig())
        print("Meta search [TODO]")
    elif args.strategy == "ablative":
        print("Ablative minimization [TODO]")
    else:
        print(f"Unknown strategy: {args.strategy}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="danny",
        description="Danny Opera Solver — Malbolge program search & verification",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # solve
    p_solve = subparsers.add_parser("solve", help="Solve a DannyScript specification")
    p_solve.add_argument("spec", help="Path to .danny spec file")
    p_solve.add_argument("--preset", default="default", choices=["default", "size_optimized", "speed_optimized", "exact_match"])
    p_solve.set_defaults(func=cmd_solve)

    # normalize
    p_norm = subparsers.add_parser("normalize", help="Normalize Malbolge program to mnemonics")
    p_norm.add_argument("specimen", help="Path to .mb specimen")
    p_norm.add_argument("-o", "--output", required=True, help="Output file")
    p_norm.set_defaults(func=cmd_normalize)

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify specimen with Walbolge/Autobolge")
    p_verify.add_argument("specimen", help="Path to .mal specimen")
    p_verify.add_argument("--manifest", help="Translator manifest JSON")
    p_verify.add_argument("--words-dir", help="Words directory for Walbolge")
    p_verify.add_argument("--walbolge", action="store_true", help="Run Walbolge roundtrip")
    p_verify.add_argument("--autobolge", action="store_true", help="Run Autobolge validation")
    p_verify.set_defaults(func=cmd_verify)

    # search
    p_search = subparsers.add_parser("search", help="Search for Malbolge programs")
    p_search.add_argument("spec", help="Path to .danny spec file")
    p_search.add_argument("--strategy", choices=["exhaustive", "sa", "meta", "ablative"], default="exhaustive")
    p_search.add_argument("--preset", default="default", choices=["default", "size_optimized", "speed_optimized", "exact_match"])
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())