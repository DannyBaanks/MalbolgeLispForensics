#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Danny Opera Solver."""

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from danny.dsl import parse_dannyscript

def test_parse():
    """Test parsing a simple DannyScript."""
    script = 'target "Hello World!"\nconstraint max_steps = 1000000\nobjective minimize steps'
    spec = parse_dannyscript(script)
    print(f"Target: {spec.target}")
    print(f"Constraints: {spec.constraints}")
    print(f"Objectives: {spec.objectives}")
    print(f"Config: {spec.config}")
    print("Parse OK!")
    return True

if __name__ == "__main__":
    test_parse()
    print("All tests passed!")