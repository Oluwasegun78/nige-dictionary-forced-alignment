import csv, sys, os, re, glob, bisect, collections, statistics as st, math
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
base = sys.argv[1]
OUT = os.path.join(base, "blind_sample_v2", "results_formants"); os.makedirs(OUT, exist_ok=True)
C = ["NigE", "Indian", "UK", "US"]; MIN_SPAN = float(os.environ.get("MIN_SPAN", "0.02")); MIN_N = int(os.environ.get("MIN_N", "40"))
ARPA = {"AA":"ɑ","AE":"æ","AH":"ʌ","AO":"ɔ","AW":"aw","AY":"aj","EH":"ɛ","ER":"ɜ","EY":"ej","IH":"ɪ","IY":"i","OW":"ow","OY":"ɔj","UH":"ʊ","UW":"u","AX":"ə"}
DIPH = {"aj","aw","ɔj","ej","ow","əw","ɑj","ɑw","aɪ","aʊ","ɔɪ","eɪ","oʊ","əʊ","ou","ei","ai","au"}
def canon(l):
    l = l.strip(); return ARPA.get(l.rstrip("012"), l) if re.match(r"^[A-Z]{2}[0-2]?$", l) else l
def num(x):
    try:
        v = float(x); return v if math.isfinite(v) else None
    except: return None
def interp(xs, ys, x0):
    if x0 <= xs[0]: return ys[0]
    if x0 >= xs[-1]: return ys[-1]
    i = bisect.bisect_left(xs, x0); x1, x2, y1, y2 = xs[i-1], xs[i], ys[i-1], ys[i]
    return y1 if x2 == x1 else y1 + (y2 - y1) * (x0 - x1) / (x2 - x1)
sets = [{os.path.basename(f)[:-9] for f in glob.glob(f"{base}/{c}/*.TextGrid")} for c in C]
shared = sorted(set.intersection(*sets)); print("Shared recordings:", len(shared))
DATA = {}      # dictionary -> list of (recording, label, F1mid, F2mid)
for c in C:
    files = {}
    for f in glob.glob(f"{base}/fave_runs/{c}/*tracks.csv"):
        nm = os.path.basename(f); files[nm[:-len("_tracks.csv")] if nm.endswith("_tracks.csv") else nm.rsplit("tracks.csv", 1)[0].rstrip("_")] = f
    rows = []
    for rec in shared:
        if rec not in files: continue
        by = collections.OrderedDict(); allrows = list(csv.DictReader(open(files[rec], encoding="utf-8")))
        for r in allrows: by.setdefault(r.get("id"), []).append(r)
        if len(by) <= 2 and len(allrows) > 300:
            by = collections.OrderedDict(); k = 0; prev = None
            for r in sorted(allrows, key=lambda r: num(r.get("time")) or 0):
                tm = num(r.get("time"))
                if prev is None or r.get("label") != prev[0] or tm is None or tm - prev[1] > 0.01: k += 1
                by.setdefault(f"tok{k}", []).append(r); prev = (r.get("label"), tm)
        for tid, rr in by.items():
            pts = []
            for r in rr:
                t = num(r.get("time")); a = num(r.get("F1_s")); b = num(r.get("F2_s"))
                a = a if a is not None else num(r.get("F1")); b = b if b is not None else num(r.get("F2"))
                if t is not None and a is not None and b is not None: pts.append((t, a, b))
            pts.sort()
            if len(pts) < 5 or pts[-1][0] - pts[0][0] < MIN_SPAN: continue
            s, e = pts[0][0], pts[-1][0]; pr = [(p[0] - s) / (e - s) for p in pts]
            rows.append((rec, canon(rr[0].get("label", "")), interp(pr, [p[1] for p in pts], .5), interp(pr, [p[2] for p in pts], .5)))
    # Lobanov by recording
    byrec = collections.defaultdict(list)
    for r in rows: byrec[r[0]].append(r)
    z = []; used = 0
    for rec, v in byrec.items():
        if len(v) < 30: continue
        a = [x[2] for x in v]; b = [x[3] for x in v]; ma, sa, mb, sb = st.mean(a), st.pstdev(a) or 1, st.mean(b), st.pstdev(b) or 1
        z += [(x[1], (x[2] - ma) / sa, (x[3] - mb) / sb) for x in v]; used += 1
    DATA[c] = z; print(f"{c:7s} tokens {len(z)} from {used} recordings (recordings with < 30 tracked vowels left out)")
allz = [x for c in C for x in DATA[c]]
lim1 = (np.percentile([x[1] for x in allz], .5) - .1, np.percentile([x[1] for x in allz], 99.5) + .1)
lim2 = (np.percentile([x[2] for x in allz], .5) - .1, np.percentile([x[2] for x in allz], 99.5) + .1)
def stats(z):
    g = collections.defaultdict(list)
    for l, a, b in z: g[l].append((a, b))
    out = {}
    for l, v in g.items():
        if len(v) < MIN_N: continue
        arr = np.array(v); out[l] = (len(v), arr.mean(0), np.cov(arr.T))
    return out
ST = {c: stats(DATA[c]) for c in C}
with open(f"{OUT}/vowel_space_centroids.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["dictionary", "label", "n", "F1z_mean", "F2z_mean", "F1z_sd", "F2z_sd"])
    for c in C:
        for l, (n, m, cv) in sorted(ST[c].items(), key=lambda kv: -kv[1][0]): w.writerow([c, l, n, round(m[0], 3), round(m[1], 3), round(math.sqrt(cv[0, 0]), 3), round(math.sqrt(cv[1, 1]), 3)])
def ell(ax, m, cv, color, ls="-", lw=1.4, alpha=1.0):
    ev, evec = np.linalg.eigh(cv[::-1, ::-1])     # coordinates: x = F2z, y = F1z
    ang = math.degrees(math.atan2(evec[1, 1], evec[0, 1])); ax.add_patch(Ellipse((m[1], m[0]), 2*math.sqrt(max(ev[1], 1e-9)), 2*math.sqrt(max(ev[0], 1e-9)), angle=ang, fill=False, ec=color, ls=ls, lw=lw, alpha=alpha))
def draw(overlay, fname):
    fig, axs = plt.subplots(2, 2, figsize=(11, 9)); axs = list(axs.flat)
    for ax, c in zip(axs, C):
        z = DATA[c]; idx = np.random.RandomState(1).permutation(len(z))[:2500]
        ax.scatter([z[i][2] for i in idx], [z[i][1] for i in idx], s=4, c="#BBBBBB", alpha=.25, linewidths=0)
        if overlay and c != "NigE":
            for l, (n, m, cv) in ST["NigE"].items():
                ell(ax, m, cv, "#888888", ls="--", lw=.9); ax.text(m[1], m[0], l, ha="center", va="center", fontsize=8, color="#777777")
        for l, (n, m, cv) in ST[c].items():
            col = "#C0392B" if l in DIPH else "#1F5FA8"; ell(ax, m, cv, col); ax.text(m[1], m[0], l, ha="center", va="center", fontsize=12, fontweight="bold", color=col)
        ax.set_xlim(lim2[1], lim2[0]); ax.set_ylim(lim1[1], lim1[0]); ax.set_title(f"{c} dictionary (n = {len(z):,})", fontsize=12, fontweight="bold")
        ax.set_xlabel("normalised F2"); ax.set_ylabel("normalised F1")
    plt.tight_layout(); plt.savefig(f"{OUT}/{fname}", dpi=170); plt.close(); print("Figure written:", f"{OUT}/{fname}")
draw(False, "vowel_space_by_dictionary.png"); draw(True, "vowel_space_by_dictionary_NigE_overlay.png")
print(f"Ellipses: 1 standard deviation, labels with at least {MIN_N} tokens. Red = diphthong labels. Grey dashed = NigE categories (overlay version).")
