import os, re
# 1. allowed labels in the annotation check
p = os.path.expanduser("~/check_annotations.py")
if os.path.exists(p):
    s = open(p, encoding="utf-8").read()
    if '"ou"' not in s:
        s = s.replace('"ɜ","ə"}', '"ɜ","ə","ʌ","ou","eə"}', 1)
        open(p, "w", encoding="utf-8").write(s); print("check_annotations.py: allowed labels extended")
    else: print("check_annotations.py: already extended")
# 2. scoring script: glides typed by the annotator, vowel quality ignoring glides, glides heard in NigE monophthong tokens
p = os.path.expanduser(os.environ.get("TARGET", "~/score_blind_sample.py"))
s = open(p, encoding="utf-8").read()
if "def nucleus" in s: print("score_blind_sample.py: already patched"); raise SystemExit
old = 'DIPH = {"aj","aw","ɔj","ej","ow","əw","ɑj","ɑw","aɪ","aʊ","ɔɪ","eɪ","oʊ","əʊ"}'
new = 'DIPH = {"aj","aw","ɔj","ej","ow","əw","ɑj","ɑw","aɪ","aʊ","ɔɪ","eɪ","oʊ","əʊ","ou","ei","ai","au","oi","ɔi","eə","ɛə","ɪə","ʊə"}\ndef nucleus(l): return l[0] if l in DIPH else l'
assert old in s; s = s.replace(old, new, 1)
extra = '''
print("\\nVowel quality ignoring glides (first element of a diphthong only), share of tokens where the model has a vowel of the same category:")
for c in CONDS:
    sub = [r for r in rows if r["cond"] == c]
    n = sum(1 for r in sub if r["detected"] and category(nucleus(r["model"])) == category(nucleus(r["ann"])))
    print(f"  {c:7s} {100*n/len(sub):5.1f}%")
print("\\nGlides you heard in tokens that the NigE alignment labels as a monophthong (by NigE label):")
by = collections.defaultdict(list)
for t in toks:
    k = key.get(t["id"], {}).get("nige_label")
    if k and k not in DIPH: by[k].append(t["lab"])
glide_rows = []
for k, v in sorted(by.items()):
    g = [x for x in v if x in DIPH]
    print(f"  NigE {k:3s} n={len(v):3d}  heard as a glide: {len(g):3d} ({100*len(g)/len(v):4.1f}%)  {dict(collections.Counter(g).most_common(3))}")
    glide_rows.append([k, len(v), len(g), dict(collections.Counter(g))])
with open(f"{OUT}/glides_heard_by_nige_label.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["nige_label", "n_tokens", "n_heard_as_glide", "glide_labels"]); w.writerows(glide_rows)
'''
marker = 'print("\\nFiles written to", OUT)'
assert marker in s; s = s.replace(marker, extra + marker, 1)
open(p, "w", encoding="utf-8").write(s); print("score_blind_sample.py: patched")
