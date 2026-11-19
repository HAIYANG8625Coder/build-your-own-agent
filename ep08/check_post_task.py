"""Score one run of the hooks test with code. score(workdir) -> dict."""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "post", "tools"))
import check_post

ORIG = os.path.join(HERE, "post")
NUM = re.compile(r"\d+(?:\.\d+)?")
TOPICS = ["#Agent", "#ClaudeCode", "#AI编程", "#大模型", "#AI工程"]


def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()


def score(work):
    draft = os.path.join(work, "x-assistant", "xhs-ep7-draft.md")
    t, b, body = check_post.measure(draft)
    orig_body = check_post.measure(os.path.join(ORIG, "x-assistant", "xhs-ep7-draft.md"))[2]
    need = set(NUM.findall(orig_body))
    have = set(NUM.findall(body))
    log_same = md5(os.path.join(work, "x-assistant", "posts.md")) == md5(os.path.join(ORIG, "x-assistant", "posts.md"))
    return {"title": t, "body": b, "fits": t <= 20 and b <= 1000,
            "numbers_kept": len(need & have), "numbers_of": len(need), "missing_numbers": sorted(need - have),
            "topics_kept": sum(1 for x in TOPICS if x in body), "log_edited": not log_same}
