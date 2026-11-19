"""Test the hooks without an API key: python3 test_hooks.py"""
import json, os, shutil, sys, tempfile
from types import SimpleNamespace as NS

d = tempfile.mkdtemp()
shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox"), d + "/p")
os.chdir(d + "/p")
os.environ["AGENT_HOME"] = d + "/home"
import agent
agent.ROOT = os.path.realpath(d + "/p")
HOOKDIR = os.path.join(agent.ROOT, "hooks"); os.makedirs(HOOKDIR)
yes = lambda *a: "y"
never = lambda *a: (_ for _ in ()).throw(AssertionError("asked the user"))
perms = lambda mode="accept-edits": agent.Permissions(mode=mode)


def hook(name, body):
    path = os.path.join(HOOKDIR, name)
    open(path, "w").write(body)
    return "python3 " + path


# 1. a before-hook that exits 2 blocks the call, and its reason is what the model reads
guard = hook("guard.py", "import json,sys\nd=json.load(sys.stdin)\n"
             "if d['tool_input'].get('path','').endswith('NOTES.md'):\n"
             "    sys.stderr.write('NOTES.md is not edited by hand'); sys.exit(2)\n")
hooks = agent.Hooks([{"event": "PreToolUse", "matcher": "edit_file", "command": guard}])
agent.READ.add(agent.safe("NOTES.md"))
before = open("NOTES.md").read()
text, bad, verdict = agent.gated("edit_file", {"path": "NOTES.md", "old_text": "Notes", "new_text": "X"}, perms(), never, hooks)
assert bad and verdict == "deny" and "NOTES.md is not edited by hand" in text, text
assert open("NOTES.md").read() == before, "the file changed although the hook blocked it"
print("ok 1: exit 2 blocks, the model reads the reason, the file is untouched")

# 2. the same hook lets other files through (matcher + exit 0), and exit 0 does not approve: the user is still asked
agent.READ.add(agent.safe("README.md"))
asked = []
def ask(*a): asked.append(a[0]); return "y"
text, bad, verdict = agent.gated("edit_file", {"path": "README.md", "old_text": open("README.md").read()[:5], "new_text": "Hello"}, perms("default"), ask, hooks)
assert not bad and asked == ["edit_file"], (text, asked)
print("ok 2: exit 0 is no objection, not approval: the permission question still comes")

# 3. a hook that matches another tool is not run
log_before = len(hooks.log)
agent.gated("grep", {"pattern": "Notes"}, perms(), never, hooks)
assert len(hooks.log) == log_before
print("ok 3: the matcher limits a hook to its tools")

# 4. an after-hook runs once the tool has run; its message is added to the result
after = hook("after.py", "import json,sys\nd=json.load(sys.stdin)\nassert 'tool_result' in d\n"
             "sys.stderr.write('checked: ' + d['tool_name']); sys.exit(2)\n")
hooks = agent.Hooks([{"event": "PostToolUse", "matcher": "grep|read_file", "command": after}])
text, bad, verdict = agent.gated("read_file", {"path": "README.md"}, perms(), never, hooks)
assert not bad and text.endswith("[hook] checked: read_file"), text
print("ok 4: an after-hook cannot undo the call, it adds a note to the result")

# 5. a broken hook (exit 1) and a slow hook do not stop the tool
broken = hook("broken.py", "import sys\nsys.stderr.write('oops'); sys.exit(1)\n")
slow = hook("slow.py", "import time\ntime.sleep(5)\n")
agent.HOOK_TIMEOUT = 1
hooks = agent.Hooks([{"event": "PreToolUse", "matcher": "read_file", "command": broken},
                     {"event": "PreToolUse", "matcher": "read_file", "command": slow}])
text, bad, verdict = agent.gated("read_file", {"path": "README.md"}, perms(), never, hooks)
assert not bad and verdict == "allow" and [c for _, _, c, _ in hooks.log] == [1, -1], (text, hooks.log)
print("ok 5: a hook error or timeout is logged, the tool still runs")

# 6. the hook is handed the event as JSON on stdin; hooks.json is loaded from .agent/
seen = os.path.join(d, "seen.json")
spy = hook("spy.py", "import sys\nopen(%r,'w').write(sys.stdin.read())\n" % seen)
os.makedirs(".agent")
json.dump({"hooks": [{"event": "PreToolUse", "matcher": "run_bash", "command": spy}]}, open(".agent/hooks.json", "w"))
hooks = agent.Hooks.load()
agent.gated("run_bash", {"command": "echo hi"}, perms("dont-ask"), yes, hooks)
got = json.load(open(seen))
assert got["hook_event_name"] == "PreToolUse" and got["tool_name"] == "run_bash" and got["tool_input"] == {"command": "echo hi"}, got
print("ok 6: the hook gets the event as JSON on stdin")

# 7. a blocking hook holds even when the permission rules would allow the call
agent.READ.add(agent.safe("NOTES.md"))
hooks = agent.Hooks([{"event": "PreToolUse", "matcher": "edit_file", "command": guard}])
p = agent.Permissions(allow=["edit_file"], mode="accept-edits")
text, bad, verdict = agent.gated("edit_file", {"path": "NOTES.md", "old_text": "Notes", "new_text": "X"}, p, never, hooks)
assert bad and verdict == "deny"
print("ok 7: a hook's block beats an allow rule")
print("all passed")
