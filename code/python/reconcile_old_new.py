#!/usr/bin/env python3
"""Reconcile the second version's corpus numbers (138 files, ~6 h, 33,064 tokens, 1,800,207 rows) with the present study set.
Usage: python3 reconcile_old_new.py "$B" [--audio DIR ...] [--txt DIR ...] [--fave DIR ...]
 B = the study folder (needs study_files.txt). Folders that do not exist are skipped and said so."""
import argparse, csv, os, re, subprocess, sys, wave, collections, statistics as st
OD = "/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
ap = argparse.ArgumentParser(); ap.add_argument("B"); ap.add_argument("--audio", nargs="*"); ap.add_argument("--txt", nargs="*"); ap.add_argument("--fave", nargs="*")
a = ap.parse_args(); B = a.B
SUB = f"{OD}/ML_summer_classes/acoustical_POMA_submission"
AUDIO = a.audio or [f"{SUB}/combined_Indian/indian_annotate/corpus", f"{OD}/ML_summer_classes/ACAL57_acoustic_models/reDO_combined_NigE/NigE_reannotated/corpus"]
TXT = a.txt or [f"{OD}/POMA_archive_20261110/acoustical_POMA_submission/combined_Indian", f"{B}/Indian", f"{B}/_not_in_study/Indian"]
FAVE = a.fave or [f"{SUB}/combined_NigE/NigE_fave_results", f"{OD}/ML_summer_classes/ACAL57_acoustic_models/reDO_combined_NigE/NigE_reannotated/NigE_fave_results"]
study = set(open(f"{B}/study_files.txt", encoding="utf-8").read().split())
OUT = f"{B}/reconciliation"; os.makedirs(OUT, exist_ok=True)
print(f"Study set: {len(study)} recordings (study_files.txt)\n")

def walk(d, exts):
    for r, _, fs in os.walk(d):
        for f in fs:
            if not f.startswith("._") and f.lower().endswith(exts): yield os.path.join(r, f)
def duration(p):
    try:
        o = subprocess.run(["afinfo", p], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"estimated duration: ([0-9.]+) sec", o)
        if m: return float(m.group(1))
    except Exception: pass
    try:
        with wave.open(p) as w: return w.getnframes() / w.getframerate()
    except Exception: return float("nan")
stem = lambda p: os.path.splitext(os.path.basename(p))[0]
def H(x): return f"{x/3600:7.3f} h ({x/60:6.1f} min)"

# ---------- A. the audio pools
txt_stems = set()
for d in TXT:
    if os.path.isdir(d): txt_stems |= {stem(p) for p in walk(d, (".txt",))}
print(f"A. AUDIO POOLS   (transcripts found for {len(txt_stems)} recording names in the transcript folders)")
for d in AUDIO:
    if not os.path.isdir(d): print(f"\n  not found, skipped: {d}"); continue
    rows = [(stem(p), duration(p)) for p in walk(d, (".wav", ".mp3"))]
    cls = lambda s: "in the study set" if s in study else ("transcribed, not in the study set" if s in txt_stems else "no transcript found")
    g = collections.defaultdict(list)
    for s, t in rows: g[cls(s)].append((s, t))
    print(f"\n  {d}\n  all audio files: {len(rows):4d}   {H(sum(t for _, t in rows if t == t))}")
    for k in ("in the study set", "transcribed, not in the study set", "no transcript found"):
        v = g.get(k, []); print(f"    {k:36s} {len(v):4d}   {H(sum(t for _, t in v if t == t))}")
    with open(f"{OUT}/audio_pool_{stem(d) or 'folder'}_{abs(hash(d))%10000}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["file", "seconds", "class"]); [w.writerow([s, round(t, 2), cls(s)]) for s, t in sorted(rows)]
    big = sorted([(t, s) for s, t in rows if s not in study and t == t], reverse=True)[:8]
    print("    longest recordings outside the study set:", ", ".join(f"{s} {t/60:.1f} min" for t, s in big))

# ---------- B. the old formant pools
DIPH = {"aj", "aw", "ɔj", "ej", "ow", "əw", "ɑj", "ɑw", "aɪ", "aʊ", "ɔɪ", "eɪ", "oʊ", "əʊ", "ou", "ei", "ai", "au", "oi", "ɔi"}
T_TOK, T_ROW = 33064, 1800207
for d in FAVE:
    print("\n" + "=" * 100)
    if not os.path.isdir(d): print(f"B. FORMANT POOL not found, skipped: {d}"); continue
    files = sorted(walk(d, ("tracks.csv",)))
    print(f"B. FORMANT POOL  {d}\n   tracks files (recursive): {len(files)}")
    ids = {}; byfile = []
    for f in files:
        n = 0; last = 0.0; seen = {}
        with open(f, encoding="utf-8", newline="") as fh:
            rd = csv.reader(fh); h = next(rd); ix = {c: i for i, c in enumerate(h)}
            ii, il, idur, it = ix.get("id"), ix.get("label"), ix.get("dur"), ix.get("time")
            for r in rd:
                n += 1
                k = r[ii]
                if k not in seen: seen[k] = [r[il] if il is not None else "", float(r[idur]) if idur is not None and r[idur] not in ("", "NA") else float("nan"), 0]
                seen[k][2] += 1
                if it is not None and r[it] not in ("", "NA"):
                    try: last = max(last, float(r[it]))
                    except ValueError: pass
        s = re.sub(r"_?tracks\.csv$", "", os.path.basename(f))
        byfile.append(dict(file=f, stem=s, folder=os.path.dirname(f), rows=n, ids=len(seen), last_time=last, mtime=os.path.getmtime(f), vowels=seen))
    cnt = collections.Counter(b["stem"] for b in byfile); dup = {s for s, c in cnt.items() if c > 1}
    print(f"   distinct recording names: {len(cnt)}   names that occur in more than one file (duplicates): {len(dup)}")
    newest = {}
    for b in byfile:
        if b["stem"] not in newest or b["mtime"] > newest[b["stem"]]["mtime"]: newest[b["stem"]] = b
    keep_new = {id(b) for b in newest.values()}
    def tot(sel):
        bs = [b for b in byfile if sel(b)]
        return len(bs), sum(b["rows"] for b in bs), sum(b["ids"] for b in bs), sum(b["last_time"] for b in bs)
    print(f"\n   {'scope':44s}{'files':>6s}{'rows':>11s}{'vowel ids':>11s}   time covered")
    for name, sel in [("all files, duplicates kept", lambda b: True), ("all files, newest copy of each name", lambda b: id(b) in keep_new),
                      ("study recordings only (newest copy)", lambda b: id(b) in keep_new and b["stem"] in study),
                      ("recordings outside the study set (newest)", lambda b: id(b) in keep_new and b["stem"] not in study)]:
        n, r, i, t = tot(sel); print(f"   {name:44s}{n:6d}{r:11,d}{i:11,d}   {H(t)}")
    with open(f"{OUT}/old_formant_pool_{abs(hash(d))%10000}_by_file.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["file", "stem", "in_study", "rows", "vowel_ids", "last_time_s", "duplicate_name"])
        for b in sorted(byfile, key=lambda b: -b["rows"]): w.writerow([b["file"], b["stem"], int(b["stem"] in study), b["rows"], b["ids"], round(b["last_time"], 1), int(b["stem"] in dup)])
    out = sorted([b for b in newest.values() if b["stem"] not in study], key=lambda b: -b["rows"])[:8]
    print("   largest files outside the study set:", ", ".join(f"{b['stem']} ({b['ids']:,} vowels, {b['last_time']/60:.0f} min)" for b in out))
    # which filter reproduces 33,064 tokens and 1,800,207 rows?
    print(f"\n   Search: which scope and filter gives about {T_TOK:,} tokens and {T_ROW:,} rows?  (ratio target {T_ROW/T_TOK:.1f} rows per token)")
    res = []
    for scope, sel in [("all, duplicates kept", lambda b: True), ("all, newest copy", lambda b: id(b) in keep_new), ("study only", lambda b: id(b) in keep_new and b["stem"] in study), ("non-study only", lambda b: id(b) in keep_new and b["stem"] not in study)]:
        bs = [b for b in byfile if sel(b)]
        for nod in (False, True):
            for md in (0, .03, .04, .05, .06, .07, .08, .10):
                tk = rw = 0
                for b in bs:
                    for lab, du, c in b["vowels"].values():
                        if nod and lab in DIPH: continue
                        if md and not (du >= md): continue
                        tk += 1; rw += c
                res.append((abs(tk / T_TOK - 1) + abs(rw / T_ROW - 1), scope, "no diphthongs" if nod else "diphthongs kept", f"dur >= {md*1000:.0f} ms" if md else "no duration filter", tk, rw))
    for e, scope, dp, mdp, tk, rw in sorted(res)[:6]:
        print(f"     {scope:22s} {dp:16s} {mdp:20s} tokens {tk:7,d} rows {rw:10,d}   off by {100*abs(tk/T_TOK-1):5.1f}% / {100*abs(rw/T_ROW-1):5.1f}%")
    best = min(res)
    print("   -> " + ("a filter reproduces both numbers within 1%." if best[0] < .02 else "no simple filter reproduces both numbers: the old Rmd's own filters (rows with a missing z-score, the wide-pivot merge) cannot be recovered from the tracks files alone."))
print(f"\nPer-file tables written to {OUT}")
