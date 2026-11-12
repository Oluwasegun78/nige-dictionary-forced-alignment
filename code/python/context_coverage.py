import re, sys, os, csv, collections
base = sys.argv[1]; folder = sys.argv[2] if len(sys.argv) > 2 else "blind_sample_v2"
def decode(p):
    b = open(p, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")
def phones(path):
    for blk in re.split(r"\n\s*item \[\d+\]:", decode(path))[1:]:
        n = re.search(r'name = "([^"]*)"', blk)
        if n and re.search("phone", n.group(1), re.I):
            return [(float(a), float(b), t.strip()) for a, b, t in re.findall(r'xmin = ([-\d.eE+]+)\s*\n\s*xmax = ([-\d.eE+]+)\s*\n\s*text = "((?:[^"]|"")*)"', blk)]
    return []
VOW = re.compile(r"^[aeiouyɑæɐɘəɚɛɜɝɞɨɪɔɵøɤɯʉʊʌʏœɶɒ]")
LAB = {"p","b","m","f","v","w"}; COR = {"t","d","n","s","z","ʃ","ʒ","tʃ","dʒ","θ","ð","l","ɫ","ɹ","r","ɾ","d̪","t̪","ʎ"}; DOR = {"k","ɡ","g","ŋ","j","c","ɟ","ɲ","ç"}; GLO = {"h","ʔ"}
VLS = {"p","t","k","tʃ","f","θ","s","ʃ","h","ʔ","c","t̪","ç"}; VCD = {"b","d","ɡ","g","dʒ","v","ð","z","ʒ","ɟ","d̪"}; NAS = {"m","n","ŋ","ɲ"}; LIQ = {"l","ɫ","ɹ","r","ɾ","j","w","ʎ"}
def base_(l):
    l = l.rstrip("ʰʲʷː˞")
    return "" if l in ("spn", "sil", "sp") else l
def prec(l):
    l = base_(l)
    if l == "": return "pause"
    if VOW.match(l): return "vowel"
    return "labial" if l in LAB else "coronal" if l in COR else "dorsal" if l in DOR else "glottal" if l in GLO else "other"
def foll(l):
    l = base_(l)
    if l == "": return "pause"
    if VOW.match(l): return "vowel"
    return "voiceless obstruent" if l in VLS else "voiced obstruent" if l in VCD else "nasal" if l in NAS else "liquid/glide" if l in LIQ else "other"
key = list(csv.DictReader(open(f"{base}/{folder}/blind_sample_KEY_do_not_open.csv", encoding="utf-8")))
cache = {}; rows = []
for r in key:
    ph = cache.setdefault(r["file"], phones(f"{base}/NigE/{r['file']}.TextGrid"))
    s = float(r["nige_start"]); i = min(range(len(ph)), key=lambda j: abs(ph[j][0] - s))
    p = ph[i-1][2] if i > 0 else ""; f = ph[i+1][2] if i + 1 < len(ph) else ""
    rows.append((r["nige_label"], r["nurse_token"], prec(p), foll(f)))
print("Preceding context x following context, all", len(rows), "tokens")
tab = collections.Counter((a, b) for _, _, a, b in rows)
P = sorted({a for a, _ in tab}); F = sorted({b for _, b in tab})
print(f"{'':10s}" + "".join(f"{x[:13]:>14s}" for x in F))
for a in P: print(f"{a:10s}" + "".join(f"{tab[(a,b)]:14d}" for b in F))
print("\nPer vowel label (non-NURSE): n, distinct preceding classes, distinct following classes")
by = collections.defaultdict(list)
for lab, nu, a, b in rows:
    if nu == "0": by[lab].append((a, b))
for lab, v in sorted(by.items()):
    pa = collections.Counter(a for a, _ in v); fb = collections.Counter(b for _, b in v)
    print(f"  {lab:4s} n={len(v):3d}")
    print("       preceding:", ", ".join(f"{k} {n}" for k, n in pa.most_common()))
    print("       following:", ", ".join(f"{k} {n}" for k, n in fb.most_common()))
