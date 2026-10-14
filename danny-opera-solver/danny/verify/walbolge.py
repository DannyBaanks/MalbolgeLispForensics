#!/usr/bin/env python3
"""
Walbolge Verification — Roundtrip verification using Walbolge decompiler.

Walbolge is the inverse of the Malbolge Translator: it takes a Malbolge
program and reconstructs the original text + structure.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import subprocess
import json
import os
import tempfile


@dataclass
class WalbolgeResult:
    """Result of Walbolge decompilation."""
    success: bool
    roundtrip_flags: Dict[str, bool]  # processed, original, words, opcodes
    reconstructed_text: str = ""
    words_found: int = 0
    opcodes_count: int = 0
    bootstrap_detected: bool = False
    segments: List[Dict] = None
    raw_output: str = ""
    stderr: str = ""
    returncode: int = -1

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def roundtrip_perfect(self) -> bool:
        """All 4 roundtrip flags True."""
        return all(self.roundtrip_flags.values())

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'roundtrip_flags': self.roundtrip_flags,
            'roundtrip_perfect': self.roundtrip_perfect,
            'reconstructed_text': self.reconstructed_text,
            'words_found': self.words_found,
            'opcodes_count': self.opcodes_count,
            'bootstrap_detected': self.bootstrap_detected,
            'segments': self.segments or [],
            'stderr': self.stderr,
            'returncode': self.returncode,
        }


class WalbolgeVerifier:
    """
    Walbolge verification wrapper.

    Walbolge is the inverse of the Malbolge Translator:
    - Input: .mal or .op file (Malbolge program)
    - Options: --manifest, --words-dir, --max-steps, --classic
    - Output: JSON with roundtrip flags, reconstructed text, segments
    """

    def __init__(self, walbolge_cwd: str = None, walbolge_exe: str = None):
        self.cwd = walbolge_cwd or r"C:\Development\ISyCo Git\Walbolge"
        self.exe = walbolge_exe  # Not used directly; uses py -m walbolge.cli

    def _run_walbolge(self, mal_file: str, manifest: str = None,
                      words_dir: str = None, max_steps: int = 500000,
                      classic: bool = False, json_output: str = None) -> Dict:
        """Run walbolge CLI and parse output."""
        cmd = [
            "py", "-m", "walbolge.cli",
            mal_file,
        ]
        if manifest:
            cmd.extend(["--manifest", manifest])
        if words_dir:
            cmd.extend(["--words-dir", words_dir])
        if max_steps:
            cmd.extend(["--max-steps", str(max_steps)])
        if classic:
            cmd.append("--classic")
        if json_output:
            cmd.extend(["--json", json_output])

        env = os.environ.copy()
        # Ensure we can find the walbolge package
        env["PYTHONPATH"] = os.path.dirname(self.cwd) + os.pathsep + os.environ.get("PYTHONPATH", "")

        proc = subprocess.run(
            cmd,
            cwd=self.cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    def verify_roundtrip(self, mal_file: str, manifest: str = None,
                         words_dir: str = None, max_steps: int = 500000) -> 'WalbolgeResult':
        """
        Run Walbolge roundtrip verification.

        Returns WalbolgeResult with roundtrip flags and reconstructed text.
        """
        result = self._run_walbolge(
            mal_file=mal_file,
            manifest=manifest,
            words_dir=words_dir,
            max_steps=500000,
        )

        # Parse output
        stdout = result["stdout"]
        stderr = result["stderr"]
        rc = result["returncode"]

        # Parse roundtrip flags from output
        roundtrip_flags = {
            "processed": False,
            "original": False,
            "words": False,
            "opcodes": False,
        }
        reconstructed_text = ""
        words_found = 0
        bootstrap_detected = False
        segments = []

        # Parse output for roundtrip flags
        for line in result["stdout"].split('\n'):
            if "Roundtrip" in line:
                for flag in ["processed", "original", "words", "opcodes"]:
                    if f"{flag}=" in line.lower():
                        val = line.split(f"{flag}=")[1].split()[0]
                        roundtrip_flags[flag] = val == "True"
            if "TEXT RECONSTRUIDO" in line or "RECONSTRUCTED" in line:
                # Next lines might contain the text
                pass
            if "words:" in line.lower():
                try:
                    words_found = int(line.split(":")[-1].strip())
                except:
                    pass

        # Try to extract reconstructed text
        lines = result["stdout"].split('\n')
        in_text = False
        for line in lines:
            if "TEXTO RECONSTRUIDO" in line or "RECONSTRUCTED" in line:
                in_text = True
                continue
            if in_text and line.strip():
                reconstructed_text += line + "\n"
            elif in_text and not line.strip():
                in_text = False

        success = result["returncode"] == 0

        return {
            "success": success,
            "roundtrip_flags": {
                "processed": result.get("processed", False),
                "original": result.get("original", False),
                "words": result.get("words", False),
                "opcodes": result.get("opcodes", False),
            },
            "reconstructed_text": reconstructed_text.strip(),
            "words_found": 0,
            "bootstrap_detected": False,
            "segments": [],
            "raw_output": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
        }

    def verify_translator_roundtrip(self, mal_file: str, manifest: str,
                                    words_dir: str) -> Dict:
        """
        Full Translator -> Walbolge roundtrip test.

        1. Run Translator-generated .mal through Walbolge
        2. Verify all 4 roundtrip flags are True
        3. Verify reconstructed text matches manifest original
        """
        result = self.verify_roundtrip(
            mal_file=mal_file,
            manifest=manifest,
            words_dir=words_dir,
        )

        # Read original text from manifest
        import json
        with open(manifest, 'r') as f:
            manifest_data = json.load(manifest)
        original_text = manifest_data.get("original", "")

        roundtrip_perfect = all(result["roundtrip_flags"].values())
        text_match = result.get("reconstructed_text", "").strip() == original_text.strip()

        return {
            "roundtrip_perfect": roundtrip_perfect,
            "text_match": text_match,
            "original_length": len(original_text),
            "reconstructed_length": len(result.get("reconstructed_text", "")),
            "flags": result["roundtrip_flags"],
            "words_found": result.get("words_found", 0),
            "bootstrap_detected": result.get("bootstrap_detected", False),
            "raw_output": result.get("stdout", ""),
        }

    def verify_specimen(self, mal_file: str, manifest: str = None,
                        words_dir: str = None) -> Dict:
        """
        Verify a specimen with Walbolge.

        Returns comprehensive verification result.
        """
        if manifest and os.path.exists(manifest):
            return self.verify_translator_roundtrip(mal_file, manifest, None)
        else:
            return self.verify_roundtrip(mal_file)

    def test_specimen(self, mal_file: str) -> Dict:
        """Quick test of a specimen with the reference interpreter."""
        return self.verify_roundtrip(mal_file)


if __name__ == "__main__":
    # Quick test
    verifier = WalbolgeVerifier()
    print("WalbolgeVerifier initialized")
    print(f"CWD: {verifier.cwd}")