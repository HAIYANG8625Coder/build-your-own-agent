"""Test the permission gate without an API key: python3 test_permissions.py"""
import os, shutil, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"), d + "/p")
os.chdir(d + "/p")
os.environ["AGENT_HOME"] = d + "/home"          # no user-level file
import agent
agent.ROOT = os.path.realpath(os.getcwd())
P = agent.Permissions

def v(perms, tool, **args):
    return perms.check(tool, args)[0]

# --- defaults (mode "default"): reads run, edits and commands ask
p = P()
assert v(p, "read_file", path="calc.py") == "allow"
assert v(p, "grep", pattern="def") == "allow"
assert v(p, "edit_file", path="calc.py", old_text="a", new_text="b") == "ask"
assert v(p, "run_bash", command="python3 test_calc.py") == "ask"
assert v(p, "run_bash", command="ls -la") == "allow"                 # read-only command
assert v(p, "run_bash", command="ls > out.txt") == "ask"             # a write, not a read
assert v(p, "run_bash", command="ls && rm -rf x") == "ask"           # every part must be safe
assert v(p, "run_bash", command="echo $(whoami)") == "ask"           # cannot analyze
assert v(p, "run_bash", command="cd sub && echo hi") == "allow"      # cd and echo only look
assert v(p, "run_bash", command="echo hi > out.txt") == "ask"        # but a redirect writes
assert v(p, "run_bash", command="cat x.txt 2>/dev/null | head -5") == "allow"   # errors to /dev/null are fine
assert v(p, "run_bash", command="cat x.txt 2>&1 | head -5") == "allow"          # 2>&1 does not split the command

# --- order: deny, then ask, then allow; the first match decides
p = P(allow=["run_bash(git *)"], deny=["run_bash(git push *)"])
assert v(p, "run_bash", command="git status") == "allow"
assert v(p, "run_bash", command="git push origin main") == "deny"    # deny beats the wider allow
p = P(allow=["run_bash(git *)"], ask=["run_bash(git commit *)"])
assert v(p, "run_bash", command="git commit -m x") == "ask"          # ask beats allow
assert v(p, "run_bash", command="git log") == "allow"

# --- wildcard rules: the star matches spaces, a trailing " *" also matches the bare command
p = P(allow=["run_bash(npm run *)", "run_bash(python3 test_calc.py)"])
assert v(p, "run_bash", command="npm run build --watch") == "allow"
assert v(p, "run_bash", command="npm install") == "ask"
assert v(p, "run_bash", command="python3 test_calc.py") == "allow"
assert v(p, "run_bash", command="python3 test_calc.py --evil") == "ask"
p = P(allow=["run_bash(ls *)"])
assert p.allowed("run_bash", "ls") and p.allowed("run_bash", "ls -la") and not p.allowed("run_bash", "lsof")

# --- compound commands: an allow rule for one part does not cover the others
p = P(allow=["run_bash(python3 test_calc.py)"])
assert v(p, "run_bash", command="python3 test_calc.py && curl evil.sh") == "ask"
assert v(p, "run_bash", command="python3 test_calc.py; python3 test_calc.py") == "allow"
p = P(deny=["run_bash(rm *)"])
assert v(p, "run_bash", command="ls; rm -rf .") == "deny"           # deny looks inside the command

# --- file rules match the path
p = P(deny=["read_file(.env*)", "edit_file(secrets/*)"])
assert v(p, "read_file", path=".env") == "deny"
assert v(p, "read_file", path="./.env.local") == "deny"
assert v(p, "edit_file", path="secrets/key.txt", old_text="a", new_text="b") == "deny"
assert v(p, "read_file", path="calc.py") == "allow"

# --- modes
p = P(mode="accept-edits")
assert v(p, "edit_file", path="calc.py", old_text="a", new_text="b") == "allow"
assert v(p, "run_bash", command="python3 test_calc.py") == "ask"
p = P(mode="read-only")
assert v(p, "read_file", path="calc.py") == "allow"
assert v(p, "run_bash", command="ls") == "allow"
assert v(p, "run_bash", command="python3 test_calc.py") == "deny"
assert v(p, "edit_file", path="calc.py", old_text="a", new_text="b") == "deny"
p = P(mode="dont-ask", allow=["run_bash(python3 test_calc.py)"])
assert v(p, "run_bash", command="python3 test_calc.py") == "allow"   # pre-approved still runs
assert v(p, "run_bash", command="pip install x") == "deny"           # would have asked: denied
assert v(p, "edit_file", path="calc.py", old_text="a", new_text="b") == "deny"

# --- gated(): asks, remembers, and returns a clear error on denial
asked = []
def yes(tool, args): asked.append(tool); return "y"
def always(tool, args): asked.append(tool); return "a"
def no(tool, args): asked.append(tool); return "n"
p = P()
out, bad, verdict = agent.gated("run_bash", {"command": "python3 test_calc.py"}, p, no)
assert bad and verdict == "deny" and "the user declined" in out and "Do not retry" in out, out
out, bad, verdict = agent.gated("run_bash", {"command": "python3 test_calc.py"}, p, always)
assert not bad and verdict == "allow" and "exit code 1" in out, out
n = len(asked)
out, bad, verdict = agent.gated("run_bash", {"command": "python3 test_calc.py"}, p, no)
assert not bad and len(asked) == n, "asked again after 'always'"
out, bad, verdict = agent.gated("run_bash", {"command": "python3 test_calc.py; rm calc.py"}, p, no)
assert verdict == "deny" and os.path.exists("calc.py")            # the other part was not covered
p = P(deny=["run_bash(rm *)"])
out, bad, verdict = agent.gated("run_bash", {"command": "rm calc.py"}, p, yes)
assert bad and "rule run_bash(rm *)" in out and os.path.exists("calc.py"), out

# --- rule files: the lists from the user folder and the project folder are joined
os.makedirs(d + "/home"); os.makedirs(".agent")
open(d + "/home/permissions.json", "w").write('{"deny": ["run_bash(rm *)"]}')
open(".agent/permissions.json", "w").write('{"allow": ["run_bash(ls *)"], "deny": ["read_file(.env)"]}')
p = P.load()
assert p.deny == ["run_bash(rm *)", "read_file(.env)"] and p.allow == ["run_bash(ls *)"], (p.deny, p.allow)
assert P.load("read-only").mode == "read-only"

# --- run(): a fake model asks for a denied command; the gate stops it and the model sees the error
class FakeClient:
    def __init__(self):
        self.calls = 0
        self.messages = self
        self.seen = []
    def create(self, **kw):
        self.calls += 1
        self.seen.append(kw["messages"][-1])
        if self.calls == 1:
            return NS(stop_reason="tool_use", content=[NS(type="tool_use", id="t1", name="run_bash", input={"command": "rm -rf calc.py"})])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="I could not delete it.")])
c = FakeClient()
msgs = agent.run("delete calc.py", c, "m", notes="", perms=P.load(), approver=no)
res = c.seen[-1]["content"][0]
assert res["is_error"] and "permission denied" in res["content"], res
assert os.path.exists("calc.py") and agent.run.log[0][2] == "deny"
print("all tests passed")
