#!/usr/bin/env python3
"""Condense one Claude Code or Codex session, with its subagents, for a session wrap-up.

What the human typed is kept in full, including messages typed while the agent was
working. The agent's own text is truncated, each tool call becomes one line, tool
errors are kept, and system reminders and skill dumps are dropped. Messages from
other agents are labelled as such, so they are never mistaken for the human, and a
compaction summary is reduced to one marker line for the same reason. The reports other
agents send back are kept whole: a builder lists the traps it hit at the end.

A subagent's own transcript is reduced to what the main session never saw: its tool
errors, and its final message when that message did not arrive. Its narration, its brief
and its tool calls are left out; read its transcript with --file to see them. An idle
notice that only repeats a report the agent had just sent becomes one line. Tool errors
seen more than once are counted at the top, across every transcript. A notice that a
background command or monitor finished becomes one line: its summary and its status.

The last line printed says whether the extract will fit: the context of the session
running the script, plus the extract, as a share of the window (--window, in tokens).

  python3 -I extract-session.py --latest [--out PATH]           # this Claude Code session
  python3 -I extract-session.py --codex [--out PATH]            # newest Codex session here
  python3 -I extract-session.py --file PATH.jsonl [--out PATH]  # any one transcript

The output can hold secrets that appeared in the session. Write it to a scratch
folder, never into a repository, and never quote a secret from it.
Standard library only.
"""
import argparse
import glob
import html
import json
import os
import re
import sys

ASSIST_MAX = 900
AGENT_MSG_MAX = 600
ERROR_MAX = 300
HINT_MAX = 160
CHARS_PER_TOKEN = 3.5  # an estimate, on the low side so the extract is not undercounted
WINDOW = 1_000_000  # the context window assumed for the size line; --window changes it
TAIL_BYTES = 4_000_000  # how much of the running session's transcript to read for its last turn
IDLE_KEY = 200  # characters of an idle notice's text compared with a subagent's final message
SENT_SHARE = 0.5  # an idle notice repeats a report when the agent sent a message at least this share of its length
ERR_KEY = 80  # characters, numbers blanked, that make two tool errors the same error
TALLY_MAX = 40  # repeated errors listed in the count at the top

SKIP_PREFIX = ("<local-command-stdout>", "<local-command-caveat>", "Caveat: The messages below",
               "Base directory for this skill:", "# AGENTS.md instructions", "<skills_instructions>",
               "<multi_agent", "<environment_context>", "<turn_aborted>", "<permissions", "<user_shell",
               "<app_context", "<collaboration_mode", "<skill>")
WRAPPER = "Another Claude session sent a message:"  # the harness's line before a teammate's message
AGENT_PREFIX = (WRAPPER, "<teammate-message", "<task-notification", "<agent-message")
REPORT_PREFIX = ("<teammate-message", "<task-notification", "<agent-message")  # results, kept whole
PEER_PREFIX = ("<cross-session-message",)
# A queue "remove" with one of these reasons means the message reached the agent mid-turn.
DELIVERED = ("absorbed_mid_turn", "delivered_to_agent")
COMPACTED = "[compaction summary skipped: an agent's words, not the human's]"
OWN = ("CLAUDE", "CODEX", "TOOL", "TOOL-ERROR", "MARKER")  # turns that are not a message received


def trunc(t, n):
    t = t.strip()
    return t if len(t) <= n else t[:n] + f" …[+{len(t) - n} chars]"


def oneline(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def clean_user(t):
    """Text a person or agent sent, minus harness wrapping; None when nothing is left."""
    if not t or t.lstrip().startswith(SKIP_PREFIX):
        return None
    m = re.search(r"<command-name>(.*?)</command-name>", t, re.S)
    if m:
        args = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
        return f"[slash command] {m.group(1).strip()} {args.group(1).strip() if args else ''}".strip()
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<pasted_content[^>]*>", "[pasted content]\n", t)
    t = re.sub(r"</pasted_content>", "", t)
    t = t.strip()
    return t or None


def speaker(text, human_label):
    """Who a user-role message really came from."""
    if text.startswith(AGENT_PREFIX):
        return "AGENT-MSG"
    if text.startswith(PEER_PREFIX):
        return "PEER-MSG"
    return human_label


def is_report(text):
    """A result another agent sent back to this session."""
    if text.startswith(WRAPPER):
        text = text[len(WRAPPER):].lstrip()
    return text.startswith(REPORT_PREFIX)


def add_user(turns, text, ts, human_label):
    who = speaker(text, human_label)
    if who.startswith("USER") or (human_label.startswith("USER") and is_report(text)):
        body = text
    else:
        body = trunc(text, ASSIST_MAX if who == "PARENT" else AGENT_MSG_MAX)
    turns.append((who, body, ts))


def norm(t):
    return re.sub(r"\s+", " ", t).strip()[:2000]


def withdraw(turns, key):
    """Blank the latest turn showing a queued message that was taken back unsent."""
    for i in range(len(turns) - 1, -1, -1):
        if turns[i] and turns[i][0] not in OWN and norm(turns[i][1]) == key:
            turns[i] = None
            return


def cut_assistant(turns, said, keep_final):
    """Truncate the agent's own text. With keep_final, the last message stays whole."""
    final = set()
    if keep_final and said:
        last_i, last_id = said[-1]  # Claude Code writes one record per block of a message
        final = {i for i, mid in said if last_id and mid == last_id} | {last_i}
    for i, _ in said:
        if i not in final:
            role, text, ts = turns[i]
            turns[i] = (role, trunc(text, ASSIST_MAX), ts)
    return [x for x in turns if x]


def tool_hint(name, inp):
    if not isinstance(inp, dict):
        return trunc(oneline(inp), HINT_MAX)
    if name == "SendMessage":
        return trunc(oneline(f"to {inp.get('to')}: {inp.get('summary') or inp.get('message') or ''}"), HINT_MAX)
    hint = (inp.get("description") or inp.get("prompt") or inp.get("command") or inp.get("file_path")
            or inp.get("message") or inp.get("skill") or inp.get("query") or "")
    return trunc(oneline(hint), HINT_MAX)


def new_meta():
    return {"id": None, "cwd": None, "branch": None, "title": None, "first": None, "last": None,
            "errors": 0, "human_turns": 0, "withdrawn": []}


# ---------- Claude Code ----------
def parse_claude(path, human_label="USER"):
    """human_label is USER for the main session; PARENT in a subagent, whose prompts come from an agent."""
    turns, meta = [], new_meta()
    meta["id"] = os.path.basename(path)[:-len(".jsonl")]
    queued = []  # mid-turn messages, so the copy that is delivered later is not shown twice
    said = []  # (index in turns, message id) of the agent's own text
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            ts = o.get("timestamp")
            if t == "ai-title":
                meta["title"] = o.get("aiTitle") or o.get("title")
            if t == "queue-operation":
                c = clean_user(o.get("content") if isinstance(o.get("content"), str) else "")
                if c and o.get("operation") == "enqueue":
                    queued.append(norm(c))
                    label = "USER (typed mid-turn)" if human_label == "USER" else human_label
                    add_user(turns, c, ts, label)
                elif (c and o.get("operation") == "remove" and o.get("reason") not in DELIVERED
                      and norm(c) in queued):
                    queued.remove(norm(c))
                    withdraw(turns, norm(c))
                    meta["withdrawn"].append(o.get("reason"))
                continue
            if t not in ("user", "assistant"):
                continue
            if ts:
                meta["first"] = meta["first"] or ts
                meta["last"] = ts
            meta["cwd"] = meta["cwd"] or o.get("cwd")
            meta["branch"] = meta["branch"] or o.get("gitBranch")
            content = (o.get("message") or {}).get("content")
            if t == "user":
                if o.get("isCompactSummary") or o.get("isVisibleInTranscriptOnly"):
                    turns.append(("MARKER", COMPACTED, ts))
                    continue
                if o.get("isMeta"):  # skill dumps and other harness-injected text
                    continue
                blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
                for b in blocks:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text":
                        c = clean_user(b.get("text", ""))
                        if not c:
                            continue
                        if norm(c) in queued:
                            queued.remove(norm(c))
                            continue
                        add_user(turns, c, ts, human_label)
                    elif b.get("type") == "tool_result" and b.get("is_error"):
                        meta["errors"] += 1
                        body = b.get("content")
                        if isinstance(body, list):
                            body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                        turns.append(("TOOL-ERROR", trunc(oneline(body), ERROR_MAX), ts))
            else:
                blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
                for b in blocks:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        said.append((len(turns), (o.get("message") or {}).get("id")))
                        turns.append(("CLAUDE", b["text"].strip(), ts))
                    elif b.get("type") == "tool_use":
                        name = b.get("name")
                        turns.append(("TOOL", f"{name}: {tool_hint(name, b.get('input', {}))}", ts))
    return cut_assistant(turns, said, keep_final=True), meta


def claude_subagents(path):
    """The session's subagent transcripts: path, a label from its .meta.json, the name it
    messages under (named ones only) and the id its task notification carries."""
    found = []
    for sub in glob.glob(os.path.join(path[:-len(".jsonl")], "subagents", "*.jsonl")):
        label = os.path.basename(sub)[:-len(".jsonl")]
        try:
            with open(sub[:-len(".jsonl")] + ".meta.json") as fh:
                m = json.load(fh)
            name = m.get("name") or m.get("agentType") or label
            label = f"{name} — {m['description']}" if m.get("description") else name
            sent_as = m.get("name")
        except Exception:
            sent_as = None
        aid = os.path.basename(sub)[:-len(".jsonl")]
        found.append((sub, label, sent_as, aid[len("agent-"):] if aid.startswith("agent-") else aid))
    return found


def latest_claude(cwd):
    root = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:  # its folder is named for the directory it started in, which may not be this one
        found = glob.glob(os.path.join(root, "projects", "*", f"{sid}.jsonl"))
        if not found:
            sys.exit(f"no transcript for this session ({sid}) under {os.path.join(root, 'projects')}")
        return max(found, key=os.path.getmtime), "this session (CLAUDE_CODE_SESSION_ID)"
    folder = os.path.join(root, "projects", re.sub(r"[^A-Za-z0-9]", "-", cwd))
    paths = glob.glob(os.path.join(folder, "*.jsonl"))
    if not paths:
        sys.exit(f"no Claude Code transcripts for {cwd} under {folder}")
    return (max(paths, key=os.path.getmtime),
            "CLAUDE_CODE_SESSION_ID is not set: newest transcript in this folder, maybe another session")


# ---------- Codex ----------
def codex_head(path):
    try:
        with open(path, errors="replace") as fh:
            o = json.loads(fh.readline())
        return o.get("payload", {}) if o.get("type") == "session_meta" else None
    except Exception:
        return None


def parse_codex(path, human_label="USER"):
    turns, meta, said = [], new_meta(), []
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            p = o.get("payload") or {}
            ts = o.get("timestamp")
            if t == "session_meta":
                meta["id"] = p.get("id")
                meta["cwd"] = p.get("cwd")
                meta["branch"] = (p.get("git") or {}).get("branch")
                continue
            if t != "response_item":
                continue
            if ts:
                meta["first"] = meta["first"] or ts
                meta["last"] = ts
            pt = p.get("type")
            if pt == "message":
                role = p.get("role")
                text = " ".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
                if role == "user":
                    c = clean_user(text)
                    if c:
                        add_user(turns, c, ts, human_label)
                elif role == "assistant" and text.strip():
                    said.append((len(turns), None))
                    turns.append(("CODEX", text.strip(), ts))
            elif pt == "agent_message":
                text = " ".join(c.get("text", "") for c in p.get("content", [])
                                if isinstance(c, dict) and c.get("type") == "input_text")
                msg = f"{p.get('author')} → {p.get('recipient')}: {text}"
                turns.append(("AGENT-MSG", msg if human_label == "USER" else trunc(msg, AGENT_MSG_MAX), ts))
            elif pt in ("function_call", "custom_tool_call"):
                arg = p.get("arguments") or p.get("input") or ""
                turns.append(("TOOL", f"{p.get('name')}: {trunc(oneline(arg), HINT_MAX)}", ts))
            elif pt in ("function_call_output", "custom_tool_call_output"):
                out = str(p.get("output", ""))
                if re.search(r"exit_code\"?:\s*[1-9]|exit code:? [1-9]|exited with code [1-9]|script failed",
                             out[:300], re.I):
                    meta["errors"] += 1
                    turns.append(("TOOL-ERROR", trunc(oneline(out), ERROR_MAX), ts))
    return cut_assistant(turns, said, keep_final=True), meta


def codex_sessions():
    return os.path.join(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "sessions")


def codex_rollouts():
    return glob.glob(os.path.join(codex_sessions(), "**", "rollout-*.jsonl"), recursive=True)


def latest_codex(cwd):
    for path in sorted(codex_rollouts(), key=os.path.getmtime, reverse=True):
        head = codex_head(path)
        if head and head.get("cwd") == cwd and head.get("thread_source") != "subagent":
            return path, "newest Codex session started in this directory"
    sys.exit(f"no Codex session for {cwd} under {codex_sessions()}")


def codex_subagents(root_id):
    """Subagent rollouts at any depth carry the top session's id as session_id."""
    found = []
    for path in codex_rollouts():
        head = codex_head(path)
        if head and head.get("session_id") == root_id and head.get("id") != root_id:
            label = head.get("agent_nickname") or head.get("agent_path") or os.path.basename(path)
            if head.get("agent_path") and head.get("agent_nickname"):
                label = f"{head['agent_nickname']} — {head['agent_path']}"
            found.append((path, label, None, None))
    return found


# ---------- write ----------
def stamp(ts):
    return (ts or "")[5:16].replace("T", " ")


def render(turns, tools=True):
    """tools=False leaves out the one line per tool call; errors and messages stay."""
    out = []
    for role, text, ts in turns:
        if role == "TOOL":
            if tools:
                out.append(f"  · {stamp(ts)} [{text}]\n")
        elif role == "TOOL-ERROR":
            out.append(f"  ! {stamp(ts)} TOOL ERROR: {text}\n")
        elif role == "MARKER":
            out.append(f"\n*{text}* {stamp(ts)}\n\n")
        else:  # a heading inside a message must not read as a section of this file
            text = re.sub(r"^#", r"\\#", text, flags=re.M)
            out.append(f"\n**{role}** {stamp(ts)}\n{text}\n\n")
    return "".join(out)


def human_count(turns):
    return sum(1 for r, _, _ in turns if r.startswith("USER"))


# ---------- what reached the manager ----------
BLOCK = re.compile(r"<teammate-message\b([^>]*)>(.*?)</teammate-message>|<agent-message\b([^>]*)>(.*?)</agent-message>",
                   re.S)
TASK = re.compile(r"<task-notification>.*?</task-notification>", re.S)
BOILER = re.compile(r"\n*(?:This came from another Claude session — not typed by your user"
                    r"|That \"other Claude session\" is an agent working inside this same session)[^\n]*")
NOTE = re.compile(r"\s*<note>.*?</note>", re.S)


def attr(attrs, name):
    m = re.search(rf'\b{name}="([^"]*)"', attrs or "")
    return m.group(1) if m else None


def received(turns):
    """Find which subagents' last words reached the main session, and drop what only repeats.

    A named subagent sends its report as a message, then an idle notice that repeats its last
    words. The notice becomes one line when a message of comparable size came from the same
    agent since its previous notice. Otherwise the notice is the report, and it stays whole.
    The harness's own sentences around these messages are dropped, and a notice that a
    background command or monitor finished becomes one line.

    Returns the turns; for each named agent the start of the last idle notice it sent; the
    ids of unnamed agents whose result arrived as a task notification; and the notices cut.
    """
    last_idle, tasks, sent, cut, quiet = {}, set(), {}, 0, 0

    def one(m):
        nonlocal cut
        if m.group(2) is not None:
            who, body = attr(m.group(1), "teammate_id"), m.group(2)
        else:
            who, body = attr(m.group(3), "from"), m.group(4)
        idle = None
        if body.lstrip().startswith("{"):  # the harness's own notices are JSON
            try:
                idle = json.loads(body)
            except Exception:
                idle = None
            if not isinstance(idle, dict) or idle.get("type") != "idle_notification":
                return m.group(0)
        else:
            if body.strip():
                sent[who] = max(sent.get(who, 0), len(body))
            return m.group(0)
        who = idle.get("from") or who
        result = str(idle.get("result") or "")
        before, sent[who] = sent.get(who, 0), 0
        if result:
            last_idle[who] = norm(result)[:IDLE_KEY]
            if before < len(result) * SENT_SHARE:
                return m.group(0)
        cut += 1
        return f"[idle notice from {who}: {'repeats the report it sent above' if result else 'no text'}]"

    def task(m):
        """A subagent's result stays whole. A background command or monitor becomes one line:
        what it carries beyond its summary is tool output, which is dropped everywhere else."""
        nonlocal quiet
        note = m.group(0)
        tid = re.search(r"<task-id>([^<]+)</task-id>", note)
        if "<result>" in note:
            if tid:
                tasks.add(tid.group(1).strip())
            return note
        quiet += 1
        summary = re.search(r"<summary>(.*?)</summary>", note, re.S)
        status = re.search(r"<status>([^<]*)</status>", note)
        said = html.unescape(oneline(summary.group(1))) if summary else "no summary"
        return f"[background: {trunc(said, HINT_MAX)}{' · ' + status.group(1).strip() if status else ''}]"

    out = []
    for role, text, ts in turns:
        if role == "AGENT-MSG":
            text = TASK.sub(task, text)
            text = NOTE.sub("", BOILER.sub("", BLOCK.sub(one, text))).strip()
        out.append((role, text, ts))
    return out, last_idle, tasks, cut


# ---------- subagents ----------
def tally(sources):
    """One line for each tool error seen more than once, across every transcript."""
    seen = {}
    for who, turns in sources:
        for role, text, _ in turns:
            if role == "TOOL-ERROR":
                e = seen.setdefault(re.sub(r"[0-9a-f]{7,}|\d+", "#", text)[:ERR_KEY], [0, set(), text])
                e[0] += 1
                e[1].add(who)
    total = sum(e[0] for e in seen.values())
    if not total:
        return ""
    again = sorted((e for e in seen.values() if e[0] > 1), key=lambda e: -e[0])
    out = [f"\n## Tool errors, counted\n\n{total} in all, {len(seen)} distinct. Each one also appears "
           f"further down, where it happened. Seen more than once:\n\n"]
    for n, who, text in again[:TALLY_MAX]:
        out.append(f"- {n}× in {len(who)} transcript(s): {trunc(text, HINT_MAX)}\n")
    if len(again) > TALLY_MAX:
        out.append(f"- and {len(again) - TALLY_MAX} more seen more than once\n")
    if not again:
        out.append("- none\n")
    return "".join(out)


def subagent_part(parsed, last_idle, tasks, keep_all_finals):
    """A line for every subagent, then only what the main session never saw of each.

    That is its tool errors, and its final message when that message did not arrive. Its
    narration, its brief and its tool calls are left out: read it with --file to see them.
    """
    if not parsed:
        return ""
    folders = {os.path.dirname(sub) for _, _, sub, *_ in parsed}
    roster = [f"\n---\n\n## Subagents ({len(parsed)})\n\n"
              "One line each. A subagent's narration, brief and tool calls are left out; "
              "read its transcript with --file to see them.\n"]
    if len(folders) == 1:
        roster.append(f"Transcripts are in {folders.pop()}\n")
    roster.append("\n")
    blocks, unreported = [], 0
    for n, (first, label, sub, sturns, smeta, name, aid) in enumerate(parsed, 1):
        said = [i for i, (r, _, _) in enumerate(sturns) if r in ("CLAUDE", "CODEX")]
        final = sturns[said[-1]] if said else None
        cut_off = not said or any(r in ("TOOL", "TOOL-ERROR") for r, _, _ in sturns[said[-1] + 1:])
        arrived = bool(final) and not keep_all_finals and (
            aid in tasks or (name is not None and last_idle.get(name) == norm(final[1])[:IDLE_KEY]))
        calls = sum(1 for r, _, _ in sturns if r == "TOOL")
        errors = [t for t in sturns if t[0] == "TOOL-ERROR"]
        if final is None:
            state = "no message of its own"
        elif arrived:
            state = "its final message reached the main session"
        else:
            state = "its final message is below"
            unreported += 1
        if cut_off and final is not None:
            state += "; it stopped on a tool call"
        where = os.path.basename(sub) if not folders else sub
        roster.append(f"{n}. {label} · {stamp(smeta['first'])} to {stamp(smeta['last'])} · {calls} tool calls · "
                      f"{len(errors)} errors · {state} · {where}\n")
        if errors or (final is not None and not arrived):
            blocks.append(f"\n### Subagent {n}: {label}\n\n")
            blocks.append(render(errors))
            if final is not None and not arrived:
                blocks.append(render([(f"{final[0]} (its final message)", final[1], final[2])]))
    return "".join(roster + blocks), unreported


# ---------- size ----------
def last_usage(lines):
    """Tokens in the context at the last turn of a Claude Code transcript, or None."""
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        u = (o.get("message") or {}).get("usage")
        if o.get("type") == "assistant" and not o.get("isSidechain") and isinstance(u, dict):
            n = sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                            "cache_read_input_tokens"))
            if n:
                return n
    return None


def running_context():
    """How full the session running this script is, from its own transcript, or None."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not sid:
        return None
    root = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    found = glob.glob(os.path.join(root, "projects", "*", f"{sid}.jsonl"))
    if not found:
        return None
    path = max(found, key=os.path.getmtime)
    try:
        with open(path, "rb") as fh:
            fh.seek(max(0, os.path.getsize(path) - TAIL_BYTES))
            tail = fh.read().decode("utf-8", "replace").split("\n")[1:]
        n = last_usage(tail)
        if n is None:  # a very long last turn: read the whole file
            with open(path, errors="replace") as fh:
                n = last_usage(fh.read().split("\n"))
        return n
    except OSError:
        return None


def size_line(chars, window):
    """The arithmetic a reader needs before opening the extract: will it fit?"""
    extract = int(chars / CHARS_PER_TOKEN)
    now = running_context()
    if now is None:
        return (f"size: extract about {extract:,} tokens, {extract * 100 // window}% of a {window:,}-token "
                f"window; this session's own context is not known (no CLAUDE_CODE_SESSION_ID transcript)")
    total = now + extract
    return (f"size: this session's context {now:,} tokens + extract about {extract:,} = {total:,}, "
            f"{total * 100 // window}% of a {window:,}-token window")


def main():
    ap = argparse.ArgumentParser(description="Condense a session transcript for a session wrap-up.")
    ap.add_argument("--file", help="one transcript (.jsonl), Claude Code or Codex")
    ap.add_argument("--latest", action="store_true", help="this Claude Code session ($CLAUDE_CODE_SESSION_ID), else the newest for this directory")
    ap.add_argument("--codex", action="store_true", help="the newest Codex session for this directory")
    ap.add_argument("--out", help="write here instead of stdout")
    ap.add_argument("--window", type=int, default=WINDOW,
                    help=f"context window in tokens, for the size line (default {WINDOW:,})")
    args = ap.parse_args()
    if not (args.file or args.latest or args.codex):
        ap.error("name a transcript: --file PATH, --latest, or --codex")
    if args.file and (args.latest or args.codex):
        ap.error("--file names one transcript; leave out --latest and --codex")
    cwd = os.getcwd()

    if args.file:
        path, why = os.path.abspath(os.path.expanduser(args.file)), "given with --file"
        if not os.path.isfile(path):
            sys.exit(f"no transcript file at {path}")
        is_codex = codex_head(path) is not None
    elif args.codex:
        (path, why), is_codex = latest_codex(cwd), True
    else:
        (path, why), is_codex = latest_claude(cwd), False
    print(f"reading {path} ({why})", file=sys.stderr)

    parse = parse_codex if is_codex else parse_claude
    turns, meta = parse(path)
    subs = codex_subagents(meta["id"]) if is_codex else claude_subagents(path)
    parsed = []
    for sub, label, name, aid in subs:
        sturns, smeta = parse(sub, human_label="PARENT")
        parsed.append((smeta["first"] or "", label, sub, sturns, smeta, name, aid))
    parsed.sort(key=lambda x: x[0])
    if not turns and not parsed:
        sys.exit(f"nothing read from {path}: it holds no Claude Code or Codex messages")
    turns, last_idle, tasks, cut = received(turns)
    withdrawn = meta["withdrawn"] + [r for p in parsed for r in p[4]["withdrawn"]]
    if withdrawn:
        print(f"dropped {len(withdrawn)} queued message(s) taken back unsent (reasons: "
              f"{sorted(set(map(str, withdrawn)))}); a reason that means delivered belongs in DELIVERED",
              file=sys.stderr)

    sub_text, unreported = subagent_part(parsed, last_idle, tasks, keep_all_finals=is_codex) if parsed else ("", 0)
    if parsed:
        print(f"subagents: {len(parsed)}; final messages that never reached the main session: {unreported}; "
              f"idle notices cut to one line: {cut}", file=sys.stderr)
    doc = [f"# Session {meta['id']}\n",
           f"- tool: {'codex' if is_codex else 'claude code'}\n- cwd: {meta['cwd']}\n- branch: {meta['branch']}\n",
           f"- title: {meta['title']}\n- from: {meta['first']}\n- to: {meta['last']}\n",
           f"- human turns: {human_count(turns)}  tool errors: {meta['errors']}  subagents: {len(parsed)}\n",
           f"- source: {path}\n",
           tally([("main session", turns)] + [(p[2], p[3]) for p in parsed]),
           "\n---\n", render(turns), sub_text]
    text = "".join(doc)

    if args.out:
        try:
            with open(args.out, "w") as fh:
                fh.write(text)
        except OSError as e:
            sys.exit(f"cannot write {args.out}: {e.strerror}")
        print(f"wrote {args.out}: {human_count(turns)} human turns, {len(parsed)} subagents, "
              f"{len(text):,} characters", file=sys.stderr)
    else:
        sys.stdout.write(text)
    print(size_line(len(text), args.window), file=sys.stderr)


if __name__ == "__main__":
    main()
