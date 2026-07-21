#!/usr/bin/env python3
# procedural sfx kit: the micro-sounds of motion videos, synthesized.
# every sound is a parameterized transient (5-400ms) built from noise
# bursts, pitch-bent sines and simple one-pole filters -- no samples.
# writes variant banks into assets/sfx/ plus a listening demo into out/
# that sequences them the way a real film would use them: a typewriter
# with humanized ticks, a ui click, a rising pop cascade, a whoosh, a
# success ding. deterministic (seeded) so the kit is rebuildable.
import os
import struct
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(44)

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("assets/sfx", exist_ok=True)


def write_wav(path, x, gain=1.0):
    x = np.asarray(x, dtype=np.float64) * gain
    peak = np.max(np.abs(x)) or 1.0
    if peak > 1.0:
        x = x / peak
    pcm = (x * 32000).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def env_exp(dur, tau):
    return np.exp(-t_axis(dur) / tau)


def highpass(x, cutoff):
    # one-pole highpass, enough to make a noise burst read as a tick
    rc = 1.0 / (2 * np.pi * cutoff)
    a = rc / (rc + 1.0 / SR)
    y = np.zeros_like(x)
    for i in range(1, len(x)):
        y[i] = a * (y[i - 1] + x[i] - x[i - 1])
    return y


def lowpass(x, cutoff):
    rc = 1.0 / (2 * np.pi * cutoff)
    a = (1.0 / SR) / (rc + 1.0 / SR)
    y = np.zeros_like(x)
    for i in range(1, len(x)):
        y[i] = y[i - 1] + a * (x[i] - y[i - 1])
    return y


def tick(pitch=1.0):
    """keyboard tick: 6ms high-passed noise snap + a whisper of body."""
    n = highpass(rng.standard_normal(int(SR * 0.006)), 2600 * pitch)
    n *= env_exp(0.006, 0.0012)
    body = np.sin(2 * np.pi * 190 * pitch * t_axis(0.004)) * env_exp(0.004, 0.0015) * 0.25
    out = np.zeros(int(SR * 0.010))
    out[: len(n)] += n
    out[: len(body)] += body
    return out


def thock(pitch=1.0):
    """typewriter body knock: rounder, meatier than the tick."""
    k = lowpass(rng.standard_normal(int(SR * 0.02)), 900 * pitch)
    k *= env_exp(0.02, 0.004)
    body = np.sin(2 * np.pi * 150 * pitch * t_axis(0.03)) * env_exp(0.03, 0.008) * 0.5
    out = np.zeros(int(SR * 0.035))
    out[: len(k)] += k
    out[: len(body)] += body
    return out


def click():
    """ui click: bright tick over a low 120hz thump."""
    top = tick(1.2) * 0.8
    thump = np.sin(2 * np.pi * 120 * t_axis(0.045)) * env_exp(0.045, 0.012) * 0.6
    out = np.zeros(int(SR * 0.05))
    out[: len(top)] += top
    out[: len(thump)] += thump
    return out


def pop(step=0):
    """element pop: pitch-bent blip. step walks up the cascade scale."""
    f0 = 520 * (2 ** (step / 12 * 2))          # two semitones per step
    dur = 0.045
    t = t_axis(dur)
    freq = f0 * (2 ** (-t / 0.05))             # falling glide
    phase = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * env_exp(dur, 0.012)
    snap = highpass(rng.standard_normal(int(SR * 0.002)), 3000)
    snap *= env_exp(0.002, 0.0006) * 0.5
    out = np.zeros(int(SR * dur))
    out += body
    out[: len(snap)] += snap
    return out * 0.8


def whoosh(dur=0.38):
    """camera whoosh: band-swept noise, rises then exits."""
    n = rng.standard_normal(int(SR * dur))
    lo = lowpass(n, 400)
    hi = lowpass(n, 3600)
    band = hi - lo
    t = t_axis(dur)
    sweep = np.sin(np.pi * t / dur) ** 2       # in and out
    tilt = np.linspace(0.4, 1.0, len(t))       # brightens as it passes
    return band * sweep * tilt * 0.7


def ding():
    """success chime: three partials, long decay."""
    dur = 0.7
    t = t_axis(dur)
    out = np.zeros(len(t))
    for f, g, tau in [(880, 1.0, 0.22), (1318, 0.5, 0.16), (1760, 0.3, 0.11)]:
        out += np.sin(2 * np.pi * f * t) * np.exp(-t / tau) * g
    return out * 0.35


def place(mix, sound, at, gain=1.0):
    i = int(at * SR)
    j = min(i + len(sound), len(mix))
    mix[i:j] += sound[: j - i] * gain


# ---- the kit: variant banks --------------------------------------------
for i in range(8):
    write_wav(f"assets/sfx/tick_{i+1:02d}.wav", tick(1.0 + (i - 4) * 0.045))
    write_wav(f"assets/sfx/pop_{i+1:02d}.wav", pop(i))
write_wav("assets/sfx/thock.wav", thock())
write_wav("assets/sfx/click.wav", click())
write_wav("assets/sfx/whoosh.wav", whoosh())
write_wav("assets/sfx/ding.wav", ding())

# ---- the listening demo -------------------------------------------------
# how a film would use them: humanized typewriter, a click on send, a
# rising cascade as cards stagger in, a whoosh on the whip, a ding to land.
demo = np.zeros(int(SR * 6.2))

# 1. typewriter (14 keystrokes, 65ms cadence, jittered pitch and gain,
#    a thock on the space, the last key accented)
at = 0.35
for i in range(14):
    if i == 8:
        place(demo, thock(), at, 0.9)
    else:
        v = tick(1.0 + rng.uniform(-0.12, 0.12))
        place(demo, v, at, 0.75 + rng.uniform(-0.1, 0.1))
    at += 0.065 + rng.uniform(-0.008, 0.008)
place(demo, tick(0.82), at + 0.12, 1.15)      # the period, accented

# 2. ui click on send
place(demo, click(), 2.2, 1.0)

# 3. the cascade: five cards pop in, each a step higher
for i in range(5):
    place(demo, pop(i), 2.9 + i * 0.14, 0.9)

# 4. whip pan
place(demo, whoosh(), 4.1, 1.0)

# 5. landing ding
place(demo, ding(), 4.9, 1.0)

write_wav("out/sfx-demo.wav", demo, gain=0.9)
print("kit:", len(os.listdir("assets/sfx")), "files in assets/sfx/")
print("demo: out/sfx-demo.wav (6.2s)")
