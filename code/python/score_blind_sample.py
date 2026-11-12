import csv, sys, os, re, glob, collections, random, statistics as st
base, ann_dir = sys.argv[1], sys.argv[2]            # POMA_New_20261110 folder, folder holding batch_*_annotated.tsv
OUT = os.path.join(base, "blind_sample_v2", "results"); os.makedirs(OUT, exist_ok=True)
CONDS = ["NigE", "Indian", "UK", "US"]
TOL = [5, 10, 20]; B = 1000; random.seed(2028)
MATCH = os.environ.get("MATCH", "overlap")   # overlap: a model vowel overlapping the annotated vowel by >= 50% of the shorter interval; midpoint: the midpoint must fall inside a model vowel
DIPH_AS_VOWEL = os.environ.get("DIPH_AS_VOWEL", "1") == "1"   # model-side diphthong labels count as vowels (a substitution), not as a miss
VOW = re.compile(r"^[aeiouyɑæɐɘəɚɛɜɝɞɨɪɔɵøɤɯʉʊʌʏœɶɒ]")
ARPA = {"AA":"ɑ","AE":"æ","AH":"ʌ","AO":"ɔ","AW":"aw","AY":"aj","EH":"ɛ","ER":"ɜ","EY":"ej","IH":"ɪ","IY":"i","OW":"ow","OY":"ɔj","UH":"ʊ","UW":"u","AX":"ə"}
DIPH = {"aj","aw","ɔj","ej","ow","əw","ɑj","ɑw","aɪ","aʊ","ɔɪ","eɪ","oʊ","əʊ","ou","ei","ai","au","oi","ɔi","eə","ɛə","ɪə","ʊə"}
def nucleus(l): return l[0] if l in DIPH else l
FRONT = {"i","iː","ɪ","ɪː","e","eː","ɛ","ɛː","æ","a","aː"}; CENTRAL = {"ɜ","ɜː","ə","ʌ","ɐ","ɚ","ɝ"}; BACK = {"u","uː","ʊ","o","oː","ɔ","ɔː","ɑ","ɒ"}
def canon(l):
    l = l.strip()
    if re.match(r"^[A-Z]{2}[0-2]?$", l): l = ARPA.get(l.rstrip("012"), l)
    return l
def is_vowel(l): return bool(VOW.match(l)) and (DIPH_AS_VOWEL or l not in DIPH)
def category(l): return "Diphthong" if l in DIPH else "Front" if l in FRONT else "Central" if l in CENTRAL else "Back" if l in BACK else "Other"
def decode(p):
    b = open(p, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")
_cache = {}
def phones(cond, f):
    k = (cond, f)
    if k not in _cache:
        p = f"{base}/{cond}/{f}.TextGrid"; out = []
        if os.path.exists(p):
            for blk in re.split(r"\n\s*item \[\d+\]:", decode(p))[1:]:
                n = re.search(r'name = "([^"]*)"', blk)
                if n and re.search("phone", n.group(1), re.I):
                    out = [(float(a), float(b), canon(t)) for a, b, t in re.findall(r'xmin = ([-\d.eE+]+)\s*\n\s*xmax = ([-\d.eE+]+)\s*\n\s*text = "((?:[^"]|"")*)"', blk)]
        _cache[k] = out
    return _cache[k]
def num(x):
    try: return float(x)
    except: return None

ann = []
for f in sorted(glob.glob(f"{ann_dir}/batch_*_annotated.tsv")):
    ann += [r for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t")]
for _r in ann:
    for _k in list(_r):
        if (_r[_k] or "").strip() in ("?", "--undefined--"): _r[_k] = ""
ann = list({r["id"]: r for r in ann}.values())   # the latest annotation of an id wins (batch_9 re-annotations replace earlier rows)
key = {r["id"]: r for r in csv.DictReader(open(f"{base}/blind_sample_v2/blind_sample_KEY_do_not_open.csv", encoding="utf-8"))}
toks = []
for r in ann:
    lab = (r.get("label") or "").strip(); on, off = num(r.get("onset_s")), num(r.get("offset_s"))
    if not lab or lab == "UNSURE" or on is None or off is None: continue
    toks.append(dict(id=r["id"], file=r["file"], word=r["word"], lab=canon(lab), on=on, off=off, nurse=int(key.get(r["id"], {}).get("nurse_token", 0))))
print(f"Detection rule: {MATCH}")
print(f"Annotated tokens used: {len(toks)} from {len({t['file'] for t in toks})} recordings (UNSURE and blank rows excluded)")

rows = []
for t in toks:
    mid = (t["on"] + t["off"]) / 2
    for c in CONDS:
        ph = phones(c, t["file"]); hit = next((p for p in ph if p[0] <= mid < p[1]), None)
        det = bool(hit) and is_vowel(hit[2]) and hit[1] - hit[0] > 0
        if MATCH == "overlap":
            cand = [(max(0.0, min(t["off"], p[1]) - max(t["on"], p[0])), p) for p in ph if is_vowel(p[2]) and p[1] > p[0]]
            ov, best = max(cand, key=lambda x: x[0], default=(0.0, None))
            if best is not None and ov >= 0.5 * min(t["off"] - t["on"], best[1] - best[0]):
                hit, det = best, True
            else:
                det = False
        m = hit[2] if det else None
        rows.append(dict(id=t["id"], file=t["file"], word=t["word"], nurse=t["nurse"], cond=c, ann=t["lab"], model=m or ("(none)" if not hit else "(" + (hit[2] or "silence") + ")"),
            detected=int(det), strict=int(det and m == t["lab"]), nolen=int(det and m.rstrip("ː") == t["lab"].rstrip("ː")),
            cat=int(det and category(m) == category(t["lab"])), mono2diph=int(det and m in DIPH and t["lab"] not in DIPH),
            on_err=(hit[0] - t["on"]) * 1000 if det else None, off_err=(hit[1] - t["off"]) * 1000 if det else None))
with open(f"{OUT}/token_level_scores.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def ci(sub, fn):
    files = sorted({r["file"] for r in sub}); by = collections.defaultdict(list)
    for r in sub: by[r["file"]].append(r)
    est = fn(sub); bs = []
    for _ in range(B):
        s = [r for f in random.choices(files, k=len(files)) for r in by[f]]
        bs.append(fn(s))
    bs.sort(); return est, bs[int(0.025 * B)], bs[int(0.975 * B)]
def pct(sub, key): return 100 * sum(r[key] for r in sub) / len(sub) if sub else float("nan")
def within(sub, t): d = [r for r in sub if r["detected"]]; return 100 * sum(abs(r["on_err"]) <= t and abs(r["off_err"]) <= t for r in d) / len(d) if d else float("nan")
summ = []
print(f"\n{'condition':8s} {'n':>4s} {'detected%':>10s} {'strict%':>8s} {'no-length%':>11s} {'category%':>10s} {'mono->diph%':>12s}  within +/-5/10/20 ms (both edges, detected tokens)")
for c in CONDS:
    sub = [r for r in rows if r["cond"] == c]
    d = ci(sub, lambda s: pct(s, "detected")); sx = ci(sub, lambda s: pct(s, "strict")); ct = ci(sub, lambda s: pct(s, "cat"))
    wi = [within(sub, t) for t in TOL]; det = [r for r in sub if r["detected"]]
    med_on = st.median(r["on_err"] for r in det) if det else float("nan"); med_off = st.median(r["off_err"] for r in det) if det else float("nan")
    print(f"{c:8s} {len(sub):4d} {d[0]:6.1f} [{d[1]:.0f}-{d[2]:.0f}] {sx[0]:5.1f} {pct(sub,'nolen'):9.1f} {ct[0]:10.1f} {pct(sub,'mono2diph'):12.1f}   {wi[0]:.0f}/{wi[1]:.0f}/{wi[2]:.0f}   median onset {med_on:+.0f} ms, offset {med_off:+.0f} ms")
    summ.append(dict(condition=c, n=len(sub), detected_pct=d[0], detected_lo=d[1], detected_hi=d[2], strict_pct=sx[0], strict_lo=sx[1], strict_hi=sx[2],
        nolength_pct=pct(sub, "nolen"), category_pct=ct[0], category_lo=ct[1], category_hi=ct[2], mono_to_diph_pct=pct(sub, "mono2diph"),
        within5=wi[0], within10=wi[1], within20=wi[2], median_onset_err_ms=med_on, median_offset_err_ms=med_off))
with open(f"{OUT}/summary_by_condition.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(summ[0].keys())); w.writeheader(); w.writerows(summ)

for c in CONDS:
    cm = collections.Counter((r["ann"], r["model"]) for r in rows if r["cond"] == c)
    labs = sorted({a for a, _ in cm}); cols = sorted({m for _, m in cm})
    with open(f"{OUT}/confusion_{c}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["annotated \\ model"] + cols)
        for a in labs: w.writerow([a] + [cm[(a, m)] for m in cols])
print("\nBy annotated vowel (detected%, category%) per condition:")
byv = collections.defaultdict(dict)
for r in rows: byv[r["ann"]].setdefault(r["cond"], []).append(r)
for a in sorted(byv):
    print(f"  {a:3s} n={len(byv[a]['NigE']):3d} " + "  ".join(f"{c}: {pct(byv[a][c],'detected'):3.0f}/{pct(byv[a][c],'cat'):3.0f}" for c in CONDS))
print("\nNURSE tokens: what each condition returns")
for c in CONDS:
    sub = [r for r in rows if r["cond"] == c and r["nurse"] == 1]
    if sub: print(f"  {c:7s} n={len(sub):3d} annotated as {dict(collections.Counter(r['ann'] for r in sub).most_common(4))}; model gives {dict(collections.Counter(r['model'] for r in sub).most_common(5))}")

print("\nVowel quality ignoring glides (first element of a diphthong only), share of tokens where the model has a vowel of the same category:")
for c in CONDS:
    sub = [r for r in rows if r["cond"] == c]
    n = sum(1 for r in sub if r["detected"] and category(nucleus(r["model"])) == category(nucleus(r["ann"])))
    print(f"  {c:7s} {100*n/len(sub):5.1f}%")
print("\nGlides you heard in tokens that the NigE alignment labels as a monophthong (by NigE label):")
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
print("\nFiles written to", OUT)
