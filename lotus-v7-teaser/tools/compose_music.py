"""Original score for the Lotus V7 teaser, synthesised from scratch with numpy.

80 BPM, D major, 40 bars = 120 s. Bar lines fall every 3 s and every chapter of
teaser.js starts on a downbeat. Sound cues (engraving taps, forty carving strokes,
voxel taps, crumbling words) use the same times as the animation.

    python3 tools/compose_music.py            -> dist/music.wav, assets/music.m4a
"""
import math, pathlib, subprocess, sys
import numpy as np
from scipy import signal

SR = 48000
DUR = 120.0
N = int(SR * (DUR + 4))
ROOT = pathlib.Path(__file__).resolve().parent.parent
rng = np.random.default_rng(20260926)

BAR, BEAT = 3.0, 0.75
def bar(i):            # 1-based bar -> start time
    return (i - 1) * BAR

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def buf():
    return np.zeros((2, N), dtype=np.float64)

def add(dst, x, t0, gain=1.0, pan=0.0):
    """Mix mono or stereo x into dst at time t0 with constant-power pan."""
    i0 = int(round(t0 * SR))
    if i0 >= N: return
    if x.ndim == 1:
        a = (pan + 1) * math.pi / 4
        x = np.vstack([x * math.cos(a), x * math.sin(a)]) * math.sqrt(2)
    n = min(x.shape[1], N - i0)
    if i0 < 0:
        x = x[:, -i0:]; n = min(x.shape[1], N); i0 = 0
    dst[:, i0:i0 + n] += x[:, :n] * gain

def lp(x, fc, order=2):
    sos = signal.butter(order, fc, 'low', fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=-1)
def hp(x, fc, order=2):
    sos = signal.butter(order, fc, 'high', fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=-1)
def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], 'band', fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=-1)

# ───────────────────────── instruments ─────────────────────────
_piano_cache = {}
def piano(m, vel, dur):
    """Felt piano: inharmonic partials, two detuned strings, soft hammer."""
    key = (m, round(vel, 2))
    if key not in _piano_cache:
        f = mtof(m); L = 7.0; t = np.arange(int(L * SR)) / SR
        B = 0.00032; base_tau = 3.2 * (262 / f) ** 0.45
        bright = 0.35 + 0.65 * vel
        y = np.zeros_like(t)
        for k in range(1, 16):
            fk = k * f * math.sqrt(1 + B * k * k)
            if fk > 9000: break
            amp = (1 / k ** 1.2) * math.exp(-(k - 1) * (0.36 - 0.24 * bright))
            tau = base_tau / (1 + 0.42 * (k - 1))
            d = 1 + (0.0006 if k < 4 else 0.0009)
            ph = rng.uniform(0, 2 * math.pi)
            y += amp * np.exp(-t / tau) * 0.5 * (np.sin(2 * math.pi * fk * t + ph) + np.sin(2 * math.pi * fk * d * t + ph * 0.7))
        y *= 1 - np.exp(-t / 0.006)
        ham = lp(rng.standard_normal(int(0.03 * SR)), 1800) * np.exp(-np.arange(int(0.03 * SR)) / SR / 0.006) * 0.12
        y[:ham.size] += ham
        y = lp(y, 2600 + 5200 * vel)
        _piano_cache[key] = y / (np.max(np.abs(y)) + 1e-9)
    y = _piano_cache[key].copy()
    r = int(min(dur, 6.0) * SR)
    if r < y.size:
        tail = np.exp(-np.arange(y.size - r) / SR / 0.32)
        y[r:] *= tail
        y = y[:r + int(1.6 * SR)]
    return y * (0.25 + 0.75 * vel)

def pad(notes, dur, att=1.2, rel=1.6, fc=1500, bright=1.0):
    """Warm detuned saw pad, band-limited additive, stereo voices."""
    L = dur + rel; t = np.arange(int(L * SR)) / SR
    out = np.zeros((2, t.size))
    for m in notes:
        f = mtof(m)
        for v, (det, side) in enumerate([(-0.0045, 0), (0.0, None), (0.0048, 1)]):
            ff = f * (1 + det); y = np.zeros_like(t)
            vib = 1 + 0.0012 * np.sin(2 * math.pi * (0.21 + 0.05 * v) * t + v)
            ph = 2 * math.pi * ff * np.cumsum(vib) / SR
            for k in range(1, 18):
                if ff * k > 7000: break
                a = (1 / k) / (1 + (ff * k / (fc * bright)) ** 2)
                y += a * np.sin(k * ph + rng.uniform(0, 6.28))
            if side is None: out += y * 0.5
            else: out[side] += y
    env = np.minimum(1, t / att) ** 1.6
    env *= np.where(t > dur, np.exp(-(t - dur) / (rel / 3)), 1)
    out *= env
    return out / (len(notes) * 1.6)

def bell(m, vel=0.5, ratio=3.5, decay=1.4):
    f = mtof(m); t = np.arange(int((decay * 4) * SR)) / SR
    I = 1.8 * vel * np.exp(-t / 0.18)
    y = np.sin(2 * math.pi * f * t + I * np.sin(2 * math.pi * f * ratio * t))
    y += 0.25 * np.sin(2 * math.pi * f * 2.0 * t) * np.exp(-t / (decay * 0.4))
    y *= np.exp(-t / decay) * (1 - np.exp(-t / 0.002))
    return y * vel

def pluck(m, vel=0.4):
    f = mtof(m); t = np.arange(int(0.9 * SR)) / SR
    y = np.sin(2 * math.pi * f * t) + 0.35 * np.sin(4 * math.pi * f * t) * np.exp(-t / 0.06)
    return lp(y * np.exp(-t / 0.22) * (1 - np.exp(-t / 0.003)), 3500) * vel

def sub(m, dur, vel=0.6):
    f = mtof(m); t = np.arange(int((dur + 0.3) * SR)) / SR
    y = np.sin(2 * math.pi * f * t) + 0.45 * np.sin(4 * math.pi * f * t) + 0.12 * np.sin(6 * math.pi * f * t)
    env = np.minimum(1, t / 0.02) * np.where(t > dur, np.exp(-(t - dur) / 0.08), 1)
    return np.tanh(1.4 * y * env) * vel

def kick(vel=0.6):
    t = np.arange(int(0.6 * SR)) / SR
    f = 46 + 70 * np.exp(-t / 0.035)
    y = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    y += lp(rng.standard_normal(t.size), 5000) * np.exp(-t / 0.005) * 0.3
    return np.tanh(1.6 * y) * vel

def shaker(vel=0.3):
    n = int(0.09 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 6500) * np.exp(-t / 0.022) * (1 - np.exp(-t / 0.004)) * vel

def snap(vel=0.3):
    n = int(0.25 * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 900, 5200) * np.exp(-t / 0.05) * (1 - np.exp(-t / 0.001)) * vel

def click(vel=0.25, f=2400):
    n = int(0.03 * SR); t = np.arange(n) / SR
    y = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.0025) + 0.4 * np.sin(2 * math.pi * f * t) * np.exp(-t / 0.006)
    return y * vel

def pop(f, vel=0.3):
    t = np.arange(int(0.22 * SR)) / SR
    fr = f * (1 + 0.35 * np.exp(-t / 0.02))
    return np.sin(2 * math.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.05) * (1 - np.exp(-t / 0.0015)) * vel

def sweep(dur, f0, f1, vel=0.3, q=4.0, shape=1.0):
    """Filtered-noise whoosh with a moving resonant state-variable filter."""
    n = int(dur * SR); x = rng.standard_normal(n)
    y = np.zeros(n); low = band = 0.0
    fc = f0 * (f1 / f0) ** (np.linspace(0, 1, n) ** shape)
    F = 2 * np.sin(np.pi * np.minimum(fc, 12000) / SR); damp = 1 / q
    for i in range(n):
        low += F[i] * band; high = x[i] - low - damp * band; band += F[i] * high
        y[i] = band
    return y / (np.max(np.abs(y)) + 1e-9) * vel

def hann_env(n, a=0.5):
    t = np.linspace(0, 1, n); return np.sin(np.pi * t) ** a

def cello(m, dur, vel=0.5, att=0.5):
    """Bowed low string: band-limited saw, slow bow, gentle vibrato."""
    f = mtof(m); t = np.arange(int((dur + 1.2) * SR)) / SR
    vib = 1 + 0.0035 * np.sin(2 * math.pi * 5.1 * t) * np.minimum(1, t / 0.8)
    ph = 2 * math.pi * f * np.cumsum(vib) / SR; y = np.zeros_like(t)
    for k in range(1, 22):
        if f * k > 5000: break
        y += (1 / k) * np.sin(k * ph + 0.3 * k) / (1 + (f * k / 900) ** 2)
    env = np.minimum(1, t / att) ** 1.5 * np.where(t > dur, np.exp(-(t - dur) / 0.35), 1)
    return lp(y * env, 2200) * vel

def chisel(vel=0.2, f=3100):
    """Short metallic tap for engraving and carving."""
    t = np.arange(int(0.12 * SR)) / SR
    y = np.sin(2 * math.pi * f * t + 2.2 * np.exp(-t / 0.01) * np.sin(2 * math.pi * f * 2.76 * t))
    y += hp(rng.standard_normal(t.size), 4000) * np.exp(-t / 0.003) * 0.6
    return y * np.exp(-t / 0.028) * vel

def wood(vel=0.2, f=900):
    t = np.arange(int(0.08 * SR)) / SR
    return (np.sin(2 * math.pi * f * t) * np.exp(-t / 0.012) + bp(rng.standard_normal(t.size), 600, 2500) * np.exp(-t / 0.004) * 0.5) * vel

def dust(dur, vel=0.1, lo=1500, hi=9000):
    """Crackle of falling grains."""
    n = int(dur * SR); y = np.zeros(n)
    k = rng.random(n) < 0.004
    y[k] = rng.standard_normal(k.sum())
    return bp(y, lo, hi) * vel * hann_env(n, 0.6)

# ───────────────────────── harmony ─────────────────────────
CH = {
    'Dmaj9': [50, 57, 61, 64, 66], 'Bm9': [47, 54, 57, 61, 62], 'Gmaj9': [43, 50, 54, 57, 59], 'Asus4': [45, 52, 57, 62, 64],
    'A': [45, 52, 57, 61, 64], 'D/F#': [42, 50, 57, 62, 64], 'Em9': [40, 47, 55, 62, 66], 'A7sus4': [45, 52, 55, 62, 64],
    'D': [50, 57, 62, 64, 66], 'A/C#': [49, 52, 57, 61, 64], 'Bm7': [47, 54, 57, 62, 66], 'Gmaj7': [43, 50, 54, 59, 62],
    'G': [43, 50, 55, 59, 62], 'Em7': [40, 47, 55, 59, 62], 'Gmaj7#11': [43, 50, 54, 57, 61], 'Bmadd9': [47, 54, 59, 61, 62],
    'Emadd9': [40, 47, 54, 55, 59], 'Dmaj9/F#': [42, 50, 57, 61, 64],
}
PROG = {1: 'Dmaj9', 2: 'Bm9', 3: 'Gmaj9', 4: 'Asus4', 5: 'Dmaj9', 6: 'Gmaj9', 7: 'Asus4',
        8: 'Bm9', 9: 'Gmaj9', 10: 'Dmaj9/F#', 11: 'A7sus4', 12: 'Bm9', 13: 'Gmaj9', 14: 'Em9', 15: 'Asus4',
        16: 'D', 17: 'Bmadd9', 18: 'Gmaj7#11', 19: 'Em9', 20: 'Gmaj9', 21: 'A7sus4', 22: 'Bm9', 23: 'Gmaj9', 24: 'Asus4',
        25: 'Bmadd9', 26: 'Gmaj7#11', 27: 'Emadd9', 28: 'D', 29: 'A/C#', 30: 'Bm7', 31: 'Gmaj7', 32: 'D', 33: 'A/C#',
        34: 'Bm7', 35: 'G', 36: 'Em7', 37: 'D/F#', 38: 'D', 39: 'Gmaj9', 40: 'Dmaj9'}

# ───────────────────────── tracks ─────────────────────────
P, PADB, BASS, DR, BELL, UIX, FXB = buf(), buf(), buf(), buf(), buf(), buf(), buf()
kicks = []
def pn(t, m, vel, dur=1.6, g=1.0):
    add(P, piano(m, vel, dur), t, 0.42 * g, pan=np.clip((m - 62) / 40, -0.6, 0.6))

# pads and bowed bass, bar by bar
for b in range(1, 41):
    t0 = bar(b); c = CH[PROG[b]]
    lvl = 0.55 if b <= 4 else 0.7 if b <= 15 else 0.78 if b <= 24 else 0.7 if b <= 27 else 1.0 if b <= 37 else 0.9
    fc = 1000 if b <= 4 else 1300 if b <= 24 else 1100 if b <= 27 else 2100
    notes = c[1:] + ([c[-1] + 12] if b >= 28 else [])
    if b == 27: x = pad(notes, 1.3, att=0.6, rel=1.4, fc=fc)          # the breath begins at 79.4
    else: x = pad(notes, BAR + 0.15, att=2.2 if b == 1 else 0.9, rel=1.8, fc=fc)
    add(PADB, x, t0 - 0.05, 0.28 * lvl)
    if b not in (27,) and (b <= 15 or b >= 19):
        add(BASS, cello(c[0] - 12 if c[0] >= 45 else c[0], BAR - 0.2, 0.34 if b <= 4 else 0.3, att=0.9 if b <= 4 else 0.45), t0, 1.0)
add(PADB, pad([52, 57, 61, 64], 0.9, att=0.3, rel=1.0, fc=1400), 20.1, 0.18)

# I · prologue: sparse piano over a low drone, the stone loosening into grain
for t, m, v in [(0.3, 62, .3), (2.6, 69, .34), (3.4, 74, .3), (5.2, 73, .26), (7.4, 66, .32), (8.2, 71, .3), (9.0, 74, .34), (10.6, 76, .3)]:
    pn(t, m, v, dur=2.8)
add(FXB, np.vstack([dust(4.2, 0.35), dust(4.2, 0.35)]), 6.8)
add(FXB, np.vstack([sweep(4.0, 3000, 9000, 0.05, q=2, shape=1.0) * hann_env(int(4.0 * SR)), sweep(4.0, 3200, 9500, 0.05, q=2) * hann_env(int(4.0 * SR))]), 6.9)

# 01 · the sentence is engraved letter by letter
SENT = 'A lotus in full bloom.'
for i, ch in enumerate(SENT):
    if ch != ' ': add(UIX, chisel(0.12, 2900 + 180 * (i % 4)), 13.2 + i * 1.3 / len(SENT), 1.0, pan=0.1)
for t, m, v in [(12.0, 62, .32), (13.0, 66, .26), (15.0, 69, .3), (16.7, 74, .34), (18.0, 73, .28), (19.5, 69, .3)]:
    pn(t, m, v, dur=2.5)

# 02 · learning: harp figures; noise swells forward, then rewinds
for b in range(8, 12):
    up = [n + 12 for n in CH[PROG[b]]]
    for k, i in enumerate([0, 2, 3, 4, 1, 3, 2, 4]): add(UIX, pluck(up[i] + 12, 0.16 + 0.03 * (k == 0)), bar(b) + k * BEAT / 2, 1.0, pan=0.3 if k % 2 else -0.3)
fw = sweep(3.6, 500, 7000, 0.14, q=3, shape=1.4) * np.linspace(0, 1, int(3.6 * SR)) ** 1.5
add(FXB, np.vstack([fw, np.roll(fw, 200)]), 22.2)
rv = fw[::-1] * 0.9
add(FXB, np.vstack([rv, np.roll(rv, 200)]), 27.2)
for k in range(5): add(BELL, bell(81 - k * 2, 0.22), 27.3 + k * 0.85, 0.5, pan=-0.4 + k * 0.2)

# 03 · carving: forty chisel strokes climbing the scale, then the form is revealed
SCALE = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83]
for k in range(40):
    t = 33.9 + k * (44.1 - 33.9) / 40
    add(UIX, pluck(SCALE[(k * 3) % 10] + 12, 0.1 + 0.004 * k), t, 1.0, pan=((k * 7) % 9 - 4) / 6)
    add(UIX, chisel(0.05 + 0.002 * k, 3300), t, 1.0, pan=0.05)
for b in range(12, 16):
    up = [n + 12 for n in CH[PROG[b]]]
    for k, i in enumerate([0, 2, 3, 4]): pn(bar(b) + k * BEAT, up[i], 0.22 + 0.02 * (b - 12), dur=1.8, g=0.8)
for i, m in enumerate([74, 78, 81, 86, 90]): add(BELL, bell(m, 0.3, decay=2.4), 44.1 + i * 0.07, 0.6, pan=-0.3 + i * 0.15)

# 04 · steering: melody; cards flip; the chord darkens for the bud and opens again
for t, m, v, d in [(45.0, 78, .36, 1.2), (45.75, 76, .3, .8), (46.5, 74, .34, 1.5), (48.0, 81, .32, 2.2), (50.2, 71, .3, 1.5), (51.4, 69, .28, 1.5), (53.1, 78, .38, 2.4)]:
    pn(t, m, v, dur=d + 0.6)
for t in (49.4, 52.4):
    x = sweep(0.7, 800, 4000, 0.07, q=2) * hann_env(int(0.7 * SR)); add(FXB, np.vstack([x, x]), t - 0.1)
add(BELL, bell(85, 0.28, decay=2.0), 53.0, 0.5, pan=0.3)

# 05 · the sketch: small wooden taps as the clay voxels land; a rising shimmer for the decoder
rr = np.random.default_rng(5)
for k in range(46): add(UIX, wood(0.09 + rr.random() * 0.05, 700 + rr.random() * 700), 54.9 + k * 0.037 + rr.random() * 0.04, 1.0, pan=rr.random() - 0.5)
dec = sweep(1.8, 600, 9000, 0.1, q=5, shape=1.5) * np.linspace(0, 1, int(1.8 * SR)) ** 1.2 * hann_env(int(1.8 * SR), 0.3)
add(FXB, np.vstack([dec, np.roll(dec, 300)]), 58.5)
for i, m in enumerate([69, 74, 78, 81]): add(BELL, bell(m + 12, 0.22, decay=1.6), 58.7 + i * 0.28, 0.5, pan=0.4 - i * 0.2)
for t, m, v in [(54.0, 64, .3), (55.5, 66, .28), (57.0, 71, .3), (60.0, 69, .3), (61.5, 73, .28)]: pn(t, m, v, dur=2.2)

# 06 · the workshop: a pulse arrives; threads ring like glass
for b in range(22, 25):
    up = [n + 12 for n in CH[PROG[b]]]
    for k, i in enumerate([0, 2, 3, 4, 1, 3, 2, 4]): pn(bar(b) + k * BEAT / 2, up[i], 0.24 + (0.06 if k == 0 else 0), dur=1.2, g=0.8)
    for k in range(4):
        tk = bar(b) + k * BEAT
        if k in (0, 2): add(DR, kick(0.42), tk); kicks.append(tk)
    for k in range(8): add(DR, shaker(0.12 + 0.05 * (k % 2)), bar(b) + k * BEAT / 2, pan=0.3)
    add(BASS, sub(CH[PROG[b]][0] - 12, BAR - 0.1, 0.5), bar(b))
for k in range(18): add(BELL, bell(SCALE[(k * 4) % 10] + 24, 0.12, ratio=4.1, decay=0.8), 66.0 + k * 0.09, 0.45, pan=((k * 5) % 7 - 3) / 4)
x = sweep(1.2, 400, 3000, 0.08, q=2) * hann_env(int(1.2 * SR)); add(FXB, np.vstack([x, np.roll(x, 150)]), 64.4)

# 07 · the catch: rough stone, a pile of magic words, then they crumble — and silence
for t, m in [(72.2, 47), (72.2, 54)]: pn(t, m, 0.4, dur=3.0)
for k in range(64): add(UIX, chisel(0.07, 2600 + 400 * (k % 3)), 75.3 + k * 2.2 / 64, 1.0, pan=((k * 3) % 7 - 3) / 5)
tens = pad([61, 66, 67, 71], 3.8, att=2.5, rel=0.4, fc=2500)
add(FXB, tens, 75.2, 0.12)
add(FXB, np.vstack([dust(1.8, 0.55, 400, 6000), dust(1.8, 0.55, 400, 6000)]), 78.5)
fall = sweep(1.6, 3000, 200, 0.08, q=2) * hann_env(int(1.6 * SR)); add(FXB, np.vstack([fall, fall]), 78.6)

# Lotus V7: arrival chord, bells, the crane up to the inscription
riser = sweep(1.4, 300, 8000, 0.1, q=4, shape=2) * np.linspace(0, 1, int(1.4 * SR)) ** 3
add(FXB, np.vstack([riser, np.roll(riser, 200)]), 79.6)
MEL = [(0, 78, 1.5), (1.5, 76, .5), (2, 74, 1), (3, 69, 1), (4, 76, 2), (6, 73, 1), (7, 76, 1),
       (8, 78, 1.5), (9.5, 81, .5), (10, 78, 1), (11, 74, 1), (12, 76, 3), (15, 74, 1),
       (16, 78, 1.5), (17.5, 76, .5), (18, 74, 1), (19, 81, 1), (20, 83, 1.5), (21.5, 81, .5), (22, 76, 2),
       (24, 78, 1), (25, 81, 1), (26, 83, 1), (27, 81, 1), (28, 86, 2), (30, 83, 1), (31, 81, 1),
       (32, 79, 1.5), (33.5, 78, .5), (34, 76, 1), (35, 71, 1), (36, 78, 2), (38, 81, 1), (39, 86, 1), (40, 86, 5)]
for bt, m, ln in MEL:
    t = 81 + bt * BEAT
    pn(t, m, 0.5 if bt % 4 == 0 else 0.44, dur=ln * BEAT + 0.4, g=1.15)
    if t >= 99: add(BELL, bell(m + 12, 0.22), t, 0.55, pan=0.25)
for b in range(28, 38):
    t0 = bar(b); c = CH[PROG[b]]; up = [n + 12 for n in c]
    for k, i in enumerate([0, 2, 3, 4, 1, 3, 2, 3]): pn(t0 + k * BEAT / 2, up[i], 0.22 + (0.06 if k == 0 else 0), dur=1.2, g=0.75)
    for k in range(8): add(BASS, sub(c[0] - 12 + (12 if k in (3, 7) else 0), BEAT / 2 - 0.05, 0.5), t0 + k * BEAT / 2)
    if b >= 30:
        for k in range(4):
            tk = t0 + k * BEAT
            if k in (0, 2): add(DR, kick(0.5), tk); kicks.append(tk)
            if k in (1, 3): add(DR, snap(0.18), tk, pan=-0.1)
        for k in range(8): add(DR, shaker(0.12 + 0.05 * (k % 2)), t0 + k * BEAT / 2, pan=0.3)
    if b >= 34:
        for k in range(16): add(UIX, pluck(up[[1, 2, 3, 4][k % 4]] + 12, 0.09 + 0.03 * (k % 4 == 0)), t0 + k * BEAT / 4, 1.0, pan=0.4 if k % 2 else -0.4)
for t, v in [(81.0, 0.75), (87.0, 0.5), (99.0, 0.55)]:
    b = int(t // BAR) + 1; c = CH[PROG[b]]
    add(DR, kick(v), t); kicks.append(t)
    pn(t, c[0] - 12, 0.55, dur=3.0); pn(t, c[0], 0.5, dur=3.0)
    for i, m in enumerate([c[3] + 24, c[4] + 24, c[2] + 36]): add(BELL, bell(m, 0.3, decay=2.2), t + i * 0.03, 0.5, pan=(i - 1) * 0.4)
crane = pad([69, 74, 78, 81], 3.2, att=2.6, rel=1.2, fc=3000); add(FXB, crane, 81.8, 0.14)
# Realistic: the patch resolve shimmers; the jungle opens with a soft rush
for k in range(24): add(BELL, bell(SCALE[(k * 3) % 10] + 24, 0.08, ratio=4.1, decay=0.6), 89.0 + k * 0.16, 0.4, pan=((k * 5) % 9 - 4) / 5)
x = sweep(1.8, 300, 4000, 0.1, q=2) * hann_env(int(1.8 * SR)); add(FXB, np.vstack([x, np.roll(x, 240)]), 96.9)
# Anime: a quick pencil scratch for the line art, colour arrives with bells
for t0, d in [(100.3, 1.6), (106.5, 1.1)]:
    sc = bp(rng.standard_normal(int(d * SR)), 2500, 7000) * (0.5 + 0.5 * np.abs(np.sin(np.linspace(0, 40 * d, int(d * SR))))) * hann_env(int(d * SR)) * 0.05
    add(FXB, np.vstack([sc, np.roll(sc, 90)]), t0)
for t0 in (101.9, 107.4):
    for i, m in enumerate([78, 81, 85, 90]): add(BELL, bell(m + 12, 0.18, decay=1.6), t0 + i * 0.12, 0.5, pan=-0.3 + i * 0.2)

# finale: resolve on the carved title
for i, m in enumerate([62, 66, 69, 74]): pn(111.0 + i * 0.02, m, 0.34, dur=3.0)
add(BASS, cello(38, 5.5, 0.34, att=0.6), 111.0)
add(DR, kick(0.55), 111.0); kicks.append(111.0)
pn(111.0, 86, 0.46, dur=3.5)
for t, m, v in [(114.2, 78, .36), (114.95, 76, .32), (115.7, 74, .38)]: pn(t, m, v, dur=3.5)
for i, m in enumerate([74, 78, 81, 83, 86, 90]): add(BELL, bell(m + 12, 0.2, decay=2.2), 116.6 + i * 0.14, 0.5, pan=-0.4 + i * 0.16)
for i, m in enumerate([50, 57, 61, 64, 66, 69]): pn(117.0 + i * 0.05, m, 0.28, dur=4.0)
add(BASS, cello(38, 3.2, 0.3, att=0.8), 117.0)

# camera moves
for t, d, f0, f1, v in [(20.1, 3.0, 300, 1800, 0.06), (32.0, 3.0, 1800, 300, 0.06), (53.6, 2.8, 300, 2200, 0.06), (62.4, 1.8, 2000, 400, 0.05),
                        (85.2, 2.4, 300, 2200, 0.07), (98.9, 2.5, 400, 2600, 0.08), (110.5, 3.0, 2200, 300, 0.07)]:
    x = sweep(d, f0, f1, v, q=2.5) * hann_env(int(d * SR), 0.8)
    add(FXB, np.vstack([x, np.roll(x, 240)]), t)

# ───────────────────────── mix ─────────────────────────
def sidechain(x, depth=0.35, tau=0.16):
    g = np.ones(N)
    for tk in kicks:
        i0 = int(tk * SR); n = min(int(0.6 * SR), N - i0)
        if n <= 0: continue
        tt = np.arange(n) / SR
        g[i0:i0 + n] = np.minimum(g[i0:i0 + n], 1 - depth * np.exp(-tt / tau))
    return x * g

def reverb_ir(L=3.4, tau=0.62, pre=0.022):
    n = int(L * SR); t = np.arange(n) / SR
    ir = np.zeros((2, n))
    for ch in range(2):
        e = rng.standard_normal(n) * np.exp(-t / tau)
        dark = lp(e, 2400) * 0.8; bright = hp(e, 2400) * np.exp(-t / 0.18) * 0.5
        ir[ch] = dark + bright
    for d, g in [(0.011, .5), (0.017, .4), (0.023, .35), (0.031, .3), (0.041, .25)]:  # early reflections
        ir[0, int(d * SR)] += g; ir[1, int((d + 0.0037) * SR)] += g
    ir = np.concatenate([np.zeros((2, int(pre * SR))), ir], axis=1)
    return ir / np.sqrt((ir ** 2).sum(axis=1, keepdims=True))

PADB = sidechain(PADB, 0.30); BASS = sidechain(BASS, 0.45, 0.12)
# section dynamics: build through history, breathe at the turn, peak at the reveal
AUT = np.interp(np.arange(N) / SR, [0, 12, 21, 33, 45, 54, 63, 72, 78.4, 79.4, 80.6, 81, 111, 114, 120, 124],
                [0.85, 0.72, 0.74, 0.8, 0.82, 0.8, 0.88, 0.9, 0.95, 0.55, 0.6, 1.0, 1.0, 0.95, 0.9, 0.9])
dry = (P * 1.0 + PADB * 1.0 + BASS * 0.38 + DR * 0.42 + BELL * 0.6 + UIX * 0.7 + FXB * 0.8) * AUT
send = (P * 0.34 + PADB * 0.30 + BELL * 0.55 + UIX * 0.25 + FXB * 0.35 + DR * 0.04) * AUT
ir = reverb_ir()
wet = np.vstack([signal.fftconvolve(send[c], ir[c])[:N] for c in range(2)])
mix = dry + wet * 0.42
mix = hp(mix, 35)
mix = mix + hp(mix, 5500) * 0.45 - lp(mix, 140) * 0.18   # air shelf, tame lows

# gentle bus compression (RMS, 2:1 above threshold) and soft limiting
rms = np.sqrt(signal.sosfilt(signal.butter(1, 6, fs=SR, output='sos'), (mix ** 2).mean(axis=0)) + 1e-12)
thr = np.percentile(rms[: int(DUR * SR)], 88)
gain = np.where(rms > thr, (thr / rms) ** 0.33, 1.0)
mix *= gain

try:
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(mix[:, : int(DUR * SR)].T)
    mix *= 10 ** ((-15.5 - lufs) / 20)
except Exception as e:
    print('loudness fallback:', e); mix /= np.max(np.abs(mix)) / 0.7

ceiling = 10 ** (-1.0 / 20)
mix = np.tanh(mix / ceiling) * ceiling
mix = mix[:, : int(DUR * SR)]
fade_in = int(0.02 * SR); mix[:, :fade_in] *= np.linspace(0, 1, fade_in)
fo = int(1.6 * SR); mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5

out_wav = ROOT / 'dist' / 'music.wav'
out_wav.parent.mkdir(parents=True, exist_ok=True)
from scipy.io import wavfile
wavfile.write(out_wav, SR, (mix.T * 32767).astype(np.int16))
try:
    import pyloudnorm as pyln
    print('integrated LUFS', round(pyln.Meter(SR).integrated_loudness(mix.T), 2), 'peak dBFS', round(20 * np.log10(np.max(np.abs(mix))), 2))
except Exception:
    pass
ff = sys.argv[1] if len(sys.argv) > 1 else 'ffmpeg'
subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(out_wav), '-c:a', 'aac', '-b:a', '256k', str(ROOT / 'assets' / 'music.m4a')], check=True)
print('wrote', out_wav, 'and assets/music.m4a')
