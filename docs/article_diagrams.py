"""Diagrams for the episode articles (English, light + dark) into docs/img/.
CHART_DRAW=<chart-draw scripts folder> python3 docs/article_diagrams.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("CHART_DRAW") or os.path.expanduser("~/Documents/claude_code_workplace/.claude/skills/chart-draw/scripts"))
from svgkit import Diagram
OUT = os.path.join(HERE, "img")
def save(d, name): d.save(os.path.join(OUT, name + ".svg"))

# ---------------- episode 1
d = Diagram(1200, 640)
d.title(40, 50, "The agent loop · run() in agent.py")
d.note(40, 80, "Orange: the path each turn takes. Grey: the loop ends.", 17)
d.box(40, 130, 220, 100, "messages", "user · assistant\ntool_result", kind="main", title_size=24, sub_size=17)
d.box(330, 130, 270, 100, "Call the model", "client.messages.create", kind="plain", title_size=22, sub_size=17)
d.arrow([(266, 180), (324, 180)], color="accent"); d.step(150, 118, "1", 26, "middle"); d.step(465, 118, "2", 26, "middle")
d.arrow([(606, 180), (664, 180)], color="accent")
d.box(670, 130, 270, 100, "Check stop_reason", "is it tool_use?", kind="main", title_size=22, sub_size=17); d.step(805, 118, "3", 26, "middle")
d.arrow([(946, 180), (1004, 180)], color="grey", label="no", label_size=17)
d.box(1010, 130, 150, 100, "Return the answer", "end_turn", kind="faded", title_size=17, sub_size=16)
d.arrow([(805, 236), (805, 384)], color="accent", label="yes: tool_use", label_size=17)
d.box(670, 390, 270, 100, "Run the tool", "run_tool(...)\nour code does the work", kind="accent", title_size=22, sub_size=16); d.step(805, 540, "4", 26, "middle")
d.arrow([(664, 440), (606, 440)], color="accent")
d.box(330, 390, 270, 100, "Wrap as tool_result", "same id as the request", kind="plain", title_size=21, sub_size=17)
d.arrow([(324, 440), (266, 440)], color="accent")
d.box(40, 390, 220, 100, "Append to messages", "as a user message", kind="plain", title_size=19, sub_size=17); d.step(465, 540, "5", 26, "middle")
d.arrow([(150, 384), (150, 236)], color="accent", width=4, label="back to step 2", label_size=17)
d.note(40, 610, "The whole loop: call the model, check stop_reason, run the tool, append the result, repeat.", 19)
save(d, "ep01-loop")

d = Diagram(1200, 680)
d.title(40, 52, "One question, two turns")
d.note(40, 80, "Orange: requests. Grey dashed: replies.", 17)
cols = [("User", "", 140, "plain"), ("agent.py", "our code", 440, "main"), ("Model", "Claude / DeepSeek", 760, "accent"), ("list_files", "tool function", 1050, "plain")]
for name, sub, cx, kind in cols:
    d.box(cx - 105, 104, 210, 76, name, sub or None, kind=kind, title_size=20, sub_size=15)
    d.line(cx, 186, cx, 650, color="#c9c4ba", width=2, dash="3 7")
msgs = [(0, 1, "What is in this folder?", False), (1, 2, "messages.create(messages)", False), (2, 1, "tool_use · list_files", True),
        (1, 3, "run_tool → list_files(\".\")", False), (3, 1, "agent.py  test_loop.py", True), (1, 2, "messages.create(+ result)", False),
        (2, 1, "end_turn · text answer", True), (1, 0, "This folder has two files", True)]
for k, (a, b, text, ret) in enumerate(msgs):
    y = 232 + k * 58; xa, xb = cols[a][2], cols[b][2]; s = 1 if xb > xa else -1
    d.arrow([(xa + s * 8, y), (xb - s * 10, y)], color="grey" if ret else "accent", dashed=ret, width=2 if ret else 2.5)
    lx = (760 + 1050) / 2 if 3 in (a, b) else (xa + xb) / 2
    d.text(lx, y - 12, "%d. %s" % (k + 1, text), 18, "#6b6b6b" if ret else "#d4600b", 400 if ret else 700, "middle")
save(d, "ep01-sequence")

d = Diagram(1200, 640)
d.title(40, 50, "The model has no memory: every call resends the whole messages list")
cols = [("Call 1 · 1 message", 130, [("user", "question", "plain")]),
        ("Call 2 · 3 messages", 500, [("user", "question", "plain"), ("assistant", "tool_use", "plain"), ("user", "tool_result", "plain")]),
        ("Call 3 · 5 messages", 870, [("user", "question", "plain"), ("assistant", "tool_use", "plain"), ("user", "tool_result", "plain"), ("assistant", "tool_use", "plain"), ("user", "tool_result", "accent")])]
for name, x, items in cols:
    d.text(x + 100, 118, name, 20, "#1f1f1f", 700, "middle")
    for j, (role, what, kind) in enumerate(items):
        d.box(x, 140 + j * 74, 200, 62, role, what, kind="accent" if kind == "accent" else "plain", title_size=18, sub_size=16)
d.arrow([(340, 200), (490, 200)], color="grey", dashed=True); d.arrow([(710, 200), (860, 200)], color="grey", dashed=True)
d.text(600, 610, "The longer the conversation, the more each call sends, and the more it costs", 20, "#d4600b", 700, "middle")
save(d, "ep01-stateless")

d = Diagram(1200, 600)
d.title(40, 50, "Claude Code's three phases · and our minimal version")
d.panel(40, 90, 480, 440, "Claude Code (official docs)"); d.panel(680, 90, 480, 440, "Our agent.py")
rows = [("Gather context", "read files, search", "list_files", "this episode", "accent"), ("Take action", "edit files, run commands", "edit_file · run_bash", "next episode", "dashed"), ("Verify results", "run the tests, look again", "feed the output back", "same loop", "dashed")]
for k, (a, sub, mine, tag, kind) in enumerate(rows):
    y = 150 + k * 125
    d.box(70, y, 420, 96, a, sub, kind="main", title_size=22, sub_size=17); d.box(710, y, 420, 96, mine, tag, kind=kind, title_size=21, sub_size=17)
    d.arrow([(496, y + 48), (704, y + 48)], color="accent" if kind == "accent" else "grey", dashed=kind != "accent", width=2.5)
d.note(40, 572, "The phases blend together and repeat until the model's reply has no tool calls.", 18)
save(d, "ep01-three-phases")

d = Diagram(1200, 520)
d.title(40, 50, "Same code, two models: change one environment variable")
d.box(450, 190, 300, 130, "agent.py", "Anthropic message format\ntool_use · tool_result", kind="main", title_size=26, sub_size=17)
d.box(40, 190, 300, 130, "Claude API", "claude-haiku-5-5", kind="plain", title_size=24, sub_size=17)
d.arrow([(446, 255), (346, 255)], color="ink", both=True)
d.text(110, 360, "PROVIDER=claude", 20, "#6b6b6b", 700); d.text(95, 388, "ANTHROPIC_API_KEY", 18, "#8a8a8a")
d.box(860, 190, 300, 130, "DeepSeek API", "deepseek-flash", kind="accent", title_size=24, sub_size=17)
d.arrow([(754, 255), (854, 255)], color="accent", both=True)
d.text(880, 360, "PROVIDER=deepseek", 20, "#d4600b", 700); d.text(895, 388, "DEEPSEEK_API_KEY", 18, "#8a8a8a")
d.text(1010, 150, "used in the videos", 20, "#d4600b", 700, "middle"); d.text(1010, 172, "api.deepseek.com/anthropic", 17, "#8a8a8a", 400, "middle")
d.note(40, 480, "DeepSeek offers an Anthropic-compatible endpoint, so only the key, the address and the model name change.", 18)
save(d, "ep01-providers")

# ---------------- episode 2
d = Diagram(1200, 560)
d.title(40, 52, "A tool is four things")
rows = [("Name", "read_file", "plain"), ("Description", "Read a text file and return its lines…", "plain"), ("Input schema", "{ path: string }", "plain"), ("The function", "def read_file(path): …", "dashed")]
for k, (a, b, kind) in enumerate(rows):
    y = 90 + k * 106; d.text(50, y + 54, a, 22, "#1f1f1f", 700); d.box(300, y, 560, 82, b, None, kind=kind, title_size=21)
d.line(900, 96, 900, 392, color="#d4600b", width=4); d.text(920, 225, "The model sees these", 22, "#d4600b", 700); d.text(920, 258, "name · description · schema", 17, "#6b6b6b")
d.line(900, 412, 900, 492, color="#8a8a8a", width=4); d.text(920, 458, "Only our code sees this", 22, "#6b6b6b", 700)
save(d, "ep02-tool-anatomy")

d = Diagram(1200, 560)
d.title(40, 52, "edit_file: old_text must appear, and appear exactly once")
cases = [(60, "0 matches", "return a * b", "not in the file", "error", "plain", 0), (440, "1 match", "return a - b", "only one place", "edited calc.py", "accent", 1), (820, "2+ matches", "result", "several places", "error", "plain", 4)]
for x, head, old, why, out, kind, cnt in cases:
    d.text(x + 150, 118, head, 22, "#d4600b" if kind == "accent" else "#1f1f1f", 700, "middle")
    d.box(x, 150, 300, 90, "old_text = " + old, why, kind="plain", title_size=18, sub_size=16)
    d.arrow([(x + 150, 246), (x + 150, 318)], color="accent" if kind == "accent" else "grey")
    if kind == "accent": d.box(x, 324, 300, 100, "edited calc.py", "replaced", kind="accent", title_size=21, sub_size=17)
    else: d.box(x, 324, 300, 100, "error", "'old_text' appears %d times" % cnt, kind="dashed", title_size=21, sub_size=16)
d.note(60, 500, "The error says how many times it matched, so the model knows how to fix the call.", 19)
save(d, "ep02-edit-match")

d = Diagram(1200, 640)
d.title(40, 52, "An error is just another result: the model recovers on its own")
d.note(40, 84, "Orange: requests. Grey dashed: replies.", 17)
cols = [("Model", 220, "accent"), ("agent.py", 700, "main")]
for name, cx, kind in cols:
    d.box(cx - 120, 110, 240, 70, name, None, kind=kind, title_size=22); d.line(cx, 186, cx, 620, color="#c9c4ba", width=2, dash="3 7")
msgs = [(0, 1, "1. edit_file (file not read yet)", False), (1, 0, "2. error: read the file first", True), (0, 1, "3. read_file(calc.py)", False),
        (1, 0, "4. file contents", True), (0, 1, "5. edit_file (same change)", False), (1, 0, "6. edited calc.py", True)]
for k, (a, b, text, ret) in enumerate(msgs):
    y = 235 + k * 66; xa, xb = cols[a][1], cols[b][1]; s = 1 if xb > xa else -1
    d.arrow([(xa + s * 8, y), (xb - s * 10, y)], color="grey" if ret else "accent", dashed=ret, width=2 if ret else 2.5)
    d.text((xa + xb) / 2, y - 14, text, 20, "#6b6b6b" if ret else "#d4600b", 400 if ret else 700, "middle")
save(d, "ep02-error-recovery")

d = Diagram(1200, 520)
d.title(40, 52, "Don't flood the context: cut long output")
d.text(60, 130, "Tool output", 21, "#1f1f1f", 700); d.bar(60, 150, 1000, 44, color="#d8d4cc"); d.text(1075, 182, "20,000 chars", 18, "#6b6b6b")
d.text(60, 250, "Returned to the model (our code)", 21, "#1f1f1f", 700); d.bar(60, 270, 200, 44, color="#d4600b")
d.text(275, 302, "at most 4,000 chars + \"... cut off. Ask for less.\"", 18, "#d4600b", 700)
d.panel(60, 350, 1080, 130)
d.text(90, 392, "Claude Code (official docs)", 21, "#1f1f1f", 700)
d.text(90, 430, "Bash output over about 30,000 characters is saved to a file, with a short preview kept", 19, "#6b6b6b")
d.text(90, 462, "Anthropic's article: tool responses default to at most 25,000 tokens in Claude Code", 19, "#6b6b6b")
save(d, "ep02-truncation")

d = Diagram(1200, 580)
d.title(40, 52, "Boundaries: a path check and a timeout")
d.panel(40, 90, 620, 440, "The project folder")
for k, nm in enumerate(["read_file", "grep", "edit_file"]): d.box(80 + k * 190, 160, 170, 80, nm, "checks the path", kind="plain", title_size=18, sub_size=15)
d.text(80, 300, "Path inside the project folder: allowed", 20, "#1e7a3c", 700)
d.panel(760, 90, 400, 440, "Other folders")
d.arrow([(640, 200), (756, 200)], color="grey"); d.text(790, 190, "for example ../p-other", 18, "#6b6b6b"); d.text(790, 300, "✗ path outside: refused", 20, "#c23b22", 700)
d.box(80, 400, 300, 90, "run_bash", "not covered by the path check", kind="dashed", title_size=21, sub_size=16)
d.arrow([(384, 445), (754, 445)], color="accent"); d.text(400, 432, "can reach other folders", 18, "#d4600b", 700)
d.text(80, 520, "So real permissions come later (episode 4).", 20, "#d4600b", 700)
save(d, "ep02-boundary")

d = Diagram(1200, 700)
d.title(40, 52, "Our four tools · Claude Code's built-in tools")
d.panel(40, 90, 440, 570, "Ours (this episode)"); d.panel(660, 90, 500, 570, "Claude Code (official docs)")
pairs = [("read_file", "Read", "no permission prompt"), ("grep", "Grep", "off by default on macOS / Linux"), ("run_bash", "Bash", "asks first"), ("edit_file", "Edit", "asks first")]
for k, (a, b, c) in enumerate(pairs):
    y = 150 + k * 108
    d.box(70, y, 380, 84, a, None, kind="plain", title_size=21); d.box(690, y, 440, 84, b, c, kind="main", title_size=21, sub_size=16)
    d.arrow([(456, y + 42), (684, y + 42)], color="accent", width=2.5)
d.text(690, 630, "Also: Write · Glob\nWebFetch · WebSearch · subagents", 19, "#6b6b6b")
save(d, "ep02-compare")

d = Diagram(1200, 600)
d.title(40, 52, "A real run: 5 turns")
d.note(40, 84, "Task: the tests in this folder fail. Find out why and fix it.", 19)
rows = [("1", "run_bash", "ls -la", "plain"), ("2", "read_file × 2", "calc.py and test_calc.py (two requests in one reply)", "accent"),
        ("3", "edit_file", "return a - b  →  return a + b", "plain"), ("4", "run_bash", "python3 test_calc.py", "plain"), ("5", "end_turn", "no more tool calls: the loop ends with an answer", "main")]
for k, (t, a, b, kind) in enumerate(rows):
    y = 110 + k * 96
    d.text(60, y + 50, "Turn %s" % t, 22, "#6b6b6b", 700); d.box(200, y, 260, 76, a, None, kind=kind, title_size=21); d.text(490, y + 46, b, 20, "#1f1f1f", 600)
save(d, "ep02-run-trace")
print("ok")
