# Stage 3 — Capture

The bottleneck, and the reason this system is not fully automated.

## Why it is manual

AI engines refuse automated clients. Verified against Perplexity, ChatGPT and
Google AI Mode: HTTP 403 to plain requests, `ERR_CONNECTION_RESET` to headless
Chromium. Note the honest caveat — those tests ran from a sandboxed cloud
container whose egress is restricted, so **some of that is the sandbox, not
purely bot detection**. On a normal machine the picture is better but not
solved: vanilla headless Playwright is the worst-performing configuration in
every published benchmark.

Two things follow. First, capture belongs in a real, signed-in browser.
Second — and this matters more than the automation question — **an engine's
API answer is not the answer the client's buyer sees.** Perplexity's Sonar API
and Gemini's grounded API both return different results from their web UIs.
Use APIs for a cheap 21-day tripwire between audits; never as the source for
`client_named` in the record.

## Doing it with Claude in Chrome

This is the fastest honest path. Claude in Chrome drives the user's own
browser with their own sessions.

1. Read `clients/<name>/01-audit/prompt-set.json`. Each object is one prompt
   on one engine.
2. `tabs_context_mcp` first, then `tabs_create_mcp` for a fresh tab. Never
   reuse a tab the user is working in.
3. For each prompt: navigate to the engine, enter the prompt, let the answer
   finish rendering, then `get_page_text` for the answer and `computer` for a
   screenshot.
4. Save each screenshot into `clients/<name>/01-audit/images/` as
   `figN.png`. **The filename in the record must match a file that exists** —
   `vm.py` checks the disk, not just the JSON key.
5. Write each row back:

   - `date` — ISO date you ran it
   - `client_named` — `true`/`false`. Never leave `null`, never guess
   - `client_position` — rank in the list, or `null`
   - `competitors_named` — every brand named, in the order given
   - `sources_cited` — the domains the engine cited. A branded query answered
     from review aggregators is a finding in itself
   - `sentiment` — positive / neutral / hedged / negative / n/a
   - `screenshot` — `images/figN.png`
   - `verbatim_note` — short and factual. Not interpretation

6. If an engine throws a CAPTCHA or a login wall, **stop and tell the user**.
   Do not try to work around it, and do not fill the row from what you would
   expect the answer to be. A row left uncaptured becomes an entry in
   `unknowns[]`, which is the correct outcome.

## What "not named" means

Only `false` if you read the whole answer and the brand is absent. Not "it
wasn't in the first paragraph". If the answer is truncated or still streaming,
wait — a premature `false` with a screenshot attached is worse than no data,
because it looks like evidence.

## Worth stealing, not depending on

`PleasePrompto/google-ai-mode-skill` and `google-ai-mode-mcp` (MIT) drive
Patchright with real Chrome against a persistent profile, and return a
structured `sources[]` array that maps directly onto `sources_cited`. Google
AI Mode only. The persistent-profile pattern — solve the CAPTCHA once by hand,
reuse the profile after — is the right shape for this problem.

For ChatGPT and Perplexity web UIs there is no credible open-source capture
tool. Anything marketed as one by Oxylabs, Crawlbase or Scrapeless is an
example snippet calling their paid endpoint.
