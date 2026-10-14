#!/usr/bin/env python3
"""Test all backends with quijote specimen."""

import sys
sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator

def main():
    evaluator = UnifiedEvaluator()
    
    specimen = Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\quijote\chapter_001\quijote_ch001_full.mal")
    print(f"Testing with: {specimen}")
    print(f"Exists: {specimen.exists()}")
    
    results = evaluator.evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\quijote\chapter_001\quijote_ch001_full.mal"))
    
    for name, result in results.items():
        print(f"\n  {name}:")
        print(f"  success: {result.success}")
        print(f"  returncode: {result.returncode}")
        stdout_preview = result.stdout[:80] if result.stdout else "(empty)"
        print(f"  stdout: {stdout_preview}")
        print(f"  steps: {result.steps}")
        print(f"  halted: {result.halted}")
        print(f"  halt_reason: {result.halt_reason}")

if __name__ == "__main__":
    main()