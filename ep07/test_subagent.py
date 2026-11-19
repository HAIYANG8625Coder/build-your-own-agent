"""Test the subagent without an API key: python3 test_subagent.py"""
import os, shutil, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"), d + "/p")
os.chdir(d + "/p")
os.environ["AGENT_HOME"] = d + "/home"
import agent
agent.ROOT = os.path.realpath(d + "/p")


def use(name, **inp):
    use.n += 1
    return NS(type="tool_use", id="t%d" % use.n, name=name, input=inp)
use.n = 0


class Fake:
    """A scripted model shared by the main loop and the helper. Records what each call saw."""
    def __init__(self, steps):
        self.messages, self.steps, self.calls = self, steps, []

    def create(self, **kw):
        self.calls.append({"tools": [t["name"] for t in kw["tools"]], "system": kw["system"],
                           "first": kw["messages"][0]["content"], "n": len(kw["messages"])})
        step = self.steps.pop(0)
        usage = NS(input_tokens=100 + 50 * len(kw["messages"]))
        if isinstance(step, str):
            return NS(stop_reason="end_turn", usage=usage, content=[NS(type="text", text=step)])
        return NS(stop_reason="tool_use", usage=usage, content=step)


def results(messages):
    return [b["content"] for m in messages if m["role"] == "user" and isinstance(m["content"], list)
            for b in m["content"]]


perms = agent.Permissions(mode="accept-edits")
yes = lambda *a: "y"

# 1. delegate is offered only when subagents are on
fake = Fake(["done"])
agent.run("x", fake, "m", perms=perms, approver=yes)
assert "delegate" not in fake.calls[0]["tools"]
fake = Fake(["done"])
agent.run("x", fake, "m", perms=perms, approver=yes, subagents=True)
assert "delegate" in fake.calls[0]["tools"] and "delegate" in fake.calls[0]["system"]
print("ok 1: delegate is offered only with subagents on")

# 2. the helper starts fresh, reads only, and only its final text comes back
fake = Fake([[use("delegate", task="Find the tax rate in the project and answer in one line.")],   # main asks
             [use("read_file", path="config.py")],                                                  # helper reads
             "The tax rate is in config.py.",                                                       # helper answers
             "The helper says: the tax rate is in config.py."])                                     # main answers
msgs = agent.run("What is the tax rate?", fake, "m", perms=perms, approver=yes, subagents=True)
sub_calls = [c for c in fake.calls if c["system"] == agent.SUB_SYSTEM]
assert len(sub_calls) == 2 and sub_calls[0]["first"] == "Find the tax rate in the project and answer in one line."
assert sub_calls[0]["tools"] == ["read_file", "grep"], sub_calls[0]["tools"]
assert sub_calls[0]["n"] == 1                       # a fresh conversation: just the brief
r = results(msgs)
assert r == ["The tax rate is in config.py."], r    # the main loop never saw the helper's read_file result
assert "VERSION" not in str(msgs)                   # nothing the helper read leaked into the main messages
assert agent.run.subs == [{"turns": 2, "peak": sub_calls[1]["n"] * 50 + 100, "spent": agent.run.subs[0]["spent"], "done": True}]
print("ok 2: the helper starts fresh with read-only tools; only its final text reaches the main loop")

# 3. a helper cannot edit, run commands or delegate, even if it asks
fake = Fake([[use("delegate", task="t")], [use("edit_file", path="config.py", old_text="1.0.0", new_text="9.9.9")],
             "I could not edit.", "done"])
msgs = agent.run("x", fake, "m", perms=perms, approver=yes, subagents=True)
assert "1.0.0" in open("config.py").read() and "9.9.9" not in open("config.py").read()
print("ok 3: a helper cannot edit files")

# 4. the helper has a turn limit
agent.SUB_MAX_TURNS = 3
fake = Fake([[use("delegate", task="loop forever")]] + [[use("grep", pattern="a")]] * 3 + ["gave up"])
msgs = agent.run("x", fake, "m", perms=perms, approver=yes, subagents=True)
assert "stopped after 3 turns" in results(msgs)[0] and agent.run.subs[0]["done"] is False
print("ok 4: the helper stops at its turn limit and says so")
print("all passed")
