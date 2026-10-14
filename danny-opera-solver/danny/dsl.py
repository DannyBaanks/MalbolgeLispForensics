#!/usr/bin/env python3
"""
DannyScript — DSL for specifying Malbolge search objectives.

Grammar:
    program := statement*
    statement := target_spec | constraint | objective | config
    target_spec := "target" string_literal
    constraint := "constraint" identifier "=" value
    objective := "minimize" | "maximize" identifier
    config := "config" identifier "=" value

Example:
    target "Hello World!"
    constraint max_steps = 1000000
    constraint memory_limit = 59049
    objective minimize steps
    objective minimize size
    config backend = "bolge19"
    config seed = 42
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class DannySpec:
    """Parsed DannyScript specification."""
    target: str = ""
    constraints: dict = field(default_factory=dict)
    objectives: list = field(default_factory=list)  # (direction, metric)
    config: dict = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate the spec, return list of errors."""
        errors = []
        if not self.target:
            errors.append("Missing target specification")
        if "backend" not in self.config:
            self.config["backend"] = "bolge19"
        if "seed" not in self.config:
            self.config["seed"] = 42
        if "max_steps" not in self.constraints:
            self.constraints["max_steps"] = 1000000
        return errors


class DannyScriptParser:
    """Parser for DannyScript DSL."""

    # Regex patterns
    TARGET_RE = re.compile(r'^target\s+(.+)$', re.IGNORECASE)
    CONSTRAINT_RE = re.compile(r'^constraint\s+(\w+)\s*=\s*(.+)$', re.IGNORECASE)
    OBJECTIVE_RE = re.compile(r'^(minimize|maximize)\s+(\w+)$', re.IGNORECASE)
    CONFIG_RE = re.compile(r'^config\s+(\w+)\s*=\s*(.+)$', re.IGNORECASE)
    COMMENT_RE = re.compile(r'^\s*#')

    def __init__(self):
        self.spec = DannySpec()

    def parse(self, source: str) -> DannySpec:
        """Parse DannyScript source into a DannySpec."""
        self.spec = DannySpec()
        lines = source.strip().split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or self.COMMENT_RE.match(line):
                continue

            # Try each pattern in order
            if m := self.TARGET_RE.match(line):
                # Strip quotes if present
                target = m.group(1).strip()
                if (target.startswith('"') and target.endswith('"')) or \
                   (target.startswith("'") and target.endswith("'")):
                    target = target[1:-1]
                self.spec.target = target
            elif m := self.CONSTRAINT_RE.match(line):
                key = m.group(1).lower()
                val = m.group(2).strip()
                # Try to parse as number
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except ValueError:
                    # Keep as string, strip quotes
                    if (val.startswith('"') and val.endswith('"')) or \
                       (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                self.spec.constraints[key] = val
            elif m := self.OBJECTIVE_RE.match(line):
                direction = m.group(1).lower()
                metric = m.group(2).lower()
                self.spec.objectives.append((direction, metric))
            elif m := self.CONFIG_RE.match(line):
                key = m.group(1).lower()
                val = m.group(2).strip()
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except ValueError:
                    if (val.startswith('"') and val.endswith('"')) or \
                       (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                self.spec.config[key] = val
            else:
                raise ValueError(f"Line {line_num}: Unrecognized syntax: {line}")

        errors = self.spec.validate()
        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))

        return self.spec

    @classmethod
    def parse_file(cls, path: Path) -> DannySpec:
        """Parse a DannyScript file."""
        source = path.read_text(encoding='utf-8')
        return cls().parse(source)


def parse_dannyscript(source: str) -> DannySpec:
    """Convenience function to parse DannyScript from string."""
    return DannyScriptParser().parse(source)


def parse_dannyscript_file(path: Path) -> DannySpec:
    """Convenience function to parse DannyScript from file."""
    return DannyScriptParser.parse_file(path)


if __name__ == "__main__":
    # Quick test
    test_script = '''
target "Hello World!"
constraint max_steps = 1000000
constraint memory_limit = 59049
objective minimize steps
objective minimize size
config backend = "bolge19"
config seed = 42
'''
    spec = parse_dannyscript(test_script)
    print(f"Target: {spec.target}")
    print(f"Constraints: {spec.constraints}")
    print(f"Objectives: {spec.objectives}")
    print(f"Config: {spec.config}")
    print("Parse OK!")