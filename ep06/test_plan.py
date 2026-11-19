"""Test plan mode and the task list without an API key: python3 test_plan.py"""
import os, shutil, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"), d + "/p")
os.chdir(d + "/p")
os.environ["AGENT_HOME"] = d + "/home"
import agent
agent.ROOT = os.path.realpath(d + "/p")


def use(name, **inp):
    return NS(type="tool_use", id="t%d" % use.n, name=name, input=inp)
use.n = 0


class Fake:
    """A scripted model. Each step is a list of tool_use blocks; the last step is plain text.
    It records the tool names it was offered each turn."""
    def __init__(self, steps):
        self.messages, self.steps, self.offered = self, steps, []

    def create(self, **kw):
        self.offered.append([t["name"] for t in kw["tools"]])
        step = self.steps.pop(0)
        usage = NS(input_tokens=100)
        if isinstance(step, str):
            return NS(stop_reason="end_turn", usage=usage, content=[NS(type="text", text=step)])
        for b in step:
            use.n += 1
            b.id = "t%d" % use.n
        return NS(stop_reason="tool_use", usage=usage, content=step)


def results(messages):
    return [b["content"] for m in messages if m["role"] == "user" and isinstance(m["content"], list)
            for b in m["content"]]


perms = agent.Permissions(mode="accept-edits")
yes = lambda *a: "y"

# 1. plan mode offers only read tools plus submit_plan, refuses an edit, and approval opens the edit tools
fake = Fake([[use("edit_file", path="config.py", old_text="1.0.0", new_text="1.1.0")],
             [use("submit_plan", plan="1. bump version")],
             [use("read_file", path="config.py")],
             "done"])
msgs = agent.run("bump the version", fake, "m", perms=perms, approver=yes, plan=True, plan_ok=lambda p: "")
assert fake.offered[0] == ["read_file", "grep", "submit_plan"], fake.offered[0]
assert "edit_file" in fake.offered[2] and "submit_plan" not in fake.offered[2], fake.offered[2]
assert "not available in plan mode" in results(msgs)[0]
assert open("config.py").read().count("1.0.0") == 1, "the refused edit must not have run"
print("ok 1: plan mode offers read tools only; an edit is refused; approval opens the edit tools")

# 2. feedback keeps plan mode on
fake = Fake([[use("submit_plan", plan="bad plan")], [use("submit_plan", plan="better plan")], "done"])
answers = iter(["also update the docs", ""])
msgs = agent.run("x", fake, "m", perms=perms, approver=yes, plan=True, plan_ok=lambda p: next(answers))
assert "wants changes" in results(msgs)[0] and "approved" in results(msgs)[1]
assert len(agent.run.plans) == 2 and "submit_plan" in fake.offered[1]
print("ok 2: feedback keeps plan mode on; the second plan is approved")

# 3. the task list is checked and shown back
items = [{"task": "a", "status": "in_progress"}, {"task": "b", "status": "pending"}]
fake = Fake([[use("todo_write", items=items)],
             [use("todo_write", items=[{"task": "a", "status": "in_progress"}, {"task": "b", "status": "in_progress"}])],
             [use("todo_write", items=[{"task": "a", "status": "done"}, {"task": "b", "status": "in_progress"}])],
             "done"])
msgs = agent.run("x", fake, "m", perms=perms, approver=yes, todo=True)
r = results(msgs)
assert "0 of 2 done" in r[0] and "[>] a" in r[0]
assert "only one item" in r[1]
assert "1 of 2 done" in r[2] and [t["status"] for t in agent.TODOS] == ["done", "in_progress"]
print("ok 3: the list is shown back; two items in progress are refused; the list is updated")

# 4. todo_write is not offered when the task list is off
fake = Fake(["done"])
agent.run("x", fake, "m", perms=perms, approver=yes)
assert "todo_write" not in fake.offered[0] and "submit_plan" not in fake.offered[0]
print("ok 4: without the flags the tool set is the old one")

# 5. reading works in plan mode (the first version refused everything before approval)
fake = Fake([[use("read_file", path="config.py")], [use("submit_plan", plan="p")], "done"])
msgs = agent.run("x", fake, "m", perms=perms, approver=yes, plan=True, plan_ok=lambda p: "")
assert "VERSION" in results(msgs)[0] and "not available" not in results(msgs)[0]
print("ok 5: read_file works while planning")

# 6. a reply cut off by max_tokens is dropped and the model is asked again
class Cut(Fake):
    def create(self, **kw):
        step = self.steps.pop(0)
        usage = NS(input_tokens=100)
        if step == "CUT":
            return NS(stop_reason="max_tokens", usage=usage, content=[NS(type="text", text="a very long pla")])
        self.steps.insert(0, step)
        return Fake.create(self, **kw)
fake = Cut(["CUT", "done"])
msgs = agent.run("x", fake, "m", perms=perms, approver=yes)
assert agent.final_text(msgs) == "done" and msgs[0]["role"] == "user" and isinstance(msgs[0]["content"], list)
assert [m["role"] for m in msgs] == ["user", "assistant"]
print("ok 6: a cut-off reply is dropped and asked again")
print("all passed")
