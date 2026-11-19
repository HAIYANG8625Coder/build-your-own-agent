"""Scoring for the memory test, all by code. s1(work, memdir) and s2(work, setup)."""
import hashlib, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
HAN = re.compile(r"[一-鿿]")


def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()


def memory_text(memdir):
    out = {}
    if os.path.isdir(memdir):
        for f in sorted(os.listdir(memdir)):
            if f.endswith(".md") and f != "MEMORY.md":
                out[f] = open(os.path.join(memdir, f), encoding="utf-8").read()
    return out


def s1(memdir):
    notes = memory_text(memdir)
    alltext = "\n".join(notes.values())
    got = {"config": "config.py" in alltext, "key": "STAGING_DEPLOY_KEY" in alltext, "url": "staging.shop.example" in alltext,
           "chinese": bool(re.search(r"chinese|中文", alltext, re.I))}
    # a note is "useful" if it holds one of the facts the user stated (the four checked ones, or the SHOP_ environment-variable convention); anything else is something the agent could look up again
    useful = [f for f, t in notes.items() if any(re.search(p, t, re.I) for p in ("config\\.py", "STAGING_DEPLOY_KEY", "staging\\.shop\\.example", "chinese|中文", "SHOP_"))]
    return {"notes": len(notes), "facts_saved": sum(got.values()), "facts": got, "junk_notes": len(notes) - len(useful), "note_files": list(notes)}


def tests_ok(work):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=work, capture_output=True, text=True)
    return r.returncode == 0


def behaves(work):
    code = "import sys; sys.path.insert(0, '.'); import pricing; print(pricing.shipping_fee(150), pricing.shipping_fee(50))"
    r = subprocess.run([sys.executable, "-c", code], cwd=work, capture_output=True, text=True, env={k: v for k, v in os.environ.items() if not k.startswith("SHOP_")})
    return r.stdout.strip() in ("0 8", "0.0 8", "0 8.0", "0.0 8.0")


def s2(work, final):
    py = "".join(open(os.path.join(work, f), encoding="utf-8").read() for f in os.listdir(work) if f.endswith(".py"))
    han = len(HAN.findall(final))
    return {"config_untouched": md5(os.path.join(work, "config.py")) == md5(os.path.join(HERE, "project", "config.py")),
            "env_override": "SHOP_" in py and "environ" in py,
            "chinese": han >= 20,
            "says_old_key": "STAGING_DEPLOY_KEY" in final, "says_old_url": "staging.shop.example" in final,
            "says_new_key": "STG_DEPLOY_TOKEN" in final, "says_new_url": "stg.shop.example" in final,
            "tests_pass": tests_ok(work), "function_works": behaves(work)}
