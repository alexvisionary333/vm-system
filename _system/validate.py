#!/usr/bin/env python3
"""
VISIONARY MEDIA — pre-send validator
====================================

    python _system/validate.py clients/icon

Four checks, in order of how much damage they prevent:

  1. SCHEMA      audit-record.json validates, required fields present
  2. PROVENANCE  every metric carries a source and a date
  3. NUMBERS     every number in proposal.md traces back to ONE of three
                 sanctioned sources: the audit record, the call notes, or
                 the case study library.  Unsourced numbers are the way
                 invented figures reach a client.
  4. PLACEHOLDER no REPLACE / TODO / [BRACKET] / $X left in the draft

Exit 0 = clean.  Exit 1 = blocking issues.  Nothing is auto-fixed.
"""
import json, re, sys, subprocess
from pathlib import Path
from datetime import date, datetime

STALE_DAYS = 21
NUM_RE = re.compile(r'(?<![\w/.-])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w-])\s*(%|K\b|M\b)?')
STRIP_RE = [re.compile(r'!?\[[^\]]*\]\([^)]*\)'),      # links + image paths
            re.compile(r'`[^`]*`'),                      # inline code
            re.compile(r'<[^>]+>'),                      # html tags/attrs
            re.compile(r'^---.*?^---', re.S | re.M),      # front matter
            re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),         # ISO dates
            re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{0,4}', re.I)]
# numbers that are structural, not claims
IGNORE = {"1","2","3","4","5","6","7","8","9","10","11","12","0","90","30","50","100","2026","2025","24","48","72"}
PLACEHOLDERS = [r'REPLACE', r'\bTODO\b', r'\$X\b', r'\$Y\b', r'\$Z\b',
                r'\[[A-Z][A-Z _/-]{2,}\]', r'\bXX\b', r'\bN months\b']


def norm(tok, suffix):
    v = float(tok.replace(",", ""))
    if suffix and suffix.upper() == "K": v *= 1_000
    if suffix and suffix.upper() == "M": v *= 1_000_000
    return round(v, 4)


def numbers_in(text):
    for r in STRIP_RE:
        text = r.sub(" ", text)
    out = {}
    for m in NUM_RE.finditer(text):
        raw = m.group(0).strip()
        if m.group(1) in IGNORE and not m.group(2):
            continue
        key = norm(m.group(1), m.group(2))
        out.setdefault(key, set()).add(raw)
        if m.group(2):                      # "8.6K" may be stored as 8600 or 8.6
            out.setdefault(norm(m.group(1), None), set()).add(raw)
    return out


def walk_numbers(obj, acc):
    if isinstance(obj, dict):
        for v in obj.values(): walk_numbers(v, acc)
    elif isinstance(obj, list):
        for v in obj: walk_numbers(v, acc)
    elif isinstance(obj, (int, float)):
        acc.add(round(float(obj), 4))
    elif isinstance(obj, str):
        for k in numbers_in(obj): acc.add(k)
    return acc


def check(client_dir):
    d = Path(client_dir)
    issues, warns, notes = [], [], []

    rec_p  = d / "01-audit" / "audit-record.json"
    call_p = d / "02-call"  / "call-notes.md"
    prop_p = d / "03-proposal" / "proposal.md"
    schema_p = Path(__file__).parent / "audit-record.schema.json"

    # ---- 1. SCHEMA ----------------------------------------------------
    record = None
    if not rec_p.exists():
        issues.append(f"missing {rec_p} — proposal cannot be sourced")
    else:
        record = json.loads(rec_p.read_text())
        try:
            import jsonschema
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                   "jsonschema", "--break-system-packages", "-q"])
            import jsonschema
        schema = json.loads(schema_p.read_text())
        for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(record),
                        key=lambda e: list(e.path)):
            issues.append(f"schema: {'/'.join(map(str, e.path)) or '(root)'} — {e.message}")

        if not record.get("run", {}).get("prompt_set_reviewed_by_human"):
            warns.append("run.prompt_set_reviewed_by_human is false — prompt set unreviewed")

        rd = record.get("run", {}).get("date")
        if rd:
            age = (date.today() - datetime.fromisoformat(rd).date()).days
            if age > STALE_DAYS:
                warns.append(f"audit is {age} days old (>{STALE_DAYS}) — AI answers move; re-run before sending")

        # ---- 2. PROVENANCE --------------------------------------------
        pm = record.get("platform_metrics", {})
        if pm and not pm.get("source"):
            issues.append("platform_metrics.source missing — metrics have no provenance")
        for i, r in enumerate(record.get("prompt_runs", [])):
            if not r.get("date"):
                issues.append(f"prompt_runs[{i}] has no date — not reproducible")
            if r.get("client_named") is False and not r.get("screenshot"):
                warns.append(f"prompt_runs[{i}] ('{r.get('prompt','?')[:38]}') claims absence with no screenshot")
        for u in record.get("unknowns", []):
            notes.append(f"unknown carried from audit: {u}")

    # ---- 3. NUMBERS ---------------------------------------------------
    if not prop_p.exists():
        issues.append(f"missing {prop_p}")
    else:
        prop = prop_p.read_text()
        sourced = set()
        if record: walk_numbers(record, sourced)
        if call_p.exists(): sourced |= set(numbers_in(call_p.read_text()))
        else: warns.append("no 02-call/call-notes.md — nothing from the call is sourceable")
        cs_p = Path(__file__).parent / "case-studies.md"
        if cs_p.exists(): sourced |= set(numbers_in(cs_p.read_text()))

        found = numbers_in(prop)
        by_raw = {}
        for v, raws in found.items():
            for r in raws: by_raw.setdefault(r, set()).add(v)
        for raw, readings in sorted(by_raw.items()):
            if not (readings & sourced):
                issues.append(f"unsourced number {raw!r} — not in the audit record, "
                              f"call notes, or case study library")

    # ---- 4. PLACEHOLDERS ----------------------------------------------
        for pat in PLACEHOLDERS:
            for m in set(re.findall(pat, prop)):
                issues.append(f"unresolved placeholder: {m if isinstance(m,str) else m[0]}")

    return issues, warns, notes


def main():
    if len(sys.argv) < 2:
        print("usage: validate.py <client-dir>"); sys.exit(2)
    issues, warns, notes = check(sys.argv[1])
    for n in notes: print(f"  note  {n}")
    for w in warns: print(f"  WARN  {w}")
    for i in issues: print(f"  FAIL  {i}")
    print()
    if issues:
        print(f"BLOCKED — {len(issues)} issue(s), {len(warns)} warning(s). Not send-ready.")
        sys.exit(1)
    print(f"CLEAN — 0 issues, {len(warns)} warning(s). Send-ready.")


if __name__ == "__main__":
    main()
