"""Checks for the chat loop (repl.py) and the engine changes in agent.py (continue a conversation, streaming).
No API key, no model: a scripted fake client plays the model. Run: python3 test_repl.py"""
import io, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
tmp = tempfile.mkdtemp()
os.environ["AGENT_HOME"], os.environ["AGENT_MEMORY"] = tmp + "/home", tmp + "/mem"
shutil.copytree(os.path.join(HERE, "project"), tmp + "/p")
os.chdir(tmp + "/p")
import agent, repl
agent.ROOT = os.path.realpath(tmp + "/p")
Block = agent.Block
ok = 0
def check(name, cond):
    global ok
    ok += 1
    print(("ok   " if cond else "FAIL ") + name)
    assert cond, name

USAGE = lambda: Block(input_tokens=10, output_tokens=5, cache_read_input_tokens=0, cache_creation_input_tokens=0)
class Stream:
    """What client.messages.stream(...) returns: a context manager with text_stream and get_final_message()."""
    def __init__(self, msg, boom=None): self.msg, self.boom = msg, boom
    def __enter__(self): return self
    def __exit__(self, *a): return False
    @property
    def text_stream(self):
        for b in self.msg.content:
            if b.get("type") == "text":
                for i in range(0, len(b["text"]), 4):
                    if self.boom:
                        raise self.boom
                    yield b["text"][i:i + 4]
    def get_final_message(self): return self.msg
class Fake:
    """script: a list of steps. A step is ("text", "...") or ("tool", name, input) or ("text+tool", "...", name, input)
    or ("boom", exception) which raises while the call is made."""
    def __init__(self, script): self.script, self.n, self.messages, self.seen, self.sent = script, 0, self, [], []
    def _next(self, kw):
        self.seen.append([t["name"] for t in kw["tools"]])
        self.sent.append(json.loads(json.dumps(kw["messages"], default=lambda b: dict(b))))
        step = self.script[min(self.n, len(self.script) - 1)]; self.n += 1
        if step[0] == "boom": raise step[1]
        content = []
        if step[0] in ("text", "text+tool"): content.append(Block(type="text", text=step[1]))
        if step[0] in ("tool", "text+tool"):
            content.append(Block(type="tool_use", id="t%d" % self.n, name=step[-2], input=step[-1]))
        return Block(stop_reason="tool_use" if step[0] != "text" else "end_turn", usage=USAGE(), content=content)
    def create(self, **kw): return self._next(kw)
    def stream(self, **kw): return Stream(self._next(kw))
def chat(script, **kw):
    out = io.StringIO()
    kw.setdefault("mode", "accept-edits")
    c = repl.Chat(Fake(script), "m", out=out, **kw)
    return c, out
def alternates(msgs):
    """user and assistant turns in order (two user turns in a row are allowed by the API, but we never produce them) and a result for every tool call"""
    roles = [m["role"] for m in msgs]
    calls = {b["id"] for m in msgs if m["role"] == "assistant" and isinstance(m["content"], list) for b in m["content"] if b.get("type") == "tool_use"}
    got = {b["tool_use_id"] for m in msgs if m["role"] == "user" and isinstance(m["content"], list) for b in m["content"] if b.get("type") == "tool_result"}
    return all(a != b for a, b in zip(roles, roles[1:])) and calls <= got

# 1 blocks are plain dicts with attribute access
b = agent.as_blocks([Block(type="text", text="hi")])[0]
check("a block is a dict with attribute access and saves to JSON as it is", b.type == "text" and b["text"] == "hi" and json.loads(json.dumps(b)) == {"type": "text", "text": "hi"})
check("a missing attribute is an AttributeError, so getattr(b, 'x', default) still works", getattr(b, "nope", 7) == 7)

# 2 continuing a conversation
c, out = chat([("text", "It adds up prices."), ("text", "config.py")])
m1 = c.turn("What does cart.py do?")
n1 = len(m1)
m2 = c.turn("And the tax rate?")
check("the second prompt continues the same list of messages", m2 is c.messages and len(m2) == n1 + 2)
sent2 = c.client.sent[1]
check("the model sees the first answer when it gets the second prompt", any("It adds up prices." in json.dumps(x) for x in sent2) and sent2[-1]["content"] == "And the tax rate?")
check("the notes go in the first message only, once", sum("Project notes" in json.dumps(x) for x in sent2) == 1)

# 3 streaming
c, out = chat([("text", "Hello there, this is streamed text.")])
pieces = []
c.on_text = lambda p: (pieces.append(p), repl.Chat.on_text(c, p))
c.turn("hi")
check("the text arrives in pieces, in order", len(pieces) > 3 and "".join(pieces) == "Hello there, this is streamed text.")
check("the screen shows the whole text and ends on a new line", out.getvalue().startswith("Hello there, this is streamed text.") and out.getvalue().endswith("\n"))
check("the time to the first piece is recorded for every model call", len(agent.run.first_token) == 1 and agent.run.first_token[0] is not None)
c2, out2 = chat([("text", "Hello there, this is streamed text.")], stream=False)
m_plain = c2.turn("hi")
check("without streaming the reply is the same message", m_plain[-1]["content"][0]["text"] == c.messages[-1]["content"][0]["text"])
check("without streaming the whole reply is printed once, when the turn is done", out2.getvalue().strip() == "Hello there, this is streamed text.")

# 4 a tool call in the middle of a streamed turn
c, out = chat([("text+tool", "Let me look.", "read_file", {"path": "cart.py"}), ("text", "It is a cart.")])
c.turn("look at cart.py")
check("a streamed turn can call a tool and go on", [x[0] for x in agent.run.log] == ["read_file"] and c.messages[-1]["content"][0]["text"] == "It is a cart.")
check("the tool call shows as one short line", "  . read_file" in out.getvalue() and "-> allow" in out.getvalue())
check("the turn text and the tool line are on separate lines", "Let me look.\n  . read_file" in out.getvalue())

# 5 saving and resuming
c, out = chat([("text", "first answer"), ("text", "second answer")])
c.turn("one")
path = c.path()
check("every turn is saved as a JSON file", os.path.exists(path) and json.load(open(path))["turns"] == 1)
saved = repl.Chat.load(c.id)
check("a saved chat loads with blocks that act like the live ones", saved["messages"][-1]["content"][0].type == "text" and saved["id"] == c.id)
check("the newest chat of this folder loads without an id", repl.Chat.load()["id"] == c.id)
c3, out3 = chat([("text", "third answer")], session_id=saved["id"], messages=saved["messages"])
c3.turn("two")
check("a resumed chat sends the old messages and goes on", any("first answer" in json.dumps(x) for x in c3.client.sent[0]) and len(c3.messages) == 4)
check("a missing id loads nothing", repl.Chat.load("nope") is None)

# 6 Ctrl+C
c, out = chat([("text+tool", "On it.", "read_file", {"path": "cart.py"}), ("boom", KeyboardInterrupt()), ("text", "Back again.")])
c.turn("read cart.py")
check("Ctrl+C while the model is working stops the turn and prints [stopped]", "[stopped]" in out.getvalue())
check("the half turn is closed: turns alternate and every tool call has a result", alternates(c.messages))
c.turn("go on")
check("the next prompt works after Ctrl+C", c.messages[-1]["content"][0]["text"] == "Back again." and alternates(c.messages))
check("the session on disk is the repaired one", alternates(json.load(open(c.path()))["messages"]))
class Boom:
    def __call__(self, *a, **k): raise KeyboardInterrupt
c, out = chat([("tool", "run_bash", {"command": "sleep 5"}), ("text", "ok")])
real = agent.run_tool
agent.run_tool = lambda name, args: (_ for _ in ()).throw(KeyboardInterrupt())
c.perms = agent.Permissions(mode="accept-edits", allow=["run_bash"])
try:
    c.turn("sleep")
finally:
    agent.run_tool = real
check("Ctrl+C while a tool runs: the open call gets a 'stopped' result", alternates(c.messages) and any("Stopped by the user" in json.dumps(m) for m in c.messages))

# 7 slash commands
c, out = chat([("text", "x")])
c.command("/help")
check("/help lists the commands", "/clear" in out.getvalue() and "/sessions" in out.getvalue())
c.turn("hello")
old = c.id
c.command("/clear")
check("/clear starts a new chat with a new id and no messages", c.messages is None and c.id != old)
c.command("/context")
check("/context works on an empty chat", "0 messages" in out.getvalue())
c.command("/frobnicate")
check("an unknown command says so", "unknown command /frobnicate" in out.getvalue())
raised = False
try:
    c.command("/exit")
except EOFError:
    raised = True
check("/exit raises EOFError, the same way Ctrl+D does", raised)
c.command("/features")
check("/features shows every episode that is wired in", all(("EP%d" % k) in out.getvalue() for k in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11)))

# 8 plan mode on request, and everything wired in
c, out = chat([("text", "a"), ("text", "b")])
c.command("/plan")
c.turn("first")
check("/plan: the next prompt starts in plan mode (read-only tools plus submit_plan)", "edit_file" not in c.client.seen[0] and "submit_plan" in c.client.seen[0])
c.turn("second")
check("plan mode is for one prompt only", "edit_file" in c.client.seen[1])
tools = set(c.client.seen[1])
check("all earlier parts are offered: tools, task list, helpers, memory, skills", {"read_file", "grep", "edit_file", "run_bash", "todo_write", "delegate", "memory_write", "memory_forget", "load_skill"} <= tools)
check("hooks are loaded from .agent/hooks.json and ran after the tool calls", len(agent.Hooks.load().entries) == 1 and c.options()["hooks"].entries[0]["event"] == "PostToolUse")
c, out = chat([("tool", "run_bash", {"command": "rm -rf /tmp/nothing-here"}), ("text", "ok")], mode="default")
c.ask = lambda *a: "n"
c.turn("remove it")
check("the permission gate is on in the chat loop: a command that changes things is asked about, and a no is a no", [v for t, a, v in agent.run.log] == ["deny"])

# 9 the prompt: a trailing backslash continues the line; Ctrl+C at the prompt needs two presses
lines = iter(["first line \\", "second line", "next"])
real_input = __builtins__["input"] if isinstance(__builtins__, dict) else __builtins__.input
import builtins
builtins.input = lambda prompt="": next(lines)
try:
    check("a trailing backslash joins the next line", repl.read_prompt() == "first line \nsecond line")
finally:
    builtins.input = real_input
c, out = chat([("text", "x")])
steps = iter(["KeyboardInterrupt", "KeyboardInterrupt"])
def reader():
    next(steps); raise KeyboardInterrupt
repl.loop(c, reader)
check("Ctrl+C twice in a row at the prompt leaves, once only warns", "press Ctrl+C again" in out.getvalue())
steps = iter(["KeyboardInterrupt", "hi", "KeyboardInterrupt", "KeyboardInterrupt"])
def reader2():
    v = next(steps)
    if v == "KeyboardInterrupt": raise KeyboardInterrupt
    return v
c, out = chat([("text", "x")])
repl.loop(c, reader2)
check("a prompt between two Ctrl+C presses resets the count", c.turns == 1 and out.getvalue().count("press Ctrl+C again") == 2)

# 10 the engine still works one-shot, as in episodes 1 to 12
fake = Fake([("tool", "read_file", {"path": "cart.py"}), ("text", "done")])
msgs = agent.run("task", fake, "m", notes="", perms=agent.Permissions(mode="accept-edits"), approver=lambda *a: "n", hooks=agent.Hooks())
check("run() without messages= still starts a conversation and returns it (one-shot use)", agent.final_text(msgs) == "done" and msgs[0]["role"] == "user")
print("%d checks passed" % ok)
