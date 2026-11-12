import csv, sys, os, re, glob, bisect, collections, statistics as st, math
base = sys.argv[1]; ann_dir = sys.argv[2]
OUT = os.path.join(base, "blind_sample_v2", "results_formants"); os.makedirs(OUT, exist_ok=True)
C = ["NigE", "Indian", "UK", "US"]; MIN_DUR = 0.05; NB = 20
MIN_SPAN = float(os.environ.get("MIN_SPAN", "0.02"))   # tokens are every vowel new-fave tracked; this only drops tracks that are almost empty
VOW = re.compile(r"^[aeiouyɑæɐɘəɚɛɜɝɞɨɪɔɵøɤɯʉʊʌʏœɶɒ]")
ARPA = {"AA":"ɑ","AE":"æ","AH":"ʌ","AO":"ɔ","AW":"aw","AY":"aj","EH":"ɛ","ER":"ɜ","EY":"ej","IH":"ɪ","IY":"i","OW":"ow","OY":"ɔj","UH":"ʊ","UW":"u","AX":"ə"}
def canon(l):
    l = l.strip()
    return ARPA.get(l.rstrip("012"), l) if re.match(r"^[A-Z]{2}[0-2]?$", l) else l
def decode(p):
    b = open(p, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")
def vowels_of(path):
    for blk in re.split(r"\n\s*item \[\d+\]:", decode(path))[1:]:
        n = re.search(r'name = "([^"]*)"', blk)
        if n and re.search("phone", n.group(1), re.I):
            return [(float(a), float(b), canon(t)) for a, b, t in re.findall(r'xmin = ([-\d.eE+]+)\s*\n\s*xmax = ([-\d.eE+]+)\s*\n\s*text = "((?:[^"]|"")*)"', blk) if t.strip() and VOW.match(canon(t))]
    return []
def num(x):
    try:
        v = float(x); return v if math.isfinite(v) else None
    except: return None
def interp(xs, ys, x0):
    if not xs: return None
    if x0 <= xs[0]: return ys[0]
    if x0 >= xs[-1]: return ys[-1]
    i = bisect.bisect_left(xs, x0); x1, x2, y1, y2 = xs[i-1], xs[i], ys[i-1], ys[i]
    return y1 if x2 == x1 else y1 + (y2 - y1) * (x0 - x1) / (x2 - x1)
def ovl(a0, a1, b0, b1): return max(0.0, min(a1, b1) - max(a0, b0))
def match(start, end, cands):                      # best-overlapping interval, needs >= half of the shorter one
    best = None
    for c in cands:
        o = ovl(start, end, c["start"], c["end"])
        if o > 0 and (best is None or o > best[0]): best = (o, c)
    if best and best[0] >= 0.5 * min(end - start, best[1]["end"] - best[1]["start"]): return best[1]
    return None
sets = [{os.path.basename(f)[:-9] for f in glob.glob(f"{base}/{c}/*.TextGrid")} for c in C]
shared = sorted(set.intersection(*sets)); print("Recordings aligned by all four dictionaries:", len(shared))
# ---------- load tracks and intervals
TOK = {c: collections.defaultdict(list) for c in C}; IV = {c: collections.defaultdict(list) for c in C}
diag = []
for c in C:
    files = {}
    for f in glob.glob(f"{base}/fave_runs/{c}/*tracks.csv"):
        nm = os.path.basename(f); stem = nm[:-len("_tracks.csv")] if nm.endswith("_tracks.csv") else nm.rsplit("tracks.csv", 1)[0].rstrip("_")
        files[stem] = f
    for rec in shared:
        for (s, e, l) in vowels_of(f"{base}/{c}/{rec}.TextGrid"): IV[c][rec].append(dict(start=s, end=e, label=l, tracked=False))
        if rec not in files: continue
        by = collections.OrderedDict()
        allrows = list(csv.DictReader(open(files[rec], encoding="utf-8")))
        for r in allrows: by.setdefault(r.get("id"), []).append(r)
        if len(by) <= 2 and len(allrows) > 300:      # id is not one per vowel: split on label change or a gap in time
            by = collections.OrderedDict(); k = 0; prev = None
            for r in sorted(allrows, key=lambda r: num(r.get("time")) or 0):
                tm = num(r.get("time"))
                if prev is None or r.get("label") != prev[0] or tm is None or tm - prev[1] > 0.01: k += 1
                by.setdefault(f"tok{k}", []).append(r); prev = (r.get("label"), tm)
            if rec == shared[0]: print("  note: 'id' was not unique per vowel in", c, "- tokens were split by label and time gaps")
        for tid, rows in by.items():
            t = [num(r.get("time")) for r in rows]
            if any(x is None for x in t): continue
            f1 = [num(r.get("F1_s")) if num(r.get("F1_s")) is not None else num(r.get("F1")) for r in rows]
            f2 = [num(r.get("F2_s")) if num(r.get("F2_s")) is not None else num(r.get("F2")) for r in rows]
            pts = sorted((a, b, d) for a, b, d in zip(t, f1, f2) if b is not None and d is not None)
            if len(pts) < 5: continue
            tt = [p[0] for p in pts]; s, e = tt[0], tt[-1]
            if e <= s: continue
            pr = [(x - s) / (e - s) for x in tt]
            TOK[c][rec].append(dict(id=tid, label=canon(rows[0].get("label", "")), start=s, end=e, dur=e - s, pr=pr, f1=[p[1] for p in pts], f2=[p[2] for p in pts]))
    nt = sum(len(v) for v in TOK[c].values()); mins = [min(x["start"] for x in v) for v in TOK[c].values() if v]
    diag.append((c, len(files), nt, round(st.median(mins), 2) if mins else None))
print("Track files read, tokens, median first time per recording (should be > 0 if time is absolute):"); [print("  ", d) for d in diag]
for c in C:
    if not TOK[c]: print("NO TRACKS for", c, "- check", f"{base}/fave_runs/{c}"); sys.exit(1)
for d in diag:
    if d[3] is not None and d[3] < 0.05:
        print(f"WARNING: for {d[0]} the track times start near 0 in every recording, so 'time' may be relative to each vowel and not to the recording. Send me the first 5 lines of one *_tracks.csv file before using these results."); sys.exit(1)
# ---------- A. availability
rows_A = []
for c in C:
    allv = tracked = 0; bins = collections.defaultdict(lambda: [0, 0])
    for rec in shared:
        for iv in IV[c][rec]:
            iv["tracked"] = match(iv["start"], iv["end"], TOK[c].get(rec, [])) is not None
            d = iv["end"] - iv["start"]; b = "<30 ms" if d < .03 else "30-50 ms" if d < .05 else "50-70 ms" if d < .07 else "70-100 ms" if d < .10 else ">=100 ms"
            bins[b][0] += 1; bins[b][1] += iv["tracked"]; allv += 1; tracked += iv["tracked"]
    ge50 = sum(1 for rec in shared for iv in IV[c][rec] if iv["end"] - iv["start"] >= MIN_DUR)
    rows_A.append(dict(dictionary=c, vowel_intervals=allv, ge50ms=ge50, tracked=tracked, tracked_pct_all=100*tracked/allv, tracked_pct_ge50=100*sum(1 for rec in shared for iv in IV[c][rec] if iv["tracked"] and iv["end"]-iv["start"]>=MIN_DUR)/max(ge50,1), **{f"{b}": f"{v[1]}/{v[0]}" for b, v in bins.items()}))
print(f"\nA. Formant availability (vowel intervals in the {len(shared)} shared recordings)")
print(f"{'dictionary':9s} {'intervals':>9s} {'>=50 ms':>8s} {'tracked':>8s} {'% of all':>9s} {'% of >=50ms':>12s}   tracked/intervals by duration")
for r in rows_A: print(f"{r['dictionary']:9s} {r['vowel_intervals']:9d} {r['ge50ms']:8d} {r['tracked']:8d} {r['tracked_pct_all']:9.1f} {r['tracked_pct_ge50']:12.1f}   " + "  ".join(f"{b} {r[b]}" for b in ["<30 ms","30-50 ms","50-70 ms","70-100 ms",">=100 ms"] if b in r))
with open(f"{OUT}/availability.csv", "w", newline="", encoding="utf-8") as fh:
    keys = sorted({k for r in rows_A for k in r}, key=lambda k: (k not in ("dictionary",), k)); w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows_A)
# ---------- Lobanov per recording and dictionary
def mid(t): return interp(t["pr"], t["f1"], .5), interp(t["pr"], t["f2"], .5)
Z = {}
for c in C:
    for rec in shared:
        toks = [t for t in TOK[c].get(rec, []) if t["dur"] >= MIN_SPAN]
        m = [mid(t) for t in toks]
        if len(m) < 30: Z[(c, rec)] = None; continue
        a = [x[0] for x in m]; b = [x[1] for x in m]
        Z[(c, rec)] = (st.mean(a), st.pstdev(a) or 1, st.mean(b), st.pstdev(b) or 1)
def zmid(c, rec, t):
    p = Z.get((c, rec)); 
    if not p: return None
    f1, f2 = mid(t); return ((f1 - p[0]) / p[1], (f2 - p[2]) / p[3])
skipped = sorted({rec for (c, rec), v in Z.items() if v is None})
print("\nRecordings with fewer than 30 tracked vowels in some dictionary (not normalised):", len(skipped))
# ---------- B. stability of the measurement across dictionaries
print("\nB. Same vowels, different dictionary: midpoint formants compared with the NigE run (Hz)")
rows_B = []
for c in C[1:]:
    d1, d2, n = [], [], 0
    for rec in shared:
        for t in TOK["NigE"].get(rec, []):
            if t["dur"] < MIN_SPAN: continue
            o = match(t["start"], t["end"], [u for u in TOK[c].get(rec, []) if u["dur"] >= MIN_SPAN])
            if o:
                a, b = mid(t), mid(o); d1.append(abs(a[0]-b[0])); d2.append(abs(a[1]-b[1])); n += 1
    q = lambda v, p: sorted(v)[min(len(v)-1, int(p*len(v)))] if v else float("nan")
    rows_B.append(dict(dictionary=c, matched=n, median_abs_F1=st.median(d1) if d1 else None, p90_abs_F1=q(d1,.9), median_abs_F2=st.median(d2) if d2 else None, p90_abs_F2=q(d2,.9)))
    print(f"  {c:7s} matched vowels {n:5d} | |dF1| median {rows_B[-1]['median_abs_F1']:.1f}  90th pct {rows_B[-1]['p90_abs_F1']:.1f} | |dF2| median {rows_B[-1]['median_abs_F2']:.1f}  90th pct {rows_B[-1]['p90_abs_F2']:.1f}")
with open(f"{OUT}/stability_vs_NigE.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_B[0].keys())); w.writeheader(); w.writerows(rows_B)
# ---------- annotated tokens
ann = {}
for f in sorted(glob.glob(f"{ann_dir}/batch_*_annotated.tsv")):
    for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t"):
        for k in list(r):
            if (r[k] or "").strip() in ("?", "--undefined--"): r[k] = ""
        ann[r["id"]] = r
key = {r["id"]: r for r in csv.DictReader(open(f"{base}/blind_sample_v2/blind_sample_KEY_do_not_open.csv", encoding="utf-8"))}
A = []
for i, r in ann.items():
    lab = (r.get("label") or "").strip(); on, off = num(r.get("onset_s")), num(r.get("offset_s"))
    if not lab or lab == "UNSURE" or on is None or off is None or r["file"] not in shared: continue
    tk = {}
    for c in C:
        t = match(on, off, [u for u in TOK[c].get(r["file"], []) if u["dur"] >= MIN_SPAN])
        z = zmid(c, r["file"], t) if t else None
        tk[c] = dict(label=t["label"], z=z, tok=t) if t and z else None
    A.append(dict(id=i, file=r["file"], ann=canon(lab), nurse=int(key.get(i, {}).get("nurse_token", 0) or 0), tk=tk))
print(f"\nAnnotated tokens with a usable mark: {len(A)}")
print("C. Annotated vowels that have formants (tracked, >= 50 ms, recording normalised), by dictionary:")
for c in C: print(f"  {c:7s} {sum(1 for a in A if a['tk'][c])} of {len(A)}")
S = [a for a in A if all(a["tk"][c] for c in C)]
print(f"   tokens with formants under all four dictionaries (used below): {len(S)}")
# ---------- D. how well each labelling sorts the same tokens
def eta(groups):
    allv = [v for g in groups.values() for v in g]; n = len(allv); k = len(groups)
    if n < 5 or k < 2: return None, k
    gm = st.mean(allv); sst = sum((v - gm) ** 2 for v in allv); ssb = sum(len(g) * (st.mean(g) - gm) ** 2 for g in groups.values())
    e = ssb / sst if sst else 0; return 1 - (1 - e) * (n - 1) / max(n - k, 1), k
schemes = {"Listener": lambda a: a["ann"]}
for c in C: schemes[c] = (lambda cc: (lambda a: a["tk"][cc]["label"]))(c)
rows_D = []
print("\nD. Share of the variance in normalised F1 and F2 explained by the vowel labels (adjusted), same tokens")
for name, fn in schemes.items():
    out = {}
    for ax, nm in ((0, "F1"), (1, "F2")):
        g = collections.defaultdict(list)
        for a in S:
            zs = [a["tk"][c]["z"][ax] for c in C] if name == "Listener" else [a["tk"][name]["z"][ax]]
            g[fn(a)].append(st.mean(zs))
        out[nm], k = eta(g)
    rows_D.append(dict(labels=name, categories=k, adj_R2_F1=out["F1"], adj_R2_F2=out["F2"]))
    print(f"  {name:9s} categories {k:2d}   F1 {out['F1']:.2f}   F2 {out['F2']:.2f}")
with open(f"{OUT}/label_variance_explained.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_D[0].keys())); w.writeheader(); w.writerows(rows_D)
# ---------- E. NURSE tokens
NU = [a for a in S if a["nurse"] == 1]
print(f"\nE. NURSE tokens with formants under all dictionaries (n = {len(NU)}): mean normalised F1 / F2 by label")
rows_E = []
for name, fn in schemes.items():
    g = collections.defaultdict(list)
    for a in NU:
        zs = [a["tk"][c]["z"] for c in C] if name == "Listener" else [a["tk"][name]["z"]]
        g[fn(a)].append((st.mean(z[0] for z in zs), st.mean(z[1] for z in zs)))
    txt = "; ".join(f"{l} n={len(v)} ({st.mean(x[0] for x in v):+.2f}, {st.mean(x[1] for x in v):+.2f})" for l, v in sorted(g.items(), key=lambda kv: -len(kv[1])))
    print(f"  {name:9s} {txt}")
    for l, v in g.items(): rows_E.append(dict(labels=name, label=l, n=len(v), F1z=st.mean(x[0] for x in v), F2z=st.mean(x[1] for x in v)))
if NU:
    allz = [(st.mean(a["tk"][c]["z"][0] for c in C), st.mean(a["tk"][c]["z"][1] for c in C)) for a in NU]
    print(f"  spread of all NURSE tokens: SD F1z {st.pstdev([z[0] for z in allz]):.2f}, SD F2z {st.pstdev([z[1] for z in allz]):.2f}")
if rows_E:
    with open(f"{OUT}/nurse_by_label.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_E[0].keys())); w.writeheader(); w.writerows(rows_E)
# ---------- F. trajectories (all tracked vowels of the shared recordings)
print("\nF. Trajectory: path length through the normalised F1-F2 plane over bins 3-18 of 20 (median, labels with >= 20 tokens)")
rows_F = []
cent = [(i + .5) / NB for i in range(NB)]
for c in C:
    g = collections.defaultdict(list)
    for rec in shared:
        p = Z.get((c, rec))
        if not p: continue
        for t in TOK[c].get(rec, []):
            if t["dur"] < MIN_SPAN: continue
            tr = [((interp(t["pr"], t["f1"], x) - p[0]) / p[1], (interp(t["pr"], t["f2"], x) - p[2]) / p[3]) for x in cent][2:18]
            L = sum(math.hypot(tr[i+1][0]-tr[i][0], tr[i+1][1]-tr[i][1]) for i in range(len(tr)-1)); net = math.hypot(tr[-1][0]-tr[0][0], tr[-1][1]-tr[0][1])
            g[t["label"]].append((L, net))
    line = []
    for l, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
        if len(v) < 20: continue
        rows_F.append(dict(dictionary=c, label=l, n=len(v), median_path=st.median(x[0] for x in v), median_net=st.median(x[1] for x in v)))
        line.append(f"{l} {st.median(x[0] for x in v):.2f} (n={len(v)})")
    print(f"  {c:7s} " + "; ".join(line[:14]))
if rows_F:
    with open(f"{OUT}/trajectory_by_label.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_F[0].keys())); w.writeheader(); w.writerows(rows_F)
# ---------- figure
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 3, figsize=(12, 7.4)); axs = list(axs.flat)
    allx = [st.mean(a["tk"][c]["z"][1] for c in C) for a in S]; ally = [st.mean(a["tk"][c]["z"][0] for c in C) for a in S]
    xl = (max(allx) + .2, min(allx) - .2); yl = (max(ally) + .2, min(ally) - .2)
    for ax, (name, fn) in zip(axs, schemes.items()):
        g = collections.defaultdict(list)
        for a in S:
            zs = [a["tk"][c]["z"] for c in C] if name == "Listener" else [a["tk"][name]["z"]]
            g[fn(a)].append((st.mean(z[0] for z in zs), st.mean(z[1] for z in zs)))
        ax.scatter([v[1] for l in g.values() for v in l], [v[0] for l in g.values() for v in l], s=6, c="#CCCCCC")
        for l, v in g.items():
            if len(v) >= 3: ax.text(st.mean(x[1] for x in v), st.mean(x[0] for x in v), l, ha="center", va="center", fontsize=11, fontweight="bold", color="#0072B2")
        ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_title(("Annotator's labels" if name == "Listener" else f"{name} dictionary labels"), fontsize=11)
        ax.set_xlabel("normalised F2"); ax.set_ylabel("normalised F1")
    for ax in axs[len(schemes):]: ax.axis("off")
    plt.tight_layout(); plt.savefig(f"{OUT}/vowel_space_by_labelling.png", dpi=170); print("\nFigure written:", f"{OUT}/vowel_space_by_labelling.png")
except Exception as ex:
    print("\nFigure not made (", ex, "). Install matplotlib in this environment to get it.")
print("Files written to", OUT)
