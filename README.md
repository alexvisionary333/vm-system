# Visionary Media — proposal system

One folder. No files move between chats.

## Start here

```
python _system/vm.py            # where every client stands, and the next action
python _system/vm.py serve      # the same thing in a browser, localhost only
```

`vm.py` is the only thing you need to remember. It knows where each client is,
tells you the one next action in plain English, and **refuses to advance a
stage until a person signs it off**. Nine stages, nine stops:

```
Scope → Prompt set → Capture → Platform metrics → Interpretation
      → Audit record + report → Call 1 notes → Pricing → Proposal
```

Each gate records who approved it and when, in `clients/<name>/.pipeline.json`.
`vm.py reopen <client> <stage>` un-approves that stage and everything after it.

A clean validator run means every number traced to a source. It does **not**
mean the document is right — the build will happily pass a proposal whose
audit is half-captured. That gap is why the nine gates exist.

```
_system/                     built once, changed rarely
  visionary_media.py         markdown -> branded PDF
  validate.py                the accuracy checks
  build.py                   the only command anyone runs
  new_client.py              creates the folder tree
  run_audit.py               the AI visibility workflow
  render_audit_report.py     audit-record.json -> the Call 1 leave-behind
  audit-record.schema.json   the contract between workflow and proposal
  case-studies.md            the ONLY sanctioned source for proof numbers
  templates/proposal.md      the blank fill-in
  templates/call-notes.md    the blank fill-in
  templates/audit-report.md  rendered, never hand-edited
  templates/call-sop.md      the Call 1 script

clients/<name>/
  01-audit/
    prompt-set.json          generated, human-reviewed, then filled by capture
    semrush.json             pasted by hand. Blank lines stay blank
    interpretation.json      the tracks and the day-90 column. Human-written
    site-probe.json          measured automatically each run
    CAPTURE-CHECKLIST.md     what the operator still owes
    audit-record.json        written by run_audit.py. Never hand-edited
    audit-report.md / .pdf   the Call 1 leave-behind
    images/                  screenshots referenced by the record
  02-call/
    call-notes.md            written by the rep after Call 1
  03-proposal/
    proposal.md              drafted from 01 + 02
    proposal.pdf             only appears when checks pass
```

## The one command

```
python _system/build.py clients/icon
```

Validates, then renders. If anything fails you still get a PDF so you can read
it — named `proposal-NOT-FOR-SEND.pdf` and stamped across every page. A clean
run produces `proposal.pdf`. There is no flag to skip the check.

## What gets checked

**Schema.** `audit-record.json` must validate. A missing required field is a
hard fail, not a gap the drafter fills in.

**Provenance.** Every metric block carries a source and a date. Any prompt run
claiming the client was absent must carry a screenshot — an absence assertion
without evidence is the easiest thing in the world to get wrong.

**Numbers.** Every number in `proposal.md` must trace to one of exactly three
places: the audit record, the call notes, or the case study library. Anything
else is reported as unsourced and blocks the build.

This is the check that matters. It is the one that catches a plausible figure
that nobody actually measured — a made-up price, a target nobody set, a case
study result off by a digit. Run against the first Icon draft it caught six
invented prices and nothing else.

**Placeholders.** `REPLACE`, `TODO`, `$X`, `[BRACKET]` left in the draft block
the build. So do `unknowns[]` carried out of the audit — they surface as notes
listing exactly what the rep still owes.

**Staleness.** An audit older than 21 days warns. AI answers move.

## Adding a client

```
python _system/new_client.py "Icon" --url https://icon.com
```

Then, in order:

```
# 1. generates the prompt set, probes the site, writes the capture checklist
python _system/run_audit.py https://icon.com --name "Icon" \
    --category "UGC ad agency for DTC brands" --offering "UGC video ads" \
    --competitors "Billo,Soona,Arcads" --operator "your name"

# 2. work 01-audit/CAPTURE-CHECKLIST.md, then re-run to write the record
python _system/run_audit.py https://icon.com ...same flags... --reviewed

# 3. the Call 1 leave-behind
python _system/render_audit_report.py clients/icon

# 4. run Call 1 against _system/templates/call-sop.md, fill call-notes.md
# 5. draft the proposal, then
python _system/build.py clients/icon
```

`run_audit.py` never overwrites an existing `audit-record.json` — it writes
`audit-record.NEW.json` and asks you to diff. `--force` overrides.

### The prompt runs are manual, deliberately

Every AI engine refuses automated clients. Capture happens in a real,
signed-in browser — Claude in Chrome, or by hand — and the answers go back
into `prompt-set.json`. `run_audit.py` does everything either side of that:
prompt generation, the site probe, the scoring, the schema check, the record.

### Where numbers come from

Nothing in the audit record and nothing in the case study library contains a
price. `02-call/call-notes.md` is therefore the ONLY legal source for any
figure in the Investment section. If its pricing table is empty, every price
in the proposal is reported as unsourced and the PDF ships stamped NOT FOR
SEND. Write digits, not words — the validator can only source what it can
parse.

### Scores

Every score in `gaps[]` is computed from a stated formula over measured
inputs, and each one prints its own arithmetic into `evidence[]`. No score is
a judgement call, and a layer whose inputs are missing produces an entry in
`unknowns[]` rather than a number.

## Rules for whoever is drafting

- Keep every heading in the template. Do not add, remove or reorder sections.
- Never write a number that isn't in one of the three sanctioned sources. If
  it isn't there, leave the `REPLACE` marker and list what's missing.
- Proof numbers come only from `_system/case-studies.md`.
- The headline is the outcome in the client's words from the call.
- Pricing: always three options, total contract value always stated.
- If the build says BLOCKED, fix the source data. Do not edit around the check.
