#!/usr/bin/env python3
"""Test the evaluator with all backends."""

import sys
sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator

def main():
    evaluator = UnifiedEvaluator()
    print("Backends:", evaluator.registry.list_backends())
    
    # Test hello.malbolge
    specimen = Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge")
    results = evaluator.evaluate_all(specimen)
    
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  success: {result.success}")
        print(f"  rc: {result.returncode}")
        print(f"  stdout: {repr(result.stdout[:50])}")
        print(f"  steps: {result.steps}")
        print(f"  halted: {result.halted}")
        print(f"  reason: {result.halt_reason}")

if __name__ == "__main__":
    main()