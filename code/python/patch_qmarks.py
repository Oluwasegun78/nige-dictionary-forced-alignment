import os
FIX = '''for _r in {rows}:
    for _k in list(_r):
        if (_r[_k] or "").strip() in ("?", "--undefined--"): _r[_k] = ""
'''
# 1. check_annotations.py
p = os.path.expanduser("~/check_annotations.py"); s = open(p, encoding="utf-8").read()
if '"?", "--undefined--"' not in s:
    marker = 'rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\\t"))\n'
    assert marker in s; s = s.replace(marker, marker + FIX.format(rows="rows"), 1); open(p, "w", encoding="utf-8").write(s); print("check_annotations.py patched")
else: print("check_annotations.py already patched")
# 2. count_per_label.py (ann is a dict id -> row)
p = os.path.expanduser("~/count_per_label.py"); s = open(p, encoding="utf-8").read()
if '"?", "--undefined--"' not in s:
    marker = 'def ok(r):'
    assert marker in s; s = s.replace(marker, FIX.format(rows="ann.values()") + marker, 1)
    s = s.replace('return l and l != "UNSURE" and r.get("onset_s") not in ("", None, "--undefined--")', 'return l and l != "UNSURE" and r.get("onset_s") not in ("", None)')
    open(p, "w", encoding="utf-8").write(s); print("count_per_label.py patched")
else: print("count_per_label.py already patched")
# 3. scoring script: same cleaning for safety
p = os.path.expanduser("~/score_blind_sample.py"); s = open(p, encoding="utf-8").read()
if '"?", "--undefined--"' not in s:
    marker = 'ann = list({r["id"]: r for r in ann}.values())'
    if marker in s:
        s = s.replace(marker, FIX.format(rows="ann") + marker, 1); open(p, "w", encoding="utf-8").write(s); print("score_blind_sample.py patched")
    else: print("score_blind_sample.py: run patch_score.py first")
else: print("score_blind_sample.py already patched")
