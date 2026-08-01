#!/usr/bin/env python3
# generate a music bed for a film with lyria 3 (gemini api). reads the
# film's stage doc, turns its scene boundaries into a timestamped
# instrumental prompt, generates, measures bpm/offset, saves to
# assets/audio/gen/<slug>.mp3 and wires the stage audio field.
#
#   gen-music.py <slug> [mood] [bpm]
#
# mood defaults to "driving minimal electronic, dark, four on the floor".
# needs GEMINI_API_KEY in whippan/.env (paid tier; $0.04 per clip).
import base64
import json
import os
import sys
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for line in open(".env"):
    if line.startswith("GEMINI_API_KEY="):
        KEY = line.split("=", 1)[1].strip()
        break
else:
    sys.exit("no GEMINI_API_KEY in .env")

slug = sys.argv[1]
mood = sys.argv[2] if len(sys.argv) > 2 else \
    "driving minimal electronic, dark, four on the floor kick, tight hats"
bpm_hint = sys.argv[3] if len(sys.argv) > 3 else None

stage = json.load(open(f"docs/{slug}.stage.json"))
scenes = stage.get("scenes", [])
total = sum(s.get("dur", 0) for s in scenes) or stage.get("dur", 10)


def ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


lines = [f"Instrumental only, no vocals. {mood}."]
if bpm_hint:
    lines[0] += f" Exactly {bpm_hint} bpm, steady tempo throughout."
t = 0.0
for i, s in enumerate(scenes):
    d = s.get("dur", 0)
    if i == 0:
        part = "sparse intro, percussion enters with a clear downbeat at 0:00"
    elif i == len(scenes) - 1:
        part = "final section, biggest energy, hard hit on the downbeat"
    else:
        part = "add a layer, energy step up, accent hit on the downbeat"
    lines.append(f"[{ts(t)} - {ts(t + d)}] {part}.")
    t += d
lines.append(f"[{ts(total)}] everything cuts to silence.")
prompt = "\n".join(lines)
print(prompt)

req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/interactions",
    data=json.dumps({"model": "lyria-3-clip-preview",
                     "input": prompt}).encode(),
    headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
resp = json.load(urllib.request.urlopen(req, timeout=300))


def find_audio(obj):
    if isinstance(obj, dict):
        d = obj.get("data")
        if isinstance(d, str) and len(d) > 10000:
            return d
        for v in obj.values():
            r = find_audio(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_audio(v)
            if r:
                return r


audio = find_audio(resp)
if not audio:
    json.dump(resp, open("out/lyria-resp.json", "w"), indent=1)
    sys.exit("no audio in response, dumped to out/lyria-resp.json")

os.makedirs("assets/audio/gen", exist_ok=True)
path = f"assets/audio/gen/{slug}.mp3"
open(path, "wb").write(base64.b64decode(audio))
print(f"wrote {path} ({os.path.getsize(path) // 1024}kb)")

import warnings
warnings.filterwarnings("ignore")
import librosa
import numpy as np
y, sr = librosa.load(path, sr=22050)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
times = librosa.frames_to_time(beats, sr=sr)
bpm = round(float(np.atleast_1d(tempo)[0]), 1)
offset = round(float(times[0]), 3) if len(times) else 0.0
print(f"measured {bpm} bpm, first beat {offset}s")

stage["audio"] = {"src": f"/assets/audio/gen/{slug}.mp3", "gain": 0.85,
                  "fade_out": 0.5, "bpm": bpm, "offset": offset}
json.dump(stage, open(f"docs/{slug}.stage.json", "w"), indent=1)
print(f"wired docs/{slug}.stage.json")
