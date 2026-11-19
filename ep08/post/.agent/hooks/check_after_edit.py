"""After-hook: after an edit to a post file, run the limit check and tell the model the result."""
import json, subprocess, sys
d = json.load(sys.stdin)
path = d["tool_input"].get("path", "")
if path.endswith("-draft.md") or "xhs-" in path:
    out = subprocess.run([sys.executable, "tools/check_post.py", path], capture_output=True, text=True).stdout.strip()
    sys.stderr.write("limit check after your edit: " + out.replace("\n", "; "))
    sys.exit(2)       # exit 2 on an after-hook: the message is shown to the model
