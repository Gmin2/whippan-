#!/usr/bin/env python3
# find the bed start offset that lands the music's energy jumps on the
# film's target moments, write audio.start into the doc.
#   align-music.py <doc.stage.json> <t1,t2,...>
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
import librosa
import numpy as np

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc_path, targets = sys.argv[1], [float(t) for t in sys.argv[2].split(",")]
doc = json.load(open(doc_path))
src = doc["audio"]["src"].lstrip("/")

y, sr = librosa.load(src, sr=22050, duration=25)
rms = librosa.feature.rms(y=y, hop_length=256)[0]
jump = np.maximum(np.diff(rms), 0)
t = librosa.frames_to_time(np.arange(len(jump)), sr=sr, hop_length=256)
hop = t[1] - t[0]


def score(shift):
    s = 0.0
    for tgt in targets:
        i = int((tgt + shift) / hop)
        if 0 <= i < len(jump) - 4:
            s += jump[i - 3 : i + 4].max()
    return s


shifts = np.arange(0, 12, 0.01)
best = max(shifts, key=score)
doc["audio"]["start"] = round(float(best), 2)
json.dump(doc, open(doc_path, "w"), indent=1)
print(f"best start {best:.2f}s (score {score(best):.4f}), wired {doc_path}")
for tgt in targets:
    i = int((tgt + best) / hop)
    w = jump[max(0, i - 3) : i + 4]
    print(f"  moment {tgt}s -> jump energy {w.max():.4f}")
