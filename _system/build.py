#!/usr/bin/env python3
"""
    python _system/build.py clients/icon

The only command the team runs. Validates, then renders.

If validation fails the PDF is still produced — so you can read it — but it is
named  proposal-NOT-FOR-SEND.pdf  and stamped across every page. A clean run
produces  proposal.pdf.  There is no flag to skip the check.
"""
import sys, subprocess, importlib.util
from pathlib import Path

SYS = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def main():
    if len(sys.argv) < 2:
        print("usage: build.py <client-dir>"); sys.exit(2)
    client = Path(sys.argv[1])
    prop = client / "03-proposal" / "proposal.md"
    if not prop.exists():
        print(f"no {prop}"); sys.exit(2)

    v = load("validate", SYS / "validate.py")
    issues, warns, notes = v.check(client)

    print(f"\n── {client.name} ─────────────────────────────")
    for n in notes: print(f"  note  {n}")
    for w in warns: print(f"  WARN  {w}")
    for i in issues: print(f"  FAIL  {i}")

    gen = load("vm", SYS / "visionary_media.py")
    out = client / "03-proposal" / ("proposal-NOT-FOR-SEND.pdf" if issues else "proposal.pdf")
    gen.OUTPUT_PATH = str(out)

    # rewrite front-matter output so the PDF lands beside the markdown
    raw = prop.read_text()
    body = raw.split("---", 2)[2] if raw.lstrip().startswith("---") else raw
    fm = {}
    if raw.lstrip().startswith("---"):
        for line in raw.split("---", 2)[1].strip().splitlines():
            if ":" in line:
                k, val = line.split(":", 1); fm[k.strip()] = val.strip()
    fm["output"] = str(out)
    tmp = prop.parent / "_build.md"
    tmp.write_text("---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n" + body)

    gen.render(str(tmp), draft=bool(issues))
    tmp.unlink()

    print()
    if issues:
        print(f"BLOCKED — {len(issues)} issue(s). PDF stamped NOT FOR SEND.")
        sys.exit(1)
    print(f"CLEAN — {len(warns)} warning(s). {out}")


if __name__ == "__main__":
    main()
