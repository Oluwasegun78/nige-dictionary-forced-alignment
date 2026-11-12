import re, sys, os, difflib

def decode(path):
    b = open(path, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")

def words_tier(path):
    t = decode(path)
    blocks = re.split(r"\n\s*item \[\d+\]:", t)
    for blk in blocks:
        m = re.search(r'name = "([^"]*)"', blk)
        if m and re.search(r"word", m.group(1), re.I):
            return [w.lower() for w in re.findall(r'text = "([^"]+)"', blk) if w.strip() and w.lower() not in ("<unk>",)]
    return None

tg_dir = sys.argv[1]; txt_dir = sys.argv[2]
for stem in sys.argv[3:]:
    tg = os.path.join(tg_dir, stem + ".TextGrid"); tx = os.path.join(txt_dir, stem + ".txt")
    if not (os.path.exists(tg) and os.path.exists(tx)): print(stem, "missing file"); continue
    old = words_tier(tg)
    new = re.sub(r"[^\w\s']", " ", decode(tx).lower()).split()
    if old is None: print(stem, "no word tier in the old TextGrid"); continue
    r = difflib.SequenceMatcher(None, old, new).ratio()
    print(f"{stem}: old TextGrid words {len(old)}, txt words {len(new)}, similarity {r:.2f}")
    print("   old:", " ".join(old[:14])); print("   txt:", " ".join(new[:14]))
