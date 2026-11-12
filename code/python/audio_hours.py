import csv, sys, os, glob
base = sys.argv[1]; C = ["NigE", "Indian", "UK", "US"]
csvs = glob.glob(f"{base}/audio_checks/*audio_properties.csv") or glob.glob(f"{base}/**/Indian_audio_properties.csv", recursive=True)
if not csvs: sys.exit("No *_audio_properties.csv found under " + base)
dur = {}
for r in csv.DictReader(open(csvs[0], encoding="utf-8-sig")):
    dur[os.path.splitext(r["file"].strip('"'))[0]] = float(r["duration_sec"])
study = {os.path.splitext(f)[0] for f in os.listdir(f"{base}/NigE") if f.endswith(".wav")}
al = {c: {os.path.splitext(f)[0] for f in os.listdir(f"{base}/{c}") if f.endswith(".TextGrid")} for c in C}
shared = set.intersection(*al.values()); anyal = set.union(*al.values())
H = lambda s: sum(dur[k] for k in s if k in dur) / 3600
def line(name, s): print(f"{name:55s} {len(s):4d} recordings  {H(s):6.3f} h  ({H(s)*60:5.1f} min)")
print("Source:", csvs[0])
line("All audio files in the folder", set(dur))
line("Study recordings (aligned or not)", study)
for c in C: line(f"  aligned under the {c} dictionary", al[c] & study)
line("Aligned by all four dictionaries (the analysed set)", shared & study)
line("Aligned by at least one dictionary", anyal & study)
line("Not aligned by any dictionary", study - anyal)
line("Not aligned by at least one dictionary", study - shared)
for c in C: line(f"  not aligned under the {c} dictionary", study - al[c])
