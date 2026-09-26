"""Original score for the Lotus V7 teaser, synthesised from scratch with numpy.

80 BPM, D major, 40 bars = 120 s. Bar lines fall every 3 s, so every scene
change in teaser.js lands on a downbeat. UI cues (typing, chip pops) use the
same formulas as TYPE_T / CHIP_T / CHIPX_T in teaser.js.

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

# ───────────────────────── harmony ─────────────────────────
CH = {
    'Dmaj9': [50, 57, 61, 64, 66], 'Bm9': [47, 54, 57, 61, 62], 'Gmaj9': [43, 50, 54, 57, 59], 'Asus4': [45, 52, 57, 62, 64],
    'A': [45, 52, 57, 61, 64], 'D/F#': [42, 50, 57, 62, 64], 'Em9': [40, 47, 55, 62, 66], 'A7sus4': [45, 52, 55, 62, 64],
    'D': [50, 57, 62, 64, 66], 'A/C#': [49, 52, 57, 61, 64], 'Bm7': [47, 54, 57, 62, 66], 'Gmaj7': [43, 50, 54, 59, 62],
    'G': [43, 50, 55, 59, 62], 'Em7': [40, 47, 55, 59, 62], 'Gmaj7#11': [43, 50, 54, 57, 61], 'Bmadd9': [47, 54, 59, 61, 62],
    'Emadd9': [40, 47, 54, 55, 59],
}
PROG = {1: 'Dmaj9', 2: 'Bm9', 3: 'Gmaj9', 4: 'Asus4'}
for b in range(5, 21): PROG[b] = ['Gmaj9', 'D/F#', 'Em9', 'A7sus4'][(b - 5) % 4]
PROG.update({21: 'Bm9', 22: 'Gmaj7#11', 23: 'Emadd9', 24: 'Bmadd9', 25: 'Gmaj9', 26: 'Asus4'})
for b, c in zip(range(27, 38), ['D', 'A/C#', 'Bm7', 'Gmaj7', 'D', 'A/C#', 'Bm7', 'G', 'Em7', 'D/F#', 'G']): PROG[b] = c
PROG.update({38: 'D', 39: 'Gmaj9', 40: 'Dmaj9'})

# ───────────────────────── tracks ─────────────────────────
P, PADB, BASS, DR, BELL, UIX, FXB = buf(), buf(), buf(), buf(), buf(), buf(), buf()
kicks = []

def pn(t, m, vel, dur=1.6, g=1.0):
    add(P, piano(m, vel, dur), t, 0.42 * g, pan=np.clip((m - 62) / 40, -0.6, 0.6))

# pads, bar by bar
for b in range(1, 41):
    t0 = bar(b); c = CH[PROG[b]]
    if b == 24: gain, fc = 0.55, 900             # the breath
    elif b <= 4: gain, fc = 0.8, 1100
    elif b <= 23: gain, fc = 0.75 + 0.02 * (b - 5), 1200 + 60 * (b - 5)
    elif b <= 26: gain, fc = 0.9, 1400
    elif b <= 37: gain, fc = 1.0, 2000 + (300 if b >= 33 else 0)
    else: gain, fc = 0.95, 1600
    notes = c[1:] + [c[-1] + 12] if b >= 27 else c[1:]
    att = 2.5 if b == 1 else (1.6 if b in (24, 25) else 0.9)
    if b == 23:                                   # hard stop at 69.0 for the breath
        x = pad(notes, BAR - 0.02, att=0.6, rel=0.25, fc=fc)
    else:
        x = pad(notes, BAR + 0.15, att=att, rel=1.8, fc=fc)
    add(PADB, x, t0 - 0.05, 0.30 * gain)
# Asus4 → A at 77.25
add(PADB, pad([52, 57, 61, 64], 0.75, att=0.3, rel=1.0, fc=1500), 77.25, 0.26)

# intro piano: the dot, the typing, the question
for t, m, v in [(0.22, 74, .42), (1.95, 69, .30), (4.52, 66, .26), (4.52, 69, .26), (4.52, 74, .30),
                (4.85, 78, .36), (5.6, 76, .32), (6.35, 74, .34), (7.8, 69, .30), (8.2, 71, .30), (8.6, 74, .32), (9.0, 76, .36)]:
    pn(t, m, v, dur=2.5)
for i in range(8):                                # A sus arpeggio leaning into 2014
    pn(9.75 + i * 0.375, CH['Asus4'][[0, 2, 3, 4, 1, 3, 2, 4][i]] + 12, 0.22 + i * 0.015, dur=1.2)

# history arpeggios with growing density (bars 5–23)
for b in range(5, 24):
    t0 = bar(b); c = CH[PROG[b]]
    up = [n + 12 for n in c]
    if b <= 8:
        for k, i in enumerate([0, 2, 3, 4]): pn(t0 + k * BEAT, up[i], 0.30 + (0.06 if k == 0 else 0), dur=1.8)
    elif b <= 20:
        pat = [0, 2, 3, 4, 1, 3, 2, 4]
        for k, i in enumerate(pat): pn(t0 + k * BEAT / 2, up[i], 0.26 + (0.08 if k == 0 else 0) + 0.004 * (b - 9), dur=1.3)
    else:
        seq = up + [n + 12 for n in up[1:4]]
        for k in range(16):
            i = k if k < 8 else 15 - k
            pn(t0 + k * BEAT / 4, seq[i % len(seq)], 0.24 + 0.012 * k + 0.05 * (b - 21), dur=0.9)
# station accents: low root + bell
for t in [12, 18, 24, 33, 39, 48, 54, 60]:
    b = int(t // BAR) + 1; c = CH[PROG[b]]
    pn(t, c[0], 0.50, dur=3.0)
    add(BELL, bell(c[3] + 24, 0.35), t + 0.02, 0.5, pan=0.3)
# bell counter-line from CLIP onward
for b in range(12, 21):
    c = CH[PROG[b]]
    add(BELL, bell(c[4] + 24 - (12 if b % 2 else 0), 0.28), bar(b) + 2.5 * BEAT, 0.45, pan=-0.3)
    add(BELL, bell(c[2] + 24, 0.22), bar(b) + 3.5 * BEAT, 0.4, pan=0.35)
# sub bass
for b in range(9, 21):
    add(BASS, sub(CH[PROG[b]][0] - 12, BAR - 0.1, 0.55), bar(b))
for b in range(21, 24):
    for k in range(8): add(BASS, sub(CH[PROG[b]][0] - 12, BEAT / 2 - 0.04, 0.5 + 0.02 * k), bar(b) + k * BEAT / 2)
# drums in history
for b in range(14, 24):
    for k in range(4):
        t = bar(b) + k * BEAT
        if k in (0, 2) or b >= 21:
            v = 0.42 if b < 21 else 0.40 + 0.05 * (b - 21) + (0.05 if k == 0 else 0)
            add(DR, kick(v), t); kicks.append(t)
    if b >= 17:
        n = 8 if b < 21 else 16
        for k in range(n): add(DR, shaker(0.16 + (0.05 if k % 2 else 0) + 0.02 * (b - 17)), bar(b) + k * BAR / n, pan=0.25)

# UI: typing clicks, send, chip pops (same formulas as teaser.js)
PROMPT = 'a penguin running across water'
for i, ch in enumerate(PROMPT):
    t = 2.45 + i * 0.058 + 0.012 * math.sin(i * 2.7)
    add(UIX, click(0.16 if ch != ' ' else 0.10, 2200 + 300 * ((i * 7) % 5)), t, 1.0, pan=0.1)
add(UIX, pop(900, 0.35), 4.45); add(UIX, pop(1350, 0.22), 4.52)
PENTA = [74, 76, 78, 81, 83, 86, 88, 90, 93]
for i in range(24):
    t = 60.8 + 5.4 * (1 - (1 - i / 24) ** 1.6)
    add(UIX, pop(mtof(PENTA[i % len(PENTA)] + 12), 0.14), t, 1.0, pan=((i * 37) % 11 - 5) / 8)
for j in range(16):
    t = 66.2 + 2.6 * (1 - (1 - j / 16) ** 1.4)
    add(UIX, pop(mtof(PENTA[(j * 5) % len(PENTA)] + 12 + (1 if j % 3 == 0 else 0)), 0.15), t, 1.0, pan=((j * 53) % 11 - 5) / 7)

# whooshes on camera moves
for t, d, f0, f1, v in [(10.3, 1.9, 300, 2600, 0.10), (59.9, 1.2, 2400, 500, 0.07), (70.5, 1.5, 1800, 400, 0.08),
                        (81.7, 1.6, 350, 3200, 0.12), (89.6, 1.6, 400, 3800, 0.10), (95.3, 1.2, 2600, 500, 0.08),
                        (99.8, 1.5, 400, 3000, 0.10), (104.5, 1.8, 500, 2500, 0.08), (110.3, 1.6, 400, 2400, 0.08), (113.6, 1.3, 2600, 450, 0.08)]:
    x = sweep(d, f0, f1, v, q=2.5) * hann_env(int(d * SR), 0.8)
    add(FXB, np.vstack([x, np.roll(x, 240)]), t)

# the turn: crowd peak, cut, breath, question, bloom, riser
riser = sweep(9.0, 250, 6000, 0.12, q=3.0, shape=1.6) * np.linspace(0, 1, int(9.0 * SR)) ** 2.2
add(FXB, np.vstack([riser, np.roll(riser, 300)]), 60.0)
pn(69.02, 35, 0.40, dur=4.0); pn(69.02, 47, 0.34, dur=4.0)
for t, m, v in [(69.8, 74, .24), (70.6, 78, .22), (71.4, 85, .16), (72.1, 69, .30), (72.85, 74, .32), (73.6, 76, .36), (74.4, 78, .28)]:
    pn(t, m, v, dur=3.0)
for i, m in enumerate([74, 76, 78, 81, 83, 86, 88, 90]):
    add(BELL, bell(m + 12, 0.30 + 0.02 * i, decay=1.8), 76.0 + i * 0.13, 0.55, pan=-0.4 + i * 0.11)
r2 = sweep(3.0, 400, 9000, 0.16, q=5.0, shape=2.0) * np.linspace(0, 1, int(3.0 * SR)) ** 3
add(FXB, np.vstack([r2, np.roll(r2, 200)]), 75.0)
for i, m in enumerate([57, 62, 64, 69]):          # reversed swell into the downbeat
    x = pad([m + 12], 2.4, att=2.3, rel=0.05, fc=3000)
    add(FXB, x, 75.6, 0.18)

# reveal: bars 27–37 full arrangement
MEL = [  # (beat from 78, midi, beats)
    (0, 78, 1.5), (1.5, 76, .5), (2, 74, 1), (3, 69, 1),
    (4, 76, 2), (6, 73, 1), (7, 76, 1),
    (8, 78, 1.5), (9.5, 81, .5), (10, 78, 1), (11, 74, 1),
    (12, 76, 3), (15, 74, 1),
    (16, 78, 1.5), (17.5, 76, .5), (18, 74, 1), (19, 81, 1),
    (20, 83, 1.5), (21.5, 81, .5), (22, 76, 2),
    (24, 78, 1), (25, 81, 1), (26, 83, 1), (27, 81, 1),
    (28, 86, 2), (30, 83, 1), (31, 81, 1),
    (32, 79, 1.5), (33.5, 78, .5), (34, 76, 1), (35, 71, 1),
    (36, 78, 2), (38, 81, 1), (39, 86, 1),
    (40, 88, 1.5), (41.5, 86, .5), (42, 85, 1), (43, 81, 1),
    (44, 86, 5),
]
for bt, m, ln in MEL:
    t = 78 + bt * BEAT
    pn(t, m, 0.50 if bt % 4 == 0 else 0.44, dur=ln * BEAT + 0.4, g=1.15)
    if t >= 96: add(BELL, bell(m + 12, 0.24), t, 0.55, pan=0.25)
for b in range(27, 38):
    t0 = bar(b); c = CH[PROG[b]]
    up = [n + 12 for n in c]
    for k, i in enumerate([0, 2, 3, 4, 1, 3, 2, 3]): pn(t0 + k * BEAT / 2, up[i], 0.24 + (0.06 if k == 0 else 0), dur=1.2, g=0.8)
    for k in range(8):
        root = c[0] - 12
        add(BASS, sub(root + (12 if k in (3, 7) else 0), BEAT / 2 - 0.05, 0.55), t0 + k * BEAT / 2)
    for k in range(4):
        tk = t0 + k * BEAT
        if k in (0, 2): add(DR, kick(0.55), tk); kicks.append(tk)
        if k in (1, 3): add(DR, snap(0.22), tk, pan=-0.1)
    if b >= 33:
        for k in range(16):
            add(UIX, pluck(up[[1, 2, 3, 4][k % 4]] + 12, 0.10 + 0.03 * (k % 4 == 0)), t0 + k * BEAT / 4, 1.0, pan=0.4 if k % 2 else -0.4)
    for k in range(8): add(DR, shaker(0.13 + 0.06 * (k % 2)), t0 + k * BEAT / 2, pan=0.3)
# downbeats: impact at 78 and 111, lift at 90 and 96
for t, v in [(78.0, 0.8), (90.0, 0.55), (96.0, 0.6), (111.0, 0.75)]:
    b = int(t // BAR) + 1; c = CH[PROG[b]]
    add(DR, kick(v), t); kicks.append(t)
    pn(t, c[0] - 12, 0.55, dur=3.0); pn(t, c[0], 0.5, dur=3.0)
    for i, m in enumerate([c[3] + 24, c[4] + 24, c[2] + 36]): add(BELL, bell(m, 0.3, decay=2.2), t + i * 0.03, 0.5, pan=(i - 1) * 0.4)
# finale
pn(111.0, 86, 0.48, dur=3.5)
for i, m in enumerate([62, 66, 69, 74]): pn(111.0 + i * 0.02, m, 0.34, dur=3.0)
add(BASS, sub(38, 2.8, 0.55), 111.0)
for i, m in enumerate([74, 78, 81, 83, 86, 90]):
    add(BELL, bell(m + 12, 0.26, decay=2.0), 114.35 + i * 0.13, 0.55, pan=-0.4 + i * 0.16)
for t, m, v in [(114.9, 78, .38), (115.65, 76, .34), (116.4, 74, .40)]:
    pn(t, m, v, dur=3.5)
for i, m in enumerate([50, 57, 61, 64, 66, 69]): pn(117.0 + i * 0.05, m, 0.30, dur=4.0)
add(BASS, sub(38, 3.0, 0.45), 117.0)

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
AUT = np.interp(np.arange(N) / SR, [0, 12, 24, 48, 60, 66, 69, 69.3, 72, 77.5, 78, 111, 114, 120, 124],
                [0.9, 0.62, 0.66, 0.74, 0.82, 0.9, 0.95, 0.8, 0.8, 0.9, 1.0, 1.0, 0.95, 0.9, 0.9])
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
