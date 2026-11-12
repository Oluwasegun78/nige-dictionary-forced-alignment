import sys, os, glob, re, collections
import numpy as np, soundfile as sf
d = sys.argv[1]
rows = []
for f in sorted(glob.glob(d + "/*.wav")):
    s = os.path.basename(f)[:-4]
    x, sr = sf.read(f, dtype="float64", always_2d=True); x = x.mean(axis=1)
    n = int(sr * 0.025); k = len(x) // n
    e = 10 * np.log10((x[:k*n].reshape(k, n) ** 2).mean(axis=1) + 1e-12)
    txt = open(f[:-4] + ".txt", encoding="utf-8", errors="ignore").read()
    dur = len(x) / sr
    ser = re.match(r"(btal_\d+)_", s).group(1) if s.startswith("btal_") else re.sub(r"\d+$", "", s)
    rows.append((ser, dict(dur=dur, rms=10*np.log10((x**2).mean()+1e-12), peak=np.abs(x).max(),
        dyn=np.percentile(e, 95) - np.percentile(e, 10), quiet=(e < np.percentile(e, 95) - 35).mean() * 100,
        wps=len(re.findall(r"[A-Za-z0-9']+", txt)) / dur, clip=(np.abs(x) >= 0.999).mean() * 100)))
by = collections.defaultdict(list)
for ser, r in rows: by[ser].append(r)
print(f"{'series':9s} {'n':>3s} {'dur_s':>6s} {'rms_dB':>7s} {'peak':>5s} {'dyn_dB':>7s} {'quiet%':>7s} {'words/s':>8s} {'clip%':>6s}")
for ser, v in sorted(by.items(), key=lambda t: -len(t[1])):
    m = lambda k: np.mean([r[k] for r in v])
    print(f"{ser:9s} {len(v):3d} {m('dur'):6.1f} {m('rms'):7.1f} {m('peak'):5.2f} {m('dyn'):7.1f} {m('quiet'):7.1f} {m('wps'):8.2f} {m('clip'):6.2f}")
