# The nine gates — what each one is really asking

`vm.py` prints a question at each stop. This is the longer version: what the
operator owes, what goes wrong here, and what a good answer sounds like.

Never approve a gate yourself. Put the question to the person, in their terms.

---

## 1. Scope
**Asks:** is the category, offering and competitor list how the CLIENT would
say it — not how we would?

Three inputs, all from the client's own words or their own site:

- `--category` what they ARE: `UGC ad agency for DTC brands`
- `--offering` what they SELL, as a buyer says it: `UGC video ads`
- `--competitors` who they name themselves, often on their pricing page
- `--stale-category` any prior positioning the engines may still hold

**Goes wrong:** swapping category and offering. "Billo alternatives for UGC ad
agency" is not a sentence anyone types. Also: inventing competitors. If the
client did not name them and they are not on the site, they are not input.

**Stale positioning is a real finding, not trivia.** If a client rebranded,
the engines learned the old story and will keep telling it.

## 2. Prompt set
**Asks:** would a real buyer type these?

Nine prompts across five types. The schema explicitly warns that a cold prompt
set produces a generic audit, and `run_audit.py` will not mark the record
human-reviewed until this gate is signed.

**Read the prompts aloud to the user.** Don't say "review prompt-set.json".
Encourage deletion — a prompt nobody would type is worse than one fewer row.

## 3. Capture
**Asks:** every prompt run in a real browser, answers recorded, screenshots
saved?

See `capture-with-chrome.md`. This gate will not go green while any absence
claim lacks a screenshot or any referenced screenshot is missing from disk.

## 4. Platform metrics
**Asks:** figures pasted, and did you actually see each one?

Pasted by hand into `01-audit/semrush.json`. There is no Semrush API endpoint
for AI visibility data — the manual paste is not laziness, it is the only
option.

**Delete any line you could not read off the screen.** Deleted becomes an
unknown; guessed becomes a lie in a PDF.

Where per-engine values disagree with the platform total, keep the platform's
figure and attribute it. Do not silently reconcile.

## 5. Interpretation
**Asks:** the tracks and the day-90 column.

The one stage with no automation at all, deliberately. `run_audit.py` emits
zero recommendations on its own.

- `recommendations` — 2 to 4 tracks in priority order, each with a rationale
  specific to THIS client
- `target_commitments` — `today` is measured; `day_90` is a promise a person
  makes. The pace note saying why a row moves fast or slow is the paragraph
  competitors cannot copy

Draft options, argue for one, let them choose. Their name on the gate.

## 6. Audit record + report
**Asks:** read the leave-behind end to end.

This is what gets handed over on Call 1. Findings and evidence only — no
pricing, no scope, no plan.

Check the PDF actually rendered: figures present, no REPLACE markers in a
table, unknowns section reads like a list of honest questions rather than
holes.

## 7. Call 1 notes
**Asks:** your notes, however you write them, plus the handful of facts.

Freeform above, tidy below. Do not restructure their prose. Two things are
worth having verbatim because the proposal is built from them: **the outcome
in their words** (becomes the headline) and **which finding they reacted to**
(decides what leads).

## 8. Pricing
**Asks:** the three options as you said them out loud.

`vm.py price <client> 2000/6 4000/6 7000/6` does the contract-value arithmetic
and writes the table.

This is the gate that blocks builds. No price exists anywhere else in the
system by design, so an empty table means every Investment figure reports as
unsourced. That is the check working.

## 9. Proposal
**Asks:** read the built PDF before it goes.

Last stop. A clean validator run means every number traced to a source — it
does **not** mean the document is right. The build will happily pass a
proposal whose audit is half-captured.

That gap is the entire reason these nine gates exist.
