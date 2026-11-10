#!/usr/bin/env python3
"""Condense one Claude Code or Codex session, with its subagents, for a session review.

What the human typed is kept in full, including messages typed while the agent was
working. The agent's own text is truncated, each tool call becomes one line, tool
errors are kept, and system reminders and skill dumps are dropped. Messages from
other agents are labelled as such, so they are never mistaken for the human, and a
compaction summary is reduced to one marker line for the same reason. A subagent's
final message and the reports other agents send back are kept whole: a builder lists
the traps it hit at the end.

  python3 -I extract-session.py --latest [--out PATH]           # this Claude Code session
  python3 -I extract-session.py --codex [--out PATH]            # newest Codex session here
  python3 -I extract-session.py --file PATH.jsonl [--out PATH]  # any one transcript

The output can hold secrets that appeared in the session. Write it to a scratch
folder, never into a repository, and never quote a secret from it.
Standard library only.
"""
import argparse
import glob
import json
import os
import re
import sys

ASSIST_MAX = 900
AGENT_MSG_MAX = 600
ERROR_MAX = 300
HINT_MAX = 160

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
    """The session's subagent transcripts, each with a label from its .meta.json."""
    found = []
    for sub in glob.glob(os.path.join(path[:-len(".jsonl")], "subagents", "*.jsonl")):
        label = os.path.basename(sub)[:-len(".jsonl")]
        try:
            with open(sub[:-len(".jsonl")] + ".meta.json") as fh:
                m = json.load(fh)
            name = m.get("name") or m.get("agentType") or label
            label = f"{name} — {m['description']}" if m.get("description") else name
        except Exception:
            pass
        found.append((sub, label))
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
            found.append((path, label))
    return found


# ---------- write ----------
def stamp(ts):
    return (ts or "")[5:16].replace("T", " ")


def render(turns):
    out = []
    for role, text, ts in turns:
        if role == "TOOL":
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


def main():
    ap = argparse.ArgumentParser(description="Condense a session transcript for a session review.")
    ap.add_argument("--file", help="one transcript (.jsonl), Claude Code or Codex")
    ap.add_argument("--latest", action="store_true", help="this Claude Code session ($CLAUDE_CODE_SESSION_ID), else the newest for this directory")
    ap.add_argument("--codex", action="store_true", help="the newest Codex session for this directory")
    ap.add_argument("--out", help="write here instead of stdout")
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
    for sub, label in subs:
        sturns, smeta = parse(sub, human_label="PARENT")
        parsed.append((smeta["first"] or "", label, sub, sturns, smeta))
    parsed.sort(key=lambda x: x[0])
    if not turns and not parsed:
        sys.exit(f"nothing read from {path}: it holds no Claude Code or Codex messages")
    withdrawn = meta["withdrawn"] + [r for *_, smeta in parsed for r in smeta["withdrawn"]]
    if withdrawn:
        print(f"dropped {len(withdrawn)} queued message(s) taken back unsent (reasons: "
              f"{sorted(set(map(str, withdrawn)))}); a reason that means delivered belongs in DELIVERED",
              file=sys.stderr)

    doc = [f"# Session {meta['id']}\n",
           f"- tool: {'codex' if is_codex else 'claude code'}\n- cwd: {meta['cwd']}\n- branch: {meta['branch']}\n",
           f"- title: {meta['title']}\n- from: {meta['first']}\n- to: {meta['last']}\n",
           f"- human turns: {human_count(turns)}  tool errors: {meta['errors']}  subagents: {len(parsed)}\n",
           f"- source: {path}\n\n---\n", render(turns)]
    for n, (first, label, sub, sturns, smeta) in enumerate(parsed, 1):
        doc.append(f"\n---\n\n## Subagent {n}: {label}\n\n"
                   f"- from: {smeta['first']}\n- to: {smeta['last']}\n- tool errors: {smeta['errors']}\n"
                   f"- source: {sub}\n")
        doc.append(render(sturns))
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


if __name__ == "__main__":
    main()
