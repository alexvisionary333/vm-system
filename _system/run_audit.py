#!/usr/bin/env python3
"""
VISIONARY MEDIA — AI visibility audit engine
============================================

    python _system/run_audit.py https://icon.com

Produces  clients/<name>/01-audit/audit-record.json  — the contract the
proposal is built from — plus the working files the operator fills in.

WHAT THIS SCRIPT WILL AND WILL NOT DO
-------------------------------------
It measures what a machine can measure and refuses to fabricate the rest.

  MEASURED (automatic)
    - robots.txt: which AI crawlers are allowed, which are blocked
    - sitemap presence, homepage reachability, title/description
    - JSON-LD entity coverage on the homepage (Organization, WebSite,
      Service/Product, FAQPage, Review/AggregateRating)
    - the prompt set: generated deterministically from category,
      audience, competitors and any stale positioning
    - every derived score, from a stated formula over measured inputs
      (each one carries its own arithmetic in `evidence[]`)

  HUMAN (this script writes the checklist, a person does the work)
    - running the prompts in the live engines and screenshotting them
    - pasting the Semrush figures
    - reviewing the prompt set before it counts
    - the recommendation tracks and the day-90 targets — the
      interpretation is the product and is not derivable from a crawl

Anything neither measured nor supplied lands in `unknowns[]`, verbatim,
and the proposal turns it into a REPLACE marker. Nothing is guessed.

THREE-PASS OPERATION — the same command, run three times
--------------------------------------------------------
  pass 1   nothing exists       -> probes the site, writes prompt-set.json,
                                   semrush.json (blank), interpretation.json
                                   (blank) and CAPTURE-CHECKLIST.md. Stops.
  pass 2   operator has run the prompts and filled the files
                                -> ingests them, derives, validates, writes
                                   audit-record.json + audit-report.md
  pass 3   re-run after edits   -> same, idempotent. Refuses to clobber an
                                   existing record unless --force.

Exit 0 = record written.  Exit 3 = waiting on the operator.  Exit 1 = invalid.
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SYS_DIR = Path(__file__).resolve().parent
ROOT = SYS_DIR.parent
SCHEMA_PATH = SYS_DIR / "audit-record.schema.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Engines the schema allows. Default run order = the ones a rep can actually
# reach in a browser without an enterprise seat.
ALL_ENGINES = ["ChatGPT", "Perplexity", "Gemini", "Google AI Mode",
               "Google AI Overviews", "Claude", "Copilot"]
DEFAULT_ENGINES = ["Perplexity"]

# AI crawlers that matter for citation eligibility.
AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot",
               "anthropic-ai", "PerplexityBot", "Google-Extended", "CCBot",
               "Bytespider", "Applebot-Extended"]

# JSON-LD @types that carry entity meaning for this category of buyer.
ENTITY_TYPES = {
    "Organization": ["Organization", "Corporation", "LocalBusiness", "Brand"],
    "WebSite": ["WebSite"],
    "Service/Product": ["Service", "Product", "SoftwareApplication", "Offer"],
    "FAQPage": ["FAQPage", "Question"],
    "Review": ["Review", "AggregateRating"],
}


# ===========================================================================
# small helpers
# ===========================================================================

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def domain_of(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.replace("www.", "")


def fetch(url: str, timeout: int = 20):
    """Returns (status, text, error). Never raises."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = r.read(2_000_000)
            return r.status, raw.decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        return e.code, "", f"HTTP {e.code}"
    except Exception as e:                                  # noqa: BLE001
        return None, "", f"{type(e).__name__}: {e}"


def jwrite(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def jread(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return None


def is_blank(obj) -> bool:
    """A scaffold file the operator hasn't touched."""
    if obj is None:
        return True
    if isinstance(obj, dict):
        return all(is_blank(v) for k, v in obj.items() if not k.startswith("_"))
    if isinstance(obj, list):
        return len(obj) == 0 or all(is_blank(v) for v in obj)
    if isinstance(obj, str):
        return obj.strip() == "" or obj.strip().upper().startswith("REPLACE")
    return False


# ===========================================================================
# 1. SITE PROBE — the part that is genuinely automatable
# ===========================================================================

def probe_site(url: str) -> dict:
    base = url.rstrip("/")
    out = {
        "url": base,
        "checked": date.today().isoformat(),
        "homepage_status": None,
        "title": None,
        "meta_description": None,
        "sitemap_urls": [],
        "robots_status": None,
        "ai_crawlers_blocked": [],
        "ai_crawlers_allowed": [],
        "entity_types_present": [],
        "entity_types_missing": [],
        "jsonld_blocks": 0,
        "errors": [],
    }

    status, html, err = fetch(base + "/")
    out["homepage_status"] = status
    if err:
        out["errors"].append(f"homepage: {err}")
    if html:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        if m:
            out["title"] = re.sub(r"\s+", " ", m.group(1)).strip()[:200]
        m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+'
                      r'content=["\'](.*?)["\']', html, re.S | re.I)
        if m:
            out["meta_description"] = re.sub(r"\s+", " ", m.group(1)).strip()[:300]

        blocks = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.S | re.I)
        out["jsonld_blocks"] = len(blocks)
        found_types = set()
        for b in blocks:
            found_types.update(t.lower() for t in re.findall(r'"@type"\s*:\s*"([^"]+)"', b))
            for arr in re.findall(r'"@type"\s*:\s*\[([^\]]+)\]', b):
                found_types.update(t.strip().strip('"').lower()
                                   for t in arr.split(","))
        for label, aliases in ENTITY_TYPES.items():
            if any(a.lower() in found_types for a in aliases):
                out["entity_types_present"].append(label)
            else:
                out["entity_types_missing"].append(label)

    # robots.txt
    rstatus, robots, rerr = fetch(base + "/robots.txt")
    out["robots_status"] = rstatus
    if rerr:
        out["errors"].append(f"robots.txt: {rerr}")
    if robots:
        out["sitemap_urls"] = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
        groups, current = {}, []
        for line in robots.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            k, _, v = line.partition(":")
            k, v = k.strip().lower(), v.strip()
            if k == "user-agent":
                current = [v]
                groups.setdefault(v, [])
            elif k == "disallow" and current:
                groups.setdefault(current[0], []).append(v)
        for bot in AI_CRAWLERS:
            rules = None
            for agent, dis in groups.items():
                if agent.lower() == bot.lower():
                    rules = dis
                    break
            if rules is None:
                rules = groups.get("*")
            if rules and any(r == "/" for r in rules):
                out["ai_crawlers_blocked"].append(bot)
            elif rules is not None:
                out["ai_crawlers_allowed"].append(bot)
    else:
        out["errors"].append("robots.txt unreadable — crawler posture unknown")

    if not out["sitemap_urls"]:
        s, _, _ = fetch(base + "/sitemap.xml")
        if s == 200:
            out["sitemap_urls"] = [base + "/sitemap.xml"]
    return out


# ===========================================================================
# 2. PROMPT SET — deterministic generation
# ===========================================================================

def build_prompt_set(client_name, url, noun, audience, competitors,
                     stale_noun, engines, offering=None, max_alternatives=2,
                     max_comparisons=2) -> list:
    """Mirrors the shape of the Icon record: category prompts first (the ones
    that decide whether you exist), then alternatives against the competitors
    the client names themselves, then comparison, then a buying guide, then
    branded last (the one a launch multiplies).

    `noun` is what the client IS ("UGC ad agency"). `offering` is what they
    SELL ("UGC video ads"). They are different words and swapping them
    produces prompts no buyer would type — which is exactly the "cold prompt
    set" the schema warns about. Offering falls back to noun."""
    dom = domain_of(url)
    thing = offering or noun
    aud = f" for {audience}" if audience else ""
    rows = []

    def add(prompt, ptype):
        rows.append({"prompt": prompt, "prompt_type": ptype})

    add(f"best {noun}{aud}", "category")
    if stale_noun:
        # a stale positioning may carry its own audience: "AI ad generator for
        # ecommerce brands" -> keep it whole rather than re-suffixing
        add(f"best {stale_noun}" if " for " in stale_noun
            else f"best {stale_noun}{aud}", "category")
    for c in competitors[:max_alternatives]:
        add(f"{c} alternatives for {thing}", "alternatives")
    for c in competitors[:max_comparisons]:
        add(f"{client_name} vs {c}", "comparison")
    add(f"how to choose a {noun}{aud}", "buying_guide")
    add(f"Is {client_name} ({dom}) a good service for {thing}?", "branded")
    add(f"{client_name} reviews — is it legit?", "branded")

    out = []
    for e in engines:
        for r in rows:
            out.append({
                "prompt": r["prompt"],
                "prompt_type": r["prompt_type"],
                "engine": e,
                "date": "",
                "client_named": None,
                "client_position": None,
                "competitors_named": [],
                "sources_cited": [],
                "sentiment": "",
                "screenshot": "",
                "verbatim_note": "",
            })
    return out


# ===========================================================================
# 3. DERIVATIONS — every score carries its own arithmetic
# ===========================================================================

def _pct(n, d):
    return 0.0 if not d else 100.0 * n / d


def derive_gaps(probe, metrics, runs) -> tuple[list, list]:
    """What is TRUE, and what is concretely ABSENT. No scores.

    A score is a number we made up about data we already have. It invites the
    client to argue with the grade instead of the facts, and it is the one
    figure in this system that cannot be traced to a source. So there isn't
    one. Each layer states what was measured, the evidence it rests on, and
    the specific things that do not exist — every `missing` entry should be
    something a deliverable could create.

    A layer whose inputs were not measured produces an entry in unknowns[],
    never a filled-in blank."""
    gaps, unknown = [], []
    cited = (metrics or {}).get("cited_pages_by_engine") or {}
    by_e = (metrics or {}).get("mentions_by_engine") or {}
    owned = domain_of(probe["url"])

    # ---- crawlability -----------------------------------------------------
    if probe.get("robots_status") == 200:
        blocked, missing = probe["ai_crawlers_blocked"], []
        if blocked:
            missing.append(f"Crawl access for {', '.join(blocked)}")
        if not probe["sitemap_urls"]:
            missing.append("A sitemap declared in robots.txt")
        finding = ("Every major AI crawler is permitted and a sitemap is declared. "
                   "The engines can read the site — this is not the constraint."
                   if not missing else
                   f"{len(blocked)} AI crawler(s) are disallowed in robots.txt"
                   + ("; no sitemap is declared." if not probe["sitemap_urls"] else "."))
        gaps.append({
            "layer": "crawlability", "finding": finding, "missing": missing,
            "evidence": [f"robots.txt read {probe['checked']}",
                         f"permitted: {', '.join(probe['ai_crawlers_allowed']) or 'none'}",
                         f"disallowed: {', '.join(blocked) or 'none'}",
                         f"sitemap: {probe['sitemap_urls'][0] if probe['sitemap_urls'] else 'not declared'}"]})
    else:
        unknown.append("Crawler posture — robots.txt could not be read "
                       f"(status {probe.get('robots_status')})")

    # ---- entity_schema ----------------------------------------------------
    if probe.get("homepage_status") == 200:
        absent = probe["entity_types_missing"]
        present = probe["entity_types_present"]
        missing = [f"{t} structured data on the homepage" for t in absent]
        zero = [e for e, v in cited.items() if not v]
        missing += [f"Any page {e} is willing to cite" for e in zero]
        finding = (f"{len(present)} of {len(ENTITY_TYPES)} entity schema types are present "
                   f"on the homepage ({probe['jsonld_blocks']} JSON-LD block(s) found).")
        if not present:
            finding = (f"The homepage carries no structured data at all — "
                       f"{probe['jsonld_blocks']} JSON-LD blocks. Nothing on the site tells "
                       f"an engine what this company is or what it sells.")
        if zero:
            finding += f" {', '.join(zero)} cites zero pages."
        gaps.append({
            "layer": "entity_schema", "finding": finding, "missing": missing,
            "evidence": [f"present: {', '.join(present) or 'none'}",
                         f"absent: {', '.join(absent) or 'none'}"]
                        + [f"{e}: {v} page(s) cited" for e, v in cited.items()]})
    else:
        unknown.append("Structured data coverage — the homepage could not be read "
                       f"(status {probe.get('homepage_status')})")

    # ---- on_page ----------------------------------------------------------
    scoreable = {e: c for e, c in cited.items() if (c or 0) > 0}
    if scoreable and by_e:
        ratios = sorted(((e, c, by_e.get(e, 0)) for e, c in scoreable.items()),
                        key=lambda t: t[2] / t[1])
        e, cp, mn = ratios[0]
        gaps.append({
            "layer": "on_page",
            "finding": (f"{e} reads {cp} pages on the site and names the brand {mn} time(s). "
                        f"The pages are being crawled and are not producing recommendations."),
            "missing": [f"Pages that answer a hiring question directly — {e} currently "
                        f"finds {cp - mn if cp > mn else 0} page(s) it reads but does not "
                        f"cite in an answer"],
            "evidence": [f"source: {(metrics or {}).get('source', '?')}"]
                        + [f"{en}: {m2} mention(s) from {c2} cited page(s)"
                           for en, c2, m2 in ratios]})
    else:
        unknown.append("Crawl-to-mention conversion — needs mentions_by_engine and "
                       "cited_pages_by_engine from the platform")

    # ---- off_domain_authority ---------------------------------------------
    disc = [r for r in runs
            if r.get("prompt_type") in ("category", "alternatives", "buying_guide")
            and r.get("client_named") is not None]
    if disc:
        named = sum(1 for r in disc if r["client_named"])
        rivals, seen = [], set()
        for r in disc:
            for c in r.get("competitors_named") or []:
                if c not in seen:
                    seen.add(c)
                    rivals.append(c)
        client = (runs[0].get("_client") if runs else None) or "the client"
        gaps.append({
            "layer": "off_domain_authority",
            "finding": (f"Named in {named} of {len(disc)} discovery prompts. "
                        f"{len(rivals)} other companies were named across the same "
                        f"answers." if named else
                        f"Absent from all {len(disc)} discovery prompts. "
                        f"{len(rivals)} other companies were named instead."),
            "missing": [f"Presence in the sources that answer \u201c{r['prompt']}\u201d"
                        for r in disc if not r["client_named"]],
            "evidence": [f"\u201c{r['prompt']}\u201d ({r['engine']}, {r['date']}) — "
                         f"{'named' if r['client_named'] else 'not named'}; returned: "
                         f"{', '.join(r.get('competitors_named') or []) or 'no brands'}"
                         for r in disc]})
    else:
        unknown.append("Discovery-prompt presence — no category, alternatives or "
                       "buying-guide prompts have been captured yet")

    # ---- live_ai_baseline: who writes the branded answer ------------------
    branded = [r for r in runs if r.get("prompt_type") == "branded"
               and r.get("client_named")]
    if branded:
        third = sorted({s for r in branded for s in (r.get("sources_cited") or [])
                        if owned not in s})
        own = sorted({s for r in branded for s in (r.get("sources_cited") or [])
                      if owned in s})
        sent = [r.get("sentiment") for r in branded if r.get("sentiment")
                not in (None, "", "n/a")]
        finding = (f"Asked about the brand by name, the engine answers from "
                   f"{', '.join(third) or 'sources it does not disclose'}"
                   + (f" and not from {owned}." if not own else f" alongside {owned}."))
        if sent:
            finding += f" The tone is {sent[0]}."
        gaps.append({
            "layer": "live_ai_baseline", "finding": finding,
            "missing": ([f"An owned page {owned} controls that answers "
                         f"\u201c{r['prompt']}\u201d" for r in branded]
                        if not own else []),
            "evidence": [f"\u201c{r['prompt']}\u201d ({r['engine']}, {r['date']}) — cited: "
                         f"{', '.join(r.get('sources_cited') or []) or 'none recorded'}"
                         + (f"; {r['verbatim_note']}" if r.get("verbatim_note") else "")
                         for r in branded]})
    else:
        unknown.append("Who writes the branded answer — no branded prompt has been "
                       "captured with the client named")

    return gaps, unknown


def derive_targets_today(metrics, runs) -> list:
    """`today` is measured. `day_90` and `stretch` are commitments a human
    makes — this only fills the column it can prove."""
    rows = []
    if (metrics or {}).get("ai_visibility_score") is not None:
        rows.append({"metric": "AI Visibility score",
                     "today": metrics["ai_visibility_score"]})
    # Metric strings are the key `interpretation.json` commits against, so they
    # must not move when the prompt count changes. The denominator lives in the
    # value, not the label.
    disc = [r for r in runs if r.get("prompt_type") in
            ("category", "alternatives", "buying_guide")
            and r.get("client_named") is not None]
    if disc:
        rows.append({"metric": "Discovery prompts naming the client",
                     "today": f"{sum(1 for r in disc if r['client_named'])} of {len(disc)}"})
    for eng, v in ((metrics or {}).get("cited_pages_by_engine") or {}).items():
        if v == 0:
            rows.append({"metric": f"Pages cited — {eng}", "today": 0})
    branded = [r for r in runs if r.get("prompt_type") == "branded"
               and r.get("sentiment") not in (None, "", "n/a")]
    if branded:
        rows.append({"metric": "Branded answer sentiment",
                     "today": branded[0]["sentiment"]})
    return rows


# ===========================================================================
# 4. SCAFFOLDS the operator fills in
# ===========================================================================

SEMRUSH_SCAFFOLD = {
    "_README": "Paste from the Semrush AI Toolkit + Domain Overview. Delete any "
               "line you cannot read off the screen — a deleted line becomes an "
               "unknown, a guessed line becomes a lie in a client PDF.",
    "source": "Semrush",
    "date": "",
    "ai_visibility_score": None,
    "mentions_by_engine": {},
    "cited_pages_by_engine": {},
    "mentions_total": None,
    "cited_pages_total": None,
    "authority_score": None,
    "organic_traffic": {"value": None, "delta_pct": None},
    "organic_keywords": {"value": None, "delta_pct": None},
    "paid_keywords": None,
    "backlinks": None,
    "referring_domains": None,
}

INTERPRETATION_SCAFFOLD = {
    "_README": "The two things a crawl cannot produce. The strategist writes "
               "these after reading the captured answers. Leave blank and the "
               "audit still validates — the proposal will just carry REPLACE "
               "markers for the plan and the day-90 column.",
    "positioning_note": "",
    "recommendations": [
        {"track": "", "rationale": "", "time_to_impact": "",
         "effort": "", "deliverables": [], "client_dependencies": []}
    ],
    "target_commitments": {
        "_README": "key = the exact `metric` string run_audit derived; "
                   "value = {\"day_90\": ..., \"stretch\": ..., \"pace_note\": \"...\"}"
    },
}

CHECKLIST = """# Capture checklist — {client}

Generated {today} by `run_audit.py`. Nothing below is optional; the audit
record stays incomplete until each box is done. **Do not fill a value you did
not see on a screen.**

## Why this is manual

The prompt runs cannot be automated from the build environment. Perplexity,
ChatGPT and Google AI Mode all refuse automated clients — verified from this
sandbox: `403` on plain requests, `ERR_CONNECTION_RESET` from a headless
Chromium. Capture happens in a real, signed-in browser. Two supported ways:

- **Claude in Chrome** — drive your own logged-in browser, one prompt per tab,
  screenshot each answer. Fastest, and the session is real.
- **By hand** — same thing, manually.

Either way the answers land in `prompt-set.json` and the images in `images/`.

---

## 1. Review the prompt set  →  `01-audit/prompt-set.json`

{n_prompts} prompts × {n_engines} engine(s) were generated from the category,
the competitors and the stale positioning. **Read them before running them.**
A cold prompt set produces a generic audit — the record will not be marked
human-reviewed until you re-run with `--reviewed`.

- [ ] Every prompt is one a real buyer would type
- [ ] Delete any that isn't. Add any obvious one that's missing
- [ ] Competitor list matches who the client actually names

## 2. Run each prompt and fill its row

For every object in `prompt-set.json`:

- [ ] `date` — ISO date you ran it
- [ ] `client_named` — `true` / `false`. **Never leave null.**
- [ ] `client_position` — rank in the list, or `null` if unranked/absent
- [ ] `competitors_named` — every brand the answer named, in order
- [ ] `sources_cited` — the domains the engine cited
- [ ] `sentiment` — one of positive / neutral / hedged / negative / n/a
- [ ] `screenshot` — `images/figN.png`. **Required for every `client_named:
      false` row.** An absence claim without a screenshot is the single
      easiest thing in this system to get wrong, and the validator will warn.
- [ ] `verbatim_note` — short and factual. Not interpretation.

## 3. Paste the platform metrics  →  `01-audit/semrush.json`

- [ ] AI Visibility score, mentions + cited pages per engine, totals
- [ ] Authority score, organic traffic + keywords with deltas, backlinks
- [ ] `date` the figures were read
- [ ] If per-engine values disagree with the platform total, keep the
      platform's figure and say whose it is — do not silently reconcile

## 4. Write the interpretation  →  `01-audit/interpretation.json`

- [ ] `recommendations` — 2 to 4 tracks, priority order, each with a
      rationale specific to THIS client
- [ ] `target_commitments` — day-90 and stretch for each derived metric,
      plus the pace note explaining why that row moves fast or slow
- [ ] `positioning_note` — any rebrand or pivot that means the engines
      learned an out-of-date story

## 5. Re-run

    python _system/run_audit.py {url} --reviewed

Validates against the schema and writes `audit-record.json` +
`audit-report.md`. If it refuses, fix the source data — never the check.
"""


# ===========================================================================
# 5. ASSEMBLE + VALIDATE
# ===========================================================================

def validate_record(record) -> list:
    try:
        import jsonschema
    except ImportError:
        print("run_audit: jsonschema not installed — "
              "pip install jsonschema --break-system-packages", file=sys.stderr)
        raise
    schema = json.loads(SCHEMA_PATH.read_text())
    return [f"{'/'.join(map(str, e.path)) or '(root)'} — {e.message}"
            for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(record),
                            key=lambda e: list(e.path))]


def clean_metrics(raw) -> dict:
    """Drop scaffold keys and anything the operator left empty. An empty field
    must not survive as a zero."""
    if not raw:
        return {}
    out = {}
    for k, v in raw.items():
        if k.startswith("_") or v in (None, "", [], {}):
            continue
        if isinstance(v, dict):
            inner = {ik: iv for ik, iv in v.items()
                     if not ik.startswith("_") and iv not in (None, "")}
            if inner:
                out[k] = inner
        else:
            out[k] = v
    return out


def clean_runs(raw) -> tuple[list, list]:
    """Returns (complete runs, complaints). A row missing client_named has not
    been run and is dropped with a note — it never becomes a false."""
    runs, missing = [], []
    for i, r in enumerate(raw or []):
        if r.get("client_named") is None or not r.get("date"):
            missing.append(f"prompt run not completed: \"{r.get('prompt','?')}\" "
                           f"({r.get('engine','?')})")
            continue
        row = {"prompt": r["prompt"], "engine": r["engine"], "date": r["date"],
               "client_named": bool(r["client_named"]),
               "competitors_named": r.get("competitors_named") or []}
        for k in ("prompt_type", "client_position", "sources_cited",
                  "sentiment", "screenshot", "verbatim_note"):
            v = r.get(k)
            if v not in (None, "", []):
                row[k] = v
        runs.append(row)
    return runs, missing


def main() -> int:
    ap = argparse.ArgumentParser(description="Visionary Media AI visibility audit")
    ap.add_argument("url")
    ap.add_argument("--name", help="Client name. Default: derived from the domain.")
    ap.add_argument("--category", help='How THEY describe it, e.g. "UGC ad agency '
                                       'for DTC brands". Drives prompt selection.')
    ap.add_argument("--audience", help='e.g. "DTC brands". Default: parsed from '
                                       '--category after " for ".')
    ap.add_argument("--competitors", default="",
                    help="Comma-separated. Named by the client or on their own site.")
    ap.add_argument("--offering", help='What they SELL, as a buyer would say it, '
                                       'e.g. "UGC video ads". Used for the '
                                       'alternatives and branded prompts. '
                                       'Defaults to --category.')
    ap.add_argument("--stale-category", help="Old positioning the engines may still "
                                             "hold, e.g. \"AI ad generator for "
                                             "ecommerce brands\".")
    ap.add_argument("--engines", default=",".join(DEFAULT_ENGINES),
                    help=f"Comma-separated. Allowed: {', '.join(ALL_ENGINES)}")
    ap.add_argument("--operator", default="", help="Who ran it. Required to write.")
    ap.add_argument("--reviewed", action="store_true",
                    help="You have read the prompt set. Only a human may pass this.")
    ap.add_argument("--root", default=str(ROOT), help="Repo root.")
    ap.add_argument("--out", help="Client dir. Default: <root>/clients/<slug>")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite an existing audit-record.json.")
    a = ap.parse_args()

    url = a.url if a.url.startswith("http") else "https://" + a.url
    name = a.name or domain_of(url).split(".")[0].capitalize()
    cdir = Path(a.out) if a.out else Path(a.root) / "clients" / slugify(name)
    adir = cdir / "01-audit"
    (adir / "images").mkdir(parents=True, exist_ok=True)

    engines = [e.strip() for e in a.engines.split(",") if e.strip()]
    bad = [e for e in engines if e not in ALL_ENGINES]
    if bad:
        print(f"unknown engine(s): {', '.join(bad)}\nallowed: {', '.join(ALL_ENGINES)}")
        return 2

    print(f"── audit: {name} ({url}) ────────────────")

    # -- probe (always re-run; it is cheap and it is the freshest thing here)
    probe = probe_site(url)
    jwrite(adir / "site-probe.json", probe)
    print(f"  probe   homepage {probe['homepage_status']}, robots "
          f"{probe['robots_status']}, {probe['jsonld_blocks']} JSON-LD block(s), "
          f"{len(probe['ai_crawlers_blocked'])} AI crawler(s) blocked")

    # -- prompt set (generate once, never clobber operator edits)
    ps_path = adir / "prompt-set.json"
    competitors = [c.strip() for c in a.competitors.split(",") if c.strip()]
    noun = (a.category or "").split(" for ")[0].strip() or None
    audience = a.audience or (a.category.split(" for ", 1)[1].strip()
                              if a.category and " for " in a.category else None)
    existing_ps = jread(ps_path)
    if existing_ps is None:
        if not noun:
            print("\n  STOP  --category is required to generate the prompt set.\n"
                  '        e.g. --category "UGC ad agency for DTC brands"')
            return 2
        ps = build_prompt_set(name, url, noun, audience, competitors,
                              a.stale_category, engines, offering=a.offering)
        jwrite(ps_path, ps)
        print(f"  wrote   prompt-set.json ({len(ps)} runs to capture)")
    else:
        ps = existing_ps
        print(f"  read    prompt-set.json ({len(ps)} rows)")

    # -- scaffolds
    sem_path, int_path = adir / "semrush.json", adir / "interpretation.json"
    if not sem_path.exists():
        jwrite(sem_path, SEMRUSH_SCAFFOLD)
        print("  wrote   semrush.json (blank — paste the figures)")
    if not int_path.exists():
        jwrite(int_path, INTERPRETATION_SCAFFOLD)
        print("  wrote   interpretation.json (blank — write the tracks)")

    metrics = clean_metrics(jread(sem_path))
    interp = jread(int_path) or {}
    runs, incomplete = clean_runs(ps)

    # -- gate: is there anything to build from?
    if not runs:
        (adir / "CAPTURE-CHECKLIST.md").write_text(CHECKLIST.format(
            client=name, today=date.today().isoformat(), url=url,
            n_prompts=len({r['prompt'] for r in ps}), n_engines=len(engines)),
            encoding="utf-8")
        print(f"\n  wrote   CAPTURE-CHECKLIST.md")
        print(f"\nWAITING — 0 of {len(ps)} prompt runs captured. "
              f"No record written.\n         Work through "
              f"{(adir / 'CAPTURE-CHECKLIST.md').relative_to(Path(a.root))}, then re-run.")
        return 3

    # -- build the record
    gaps, gap_unknowns = derive_gaps(probe, metrics, runs)
    targets_today = derive_targets_today(metrics, runs)

    commitments = (interp.get("target_commitments") or {})
    targets, target_unknowns = [], []
    for t in targets_today:
        c = commitments.get(t["metric"])
        if isinstance(c, dict) and c.get("day_90") not in (None, ""):
            row = {"metric": t["metric"], "today": t["today"], "day_90": c["day_90"]}
            for k in ("stretch", "pace_note"):
                if c.get(k) not in (None, ""):
                    row[k] = c[k]
            targets.append(row)
        else:
            target_unknowns.append(
                f"Day-90 target for \"{t['metric']}\" (today = {t['today']}) — "
                f"a commitment, not a measurement; set it in interpretation.json")

    recs = [r for r in (interp.get("recommendations") or [])
            if r.get("track") and r.get("rationale") and r.get("time_to_impact")
            and r.get("deliverables")]
    recs = [{k: v for k, v in r.items() if v not in (None, "", [])} for r in recs]

    unknowns = gap_unknowns + target_unknowns + incomplete
    if not recs:
        unknowns.append("Recommendation tracks — the interpretation is the product "
                        "and is not derivable from measurement; write them in "
                        "interpretation.json")
    if not metrics:
        unknowns.append("Platform metrics — semrush.json is empty; every metric row "
                        "in the proposal will carry a REPLACE marker")
    for r in runs:
        shot = r.get("screenshot")
        if r["client_named"] is False and not shot:
            unknowns.append(f"Screenshot for absence claim: \"{r['prompt']}\" "
                            f"({r['engine']}) — absence without evidence is not usable")
        elif shot and not (adir / shot).exists():
            unknowns.append(f"Screenshot file missing on disk: {shot} — referenced by "
                            f"\"{r['prompt']}\" ({r['engine']}); the figure will not render")
    if probe["errors"]:
        unknowns += [f"Site probe: {e}" for e in probe["errors"]]

    client = {"name": name, "url": url}
    if a.category:
        client["category"] = a.category
    if competitors:
        client["competitors"] = competitors
    if interp.get("positioning_note"):
        client["positioning_note"] = interp["positioning_note"]

    record = {
        "schema_version": "1.0",
        "client": client,
        "run": {"date": date.today().isoformat(),
                "operator": a.operator or "unattributed",
                "prompt_set_reviewed_by_human": bool(a.reviewed)},
        "platform_metrics": metrics,
        "prompt_runs": runs,
        "gaps": gaps,
        "recommendations": recs,
        "targets": targets,
        "unknowns": unknowns,
    }

    errs = validate_record(record)
    if errs:
        print("\n  INVALID — record not written:")
        for e in errs:
            print(f"    schema: {e}")
        jwrite(adir / "audit-record.REJECTED.json", record)
        print(f"    (rejected draft saved to {adir.name}/audit-record.REJECTED.json)")
        return 1

    rec_path = adir / "audit-record.json"
    if rec_path.exists() and not a.force:
        jwrite(adir / "audit-record.NEW.json", record)
        print(f"\n  REFUSED to overwrite an existing audit-record.json.")
        print(f"          New record written to {adir.name}/audit-record.NEW.json — "
              f"diff it, then re-run with --force.")
        return 3
    jwrite(rec_path, record)

    try:
        write_audit_report(cdir, record)
        print(f"  wrote   01-audit/audit-report.md")
    except Exception as e:                                   # noqa: BLE001
        print(f"  WARN    audit-report.md not written: {e}")

    print(f"  wrote   01-audit/audit-record.json")
    print(f"\n  runs {len(runs)} · gaps {len(gaps)} · tracks {len(recs)} · "
          f"targets {len(targets)} · unknowns {len(unknowns)}")
    if not a.reviewed:
        print("  WARN  prompt set not marked human-reviewed — pass --reviewed "
              "once you have read it")
    for u in unknowns:
        print(f"  unknown  {u}")
    print("\nOK — record written and schema-valid.")
    return 0


# imported late so the module stays importable without the renderer
def write_audit_report(cdir: Path, record: dict):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "render_audit_report", SYS_DIR / "render_audit_report.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.render_markdown(cdir, record)


if __name__ == "__main__":
    sys.exit(main())
