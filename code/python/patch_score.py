import os
p = os.path.expanduser(os.environ.get("TARGET", "~/score_blind_sample.py"))
s = open(p, encoding="utf-8").read()
if "MATCH =" in s: print("already patched"); raise SystemExit
a1 = 'DIPH_AS_VOWEL = os.environ.get("DIPH_AS_VOWEL", "1") == "1"'
b1 = 'MATCH = os.environ.get("MATCH", "overlap")   # overlap: a model vowel overlapping the annotated vowel by >= 50% of the shorter interval; midpoint: the midpoint must fall inside a model vowel\n' + a1
a2 = '''        ph = phones(c, t["file"]); hit = next((p for p in ph if p[0] <= mid < p[1]), None)
        det = bool(hit) and is_vowel(hit[2]) and hit[1] - hit[0] > 0
        m = hit[2] if det else None'''
b2 = '''        ph = phones(c, t["file"]); hit = next((p for p in ph if p[0] <= mid < p[1]), None)
        det = bool(hit) and is_vowel(hit[2]) and hit[1] - hit[0] > 0
        if MATCH == "overlap":
            cand = [(max(0.0, min(t["off"], p[1]) - max(t["on"], p[0])), p) for p in ph if is_vowel(p[2]) and p[1] > p[0]]
            ov, best = max(cand, key=lambda x: x[0], default=(0.0, None))
            if best is not None and ov >= 0.5 * min(t["off"] - t["on"], best[1] - best[0]):
                hit, det = best, True
            else:
                det = False
        m = hit[2] if det else None'''
a3 = 'key = {r["id"]: r for r in csv.DictReader('
b3 = 'ann = list({r["id"]: r for r in ann}.values())   # the latest annotation of an id wins (batch_9 re-annotations replace earlier rows)\n' + a3
for a, b in ((a1, b1), (a2, b2), (a3, b3)):
    assert a in s, a[:50]
    s = s.replace(a, b, 1)
s = s.replace('print(f"Annotated tokens used:', 'print(f"Detection rule: {MATCH}")\nprint(f"Annotated tokens used:', 1)
open(p, "w", encoding="utf-8").write(s); print("patched", p)
