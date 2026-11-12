#!/usr/bin/env python3
"""Before aligning: how many words of the extension transcripts are missing from each MFA dictionary?
Usage: python3 oov_precheck.py "$B"   (reads $B/extension_transcripts/*.txt and the four dictionaries in ~/Documents/MFA/pretrained_models/dictionary)
An estimate of MFA's own handling: lower-case, punctuation stripped at the edges, a hyphenated word counts as known if all its parts are."""
import sys, os, re, glob, collections
B = sys.argv[1]; PM = os.path.expanduser(os.environ.get("PM", "~/Documents/MFA/pretrained_models")) + "/dictionary"
D = {"NigE": "english_nigeria_mfa.dict", "Indian": "english_india_mfa.dict", "UK": "english_uk_mfa.dict", "US": "english_us_mfa.dict"}
def load(p):
    s = set()
    for line in open(p, encoding="utf-8"):
        w = re.split(r"[\t ]", line.rstrip("\n"), 1)[0].strip().lower()
        if w: s.add(w)
    return s
dic = {k: load(f"{PM}/{v}") for k, v in D.items()}
files = sorted(glob.glob(f"{B}/extension_transcripts/*.txt"))
toks = {}; frag = collections.Counter()
for f in files:
    t = open(f, encoding="utf-8-sig").read().lower(); stem = os.path.basename(f)[:-4]; L = []
    for tok in t.split():
        core = re.sub(r"^[^\w']+|[^\w']+$", "", tok)
        if not core: continue
        if tok.startswith("-") or tok.endswith("-"): frag[stem] += 1
        L.append(core)
    toks[stem] = L
def known(w, d): return w in d or ("-" in w and all(p in d for p in w.split("-") if p))
print(f"{len(files)} transcripts, {sum(len(v) for v in toks.values()):,} word tokens, {sum(frag.values())} word fragments written with a hyphen (e.g. 'gov-')\n")
print(f"{'dictionary':10s}{'dictionary words':>18s}{'OOV tokens':>12s}{'OOV %':>8s}{'OOV types':>11s}")
res = {}
for k, d in dic.items():
    oov = collections.Counter(w for L in toks.values() for w in L if not known(w, d)); n = sum(len(v) for v in toks.values())
    res[k] = oov; print(f"{k:10s}{len(d):18,d}{sum(oov.values()):12,d}{100*sum(oov.values())/n:8.1f}{len(oov):11,d}")
print("\nMost frequent words missing from the NigE dictionary:  " + ", ".join(f"{w} ({c})" for w, c in res["NigE"].most_common(30)))
print("\nWorst recordings under the NigE dictionary (OOV % of their words):")
rows = sorted(((sum(1 for w in L if not known(w, dic['NigE'])) / max(len(L), 1), s, len(L)) for s, L in toks.items()), reverse=True)[:6]
for r, s, n in rows: print(f"  {s:10s}{100*r:6.1f}%  of {n} words;  fragments with a hyphen: {frag[s]}")
