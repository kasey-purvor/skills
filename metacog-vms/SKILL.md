---
name: metacog-vms
description: How to reach MetacogAI's two production servers from Kasey's machine (the MyDams VM `dams` and the Orbit ETL box `orbit`), reload the SSH key agent after a reboot, read the Supabase Management API read-only through the MyDams VM, and the standing rules on both boxes. Use when a task needs `ssh dams` or `ssh orbit`, a read on either box, Supabase project facts for MyDams or Orbit, or when SSH to them fails. Only for MetacogAI work (MyDams, Orbit) in the `freelance` profile; in any other profile or for any other client, do not use it.
---

# MetacogAI VMs: reaching `dams` and `orbit`

## Scope gate (check first)

This skill applies only when **both** hold: `echo $CLOUD_PROFILE` prints `freelance` (`$GH_CONFIG_DIR` ends in `gh-freelance`), and the work is for MetacogAI (MyDams or Orbit). In the `work` or `personal` profile, or for any other client, these hosts are not yours to reach: stop and say so.

## Quick start

```bash
ssh -o BatchMode=yes -o ConnectTimeout=20 dams  'id -un; sudo -n whoami'    # MyDams production VM
ssh -o BatchMode=yes -o ConnectTimeout=40 orbit 'id -un; sudo -n whoami'    # Orbit production ETL box
```

Nothing else goes on the command: no key path, no password, no environment variable. Both print `kasey` then `root`. Verified 2026-11-05 on `dams` and 2026-11-03 on `orbit` via exactly these commands.

## The two hosts

| Alias | Address | What it is | Login | Project rules |
|---|---|---|---|---|
| `dams` | 188.245.80.20 | MyDams production: ETL timers, pdf-engine, render worker, journey gate. `/opt/mydams-v2` is production, `/home/dams/mydams-dev` the dev clone. | `kasey`, passwordless sudo | repo `CLAUDE.md` and `AGENTS.md` in mydams-dealer-delight |
| `orbit` | 159.195.65.109 | Orbit production ETL: cron as user `orbit` runs `/opt/orbit-sales-insight` **from its working tree**. Shared box with a self-hosted GitHub runner. | `kasey`, passwordless sudo | repo `CLAUDE.md` rule 16 and ADR 0005 in orbit-sales-insight |

The repo files are authoritative for what may be done on each box; this skill only gets you there.

## The key agent

The key is `~/.ssh/id_ed25519`, loaded in an agent at `/tmp/kasey-ssh-agent.sock`; the `Host dams` and `Host orbit` entries in `~/.ssh/config` reach it through the symlink `~/.ssh/agent.sock`, so no `SSH_AUTH_SOCK` is needed. The agent dies when the machine reboots. If `ssh` fails with `Permission denied (publickey)`, Kasey reloads it in a real terminal (the passphrase is typed there and is never given to or accepted by an agent):

```bash
ssh-agent -a /tmp/kasey-ssh-agent.sock >/dev/null
SSH_AUTH_SOCK=/tmp/kasey-ssh-agent.sock ssh-add ~/.ssh/id_ed25519
```

Check with `SSH_AUTH_SOCK=/tmp/kasey-ssh-agent.sock ssh-add -l` (one ED25519 key, comment `kasey-metacogai`).

## Rules on both boxes

1. **`orbit`: one attempt per command, never retry a failed login.** The box runs fail2ban; a second failure can lock Kasey out. On failure, stop and report.
2. **Both are production. Read-only unless Kasey has given the word for a specific change.** Any change on `orbit` also needs Moses's go (the working tree is the live ETL; never move its checked-out ref). Never restart or stop units you did not start.
3. **`dams` is slow to answer during full journey runs**: use `-o ConnectTimeout=40`. Every login session there is capped at 1920 MB RAM, so run no builds or test suites on it.
4. **Secrets: names, never values.** `grep -oE '^[A-Z_]+=' file` is fine; `grep KEY file` is not. Never put a credential on a command line (`argv` is world-readable). Pass secrets by file or stdin, read in-process.
5. **Orbit production database: no heavy diagnostics between 07:00 and 18:00 UK** (no `EXPLAIN ANALYZE`, no tenant-wide scans); use SIT (Moses, 5 Nov 2026).
6. Subagents do not SSH. The orchestrating session makes the one attempt and passes the output on.

## Supabase Management API, read-only, through `dams`

The `dams` user on the MyDams VM holds a working Supabase login whose token sees every project in the org, including Orbit's. The token on Kasey's own machine (`~/.supabase/access-token`) is dead (HTTP 401, checked 2026-11-05). Helpers in `/home/dams/bin/` read the token in-process and never print it:

```bash
ssh dams 'sudo -u dams -H python3 /home/dams/bin/sb-api.py /v1/projects'                       # any GET
ssh dams 'sudo -u dams -H python3 /home/dams/bin/sb-sql.py <project-ref> /path/on/dams/q.sql'  # one read-only statement, 20 s timeout
ssh dams 'sudo -u dams -H python3 /home/dams/bin/sb-logs.py <project-ref> "<clickhouse sql>" [minutes]'  # logs endpoint
```

Project refs: MyDams production `bdoudwpljaibyudqddes`; Orbit production `rxwoxwjvputmlaxulkoz`, SIT branch `qrdsujrjxmcwylivdnla`, DEV branch `mgbvzsurgebwbgdakwdy`. The logs endpoint is `/v1/projects/{ref}/analytics/endpoints/logs?sql=...` with ClickHouse SQL over one `logs` table filtered by `source` (`postgres_logs`, `edge_logs`, `function_logs`, ...); it throttles, so back off on HTTP 429. If a helper is missing, recreate it as a short Python script using `urllib`, reading `~/.supabase/access-token` in-process, with `read_only: true` and a `BEGIN READ ONLY ... ROLLBACK` wrapper for SQL.

## When it fails

| Symptom | Meaning | Do |
|---|---|---|
| `Permission denied (publickey)` | agent not loaded (reboot) | ask Kasey to run the reload above; do not retry `orbit` |
| connect timeout on `dams` | full journey run in progress | wait, retry with `-o ConnectTimeout=40` |
| connect timeout on `orbit` | box or fail2ban | stop; report; one attempt only |
| `HTTP 401` from a helper | the `dams` user's Supabase login expired | report; Kasey re-logs in as `dams` with the CLI |
