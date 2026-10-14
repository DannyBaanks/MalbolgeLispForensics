#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test of DannyScript parser."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from danny.dsl import parse_dannyscript

def main():
    # Test basic target parsing
    script1 = 'target "Hello World!"'
    spec1 = parse_dannyscript(script1)
    print(f"Test 1 - Basic target:")
    print(f"  Target: {spec1.target}")
    print(f"  Constraints: {spec1.constraints}")
    print(f"  Objectives: {spec1.objectives}")
    print(f"  Config: {spec1.config}")
    print()

    # Test with constraints
    script2 = '''target "Hello World!"
constraint max_steps = 1000000
constraint memory_limit = 59049
config backend = "bolge19"
config seed = 42'''
    spec2 = parse_dannyscript(script2)
    print(f"Test 2 - With constraints:")
    print(f"  Target: {spec2.target}")
    print(f"  Constraints: {spec2.constraints}")
    print(f"  Config: {spec2.config}")
    print()

    # Test objectives (minimize/maximize)
    script3 = '''target "Hello World!"
minimize steps
minimize size
maximize correctness'''
    spec3 = parse_dannyscript(script3)
    print(f"Test 3 - With objectives:")
    print(f"  Target: {spec3.target}")
    print(f"  Objectives: {spec3.objectives}")
    print()

    print("All basic parsing tests passed!")
    return True

if __name__ == "__main__":
    try:
        main()
        print("All tests passed!")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)