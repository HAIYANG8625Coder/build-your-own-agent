"""After-hook: append one line per tool call to .agent/calls.log (an audit trail). Exit 0: no comment on the call."""
import json, sys, time
d = json.load(sys.stdin)
open(".agent/calls.log", "a").write("%s %s\n" % (time.strftime("%H:%M:%S"), d["tool_name"]))
