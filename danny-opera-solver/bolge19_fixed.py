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
    # bolge19 prints debug info to stdout: "bolge19: imagen=... HALT steps=X"
    # We need to extract the HALT line and steps from the mixed output
    steps = 0
    halted = False
    halt_reason = ""
    program_output = ""
    
    for line in out.split('\n'):
        line = line.strip()
        if "HALT steps=" in line:
            # Extract steps from "bolge19: HALT steps=39"
            parts = line.split()
            for i, p in enumerate(parts):
                if p == "steps=":
                    try:
                        steps = int(parts[i+1].rstrip(','))
                    except (ValueError, IndexError):
                        pass
                    halted = True
                    halt_reason = "halt_opcode"
        elif line and not line.startswith("bolge19:"):
            # Non-debug output line - this is actual program output
            program_output += line + "\n"

    # If no explicit output captured, check if there's any non-debug output
    if not program_output and out:
        # Filter out debug lines
        output_lines = [l for l in out.split('\n') if l.strip() and not l.strip().startswith("bolge19:")]
        if output_lines:
            program_output = "\n".join(output_lines)

    return EvalResult(
        success=rc == 0,
        stdout=program_output or out,
        stderr=err,
        returncode=rc,
        steps=steps,
        halted=halted,
        halt_reason=halt_reason or ("max_steps" if "max_steps" in err.lower() else ""),
        elapsed_ms=elapsed,
        backend="bolge19",
        raw_output=out,
        metadata={"steps": steps, "halted": halted, "halt_reason": halt_reason},
    )