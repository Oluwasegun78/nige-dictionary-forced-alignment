import csv, sys, glob, collections
base, ann_dir = sys.argv[1], sys.argv[2]
key = {r["id"]: r for r in csv.DictReader(open(f"{base}/blind_sample_v2/blind_sample_KEY_do_not_open.csv", encoding="utf-8"))}
ann = {}
for f in sorted(glob.glob(f"{ann_dir}/batch_*_annotated.tsv")):
    for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t"): ann[r["id"]] = r
for _r in ann.values():
    for _k in list(_r):
        if (_r[_k] or "").strip() in ("?", "--undefined--"): _r[_k] = ""
def ok(r):
    l = (r.get("label") or "").strip()
    return l and l != "UNSURE" and r.get("onset_s") not in ("", None)
done = [i for i, r in ann.items() if ok(r)]
tot = collections.Counter(key[i]["nige_label"] for i in key if key[i]["nurse_token"] == "0")
got = collections.Counter(key[i]["nige_label"] for i in done if i in key and key[i]["nurse_token"] == "0")
print(f"Annotated and usable: {len(done)} of {len(key)} drawn")
print("Per NigE label (annotated / drawn):", {k: f"{got[k]}/{tot[k]}" for k in sorted(tot)})
nur_t = sum(1 for i in key if key[i]["nurse_token"] == "1"); nur_g = sum(1 for i in done if i in key and key[i]["nurse_token"] == "1")
print(f"NURSE tokens (annotated / drawn): {nur_g}/{nur_t}")
