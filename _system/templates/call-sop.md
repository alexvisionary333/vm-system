# Call 1 — SOP

45 minutes. One outcome: a decision, or a booked Call 2 with a named date.

**Before you dial.** Read `01-audit/audit-record.json` end to end, and read
its `unknowns[]` twice. Every unknown is a question you must ask on this call —
the proposal cannot be built until they are answered. Send the audit report
(`01-audit/audit-report.pdf`) only after the walkthrough, never before.

**How to read this document.** Every question has a `→` line naming the exact
field it fills. If a question does not fill a field, it is not on this call.
Write into `02-call/call-notes.md` as you go. Digits, not words — the
validator can only source a number it can see.

`CN §` = a heading in `call-notes.md`. `AR .` = a path in `audit-record.json`.

---

## 0. Frame (2 min)

> "Three things today. What you're trying to hit, what we actually found when
> we ran the questions your buyers ask, and what it would take to change it.
> I'll leave you the audit either way — it's yours, we ran it before you paid
> us anything."

Say the last clause. It is the reason the rest of the call works.

---

## 1. Discovery (12 min) — before you show them anything

Do not open the audit yet. Everything you learn here is what makes the
walkthrough land, and once they have seen the findings they will answer these
questions in your language instead of theirs.

**"What are you trying to hit in the next quarter, and what happens if you
don't?"**
→ `CN § Success metric they named` — the proposal headline is this sentence in
their words. Not the service name.

**"Say that back the way you'd say it to your board."**
→ `CN § What they said (their words)` — verbatim. The opening paragraph of the
proposal is built from this, and it is the only part of the document that
proves someone was on the call.

**"When someone becomes a customer, what are they worth to you on average?"**
→ `CN § Numbers → Average customer value`
Resolves `AR .unknowns[]` "Average customer LTV". Without this figure the
"What it's costing you" section gets deleted, not estimated.

**"And how many of those are you signing a month right now?"**
→ `CN § Numbers → Signups / month`
These two multiply. That product is the only arithmetic in the proposal.

**"Are you spending on ads at the moment, and roughly what?"**
→ `CN § Numbers → Ad spend / month`
Resolves `AR .unknowns[]` "Whether Google Ads spend exists". Ask it plainly if
`AR .platform_metrics.paid_keywords` is 0 — a zero there means either no spend
or spend the tool can't see, and those are different conversations.

**"How long from first conversation to signed, typically?"**
→ `CN § Numbers → Deal cycle (weeks)` — tells you whether a 90-day target is
a real promise or a slow one.

**"Who else has to be comfortable with this before it happens?"**
→ `CN § Who else decides → Named approver` / `Others in the room`
Ask now. Asking it after the price makes it sound like an objection handler.

---

## 2. Audit walkthrough (12 min) — evidence, in this order

Share screen. Work the report top to bottom. **Read what is on the page. Do
not add numbers that are not on it.**

**Open with the discovery prompts.**
→ `AR .prompt_runs[]` where `prompt_type` ∈ category, alternatives, buying_guide

> "These are the questions someone types when they don't know who to hire yet.
> Here's who came back."

Then the single strongest row — usually an `alternatives` prompt naming a
competitor the client names on their own site.

> "This one is the buyer who is already in market. Five names came back. None
> of them was yours."

**Then the branded prompt.**
→ `AR .prompt_runs[]` where `prompt_type` = branded, plus `.sources_cited`

> "Now here's you by name. The engine knows you. Look at where the answer
> comes from — that's a review aggregator, not your site. Your brand-level
> answer is currently being written by third parties."

**Then the scored layers.**
→ `AR .gaps[]` — read `finding`, then `evidence`

Every score on the page shows the arithmetic that produced it. Say so:

> "Nothing here is our opinion. Each score prints its own maths underneath it,
> and every prompt is in a file you can re-run yourself."

**Then stop talking.**

**"Which of these is the one that bothers you?"**
→ `CN § What they reacted to in the audit`
Whatever they name leads the proposal. This is the highest-value answer on the
call and you only get it by shutting up first.

**"Anything here you think is wrong?"**
→ `CN § Objections raised`
Note it verbatim. If they are right, the fix is the record, not the argument.

**Say the unknowns out loud.**
→ `AR .unknowns[]`

> "Three things we deliberately didn't fill in, because we'd have been
> guessing. Here they are."

Reading your own gaps aloud is the cheapest credibility in this call.

---

## 3. Proof (5 min)

→ Source: `_system/case-studies.md`, and **only** that file.

Pick the one case study matched to their situation. Say the numbers as they
are written.

If the service line has no case study, say so first, plainly:

> "We don't have a published AI-visibility case study yet — the practice is
> newer than our SEO work. What I can show you is the same machinery pointed
> at a different surface."

Then IAA: keyword movement in seven weeks, 52→15, 61→12, 58→11, 75→10, 67→9;
new users +31.3%, engaged sessions +25%.

Do not round these. Do not add a number to them. There is no testimonial on
file for any case study — do not imply one.

→ `CN § Objections raised` if the "no case study" admission draws a reaction.

---

## 4. Path and budget (8 min)

Describe the tracks in `AR .recommendations[]` — **shape and sequence only**.
No deliverable counts, no hours, no monthly figure yet.

> "Two tracks. One moves in weeks because it only needs sources to exist that
> we can create. One moves in 60 to 90 days because it depends on third-party
> pages we have to earn. We'd run both, starting with the fast one."

**"What sort of budget did you have in mind for this?"**
→ `CN § Budget range discussed → Range they named`
Resolves `AR .unknowns[]` "Budget range". Ask it before you quote. If they
deflect once, give the band and ask which end they're at.

**Then quote three options.** Say the monthly, the term, and the total
contract value for each. Write all three down while they are on the call.
→ `CN § Pricing quoted on the call` — the table, all cells

> This is the one that blocks builds. A price exists in the audit record
> nowhere and in the case study library nowhere, so `call-notes.md` is the
> only place a price in the proposal can come from. If this table is empty the
> validator will report every figure in the Investment section as unsourced
> and the PDF ships stamped NOT FOR SEND. Six of those, exactly, on the first
> Icon draft.

**"If we start, who's our named approver, and how fast can you turn feedback
around?"**
→ `CN § Access and turnaround → Feedback turnaround (business days)`
→ `CN § Who else decides → Named approver`

**"What would we need access to — CMS, analytics, the review profiles?"**
→ `CN § Access and turnaround → Systems we need access to`
Fills the proposal's "What we need from you" line. Vague here means a stalled
month later.

---

## 5. Ask for the decision (3 min)

Ask once. Then be quiet.

**"Of those three, which one are you leaning toward?"**
→ `CN § Pricing quoted on the call` — mark the leaning option
→ `CN § Who else decides → Decision expected by`

If yes: confirm the option, confirm the approver, tell them what happens
inside two business days.

If not yet:

**"What has to be true for this to be a yes?"**
→ `CN § Objections raised`

**"Who sees it before you decide, and when?"**
→ `CN § Who else decides → Others in the room` / `Decision expected by`

Do not discount. Do not add scope to rescue the call. Either is a decision the
proposal cannot source.

---

## 6. Book Call 2 (3 min)

Never end without a date in a calendar.

**"I'll have the proposal to you by [day]. Let's put 20 minutes in for [day+2]
to walk it through — does the morning work?"**
→ `CN § Call 2 → Booked for`

**"Anything you want in it that we haven't covered?"**
→ `CN § Call 2 → What we owe them before it`

---

## After the call — 10 minutes, same day

1. Finish `02-call/call-notes.md`. Every field or an explicit blank.
2. Re-read `AR .unknowns[]`. Each one is now answered in the notes, or it is
   still open and the proposal will carry a REPLACE marker for it. Both are
   fine. Silently filling it is not.
3. Draft `03-proposal/proposal.md` from the audit record and the notes.
4. `python _system/build.py clients/<name>`
5. If it says BLOCKED, the fix is in the source data. Never in the check.

## The four things that block a build, and where each is fixed

| Blocker | Fix |
|---|---|
| Unsourced number | It was never captured. Go back to `call-notes.md` — usually the pricing table |
| Unresolved placeholder | You owe a field. Answer it or delete the section |
| Schema failure | The audit record is wrong. Re-run `run_audit.py` |
| Stale audit warning (>21 days) | Re-run the prompt set. AI answers move |
