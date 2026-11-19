"""Count a Xiaohongshu post the way the editor does. Usage: python3 tools/check_post.py <post.md>
The file has a '# 标题' section and a '# 正文' section; the topics are the last line of the body."""
import re, sys

def u16(s): return len(s.encode("utf-16-le")) // 2          # the editor counts emoji as 2

def section(text, name):
    m = re.search(r"^#\s*" + name + r"\s*\n(.*?)(?=^#\s|\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""

def measure(path):
    text = open(path, encoding="utf-8").read()
    return u16(section(text, "标题")), u16(section(text, "正文")), section(text, "正文")

if __name__ == "__main__":
    t, b, _ = measure(sys.argv[1])
    print("title %d / 20  %s" % (t, "OK" if t <= 20 else "TOO LONG"))
    print("body+topics %d / 1000  %s" % (b, "OK" if b <= 1000 else "TOO LONG"))
