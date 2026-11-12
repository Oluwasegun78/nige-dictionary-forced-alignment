import csv, sys, os, glob, collections, statistics as st, math
base = sys.argv[1]; C = ["NigE", "Indian", "UK", "US"]; LOW = float(os.environ.get("LOW_DB", "3"))
OUT = os.path.join(base, "alignment_info"); os.makedirs(OUT, exist_ok=True)
sets = [{os.path.basename(f)[:-9] for f in glob.glob(f"{base}/{c}/*.TextGrid")} for c in C]
shared = sorted(set.intersection(*sets)); print("Recordings aligned by all four dictionaries:", len(shared))
def pick(h, cands):
    for c in cands:
        if c in h: return c
def num(x):
    try:
        v = float(x); return v if math.isfinite(v) else None
    except: return None
DATA = {}
for c in C:
    f = f"{OUT}/{c}_alignment_analysis.csv"
    if not os.path.exists(f):
        g = glob.glob(f"{OUT}/*{c}*alignment_analysis*.csv"); f = g[0] if g else None
    if not f: print("NOT FOUND for", c, "in", OUT); sys.exit(1)
    rows = list(csv.DictReader(open(f, encoding="utf-8-sig"))); h = rows[0].keys()
    print(f"{c:7s} {os.path.basename(f)}: {len(rows)} rows; columns: {', '.join(h)}")
    cf = pick(h, ["file", "utterance", "Filename", "file_name"]); cl = pick(h, ["overall_log_likelihood"]); cs = pick(h, ["snr"]); cd = pick(h, ["phone_duration_deviation"])
    if not cf: print("  no file column; send me the column list above"); sys.exit(1)
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        stem = os.path.splitext(os.path.basename(str(r[cf])))[0]
        for k, col in (("ll", cl), ("snr", cs), ("dd", cd)):
            v = num(r.get(col)) if col else None
            if v is not None: per[stem][k].append(v)
    DATA[c] = {s: {k: st.mean(v) for k, v in d.items()} for s, d in per.items()}
def ms(v): return (f"{st.mean(v):.2f} ({st.pstdev(v):.2f})" if len(v) > 1 else (f"{v[0]:.2f}" if v else "n/a"))
print(f"\nMFA alignment output on the {len(shared)} shared recordings (mean (SD) over recordings)")
print(f"{'dictionary':9s} {'files':>6s} {'log-likelihood':>18s} {'SNR (dB)':>16s} {'min SNR':>8s} {f'<= {LOW:g} dB':>8s} {'phone dur. deviation':>22s}")
rows_out = []
for c in C:
    d = {s: DATA[c][s] for s in shared if s in DATA[c]}
    ll = [v["ll"] for v in d.values() if "ll" in v]; sn = [v["snr"] for v in d.values() if "snr" in v]; dd = [v["dd"] for v in d.values() if "dd" in v]
    low = sum(1 for x in sn if x <= LOW)
    print(f"{c:9s} {len(d):6d} {ms(ll):>18s} {ms(sn):>16s} {(f'{min(sn):.2f}' if sn else 'n/a'):>8s} {low:8d} {ms(dd):>22s}")
    rows_out.append(dict(dictionary=c, files=len(d), ll_mean=st.mean(ll) if ll else "", ll_sd=st.pstdev(ll) if len(ll) > 1 else "", snr_mean=st.mean(sn) if sn else "", snr_sd=st.pstdev(sn) if len(sn) > 1 else "", snr_min=min(sn) if sn else "", files_at_or_below=low, dd_mean=st.mean(dd) if dd else "", dd_sd=st.pstdev(dd) if len(dd) > 1 else ""))
with open(f"{OUT}/alignment_output_summary.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys())); w.writeheader(); w.writerows(rows_out)
# SNR agreement between dictionaries and the low-SNR recordings
diffs = []; lowfiles = []
for s in shared:
    v = {c: DATA[c][s]["snr"] for c in C if s in DATA[c] and "snr" in DATA[c][s]}
    if len(v) >= 2: diffs.append(max(v.values()) - min(v.values()))
    if any(x <= LOW for x in v.values()): lowfiles.append((s, v))
if diffs: print(f"\nLargest difference in a recording's SNR between dictionaries: {max(diffs):.2f} dB (median {st.median(diffs):.2f} dB)")
print(f"Recordings with SNR at or below {LOW:g} dB under at least one dictionary: {len(lowfiles)}")
for s, v in lowfiles[:20]: print("  ", s, {c: round(x, 2) for c, x in v.items()})
with open(f"{OUT}/low_snr_recordings.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["file"] + C)
    for s, v in lowfiles: w.writerow([s] + [round(v.get(c, float("nan")), 3) for c in C])
# recordings that some dictionary did not align: which are they and what SNR did the others give
allr = sorted(set().union(*[set(DATA[c]) for c in C]))
miss = [s for s in allr if any(s not in DATA[c] for c in C)]
print(f"\nRecordings with an alignment row in some dictionaries but not in all: {len(miss)}")
for s in miss[:15]: print("  ", s, {c: (round(DATA[c][s]['snr'], 2) if s in DATA[c] and 'snr' in DATA[c][s] else 'none') for c in C})
print("\nFiles written to", OUT)
