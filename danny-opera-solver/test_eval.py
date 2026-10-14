#!/usr/bin/env python3
"""Test the evaluator with real backends."""

import sys
sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator

def main():
    evaluator = UnifiedEvaluator()
    print("Backends:", evaluator.registry.list_backends())
    
    # Test with hello.malbolge
    specimen = Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge")
    if specimen.exists():
        print(f"\nTesting with {specimen}")
        results = evaluator.evaluate_all(specimen)
        
        for name, result in results.items():
            print(f"\n  {name}:")
            print(f"  success: {result.success}")
            print(f"  returncode: {result.returncode}")
            print(f"  stdout: {result.stdout[:100] if result.stdout else '(empty)'}")
            print(f"  stderr: {result.stderr[:100] if result.stderr else '(empty)'}")
            print(f"  steps: {result.steps}")
            print(f"  halted: {result.halted}")
            print(f"  halt_reason: {result.halt_reason}")
            print(f"  elapsed_ms: {result.elapsed_ms}")
            print(f"  backend: {result.backend}")

if __name__ == "__main__":
    main()