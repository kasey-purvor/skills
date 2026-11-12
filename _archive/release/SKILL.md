---
name: release
description: How code reaches DEV, SIT and production for Orbit and MyDams, and what an agent may do at each step. Use before merging, promoting, deploying, releasing, rolling back, refreshing SIT, or touching a VM, and when a ticket or human asks "is this live", "deploy this" or "what is on SIT". Repo CLAUDE.md files hold the per-app facts; this skill holds the procedure.
---

# Release

> **DRAFT v2, 29 Oct 2026.** For Kasey to read before adoption. Matches `REQUIREMENTS.md` v2 in `/home/kasey/dev_wsl/audits/2026-10-23-cicd/`. The Orbit half describes what runs today (ADR 0015 there). The MyDams half describes the target. The design for both apps is that a merge deploys DEV only. MyDams has no DEV yet, so today a MyDams merge reaches the live site, and Moses's "Release rule" block in that repo's CLAUDE.md lists the steps after a merge.

## The model, in one paragraph

Each app has three environments. **DEV** (development) receives every merge to `main` automatically. **SIT** (system integration testing) receives one commit when a person presses **Promote to SIT**, and holds it until the next press. **Production** receives a commit only when a person presses **Deploy to Production**; the workflow refuses any commit that is not the one SIT holds now (except a rollback), whose CI was red, or whose ETL rehearsal status is missing or red. Every environment is pinned to a commit SHA. Production's released commit is the newest `deploy-prod.yml` run on `main` whose jobs all succeeded; GitHub deployment records are not trusted, because Vercel and scheduled jobs write them too. Vercel builds nothing from Git; every website deploy is created by a workflow for an exact commit. The ETL on each app's VM follows the production release by pulling it, and ETL changes are rehearsed against SIT first.

## What is live where

Build order for the missing rows (DAMS-482, MET-867): safety-net tests (lane A) in both apps in parallel throughout, and an Orbit nightly gates nothing until it is green. Steps 1 to 3 (labelled environments, guards in block mode, release buttons) are MyDams copying what Orbit already has; after step 3 a MyDams merge reaches DEV only. Step 4 (nightly SIT refresh and freshness check) and step 5 (VM release folders, then the ETL rehearsal) are built on Orbit first, then copied to MyDams. Step 6 (record) follows each app's step 5.

| | Orbit | MyDams |
|---|---|---|
| What a merge to `main` does | deploys DEV only (`deploy-dev.yml`) | reaches the live site until step 3 switches Vercel's Git deploys off (verified 29 Oct: `ab37520e` got a Production deployment from `vercel[bot]` at 18:30 UTC). Moses does the remaining steps by hand |
| Promote to SIT | live (`deploy-sit.yml`) | not built |
| Deploy to Production, gated on SIT | live (`deploy-prod.yml`, `scripts/release-gates.mjs`) | not built |
| Refresh SIT from production | live (`refresh-sit.yml`; today it re-promotes `main`'s tip afterwards) | not built; will copy Orbit's method (recreate the `sit` branch, strip Vault keys, neutralise) |
| Environment labels | Edge Functions and GitHub `dev`/`sit` only; the rest in step 1 | step 1 |
| Side-effect guards (block mode) | Edge Functions only; ETL in step 2 | step 2 |
| ETL release folder on the VM | not built; the checkout is the runtime (ADR 0005) | not built; `/opt/mydams-v2` checkout is the runtime |
| ETL rehearsal on SIT | not built | not built |
| Pre-merge journey gate | n/a | live (`MyDams journey gate` status on #682 to #688, seen 29 Oct via `gh pr view`) |

Update this table in the same PR as the change it describes. A "live" row carries its proof (`verified <date> via <command>`).

## Rules for agents

1. **Buttons, not hands.** Never run `supabase db push`, `supabase functions deploy`, `vercel deploy`, a migration runner, `git merge` on a VM checkout, or a systemd restart against SIT or production from a shell. The workflows do those. On MyDams today the hand steps are Moses's (rule 3).
2. **One PR at a time per repo.** Merge each before opening the next. Do not stack.
3. **Know what a merge does.** The design for both apps is that a merge deploys DEV only, and on Orbit that is how it works. MyDams has no DEV yet, so a MyDams merge reaches the live site today. Only Moses can merge there (or the one session he names). After a merge he applies migrations, checks the served bundle's commit, fast-forwards `/opt/mydams-v2` and waits for the full journey run to go green. Do not ask anyone to bypass that.
4. **Promote only on the human's word.** Press Promote to SIT only when Kasey has said so for that commit. Then check SIT (Orbit: the SIT smoke; the Tier 2 nightly is not a usable signal until it is rewired). If `main` moved after the press, production will refuse; ask before promoting again.
5. **Release only what SIT holds.** Deploy to Production takes `confirm=deploy`. It refuses a commit SIT does not hold, a red CI, a missing or red rehearsal status (a status saying "skipped: no ETL path in diff" is fine), and on Orbit, once MET-867 lane A2 lands, a commit without green authz nightly evidence since the last schema change.
6. **Read SIT results the way the gate does.** Red on SIT while the same read-only check is green on production: the change broke it, block. Red on both: pre-existing or data, warn and report. SIT stale: refresh, then re-run. Until the promotion checks freshness itself, refresh SIT before a promotion that will be checked against data. A failed refresh, a publication-guard hold or a warn result: stop and tell Kasey; never pick resume inputs or accept a guard drop yourself. Refresh never writes to production.
7. **Rollback is a re-release.** Re-run Deploy to Production for the previous commit; it accepts an older commit only if that workflow released it green before. Migrations are never rolled back. On the VM the puller follows the newest green release run. On MyDams today, roll back with a revert PR through the journey gate.
8. **A human presses production.** Agents prepare, verify and report. Pressing Deploy to Production, or asking a peer session to press it, needs Kasey's explicit instruction for that commit. Overnight, Orbit work merges to `main` and stops; MyDams work stops at an open, reviewed PR.
9. **Say which environment.** Every claim of "deployed", "live" or "on SIT" names the environment, the commit SHA and the command or page that proved it. "Merged" is not "live".
10. **Treat DEV and SIT as able to reach real people today.** Each environment will carry a label (`MYDAMS_ENV` / `ORBIT_ENV`: `dev`, `sit`, `prod`) from step 1, and side-effect guards that read it will block from their first release in step 2. Only `prod` may send email, phone, Graph, IFS writes, order submission or Horizon writes; a missing or unknown label may not. The Supabase project ref is a cross-check: a `prod` label on any database but production's (MyDams `bdoudwpljaibyudqddes`, Orbit `rxwoxwjvputmlaxulkoz`), or a `dev`/`sit` label on production's, refuses to start. Only Orbit's Edge Functions have a guard today. Until step 2 lands, never run ETL or send anything from DEV or SIT on the assumption that a guard will stop it. If you find a path that bypasses a guard, stop and raise it as a security finding.

## Step by step

**Ship a change.** Branch off `origin/main` with the ticket id in the name. Open the PR, get CI green, run the change review (global review policy). Orbit: merge and confirm the DEV deployment went green. MyDams: stop; Moses merges and releases. Record the outcome on the ticket.

**Promote to SIT** (on Kasey's word). `gh workflow run deploy-sit.yml --ref main` (Orbit; MyDams equivalent once built). Wait for green. Read the SIT checks and the rehearsal status. Record the SIT SHA on the stream ticket.

**Release to production** (on Kasey's word for that SHA). `gh workflow run deploy-prod.yml --ref main -f confirm=deploy`. Watch the run. Then verify the served bundle's commit and the backend it names, and read the post-deploy checks. Record the production SHA and the evidence on the ticket.

**Refresh SIT.** `gh workflow run refresh-sit.yml` (Orbit). Today it re-promotes `main`'s tip afterwards, so check which SHA SIT holds before asking for a production release. The target is that a refresh re-promotes the SHA SIT held before.

**ETL change.** Same as any change up to SIT. On promotion, the VM rehearses the affected syncs from the candidate SHA against SIT, compared with production's released SHA, and posts a status; production refuses while it is red or missing. After a production release the VM pulls the SHA of the newest fully green `deploy-prod.yml` run on `main` and flips `current`; check the VM's reported SHA and the unit journal, not the checkout.

## Where the facts are

- Orbit: `docs/adr/0015-environments-and-production-promotion.md`, the top block of `CLAUDE.md`, Linear runbook "Deployment workflow".
- MyDams: `CLAUDE.md` "Release rule" (Moses, 23 to 26 Oct 2026) until the pipeline lands; then the ADR written in DAMS-482 step 6.
- Requirements and decisions: `/home/kasey/dev_wsl/audits/2026-10-23-cicd/REQUIREMENTS.md` (v2).
- Streams building the missing rows: DAMS-482 (MyDams), MET-867 (Orbit, all steps).
