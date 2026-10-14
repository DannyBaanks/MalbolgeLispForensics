#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast SA Search for Hello World."""

import sys
import time
import tempfile
import random
import math
import os

sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator


def main():
    print("=" * 50)
    print("FAST SA SEARCH - HELLO WORLD")
    print("=" * 50)

    evaluator = UnifiedEvaluator()
    print("Backends:", list(UnifiedEvaluator().registry.backends.keys()))

    # Verify
    r = UnifiedEvaluator().evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge"))
    for n, v in r.items():
        print(f"  {n}: ok={v.success}, steps={v.steps}, out={v.stdout[:30] if v.stdout else ''}")

    # --- SA Search ---
    print("\nStarting SA search for Hello World...")

    evaluator = UnifiedEvaluator()

    def eval_prog(prog):
        """Evaluate program, return (output, steps, halted, success)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
            f.write(prog)
            path = f.name
        try:
            results = UnifiedEvaluator().evaluate_all(Path(f.name))
            oracle = results.get('oracle')
            if oracle and oracle.success:
                return (oracle.stdout or '', oracle.steps, oracle.halted, True)
            return '', 0, False, False
        except:
            return '', 0, False, False
        finally:
            try: os.unlink(f.name)
            except: pass

    def fitness(out, steps, halted):
        if not halted:
            return 10000
        target = "Hello World!"
        pref = sum(a==b for a,b in zip(out or '', "Hello World!"))
        fit = (12 - sum(a==b for a,b in zip(out or '', "Hello World!"))) * 100
        fit += steps / 100.0
        fit += abs(len(out) - 12) * 10
        if out.strip() == "Hello World!":
            return 0
        return fit

    def mutate(prog, rate=0.1):
        return ''.join(chr(random.randint(33,126)) if random.random()<0.1 else c for c in prog)

    # Initial random program
    current = ''.join(chr(random.randint(33,126)) for _ in range(64))
    
    # Evaluate initial
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
        f.write(current)
        path = f.name
    results = UnifiedEvaluator().evaluate_all(Path(path))
    oracle = results.get('oracle')
    if oracle and oracle.success:
        cur_fit = 0 if oracle.stdout.strip()=="Hello World!" else (
            (12 - sum(a==b for a,b in zip(oracle.stdout or '', "Hello World!")))*100 + 
            oracle.steps/100 + abs(len(oracle.stdout)-12)*10
        )
    else:
        cur_fit = 10000
    os.unlink(path)

    best_prog = current
    best_fit = 10000
    current = current
    cur_fit = 10000
    T = 5.0

    print(f"Initial fitness: {cur_fit}")
    start = time.time()

    for it in range(3000):
        if it % 200 == 0:
            elapsed = time.time() - start
            print(f"  it={it}, best={best_fit:.1f}, cur={cur_fit:.1f}, T={T:.3f}, t={time.time()-start:.1f}s")

        temp *= 0.995
        if temp < 0.01: temp = 0.01

        cand = ''.join(chr(random.randint(33,126)) if random.random()<0.1 else c for c in current)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
            f.write(cand)
            tp = f.name

        try:
            results = UnifiedEvaluator().evaluate_all(Path(tp))
            oracle = results.get('oracle')
            if oracle and oracle.success:
                out = oracle.stdout or ''
                steps = oracle.steps
                halt = oracle.halted
                if oracle.stdout.strip() == "Hello World!":
                    fit = 0
                else:
                    pref = sum(a==b for a,b in zip(oracle.stdout or '', "Hello World!"))
                    fit = (12 - sum(a==b for a,b in zip(oracle.stdout or '', "Hello World!"))) * 100
                    fit += steps/100 + abs(len(oracle.stdout)-12)*10
            else:
                fit = 10000
        except:
            fit = 10000
        finally:
            try: os.unlink(tp)
            except: pass

        delta = fit - cur_fit
        if cand_fit <= cur_fit or random.random() < math.exp(-(cand_fit - cur_fit)/temp):
            current = cand
            cur_fit = cand_fit
            if cand_fit < best_fit:
                best_fit = cand_fit
                best_prog = cand
                elapsed = time.time() - start
                print(f"  it={it}: BEST={best_fit:.1f}, T={temp:.3f}, prog={cand[:40]}...")

        if best_fit == 0:
            print("\n*** FOUND PERFECT MATCH! ***")
            print(f"Program: {best_prog}")
            break

        if it % 200 == 0:
            elapsed = time.time() - start
            print(f"  it={it}: best={best_fit:.1f}, cur={cur_fit:.1f}, T={temp:.3f}, t={time.time()-t0:.1f}s")

        temp *= 0.995
        if temp < 0.01: temp = 0.01

    elapsed = time.time() - start
    print(f"\nDone in {time.time()-start:.1f}s, best fitness={best_fit}")
    print(f"Best program: {best_prog[:50]}...")
    return best_prog, best_fit


if __name__ == "__main__":
    import sys
    import time
    import tempfile
    import random
    import math
    import os

    sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

    import time
    import tempfile
    import random
    import math
    import os

    from pathlib import Path
    from danny.evaluator import UnifiedEvaluator

    print("="*50)
    print("FAST SA SEARCH - HELLO WORLD")
    print("="*50)

    evaluator = UnifiedEvaluator()
    print("Backends:", list(UnifiedEvaluator().registry.backends.keys()))

    # Quick verify
    r = UnifiedEvaluator().evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge"))
    for n, v in r.items():
        print(f"  {n}: ok={v.success}, steps={v.steps}, out={v.stdout[:30] if v.stdout else ''}")

    # Run SA
    run_sa()