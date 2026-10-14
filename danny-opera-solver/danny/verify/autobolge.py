#!/usr/bin/env python3
"""
Autobolge Verification — BOLG1/BOLG2 container validation.

Autobolge uses a container format for Malbolge programs:
- BOLG1: input container (program + input + max_steps)
- BOLG2: output container (output + steps + final state)
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import struct
import subprocess
import os
import hashlib


@dataclass
class AutobolgeResult:
    """Result of Autobolge execution."""
    success: bool
    output: bytes = b""
    steps: int = 0
    halted: bool = False
    reason: int = 0  # 0=running, 1=terminated
    final_c: int = 0
    final_a: int = 0
    final_d: int = 0
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1

    @property
    def output_text(self) -> str:
        return self.output.decode('latin-1', errors='replace')


@dataclass
class BOLG1Record:
    """Single BOLG1 record (program + input + max_steps)."""
    program: List[int]  # u32 cells
    input_bytes: bytes = b""
    max_steps: int = 5_000_000

    def to_bytes(self) -> bytes:
        """Serialize to BOLG1 format."""
        # BOLG1: "BOLG1" + u64 count + records
        # Record: u32 prog_len + prog_len*u32 + u32 input_len + input_bytes + u32 max_steps
        b = b"BOLG1" + struct.pack("<Q", 1)
        b += struct.pack("<I", len(self.program))
        for cell in self.program:
            b += struct.pack("<I", cell & 0xFFFFFFFF)
        b += struct.pack("<I", len(self.input_bytes))
        b += self.input_bytes
        b += struct.pack("<I", self.max_steps)
        return b


@dataclass
class BOLG2Result:
    """Parsed BOLG2 result."""
    count: int
    results: List[Dict]

    @classmethod
    def parse(cls, data: bytes) -> 'BOLG2Result':
        if len(data) < 13 or data[:5] != b"BOLG2":
            raise ValueError("Invalid BOLG2 header")
        pos = 5
        (count,) = struct.unpack_from("<Q", data, pos); pos += 8
        results = []
        pos_offset = pos
        for _ in range(count):
            if pos + 4 > len(data): break
            (olen,) = struct.unpack_from("<I", data, pos); pos += 4
            if pos + olen > len(data): break
            output = data[pos:pos+olen]; pos += olen
            if pos + 10 > len(data): break
            (steps, term) = struct.unpack_from("<Q B".replace(" ", ""), data, pos); pos += 9
            if pos + 12 > len(data): break
            fc, fa, fd = struct.unpack_from("<III", data, pos); pos += 12
            results.append({
                "output": output,
                "steps": steps,
                "terminated": bool(term),
                "reason": term,
                "final_c": fc,
                "final_a": fa,
                "final_d": fd,
            })
        return cls(count=count, results=results)


class AutobolgeVerifier:
    """
    Autobolge BOLG1/BOLG2 container verification.

    Autobolge uses a container format:
    - Input: BOLG1 (magic + count + records)
    - Record: prog_len + prog_len*u32 + input_len + input_bytes + max_steps
    - Output: BOLG2 with results per record
    """

    def __init__(self, autobolge_exe: str = None):
        self.exe = autobolge_exe or r"C:\Development\ISyCo Git\Autobolge\zig\bolge.exe"

    def make_bolg1(self, program_text: str, input_text: str = "",
                   max_steps: int = 5_000_000) -> bytes:
        """Create BOLG1 container from ASCII Malbolge program."""
        cells = [ord(c) for c in program_text.strip()]
        record = {
            "program": [ord(c) for c in program_text.strip()],
            "input_bytes": b"",
            "max_steps": 5_000_000,
        }
        b = b"BOLG1" + struct.pack("<Q", 1)
        b += struct.pack("<I", len(program_text.strip()))
        for ch in program_text.strip():
            b += struct.pack("<I", ord(c))
        b += struct.pack("<I", 0)  # input_len
        b += struct.pack("<I", 5_000_000)  # max_steps
        return b

    def run(self, program_text: str, input_text: str = "",
            max_steps: int = 5_000_000, timeout: int = 180) -> Dict:
        """
        Run program through Autobolge BOLG1/BOLG2.

        Returns parsed result with output, steps, halted status.
        """
        # Create input BOLG1
        ib = os.path.join(os.environ.get("TEMP", "."), "autobolge_in.bin")
        ob = os.path.join(os.environ.get("TEMP", "."), "autobolge_out.bin")

        cells = [ord(c) for c in program_text.strip()]
        blob = b"BOLG1" + struct.pack("<Q", 1)
        blob += struct.pack("<I", len(cells))
        for cval in cells:
            blob += struct.pack("<I", cval)
        blob += struct.pack("<I", 0)  # input_len
        blob += struct.pack("<I", 5_000_000)  # max_steps

        with open(ib, "wb") as f:
            f.write(blob)

        # Run bolge.exe
        exe = r"C:\Development\ISyCo Git\Autobolge\zig\bolge.exe"
        if not os.path.exists(exe):
            return {"success": False, "error": "bolge.exe not found"}

        ob_path = os.path.join(os.environ.get("TEMP", "."), "autobolge_out.bin")
        proc = subprocess.run(
            [exe, "C:\\Users\\progr\\AppData\\Local\\Temp\\autobolge_in.bin", ob_path],
            capture_output=True,
            timeout=180,
        )

        # Parse output
        if not os.path.exists(ob):
            return {"success": False, "error": "No output file"}

        with open("C:\\Users\\progr\\AppData\\Local\\Temp\\autobolge_out.bin", "rb") as f:
            data = f.read()

        if len(data) < 13 or data[:5] != b"BOLG2":
            return {"success": False, "error": "Invalid BOLG2 output"}

        # Parse BOLG2
        pos = 5
        (count,) = struct.unpack_from("<Q", data, pos); pos = 13
        results = []
        for _ in range(count):
            if pos + 4 > len(data): break
            (olen,) = struct.unpack_from("<I", data, pos); pos += 4
            if pos + olen > len(data): break
            output = data[pos:pos+olen]; pos += olen
            if pos + 10 > len(data): break
            (steps, term) = struct.unpack_from("<Q B".replace(" ", ""), data, pos); pos += 9
            if pos + 12 > len(data): break
            fc, fa, fd = struct.unpack_from("<III", data, pos); pos += 12
            return {
                "success": True,
                "output": output.decode('latin-1', errors='replace'),
                "steps": steps,
                "halted": bool(term),
                "reason": term,
                "final_c": fc,
                "final_a": fa,
                "final_d": fd,
            }

        return {"success": False, "error": "No results parsed"}


def run_autobolge(program_text: str, input_text: str = "",
                  max_steps: int = 5_000_000) -> Dict:
    """Convenience function to run Autobolge on a program."""
    verifier = AutobolgeVerifier()
    return verifier.run(program_text, "", max_steps)


if __name__ == "__main__":
    # Quick test with hello world
    hello = '(=<`#9]~6ZY32Vx/4Rs+0No-&Jk)"Fh}|Bcy?`=*z]Kw%oG4UUS0/@-ejc(\'8dc'
    result = run_autobolge(hello)
    print(f"Result: {result}")