#!/usr/bin/env python3
"""Which extension recordings aligned under which dictionary, how long they are, and how many of their words each dictionary lacks.
Reads only local folders (no OneDrive):  python3 extension_alignment_summary.py"""
import os, glob, re, wave, csv, collections, statistics as st
H = os.path.expanduser("~"); MW = os.environ.get("MFA_WORK", f"{H}/mfa_work_ext")
PM = os.path.expanduser(os.environ.get("PM", "~/Documents/MFA/pretrained_models")) + "/dictionary"
C = ["NigE", "Indian", "UK", "US"]; D = {"NigE": "english_nigeria_mfa.dict", "Indian": "english_india_mfa.dict", "UK": "english_uk_mfa.dict", "US": "english_us_mfa.dict"}
recs = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(f"{MW}/in/ext_NigE/*.wav"))
if not recs: raise SystemExit(f"No recordings in {MW}/in/ext_NigE")
ok = {c: {r for r in recs if os.path.exists(f"{MW}/out/{c}/{r}.TextGrid")} for c in C}
def seconds(r):
    with wave.open(f"{MW}/in/ext_NigE/{r}.wav") as w: return w.getnframes() / w.getframerate()
def load(p):
    s = set()
    for line in open(p, encoding="utf-8"):
        w = re.split(r"[\t ]", line.rstrip("\n"), maxsplit=1)[0].strip().lower()
        if w: s.add(w)
    return s
dic = {c: load(f"{PM}/{D[c]}") for c in C}
def words(r):
    t = open(f"{MW}/in/ext_NigE/{r}.txt", encoding="utf-8-sig").read().lower(); L = []
    for tok in t.split():
        core = re.sub(r"^[^\w']+|[^\w']+$", "", tok)
        if core: L.append(core)
    return L
known = lambda w, d: w in d or ("-" in w and all(p in d for p in w.split("-") if p))
dur = {r: seconds(r) for r in recs}; W = {r: words(r) for r in recs}
oov = {r: {c: 100 * sum(1 for w in W[r] if not known(w, dic[c])) / max(len(W[r]), 1) for c in C} for r in recs}
print(f"{'recording':11s}{'min':>6s}{'words':>7s}   " + "".join(f"{c:>8s}" for c in C) + "     OOV % (NigE / Indian / UK / US)")
rows = []
for r in sorted(recs, key=lambda r: -dur[r]):
    print(f"{r:11s}{dur[r]/60:6.1f}{len(W[r]):7d}   " + "".join(f"{('aligned' if r in ok[c] else 'FAILED'):>8s}" for c in C) + "     " + " / ".join(f"{oov[r][c]:4.1f}" for c in C))
    rows.append([r, round(dur[r], 1), len(W[r])] + [int(r in ok[c]) for c in C] + [round(oov[r][c], 2) for c in C])
allok = [r for r in recs if all(r in ok[c] for c in C)]; anyfail = [r for r in recs if r not in allok]
print(f"\nAligned under: " + ", ".join(f"{c} {len(ok[c])}/{len(recs)}" for c in C))
print(f"Aligned by all four dictionaries: {len(allok)} recordings, {sum(dur[r] for r in allok)/3600:.2f} h   |   not aligned by at least one: {len(anyfail)}, {sum(dur[r] for r in anyfail)/3600:.2f} h   |   aligned by none: {sum(1 for r in recs if not any(r in ok[c] for c in C))}")
print(f"\n{'dictionary':10s}{'failed':>7s}{'mean min, failed':>18s}{'mean min, aligned':>19s}{'mean OOV %, failed':>20s}{'mean OOV %, aligned':>21s}")
for c in C:
    f = [r for r in recs if r not in ok[c]]; a = [r for r in recs if r in ok[c]]
    m = lambda xs: f"{st.mean(xs):.1f}" if xs else "-"
    print(f"{c:10s}{len(f):7d}{m([dur[r]/60 for r in f]):>18s}{m([dur[r]/60 for r in a]):>19s}{m([oov[r][c] for r in f]):>20s}{m([oov[r][c] for r in a]):>21s}")
print("\nBy recording series (aligned / total):")
ser = collections.defaultdict(list)
for r in recs: ser[r.split("_")[0]].append(r)
for k, v in sorted(ser.items()): print(f"  {k:6s}" + "   ".join(f"{c} {sum(1 for r in v if r in ok[c])}/{len(v)}" for c in C) + f"   ({sum(dur[r] for r in v)/60:.0f} min)")
out = f"{H}/extension_alignment_summary.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["recording", "seconds", "words"] + [f"aligned_{c}" for c in C] + [f"oov_pct_{c}" for c in C]); w.writerows(rows)
print("\nWritten:", out)
