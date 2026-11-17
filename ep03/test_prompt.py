"""Test the prompt and notes code without an API key: python3 test_prompt.py"""
import os, shutil, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"), d + "/p")
os.chdir(d + "/p")
import agent
agent.ROOT = os.path.realpath(os.getcwd())

# the system prompt has a role, rules and the environment
s = agent.build_system()
assert agent.ROLE in s and agent.RULES in s and agent.ROOT in s, s

# notes are loaded from the project folder, and sit in the first user message
notes = agent.load_notes()
assert "integer cents" in notes
msg = agent.first_message("do it", notes)
assert msg.startswith("Project notes") and msg.endswith("Task: do it"), msg
assert "integer cents" not in s          # not in the system prompt

# no notes file: the task is sent as it is
os.remove("NOTES.md")
assert agent.load_notes() == ""
assert agent.first_message("do it", "") == "do it"

# a long notes file gives a warning
open("NOTES.md", "w").write("rule\n" * 250)
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    agent.load_notes()
assert "250" in buf.getvalue() or "251" in buf.getvalue(), buf.getvalue()


# a fake model: the run passes system and notes to the API
class FakeClient:
    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        return NS(stop_reason="end_turn", content=[NS(type="text", text="Done: x")])


c = FakeClient()
msgs = agent.run("hello", c, "m", notes="NOTE-LINE")
call = c.calls[0]
assert call["system"] == agent.build_system(), call["system"]
assert "NOTE-LINE" in call["messages"][0]["content"]
assert agent.final_text(msgs) == "Done: x"
print("all tests passed")
