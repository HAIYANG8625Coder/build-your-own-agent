"""Score a repo from make_workrepo.py: did each of the 12 faults get fixed, and did anything else break?

    python3 check_work.py <folder>
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_workrepo as M


def rd(root, p):
    try:
        return open(os.path.join(root, p)).read()
    except OSError:
        return ""


def fm(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return dict(l.split(":", 1) for l in m.group(1).split("\n") if ":" in l) if m else {}


def linked(root, kind, name, target):
    p = os.path.join(root, ".claude", kind, name)
    return os.path.islink(p) and os.path.exists(p) and os.path.realpath(p) == os.path.realpath(os.path.join(root, target))


def score(root):
    readme = rd(root, "README.md")
    market = {p["name"] for p in json.loads(rd(root, ".claude-plugin/marketplace.json") or "{}").get("plugins", [])}
    def manifest(p):
        try:
            return json.loads(rd(root, "plugins/%s/.claude-plugin/plugin.json" % p))
        except ValueError:
            return {}
    # the stray skill may go into any plugin, old or new; a new plugin needs a valid manifest and a marketplace entry
    qn = next((os.path.relpath(os.path.join(root, "plugins", p, "skills", "quick-notes"), root)
               for p in sorted(os.listdir(os.path.join(root, "plugins")))
               if os.path.isfile(os.path.join(root, "plugins", p, "skills", "quick-notes", "SKILL.md"))), "")
    home = qn.split(os.sep)[1] if qn else ""
    home_ok = home in M.PLUGINS or (bool(home) and home in market and manifest(home).get("name") == home
                                    and bool(manifest(home).get("version")) and bool(manifest(home).get("description")))
    f = {
        "F1 link for x-image": linked(root, "skills", "x-image", "plugins/x-assistant/skills/x-image"),
        "F2 link for x-reviewer": linked(root, "agents", "x-reviewer.md", "plugins/x-assistant/agents/x-reviewer.md"),
        "F3 voice-video link works": linked(root, "skills", "voice-video", "plugins/avatar-video/skills/voice-video"),
        "F4 diagrams name matches folder": manifest("diagrams").get("name") == "diagrams",
        "F5 outlook-email has version": bool(manifest("outlook-email").get("version")),
        "F6 avatar-video has description": bool(manifest("avatar-video").get("description")),
        "F7 marketplace lists diagrams": "diagrams" in market,
        "F8 xhs-post has description": bool(fm(rd(root, "plugins/x-assistant/skills/xhs-post/SKILL.md")).get("description", "").strip()),
        "F9 video-scripter has name": bool(fm(rd(root, "plugins/avatar-video/agents/video-scripter.md")).get("name", "").strip()),
        "F10 README row for youtube-post": "youtube-post" in readme,
        "F11 README row for video-reviewer": "video-reviewer" in readme,
        "F12 quick-notes moved into a plugin, linked, in README":
            bool(qn) and home_ok and linked(root, "skills", "quick-notes", qn) and "quick-notes" in readme,
    }
    # collateral damage: things that were right must stay right
    broke = []
    for plugin, parts in M.PLUGINS.items():
        for s in parts["skills"]:
            if not os.path.isfile(os.path.join(root, "plugins", plugin, "skills", s, "SKILL.md")):
                broke.append("skill " + s + " deleted")
        for a in parts["agents"]:
            if not os.path.isfile(os.path.join(root, "plugins", plugin, "agents", a + ".md")):
                broke.append("agent " + a + " deleted")
    try:
        if M.fingerprint(root) != M.fingerprint_ref:
            broke.append("third-party skill edited")
    except OSError:
        broke.append("third-party skill deleted")
    return f, broke


M.fingerprint_ref = None
if __name__ == "__main__":
    import tempfile
    ref = tempfile.mkdtemp(); M.build(ref); M.fingerprint_ref = M.fingerprint(ref)
    f, broke = score(sys.argv[1])
    for k, v in f.items():
        print("PASS" if v else "FAIL", k)
    print("fixed %d/%d, broke: %s" % (sum(f.values()), len(f), broke or "nothing"))
