"""Episode 4: permissions.

    python3 agent.py "The tests in this folder fail. Find out why and fix it."
    python3 agent.py --mode accept-edits "..."     # modes: default, accept-edits, read-only, dont-ask

Every tool call now passes through a gate before it runs: deny, then ask, then allow.

Run it inside a throwaway folder: run_bash really runs commands.
(Episode 4 adds the permission gate.)

PROVIDER=claude (default) -> ANTHROPIC_API_KEY, claude-haiku-5-5
PROVIDER=deepseek         -> DEEPSEEK_API_KEY, deepseek-flash
"""
import json
import os
import re
import subprocess
import sys

import anthropic

MAX_TURNS = 15
MAX_CHARS = 4000
ROOT = os.getcwd()
READ = set()   # files the model has read (edit needs this)

NOTES_FILE = "NOTES.md"
NOTES_MAX_LINES = 200   # Claude Code's docs: aim for under 200 lines

# The system prompt has three parts: a role, a few rules, the environment.
ROLE = "You are a small coding assistant working in a project folder."
RULES = ("Use the tools to look, then act. Read a file before you edit it. "
         "Check your work by running the tests. Answer briefly. "
         "If an action is denied, do not try to get around it: "
         "say what you could not do.")


def environment():
    return "Project folder: %s\nPlatform: %s" % (ROOT, sys.platform)


def build_system():
    return "%s\n\n%s\n\n%s" % (ROLE, RULES, environment())


def load_notes():
    """The project notes, or "" if there is no notes file."""
    path = os.path.join(ROOT, NOTES_FILE)
    if not os.path.exists(path):
        return ""
    text = open(path).read()
    n = len(text.split("\n"))
    if n > NOTES_MAX_LINES:
        print("warning: %s has %d lines; long notes get followed less"
              % (NOTES_FILE, n))
    return text


def first_message(task, notes):
    """Notes go in the first user message, not in the system prompt.
    (Claude Code does the same with CLAUDE.md.)"""
    if not notes:
        return task
    return "Project notes (%s):\n%s\n\nTask: %s" % (NOTES_FILE, notes, task)

TOOLS = [
    {"name": "read_file",
     "description": (
         "Read a text file and return its lines, "
         "each with a line number. Use it before "
         "you edit a file. Long files are cut "
         "off; use grep to find the part you need."),
     "input_schema": {
         "type": "object",
         "properties": {"path": {"type": "string"}},
         "required": ["path"]}},
    {"name": "grep",
     "description": (
         "Search the files under a folder for a "
         "regular expression. Returns file:line:"
         "text for each match, at most 50. Use it "
         "to find where something is defined."),
     "input_schema": {
         "type": "object",
         "properties": {"pattern": {"type": "string"},
                        "path": {"type": "string"}},
         "required": ["pattern"]}},
    {"name": "run_bash",
     "description": (
         "Run a shell command in the project "
         "folder and return its output and exit "
         "code. Use it to run tests or list "
         "files. It stops after 20 seconds."),
     "input_schema": {
         "type": "object",
         "properties": {"command": {"type": "string"}},
         "required": ["command"]}},
    {"name": "edit_file",
     "description": (
         "Replace one exact piece of text in a "
         "file. 'old_text' must match it exactly "
         "and appear once, so include enough "
         "surrounding text. Read the file first."),
     "input_schema": {
         "type": "object",
         "properties": {"path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"}},
         "required": ["path", "old_text", "new_text"]}},
]


class ToolError(Exception):
    """A problem the model can fix by trying again."""


def safe(path):
    full = os.path.realpath(os.path.join(ROOT, path))
    if full != ROOT and not full.startswith(ROOT + os.sep):
        raise ToolError("path is outside the project folder")
    return full


def cut(text, limit=MAX_CHARS):
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... cut off. Ask for less."


def read_file(path):
    full = safe(path)
    with open(full) as f:
        lines = f.read().split("\n")
    READ.add(full)
    body = "\n".join("%d  %s" % (i + 1, l)
                     for i, l in enumerate(lines))
    return cut(body)


def grep(pattern, path="."):
    hits = []
    for folder, _, names in os.walk(safe(path)):
        for name in sorted(names):
            file = os.path.join(folder, name)
            try:
                text = open(file).read()
            except (UnicodeDecodeError, OSError):
                continue
            for n, line in enumerate(text.split("\n"), 1):
                if re.search(pattern, line):
                    rel = os.path.relpath(file, ROOT)
                    hits.append("%s:%d:%s" % (rel, n, line))
    return "\n".join(hits[:50]) or "no matches"


def run_bash(command):
    done = subprocess.run(
        command, shell=True, cwd=ROOT, timeout=20,
        capture_output=True, text=True)
    out = cut(done.stdout + done.stderr)
    return "exit code %d\n%s" % (done.returncode, out)


def edit_file(path, old_text, new_text):
    full = safe(path)
    if full not in READ:
        raise ToolError("read the file first")
    text = open(full).read()
    n = text.count(old_text)
    if n != 1:
        raise ToolError("'old_text' appears %d times; "
                        "it must appear once" % n)
    open(full, "w").write(
        text.replace(old_text, new_text))
    return "edited " + path


FUNCS = {"read_file": read_file, "grep": grep,
         "run_bash": run_bash, "edit_file": edit_file}


def run_tool(name, args):
    """Returns (text, is_error). An error is a result too."""
    try:
        return FUNCS[name](**args), False
    except subprocess.TimeoutExpired:
        return "error: the command took too long", True
    except Exception as e:
        return "error: %s" % e, True


# ---------------------------------------------------------------- permissions
MODES = ("default", "accept-edits", "read-only", "dont-ask")
SPLIT = re.compile(r"&&|\|\||;|\||&|\n")        # where a shell command splits
UNSAFE = ("$(", "`", "<(", ">(")                 # we cannot analyze these
READ_ONLY_BASH = {"ls", "cat", "pwd", "cd", "echo", "head", "tail", "wc", "grep", "diff"}


def subcommands(command):
    keep = command.replace(">&", ">\0")           # 2>&1 is not a new command
    return [p.replace("\0", "&").strip()
            for p in SPLIT.split(keep) if p.strip()]


def subject(tool, args):
    """The text a rule is matched against: the command, or the path."""
    if tool == "run_bash":
        return args.get("command", "")
    full = os.path.realpath(os.path.join(ROOT, args.get("path") or "."))
    return os.path.relpath(full, ROOT)


def pattern(spec):
    """A rule specifier as a regex. * matches any text, spaces included.
    A trailing ' *' also matches the bare command: 'ls *' matches 'ls'."""
    def esc(t):
        return ".*".join(re.escape(x) for x in t.split("*"))
    if spec.endswith(" *"):
        return re.compile(esc(spec[:-2]) + "(?: .*)?", re.S)
    return re.compile(esc(spec), re.S)


def rule_matches(rule, tool, text):
    m = re.fullmatch(r"(\w+)(?:\((.*)\))?", rule.strip(), re.S)
    if not m or m.group(1) != tool:
        return False
    return m.group(2) is None or bool(pattern(m.group(2)).fullmatch(text))


def read_only(part):
    """A single command that only looks. Output to /dev/null is fine;
    any other redirect writes a file."""
    plain = part.replace("2>/dev/null", "").replace("2>&1", "")
    return part.split()[0] in READ_ONLY_BASH and ">" not in plain


class Permissions:
    """Rules in three lists, a mode, and what the user allowed this session.
    Order: deny, then ask, then allow. The first match decides."""

    def __init__(self, allow=(), ask=(), deny=(), mode="default"):
        assert mode in MODES, mode
        self.allow, self.ask, self.deny = list(allow), list(ask), list(deny)
        self.mode = mode
        self.session = set()       # (tool, text) the user said "always" to
        self.last_asked = False

    @classmethod
    def load(cls, mode=None):
        """Rules from ~/.agent/permissions.json and ./.agent/permissions.json.
        The lists are joined, not replaced (Claude Code does the same)."""
        lists = {"allow": [], "ask": [], "deny": []}
        home = os.environ.get("AGENT_HOME") or os.path.expanduser("~/.agent")
        for path in (os.path.join(home, "permissions.json"),
                     os.path.join(ROOT, ".agent", "permissions.json")):
            if os.path.exists(path):
                data = json.load(open(path))
                for k in lists:
                    lists[k] += data.get(k, [])
        return cls(mode=mode or os.environ.get("AGENT_MODE", "default"), **lists)

    def remember(self, tool, args):
        for t in self.texts(tool, args):
            self.session.add((tool, t))

    def texts(self, tool, args):
        text = subject(tool, args)
        return subcommands(text) if tool == "run_bash" else [text]

    def allowed(self, tool, text):
        return ((tool, text) in self.session
                or any(rule_matches(r, tool, text) for r in self.allow))

    def check(self, tool, args):
        """Returns ("allow" | "ask" | "deny", reason)."""
        texts = self.texts(tool, args)
        for rule in self.deny:
            if any(rule_matches(rule, tool, t) for t in texts):
                return "deny", "the rule %s denies this" % rule
        for rule in self.ask:
            if any(rule_matches(rule, tool, t) for t in texts):
                return "ask", "the rule %s asks first" % rule
        if tool == "run_bash" and any(u in args.get("command", "") for u in UNSAFE):
            return "ask", "this command cannot be analyzed"
        if all(self.allowed(tool, t) for t in texts):
            return "allow", "an allow rule covers this"
        return self.by_mode(tool, texts)

    def by_mode(self, tool, texts):
        if tool in ("read_file", "grep"):
            return "allow", "reading is allowed"
        if tool == "run_bash" and all(
                self.allowed(tool, t) or read_only(t) for t in texts):
            return "allow", "a read-only command"
        if tool == "edit_file" and self.mode == "accept-edits":
            return "allow", "accept-edits mode"
        if self.mode == "read-only":
            return "deny", "read-only mode: no edits and no commands"
        if self.mode == "dont-ask":
            return "deny", "dont-ask mode: nothing that needs approval runs"
        return "ask", "this changes things"


def ask_user(tool, args):
    """The confirm prompt. Returns "y" (once), "a" (always, this session), "n"."""
    shown = json.dumps(args)[:200]
    print("\n  Allow %s %s ?" % (tool, shown))
    return input("  [y] once  [a] always this session  [n] no > ").strip().lower()


def gated(tool, args, perms, approver):
    """Decide, maybe ask, then run. Returns (text, is_error, verdict)."""
    verdict, why = perms.check(tool, args)
    perms.last_asked = verdict == "ask"
    if verdict == "ask":
        answer = approver(tool, args)
        if answer == "a":
            perms.remember(tool, args)
        verdict = "allow" if answer in ("y", "a") else "deny"
        why = "the user declined" if verdict == "deny" else "the user agreed"
    if verdict == "deny":
        return ("permission denied: %s. Do not retry it; "
                "tell the user what you could not do." % why), True, verdict
    text, bad = run_tool(tool, args)
    return text, bad, verdict


def run(task, client, model, system=None, notes=None, perms=None, approver=None):
    system = build_system() if system is None else system
    notes = load_notes() if notes is None else notes
    perms = perms or Permissions.load()
    approver = approver or ask_user
    log = run.log = []   # every decision, for tests and demos
    messages = [{"role": "user",
                 "content": first_message(task, notes)}]
    for turn in range(1, MAX_TURNS + 1):
        resp = client.messages.create(
            model=model, max_tokens=2048,
            system=system, tools=TOOLS,
            messages=messages)
        reply = {"role": "assistant",
                 "content": resp.content}
        messages.append(reply)
        print("turn", turn, resp.stop_reason)
        if resp.stop_reason != "tool_use":
            return messages
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out, bad, verdict = gated(block.name, block.input,
                                          perms, approver)
                log.append((block.name, block.input, verdict))
                print(" ", block.name, json.dumps(block.input)[:96], "->",
                      verdict + (" (asked)" if perms.last_asked else ""))
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": out,
                    "is_error": bad})
        messages.append(
            {"role": "user", "content": results})
    return messages


def final_text(messages):
    last = messages[-1]["content"]
    return "".join(b.text for b in last if b.type == "text")


PROVIDERS = {
    "claude": ("ANTHROPIC_API_KEY", None, "claude-haiku-5-5"),
    "deepseek": ("DEEPSEEK_API_KEY",
                 "https://api.deepseek.com/anthropic",
                 "deepseek-flash"),
}


def make_client():
    key, url, model = PROVIDERS[os.environ.get("PROVIDER", "claude")]
    return anthropic.Anthropic(api_key=os.environ[key], base_url=url), model


if __name__ == "__main__":
    if sys.argv[1:] == ["--show-prompt"]:
        print("--- system ---\n" + build_system())
        print("--- first message ---\n"
              + first_message("<your task>", load_notes()))
        sys.exit()
    args = sys.argv[1:]
    mode = None
    if args[:1] == ["--mode"]:
        mode, args = args[1].replace("_", "-"), args[2:]
    client, model = make_client()
    task = " ".join(args) or "What is in this folder?"
    print(final_text(run(task, client, model, perms=Permissions.load(mode))))
