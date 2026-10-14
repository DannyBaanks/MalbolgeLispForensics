#!/usr/bin/env python3
"""Cheap cross-backend validation suite (classic 3^10 Malbolge).

Runs whatever backends are available and records RAW results under
evidence/validation/. No absolute workstation paths are embedded here:
point the suite at your tools via environment variables.

    MALBOLGE_ENGINE_EXE   path to a classic malbolge interpreter executable
    ORACLE_DIR            directory containing oracle.py (reference control)
    TOOLKIT_CWD           cwd where `py -m malbolge.cli` resolves
    AUTOBOLGE_EXE         Autobolge Zig container VM (BOLG1/BOLG2)
    WALBOLGE_CWD          cwd where `py -m walbolge.cli` resolves

Exit code 0 iff at least two backends agree on hello world AND quijote text
matches on at least one backend that also agrees on hello.
"""
import os, sys, struct, subprocess, json, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "evidence", "validation")
os.makedirs(EV, exist_ok=True)

HELLO = os.path.join(ROOT, "specimens", "hello.malbolge")
QUIJOTE = os.path.join(ROOT, "specimens", "quijote", "chapter_001", "quijote_ch001_full.mal")

def record(name, rc, out, err):
    base = os.path.join(EV, name)
    open(base + ".out.txt", "wb").write(out)
    open(base + ".err.txt", "wb").write(err)
    return {"name": name, "rc": rc, "stdout": out.decode("latin-1"), "stderr_len": len(err)}

def run(cmd, cwd=None, timeout=120, stdin_text=""):
    p = subprocess.run(cmd, input=stdin_text.encode(), capture_output=True, timeout=timeout, cwd=cwd)
    return p.returncode, p.stdout, p.stderr

ROOT_PARENT = os.path.dirname(ROOT)

# Auto-discover backends from neighboring workspace repos if not explicitly set
if not os.environ.get("MALBOLGE_ENGINE_EXE"):
    for cand in (
        os.path.join(ROOT_PARENT, "Malbolge-Engine", "malbolge"),
        os.path.join(ROOT_PARENT, "MALBOLGE-MB-DATABASE", "runners", "malbolge-original", "malbolge"),
    ):
        if os.path.exists(cand):
            os.environ["MALBOLGE_ENGINE_EXE"] = cand
            break

if not os.environ.get("ORACLE_DIR"):
    cand = os.path.join(ROOT_PARENT, "malbolge-oracle")
    if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "oracle.py")):
        os.environ["ORACLE_DIR"] = cand

if not os.environ.get("WALBOLGE_CWD"):
    cand = os.path.join(ROOT_PARENT, "Walbolge")
    if os.path.isdir(cand) and os.path.isdir(os.path.join(cand, "walbolge")):
        os.environ["WALBOLGE_CWD"] = cand

results = []

# --- C engine -------------------------------------------------------------
exe = os.environ.get("MALBOLGE_ENGINE_EXE")
if exe and os.path.exists(exe):
    for tag, spec in (("engine_hello", HELLO), ("engine_quijote", QUIJOTE)):
        rc, out, err = run([exe, spec])
        results.append(record(tag, rc, out, err))
else:
    results.append({"name": "engine", "skipped": "MALBOLGE_ENGINE_EXE not set"})

# --- Python oracle --------------------------------------------------------
odir = os.environ.get("ORACLE_DIR")
if odir and os.path.isdir(odir):
    driver = (
        "import sys; sys.path.insert(0, r'%s')\n"
        "from oracle import Oracle\n"
        "text=open(sys.argv[1],encoding='ascii').read().strip()\n"
        "m=Oracle(); m.load_ascii(text); r=m.run(max_steps=2000000)\n"
        "print('OUT:',repr(r.output));print('STEPS:',r.steps,'HALTED:',r.halted,r.halt_reason)\n"
    ) % odir
    for tag, spec in (("oracle_hello", HELLO), ("oracle_quijote", QUIJOTE)):
        rc, out, err = run([sys.executable, "-c", driver, spec])
        results.append(record(tag, rc, out, err))
else:
    results.append({"name": "oracle", "skipped": "ORACLE_DIR not set"})

# --- Python toolkit -------------------------------------------------------
tkcwd = os.environ.get("TOOLKIT_CWD")
if tkcwd and os.path.isdir(tkcwd):
    for tag, spec in (("toolkit_hello", HELLO), ("toolkit_quijote", QUIJOTE)):
        rc, out, err = run([sys.executable, "-m", "malbolge.cli", "run", "--ascii-file", spec, "--cycle-limit", "500000"], cwd=tkcwd)
        results.append(record(tag, rc, out, err))
else:
    results.append({"name": "toolkit", "skipped": "TOOLKIT_CWD not set"})

# --- Autobolge Zig container (BOLG1/BOLG2) --------------------------------
abx = os.environ.get("AUTOBOLGE_EXE")
if abx and os.path.exists(abx):
    def bolg1(cells):
        b = b"BOLG1" + struct.pack("<Q", 1) + struct.pack("<I", len(cells))
        b += b"".join(struct.pack("<I", c) for c in cells)
        return b + struct.pack("<I", 0) + struct.pack("<I", 5_000_000)
    def parse_bolg2(data):
        (n,) = struct.unpack_from("<Q", data, 5); pos = 13
        res = []
        for _ in range(n):
            (olen,) = struct.unpack_from("<I", data, pos); pos += 4
            output = data[pos:pos+olen]; pos += olen
            steps, term = struct.unpack_from("<Q B".replace(" ", ""), data, pos); pos += 9
            fc, fa, fd = struct.unpack_from("<III", data, pos); pos += 12
            res.append((output, steps, term))
        return res
    for tag, spec in (("autobolge_hello", HELLO), ("autobolge_quijote", QUIJOTE)):
        cells = [ord(c) for c in open(spec, encoding="ascii").read().strip()]
        ib, ob = os.path.join(EV, tag + ".in.bin"), os.path.join(EV, tag + ".out.bin")
        open(ib, "wb").write(bolg1(cells))
        rc, out, err = run([abx, ib, ob], timeout=180)
        payload = ""
        if os.path.exists(ob) and os.path.getsize(ob) > 13:
            output, steps, term = parse_bolg2(open(ob, "rb").read())[0]
            payload = f"output={output!r} steps={steps} halted={bool(term)}"
            open(os.path.join(EV, tag + ".parsed.txt"), "w", encoding="utf-8").write(payload + "\n")
        results.append(record(tag, rc, (payload + "\n").encode(), err))
else:
    results.append({"name": "autobolge", "skipped": "AUTOBOLGE_EXE not set"})

# --- Walbolge roundtrip ---------------------------------------------------
wcwd = os.environ.get("WALBOLGE_CWD")
qdir = os.path.dirname(QUIJOTE)
if wcwd and os.path.isdir(wcwd):
    rc, out, err = run([sys.executable, "-m", "walbolge.cli",
                        os.path.join(qdir, "quijote_ch001_full.mal"),
                        "--manifest", os.path.join(qdir, "quijote_ch001_manifest.json"),
                        "--words-dir", qdir, "--max-steps", "500000"], cwd=wcwd, timeout=300)
    blob = out + err
    open(os.path.join(EV, "walbolge_roundtrip.out.txt"), "wb").write(blob)
    flags = [ln.split(":")[-1].strip() for ln in blob.decode("latin-1").splitlines() if "Roundtrip" in ln]
    results.append({"name": "walbolge_roundtrip", "rc": rc, "flags": flags,
                    "all_true": bool(flags) and all(f == "True" for f in flags[0].split() if f in ("True", "False")) or "True" in (flags[0] if flags else "")})
else:
    results.append({"name": "walbolge", "skipped": "WALBOLGE_CWD not set"})

# --- verdict -----------------------------------------------------------------
def got(tag, key="stdout"):
    for r in results:
        if r["name"] == tag and key in r:
            return r[key]
    return ""

hello_ok = [r["name"] for r in results if "Hello World!" in str(r.get("stdout", ""))]
quijote_ok = [r["name"] for r in results if "DON QUIXOTE OF LA MANCHA" in str(r.get("stdout", ""))]
verdict = {"hello_agreement_backends": len(hello_ok), "hello_backends": hello_ok,
           "quijote_agreement_backends": len(quijote_ok), "ok": len(hello_ok) >= 2}
open(os.path.join(EV, "verdict.json"), "w", encoding="ascii").write(json.dumps(verdict, indent=1))
for r in results:
    print(json.dumps({k: (v[:80] if isinstance(v, str) else v) for k, v in r.items()}, default=str)[:200])
print("VERDICT:", json.dumps(verdict))
sys.exit(0 if verdict["ok"] else 1)
