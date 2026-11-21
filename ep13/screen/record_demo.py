"""Record a REAL session of the finished agent (repl.py) in a pseudo-terminal, with every key typed and every byte printed, with times.
    python3 record_demo.py OUT.json
Keys are typed by this script (a few hundredths of a second apart), the answers come from the real model. Ctrl+C is a real
Ctrl+C: byte 0x03 written to the terminal, which the terminal turns into SIGINT for the agent. Needs DEEPSEEK_API_KEY and PROVIDER=deepseek
(or ANTHROPIC_API_KEY) in the environment."""
import fcntl, json, os, pty, random, re, select, shutil, signal, struct, sys, termios, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
EP13 = os.path.dirname(HERE)
OUT = sys.argv[1]
random.seed(13)

work_root = tempfile.mkdtemp()
shop = os.path.join(work_root, "shop")
shutil.copytree(os.path.join(EP13, "project"), shop)
home = os.path.join(work_root, "home")
os.makedirs(home)
env = dict(os.environ, AGENT_HOME=home, AGENT_MEMORY=os.path.join(work_root, "mem"), TERM="xterm", COLUMNS="104", LINES="28", PYTHONUNBUFFERED="1")
events = []
t0 = time.time()
buf = ""

def now(): return round(time.time() - t0, 3)

def spawn(args):
    global buf
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(shop)
        os.execvpe(sys.executable, [sys.executable, os.path.join(EP13, "repl.py")] + args, env)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 28, 104, 0, 0))
    buf = ""
    return pid, fd

def pump(fd, seconds=0.05):
    """read whatever the program printed, record it, return it"""
    global buf
    got = ""
    r, _, _ = select.select([fd], [], [], seconds)
    while r:
        try:
            data = os.read(fd, 4096)
        except OSError:
            data = b""
        if not data:
            break
        text = data.decode("utf-8", "replace")
        events.append([now(), "o", text])
        buf += text
        got += text
        r, _, _ = select.select([fd], [], [], 0.02)
    return got

def wait_for(fd, pattern, timeout=120, quiet=0.0):
    deadline = time.time() + timeout
    last = time.time()
    start = len(buf)
    while time.time() < deadline:
        got = pump(fd, 0.1)
        if got:
            last = time.time()
        if re.search(pattern, buf[start:]) and time.time() - last >= quiet:
            return True
    raise TimeoutError("waiting for %r; tail: %r" % (pattern, buf[-300:]))

def type_text(fd, text, delay=(0.035, 0.09)):
    for ch in text:
        os.write(fd, ch.encode())
        events.append([now(), "i", ch])
        pump(fd, random.uniform(*delay))

def mark(label): events.append([now(), "m", label])

def prompt(fd, text, label=None, wait="\n> $"):
    if label: mark(label)
    pump(fd, 0.6)
    type_text(fd, text)
    pump(fd, 0.3)
    os.write(fd, b"\n")
    events.append([now(), "i", "\n"])
    # permission questions may come first: answer "a" (always this session) once per kind
    deadline = time.time() + 240
    start = len(buf)
    while time.time() < deadline:
        pump(fd, 0.2)
        tail = buf[start:]
        if re.search(r"\[n\] no > $", tail):
            mark("permission")
            pump(fd, 1.8)             # a person reads the question first
            type_text(fd, "a", delay=(0.2, 0.3))
            os.write(fd, b"\n"); events.append([now(), "i", "\n"])
            start = len(buf)
            continue
        if re.search(wait, tail) and re.search(r"> $", tail):
            pump(fd, 0.5)
            if buf.endswith("> "):
                return
    raise TimeoutError("turn did not finish: %r" % buf[-300:])

# ---- session 1
pid, fd = spawn([])
wait_for(fd, r"> $", 40)
prompt(fd, "What does cart.py do? One sentence.", "1 一个问题，答案一段一段出现（流式）")
prompt(fd, "Which file holds the tax rate?", "2 接着问：它记得上一个问题")
prompt(fd, "Change the tax rate to 8% and update whatever else needs it.", "3 改税率：第一次改文件，它先问你")
prompt(fd, "List every file you changed in this chat, one path per line, nothing else.", "4 这次聊天里，它改了哪些文件？")
# Ctrl+C in the middle of a turn
mark("5 按 Ctrl+C：停掉这一轮，聊天还在")
pump(fd, 0.6)
type_text(fd, "Read every .py file in this folder and describe each one in two sentences.")
os.write(fd, b"\n"); events.append([now(), "i", "\n"])
start = len(buf)
deadline = time.time() + 150
while time.time() < deadline:
    pump(fd, 0.2)
    tail = buf[start:]
    if re.search(r"\[n\] no > $", tail):
        pump(fd, 1.8); type_text(fd, "a", delay=(0.2, 0.3)); os.write(fd, b"\n"); events.append([now(), "i", "\n"]); start = len(buf); continue
    if re.search(r"\n  \. ", tail):
        break
else:
    raise TimeoutError("no tool line: %r" % buf[-300:])
pump(fd, 0.6)
os.write(fd, b"\x03"); events.append([now(), "i", "^C"])
wait_for(fd, r"\[stopped\]", 60)
for _ in range(100):
    pump(fd, 0.1)
    if buf.endswith("> "): break
prompt(fd, "What is the tax rate now? One short answer.", "6 再问一个问题：聊天没有坏")
mark("7 斜杠命令")
pump(fd, 0.6); type_text(fd, "/context"); os.write(fd, b"\n"); events.append([now(), "i", "\n"]); wait_for(fd, r"> $", 20)
pump(fd, 0.6); type_text(fd, "/exit"); os.write(fd, b"\n"); events.append([now(), "i", "\n"])
wait_for(fd, r"bye", 20)
pump(fd, 0.5)
try: os.waitpid(pid, 0)
except ChildProcessError: pass
# ---- session 2: a new process, resume
mark("8 关掉，再开一个新的进程：接上上一次")
pump(fd, 0.1) if False else None
events.append([now(), "o", "\n$ python3 repl.py --continue\n"])
pid, fd = spawn(["--continue"])
wait_for(fd, r"> $", 40)
prompt(fd, "Which file did you read first in this chat? Answer with the path only.", "9 它记得")
pump(fd, 0.6); type_text(fd, "/exit"); os.write(fd, b"\n"); events.append([now(), "i", "\n"]); wait_for(fd, r"bye", 20)
try: os.waitpid(pid, 0)
except ChildProcessError: pass
json.dump({"cols": 104, "rows": 28, "shop": shop, "events": events, "recorded": time.strftime("%Y-%m-%d %H:%M"), "model": os.environ.get("PROVIDER", "")}, open(OUT, "w"), ensure_ascii=False)
print("recorded %d events, %.1f s" % (len(events), now()))
