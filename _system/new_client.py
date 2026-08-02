#!/usr/bin/env python3
"""
VISIONARY MEDIA — new client scaffold
=====================================

    python _system/new_client.py "Icon"
    python _system/new_client.py "Icon" --url https://icon.com

Creates the folder tree and drops the blank templates in. Nothing else — no
audit, no record, no numbers. It is deliberately dumb so that the only things
in a client folder are things a person or `run_audit.py` put there.

Refuses to overwrite. Re-running on an existing client fills in only what is
missing and reports what it left alone.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SYS_DIR = Path(__file__).resolve().parent
ROOT = SYS_DIR.parent
TPL = SYS_DIR / "templates"

DIRS = ["01-audit/images", "02-call", "03-proposal"]
COPIES = [
    (TPL / "call-notes.md", "02-call/call-notes.md"),
    (TPL / "proposal.md", "03-proposal/proposal.md"),
]


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a client folder tree")
    ap.add_argument("name", help='Client name, e.g. "Icon"')
    ap.add_argument("--url", default="", help="Client site, used in the next-step hint")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args()

    slug = slugify(a.name)
    if not slug:
        print("client name must contain at least one letter or digit")
        return 2
    cdir = Path(a.root) / "clients" / slug

    missing = [p for p, _ in COPIES if not p.exists()]
    if missing:
        print("missing template(s) — cannot scaffold:")
        for p in missing:
            print(f"  {p}")
        return 2

    created, skipped = [], []
    for d in DIRS:
        p = cdir / d
        (created if not p.exists() else skipped).append(str(p.relative_to(a.root)))
        p.mkdir(parents=True, exist_ok=True)

    for src, rel in COPIES:
        dst = cdir / rel
        if dst.exists():
            skipped.append(str(dst.relative_to(a.root)))
            continue
        text = src.read_text(encoding="utf-8").replace("CLIENT NAME", a.name)
        dst.write_text(text, encoding="utf-8")
        created.append(str(dst.relative_to(a.root)))

    print(f"── {a.name} → clients/{slug} ────────────────")
    for c in created:
        print(f"  created  {c}")
    for s in skipped:
        print(f"  kept     {s}  (already there — not touched)")

    url = a.url or f"https://{slug}.com"
    print(f"""
Next:

  1. python _system/run_audit.py {url} \\
         --name "{a.name}" --category "<how THEY describe it> for <audience>" \\
         --competitors "<who they name themselves>" --operator "<you>"

     Writes prompt-set.json, semrush.json, interpretation.json and
     CAPTURE-CHECKLIST.md into clients/{slug}/01-audit/. Work the checklist,
     then re-run the same command with --reviewed to write the record.

  2. Run Call 1 against _system/templates/call-sop.md.
     Fill clients/{slug}/02-call/call-notes.md as you go — digits, not words.

  3. Draft clients/{slug}/03-proposal/proposal.md, then:
     python _system/build.py clients/{slug}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
