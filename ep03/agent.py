"""Episode 3: the system prompt and the notes file.

    python3 agent.py "Add a function ..."
    python3 agent.py --show-prompt      # print exactly what the model gets

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
         "Check your work by running the tests. Answer briefly.")


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


def run(task, client, model, system=None, notes=None):
    system = build_system() if system is None else system
    notes = load_notes() if notes is None else notes
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
                out, bad = run_tool(block.name,
                                    block.input)
                print(" ", block.name,
                      json.dumps(block.input)[:110])
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
    client, model = make_client()
    task = " ".join(sys.argv[1:]) or "What is in this folder?"
    print(final_text(run(task, client, model)))
