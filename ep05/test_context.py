"""Test the context manager without an API key: python3 test_context.py"""
import os, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
os.chdir(d)
os.environ["AGENT_HOME"] = d + "/home"
import agent
agent.ROOT = os.path.realpath(d)
for i in range(30):                                   # 30 files of about 3,000 characters each
    open("f%02d.txt" % i, "w").write(("line of file %d " % i) * 190)


class FakeClient:
    """A scripted model. It reads one file per turn and reports the same token
    count the API would: our estimate of everything it was sent."""
    def __init__(self, turns):
        self.messages, self.turns, self.calls, self.summaries = self, turns, 0, 0

    def create(self, **kw):
        sent = kw["messages"]
        tokens = agent.estimate(sent) + agent.estimate([{"x": kw.get("system", "")}])
        if "tools" not in kw:                         # the summary request
            self.summaries += 1
            return NS(stop_reason="end_turn", usage=NS(input_tokens=tokens),
                      content=[NS(type="text", text="Task: read the files. Done: f00..f%02d. Next: continue." % self.calls)])
        self.calls += 1
        if self.calls > self.turns:
            return NS(stop_reason="end_turn", usage=NS(input_tokens=tokens),
                      content=[NS(type="text", text="done")])
        return NS(stop_reason="tool_use", usage=NS(input_tokens=tokens),
                  content=[NS(type="tool_use", id="t%d" % self.calls, name="read_file",
                              input={"path": "f%02d.txt" % (self.calls - 1)})])


def check_pairs(messages):
    """Every tool call has its result in the next message; roles alternate."""
    for a, b in zip(messages, messages[1:]):
        assert a["role"] != b["role"], "roles must alternate"
    for i, m in enumerate(messages):
        if m["role"] == "assistant":
            ids = [x.id for x in m["content"] if getattr(x, "type", "") == "tool_use"]
            if ids:
                got = [x["tool_use_id"] for x in messages[i + 1]["content"]]
                assert got == ids, (got, ids)


perms = agent.Permissions()
# 1. Without management (limits very high): the window only grows.
agent.CLEAR_AT = agent.COMPACT_AT = 10 ** 9
agent.MAX_TURNS = 30
c = FakeClient(25)
agent.run("Read every file.", c, "fake", perms=perms, approver=lambda *a: "y")
free = [t for _, t, _ in agent.run.context]
assert free == sorted(free) and free[-1] > 5000, free
assert c.summaries == 0

# 2. With management: it stays under the line, and nothing breaks.
agent.CLEAR_AT, agent.COMPACT_AT = 2500, 4000
c = FakeClient(25)
msgs = agent.run("Read every file.", c, "fake", perms=perms, approver=lambda *a: "y")
managed = [t for _, t, _ in agent.run.context]
actions = [a for _, _, a in agent.run.context if a]
assert any(a.startswith("cleared") for a in actions), actions
assert any(a.startswith("compact") for a in actions), actions
assert c.summaries >= 1
assert max(managed) < max(free) * 0.6, (max(managed), max(free))
check_pairs(msgs)
first = msgs[0]["content"]
assert "Read every file." in first and "Summary of the work so far" in first and "Files touched so far: f0" in first
assert len(msgs) < 20, len(msgs)

# 3. Clearing keeps the newest results whole and every call keeps a result.
m = [{"role": "user", "content": "task"}]
for i in range(5):
    m.append({"role": "assistant", "content": [NS(type="tool_use", id="t%d" % i, name="read_file", input={"path": "a"})]})
    m.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t%d" % i, "content": "BIG %d" % i}]})
n = agent.clear_old_results(m, keep=2)
assert n == 3 and m[-1]["content"][0]["content"] == "BIG 4" and m[2]["content"][0]["content"] == agent.CLEARED
assert agent.clear_old_results(m, keep=2) == 0          # already cleared: nothing to do
check_pairs(m)
# 4. The split never lands inside a call/result pair.
assert agent.split_point(m, keep_turns=2) in (5, 7) and m[agent.split_point(m, 2)]["role"] == "assistant"
print("ep05 context tests passed")
