#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast SA Search for Hello World - Optimized."""

import sys
import time
import tempfile
import random
import math
import os

sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator


def random_program(length=64):
    return ''.join(chr(random.randint(33, 126)) for _ in range(length))


def mutate(prog, rate=0.1):
    return ''.join(chr(random.randint(33, 126)) if random.random() < 0.1 else c for c in prog)


def eval_prog(prog):
    """Evaluate a program, return (output, steps, halted, success)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
        f.write(prog)
        path = f.name
    try:
        results = UnifiedEvaluator().evaluate_all(Path(f.name))
        oracle = results.get('oracle')
        if oracle and oracle.success:
            return oracle.stdout or '', oracle.steps, oracle.halted, True
        return '', 0, False, False
    except:
        return '', 0, False, False
    finally:
        try: os.unlink(path)
        except: pass


def fitness(out, steps, halted):
    if not halted:
        return 10000
    pref = sum(a==b for a,b in zip(out or '', "Hello World!"))
    fit = (12 - sum(a==b for a,b in zip(out or '', "Hello World!"))) * 100
    fit += steps / 100.0
    fit += abs(len(out) - 12) * 10
    if out.strip() == "Hello World!":
        return 0
    return fit


def run_sa():
    print("="*50)
    print("FAST SA SEARCH - HELLO WORLD")
    print("="*50)

    # Quick verify
    r = UnifiedEvaluator().evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge"))
    for n, v in r.items():
        print(f"  {n}: ok={v.success}, steps={v.steps}, out={v.stdout[:30] if v.stdout else ''}")

    # --- SA ---
    current = ''.join(chr(random.randint(33, 126)) for _ in range(64))

    # Evaluate initial
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
        f.write(current)
        path = f.name
    r = UnifiedEvaluator().evaluate_all(Path(path))
    o = r.get('oracle')
    if o and o.success:
        cur_fit = 0 if o.stdout.strip()=="Hello World!" else (12-sum(a==b for a,b in zip(o.stdout or '',"Hello World!")))*100 + o.steps/100 + abs(len(o.stdout)-12)*10
    else:
        cur_fit = 10000
    os.unlink(path)

    best_prog = current
    best_fit = 10000
    cur_fit = 10000
    current = current
    T = 5.0
    t0 = time.time()

    for it in range(1000):
        if it % 100 == 0:
            elapsed = time.time() - t0
            print(f"  it={it}, best={best_fit:.1f}, cur={cur_fit:.1f}, T={T:.3f}, t={time.time()-t0:.1f}s")

        T *= 0.995
        if T < 0.01: T = 0.01

        cand = ''.join(chr(random.randint(33,126)) if random.random()<0.1 else c for c in current)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
            f.write(cand)
            tp = f.name
        try:
            r = UnifiedEvaluator().evaluate_all(Path(tp))
            o = r.get('oracle')
            if o and o.success:
                out = o.stdout or ''
                steps = o.steps
                halt = o.halted
                pref = sum(a==b for a,b in zip(o.stdout or '', "Hello World!"))
                fit = (12 - sum(a==b for a,b in zip(o.stdout or '', "Hello World!"))) * 100
                fit += steps / 100.0
                fit += abs(len(o.stdout) - 12) * 10
                if o.stdout.strip() == "Hello World!":
                    fit = 0
            else:
                fit = 10000
        except:
            fit = 10000
        finally:
            try: os.unlink(tp)
            except: pass

        delta = fit - cur_fit
        if fit <= cur_fit or random.random() < math.exp(-(fit - cur_fit)/T):
            current = cand
            cur_fit = fit
            if fit < best_fit:
                best_fit = fit
                best_prog = cand
                elapsed = time.time() - t0
                print(f"  it={it}: BEST={best_fit:.1f}, T={T:.3f}, prog={cand[:40]}...")

        if best_fit == 0:
            print("\n*** FOUND PERFECT MATCH! ***")
            print(f"Program: {best_prog}")
            break

        if it % 100 == 0:
            elapsed = time.time() - t0
            print(f"  it={it}: best={best_fit:.1f}, cur={cur_fit:.1f}, T={T:.3f}, t={time.time()-t0:.1f}s")

        T *= 0.995
        if T < 0.01: T = 0.01

    elapsed = time.time() - start
    print(f"\nDone in {time.time()-start:.1f}s, best fitness={best_fit}")
    print(f"Best program: {best_prog[:50]}...")
    return best_prog, best_fit


if __name__ == "__main__":
    import sys
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

    print("\nStarting SA...")
    run_sa()