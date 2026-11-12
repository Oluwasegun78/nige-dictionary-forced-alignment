import re, sys, os, glob, csv, random, collections
base = sys.argv[1]
random.seed(2027)
PER_LABEL, PER_FILE, PER_WORD, NURSE_MAX, NURSE_PER_WORD = 30, 3, 3, 40, 4
VARIETIES = ["NigE", "Indian", "UK", "US"]
DIPH = {"aj","aw","ɔj","ej","ow","əw","ɑj","ɑw","aɪ","aʊ","ɔɪ","eɪ","oʊ","əʊ"}
VOW = re.compile(r"^[aeiouyɑæɐɘəɚɛɜɝɞɨɪɔɵøɤɯʉʊʌʏœɶɒ]")
NURSE = {"world":1,"word":1,"work":1,"verses":1,"verse":1,"earth":1,"first":1,"church":1,"turn":1,"burned":1,"burns":1,
         "earned":1,"certain":1,"mercury":1,"purpose":1,"person":1,"personal":1,"personality":1,"perseverance":1,
         "further":1,"jersey":1,"ferguson":1,"ferguson's":1,"determine":2,"proverbs":2,"refer":2,"return":2,
         "returned":2,"returns":2,"eternal":2,"eternity":2}
LAB = {"p","b","m","f","v","w"}; COR = {"t","d","n","s","z","ʃ","ʒ","tʃ","dʒ","θ","ð","l","ɫ","ɹ","r","ɾ"}
DOR = {"k","ɡ","g","ŋ","j","c","ɟ"}; GLO = {"h","ʔ"}
VLS = {"p","t","k","tʃ","f","θ","s","ʃ","h","ʔ","c"}; VCD = {"b","d","ɡ","g","dʒ","v","ð","z","ʒ","ɟ"}
NAS = {"m","n","ŋ"}; LIQ = {"l","ɫ","ɹ","r","ɾ","j","w"}
OTHER = collections.Counter()
def b_(l): return l.rstrip("ʰʲʷː˞")
def prec(l):
    l = b_(l)
    if l == "": return "pause"
    if VOW.match(l): return "vowel"
    c = "labial" if l in LAB else "coronal" if l in COR else "dorsal" if l in DOR else "glottal" if l in GLO else "other"
    if c == "other": OTHER[("preceding", l)] += 1
    return c
def foll(l):
    l = b_(l)
    if l == "": return "pause"
    if VOW.match(l): return "vowel"
    c = "voiceless" if l in VLS else "voiced" if l in VCD else "nasal" if l in NAS else "liquid/glide" if l in LIQ else "other"
    if c == "other": OTHER[("following", l)] += 1
    return c

def decode(p):
    b = open(p, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): return b.decode("utf-16")
    if b[:3] == b"\xef\xbb\xbf": b = b[3:]
    return b.decode("utf-8")
def tiers(path):
    out = {}
    for blk in re.split(r"\n\s*item \[\d+\]:", decode(path))[1:]:
        c = re.search(r'class = "(\w+)"', blk); n = re.search(r'name = "([^"]*)"', blk)
        if not c or c.group(1) != "IntervalTier" or not n: continue
        out[n.group(1)] = [(float(a), float(b), t.replace('""', '"').strip()) for a, b, t in
                           re.findall(r'xmin = ([-\d.eE+]+)\s*\n\s*xmax = ([-\d.eE+]+)\s*\n\s*text = "((?:[^"]|"")*)"', blk)]
    return out
def tier_like(t, pat):
    for k, v in t.items():
        if re.search(pat, k, re.I): return v
    return None

sets = [{os.path.basename(f)[:-9] for f in glob.glob(f"{base}/{v}/*.TextGrid")} for v in VARIETIES]
common = sorted(set.intersection(*sets))
print("Recordings aligned by all four conditions:", len(common))
tokens = []
for s in common:
    t = tiers(f"{base}/NigE/{s}.TextGrid"); ph, wd = tier_like(t, "phone"), tier_like(t, "word")
    if not ph or not wd: print("no phone/word tier:", s); continue
    vs = [(i, a, b, l) for i, (a, b, l) in enumerate(ph) if l and VOW.match(l) and l not in DIPH and b - a > 0.02]
    for a, b, w in wd:
        if not w: continue
        inside = [v for v in vs if a - 1e-6 <= (v[1] + v[2]) / 2 <= b + 1e-6]
        for k, (i, st, en, lab) in enumerate(inside, 1):
            p = ph[i-1][2] if i > 0 else ""; f = ph[i+1][2] if i + 1 < len(ph) else ""
            tokens.append(dict(file=s, word=w, wl=w.lower(), k=k, start=st, end=en, label=lab, pc=prec(p), fc=foll(f)))
print("Monophthong vowel tokens in NigE alignment:", len(tokens))

groups = collections.defaultdict(list)
for t in tokens: groups[t["label"]].append(t)
picked = []
for lab, toks in sorted(groups.items()):
    cells = collections.defaultdict(list)
    for t in toks: cells[(t["pc"], t["fc"])].append(t)
    for c in cells.values(): random.shuffle(c)
    pf, pw, n = collections.Counter(), collections.Counter(), 0
    progress = True
    while n < PER_LABEL and progress:
        progress = False
        order = list(cells); random.shuffle(order)
        for c in order:
            if n >= PER_LABEL: break
            while cells[c]:
                t = cells[c].pop()
                if pf[t["file"]] >= PER_FILE or pw[t["wl"]] >= PER_WORD: continue
                t["nurse"] = 0; picked.append(t); pf[t["file"]] += 1; pw[t["wl"]] += 1; n += 1; progress = True; break
have = {(t["file"], t["start"]) for t in picked}
cand = [t for t in tokens if NURSE.get(t["wl"]) == t["k"] and (t["file"], t["start"]) not in have]
random.shuffle(cand); m = 0; pf, pw = collections.Counter(), collections.Counter()
for t in cand:
    if m >= NURSE_MAX: break
    if pf[t["file"]] >= PER_FILE or pw[t["wl"]] >= NURSE_PER_WORD: continue
    t["nurse"] = 1; picked.append(t); pf[t["file"]] += 1; pw[t["wl"]] += 1; m += 1
random.shuffle(picked)

out = os.path.join(base, "blind_sample_v2"); os.makedirs(out, exist_ok=True)
with open(f"{out}/blind_sample_for_annotation.csv", "w", newline="", encoding="utf-8") as f1, \
     open(f"{out}/blind_sample_KEY_do_not_open.csv", "w", newline="", encoding="utf-8") as f2:
    w1, w2 = csv.writer(f1), csv.writer(f2)
    w1.writerow(["id", "file", "word", "vowel_in_word", "window_start", "window_end", "onset_s", "offset_s", "label", "notes"])
    w2.writerow(["id", "file", "word", "vowel_in_word", "nige_label", "nige_start", "nige_end", "nurse_token", "preceding", "following"])
    for i, t in enumerate(picked, 1):
        ws = max(0.0, round(t["start"] - random.uniform(0.3, 0.6), 2)); we = round(t["end"] + random.uniform(0.3, 0.6), 2)
        w1.writerow([f"{i:04d}", t["file"], t["word"], t["k"], ws, we, "", "", "", ""])
        w2.writerow([f"{i:04d}", t["file"], t["word"], t["k"], t["label"], round(t["start"], 4), round(t["end"], 4), t["nurse"], t["pc"], t["fc"]])
print("Tokens in the sample:", len(picked), "| NURSE tokens:", sum(t["nurse"] for t in picked))
print("\nContext coverage per vowel (preceding / following classes with their counts):")
by = collections.defaultdict(list)
for t in picked:
    if not t["nurse"]: by[t["label"]].append(t)
for lab, v in sorted(by.items()):
    pa = collections.Counter(t["pc"] for t in v); fb = collections.Counter(t["fc"] for t in v)
    print(f"  {lab:3s} n={len(v)}  preceding: {dict(pa.most_common())}\n          following: {dict(fb.most_common())}")
print("\nSymbols not classified as a consonant class (preceding/following, whole alignment):", OTHER.most_common(12))
print("Written to", out)
