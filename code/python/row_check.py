import csv, glob, os, sys
D = sys.argv[1]; A = sys.argv[2]
stems = {os.path.basename(f)[:-9] for f in glob.glob(A + "/*.TextGrid")}
tot = {"all": [0, 0, 0], "acoustic": [0, 0, 0]}
for f in sorted(glob.glob(D + "/*tracks.csv")):
    name = os.path.basename(f); stem = name[:-11] if name.endswith("_tracks.csv") else name.rsplit("tracks.csv", 1)[0].rstrip("_")
    ids = set(); n = 0
    with open(f, encoding="utf-8") as fh:
        for r in csv.DictReader(fh): n += 1; ids.add(r.get("id"))
    for k in (["all", "acoustic"] if stem in stems else ["all"]):
        tot[k][0] += 1; tot[k][1] += n; tot[k][2] += len(ids)
for k, (nf, nr, nt) in tot.items():
    print(f"{k:9s} files={nf:4d} rows={nr:9d} distinct_vowel_ids={nt:7d} rows_per_vowel={nr/max(nt,1):5.1f}")
