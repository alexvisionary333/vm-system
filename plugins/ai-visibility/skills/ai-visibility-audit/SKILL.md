---
name: ai-visibility-audit
description: >-
  Run Visionary Media's AI visibility workflow — audit a client's presence in
  AI answers, produce the Call 1 leave-behind, and build the proposal. Use when
  the user says any of — run an AI visibility audit, audit a client, GEO audit,
  AEO audit, check if a brand shows up in ChatGPT or Perplexity, new client,
  prep for a sales call, build the proposal, what's next for this client — or
  when they name a client folder in the vm-system repo. Also use for "where is
  X in the pipeline", "approve this stage", and "add the pricing from the
  call". Do NOT use for general SEO keyword work or for writing marketing copy.
license: MIT
compatibility: Requires the vm-system repo checked out locally, Python 3.11+, and jsonschema, weasyprint, markdown, cairosvg installed.
---

# AI visibility audit

You are operating a system that puts numbers in front of paying clients. The
system's whole design premise is that **a plausible number nobody measured is
worse than a blank**. Your job is to move a client through nine stages without
ever filling a blank yourself.

## The one command

Everything routes through `_system/vm.py`. Run it with no arguments to see
where every client stands and what the single next action is:

```
python _system/vm.py
```

Then follow what it says. It is the source of truth about state — **do not
infer a client's status by reading files yourself.**

| The user wants | Run |
|---|---|
| "where are we" / "what's next" | `vm.py` or `vm.py status <client>` |
| a new client | `vm.py new "Name" --url https://…` |
| to run/re-run the audit | `vm.py audit <client>` |
| to approve the current stage | `vm.py ok <client> --by "<their name>"` |
| the Call 1 leave-behind | `vm.py report <client>` |
| pricing from the call | `vm.py price <client> 2000/6 4000/6 7000/6` |
| the proposal | `vm.py build <client>` |
| to redo an approved stage | `vm.py reopen <client> <stage>` |
| a browser panel instead of a terminal | `vm.py serve` |

## The nine stages, and the two that are yours

1. Scope · 2. Prompt set · 3. Capture · 4. Platform metrics ·
5. Interpretation · 6. Audit record + report · 7. Call 1 notes ·
8. Pricing · 9. Proposal

**Stage 3 (Capture) is the one you can actually do for them** — see
`references/capture-with-chrome.md`. Everything else you either run a command
for, or you help them think.

**Stage 5 (Interpretation) is the one you must NOT do alone.** The tracks and
the day-90 targets are the judgement the client is paying for. Draft options
and argue for them, but the human decides and the human's name goes on the
gate.

## The gates are the point

Every stage ends at a stop. `vm.py` will show `STOP FOR REVIEW` with a
specific question. **Put that question to the user in their own terms and wait
for an actual answer.** Never run `vm.py ok` on your own initiative, and never
pass `--by` a name the user did not give you — the gate record is who takes
responsibility for what shipped.

If they seem unsure what they're approving, show them the thing rather than
the filename: read them the prompts, describe what the report says, quote the
finding. "Review prompt-set.json" is not a question a person can answer.

## The rules that do not bend

1. **Never invent a number.** Every figure in a client document must trace to
   the audit record, the call notes, or `_system/case-studies.md`. If it is
   not in one of those three, it does not go in.
2. **Anything undetermined goes in `unknowns[]`, verbatim.** An unknown is a
   feature. It becomes a question on the call and a REPLACE marker in the
   proposal. Never quietly fill one.
3. **An absence claim needs a screenshot.** "The engine didn't name them" is
   the easiest thing in this system to get wrong.
4. **If the build says BLOCKED, fix the source data — never the check.** Do
   not edit the validator, do not delete the failing line to make it pass, do
   not move a number to dodge a rule. If a price is unsourced, the answer is
   that the pricing was never written into the call notes.
5. **Prices only ever come from the call notes.** No price exists in the audit
   record or the case study library. The user adds them after the meeting,
   because they get spoken aloud.
6. **No scores.** Findings state what is true and what is concretely absent,
   with the measurements underneath. A 0-100 grade is a number we invented
   about data we already have — it invites the client to argue with the score
   instead of the facts, and it is the one figure that cannot be traced to a
   source. If you catch yourself writing "38/100", write what is missing
   instead.
7. **Do not change the brand tokens** in `_system/visionary_media.py`.

## Notes are freeform, facts are not

`02-call/call-notes.md` has a `## My notes` section the user writes however
they like — prose, fragments, a pasted transcript. Do not restructure it and
do not ask them to fill in a form.

Only the `## Facts` block needs to be tidy, and only because `validate.py`
parses digits out of it. If they give you their notes in chat, put the prose
in `## My notes` verbatim and lift only the figures into `## Facts`. If a
figure was not said, leave it blank — blank is a REPLACE marker, which is a
to-do; a guess is a wrong number in a PDF.

## When it blocks

`BLOCKED — N issue(s)` still produces a PDF so it can be read, named
`proposal-NOT-FOR-SEND.pdf` and stamped on every page. Read the FAIL lines to
the user and say which of the three sources the number should have come from.
Almost always the answer is the pricing table in the call notes.

## Verify before you claim it worked

After `vm.py report` or `vm.py build`, the PDF exists but nobody has looked at
it. If you can, rasterise page 1 and actually look:

```
python -c "import pypdfium2 as p; d=p.PdfDocument('<file>.pdf'); \
d[0].render(scale=1.3).to_pil().save('/tmp/p1.png')"
```

A figure that fell back to raw `**Fig 1.**` text, or a table of REPLACE
markers, is a real failure that exits 0.

## Reference files

- `references/capture-with-chrome.md` — Stage 3, the manual bottleneck, and
  how to drive it with Claude in Chrome
- `references/stages.md` — what each gate is really asking, and what the
  operator owes at each one
