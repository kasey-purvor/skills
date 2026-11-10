---
name: livetest
description: Run one review round of the Vantage web-presence enrichment on fresh companies — a Results tester, a Truth tester and a Personas tester, one subagent each, in sequence — and turn their reports into one ranked list with a cutoff. Use after every lane merges in an enrichment stream, and whenever Kasey asks for the enrichment to be tested.
---

# livetest — one review round of web-presence enrichment

Three subagents, one after the other, on the same fresh draw of companies. Each is an outside user
and auditor of the running system, never a part of it. They never see fix briefs or builder reports;
they get this skill, the round number and the draw. Fresh agents every round. The builder of a lane
never tests it.

Announce at start: "Running livetest round N."

## The orchestrator's part

1. **Draw.** ~30 companies the rounds have never used, stratified: 3 large plcs; 8 SMEs with
   distinctive names; 6 micro companies (one or two officers); 3 very common names; 2 charities or
   CICs; 2 LLPs; 2 dormant or recently dissolved; 2 trading under a name other than the registered
   one; 2 registered at an accountant's address. Use the draw script if the repo has one
   (`scripts/livetest-draw.*`); otherwise query the register in the shared DB. Record the draw and
   the reason for each pick in `scratchpad/livetest-r<N>-draw.md`. Keep a `scratchpad/livetest-used.txt`
   so no company is drawn twice. The 40-company regression set (`apps/enrichment-eval`, chosen in
   the first round from the old 220 to cover the shapes) is separate and runs with the Results tester
   every round.
2. **Dispatch Results, wait; dispatch Truth, wait; dispatch Personas, wait.** Opus, general-purpose,
   each with: this skill's path, the round number, the draw file, the shared rules below, and its
   section. Tell each to write its report to `scratchpad/livetest-r<N>-<results|truth|personas>.md`
   AND send it in full to its parent session (SendMessage to `main` — the orchestrator is the
   parent; a made-up name will be refused).
3. **Consolidate** the three into one ranked list (the shape at the end), apply the cutoff, post the
   list as one comment on the stream ticket, and spin up one fix lane per theme. Record every drop
   with a line saying why.
4. **Evolve the schema.** Each round, ask: what did a tester need that the data or the tab didn't
   have (a certainty, the reason for a verdict, a "listed on", a conflict, a date seen)? Add it to
   the next lane's brief. The stored and shown fields are a living thing until the rounds stop
   asking for new ones.
5. **Convergence.** The loop ends when a round yields nothing past the cutoff. Say so on the stream
   ticket with the round number.

## Shared rules (paste into every tester's prompt)

- Repo `/home/kasey/dev_wsl/projects/vantage`. Read `AGENTS.md` "Journeys from a worktree": run the
  API in dev mode (`AUTH_MODE=dev`, `AUTH_DEV_USER_EMAIL=agent001+livetest@thecloudassist.com`,
  loopback, a spare port) against the SHARED live database, and Vite on a spare port
  (`VANTAGE_WEB_PORT`). The live site is behind Cloudflare Access and you cannot sign in — use the
  dev-mode route. The live `enrich-worker` processes what the Results tester queues.
- A worktree of your own if you need a checkout (`.claude/worktrees/livetest-<role>-r<N>`), on main,
  no commits, no pushes, no PRs; never write in the main checkout; remove nothing you didn't make.
- Never run `docker compose` against project `vantage`; never touch or print `.env`, keys or
  tokens; no Codex.
- **Privacy:** never put a private person's name, phone, email or address in a report, a file name
  or a screenshot caption — say "a director", "a named person", counts. Company names and numbers
  are fine. Delete any raw dump you make.
- **Budget and pace:** only the Results tester runs enrichment; at most the draw plus the 40-set;
  one company at a time (the provider pace lives in the DB); wait for each to settle.
- Read enough of the design to say where the intent is wrong, not only where the code misses it:
  the stream ticket's spec (VAN-302 and the current spec comment), `apps/web/src/routes/
  company-web-presence-tab.tsx`, `enrichment-words.ts`, `canonical-enrichment-record/src/*`,
  `apps/public-api/src/enrichment-routes.ts`, ADR-0014.
- Report EVERYTHING: good, bad, confusing, slow, ugly, wrong, missing. Rank by harm to a reader.
  Evidence on every finding (a number, the UI's own words, a screenshot path, a company number).
  One-line fix suggestions at most; the orchestrator cuts the tickets.

## Results tester — the finder's scorecard

Queue each drawn company through the API (`POST …/enrichment`, both kinds), one at a time, waiting
for the status to settle; time each. Also run the 40-set. For every company record: the outcome per
source (own / listing / turned down / undecided / none / failed), what was held (counts by group),
every candidate with its basis and the reason it was turned down or left undecided
(`enrichment_source_matches`), elapsed seconds, provider calls and credits (the `raw` schema).

Then establish the truth yourself: open the real website and LinkedIn page (WebFetch or the
Scrapfly tools), look for the ties the judge accepts — the company number on the page, the
registered name with the registered postcode, a link from a confirmed page — and say for each
verdict: right, a miss (their real page was a candidate and was refused, or was never a
candidate), or a false claim. For every miss, the rule that would have caught it. Precision and
recall per source over the draw and over the 40-set (the regression number: it must not fall).
Worker log lines at warn or error (`docker compose logs enrich-worker` is read-only and fine).
Anything slow, anything that cost more than it should.

**While an agentic finder exists** (its ticket says how to run it): run it on the same draw and the
40-set, score it the same way, and add a table — per company, which finder was right, what each cost,
and where each wins by company shape.

## Truth tester — the statement auditor

For every company that holds statements after this round's runs: read what was held (statements,
page texts, LinkedIn readings, locations, site-named people — counts only for people), fetch the
real pages, and judge each statement: TRUE; WRONG; ABOUT SOMEONE ELSE (a subsidiary, parent,
franchisee, a different firm on the same page); the receipt not on the page it claims; DUPLICATE of
another; STALE; wrong VOICE (the company's words vs a third party's); wrong FIELD. The reader's
soft fields: faithful or embellished; read from the right region (never a menu, footer or legal
page); any prompt text leaked into data. People: roles right, details attributed to the right
person, any category of personal data that shouldn't be held (category and count, never the
detail). Tally true / wrong / unverifiable / duplicate / about-someone-else by group and by source.
A false statement shown as the company's own words is always severity 1.

## Personas tester — a reader with a goal, then the cold read

Run the real frontend. Playwright at 1280 and 390 px. Two passes on the companies that landed:

1. **A salesperson prospecting.** "Here are eight of this round's companies. For each, find how to
   reach them, what they do and how big they are; write an opening line for three." Judge: time per
   company; whether the tab is trusted and why; what helped; what was noise; where you had to look
   elsewhere (the register tabs, the real site); whether the certainty and the reason for a verdict
   were clear enough to act on. Say whether the objective was met: yes / partly / no.
2. **The cold read, as a UX/UI reviewer.** Hierarchy (what is first, what should be); the amount of
   stuff; repetition; the receipts; every state's words (not asked, queued, running, mixed,
   landed, undecided, none found, failed, the refresh cap); the buttons; the empty states; the
   phone; consistency with the rest of the company page; axe accessibility; how long the tab takes
   to paint. Screenshots of each state you reach to `scratchpad/livetest-r<N>-shots/`, named.
   Also look outside the tab: hero, search cards, People — anything leaking or duplicated.

## The report (all three)

1. Headline: three sentences a busy owner reads first.
2. Findings, ranked: what, where (company number, field, screenshot), evidence, why it matters,
   severity (wrong / misleading / confusing / ugly / slow / nit).
3. What's good — specifically, so the fixes don't break it.
4. Tallies and the list of companies with their numbers.
5. Fields a reader needed that weren't there.
6. Open questions for Kasey.

## The consolidated list (the orchestrator's comment on the stream ticket)

```markdown
## Round N — <date, time>
Draw: <n> companies (<file>). Results: website P x/y R x/y (40-set R …); LinkedIn …
Truth: website <n> distinct, <%> true; LinkedIn …  Personas: objective met <yes/partly/no>, <minutes>/company.

### Past the cutoff (fix this round)
1. <theme> — <what, where, evidence, who saw it> → lane <ticket>
### Below the cutoff (waiting)
- …
### Dropped
- <what> — <why>
### Fields asked for
- …
### New this round / seen before
- new: … / repeat: … (convergence: <n> new)
```
