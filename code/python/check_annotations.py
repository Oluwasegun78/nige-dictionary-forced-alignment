import csv, sys, collections, statistics as st
path = sys.argv[1]
INVENTORY = {"a","aː","e","i","iː","o","u","uː","ɔ","ɛ","ɛː","ʊ","ɜ","ə","ʌ","ou","eə"}
rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))
for _r in rows:
    for _k in list(_r):
        if (_r[_k] or "").strip() in ("?", "--undefined--"): _r[_k] = ""
def num(x):
    try: return float(x)
    except: return None
done = [r for r in rows if (r.get("label") or "").strip() and r["label"].strip() != "UNSURE" and num(r.get("onset_s")) is not None]
unsure = [r for r in rows if (r.get("label") or "").strip() == "UNSURE"]
blank = [r for r in rows if not (r.get("label") or "").strip()]
print(f"Rows: {len(rows)} | annotated: {len(done)} | UNSURE: {len(unsure)} | blank: {len(blank)}")
bad = []
for r in done:
    on, off, ws, we = num(r["onset_s"]), num(r["offset_s"]), num(r["window_start"]), num(r["window_end"])
    d = off - on
    why = []
    if d < 0.03: why.append(f"very short ({d*1000:.0f} ms)")
    if d > 0.35: why.append(f"very long ({d*1000:.0f} ms)")
    if on < ws - 0.001 or off > we + 0.001: why.append("outside the time window")
    if r["label"].strip() not in INVENTORY: why.append(f"label '{r['label'].strip()}' not in the inventory")
    if why: bad.append((r["id"], r["file"], r["word"], "; ".join(why)))
print("Labels chosen:", dict(collections.Counter(r["label"].strip() for r in done).most_common()))
dur = collections.defaultdict(list)
for r in done: dur[r["label"].strip()].append((num(r["offset_s"]) - num(r["onset_s"])) * 1000)
print("Median duration by label (ms):", {k: round(st.median(v)) for k, v in sorted(dur.items())})
print(f"Rows to look at again: {len(bad)}")
for b in bad[:25]: print("  ", *b)
print("UNSURE rows (id, word, notes):", [(r["id"], r["word"], (r.get("notes") or "")[:30]) for r in unsure][:15])
