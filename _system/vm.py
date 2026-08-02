#!/usr/bin/env python3
"""
VISIONARY MEDIA — the one thing you run
=======================================

    python _system/vm.py                 what needs doing, across every client
    python _system/vm.py serve           the same thing, in a browser

Everything else is optional. `vm.py` knows where each client is in the
pipeline, tells you the single next action in plain English, and refuses to
let a stage advance until a person has signed it off.

    vm.py new "Icon" --url https://icon.com
    vm.py status [client]
    vm.py next <client>              what to do right now
    vm.py audit <client>             re-run the audit (flags are remembered)
    vm.py review <client>            open the current gate for sign-off
    vm.py ok <client> [--by NAME]    approve the current gate
    vm.py price <client> 2000/6 4000/6 7000/6
    vm.py report <client>            render the Call 1 leave-behind
    vm.py build <client>             validate + render the proposal
    vm.py serve [--port 8765]        local control panel, no internet needed

NINE STAGES, NINE STOPS
-----------------------
Every stage has two conditions: the files are ready, AND a person said so.
The second one is the point. Nothing reaches a client because a script
thought it was fine.

Stage flags are remembered in `clients/<name>/.pipeline.json`, so you type
the long `run_audit.py` command once and never again.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import webbrowser
from datetime import datetime, date
from pathlib import Path

SYS_DIR = Path(__file__).resolve().parent
ROOT = SYS_DIR.parent
CLIENTS = ROOT / "clients"

# ---------------------------------------------------------------------------
# the pipeline
# ---------------------------------------------------------------------------
# key, label, what a person is actually being asked to check at this gate
STAGES = [
    ("scope", "Scope",
     "Is the category, offering and competitor list how the CLIENT would say "
     "it — not how we would?"),
    ("prompts", "Prompt set",
     "Read the prompts. Would a real buyer type these? Delete any that miss, "
     "add any that are obviously absent."),
    ("capture", "Capture",
     "Every prompt run in a real browser, answers recorded, screenshots saved. "
     "Absence claims need a screenshot."),
    ("metrics", "Platform metrics",
     "Semrush figures pasted. Anything you could not read on screen stays "
     "blank — blank becomes an unknown, guessed becomes a lie."),
    ("interpretation", "Interpretation",
     "The tracks and the day-90 column. This is the judgement part and it is "
     "the part clients pay for."),
    ("audit", "Audit record + report",
     "Read the leave-behind end to end. This is what you hand them on Call 1."),
    ("call", "Call 1 notes",
     "Your notes from the call, however you write them, plus the handful of "
     "facts the proposal needs."),
    ("pricing", "Pricing",
     "The three options as you said them out loud on the call. No price "
     "exists anywhere else in this system."),
    ("proposal", "Proposal",
     "Read the built PDF before it goes. This is the last stop."),
]
STAGE_KEYS = [s[0] for s in STAGES]
LABEL = {k: l for k, l, _ in STAGES}
ASK = {k: a for k, _, a in STAGES}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def jread(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return default


def jwrite(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")


def pipeline_path(cdir):
    return Path(cdir) / ".pipeline.json"


def load_pipeline(cdir):
    return jread(pipeline_path(cdir), {}) or {}


def save_pipeline(cdir, p):
    jwrite(pipeline_path(cdir), p)


def all_clients():
    if not CLIENTS.exists():
        return []
    return sorted(d for d in CLIENTS.iterdir()
                  if d.is_dir() and not d.name.startswith("_"))


def blank(v):
    if v in (None, "", [], {}):
        return True
    if isinstance(v, dict):
        return all(blank(x) for k, x in v.items() if not k.startswith("_"))
    if isinstance(v, list):
        return all(blank(x) for x in v)
    if isinstance(v, str):
        return not v.strip() or v.strip().upper().startswith("REPLACE")
    return False


def run(cmd, cwd=ROOT):
    """Run a subprocess and stream nothing — return (code, combined output)."""
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ---------------------------------------------------------------------------
# readiness — what the files say, independent of who approved what
# ---------------------------------------------------------------------------

def readiness(cdir) -> dict:
    """For each stage: (ready: bool, detail: str)."""
    cdir = Path(cdir)
    a, c, p = cdir / "01-audit", cdir / "02-call", cdir / "03-proposal"
    pipe = load_pipeline(cdir)
    out = {}

    cfg = pipe.get("config", {})
    out["scope"] = (bool(cfg.get("category")),
                    "category, offering and competitors set"
                    if cfg.get("category") else
                    "no --category yet: run `vm.py audit <client> --category ...` once")

    ps = jread(a / "prompt-set.json", [])
    out["prompts"] = (bool(ps), f"{len({r['prompt'] for r in ps})} prompts generated"
                      if ps else "not generated yet")

    if ps:
        done = [r for r in ps if r.get("client_named") is not None and r.get("date")]
        shots_needed = [r for r in done if r.get("client_named") is False
                        and not r.get("screenshot")]
        shots_missing = [r for r in done if r.get("screenshot")
                         and not (a / r["screenshot"]).exists()]
        detail = f"{len(done)} of {len(ps)} runs captured"
        if shots_needed:
            detail += f"; {len(shots_needed)} absence claim(s) with no screenshot"
        if shots_missing:
            detail += f"; {len(shots_missing)} screenshot file(s) missing on disk"
        out["capture"] = (bool(done) and not shots_needed and not shots_missing, detail)
    else:
        out["capture"] = (False, "waiting on the prompt set")

    sem = jread(a / "semrush.json", {})
    out["metrics"] = (not blank(sem),
                      "figures pasted" if not blank(sem) else "semrush.json still blank")

    it = jread(a / "interpretation.json", {}) or {}
    tracks = [t for t in (it.get("recommendations") or []) if t.get("track")]
    commits = {k: v for k, v in (it.get("target_commitments") or {}).items()
               if not k.startswith("_") and isinstance(v, dict) and v.get("day_90")
               not in (None, "")}
    out["interpretation"] = (bool(tracks),
                             f"{len(tracks)} track(s), {len(commits)} day-90 target(s)"
                             if tracks else "no tracks written yet")

    rec = jread(a / "audit-record.json")
    if rec:
        n = len(rec.get("unknowns") or [])
        rep = (a / "audit-report.md").exists()
        out["audit"] = (rep, f"record written, {n} unknown(s)"
                        + ("" if rep else "; report not rendered"))
    else:
        out["audit"] = (False, "no audit record yet")

    notes_p = c / "call-notes.md"
    notes = notes_p.read_text(encoding="utf-8") if notes_p.exists() else ""
    # look only inside the freeform section — the Facts block and the pricing
    # table filling up must not read as "the rep wrote up the call"
    clean = re.sub(r"<!--.*?-->", "", notes, flags=re.S)
    m = re.search(r"##\s*My notes(.*?)(?=\n##\s|\Z)", clean, re.S | re.I)
    prose = re.sub(r"[\s\-–—>|#*_]+", "", m.group(1) if m else "")
    facts = [ln for ln in clean.splitlines()
             if re.match(r"^\s*-\s*[A-Za-z].*:\s*\$?\s*\S", ln)]
    has_notes = len(prose) > 80
    detail = (f"{len(prose)} chars of notes, {len(facts)} fact(s) filled"
              if has_notes else
              ("Facts filled but the notes section is empty"
               if facts else "no notes yet"))
    out["call"] = (has_notes, detail)

    # only count prices the operator actually wrote — never the worked examples
    # inside the template's own <!-- comments -->
    prices = re.findall(r"\$\s?([\d,]*\d)", re.sub(r"<!--.*?-->", "", notes, flags=re.S))
    out["pricing"] = (len(prices) >= 3,
                      f"{len(prices)} figure(s) in the notes"
                      if prices else "no prices recorded — `vm.py price` or type them in")

    if (p / "proposal.md").exists():
        code, _ = run([sys.executable, str(SYS_DIR / "validate.py"), str(cdir)])
        out["proposal"] = (code == 0,
                           "validator clean" if code == 0 else "validator blocking")
    else:
        out["proposal"] = (False, "no proposal drafted")
    return out


def status_of(cdir) -> list:
    """[(key, state, detail, approver)] where state is one of
    waiting / review / done."""
    ready = readiness(cdir)
    gates = load_pipeline(cdir).get("gates", {})
    rows, blocked = [], False
    for k in STAGE_KEYS:
        is_ready, detail = ready[k]
        g = gates.get(k)
        if g:
            state = "done"
        elif is_ready and not blocked:
            state = "review"
        else:
            state = "waiting"
        if state != "done":
            blocked = True
        rows.append((k, state, detail, (g or {}).get("by", "")))
    return rows


def current_gate(cdir):
    for k, state, detail, _ in status_of(cdir):
        if state != "done":
            return k, state, detail
    return None, "done", "every stage signed off"


# ---------------------------------------------------------------------------
# next-action advice, in plain English
# ---------------------------------------------------------------------------

HOWTO = {
    "scope": lambda c, cfg: (
        f'Tell the system what they sell:\n'
        f'  python _system/vm.py audit {c} \\\n'
        f'      --category "<how THEY describe it> for <audience>" \\\n'
        f'      --offering "<what a buyer would call the product>" \\\n'
        f'      --competitors "<who they name on their own site>"'),
    "prompts": lambda c, cfg: (
        f'Open clients/{c}/01-audit/prompt-set.json and read the prompts.\n'
        f'Edit freely — delete what misses, add what is obviously absent.\n'
        f'Then: python _system/vm.py ok {c}'),
    "capture": lambda c, cfg: (
        f'Run each prompt in a real, signed-in browser and fill its row in\n'
        f'clients/{c}/01-audit/prompt-set.json. Claude in Chrome does this well.\n'
        f'Screenshots go in 01-audit/images/. Every "not named" needs one.\n'
        f'Checklist: clients/{c}/01-audit/CAPTURE-CHECKLIST.md'),
    "metrics": lambda c, cfg: (
        f'Paste the Semrush figures into clients/{c}/01-audit/semrush.json.\n'
        f'Delete any line you cannot read off the screen.'),
    "interpretation": lambda c, cfg: (
        f'Write the tracks and the day-90 column in\n'
        f'clients/{c}/01-audit/interpretation.json.\n'
        f'This is the judgement part — the script deliberately writes none of it.'),
    "audit": lambda c, cfg: (
        f'python _system/vm.py audit {c}      (writes the record)\n'
        f'python _system/vm.py report {c}     (renders the leave-behind)\n'
        f'Then read the PDF end to end before you sign it off.'),
    "call": lambda c, cfg: (
        f'Run Call 1 against _system/templates/call-sop.md.\n'
        f'Afterwards paste your notes — however you write them — into\n'
        f'clients/{c}/02-call/call-notes.md. Prose is fine.\n'
        f'Only the FACTS block at the bottom needs to be tidy.'),
    "pricing": lambda c, cfg: (
        f'Add the three options you quoted out loud:\n'
        f'  python _system/vm.py price {c} 2000/6 4000/6 7000/6\n'
        f'(monthly/term-in-months). Or just type them into the notes.'),
    "proposal": lambda c, cfg: (
        f'Draft clients/{c}/03-proposal/proposal.md from the record and the notes,\n'
        f'then: python _system/vm.py build {c}\n'
        f'If it blocks, fix the source data — never the check.'),
}


def next_action(cdir):
    c = Path(cdir).name
    cfg = load_pipeline(cdir).get("config", {})
    key, state, detail = current_gate(cdir)
    if key is None:
        return "done", "Every stage signed off. Nothing outstanding.", ""
    if state == "review":
        return ("review",
                f"STOP FOR REVIEW — {LABEL[key]}\n\n{ASK[key]}\n\nWhat the files say: {detail}",
                f"python _system/vm.py ok {c}")
    return "work", f"{LABEL[key]} — {detail}\n\n{HOWTO[key](c, cfg)}", ""


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_new(a):
    code, out = run([sys.executable, str(SYS_DIR / "new_client.py"), a.name]
                    + (["--url", a.url] if a.url else []))
    print(out.strip())
    cdir = CLIENTS / slugify(a.name)
    p = load_pipeline(cdir)
    p.setdefault("client", a.name)
    p.setdefault("config", {})
    if a.url:
        p["config"]["url"] = a.url
    p.setdefault("gates", {})
    save_pipeline(cdir, p)
    print()
    cmd_next(argparse.Namespace(client=slugify(a.name)))
    return code


def _resolve(name):
    d = CLIENTS / slugify(name)
    if not d.exists():
        print(f"no client '{name}'. Known: "
              f"{', '.join(c.name for c in all_clients()) or '(none)'}")
        sys.exit(2)
    return d


def cmd_audit(a):
    cdir = _resolve(a.client)
    p = load_pipeline(cdir)
    cfg = p.setdefault("config", {})
    for k in ("url", "category", "offering", "competitors", "stale_category",
              "engines", "operator"):
        v = getattr(a, k, None)
        if v:
            cfg[k] = v
    if not cfg.get("url"):
        print("need --url once (it is remembered afterwards)")
        return 2
    if not cfg.get("category"):
        print('need --category once, e.g. --category "UGC ad agency for DTC brands"')
        return 2
    save_pipeline(cdir, p)

    cmd = [sys.executable, str(SYS_DIR / "run_audit.py"), cfg["url"],
           "--name", p.get("client", cdir.name), "--out", str(cdir),
           "--category", cfg["category"]]
    for flag, key in (("--offering", "offering"), ("--competitors", "competitors"),
                      ("--stale-category", "stale_category"),
                      ("--engines", "engines"), ("--operator", "operator")):
        if cfg.get(key):
            cmd += [flag, cfg[key]]
    # the prompt-set gate IS the human review the schema asks about
    if p.get("gates", {}).get("prompts"):
        cmd.append("--reviewed")
    if a.force:
        cmd.append("--force")
    code, out = run(cmd)
    print(out.rstrip())
    print()
    cmd_next(argparse.Namespace(client=cdir.name))
    return 0 if code in (0, 3) else code


def cmd_report(a):
    cdir = _resolve(a.client)
    code, out = run([sys.executable, str(SYS_DIR / "render_audit_report.py"), str(cdir)])
    print(out.rstrip())
    return code


def cmd_build(a):
    cdir = _resolve(a.client)
    code, out = run([sys.executable, str(SYS_DIR / "build.py"), str(cdir)])
    print(out.rstrip())
    return code


def cmd_price(a):
    """vm.py price icon 2000/6 4000/6 7000/6  — monthly/term."""
    cdir = _resolve(a.client)
    notes = cdir / "02-call" / "call-notes.md"
    if not notes.exists():
        print(f"no {notes}")
        return 2
    names = (a.names.split(",") if a.names else
             ["Option A", "Option B", "Option C"])
    rows = []
    for i, spec in enumerate(a.options):
        if "/" not in spec:
            print(f"'{spec}' should be monthly/term, e.g. 2000/6")
            return 2
        monthly, term = spec.split("/", 1)
        monthly, term = int(monthly.replace(",", "")), int(term)
        nm = names[i].strip() if i < len(names) else f"Option {chr(65+i)}"
        rows.append(f"| {chr(65+i)} | {nm} | ${monthly:,} | {term} months | "
                    f"${monthly*term:,} |")
    block = ("| Option | Name | Monthly | Term | Total contract value |\n"
             "|---|---|---|---|---|\n" + "\n".join(rows))
    text = notes.read_text(encoding="utf-8")
    stamp = f"\n<!-- written by vm.py price on {date.today().isoformat()} -->\n"
    if "## Pricing quoted on the call" in text:
        head, _, tail = text.partition("## Pricing quoted on the call")
        rest = re.split(r"\n## ", tail, maxsplit=1)
        after = ("\n## " + rest[1]) if len(rest) > 1 else ""
        text = head + "## Pricing quoted on the call\n" + stamp + block + "\n" + after
    else:
        text += "\n\n## Pricing quoted on the call\n" + stamp + block + "\n"
    notes.write_text(text, encoding="utf-8")
    print(f"wrote {len(rows)} option(s) into {notes.relative_to(ROOT)}\n")
    print(block)
    return 0


def cmd_ok(a):
    cdir = _resolve(a.client)
    key, state, detail = current_gate(cdir)
    if key is None:
        print("nothing left to approve.")
        return 0
    if state != "review":
        print(f"{LABEL[key]} is not ready yet — {detail}\n")
        cmd_next(argparse.Namespace(client=cdir.name))
        return 1
    p = load_pipeline(cdir)
    p.setdefault("gates", {})[key] = {
        "by": a.by or "unattributed",
        "at": datetime.now().isoformat(timespec="seconds"),
        "saw": detail,
    }
    save_pipeline(cdir, p)
    print(f"✓ {LABEL[key]} approved by {a.by or 'unattributed'}\n")
    cmd_next(argparse.Namespace(client=cdir.name))
    return 0


def cmd_reopen(a):
    cdir = _resolve(a.client)
    p = load_pipeline(cdir)
    g = p.get("gates", {})
    if a.stage not in g:
        print(f"{a.stage} is not approved. Stages: {', '.join(STAGE_KEYS)}")
        return 2
    for k in STAGE_KEYS[STAGE_KEYS.index(a.stage):]:
        g.pop(k, None)
    save_pipeline(cdir, p)
    print(f"reopened {a.stage} and everything after it.\n")
    cmd_next(argparse.Namespace(client=cdir.name))
    return 0


MARK = {"done": "✓", "review": "→", "waiting": "·"}


def cmd_status(a):
    targets = [_resolve(a.client)] if a.client else all_clients()
    if not targets:
        print("no clients yet.  python _system/vm.py new \"Name\" --url https://…")
        return 0
    for cdir in targets:
        rows = status_of(cdir)
        done = sum(1 for r in rows if r[1] == "done")
        print(f"\n── {cdir.name}  ({done}/{len(rows)} signed off) "
              f"{'─' * max(0, 28 - len(cdir.name))}")
        for k, state, detail, by in rows:
            line = f"  {MARK[state]} {LABEL[k]:<22} {detail}"
            if by:
                line += f"   [{by}]"
            print(line)
    print()
    if a.client:
        cmd_next(argparse.Namespace(client=Path(targets[0]).name))
    return 0


def cmd_next(a):
    cdir = _resolve(a.client)
    kind, msg, cmd = next_action(cdir)
    bar = "═" * 58
    print(f"{bar}\nNEXT — {cdir.name}\n{bar}\n{msg}")
    if cmd:
        print(f"\n  {cmd}")
    print()
    return 0


def cmd_dash(a):
    """Bare `vm.py` — everything, and the one thing to do next."""
    cs = all_clients()
    if not cs:
        print("No clients yet.\n\n  python _system/vm.py new \"Icon\" "
              "--url https://icon.com")
        return 0
    print("\nVISIONARY MEDIA — pipeline\n")
    for cdir in cs:
        rows = status_of(cdir)
        done = sum(1 for r in rows if r[1] == "done")
        key, state, detail = current_gate(cdir)
        bar = "".join(MARK[r[1]] for r in rows)
        head = ("all stages signed off" if key is None
                else ("REVIEW: " + LABEL[key]) if state == "review"
                else LABEL[key] + " — " + detail)
        print(f"  {cdir.name:<16} {bar}  {done}/{len(rows)}  {head}")
    waiting = [c for c in cs if current_gate(c)[1] == "review"]
    print()
    for c in waiting:
        cmd_next(argparse.Namespace(client=c.name))
    if not waiting:
        cmd_next(argparse.Namespace(client=cs[0].name))
    return 0


# ---------------------------------------------------------------------------
# serve — the control panel, stdlib only, localhost only
# ---------------------------------------------------------------------------

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Visionary Media — pipeline</title>
<style>
:root{--ink:#17171B;--paper:#FBF9F5;--navy:#1B3A5C;--alert:#9C3226;--mute:#6b6b70}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
 font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:48px 28px 80px}
h1{font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:var(--navy);
 font-weight:600;margin:0 0 32px}
.card{background:#fff;border:1px solid #e8e4dc;border-radius:10px;
 padding:22px 24px;margin-bottom:18px}
.card h2{margin:0 0 4px;font-size:20px;font-weight:600}
.sub{color:var(--mute);font-size:13px;margin-bottom:16px}
ol{list-style:none;margin:0;padding:0}
li{display:flex;gap:12px;align-items:flex-start;padding:7px 0;
 border-top:1px solid #f0ece4;font-size:14px}
li:first-child{border-top:0}
.m{width:18px;flex:none;font-weight:700;text-align:center}
.done .m{color:var(--navy)} .review .m{color:var(--alert)} .waiting .m{color:#cfcbc3}
.waiting{color:#a5a19a}
.lab{width:170px;flex:none;font-weight:500}
.det{color:var(--mute);font-size:13px}
.by{color:var(--navy);font-size:12px;margin-left:auto;white-space:nowrap}
.gate{background:#fff8f4;border:1px solid #f0d9cd;border-left:4px solid var(--alert);
 border-radius:8px;padding:18px 20px;margin-top:16px}
.gate h3{margin:0 0 6px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;
 color:var(--alert)}
.gate p{margin:0 0 14px}
pre{background:#f6f3ee;border-radius:6px;padding:12px 14px;overflow-x:auto;
 font-size:12.5px;margin:10px 0 0;white-space:pre-wrap}
button{background:var(--navy);color:#fff;border:0;border-radius:6px;
 padding:9px 18px;font-size:14px;font-weight:500;cursor:pointer}
button:hover{background:#2E5580}
button.ghost{background:transparent;color:var(--mute);border:1px solid #ddd8d0}
input{border:1px solid #ddd8d0;border-radius:6px;padding:8px 11px;font-size:14px;
 margin-right:8px}
form{display:inline}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px}
.out{background:#17171B;color:#e8e4dc;border-radius:8px;padding:16px 18px;
 font:12.5px/1.5 ui-monospace,Menlo,monospace;white-space:pre-wrap;margin-bottom:22px}
a{color:var(--navy)}
</style></head><body><div class="wrap">
<h1>Visionary Media · pipeline</h1>
{{OUT}}{{BODY}}
<p style="color:var(--mute);font-size:12.5px;margin-top:40px">
Local only — nothing here leaves this machine. Stop with Ctrl-C.</p>
</div></body></html>"""


def _html_client(cdir):
    rows = status_of(cdir)
    done = sum(1 for r in rows if r[1] == "done")
    key, state, detail = current_gate(cdir)
    lis = []
    for k, st, det, by in rows:
        lis.append(f'<li class="{st}"><span class="m">{MARK[st]}</span>'
                   f'<span class="lab">{LABEL[k]}</span>'
                   f'<span class="det">{det}</span>'
                   + (f'<span class="by">{by}</span>' if by else "") + "</li>")
    gate = ""
    if key is None:
        gate = ('<div class="gate" style="border-left-color:#1B3A5C;'
                'background:#f4f7fa;border-color:#d8e3ee">'
                '<h3 style="color:#1B3A5C">Complete</h3>'
                '<p>Every stage signed off.</p></div>')
    elif state == "review":
        gate = (f'<div class="gate"><h3>Stop for review — {LABEL[key]}</h3>'
                f'<p>{ASK[key]}</p>'
                f'<p class="det">What the files say: {detail}</p>'
                f'<form method="post" action="/ok" class="row">'
                f'<input type="hidden" name="client" value="{cdir.name}">'
                f'<input name="by" placeholder="your name" required>'
                f'<button type="submit">Approve {LABEL[key]}</button></form></div>')
    else:
        _, msg, _ = next_action(cdir)
        body = msg.split("\n\n", 1)[-1]
        gate = (f'<div class="gate" style="border-left-color:#1B3A5C;'
                f'background:#f4f7fa;border-color:#d8e3ee">'
                f'<h3 style="color:#1B3A5C">Next — {LABEL[key]}</h3>'
                f'<pre>{body}</pre>'
                f'<form method="post" action="/run" class="row">'
                f'<input type="hidden" name="client" value="{cdir.name}">'
                f'<button name="what" value="audit" type="submit">Run audit</button>'
                f'<button class="ghost" name="what" value="report" type="submit">'
                f'Render report</button>'
                f'<button class="ghost" name="what" value="build" type="submit">'
                f'Build proposal</button></form></div>')
    return (f'<div class="card"><h2>{cdir.name}</h2>'
            f'<div class="sub">{done} of {len(rows)} stages signed off</div>'
            f'<ol>{"".join(lis)}</ol>{gate}</div>')


def cmd_serve(a):
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs
    state = {"out": ""}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _page(self):
            cs = all_clients()
            body = ("".join(_html_client(c) for c in cs) if cs else
                    '<div class="card"><h2>No clients yet</h2>'
                    '<div class="sub">Create one from the terminal:</div>'
                    '<pre>python _system/vm.py new "Icon" --url https://icon.com</pre>'
                    '</div>')
            out = (f'<div class="out">{state.pop("out", "")}</div>'
                   if state.get("out") else "")
            html = PAGE.replace("{{BODY}}", body).replace("{{OUT}}", out)
            state["out"] = ""
            b = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            self._page()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            f = parse_qs(self.rfile.read(n).decode())
            client = (f.get("client") or [""])[0]
            cdir = CLIENTS / slugify(client)
            if cdir.exists():
                if self.path == "/ok":
                    ns = argparse.Namespace(client=cdir.name,
                                            by=(f.get("by") or ["unattributed"])[0])
                    import io
                    import contextlib
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        cmd_ok(ns)
                    state["out"] = buf.getvalue().strip()
                elif self.path == "/run":
                    what = (f.get("what") or ["audit"])[0]
                    script = {"audit": "run_audit.py", "report": "render_audit_report.py",
                              "build": "build.py"}[what]
                    if what == "audit":
                        import io
                        import contextlib
                        buf = io.StringIO()
                        with contextlib.redirect_stdout(buf):
                            cmd_audit(argparse.Namespace(
                                client=cdir.name, url=None, category=None,
                                offering=None, competitors=None,
                                stale_category=None, engines=None,
                                operator=None, force=False))
                        state["out"] = buf.getvalue().strip()
                    else:
                        _, o = run([sys.executable, str(SYS_DIR / script), str(cdir)])
                        state["out"] = o.strip()
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

    srv = HTTPServer(("127.0.0.1", a.port), H)
    url = f"http://127.0.0.1:{a.port}/"
    print(f"Visionary Media control panel → {url}\nCtrl-C to stop.")
    if not a.no_open:
        try:
            webbrowser.open(url)
        except Exception:                                    # noqa: BLE001
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(prog="vm.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    n = sub.add_parser("new"); n.add_argument("name"); n.add_argument("--url", default="")
    n.set_defaults(fn=cmd_new)

    au = sub.add_parser("audit"); au.add_argument("client")
    for f in ("--url", "--category", "--offering", "--competitors",
              "--stale-category", "--engines", "--operator"):
        au.add_argument(f, default=None)
    au.add_argument("--force", action="store_true"); au.set_defaults(fn=cmd_audit)

    for name, fn in (("report", cmd_report), ("build", cmd_build), ("next", cmd_next)):
        s = sub.add_parser(name); s.add_argument("client"); s.set_defaults(fn=fn)

    st = sub.add_parser("status"); st.add_argument("client", nargs="?")
    st.set_defaults(fn=cmd_status)

    o = sub.add_parser("ok"); o.add_argument("client"); o.add_argument("--by", default="")
    o.set_defaults(fn=cmd_ok)
    rv = sub.add_parser("review"); rv.add_argument("client"); rv.set_defaults(fn=cmd_next)

    ro = sub.add_parser("reopen"); ro.add_argument("client"); ro.add_argument("stage")
    ro.set_defaults(fn=cmd_reopen)

    pr = sub.add_parser("price"); pr.add_argument("client")
    pr.add_argument("options", nargs="+", help="monthly/term, e.g. 2000/6")
    pr.add_argument("--names", default="", help="comma-separated option names")
    pr.set_defaults(fn=cmd_price)

    sv = sub.add_parser("serve"); sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--no-open", action="store_true"); sv.set_defaults(fn=cmd_serve)

    a = ap.parse_args()
    if not a.cmd:
        return cmd_dash(a)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main() or 0)
