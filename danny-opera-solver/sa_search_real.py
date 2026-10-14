#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SA Search for Hello World with guided fitness."""

import sys
import time
import tempfile
import random
import math
import os

sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

from pathlib import Path
from danny.evaluator import UnifiedEvaluator


def mutate_program(program, mutation_rate=0.1):
    """Mutate a Malbolge program by randomly changing characters."""
    chars = list(program)
    for i in range(len(chars)):
        if random.random() < mutation_rate:
            chars[i] = chr(random.randint(33, 126))
    return ''.join(chars)


def fitness_hello_world(result, target="Hello World!"):
    """Fitness function for Hello World. Lower = better."""
    if not result['success'] or not result['halted']:
        return 10000 + (1000 if not result['success'] else 0)
    
    output = result['output'] or ''
    target = target
    
    if not result['halted']:
        return 10000
    
    # Longest common prefix
    prefix_len = 0
    for a, b in zip(output, target):
        if a == b:
            prefix_len += 1
        else:
            break
    
    prefix_score = (len(target) - prefix_len) * 100
    step_penalty = result['steps'] / 100.0
    length_penalty = abs(len(output) - len(target)) * 10
    
    fitness = prefix_score + step_penalty + length_penalty
    
    if output.strip() == target:
        fitness = 0
    
    return fitness


def mutate_program(program, mutation_rate=0.1):
    """Mutate a Malbolge program by randomly changing characters."""
    chars = list(program)
    for i in range(len(chars)):
        if random.random() < mutation_rate:
            chars[i] = chr(random.randint(33, 126))
    return ''.join(chars)


def run_sa_search():
    """Simulated Annealing search for Hello World."""
    print("=" * 60)
    print("SA SEARCH FOR HELLO WORLD - GUIDED FITNESS")
    print("=" * 60)
    
    evaluator = UnifiedEvaluator()
    print("Backends:", UnifiedEvaluator().registry.list_backends())
    
    # Verify evaluator works
    print("\n[1] Verifying evaluator with known hello.malbolge...")
    evaluator = UnifiedEvaluator()
    results = UnifiedEvaluator().evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge"))
    for name, result in results.items():
        print(f"  {name}: success={result.success}, stdout={result.stdout[:30] if result.stdout else 'empty'}, steps={result.steps}, halted={result.halted}")
    
    # Fitness function
    def fitness_hello_world(result, target="Hello World!"):
        if not result['success'] or not result['halted']:
            return 10000 + (1000 if not result['success'] else 0)
        
        output = result['output'] or ''
        target = target
        
        if not result['halted']:
            return 10000
        
        prefix_len = 0
        for a, b in zip(output, target):
            if a == b:
                prefix_len += 1
            else:
                break
        
        prefix_score = (len(target) - prefix_len) * 100
        step_penalty = result['steps'] / 100.0
        length_penalty = abs(len(output) - len(target)) * 10
        
        fitness = prefix_score + step_penalty + length_penalty
        
        if output.strip() == target:
            fitness = 0
        
        return fitness
    
    def mutate_program(program, mutation_rate=0.1):
        chars = list(program)
        for i in range(len(chars)):
            if random.random() < mutation_rate:
                chars[i] = chr(random.randint(33, 126))
        return ''.join(chars)
    
    # Start with random program
    current = ''.join(chr(random.randint(33, 126)) for _ in range(64))
    
    # Evaluate initial
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
        f.write(current)
        temp_path = f.name
    
    evaluator = UnifiedEvaluator()
    results = UnifiedEvaluator().evaluate_all(Path(temp_path))
    oracle_result = results.get('oracle')
    
    if oracle_result and oracle_result.success:
        current_fitness = fitness_hello_world({
            'success': oracle_result.success,
            'output': oracle_result.stdout or '',
            'steps': oracle_result.steps,
            'halted': oracle_result.halted
        })
    else:
        current_fitness = 10000
    
    os.unlink(temp_path)
    
    best_program = current
    best_fitness = current_fitness
    
    print(f"Initial program fitness: {current_fitness}")
    print(f"Initial program: {current[:50]}...")
    
    # SA parameters
    temp = 5.0
    cooling_rate = 0.9995
    min_temp = 0.01
    max_iterations = 5000
    
    start_time = time.time()
    current_program = current
    current_fitness = current_fitness
    
    best_program = current
    best_fitness = current_fitness
    
    for iteration in range(5000):
        temp *= 0.9995
        if temp < 0.01:
            temp = 0.01
        
        # Generate neighbor
        neighbor = mutate_program(current, mutation_rate=0.1)
        
        # Evaluate neighbor
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mb', delete=False, encoding='ascii') as f:
            f.write(neighbor)
            temp_path = f.name
        
        try:
            results = UnifiedEvaluator().evaluate_all(Path(temp_path))
            oracle_result = results.get('oracle')
            
            if oracle_result and oracle_result.success:
                neighbor_fitness = fitness_hello_world({
                    'success': oracle_result.success,
                    'output': oracle_result.stdout or '',
                    'steps': oracle_result.steps,
                    'halted': oracle_result.halted
                })
            else:
                neighbor_fitness = 10000
        except:
            neighbor_fitness = 10000
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
        
        # Metropolis acceptance
        delta = neighbor_fitness - current_fitness
        accept = False
        if delta <= 0:
            accept = True
        else:
            prob = math.exp(-delta / temp)
            if random.random() < prob:
                accept = True
        
        if accept:
            current = neighbor
            current_fitness = neighbor_fitness
            if current_fitness < best_fitness:
                best_fitness = current_fitness
                best_program = current
                elapsed = time.time() - start_time
                print(f"  Iter {iteration}: New best fitness = {best_fitness:.2f}, temp={temp:.3f}, prog={current[:50]}...")
        
        if best_fitness == 0:
            print(f"\n*** PERFECT MATCH FOUND at iteration {iteration}! ***")
            print(f"Program: {best_program}")
            break
        
        if iteration % 500 == 0:
            elapsed = time.time() - start_time
            print(f"  Iter {iteration}: best={best_fitness:.2f}, current={current_fitness:.2f}, temp={temp:.3f}, time={elapsed:.1f}s")
    
    elapsed = time.time() - start_time
    print(f"\nSA completed in {time.time() - start_time:.1f}s")
    print(f"Best fitness: {best_fitness}")
    print(f"Best program: {best_program}")
    return best_program, best_fitness


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")
    
    import time
    import tempfile
    import random
    import math
    
    from pathlib import Path
    from danny.evaluator import UnifiedEvaluator
    
    print("=" * 60)
    print("SA SEARCH FOR HELLO WORLD - GUIDED FITNESS")
    print("=" * 60)
    
    evaluator = UnifiedEvaluator()
    print("Backends:", UnifiedEvaluator().registry.list_backends())
    
    # Verify evaluator works
    print("\n[1] Verifying evaluator with known hello.malbolge...")
    evaluator = UnifiedEvaluator()
    results = UnifiedEvaluator().evaluate_all(Path(r"C:\Development\ISyCo Git\malbolge-lisp-forensics\specimens\hello.malbolge"))
    for name, result in results.items():
        print(f"  {name}: success={result.success}, stdout={result.stdout[:30] if result.stdout else 'empty'}, steps={result.steps}, halted={result.halted}")
    
    print("\n[2] Starting Simulated Annealing search for Hello World...")
    print("Target: Hello World!")
    print("Max iterations: 5000")
    
    # Run the SA search
    run_sa_search()
    
    print("\nSearch completed!")