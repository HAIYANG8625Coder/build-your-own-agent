"""Before-hook: nobody edits the publishing log by hand. Exit 2 = block, stderr = the reason."""
import json, sys
d = json.load(sys.stdin)
args = d["tool_input"]
text = args.get("path", "") if d["tool_name"] == "edit_file" else args.get("command", "")
if "posts.md" in text:
    sys.stderr.write("x-assistant/posts.md is the publishing log; only the publish step writes it")
    sys.exit(2)
