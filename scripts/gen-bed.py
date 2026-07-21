#!/usr/bin/env python3
# synthesized music beds with real percussion, parametric by bpm. still
# not a produced track -- a licensed bed drops in later -- but these
# groove: four-on-floor kick, offbeat hats, clap on 2/4, sub bass with
# sidechain pump, a dark filtered pad. deterministic.
import os
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def write(path, x, gain=0.9):
    x = np.asarray(x) * gain
    p = np.max(np.abs(x)) or 1
    if p > 1:
        x = x / p
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32000).astype(np.int16).tobytes())


def lowpass(x, cutoff):
    rc = 1.0 / (2 * np.pi * cutoff)
    a = (1.0 / SR) / (rc + 1.0 / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def kick():
    t = np.arange(int(SR * 0.28)) / SR
    f = 150 * np.exp(-t / 0.035) + 48
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.11)
    snap = rng.standard_normal(int(SR * 0.004)) * np.exp(-np.arange(int(SR * 0.004)) / (SR * 0.001))
    out = body.copy()
    out[: len(snap)] += snap * 0.4
    return out


def hat(open_=False):
    dur = 0.14 if open_ else 0.045
    n = rng.standard_normal(int(SR * dur))
    hp = n - lowpass(n, 6000)
    return hp * np.exp(-np.arange(len(n)) / (SR * (0.045 if open_ else 0.012)))


def clap():
    dur = 0.18
    n = rng.standard_normal(int(SR * dur))
    band = lowpass(n, 2600) - lowpass(n, 900)
    env = np.exp(-np.arange(len(n)) / (SR * 0.04))
    for d in (0.008, 0.017):
        i = int(SR * d)
        env[i:] += np.exp(-np.arange(len(n) - i) / (SR * 0.03)) * 0.7
    return band * env


def bass_note(freq, dur):
    t = np.arange(int(SR * dur)) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2 * t)
    return lowpass(x, 300) * np.minimum(1, t * 200) * np.exp(-t / (dur * 1.4))


def pad_chord(freqs, dur):
    t = np.arange(int(SR * dur)) / SR
    x = np.zeros(len(t))
    for f in freqs:
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) / len(freqs)
        x += 0.4 * np.sin(2 * np.pi * f * 1.005 * t) / len(freqs)
    env = np.minimum(1, t * 8) * np.minimum(1, (dur - t) * 2)
    return lowpass(x, 900) * env


def make_bed(bpm, bars=16, root=55.0):
    beat = 60.0 / bpm
    total = bars * 4 * beat
    mix = np.zeros(int(SR * total) + SR)

    def place(x, at, g):
        i = int(at * SR)
        j = min(i + len(x), len(mix))
        mix[i:j] += x[: j - i] * g

    k, ho, hc, cl = kick(), hat(True), hat(False), clap()
    for bar in range(bars):
        for b in range(4):
            t0 = (bar * 4 + b) * beat
            place(k, t0, 1.0)
            place(hc, t0 + beat * 0.5, 0.28)
            if b in (1, 3):
                place(cl, t0, 0.5)
            if b == 2:
                place(ho, t0 + beat * 0.5, 0.3)
        # bass: root - root - b7 - 5th walk per bar pair
        seq = [1.0, 1.0, 8.0 / 9.0, 0.75] if bar % 2 else [1.0, 1.0, 1.0, 1.2]
        for b in range(4):
            place(bass_note(root * seq[b], beat * 0.9), (bar * 4 + b) * beat, 0.5)
    # pad layer: two dark chords alternating per 2 bars
    ch_a = [root * 4, root * 4 * 1.19, root * 4 * 1.5]
    ch_b = [root * 4 * 0.89, root * 4 * 1.12, root * 4 * 1.33]
    for i in range(0, bars, 2):
        place(pad_chord(ch_a if i % 4 == 0 else ch_b, 8 * beat), i * 4 * beat, 0.35)
    # sidechain pump: dip everything after each kick
    env = np.ones(len(mix))
    for bar in range(bars):
        for b in range(4):
            i = int((bar * 4 + b) * beat * SR)
            dip = np.linspace(0.45, 1.0, int(SR * beat * 0.6))
            j = min(i + len(dip), len(env))
            env[i:j] = np.minimum(env[i:j], dip[: j - i])
    n = int(SR * total)
    return mix[:n] * env[:n]


for bpm in (112, 122, 136, 160):
    bed = make_bed(bpm)
    write(f"assets/audio/drive-{bpm}.wav", bed, 0.85)
    print(f"drive-{bpm}: {len(bed)/SR:.1f}s")
