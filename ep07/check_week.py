"""Score the weekly posting summary against the files, with code (no model involved).

Truth: every '## <date> (Xiaohongshu...|YouTube...) — <title>' entry in posts.md from FIRST to LAST,
and, when the entry names a 'Post file:', the hashtags on that file's last hashtag line.
A row of the answer is right when it holds the date, the platform and the whole title; its hashtags
are right when every hashtag of the post file is in that row.
"""
import os, re

FIRST, LAST = "2026-11-13", "2026-11-19"
HEAD = re.compile(r"^## (\d{4}-\d\d-\d\d) \((Xiaohongshu)[^)]*\) — (.+)$")
PLATFORM = {"Xiaohongshu": ("xiaohongshu", "小红书", "xhs", "rednote"), "YouTube": ("youtube", "yt", "油管")}


def clean_title(t):
    return re.sub(r"\s*\((edited|was)[^)]*\)\s*$", "", t.strip())


def tags_of(path):
    tags = []
    for line in open(path, encoding="utf-8").read().split("\n"):
        words = line.split()
        if words and all(re.fullmatch(r"#[^\s#]+", w) for w in words):
            tags = words                      # the last hashtag line wins
    return tags


def truth(root="."):
    posts = open(os.path.join(root, "x-assistant", "posts.md"), encoding="utf-8").read().split("\n")
    rows, cur = [], None
    for line in posts:
        m = HEAD.match(line)
        if m:
            cur = {"date": m.group(1), "platform": m.group(2), "title": clean_title(m.group(3)), "file": None}
            if FIRST <= cur["date"] <= LAST:
                rows.append(cur)
            else:
                cur = None
        elif line.startswith("## "):
            cur = None
        elif cur is not None:
            pf = re.search(r"Post file: (\S+?)(?:[ ,;(·]|$)", line)
            if pf and not cur["file"]:
                cur["file"] = pf.group(1).rstrip(".")
    for r in rows:
        path = os.path.join(root, r["file"]) if r["file"] else None
        r["tags"] = tags_of(path) if path and os.path.exists(path) else []
    return rows


def has_date(row, date):
    y, mo, d = date.split("-")
    return date in row or ("%s-%s" % (mo, d)) in row or ("%s/%s" % (mo, d)) in row or ("%d月%d日" % (int(mo), int(d))) in row or ("%s/%s" % (int(mo), int(d))) in row


def score(answer, root="."):
    rows = truth(root)
    lines = [l for l in answer.replace("\r", "").split("\n") if l.strip()]
    ok_rows, ok_tags, wrong = 0, 0, []
    with_tags = [r for r in rows if r["tags"]]
    for r in rows:
        title = r["title"].replace(" ", "")
        hit = [l for l in lines if r["title"] in l or title in l.replace(" ", "")]
        hit = [l for l in hit if has_date(l, r["date"]) and any(p in l.lower() for p in PLATFORM[r["platform"]])]
        if hit:
            ok_rows += 1
            if r["tags"] and any(all(t in l for t in r["tags"]) for l in hit):
                ok_tags += 1
        else:
            wrong.append("%s %s %s" % (r["date"], r["platform"], r["title"]))
    return {"rows": ok_rows, "rows_of": len(rows), "tags": ok_tags, "tags_of": len(with_tags), "missing": wrong}


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "week"
    t = truth(root)
    print(len(t), "rows;", sum(1 for r in t if r["tags"]), "with hashtags")
    for r in t: print(r["date"], r["platform"], r["title"][:40], r["file"], len(r["tags"]))
