"""Test the tools and the loop without an API key: python3 test_tools.py"""
import os, shutil, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"), d + "/p")
os.chdir(d + "/p")
os.makedirs(d + "/p-other")
open(d + "/p-other/secret.txt", "w").write("x")
import agent  # ROOT is the current folder when agent is imported
agent.ROOT = os.path.realpath(os.getcwd())

out, bad = agent.run_tool("run_bash", {"command": "python3 test_calc.py"})
assert not bad and "exit code 1" in out and "add(2, 3) should be 5" in out, out
out, bad = agent.run_tool("grep", {"pattern": "def add"})
assert "calc.py:1:def add" in out, out
out, bad = agent.run_tool("edit_file", {"path": "calc.py", "old_text": "a - b", "new_text": "a + b"})
assert bad and "read the file first" in out, out
out, bad = agent.run_tool("read_file", {"path": "calc.py"})
assert not bad and "3      return a - b" in out, out
out, bad = agent.run_tool("edit_file", {"path": "calc.py", "old_text": "result", "new_text": "x"})
assert bad and "appears" in out and "times" in out, out
out, bad = agent.run_tool("edit_file", {"path": "calc.py", "old_text": "nothing like this", "new_text": "x"})
assert bad and "0 times" in out, out
out, bad = agent.run_tool("edit_file", {"path": "calc.py", "old_text": "a - b", "new_text": "a + b"})
assert not bad, out
out, bad = agent.run_tool("run_bash", {"command": "python3 test_calc.py"})
assert "exit code 0" in out and "all tests passed" in out, out
out, bad = agent.run_tool("read_file", {"path": "../../etc/passwd"})
assert bad and "outside" in out, out
out, bad = agent.run_tool("read_file", {"path": "../p-other/secret.txt"})
assert bad and "outside" in out, out   # a sibling folder with the same prefix
out, bad = agent.run_tool("read_file", {"path": "missing.py"})
assert bad and out.startswith("error"), out
open("big.txt", "w").write("x" * 20000)
out, bad = agent.run_tool("read_file", {"path": "big.txt"})
assert len(out) < 4100 and "cut off" in out, len(out)
out, bad = agent.run_tool("nope", {})
assert bad, out


class Fake:
    """Asks for run_bash, then answers."""
    def __init__(self): self.n = 0; self.messages = self
    def create(self, **kw):
        self.n += 1
        if self.n == 1:
            b = NS(type="tool_use", id="t1", name="run_bash", input={"command": "echo hi"})
            return NS(stop_reason="tool_use", content=[b])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="done")])

msgs = agent.run("x", Fake(), "fake")
assert agent.final_text(msgs) == "done" and msgs[2]["content"][0]["is_error"] is False
print("ok: 4 tools, errors as results, read-before-edit, exact-once edit, truncation, path guard, loop")
