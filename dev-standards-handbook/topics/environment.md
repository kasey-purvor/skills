# Environment

Traps in the tools and machines every repo shares: Claude Code and its harness, Codex,
Linear, the scraping and search services, git and GitHub, and the machines. Read it
before the first command of a piece of work.

A trap about one repo belongs in that repo's `docs/pitfalls.md`, not here. The test: would it bite in a different repo
too? Then it lives here.

**One line per trap,** in the same shape as a repo's `docs/pitfalls.md`
(`set-up-sdlc/domain.md` gives it):

```
YYYY-MM-DD · <symptom, plainly> → <fix or rule> · seen: N · source: <measured | read in code | an agent's word | the human said>
```

The date is the date the trap was first seen. The same trap again bumps `seen`; it
never gets a second line.

**An inbox, not an archive.** A line stays, with its `seen` count, until the trap is
fixed at its source: a hook, a script, a preflight step or the skill that covers the
tool now stops it. Then the line is deleted. A high count is the sign it is worth fixing.

**Who writes it.** Only the `session-wrap-up` skill, and only lines (and deletions) the
human says yes to. They land as one commit in the skills repo, which the human makes and pushes from
their own profile. Builders and reviewers report traps; they never edit this file.

## Claude Code

Nothing yet.

## Codex

Nothing yet.

## Linear

Nothing yet.

## Scraping and search services (Scrapfly, Serper, Bright Data)

Nothing yet.

## Git and GitHub

Nothing yet.

## Machines (hal, kasey-lt, spark, hal-mini, Tailscale)

2026-11-12 · `docker inspect` of the Spark's model container prints its launch arguments, which include the model's API key → never inspect it whole; ask for one field with `--format` · seen: 1 · source: measured
2026-11-13 · `sudo` on the Spark asks for a password, so an agent cannot run it → put the root steps in a script and hand Kasey the one command (`sudo bash …`, or `! ssh -t spark "sudo bash …"` from the session) · seen: 1 · source: measured
2026-11-13 · node_exporter on the Spark answers its first scrape, then every later one times out → its `cpufreq` collector hangs reading `cpuinfo_cur_freq` on this board; run it with `--no-collector.cpufreq` · seen: 1 · source: measured
2026-11-13 · On the Spark `nvidia-smi` reports no GPU memory totals (the memory is shared with the CPU) and no fan speed, and NVIDIA's own monitor (DCGM) does not support the chip → read temperature, power and clock from `nvidia-smi` (about 10 ms a call) and memory per process from `--query-compute-apps` · seen: 1 · source: measured (nvidia-smi), an agent's word (DCGM, from an NVIDIA forum thread)
2026-11-13 · `ssh spark` now and then fails with "Connection timed out during banner exchange" while the box is healthy → retry, with `-o ConnectTimeout=30` · seen: 1 · source: measured
2026-11-13 · A file bind-mounted on its own into a container still shows the old contents after the file is replaced by a copy (`tar`, `scp`), so a reload reads nothing new → restart the container, or mount the folder · seen: 1 · source: measured
