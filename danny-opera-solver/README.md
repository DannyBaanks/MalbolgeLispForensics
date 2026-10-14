# Danny Opera Solver

**Malbolge program search & verification framework**

A framework for searching, verifying, and analyzing Malbolge programs using multiple backends.

## Overview

Danny Opera Solver is a framework for:
- **Searching** for Malbolge programs using multiple strategies (exhaustive, simulated annealing, meta search, ablative minimization)
- **Verifying** Malbolge programs with multiple backends (bolge19, malbolge-oracle, Walbolge, Autobolge)
- **Normalizing** Malbolge programs to human-readable mnemonics with cryptographic anchors
- **Benchmarking** across multiple backends (bolge19, malbolge-oracle, genesis_engine, Walbolge, Autobolge)

## Features

- **DannyScript DSL** — Declarative specification of search objectives
- **Multiple Search Strategies**:
  - Exhaustive search (Grok/Meta style)
  - Simulated Annealing (GPT Genesis style)
  - Meta search (exhaustive signature space)
  - Ablative minimization (GPT Genesis style)
- **Multi-backend Evaluation**:
  - `bolge19` — Native Zig VM for 3^19 Malbolge Unshackled
  - `malbolge-oracle` — Python reference interpreter (3^10)
  - `genesis_engine` — 3 search variants (GPT/Grok/Meta)
  - `Walbolge` — Inverse Translator (roundtrip verification)
  - `Autobolge` — BOLG1/BOLG2 container format
- **Verification**:
  - Walbolge roundtrip (Translator ↔ Walbolge)
  - Autobolge BOLG1/BOLG2 container validation
  - Cross-backend agreement verification
- **Normalization** — Malbolge → mnemonic translation with SHA-256 anchors

## Installation

```bash
# From the malbolge-lisp-forensics repo
cd danny-opera-solver
pip install -e .
```

## Quick Start

```bash
# Solve a DannyScript specification
danny solve specimen.danny

# Verify a specimen with Walbolge and Autobolge
danny verify specimen.mal --walbolge --autobolge --manifest manifest.json

# Normalize a Malbolge program to mnemonics
danny normalize specimen.mb --output normalized.txt

# Search with specific strategy
danny search specimen.danny --strategy exhaustive --preset default
```

## DannyScript DSL

```dannyscript
target "Hello World!"
constraint max_steps = 1000000
constraint memory_limit = 59049
objective minimize steps
objective minimize size
config backend = "bolge19"
config seed = 42
```

## Architecture

```
danny-opera-solver/
├── danny/
│   ├── dsl.py              # DannyScript parser
│   ├── evaluator.py        # Unified backend evaluator
│   ├── objectives.py       # Multi-objective fitness functions
│   ├── search/
│   │   ├── exhaustive.py   # Exhaustive search (Grok/Meta style)
│   │   ├── sa.py           # Simulated Annealing (GPT style)
│   │   ├── meta.py         # Meta search (exhaustive signature space)
│   │   └── ablative.py     # Ablative minimization
│   ├── verify/
│   │   ├── walbolge.py     # Walbolge roundtrip verification
│   │   └── autobolge.py    # Autobolge BOLG1/BOLG2 validation
│   ├── objectives.py       # Multi-objective fitness functions
│   ├── evaluator.py        # Unified backend evaluator
│   └── cli.py              # CLI entry point
├── danny_script/           # Example DannyScript specifications
├── evidence/               # Evidence/hashes from runs
├── specimens/              # Test specimens
└── tests/                  # Unit tests
```

## Backends

| Backend | Type | Architecture | Use Case |
|---------|------|--------------|----------|
| `bolge19` | Native Zig | 3^19 (Unshackled) | Full MalbolgeLISP execution |
| `fast20_fixed` | C (Cygwin) | 3^19 (Unshackled) | Patched fast20 |
| `malbolge-oracle` | Python | 3^10 (classic) | Reference control |
| `genesis_engine` | Python | 4D CA | Replicator search |
| `malbolge-toolkit` | Python | 3^10 | Generation/execution |
| `Walbolge` | Python | 3^10 | Translator roundtrip |
| `Autobolge` | Zig | 3^10 | BOLG1/BOLG2 containers |

## Evidence & Reproducibility

All runs produce cryptographically verifiable evidence:
- SHA-256 hashes of all artifacts
- Anchor checkpoints (periodic SHA-256 of normalized output)
- Dual-formula cross-checks
- Raw stdout/stderr preservation
- Git commit tracking

## License

MIT (our additions) — Upstream MalbolgeLISP/fast20 is CC0 1.0 Universal.

## Citation

```bibtex
@software{danny_opera_solver,
  author = {ISyCo Research Workspace},
  title = {Danny Opera Solver: Malbolge Program Search & Verification},
  year = {2026},
  url = {https://github.com/ISyCo/malbolge-lisp-forensics}
}
```