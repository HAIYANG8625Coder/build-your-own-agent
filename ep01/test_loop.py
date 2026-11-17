"""Test the loop with a fake model (no API key needed): python3 test_loop.py"""
from types import SimpleNamespace as NS

import agent


class FakeClient:
    def __init__(self, loop_forever=False):
        self.calls, self.loop_forever = [], loop_forever
        self.messages = self

    def create(self, **kw):
        self.calls.append([dict(m) for m in kw["messages"]])
        if self.loop_forever or len(self.calls) == 1:
            block = NS(type="tool_use", id="t%d" % len(self.calls), name="list_files", input={"path": "."})
            return NS(stop_reason="tool_use", content=[block])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="done")])


c = FakeClient()
msgs = agent.run("what is here?", c, "fake")
assert agent.final_text(msgs) == "done"
assert len(msgs) == 4 and [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
second = c.calls[1]
assert second[-1]["content"][0]["type"] == "tool_result" and "agent.py" in second[-1]["content"][0]["content"]

c = FakeClient(loop_forever=True)
msgs = agent.run("x", c, "fake")
assert len(c.calls) == agent.MAX_TURNS, len(c.calls)

assert agent.run_tool("nope", {}).startswith("error")
assert agent.run_tool("list_files", {"path": "/does/not/exist"}).startswith("error")
print("ok: loop, 4 messages, tool result appended, max-turns guard, errors returned as results")
