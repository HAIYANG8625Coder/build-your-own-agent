"""Draw the project diagrams (light + dark) into docs/img/.
Needs svgkit.py from the chart-draw skill: set CHART_DRAW to its scripts folder, e.g.
  CHART_DRAW=~/Documents/claude_code_workplace/.claude/skills/chart-draw/scripts python3 docs/diagrams.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("CHART_DRAW") or os.path.expanduser("~/Documents/claude_code_workplace/.claude/skills/chart-draw/scripts"))
from svgkit import Diagram, FONT
OUT = os.path.join(HERE, "img")
CJK = FONT + ", 'PingFang SC', 'Noto Sans CJK SC'"

def save(d, name): d.save(os.path.join(OUT, name + ".svg"))

# ------------------------------------------------------------------ overview
d = Diagram(1200, 800, CJK)
d.title(40, 44, "架构总览 · 做完以后的这个 Agent（第 13 集）")
d.note(40, 70, "橙色：核心循环。每个框标出它在哪一集做。虚线：可选或旁路。", 16)
d.box(40, 100, 150, 70, "你", None, kind="plain", title_size=22)
d.arrow([(194, 135), (496, 135)], color="ink")
d.box(500, 100, 340, 70, "命令行 REPL", "第 13 集", kind="main", title_size=22, sub_size=16)
d.arrow([(670, 174), (670, 232)], color="accent")
d.box(500, 238, 340, 150, "Agent 循环", "调用模型 → 看 stop_reason\n执行工具 → 追加结果\n第 1 集", kind="accent", title_size=26, sub_size=17)
d.box(940, 263, 220, 100, "模型 API", "Claude / DeepSeek", kind="main", title_size=22, sub_size=16)
d.arrow([(846, 313), (934, 313)], color="ink", both=True)
d.box(40, 212, 300, 80, "系统提示 + 笔记文件", "第 3 集", kind="plain", title_size=19, sub_size=15)
d.arrow([(344, 252), (494, 285)], color="grey")
d.box(40, 330, 300, 80, "上下文管理", "第 5 集 · 快满时压缩", kind="plain", title_size=19, sub_size=15)
d.arrow([(344, 370), (494, 350)], color="grey")
d.arrow([(670, 392), (670, 458)], color="accent", label="模型要用工具", label_size=15)
d.box(500, 464, 340, 90, "权限闸门", "第 4 集 · 允许 · 询问 · 拒绝", kind="main", title_size=22, sub_size=16)
d.arrow([(670, 558), (670, 628)], color="accent", label="放行的才执行", label_size=15)
d.box(500, 634, 340, 90, "工具", "第 2 集 · read · grep · edit · bash", kind="plain", title_size=22, sub_size=16)
d.box(940, 464, 220, 90, "Hooks", "第 8 集", kind="dashed", title_size=20, sub_size=15)
d.arrow([(936, 509), (846, 509)], color="grey", dashed=True)
d.box(940, 634, 220, 90, "子 Agent", "第 7 集 · 新的循环", kind="dashed", title_size=20, sub_size=15)
d.arrow([(846, 679), (934, 679)], color="grey", dashed=True)
d.box(40, 464, 300, 90, "MCP 与 skills", "第 11 集 · 别人写好的工具", kind="dashed", title_size=19, sub_size=15)
d.arrow([(344, 509), (494, 509)], color="grey", dashed=True)
d.box(40, 634, 300, 90, "记忆", "第 9 集 · 笔记文件夹", kind="dashed", title_size=20, sub_size=15)
d.arrow([(344, 679), (494, 679)], color="grey", dashed=True)
d.note(40, 776, "第 10 集（一直在线）：收件箱和定时器把事件送进同一个循环，结果从发件箱发出去。第 6、12 集：计划模式，测试和调试。", 16)
save(d, "overview")

# ------------------------------------------------------------------ series map
d = Diagram(1200, 640, CJK)
d.title(40, 44, "课程地图 · 5 个部分，13 集")
d.note(40, 70, "每一集都在上一集的代码上加一块。橙色：已发布。", 16)
parts = [("A 核心", ["1 循环", "2 工具", "3 提示和笔记"]), ("B 信任和边界", ["4 权限", "5 上下文"]),
         ("C 规模化", ["6 计划和任务清单", "7 子 Agent", "8 Hooks"]), ("D 跨会话", ["9 记忆", "10 一直在线", "11 MCP 和 skills"]),
         ("E 交付", ["12 测试和调试", "13 合起来"])]
for k, (name, eps) in enumerate(parts):
    x = 40 + k * 228
    d.panel(x, 100, 212, 440, name)
    for j, e in enumerate(eps):
        d.box(x + 14, 160 + j * 112, 184, 92, e, None, kind="accent" if e.startswith("1 ") else "plain", title_size=19)
    if k < 4:
        d.arrow([(x + 214, 130), (x + 238, 130)], color="grey")
d.note(40, 580, "A：能跑起来。B：能放心用。C：能做大任务。D：能长期工作。E：能验证、能交付。", 17)
save(d, "series-map")

# ------------------------------------------------------------------ part A
d = Diagram(1200, 520, CJK)
d.title(40, 44, "A 核心 · 循环、工具、提示（第 1 到 3 集）")
d.box(40, 150, 260, 90, "系统提示 + 笔记", "第 3 集", kind="plain", title_size=20, sub_size=16)
d.arrow([(304, 195), (396, 195)], color="grey")
d.box(400, 130, 300, 130, "Agent 循环", "第 1 集", kind="accent", title_size=26, sub_size=17)
d.arrow([(704, 195), (796, 195)], color="ink", both=True)
d.box(800, 150, 220, 90, "模型 API", None, kind="main", title_size=22)
d.arrow([(550, 264), (550, 336)], color="accent", label="tool_use → tool_result", label_size=15)
d.box(400, 342, 300, 110, "工具", "第 2 集\nread · grep · edit · bash", kind="plain", title_size=22, sub_size=16)
d.note(40, 490, "做完这一部分：一个能读文件、改文件、跑命令的最小 Agent。", 17)
save(d, "part-a")

# ------------------------------------------------------------------ part B
d = Diagram(1200, 560, CJK)
d.title(40, 44, "B 信任和边界 · 权限和上下文（第 4、5 集）")
d.panel(40, 80, 540, 420, "第 4 集 · 权限")
d.box(70, 150, 200, 80, "模型要用工具", None, kind="plain", title_size=18)
d.arrow([(274, 190), (326, 190)], color="accent")
d.box(330, 140, 220, 100, "权限闸门", "按规则判断", kind="main", title_size=20, sub_size=15)
for k, (t, c) in enumerate([("允许 → 直接执行", "#1e7a3c"), ("询问 → 问你", "#d4600b"), ("拒绝 → 返回错误", "#c23b22")]):
    d.text(100, 300 + k * 50, t, 19, c, 700)
d.note(70, 470, "规则顺序：拒绝，再询问，再允许", 15)
d.panel(620, 80, 540, 420, "第 5 集 · 上下文")
for k, (w, t) in enumerate([(110, "第 1 轮"), (250, "第 5 轮"), (400, "第 20 轮")]):
    d.bar(660, 170 + k * 62, w, 34, color="#d4600b" if k == 2 else "#d8d4cc")
    d.text(670 + w, 196 + k * 62, t, 16, "#6b6b6b")
d.box(660, 380, 460, 80, "压缩：旧的变摘要，近的保留", "接近上限时触发", kind="accent", title_size=18, sub_size=15)
save(d, "part-b")

# ------------------------------------------------------------------ part C
d = Diagram(1200, 560, CJK)
d.title(40, 44, "C 规模化 · 计划、子 Agent、Hooks（第 6 到 8 集）")
d.panel(40, 80, 360, 420, "第 6 集 · 计划")
d.box(70, 150, 300, 80, "计划模式", "只开只读工具", kind="plain", title_size=19, sub_size=15)
d.arrow([(220, 234), (220, 286)], color="accent")
d.box(70, 292, 300, 80, "任务清单", "模型一条条勾掉", kind="accent", title_size=19, sub_size=15)
d.panel(420, 80, 360, 420, "第 7 集 · 子 Agent")
d.box(450, 150, 300, 80, "主循环", "大任务", kind="main", title_size=19, sub_size=15)
d.arrow([(600, 234), (600, 286)], color="accent", label="一个清楚的任务", label_size=14)
d.box(450, 292, 300, 80, "子循环", "新的上下文 · 少量工具", kind="plain", title_size=19, sub_size=15)
d.arrow([(760, 332), (700, 332)], color="grey")
d.text(450, 410, "只带回一个短结果", 17, "#d4600b", 700)
d.panel(800, 80, 360, 420, "第 8 集 · Hooks")
d.box(830, 150, 300, 70, "工具调用之前", "可放行 · 拦下 · 记录", kind="plain", title_size=18, sub_size=14)
d.arrow([(980, 224), (980, 262)], color="accent")
d.box(830, 266, 300, 70, "执行工具", None, kind="main", title_size=19)
d.arrow([(980, 340), (980, 378)], color="accent")
d.box(830, 382, 300, 70, "工具调用之后", "记录 · 检查", kind="plain", title_size=18, sub_size=14)
save(d, "part-c")

# ------------------------------------------------------------------ part D
d = Diagram(1200, 560, CJK)
d.title(40, 44, "D 跨会话 · 记忆、一直在线、MCP（第 9 到 11 集）")
d.panel(40, 80, 360, 420, "第 9 集 · 记忆")
d.box(70, 150, 300, 80, "笔记文件夹", "只记查不到的", kind="plain", title_size=19, sub_size=15)
d.arrow([(220, 234), (220, 286)], color="accent", label="开始时加载索引", label_size=14)
d.box(70, 292, 300, 80, "新会话", None, kind="main", title_size=19)
d.panel(420, 80, 360, 420, "第 10 集 · 一直在线")
d.box(450, 140, 300, 60, "收件箱 · 定时器", None, kind="plain", title_size=18)
d.arrow([(600, 204), (600, 236)], color="accent")
d.box(450, 240, 300, 70, "同一个循环", "一次只跑一个", kind="accent", title_size=18, sub_size=14)
d.arrow([(600, 314), (600, 346)], color="accent")
d.box(450, 350, 300, 60, "发件箱 → 聊天软件", None, kind="plain", title_size=18)
d.panel(800, 80, 360, 420, "第 11 集 · MCP 和 skills")
d.box(830, 150, 300, 80, "MCP 服务器", "别人写好的工具", kind="plain", title_size=19, sub_size=15)
d.arrow([(980, 234), (980, 286)], color="accent", label="列出 · 调用", label_size=14)
d.box(830, 292, 300, 80, "我们的循环", "同样要过权限闸门", kind="main", title_size=19, sub_size=14)
save(d, "part-d")

# ------------------------------------------------------------------ part E
d = Diagram(1200, 520, CJK)
d.title(40, 44, "E 交付 · 测试和合起来（第 12、13 集）")
d.panel(40, 80, 540, 380, "第 12 集 · 测试和调试")
d.box(70, 150, 220, 80, "固定的任务", "3 到 5 个", kind="plain", title_size=19, sub_size=15)
d.arrow([(294, 190), (346, 190)], color="accent")
d.box(350, 150, 200, 80, "Agent", None, kind="main", title_size=20)
d.arrow([(450, 234), (450, 286)], color="accent")
d.box(70, 292, 480, 80, "完整轨迹 · 轮数 · token", "一次只改一处，再比较", kind="accent", title_size=19, sub_size=15)
d.panel(620, 80, 540, 380, "第 13 集 · 合起来")
d.box(650, 150, 480, 80, "命令行 REPL", "边输入边输出", kind="main", title_size=20, sub_size=15)
d.arrow([(890, 234), (890, 286)], color="accent")
d.box(650, 292, 480, 80, "前面所有部分", "循环 · 工具 · 权限 · 上下文 · 记忆 …", kind="plain", title_size=19, sub_size=15)
save(d, "part-e")
print("ok")
