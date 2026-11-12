import csv
r = list(csv.DictReader(open("/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh/POMA_New_20261110/blind_sample_v2/results/token_level_scores.csv", encoding="utf-8")))
n = [x for x in r if x["cond"] == "NigE"]
print("You: i, NigE: ɛː ->", [(x["word"], x["file"]) for x in n if x["ann"] == "i" and x["model"] == "ɛː"])
print("You: monophthong, NigE: diphthong ->", [(x["word"], x["ann"], x["model"]) for x in n if x["mono2diph"] == "1"])
print("You: ɜ or ə, NigE:", [(x["word"], x["ann"], x["model"]) for x in n if x["ann"] in ("ɜ", "ə")][:12])
