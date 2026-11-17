"""Draw the project diagrams (light + dark) into docs/img/.
Needs svgkit.py from the chart-draw skill: set CHART_DRAW to its scripts folder, e.g.
  CHART_DRAW=~/Documents/claude_code_workplace/.claude/skills/chart-draw/scripts python3 docs/diagrams.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("CHART_DRAW") or os.path.expanduser("~/Documents/claude_code_workplace/.claude/skills/chart-draw/scripts"))
from svgkit import Diagram
OUT = os.path.join(HERE, "img")

def save(d, name): d.save(os.path.join(OUT, name + ".svg"))

# ------------------------------------------------------------------ overview
d = Diagram(1200, 800)
d.title(40, 44, "Architecture · the finished agent (episode 13)")
d.note(40, 70, "Orange: the core loop. Each box says which episode adds it. Dashed: optional or side paths.", 16)
d.box(40, 100, 150, 70, "You", None, kind="plain", title_size=22)
d.arrow([(194, 135), (496, 135)], color="ink")
d.box(500, 100, 340, 70, "Command-line REPL", "Episode 13", kind="main", title_size=22, sub_size=16)
d.arrow([(670, 174), (670, 232)], color="accent")
d.box(500, 238, 340, 150, "Agent loop", "call the model → check stop_reason\nrun the tool → append the result\nEpisode 1", kind="accent", title_size=26, sub_size=17)
d.box(940, 263, 220, 100, "Model API", "Claude / DeepSeek", kind="main", title_size=22, sub_size=16)
d.arrow([(846, 313), (934, 313)], color="ink", both=True)
d.box(40, 212, 300, 80, "System prompt + notes file", "Episode 3", kind="plain", title_size=18, sub_size=15)
d.arrow([(344, 252), (494, 285)], color="grey")
d.box(40, 330, 300, 80, "Context management", "Episode 5 · compact when full", kind="plain", title_size=18, sub_size=15)
d.arrow([(344, 370), (494, 350)], color="grey")
d.arrow([(670, 392), (670, 458)], color="accent", label="model asks for a tool", label_size=15)
d.box(500, 464, 340, 90, "Permission gate", "Episode 4 · allow · ask · deny", kind="main", title_size=22, sub_size=16)
d.arrow([(670, 558), (670, 628)], color="accent", label="only allowed calls run", label_size=15)
d.box(500, 634, 340, 90, "Tools", "Episode 2 · read · grep · edit · bash", kind="plain", title_size=22, sub_size=16)
d.box(940, 464, 220, 90, "Hooks", "Episode 8", kind="dashed", title_size=20, sub_size=15)
d.arrow([(936, 509), (846, 509)], color="grey", dashed=True)
d.box(940, 634, 220, 90, "Subagents", "Episode 7 · a new loop", kind="dashed", title_size=20, sub_size=15)
d.arrow([(846, 679), (934, 679)], color="grey", dashed=True)
d.box(40, 464, 300, 90, "MCP and skills", "Episode 11 · tools others wrote", kind="dashed", title_size=19, sub_size=15)
d.arrow([(344, 509), (494, 509)], color="grey", dashed=True)
d.box(40, 634, 300, 90, "Memory", "Episode 9 · a notes folder", kind="dashed", title_size=20, sub_size=15)
d.arrow([(344, 679), (494, 679)], color="grey", dashed=True)
d.note(40, 776, "Episode 10 (always on): an inbox and timers feed events into the same loop; results leave through an outbox. Episodes 6 and 12: plans, testing.", 15)
save(d, "overview")

# ------------------------------------------------------------------ series map
d = Diagram(1200, 640)
d.title(40, 44, "Course map · 5 parts, 13 episodes")
d.note(40, 70, "Each episode adds one piece to the code from the last one. Orange: published.", 16)
parts = [("A  Core", ["1  The loop", "2  Tools", "3  Prompt and notes"]), ("B  Trust and limits", ["4  Permissions", "5  Context"]),
         ("C  Working at scale", ["6  Plans and tasks", "7  Subagents", "8  Hooks"]), ("D  Beyond one session", ["9  Memory", "10  Always on", "11  MCP and skills"]),
         ("E  Ship it", ["12  Testing", "13  Put it together"])]
for k, (name, eps) in enumerate(parts):
    x = 40 + k * 228
    d.panel(x, 100, 212, 440, name, heading_size=16)
    for j, e in enumerate(eps):
        d.box(x + 14, 160 + j * 112, 184, 92, e, None, kind="accent" if e.startswith("1 ") else "plain", title_size=18)
    if k < 4:
        d.arrow([(x + 214, 130), (x + 238, 130)], color="grey")
d.note(40, 580, "A: it runs. B: you can trust it. C: it handles big tasks. D: it works over time. E: you can test and ship it.", 16)
save(d, "series-map")

# ------------------------------------------------------------------ part A
d = Diagram(1200, 520)
d.title(40, 44, "A  Core · loop, tools, prompt (episodes 1 to 3)")
d.box(40, 150, 260, 90, "System prompt + notes", "Episode 3", kind="plain", title_size=19, sub_size=16)
d.arrow([(304, 195), (396, 195)], color="grey")
d.box(400, 130, 300, 130, "Agent loop", "Episode 1", kind="accent", title_size=26, sub_size=17)
d.arrow([(704, 195), (796, 195)], color="ink", both=True)
d.box(800, 150, 220, 90, "Model API", None, kind="main", title_size=22)
d.arrow([(550, 264), (550, 336)], color="accent", label="tool_use → tool_result", label_size=15)
d.box(400, 342, 300, 110, "Tools", "Episode 2\nread · grep · edit · bash", kind="plain", title_size=22, sub_size=16)
d.note(40, 490, "After this part: a minimal agent that reads files, edits files and runs commands.", 17)
save(d, "part-a")

# ------------------------------------------------------------------ part B
d = Diagram(1200, 560)
d.title(40, 44, "B  Trust and limits · permissions and context (episodes 4 and 5)")
d.panel(40, 80, 540, 420, "Episode 4 · Permissions")
d.box(70, 150, 200, 80, "Model asks for a tool", None, kind="plain", title_size=16)
d.arrow([(274, 190), (326, 190)], color="accent")
d.box(330, 140, 220, 100, "Permission gate", "checks the rules", kind="main", title_size=20, sub_size=15)
for k, (t, c) in enumerate([("allow → run it", "#1e7a3c"), ("ask → ask you first", "#d4600b"), ("deny → return an error", "#c23b22")]):
    d.text(100, 300 + k * 50, t, 19, c, 700)
d.note(70, 470, "Rule order: deny, then ask, then allow", 15)
d.panel(620, 80, 540, 420, "Episode 5 · Context")
for k, (w, t) in enumerate([(110, "turn 1"), (250, "turn 5"), (400, "turn 20")]):
    d.bar(660, 170 + k * 62, w, 34, color="#d4600b" if k == 2 else "#d8d4cc")
    d.text(670 + w, 196 + k * 62, t, 16, "#6b6b6b")
d.box(660, 380, 460, 80, "Compact: old turns become a summary", "triggered near the limit", kind="accent", title_size=17, sub_size=15)
save(d, "part-b")

# ------------------------------------------------------------------ part C
d = Diagram(1200, 560)
d.title(40, 44, "C  Working at scale · plans, subagents, hooks (episodes 6 to 8)")
d.panel(40, 80, 360, 420, "Episode 6 · Plans")
d.box(70, 150, 300, 80, "Plan mode", "read-only tools only", kind="plain", title_size=19, sub_size=15)
d.arrow([(220, 234), (220, 286)], color="accent")
d.box(70, 292, 300, 80, "Task list", "the model ticks items off", kind="accent", title_size=19, sub_size=15)
d.panel(420, 80, 360, 420, "Episode 7 · Subagents")
d.box(450, 150, 300, 80, "Main loop", "a big task", kind="main", title_size=19, sub_size=15)
d.arrow([(600, 234), (600, 286)], color="accent", label="a clear brief", label_size=14)
d.box(450, 292, 300, 80, "Child loop", "fresh context · fewer tools", kind="plain", title_size=19, sub_size=14)
d.arrow([(760, 332), (700, 332)], color="grey")
d.text(450, 410, "Returns one short result", 17, "#d4600b", 700)
d.panel(800, 80, 360, 420, "Episode 8 · Hooks")
d.box(830, 150, 300, 70, "Before a tool call", "allow · block · log", kind="plain", title_size=18, sub_size=14)
d.arrow([(980, 224), (980, 262)], color="accent")
d.box(830, 266, 300, 70, "Run the tool", None, kind="main", title_size=19)
d.arrow([(980, 340), (980, 378)], color="accent")
d.box(830, 382, 300, 70, "After a tool call", "log · check", kind="plain", title_size=18, sub_size=14)
save(d, "part-c")

# ------------------------------------------------------------------ part D
d = Diagram(1200, 560)
d.title(40, 44, "D  Beyond one session · memory, always on, MCP (episodes 9 to 11)")
d.panel(40, 80, 360, 420, "Episode 9 · Memory")
d.box(70, 150, 300, 80, "Notes folder", "only what can't be looked up", kind="plain", title_size=19, sub_size=14)
d.arrow([(220, 234), (220, 286)], color="accent", label="index loaded at start", label_size=14)
d.box(70, 292, 300, 80, "New session", None, kind="main", title_size=19)
d.panel(420, 80, 360, 420, "Episode 10 · Always on")
d.box(450, 140, 300, 60, "Inbox · timers", None, kind="plain", title_size=18)
d.arrow([(600, 204), (600, 236)], color="accent")
d.box(450, 240, 300, 70, "The same loop", "one run at a time", kind="accent", title_size=18, sub_size=14)
d.arrow([(600, 314), (600, 346)], color="accent")
d.box(450, 350, 300, 60, "Outbox → chat app", None, kind="plain", title_size=18)
d.panel(800, 80, 360, 420, "Episode 11 · MCP and skills")
d.box(830, 150, 300, 80, "MCP server", "tools others wrote", kind="plain", title_size=19, sub_size=15)
d.arrow([(980, 234), (980, 286)], color="accent", label="list · call", label_size=14)
d.box(830, 292, 300, 80, "Our loop", "still behind the permission gate", kind="main", title_size=19, sub_size=13)
save(d, "part-d")

# ------------------------------------------------------------------ part E
d = Diagram(1200, 520)
d.title(40, 44, "E  Ship it · testing and putting it together (episodes 12 and 13)")
d.panel(40, 80, 540, 380, "Episode 12 · Testing and debugging")
d.box(70, 150, 220, 80, "Fixed tasks", "3 to 5 of them", kind="plain", title_size=19, sub_size=15)
d.arrow([(294, 190), (346, 190)], color="accent")
d.box(350, 150, 200, 80, "Agent", None, kind="main", title_size=20)
d.arrow([(450, 234), (450, 286)], color="accent")
d.box(70, 292, 480, 80, "Full trace · turns · tokens", "change one thing, then compare", kind="accent", title_size=19, sub_size=15)
d.panel(620, 80, 540, 380, "Episode 13 · Put it together")
d.box(650, 150, 480, 80, "Command-line REPL", "type and watch output stream", kind="main", title_size=20, sub_size=15)
d.arrow([(890, 234), (890, 286)], color="accent")
d.box(650, 292, 480, 80, "Every earlier part", "loop · tools · permissions · context · memory …", kind="plain", title_size=19, sub_size=14)
save(d, "part-e")
print("ok")
