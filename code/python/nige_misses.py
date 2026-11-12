import csv, collections
r = [x for x in csv.DictReader(open("token_level_scores.csv", encoding="utf-8")) if x["cond"] == "NigE" and x["detected"] == "0"]
print(len(r), "NigE misses; what the alignment had there:", collections.Counter(x["model"] for x in r).most_common(12))
for x in r[:15]: print(x["id"], x["file"], x["word"], "you:", x["ann"], "NigE:", x["model"])
