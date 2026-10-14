#!/usr/bin/env python3
"""
Unified Evaluator — wraps all Malbolge backends for Danny Opera Solver.

Provides a unified interface to evaluate Malbolge programs across multiple backends:
- bolge19 (native Zig, 3^19)
- malbolge-oracle (Python, 3^10 reference)
- fast20_fixed (Cygwin patched)
- autobolge (BOLG1/BOLG2 container)
- walbolge (decompiler/roundtrip)
"""
from __future__ import annotations
import subprocess
import json
import os
import hashlib
import time
import tempfile
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any


@dataclass
class EvalResult:
    """Result of evaluating a Malbolge program."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    steps: int = 0
    halted: bool = False
    halt_reason: str = ""
    elapsed_ms: float = 0.0
    backend: str = ""
    raw_output: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BackendRegistry:
    """Registry of available backends and their capabilities."""

    def __init__(self, repo_root: Path = None):
        forensics_root = Path(__file__).resolve().parents[2]
        isyco_git = forensics_root.parent
        isyco_root = isyco_git.parent / "ISyCo"
        if repo_root is None:
            repo_root = isyco_root if isyco_root.exists() else forensics_root
        self.repo_root = Path(repo_root)
        self.forensics_root = forensics_root
        self.isyco_git = isyco_git
        self.backends = {}
        self._discover_backends()

    def _discover_backends(self):
        """Auto-discover available backends across Linux and Windows."""
        # bolge19 (native Zig)
        for cand in (
            self.forensics_root / "bolge19",
            self.forensics_root / "bolge19.exe",
            self.repo_root / "experiments0000" / "MalbolgeLisp Vs Isyco" / "runtime" / "bolge19.exe",
        ):
            if cand.exists():
                self.backends["bolge19"] = {
                    "type": "native",
                    "exe": cand,
                    "supports_19trit": True,
                    "supports_10trit": False,
                }
                break

        # fast20_fixed
        for cand in (
            self.forensics_root / "src" / "patches" / "fast20_fixed",
            self.forensics_root / "src" / "patches" / "fast20_fixed.exe",
            self.repo_root / "experiments0000" / "MalbolgeLisp Vs Isyco" / "runtime" / "fast20_fixed.exe",
        ):
            if cand.exists():
                self.backends["fast20_fixed"] = {
                    "type": "native",
                    "exe": cand,
                    "supports_19trit": True,
                    "supports_10trit": False,
                }
                break

        # malbolge-oracle
        for cand in (
            self.isyco_git / "malbolge-oracle",
            self.repo_root / "experiments0000" / "MalbolgeLisp Vs Isyco" / "tools" / "malbolge-oracle",
        ):
            if (cand / "oracle.py").exists():
                self.backends["oracle"] = {
                    "type": "python",
                    "module": "oracle",
                    "dir": cand,
                }
                break

        # Classic Malbolge engine
        for cand in (
            self.isyco_git / "Malbolge-Engine" / "malbolge",
            self.isyco_git / "Malbolge-Engine" / "malbolge.exe",
            self.isyco_git / "MALBOLGE-MB-DATABASE" / "runners" / "malbolge-original" / "malbolge",
        ):
            if cand.exists():
                self.backends["engine"] = {
                    "type": "native",
                    "exe": cand,
                }
                break

        # malbolge-toolkit
        for cand in (
            self.isyco_git / "workspace" / "malbolge_toolkit",
            self.repo_root / "workspace" / "malbolge_toolkit",
        ):
            if (cand / "malbolge" / "cli.py").exists():
                self.backends["toolkit"] = {
                    "type": "python",
                    "module": "malbolge.cli",
                    "cwd": cand,
                }
                break

        # Autobolge
        for cand in (
            self.isyco_git / "Autobolge" / "zig" / "bolge",
            self.isyco_git / "Autobolge" / "zig" / "bolge.exe",
        ):
            if cand.exists():
                self.backends["autobolge"] = {
                    "type": "native",
                    "exe": cand,
                    "container": True,
                }
                break

        # Walbolge
        walbolge_dir = self.isyco_git / "Walbolge"
        if (walbolge_dir / "walbolge" / "cli.py").exists():
            self.backends["walbolge"] = {
                "type": "python",
                "module": "walbolge.cli",
                "cwd": walbolge_dir,
            }

    def list_backends(self) -> dict:
        return {k: {k2: v2 for k2, v2 in v.items() if k2 != "exe"} for k, v in self.backends.items()}


class UnifiedEvaluator:
    """Unified evaluator for Malbolge programs across multiple backends."""

    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            forensics_root = Path(__file__).resolve().parents[2]
            isyco_git = forensics_root.parent
            isyco_root = isyco_git.parent / "ISyCo"
            repo_root = isyco_root if isyco_root.exists() else forensics_root
        self.repo_root = Path(repo_root)
        self.registry = BackendRegistry(self.repo_root)

    def _run_subprocess(self, cmd: list, cwd: Optional[Path] = None,
                        stdin_data: str = "", timeout: int = 120) -> tuple:
        """Run subprocess and return (rc, stdout, stderr, elapsed_ms)."""
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=stdin_data.encode() if stdin_data else None,
                capture_output=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
            )
            elapsed = (time.perf_counter() - start) * 1000
            return proc.returncode, proc.stdout.decode('latin-1', errors='replace'), \
                   proc.stderr.decode('latin-1', errors='replace'), elapsed
        except subprocess.TimeoutExpired:
            elapsed = (time.perf_counter() - start) * 1000
            return -1, "", f"TIMEOUT after {timeout}s", elapsed
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return -1, "", str(e), elapsed

    def evaluate_bolge19(self, program_path: Path, stdin_data: str = "",
                         max_steps: Optional[int] = None) -> EvalResult:
        """Evaluate using bolge19 (native 3^19 VM)."""
        backend = self.registry.backends.get("bolge19")
        if not backend:
            return EvalResult(success=False, backend="bolge19",
                              stderr="bolge19 not found")

        cmd = [str(backend["exe"]), str(program_path)]
        rc, out, err, elapsed = self._run_subprocess(
            cmd, stdin_data=stdin_data, timeout=300)

        # Parse bolge19 output for steps/halt
        steps = 0
        halted = False
        halt_reason = ""
        for line in out.split('\n'):
            if "HALT steps=" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "steps=":
                        try:
                            steps = int(parts[i+1].rstrip(','))
                        except (ValueError, IndexError):
                            pass
                    if "halted=True" in line or "halted=True" in line.lower():
                        halted = True
                        halt_reason = "halt_opcode"

        return EvalResult(
            success=rc == 0,
            stdout=out,
            stderr=err,
            returncode=rc,
            steps=steps,
            halted=halted,
            halt_reason=halt_reason or ("max_steps" if "max_steps" in err.lower() else ""),
            elapsed_ms=0,
            backend="bolge19",
            raw_output=out,
        )

    def evaluate_oracle(self, program_text: str, max_steps: int = 1000000) -> EvalResult:
        """Evaluate using malbolge-oracle (Python reference)."""
        backend = self.registry.backends.get("oracle")
        if not backend:
            return EvalResult(success=False, backend="oracle",
                              stderr="oracle not found")

        # Use oracle directly via Python import (cleaner than temp files)
        oracle_dir = backend["dir"]
        if str(oracle_dir) not in sys.path:
            sys.path.insert(0, str(oracle_dir))

        try:
            from oracle import Oracle

            m = Oracle()
            m.load_ascii(program_text)
            r = m.run(max_steps=max_steps)

            return EvalResult(
                success=True,
                stdout=r.output,
                returncode=0,
                steps=r.steps,
                halted=r.halted,
                halt_reason=r.halt_reason,
                elapsed_ms=0,
                backend="oracle",
                raw_output=r.output or "",
                metadata={"steps": r.steps, "halted": r.halted, "halt_reason": r.halt_reason},
            )
        except Exception as e:
            return EvalResult(success=False, backend="oracle", stderr=str(e))

    def evaluate_autobolge(self, program_path: Path, input_data: bytes = b"",
                       max_steps: int = 5000000) -> EvalResult:
        """Evaluate using Autobolge BOLG1/BOLG2 container."""
        backend = self.registry.backends.get("autobolge")
        if not backend:
            return EvalResult(success=False, backend="autobolge",
                              stderr="autobolge not found")

        import struct
        import tempfile

        # Read program
        with open(program_path, "r", encoding="ascii") as f:
            text = f.read().strip()
        cells = [ord(c) for c in text]

        # Build BOLG1 container
        def make_bolg1(cells, input_bytes=b"", max_steps=5000000):
            b = b"BOLG1" + struct.pack("<Q", 1)
            b += struct.pack("<I", len(cells))
            for cval in cells:
                b += struct.pack("<I", cval)
            b += struct.pack("<I", 0)  # input_len
            b += struct.pack("<I", max_steps)
            return b

        # Write temp input file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            ib = f.name
            blob = b"BOLG1" + struct.pack("<Q", 1)
            blob += struct.pack("<I", len(cells))
            for cval in cells:
                blob += struct.pack("<I", cval)
            blob += struct.pack("<I", 0)  # input_len
            blob += struct.pack("<I", max_steps)
            f.write(blob)

        try:
            ob = tempfile.mktemp(suffix='.bin')
            rc, out, err, elapsed = self._run_subprocess(
                [backend["exe"], ib, "/dev/null"], timeout=180)  # Use /dev/null for output on Windows

            # Actually, Autobolge writes to the output file specified as second arg
            # Let's use a temp file for output
            with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
                ob = f.name

            rc, out, err, elapsed = self._run_subprocess(
                [backend["exe"], ib, ob], timeout=180)

            # Parse BOLG2 output
            output = b""
            steps = 0
            halted = False
            reason = 0

            if os.path.exists(ob) and os.path.getsize(ob) > 13:
                data = open(ob, "rb").read()
                if data[:5] == b"BOLG2":
                    pos = 5
                    (count,) = struct.unpack_from("<Q", data, 5)
                    pos = 13
                    for _ in range(1):  # Just first record
                        if pos + 4 > len(data): break
                        (olen,) = struct.unpack_from("<I", data, pos); pos += 4
                        if pos + olen > len(data): break
                        output = data[pos:pos+olen]; pos += olen
                        steps, term = struct.unpack_from("<Q B".replace(" ", ""), data, pos); pos += 9
                        fc, fa, fd = struct.unpack_from("<III", data, pos); pos += 12
                        return EvalResult(
                            success=True,
                            stdout=output.decode('latin-1', errors='replace'),
                            stderr="",
                            returncode=0,
                            steps=steps,
                            halted=bool(term),
                            halt_reason="halt_opcode" if term else "",
                            elapsed_ms=elapsed,
                            backend="autobolge",
                            metadata={"final_c": fc, "final_a": fa, "final_d": fd} if 'fc' in locals() else {},
                        )

            return EvalResult(
                success=rc == 0,
                stdout="",
                stderr="No valid output",
                returncode=rc,
                steps=0,
                halted=False,
                halt_reason="",
                elapsed_ms=elapsed,
                backend="autobolge",
            )
        finally:
            # Cleanup
            for f in [ib, ob]:
                try:
                    os.unlink(f)
                except:
                    pass

    def evaluate_all(self, program_path: Path, program_text: str = "") -> Dict[str, EvalResult]:
        """Evaluate program with all available backends."""
        results = {}

        # bolge19 (if 19-trit compatible)
        if Path(program_path).exists():
            results["bolge19"] = self.evaluate_bolge19(Path(program_path))

        # oracle
        if os.path.exists(program_path):
            with open(program_path, 'r', encoding='ascii') as f:
                text = f.read().strip()
            results["oracle"] = self.evaluate_oracle(text)

        # autobolge (if 3^10)
        if os.path.exists(program_path):
            with open(program_path, 'r', encoding='ascii') as f:
                text = f.read().strip()
            if len(text) <= 59049:  # classic 3^10
                results["autobolge"] = self.evaluate_autobolge(Path(program_path))

        return results


# Convenience imports
import tempfile
import os
import time
import sys
import struct


if __name__ == "__main__":
    # Quick test
    evaluator = UnifiedEvaluator()
    print("Available backends:", evaluator.registry.list_backends())