"""Episode 13: the finished command-line agent.

    python3 repl.py                 # a new chat in this folder
    python3 repl.py --continue      # the latest saved chat of this folder
    python3 repl.py --resume ID     # a saved chat by id
    python3 repl.py --mcp tickets   # also load tools from an MCP server (episode 11)
    python3 repl.py --no-stream     # print each reply when it is complete

A chat loop around the engine in agent.py. What this file adds: the conversation is kept between prompts, the text is shown
as it arrives (streaming), Ctrl+C stops the current turn and keeps the chat, every turn is saved so a chat can be resumed,
and a few slash commands. Episodes 1 to 9 and 11 are switched on (see FEATURES); episode 10's always-on runner uses the same
engine without a chat loop. Claude Code does all of this too; the docs for it are in series/EP13-RESEARCH.md.

Run it inside a throwaway folder: run_bash really runs commands.
PROVIDER=claude (default) -> ANTHROPIC_API_KEY;  PROVIDER=deepseek -> DEEPSEEK_API_KEY.
"""
import json
import os
import sys
import time
import uuid

import agent

try:
    import readline          # line editing and history for input(); not available on every platform
except ImportError:
    readline = None

# What is switched on, and the episode that built it. The first column is the key of a run() argument (or "-" for a part
# that has no switch because it is always there).
FEATURES = [
    ("-", "EP1", "the loop"), ("-", "EP2", "tools: read, grep, edit, run"), ("-", "EP3", "system prompt and notes"),
    ("perms", "EP4", "permissions: ask before a command or an edit"), ("-", "EP5", "context: clear old results, compact"),
    ("todo", "EP6", "task list"), ("plan", "EP6", "plan mode (/plan)"), ("subagents", "EP7", "helpers (delegate)"),
    ("hooks", "EP8", "hooks in .agent/hooks.json"), ("memory", "EP9", "memory between chats"),
    ("skills", "EP11", "skills in .agent/skills"), ("mcp", "EP11", "MCP servers (--mcp NAME)"),
]

HELP = """  /help          this list
  /exit          leave (Ctrl+D works too)
  /clear         start a new chat
  /context       what is in the conversation now
  /compact       summarize the old turns now
  /plan          the next prompt starts in plan mode
  /todo          the task list
  /perms         permission mode and rules
  /memory        the memory index
  /features      what is switched on, by episode
  /sessions      saved chats of this folder
  /usage         tokens read so far in this chat
  end a line with \\ to continue on the next line"""


def sessions_dir():
    d = os.path.join(os.environ.get("AGENT_HOME") or os.path.expanduser("~/.agent"), "sessions")
    os.makedirs(d, exist_ok=True)
    return d


def repair(messages):
    """After Ctrl+C the list can end in a half turn. The API wants user and assistant turns in order and a result for every
    tool call, so close the turn: results for open tool calls, or a short assistant note."""
    if not messages:
        return messages
    last = messages[-1]
    if last["role"] == "assistant":
        open_calls = [b for b in last["content"] if b.get("type") == "tool_use"]
        if open_calls:
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b["id"], "content": "Stopped by the user before this ran.", "is_error": True}
                for b in open_calls]})
            messages.append({"role": "assistant", "content": [agent.Block(type="text", text="[stopped by the user]")]})
        return messages
    messages.append({"role": "assistant", "content": [agent.Block(type="text", text="[stopped by the user]")]})
    return messages


class Chat:
    """One conversation. turn(text) runs a prompt and returns the updated messages; save() writes the chat to disk."""

    def __init__(self, client, model, out=None, session_id=None, messages=None, mcp=None, stream=True, mode=None, ask=None):
        self.client, self.model, self.stream = client, model, stream
        self.out = out or sys.stdout
        self.id = session_id or time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
        self.messages = messages
        self.mcp = mcp or []
        self.perms = agent.Permissions.load(mode)
        self.plan_next = False
        self.spent = 0
        self.turns = 0
        self.at_bol = True
        self.ask = ask

    # ---- output
    def write(self, text):
        self.out.write(text)
        self.out.flush()
        self.at_bol = text.endswith("\n")

    def on_text(self, piece):
        self.write(piece)

    def tool_line(self, name, args, verdict):
        if not self.at_bol:
            self.write("\n")
        shown = json.dumps(args, ensure_ascii=False)[:80]
        self.write("  . %s %s -> %s\n" % (name, shown, verdict))

    # ---- one prompt
    def options(self):
        skills = "lazy" if os.path.isdir(os.path.join(agent.ROOT, ".agent", "skills")) else "off"
        return dict(perms=self.perms, hooks=agent.Hooks.load(), todo=True, plan=self.plan_next, subagents=True, memory=True,
                    skills=skills, mcp=self.mcp, mcp_rules=bool(self.mcp), quiet=True, stream=self.stream, on_text=self.on_text,
                    approver=self.ask)

    def turn(self, text):
        agent.run.tool_line = self.tool_line
        plan, self.plan_next = self.plan_next, False
        opts = self.options()
        opts["plan"] = plan
        started = time.time()
        try:
            self.messages = agent.run(text, self.client, self.model, messages=self.messages, **opts)
            note = ""
        except KeyboardInterrupt:
            self.messages = repair(agent.run.messages)
            note = "[stopped]"
        if not self.stream and not note:
            self.write(agent.final_text(self.messages))      # not streamed: the whole reply appears at once, when the turn is done
        if not self.at_bol:
            self.write("\n")
        if note:
            self.write(note + "\n")
        self.turns += 1
        self.spent += getattr(agent.run, "spent", 0)
        self.last = {"seconds": round(time.time() - started, 1), "first_token": list(getattr(agent.run, "first_token", []))}
        self.save()
        return self.messages

    # ---- saved chats
    def path(self):
        return os.path.join(sessions_dir(), self.id + ".json")

    def save(self):
        json.dump({"id": self.id, "cwd": agent.ROOT, "model": self.model, "turns": self.turns, "saved": time.time(), "messages": self.messages},
                  open(self.path(), "w"), ensure_ascii=False)

    @staticmethod
    def load(session_id=None):
        """A saved chat as a dict. No id: the newest one saved for this folder."""
        d = sessions_dir()
        files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json")]
        if session_id:
            files = [f for f in files if os.path.basename(f) == session_id + ".json"]
        else:
            files = [f for f in files if json.load(open(f)).get("cwd") == agent.ROOT]
        if not files:
            return None
        data = json.load(open(max(files, key=os.path.getmtime)))
        for m in data["messages"]:
            if isinstance(m["content"], list):
                m["content"] = [agent.Block(b) for b in m["content"]]
        return data

    # ---- slash commands. Return True when the line was a command.
    def command(self, line):
        name, _, rest = line.strip().partition(" ")
        w = self.write
        if name in ("/exit", "/quit"):
            raise EOFError
        if name == "/help":
            w(HELP + "\n")
        elif name == "/clear":
            self.messages, self.id, self.turns, self.spent = None, time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4], 0, 0
            w("new chat %s\n" % self.id)
        elif name == "/context":
            n = len(self.messages or [])
            last = agent.run.context[-1][1] if getattr(agent.run, "context", None) else 0
            w("%d messages, about %d tokens (last call: %d)\n" % (n, agent.estimate(self.messages or []), last))
        elif name == "/compact":
            if not self.messages:
                w("nothing to compact\n")
            else:
                before = agent.estimate(self.messages)
                self.messages, n = agent.compact(self.messages, self.client, self.model, agent.load_notes())
                w("compacted %d messages: about %d -> %d tokens\n" % (n, before, agent.estimate(self.messages)))
                self.save()
        elif name == "/plan":
            self.plan_next = True
            w("the next prompt starts in plan mode\n")
        elif name == "/todo":
            w((agent.show_todos() or "no tasks") + "\n")
        elif name == "/perms":
            w("mode: %s\nallow: %s\nask: %s\ndeny: %s\n" % (self.perms.mode, self.perms.allow, self.perms.ask, self.perms.deny))
        elif name == "/memory":
            w((agent.load_memory() or "no memory yet") + "\n")
        elif name == "/features":
            for key, ep, what in FEATURES:
                w("  %-5s %s\n" % (ep, what))
        elif name == "/sessions":
            d = sessions_dir()
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    x = json.load(open(os.path.join(d, f)))
                    w("  %s  %d turns  %s\n" % (x["id"], x.get("turns", 0), x.get("cwd", "")))
        elif name == "/usage":
            w("%d tokens read in %d turns\n" % (self.spent, self.turns))
        else:
            w("unknown command %s (try /help)\n" % name)
        return True


def read_prompt(prompt="> "):
    """One prompt. A line that ends with a backslash continues on the next line."""
    lines = []
    while True:
        line = input(prompt if not lines else "... ")
        if line.endswith("\\"):
            lines.append(line[:-1])
            continue
        lines.append(line)
        return "\n".join(lines)


def loop(chat, read=read_prompt):
    """Read a prompt, run it, repeat. Ctrl+C at the prompt: the first press only warns, a second one in a row leaves.
    Ctrl+C during a turn is handled in Chat.turn: it stops the turn and keeps the chat. Ctrl+D or /exit leaves."""
    strikes = 0
    while True:
        try:
            text = read()
            strikes = 0
        except KeyboardInterrupt:
            strikes += 1
            if strikes >= 2:
                return
            chat.write("\n(press Ctrl+C again to leave)\n")
            continue
        except EOFError:
            return
        if not text.strip():
            continue
        try:
            if text.startswith("/"):
                chat.command(text)
            else:
                chat.turn(text)
        except EOFError:
            return


def main(argv):
    args = list(argv)
    flag = lambda n: (n in args) and (args.remove(n) or True)
    stream = not flag("--no-stream")
    cont = flag("--continue")
    resume = None
    if "--resume" in args:
        i = args.index("--resume")
        resume = args[i + 1]
        del args[i:i + 2]
    servers = []
    while "--mcp" in args:
        i = args.index("--mcp")
        servers.append(args[i + 1])
        del args[i:i + 2]
    from mcp_client import McpClient
    clients = [McpClient(n, agent.MCP_SERVERS[n]).start() for n in servers]
    client, model = agent.make_client()
    saved = Chat.load(resume) if (resume or cont) else None
    if (resume or cont) and not saved:
        print("no saved chat found")
        return 1
    chat = Chat(client, model, session_id=saved["id"] if saved else None, messages=saved["messages"] if saved else None,
                mcp=clients, stream=stream, ask=None)
    if saved:
        chat.turns = saved.get("turns", 0)
    hist = os.path.join(sessions_dir(), "history")
    if readline:
        try:
            readline.read_history_file(hist)
        except OSError:
            pass
    print("agent chat %s  (model %s, %s)  /help for commands, Ctrl+D to leave" % (chat.id, model, "resumed" if saved else "new"))
    try:
        loop(chat)
    finally:
        if readline:
            try:
                readline.write_history_file(hist)
            except OSError:
                pass
        for c in clients:
            c.close()
    print("bye")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
