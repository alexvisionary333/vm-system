# Capture checklist — Relier

Generated 2026-08-27 by `run_audit.py`. Nothing below is optional; the audit
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

8 prompts × 1 engine(s) were generated from the category,
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

    python _system/run_audit.py https://relier.com/ --reviewed

Validates against the schema and writes `audit-record.json` +
`audit-report.md`. If it refuses, fix the source data — never the check.
