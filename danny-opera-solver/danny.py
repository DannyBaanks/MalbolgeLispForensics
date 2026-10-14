#!/usr/bin/env python3
"""
Danny Opera Solver — Malbolge program search & verification framework.

A framework for searching, verifying, and analyzing Malbolge programs
using multiple backends (bolge19, malbolge-oracle, genesis_engine, Walbolge, Autobolge).
"""
from __future__ import annotations

from danny.cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())