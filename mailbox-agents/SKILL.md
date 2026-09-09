---
name: mailbox-agents
description: Use when testing any flow that sends an email you then need to read — signup verification, invites, magic links, password reset, OTP codes — in any repo. The shared AI-agent test mailbox (agent001…agent005@thecloudassist.com) is readable from the shell via `graph-mail`. Also use when asked "check the test inbox", "did the email arrive", "get the verification link", or when a flow under test stalls at "check your email".
---

# graph-mail — the agent's test inbox

You have a real, deliverable set of email addresses and a CLI that reads the
mailbox they land in. Use them instead of guessing links from logs, seeding
tokens by hand, or asking the user to forward an email.

```
agent001@thecloudassist.com … agent005@thecloudassist.com   → all land in agents@thecloudassist.com
agent001+anything@thecloudassist.com                        → same mailbox, distinct address
```

Tool: `graph-mail` (on PATH; source `~/dev_wsl/infrastructure/tools/graph-mail/`).
Read-only (`Mail.Read`). Server-side only — never call Graph from a page context.

## The pattern — always watermark first

```bash
WM=$(graph-mail now)                                   # BEFORE the app sends anything
ADDR="agent001+$(date +%s)@thecloudassist.com"          # fresh identity per run
# … drive the app (Playwright MCP / curl / UI) to sign up / invite / reset with $ADDR …
graph-mail wait --to "$ADDR" --after "$WM"              # blocks ≤120s, prints body + ranked links
graph-mail links latest --to "$ADDR" --since 5m --best  # just the top URL, for piping
```

Never skip the watermark. Without it a rerun matches the *previous* run's email
and follows a dead link, which looks exactly like an app bug and is not one.

Use a `+tag` per run so "an account with this email already exists" never
blocks a repeat. Matching folds the tag away, so `--to agent001@…` also finds
`agent001+run42@…`.

## Reading what came back

- `wait` / `show` print the **text body** and a **ranked link list**; the `*`
  row is the best guess at the action link. Read the body — a 6-digit OTP code
  is in the text, not in a link.
- Safe Links wrappers are already unwrapped.
- Wrong guess? `--must-contain <app domain>` pins it.
- `show latest --headers` when a message arrived but the recipient looks wrong
  (`Delivered-To`, `Received … for=`).
- `list --since 30m` to see everything recent across Inbox **and** Junk.

## When `wait` times out, read the message — it tells you which bug you have

| It says | It means |
|---|---|
| NO mail at all arrived | Delivery: the app never sent, wrong address, SES/Cognito sandbox, or Defender quarantine. Check the app's outbound log first. |
| mail arrived but none to `<addr>` | Recipient mismatch — run `list` to see who it went to. |
| mail to `<addr>` arrived but the filter excluded it | Your `--subject` / `--from` is too tight. |

## Traps you should recognise on sight

- **"This link has already been used" on a link nobody opened** → Microsoft
  Defender Safe Links pre-visited it and consumed a single-use token. Not the
  app. Needs an Exchange admin to exclude this mailbox from Safe Links. Tell the
  user; do not debug the app's token logic.
- **403 from Graph** shortly after a permission change → Exchange permission
  cache, up to ~2h. Retry later. Persisting past a day → grant or access policy
  is wrong; run `graph-mail check`.
- **Local dev-stub modes usually log the link instead of sending.** If the repo
  you're in has a dev mailer that logs, read the log; the mailbox only matters
  against deployed environments that really send.
- **The mailbox never empties** (read-only credential). Old mail is normal; the
  watermark is what keeps it irrelevant.

## Do not

- Do not paste the client secret anywhere. It lives in the tool's `.env` only.
- Do not point this at any mailbox other than `agents@thecloudassist.com`.
- Do not build an ad-hoc Graph client in a repo — call this tool.
