import csv, sys, os, re, glob, collections, statistics as st
base, ann_dir = sys.argv[1], sys.argv[2]
cond = sys.argv[3] if len(sys.argv) > 3 else "NigE"
VOW = re.compile(r"^[aeiouyɑæɐɘəɚɛɜɝɞɨɪɔɵøɤɯʉʊʌʏœɶɒ]")
def decode(p):
    b = open(p, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")
def phones(f):
    for blk in re.split(r"\n\s*item \[\d+\]:", decode(f"{base}/{cond}/{f}.TextGrid"))[1:]:
        n = re.search(r'name = "([^"]*)"', blk)
        if n and re.search("phone", n.group(1), re.I):
            return [(float(a), float(b), t.strip()) for a, b, t in re.findall(r'xmin = ([-\d.eE+]+)\s*\n\s*xmax = ([-\d.eE+]+)\s*\n\s*text = "((?:[^"]|"")*)"', blk)]
    return []
ann = {}
for f in glob.glob(f"{ann_dir}/batch_*_annotated.tsv"):
    for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t"): ann[r["id"]] = r
res = f"{base}/blind_sample_v2/results/token_level_scores.csv"
misses = [x for x in csv.DictReader(open(res, encoding="utf-8")) if x["cond"] == cond and x["detected"] == "0"]
out = []
for m in misses:
    a = ann[m["id"]]; on, off = float(a["onset_s"]), float(a["offset_s"]); ph = phones(m["file"])
    vs = [p for p in ph if p[2] and VOW.match(p[2])]
    best = None
    for p in vs:
        ov = max(0, min(off, p[1]) - max(on, p[0])); dist = 0 if ov > 0 else min(abs(p[0] - off), abs(p[1] - on))
        key = (-ov, dist)
        if best is None or key < best[0]: best = (key, p, ov)
    p, ov = best[1], best[2]
    cls = "boundary disagreement" if ov / (off - on) >= 0.2 else "nearest vowel overlaps <20%" if best[0][1] <= 0.05 else "no vowel within 50 ms"
    out.append((m["id"], m["file"], m["word"], m["ann"], m["model"], p[2], (p[0] - on) * 1000, (p[1] - off) * 1000, 100 * ov / (off - on), (off - on) * 1000, (p[1] - p[0]) * 1000, cls))
print(f"{cond}: {len(out)} misses")
print("Classification:", dict(collections.Counter(o[-1] for o in out)))
print("Per recording (recordings with 2 or more misses):", [(f, n) for f, n in collections.Counter(o[1] for o in out).most_common() if n >= 2])
print("Median duration you marked / nearest NigE vowel (ms):", round(st.median(o[9] for o in out)), "/", round(st.median(o[10] for o in out)))
print("id    file         word         you  at-midpoint  nearest-vowel  onset-diff  offset-diff  overlap%  class")
for o in out: print(f"{o[0]} {o[1]:12s} {o[2][:12]:12s} {o[3]:3s}  {o[4]:11s}  {o[5]:6s}         {o[6]:+6.0f}      {o[7]:+6.0f}     {o[8]:4.0f}    {o[11]}")
