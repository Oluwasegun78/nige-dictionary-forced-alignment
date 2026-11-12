import re, sys, os, glob, collections, statistics
dictpath, corpus, outdir = sys.argv[1:4]
words = set()
for line in open(dictpath, encoding="utf-8", errors="ignore"):
    p = line.split()
    if p: words.add(p[0].lower())
aligned = {os.path.basename(f)[:-9] for f in glob.glob(outdir + "/*.TextGrid")}
rate = {"aligned": [], "skipped": []}; oovs = collections.Counter()
for t in sorted(glob.glob(corpus + "/*.txt")):
    stem = os.path.basename(t)[:-4]
    toks = [w.strip("'") for w in re.findall(r"[a-z0-9']+", open(t, encoding="utf-8", errors="ignore").read().lower())]
    toks = [w for w in toks if w]
    bad = [w for w in toks if w not in words]
    grp = "aligned" if stem in aligned else "skipped"
    rate[grp].append(len(bad) / max(len(toks), 1))
    if grp == "skipped": oovs.update(bad)
for g in rate:
    r = rate[g]
    print(f"{g}: {len(r)} files, mean OOV rate {100*statistics.mean(r):.1f}%, median {100*statistics.median(r):.1f}%, max {100*max(r):.1f}%")
print("most frequent OOV words in the skipped files:", oovs.most_common(25))
