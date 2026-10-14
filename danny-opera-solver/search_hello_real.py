#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test search for Hello World with real evaluator."""

import sys
import time
import tempfile
import random
import os

sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator


def main():
    print("=" * 60)
    print("REAL HELLO WORLD SEARCH - PIPELINE TEST")
    print("=" * 60)
    
    evaluator = UnifiedEvaluator()
    print("Backends:", UnifiedEvaluator().registry.list_backends())
    
    # Quick verification first
    print("\n[1] Verifying evaluator with known hello.malbolge...")
    evaluator = UnifiedEvaluator()
    results = UnifiedEvaluator().evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge"))
    for name, result in results.items():
        print(f"  {name}: success={result.success}, stdout={result.stdout[:30] if result.stdout else 'empty'}, steps={result.steps}, halted={result.halted}")
    
    print("\n[1] Testing random search (50 random programs)...")
    import tempfile
    import random
    
    start = time.time()
    for i in range(50):
        prog = ''.join(chr(random.randint(33, 126)) for _ in range(64))
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
            f.write(prog)
            temp_path = f.name
        
        try:
            results = UnifiedEvaluator().evaluate_all(Path(temp_path))
            oracle_result = results.get('oracle')
            if oracle_result and oracle_result.success and 'Hello World' in oracle_result.stdout:
                print(f"  FOUND at iteration {i}!")
                print(f"  Program: {prog[:50]}...")
                break
        except Exception as e:
            pass
        finally:
            try: os.unlink(temp_path)
            except: pass
        
        if i % 10 == 0:
            elapsed = time.time() - start
            print(f"  Tried {i} random programs, {elapsed:.1f}s elapsed...")
    
    elapsed = time.time() - start
    print(f"\nRandom search completed in {time.time() - start:.1f}s")
    print("Baseline: random search is extremely unlikely to find Hello World")
    print("Need guided search (SA, GA, etc.)")
    
    return True


if __name__ == "__main__":
    import sys
    import time
    import tempfile
    import random
    from pathlib import Path
    from danny.evaluator import UnifiedEvaluator
    
    main()