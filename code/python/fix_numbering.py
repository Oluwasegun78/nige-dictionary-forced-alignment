import csv, sys, os, re, glob, shutil
base = sys.argv[1]; folder = sys.argv[2] if len(sys.argv) > 2 else "blind_sample_v2"
d = f"{base}/{folder}"
VOW = re.compile(r"^[aeiouyɑæɐɘəɚɛɜɝɞɨɪɔɵøɤɯʉʊʌʏœɶɒ]")
def decode(p):
    b = open(p, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")
_c = {}
def grid(f):
    if f not in _c:
        out = {}
        for blk in re.split(r"\n\s*item \[\d+\]:", decode(f"{base}/NigE/{f}.TextGrid"))[1:]:
            n = re.search(r'name = "([^"]*)"', blk)
            if not n: continue
            iv = [(float(a), float(b), t.strip()) for a, b, t in re.findall(r'xmin = ([-\d.eE+]+)\s*\n\s*xmax = ([-\d.eE+]+)\s*\n\s*text = "((?:[^"]|"")*)"', blk)]
            if re.search("phone", n.group(1), re.I): out["ph"] = iv
            if re.search("word", n.group(1), re.I): out["wd"] = iv
        _c[f] = out
    return _c[f]
key = list(csv.DictReader(open(f"{d}/blind_sample_KEY_do_not_open.csv", encoding="utf-8")))
chk = {}
for r in key:
    g = grid(r["file"]); s = float(r["nige_start"]); e = float(r["nige_end"]); mid = (s + e) / 2
    w = next((x for x in g["wd"] if x[0] <= mid <= x[1] and x[2]), None)
    if not w: chk[r["id"]] = (r["file"], r["word"], r["vowel_in_word"], "", "", ""); continue
    vs = sorted(p for p in g["ph"] if p[2] and VOW.match(p[2]) and w[0] - 1e-6 <= (p[0] + p[1]) / 2 <= w[1] + 1e-6)
    k = next((i for i, p in enumerate(vs, 1) if abs(p[0] - s) < 1e-3), "")
    chk[r["id"]] = (r["file"], r["word"], r["vowel_in_word"], k, len(vs), int(str(k) != str(r["vowel_in_word"])))
with open(f"{d}/vowel_numbering_check.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["id", "file", "word", "old_number", "new_number", "n_vowels_in_word", "changed"])
    for i, v in chk.items(): w.writerow([i, *v])
print("Rows checked:", len(chk), "| rows whose vowel number changes:", sum(1 for v in chk.values() if v[5] == 1), "| not found:", sum(1 for v in chk.values() if v[3] == ""))
redo = []
for bf in sorted(glob.glob(f"{d}/batch_[0-9].csv")):
    name = os.path.basename(bf)[:-4]; annotated = os.path.exists(f"{d}/{name}_annotated.tsv")
    rows = list(csv.DictReader(open(bf, encoding="utf-8"))); n = 0
    for r in rows:
        c = chk.get(r["id"])
        if not c or c[3] == "": continue
        if int(c[5]) == 1:
            n += 1
            if annotated: redo.append(dict(r, vowel_in_word=str(c[3]), onset_s="", offset_s="", label="", notes=""))
            else: r["vowel_in_word"] = str(c[3])
    if not annotated:
        shutil.copy(bf, bf + ".bak")
        with open(bf, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"{name}: {n} rows with a changed number -> " + ("listed for re-annotation (already annotated)" if annotated else "number corrected in the file (backup .bak)"))
if redo:
    with open(f"{d}/batch_9.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(redo[0].keys())); w.writeheader(); w.writerows(redo)
    print(f"Re-annotation file: {d}/batch_9.csv with {len(redo)} rows")
