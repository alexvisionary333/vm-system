#!/usr/bin/env python3
"""
VISIONARY MEDIA — the causal chain and the plan
===============================================

    python _system/plan.py clients/icon

Writes two sections into `03-proposal/proposal.md`, both generated from
`01-audit/audit-record.json`, and refreshes the evidence table:

    # Why this is happening    causes, each naming the track that fixes it
    # The plan                 what's wrong -> what we build -> what it moves

WHY THIS EXISTS
---------------
A proposal that says "own the branded answer" has told the client nothing.
Every track renders as linked statements:

    what is broken today   <- the measured finding, from gaps[]
    what we build          <- named artefacts, from recommendations[].deliverables
    what stops being missing <- from gaps[].missing
    what it moves          <- the target row, from targets[]

A track that cannot name both the gap it fixes and the target it moves leaves
a REPLACE marker, which blocks the build. That is deliberate: a plan with no
stated outcome is the failure mode this file was written to stop.

Deliverables must be nameable things. "Comparison page vs Billo" is a
deliverable; "competitor content work" is an activity. If the client could not
tell whether it had been delivered, it does not belong here.

The evidence table under "What we found" is regenerated from the record on
every run. A hand-typed table goes stale the moment a prompt is re-run.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SYS_DIR = Path(__file__).resolve().parent

HEADING = "# The plan"
WHY_HEADING = "# Why this is happening"
FOUND_HEADING = "# What we found"
NEXT_HEADINGS = ["# What changes, measured", "# Proof", "# Investment",
                 "# Next steps"]

# Cause, not symptom. "Gemini cites zero pages" is a symptom; "nothing on the
# site declares what the company is, so there is nothing to cite" is a cause.
# Each entry returns (headline, why-it-causes-the-symptom).
CAUSES = {
    "entity_schema": lambda g, c: (
        "Your site never tells the AI what you are",
        f"When someone asks an AI who to hire, it looks for structured information "
        f"on your site that says what the company does, what it sells, and what "
        f"people think of it. {c['domain']} has none of that. So the AI fills the "
        f"gap with whatever other websites have said about you, which is why the "
        f"answer about {c['name']} comes back in someone else's words."),
    "off_domain_authority": lambda g, c: (
        "The pages the AI quotes don't mention you",
        f"Category answers get built from third party roundups and buyer's guides, "
        f"not from your own website. {c['cited_line']}Those are the pages getting "
        f"quoted and {c['name']} isn't on any of them. Right now there is no path "
        f"for the AI to name you, no matter how good the work is."),
    "live_ai_baseline": lambda g, c: (
        "Nothing you own answers the buying question",
        f"When someone asks if {c['name']} is any good, the AI needs a page that "
        f"answers that. {c['domain']} doesn't have one. So it pulls from review "
        f"aggregators instead, and those get written by unhappy customers way more "
        f"often than happy ones."),
    "on_page": lambda g, c: (
        "Your pages describe the product, not the decision",
        f"The AI platforms are crawling {c['domain']} constantly, that part is "
        f"working fine. The problem is what they find when they get there. They "
        f"read it as product information rather than an answer to “who should I "
        f"hire,” so all that crawling turns into citations without "
        f"recommendations."),
    "crawlability": lambda g, c: (
        "Access isn't the problem",
        "Every major AI crawler is allowed in and your sitemap is declared. Worth "
        "saying because it's usually the first thing an agency will sell you a fix "
        "for. Yours is already right."),
}
CAUSE_ORDER = ["entity_schema", "off_domain_authority", "live_ai_baseline",
               "on_page", "crawlability"]


def _fmt_target(t):
    s = f"**{t['metric']}** — {t.get('today')} today, {t.get('day_90')} by day 90"
    if t.get("stretch") not in (None, ""):
        s += f" ({t['stretch']} if it runs hot)"
    return s


def _escape_md(s):
    return s.replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------ evidence ---

def render_found_table(record) -> str:
    runs = [r for r in (record.get("prompt_runs") or [])
            if r.get("prompt_type") in ("category", "alternatives",
                                        "buying_guide", "comparison")]
    if not runs:
        return ""
    name = record["client"]["name"]
    engines = sorted({r["engine"] for r in runs})
    dates = sorted({r["date"] for r in runs})
    span = dates[0] if len(dates) == 1 else f"{dates[0]} – {dates[-1]}"
    rows = [f"| Prompt ({', '.join(engines)}, {span}) | Who got named | {name} |",
            "|---|---|---|"]
    for r in runs:
        who = ", ".join(r.get("competitors_named") or []) or "—"
        cell = ("Named" if r["client_named"]
                else '<span class="zero">Not named</span>')
        rows.append(f"| {r['prompt']} | {who} | {cell} |")
    return "\n".join(rows)


def swap_found_table(text, record) -> str:
    block = render_found_table(record)
    if not block or FOUND_HEADING not in text:
        return text
    head, _, tail = text.partition(FOUND_HEADING)
    # a contiguous run of pipe-table lines -- anything less leaves orphan rows
    # from the previous table sitting under the new one
    m = re.search(r"(?:^[ \t]*\|.*(?:\n|$))+", tail, re.M)
    if not m:
        return text
    return head + FOUND_HEADING + tail[:m.start()] + block + "\n" + tail[m.end():]


# ----------------------------------------------------------------- why ---

def render_why(record) -> str:
    """Symptoms live in 'What we found'. This says WHY, and names the track
    that closes each cause so the plan reads as a consequence, not a menu."""
    gaps = {g["layer"]: g for g in (record.get("gaps") or [])}
    if not gaps:
        return WHY_HEADING + "\n\nREPLACE — no findings in the audit record.\n"

    name = record["client"]["name"]
    url = record["client"].get("url", "")
    domain = re.sub(r"^https?://(www\.)?", "", url).rstrip("/") or "the site"

    runs = record.get("prompt_runs") or []
    cited = sorted({s for r in runs
                    if r.get("prompt_type") in ("category", "alternatives",
                                                "buying_guide")
                    for s in (r.get("sources_cited") or [])})
    cited_line = (f"In this audit the engines cited {', '.join(cited)}. "
                  if cited else "")
    ctx = {"name": name, "domain": domain, "cited_line": cited_line}

    fixer = {}
    for i, r in enumerate(record.get("recommendations") or [], 1):
        for layer in r.get("addresses") or []:
            fixer.setdefault(layer, (i, r["track"]))

    out = [WHY_HEADING, "",
           f"{name} isn't missing from these answers because the work isn't good "
           f"enough. It's missing for specific reasons, and all of them are "
           f"fixable. Each one is below with the track that fixes it.", ""]

    for layer in CAUSE_ORDER:
        g = gaps.get(layer)
        if not g:
            continue
        head, body = CAUSES[layer](g, ctx)
        out += [f"### {head}", "", body, ""]
        ev = (g.get("evidence") or [])[:3]
        if ev and layer != "crawlability":
            out += ["*What we measured: "
                    + "; ".join(_escape_md(e.replace("\n", " ")) for e in ev)
                    + ".*", ""]
        if layer in fixer:
            i, track = fixer[layer]
            out += [f"**Fixed by Track {i}, {track}.**", ""]
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- plan ---

def render_plan(record) -> str:
    recs = record.get("recommendations") or []
    gaps = {g["layer"]: g for g in (record.get("gaps") or [])}
    targets = {t["metric"]: t for t in (record.get("targets") or [])}

    if not recs:
        return (HEADING + "\n\nREPLACE — no tracks in the audit record. Write "
                "them in `01-audit/interpretation.json` and re-run the audit.\n")

    out = [HEADING, "",
           "Each track has three parts: what's wrong now, what we actually build, "
           "and which number it moves. Nothing here is vague activity. Everything "
           "listed either exists at the end of it or it doesn't.", ""]

    for i, r in enumerate(recs, 1):
        out += [f"### Track {i} — {r['track']}", ""]

        addressed = [gaps[l] for l in (r.get("addresses") or []) if l in gaps]
        if addressed:
            out += ["**What's wrong today**", ""]
            out += [f"- {g['finding']}" for g in addressed]
            out.append("")
        elif r.get("rationale"):
            out += [f"**What's wrong today** — {r['rationale']}", ""]
        else:
            out += ["**What's wrong today** — REPLACE: link this track to a "
                    "gaps[].layer via `addresses`.", ""]

        out += ["**What we build**", ""]
        out += [f"- {d}" for d in
                (r.get("deliverables") or ["REPLACE — no deliverables listed"])]
        out.append("")

        closes = []
        for g in addressed:
            closes += g.get("missing") or []
        if closes:
            out += ["**What stops being missing**", ""]
            out += [f"- {c}" for c in closes[:6]]
            out.append("")

        moved = [targets[m] for m in (r.get("moves") or []) if m in targets]
        if moved:
            out += ["**What it moves**", ""]
            for t in moved:
                line = _fmt_target(t)
                if t.get("pace_note"):
                    line += f". {t['pace_note']}"
                out.append(f"- {line}")
            out.append("")
        else:
            out += ["**What it moves** — REPLACE: name the targets[].metric "
                    "rows this track moves, via `moves`.", ""]

        bits = []
        if r.get("time_to_impact"):
            bits.append(f"**First results:** {r['time_to_impact']}")
        if r.get("effort"):
            bits.append(f"**Effort:** {r['effort']}")
        if bits:
            out += [" · ".join(bits), ""]
        if r.get("client_dependencies"):
            out += ["**We need from you:** "
                    + "; ".join(r["client_dependencies"]) + ".", ""]

    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------- write ---

def write_into_proposal(client_dir) -> Path:
    cdir = Path(client_dir)
    rec = json.loads((cdir / "01-audit" / "audit-record.json").read_text())
    prop = cdir / "03-proposal" / "proposal.md"
    text = prop.read_text(encoding="utf-8")
    text = swap_found_table(text, rec)

    for heading, block, anchors in (
            (WHY_HEADING, render_why(rec), [HEADING] + NEXT_HEADINGS),
            (HEADING, render_plan(rec), NEXT_HEADINGS)):
        if heading in text:
            head, _, tail = text.partition(heading)
            rest = re.split(r"\n(?=# )", tail, maxsplit=1)
            text = head + block + ("\n" + rest[1] if len(rest) > 1 else "")
        else:
            anchor = next((h for h in anchors if h in text), None)
            if anchor:
                text = text.replace(anchor, block + "\n" + anchor, 1)
            else:
                text = text.rstrip() + "\n\n" + block
    prop.write_text(text, encoding="utf-8")
    return prop


def main():
    if len(sys.argv) < 2:
        print("usage: plan.py <client-dir>")
        return 2
    print(f"wrote the plan into {write_into_proposal(sys.argv[1])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
