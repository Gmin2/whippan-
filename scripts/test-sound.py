#!/usr/bin/env python3
# sound conformance: for every doc with an audio bed, verify the file
# exists, the measured bpm matches the declared one, and energy actually
# jumps near each scene boundary (the moments the music should hit).
# exit 1 if any film fails hard checks.
import glob
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
import librosa
import numpy as np

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fails = 0
rows = []
for doc_path in sorted(glob.glob("docs/*.stage.json") + glob.glob("docs/examples/*.stage.json")):
    d = json.load(open(doc_path))
    a = d.get("audio")
    if not a or not a.get("src"):
        continue
    slug = os.path.basename(doc_path).replace(".stage.json", "")
    src = a["src"].lstrip("/")
    if not os.path.exists(src):
        rows.append((slug, "FAIL", "missing file " + src))
        fails += 1
        continue
    start = a.get("start", 0.0)
    dur = sum(s.get("dur", 0) for s in d.get("scenes", []))
    y, sr = librosa.load(src, sr=22050, offset=start, duration=dur + 0.5)
    checks = []
    if a.get("bpm"):
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        m = float(np.atleast_1d(tempo)[0])
        dec = a["bpm"]
        ok = any(abs(m - dec * k) < dec * k * 0.08 for k in (0.5, 1, 2))
        checks.append(f"bpm {m:.0f}/{dec}{'' if ok else ' ~'}")
    # energy jump near interior scene boundaries (within 150ms)
    rms = librosa.feature.rms(y=y, hop_length=256)[0]
    jump = np.maximum(np.diff(rms), 0)
    t = librosa.frames_to_time(np.arange(len(jump)), sr=sr, hop_length=256)
    med = np.median(jump[jump > 0]) if (jump > 0).any() else 0
    bounds, acc = [], 0.0
    for s in d.get("scenes", [])[:-1]:
        acc += s.get("dur", 0)
        bounds.append(acc)
    hit = 0
    for b in bounds:
        w = jump[(t > b - 0.15) & (t < b + 0.15)]
        if len(w) and med > 0 and w.max() > med * 3:
            hit += 1
    if bounds:
        checks.append(f"hits {hit}/{len(bounds)} cuts")
    need = start + dur
    total = librosa.get_duration(path=src)
    if total + 0.1 < need:
        hard = "/gen/" in a["src"] or "/lib/" in a["src"]
        checks.append(f"SHORT bed {total:.1f}s < {need:.1f}s" + (" !!" if hard else " ~"))
        if hard:
            fails += 1
    rows.append((slug, "WARN" if "!!" in " ".join(checks) else "ok", "  ".join(checks)))

w = max(len(r[0]) for r in rows)
for slug, status, detail in rows:
    print(f"{slug:{w}s}  {status:4s}  {detail}")
print(f"\n{len(rows)} films with beds, {fails} hard failures")
sys.exit(1 if fails else 0)
