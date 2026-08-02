#!/usr/bin/env python3
"""
VISIONARY MEDIA — audit report renderer
=======================================

    python _system/render_audit_report.py clients/icon          # md + PDF
    python _system/render_audit_report.py clients/icon --md-only

Fills `_system/templates/audit-report.md` from `01-audit/audit-record.json`
and hands the result to visionary_media.py, which owns the brand.

This is the Call 1 leave-behind. Findings and evidence only — no pricing, no
scope, no plan. It renders ONLY what is in the record. A field that is absent
becomes a stated gap in the report, never an inferred value.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SYS_DIR = Path(__file__).resolve().parent
TEMPLATE = SYS_DIR / "templates" / "audit-report.md"

LAYER_TITLES = {
    "crawlability": "Whether the engines can read you",
    "entity_schema": "Whether they know what you are",
    "on_page": "They read you and don't recommend you",
    "off_domain_authority": "The answers you're absent from",
    "live_ai_baseline": "Who writes your branded answer",
}

METRIC_LABELS = [
    ("ai_visibility_score", "AI Visibility score", None),
    ("mentions_total", "Mentions in AI answers", None),
    ("cited_pages_total", "Pages cited by AI", None),
    ("authority_score", "Authority score", None),
    ("organic_traffic", "Organic traffic / mo", "delta"),
    ("organic_keywords", "Organic keywords", "delta"),
    ("paid_keywords", "Paid keywords", None),
    ("backlinks", "Backlinks", None),
    ("referring_domains", "Referring domains", None),
]


def _fmt(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, int) and abs(v) >= 1000:
        return f"{v:,}"
    return str(v)


def _zero(v):
    """Wrap a zero or an absence in the brand's alert colour."""
    return f'<span class="zero">{_fmt(v)}</span>' if v in (0, 0.0) else _fmt(v)


def _delta(d):
    if d is None:
        return ""
    if d < 0:
        return f' <span class="down">−{abs(d)}%</span>'
    if d > 0:
        return f' <span class="up">+{d}%</span>'
    return ' <span class="zero">0%</span>'


def _pretty_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%b %-d %Y")
    except Exception:                                        # noqa: BLE001
        return iso or ""


# ---------------------------------------------------------------- blocks ---

def _prompt_table(runs, client_name):
    if not runs:
        return "_No prompt runs captured. This report cannot be sent._"
    engines = sorted({r["engine"] for r in runs})
    dates = sorted({r["date"] for r in runs})
    head = (f"{', '.join(engines)}, "
            f"{_pretty_date(dates[0])}"
            + (f" – {_pretty_date(dates[-1])}" if len(dates) > 1 else ""))
    order = {"category": 0, "alternatives": 1, "comparison": 2,
             "buying_guide": 3, "branded": 4}
    rows = [f"| Prompt ({head}) | Who got named | {client_name} |",
            "|---|---|---|"]
    for r in sorted(runs, key=lambda r: (order.get(r.get("prompt_type"), 9),
                                         r["prompt"])):
        named = ", ".join(r.get("competitors_named") or []) or "—"
        if r["client_named"]:
            pos = r.get("client_position")
            cell = f"Named (#{pos})" if pos else "Named"
        else:
            cell = '<span class="zero">Not named</span>'
        rows.append(f"| {r['prompt']} | {named} | {cell} |")
    return "\n".join(rows)


def _count_line(runs, client_name):
    if not runs:
        return "REPLACE — no prompt runs in the record."
    disc = [r for r in runs if r.get("prompt_type") in
            ("category", "alternatives", "buying_guide")]
    if not disc:
        return (f"We ran {len(runs)} prompts your buyers actually type, in the "
                f"engines they type them into.")
    named = sum(1 for r in disc if r["client_named"])
    if named == 0:
        return (f"We ran {len(disc)} discovery prompts — the questions someone "
                f"asks when they do not yet know who to hire. {client_name} was "
                f"named in none of them.")
    return (f"We ran {len(disc)} discovery prompts. {client_name} was named in "
            f"{named} of {len(disc)}.")


def _figures(runs, adir):
    """Only emits a figure whose file is actually on disk. A caption with no
    image behind it reads as a missing figure in a client PDF; the absent ones
    are named in the callout instead so nobody has to notice the gap.

    Captions carry no markdown emphasis — visionary_media copies alt text into
    <figcaption> verbatim, so `**` would print as asterisks."""
    out, n, missing = [], 0, []
    for r in runs:
        shot = r.get("screenshot")
        if not shot:
            continue
        if not (adir / shot).exists():
            missing.append(f"{r['engine']}, “{r['prompt']}” → {shot}")
            continue
        n += 1
        cap = (f"Fig {n}. {r['engine']}, “{r['prompt']}”. "
               + ("Client named." if r["client_named"]
                  else "Client does not appear."))
        out.append(f"![{cap}]({shot})")
    if missing:
        out.append("> Screenshots referenced by the record but not on disk — "
                   "capture these before the report leaves the building:\n> - "
                   + "\n> - ".join(missing))
    if n == 0:
        out.insert(0, "> No screenshot in this record renders. An absence claim "
                      "without evidence is not usable in a client conversation.")
    return "\n\n".join(out)


def _branded_callout(runs, client_name):
    branded = [r for r in runs if r.get("prompt_type") == "branded"]
    if not branded:
        return ""
    hedged = [r for r in branded if r.get("sentiment") in ("hedged", "negative")]
    srcs = sorted({s for r in branded for s in (r.get("sources_cited") or [])})
    if not hedged and not srcs:
        return ""
    lines = []
    if srcs:
        lines.append(f"Asked about {client_name} by name, the engine answers from "
                     f"{', '.join(srcs)}.")
    if hedged:
        note = next((r.get("verbatim_note") for r in hedged if r.get("verbatim_note")), "")
        lines.append(f"The tone is **{hedged[0]['sentiment']}**." + (f" {note}" if note else ""))
    lines.append(f"**The brand-level answer about {client_name} is currently written "
                 f"by third parties, not by anything {client_name} controls.**")
    return "> " + "\n> ".join(lines)


def _metrics_table(pm):
    if not pm:
        return ("> No platform metrics in this record. REPLACE — paste them into "
                "`01-audit/semrush.json` and re-run the audit.")
    src = pm.get("source", "REPLACE — source")
    when = _pretty_date(pm.get("date", "")) or ""
    head = f"{src}{', ' + when if when else ''}"
    rows = [f"| Metric ({head}) | Value |", "|---|---|"]
    for key, label, kind in METRIC_LABELS:
        if key not in pm:
            continue
        v = pm[key]
        if kind == "delta" and isinstance(v, dict):
            if v.get("value") is None:
                continue
            rows.append(f"| {label} | {_zero(v['value'])}{_delta(v.get('delta_pct'))} |")
        elif not isinstance(v, dict):
            rows.append(f"| {label} | {_zero(v)} |")
    for group, label in (("mentions_by_engine", "Mentions"),
                         ("cited_pages_by_engine", "Pages cited")):
        for eng, v in (pm.get(group) or {}).items():
            rows.append(f"| {label} — {eng} | {_zero(v)} |")
    return "\n".join(rows) if len(rows) > 2 else \
        "> Platform metrics block is present but empty. REPLACE."


def _metrics_note(pm, adir=None):
    bits = []
    note = pm.get("cited_pages_total_note") if pm else None
    if note:
        bits.append(f"_{note}_")
    for i, shot in enumerate((pm or {}).get("evidence_screenshots") or [], 1):
        if adir is None or (adir / shot).exists():
            bits.append(f"![{(pm or {}).get('source', 'Platform')} screenshot "
                        f"{i}, read {_pretty_date((pm or {}).get('date', ''))}.]({shot})")
        else:
            bits.append(f"> Platform screenshot referenced but not on disk: {shot}")
    return "\n\n".join(bits)


def _gap_sections(gaps):
    """Findings, what is concretely absent, and the measurements underneath.
    No scores — there is no number here that we invented."""
    if not gaps:
        return ("> Nothing measurable yet. Every input these findings depend on was "
                "missing — see *What we could not determine*.")
    order = ["off_domain_authority", "live_ai_baseline", "on_page",
             "entity_schema", "crawlability"]
    out = []
    for g in sorted(gaps, key=lambda g: order.index(g["layer"])
                    if g["layer"] in order else 99):
        title = LAYER_TITLES.get(g["layer"], g["layer"].replace("_", " ").title())
        out.append(f"### {title}\n\n{g['finding']}")
        miss = g.get("missing") or []
        if miss:
            # CommonMark needs a blank line before a list or it renders inline
            out.append("**What does not exist today:**\n\n"
                       + "\n".join(f"- {m}" for m in miss))
        ev = g.get("evidence") or []
        if ev:
            out.append("<div class=\"callout\">\nMeasured:<br>\n"
                       + "<br>\n".join(_escape_md(e) for e in ev) + "\n</div>")
    return "\n\n".join(out)


def _escape_md(s):
    return s.replace("<", "&lt;").replace(">", "&gt;")


def _unknowns_block(unknowns):
    if not unknowns:
        return "Nothing. Every field the record needs was measured or supplied."
    lines = ["The audit could not determine the following. They are listed here "
             "rather than estimated, and each one is a question for the call.\n"]
    lines += [f"- {u}" for u in unknowns]
    return "\n".join(lines)


def _method_block(record, cdir):
    r = record.get("run", {})
    reviewed = r.get("prompt_set_reviewed_by_human")
    runs = record.get("prompt_runs", [])
    engines = sorted({x["engine"] for x in runs})
    lines = [
        f"- **Run date** {_pretty_date(r.get('date',''))} · **operator** "
        f"{r.get('operator','REPLACE — operator')}",
        f"- **Engines** {', '.join(engines) or 'REPLACE — none recorded'}",
        f"- **Prompts** {len({x['prompt'] for x in runs})} distinct, "
        f"{len(runs)} prompt-engine runs",
        f"- **Prompt set reviewed by a human** "
        + ("yes" if reviewed else
           "**no — this audit is not send-ready until a human has read the prompt set**"),
        "- **Every prompt, and every answer, is in "
        "`01-audit/prompt-set.json`.** Re-run them yourself.",
        "- **Every score above** is computed from the arithmetic printed beside "
        "it. No score is a judgement call.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- render ---

def render_markdown(client_dir, record=None) -> Path:
    cdir = Path(client_dir)
    if record is None:
        record = json.loads((cdir / "01-audit" / "audit-record.json").read_text())

    name = record["client"]["name"]
    runs = record.get("prompt_runs", [])
    pm = record.get("platform_metrics") or {}
    run_date = record.get("run", {}).get("date", "")

    disc = [r for r in runs if r.get("prompt_type") in
            ("category", "alternatives", "buying_guide")]
    named = sum(1 for r in disc if r["client_named"])
    if disc and named == 0:
        headline = f"{name} is not in the answer when buyers ask who to hire"
    elif disc:
        headline = f"{name} appears in {named} of {len(disc)} buying questions"
    else:
        headline = f"Where {name} stands in AI answers today"

    today = date.today()
    tokens = {
        "{{HEADLINE}}": headline,
        "{{CLIENT_NAME}}": name,
        "{{DOC_DATE}}": today.strftime("%B %-d, %Y"),
        "{{VALID_THROUGH}}": (today + timedelta(days=21)).strftime("%B %-d, %Y"),
        "{{RUN_DATE}}": _pretty_date(run_date),
        "{{PROMPT_COUNT_LINE}}": _count_line(runs, name),
        "{{PROMPT_TABLE}}": _prompt_table(runs, name),
        "{{FIGURES}}": _figures(runs, cdir / "01-audit"),
        "{{BRANDED_CALLOUT}}": _branded_callout(runs, name),
        "{{METRICS_TABLE}}": _metrics_table(pm),
        "{{METRICS_NOTE}}": _metrics_note(pm, cdir / "01-audit"),
        "{{GAP_SECTIONS}}": _gap_sections(record.get("gaps") or []),
        "{{UNKNOWNS_BLOCK}}": _unknowns_block(record.get("unknowns") or []),
        "{{METHOD_BLOCK}}": _method_block(record, cdir),
    }
    md = TEMPLATE.read_text(encoding="utf-8")
    for k, v in tokens.items():
        md = md.replace(k, v)
    md = "\n".join(line.rstrip() for line in md.splitlines())
    while "\n\n\n" in md:
        md = md.replace("\n\n\n", "\n\n")

    out = cdir / "01-audit" / "audit-report.md"
    out.write_text(md, encoding="utf-8")
    return out


def render_pdf(client_dir) -> str:
    cdir = Path(client_dir)
    md = render_markdown(cdir)
    spec = importlib.util.spec_from_file_location("vm", SYS_DIR / "visionary_media.py")
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    rec = json.loads((cdir / "01-audit" / "audit-record.json").read_text())
    draft = bool(rec.get("unknowns")) or not rec.get("run", {}).get(
        "prompt_set_reviewed_by_human")

    raw = md.read_text(encoding="utf-8")
    fm, body = raw.split("---", 2)[1], raw.split("---", 2)[2]
    lines = [l for l in fm.strip().splitlines() if ":" in l]
    out_pdf = cdir / "01-audit" / ("audit-report-DRAFT.pdf" if draft
                                   else "audit-report.pdf")
    tmp = cdir / "01-audit" / "_build.md"
    tmp.write_text("---\n" + "\n".join(lines) + f"\noutput: {out_pdf}\n---\n" + body,
                   encoding="utf-8")
    vm.render(str(tmp), draft=draft)
    tmp.unlink()
    return str(out_pdf)


def main():
    if len(sys.argv) < 2:
        print("usage: render_audit_report.py <client-dir> [--md-only]")
        return 2
    cdir = Path(sys.argv[1])
    if "--md-only" in sys.argv:
        print(f"Wrote: {render_markdown(cdir)}")
    else:
        render_pdf(cdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
