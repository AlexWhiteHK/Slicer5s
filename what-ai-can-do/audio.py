"""Score and sound design, synthesised from scratch with numpy/scipy.

The palette of sounds follows the picture: 1-bit pulses on paper, NES-style
channels on the CRTs, 16-bit echoes in the neon years, detuned synths for the
modern era and soft bells over the evening sea.

  python3 audio.py out.wav
"""
import math
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

import timeline as tl

SR = 48000
N = int(tl.DURATION * SR)
rng = np.random.default_rng(1943)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ oscillators
def _t(dur):
    return np.arange(max(1, int(dur * SR))) / SR


def _freq(f, dur, f_end=None, vib=0.0, vib_rate=5.5):
    n = max(1, int(dur * SR))
    if f_end is None:
        fr = np.full(n, float(f))
    else:
        fr = np.geomspace(max(f, 1), max(f_end, 1), n)
    if vib:
        fr = fr * (1 + vib * np.sin(2 * np.pi * vib_rate * np.arange(n) / SR))
    return fr


def _blep(p, dt):
    out = np.zeros_like(p)
    m = p < dt
    x = p[m] / dt[m]
    out[m] = x + x - x * x - 1
    m = p > 1 - dt
    x = (p[m] - 1) / dt[m]
    out[m] = x * x + x + x + 1
    return out


def pulse(f, dur, duty=0.5, f_end=None, vib=0.0):
    fr = _freq(f, dur, f_end, vib)
    dt = fr / SR
    ph = np.cumsum(dt) % 1
    s = np.where(ph < duty, 1.0, -1.0)
    s += _blep(ph, dt)
    s -= _blep((ph - duty) % 1, dt)
    return s * 0.5


def saw(f, dur, f_end=None, vib=0.0):
    fr = _freq(f, dur, f_end, vib)
    dt = fr / SR
    ph = (np.cumsum(dt) + rng.random()) % 1
    return (2 * ph - 1 - _blep(ph, dt)) * 0.5


def tri(f, dur, f_end=None, steps=16):
    fr = _freq(f, dur, f_end)
    ph = np.cumsum(fr / SR) % 1
    s = 4 * np.abs(ph - 0.5) - 1
    if steps:
        s = np.round(s * steps / 2) / (steps / 2)
    return s * 0.6


def sine(f, dur, f_end=None):
    fr = _freq(f, dur, f_end)
    return np.sin(2 * np.pi * np.cumsum(fr / SR))


def white(dur):
    return rng.uniform(-1, 1, max(1, int(dur * SR)))


def _lfsr(short):
    reg = 1
    out = np.empty(32767 if not short else 93)
    for i in range(len(out)):
        bit = (reg ^ (reg >> (6 if short else 1))) & 1
        reg = (reg >> 1) | (bit << 14)
        out[i] = 1.0 if reg & 1 else -1.0
    return out


_LFSR_LONG = _lfsr(False)
_LFSR_SHORT = _lfsr(True)


def nes_noise(dur, rate=8000, short=False):
    n = max(1, int(dur * SR))
    seq = _LFSR_SHORT if short else _LFSR_LONG
    idx = (np.arange(n) * rate / SR).astype(int) % len(seq)
    return seq[idx] * 0.5


# ------------------------------------------------------------------ envelopes / filters
def env(n, a=0.002, d=0.1, s=0.0, r=0.02, hold=None):
    t = np.arange(n) / SR
    e = np.ones(n)
    if a > 0:
        e = np.minimum(e, t / a)
    dec = s + (1 - s) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    e = np.minimum(e, dec)
    if r > 0:
        e *= np.clip((n / SR - t) / r, 0, 1)
    return e


def exp_env(n, decay):
    return np.exp(-np.arange(n) / SR / decay)


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(0.99, fc / (SR / 2)), 'low')
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, min(0.99, fc / (SR / 2)), 'high')
    return signal.lfilter(b, a, x)


def bp(x, f0, q=2.0):
    lo, hi = f0 / (1 + 1 / (2 * q)), f0 * (1 + 1 / (2 * q))
    b, a = signal.butter(2, [lo / (SR / 2), min(0.99, hi / (SR / 2))], 'band')
    return signal.lfilter(b, a, x)


def crush(x, bits=4, hold=4):
    q = 2 ** (bits - 1)
    y = np.round(x * q) / q
    if hold > 1:
        y = np.repeat(y[::hold], hold)[:len(x)]
    return y


# ------------------------------------------------------------------ buses
class Bus:
    def __init__(self):
        self.x = np.zeros((2, N))

    def add(self, t, sig, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N or len(sig) == 0:
            return
        s = sig
        if i < 0:
            s = s[-i:]
            i = 0
        j = min(N, i + len(s))
        th = (pan + 1) * math.pi / 4
        self.x[0, i:j] += s[:j - i] * gain * math.cos(th) * 1.414
        self.x[1, i:j] += s[:j - i] * gain * math.sin(th) * 1.414


music = Bus()     # dry music
echo = Bus()      # send to tempo-synced delay
sfx = Bus()       # dry effects
verb = Bus()      # send to reverb
early = Bus()     # paper-era music (gets the tape stop)


def delay(x, t_d, fb=0.4, mix=0.5, lp_fc=5000):
    """Feedback echo, unrolled into 8 taps; channels swapped for a ping-pong feel."""
    D = int(t_d * SR)
    y = np.zeros_like(x)
    for ch in range(2):
        taps = np.zeros(N)
        taps[D:] = x[ch][:-D]
        tot = np.zeros(N)
        g = mix
        for _ in range(8):
            tot += taps * g
            taps = np.concatenate([np.zeros(D), taps[:-D]])
            g *= fb
        y[ch] = lp(tot, lp_fc)
    return y[[1, 0]] * 0.9 + y * 0.1


def reverb(x, secs=2.6, damp=4000):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, N))
    for ch in range(2):
        ir = rng.normal(0, 1, n) * np.exp(-t / (secs / 5.5))
        ir = lp(ir, damp)
        ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        ir /= np.sqrt((ir ** 2).sum())
        out[ch] = signal.fftconvolve(x[ch], ir)[:N]
    return out


# ------------------------------------------------------------------ instruments
def i_pulse(bus, t, m, dur, duty=0.25, vol=0.2, pan=0.0, dec=0.18, sus=0.3, vib=0.0, slide=None):
    f = mtof(m)
    s = pulse(f, dur + 0.03, duty, f_end=mtof(slide) if slide else None, vib=vib)
    s *= env(len(s), 0.002, dec, sus, 0.03)
    bus.add(t, s, vol, pan)


def i_tri(bus, t, m, dur, vol=0.35, pan=0.0, dec=0.5, sus=0.6):
    s = tri(mtof(m), dur + 0.02)
    s *= env(len(s), 0.002, dec, sus, 0.02)
    bus.add(t, s, vol, pan)


def i_saw(bus, t, m, dur, vol=0.12, pan=0.0, cutoff=3000, detune=0.12, a=0.01, dec=0.3, sus=0.7, r=0.08):
    s = np.zeros(int((dur + r) * SR))
    for dd in (-detune, 0, detune):
        s += saw(mtof(m + dd), dur + r)[:len(s)]
    s = lp(s / 3, cutoff)
    s *= env(len(s), a, dec, sus, r)
    bus.add(t, s, vol, pan)


def i_pad(bus, t, notes, dur, vol=0.07, cutoff=1800, a=0.4, r=0.6, kind='saw'):
    for k, m in enumerate(notes):
        n = int((dur + r) * SR)
        s = np.zeros(n)
        for dd in (-0.08, 0.07):
            if kind == 'saw':
                s += saw(mtof(m + dd), dur + r)[:n]
            else:
                s += tri(mtof(m + dd), dur + r, steps=0)[:n]
        s = lp(s, cutoff)
        s *= env(n, a, 10, 1.0, r)
        bus.add(t, s, vol, pan=(k - 1) * 0.4)


def i_bell(bus, t, m, dur=1.6, vol=0.18, pan=0.0):
    f = mtof(m)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur * 0.45))
         + 0.45 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt / (dur * 0.12))
         + 0.25 * np.sin(2 * np.pi * f * 5.4 * tt) * np.exp(-tt / (dur * 0.05))
         + 0.3 * np.sin(2 * np.pi * f * 2.0 * tt) * np.exp(-tt / (dur * 0.25)))
    s *= np.minimum(1, tt / 0.002)
    bus.add(t, s * 0.5, vol, pan)


def i_sub(bus, t, m, dur, vol=0.35):
    s = sine(mtof(m), dur + 0.1)
    s *= env(len(s), 0.02, 10, 1, 0.1)
    bus.add(t, s, vol)


# drums
def d_kick(bus, t, vol=0.8, style='modern'):
    if style == 'nes':
        s = tri(180, 0.12, f_end=40, steps=16)
        s *= exp_env(len(s), 0.05)
    else:
        n = int(0.35 * SR)
        s = sine(150, 0.35, f_end=42)[:n] * exp_env(n, 0.12)
        s[:200] += np.linspace(0.6, 0, 200) * rng.uniform(-1, 1, 200)
    bus.add(t, s, vol)


def d_snare(bus, t, vol=0.4, style='modern', pan=0.0):
    if style == 'nes':
        s = nes_noise(0.14, rate=18000) * exp_env(int(0.14 * SR), 0.05)
    else:
        n = int(0.22 * SR)
        s = bp(white(0.22), 2500, 0.8) * exp_env(n, 0.07) * 1.4
        s += sine(190, 0.22)[:n] * exp_env(n, 0.04) * 0.5
    bus.add(t, s, vol, pan)


def d_hat(bus, t, vol=0.12, style='modern', pan=0.2, open_=False):
    d = 0.18 if open_ else 0.035
    if style == 'nes':
        s = nes_noise(d, rate=40000, short=True)
    else:
        s = hp(white(d), 7000)
    s *= exp_env(len(s), d / 3)
    bus.add(t, s, vol, pan)


def d_crash(bus, t, vol=0.25):
    s = hp(white(1.8), 4000) * exp_env(int(1.8 * SR), 0.5)
    bus.add(t, s, vol, 0.0)
    verb.add(t, s, vol * 0.4)


# ------------------------------------------------------------------ SFX
def s_click(t, vol=0.07, pitch=1.0, pan=-0.2):
    n = int(0.012 * SR)
    s = hp(white(0.012), 2500) * exp_env(n, 0.003)
    s += sine(900 * pitch, 0.012)[:n] * exp_env(n, 0.004) * 0.4
    sfx.add(t, s, vol, pan)


def s_key(t, vol=0.12, pan=-0.1):
    """Mechanical typewriter key."""
    n = int(0.05 * SR)
    s = bp(white(0.05), 1800 + rng.uniform(-300, 300), 1.5) * exp_env(n, 0.012)
    s += sine(120, 0.05)[:n] * exp_env(n, 0.01) * 0.6
    sfx.add(t, s, vol, pan)


def s_tick(t, vol=0.1, pitch=1.0, pan=-0.4):
    s = pulse(2200 * pitch, 0.012, 0.5) * exp_env(int(0.012 * SR), 0.004)
    sfx.add(t, s, vol, pan)


def s_blip(t, m=84, vol=0.12, dur=0.06, duty=0.25, pan=0.0, slide=None):
    s = pulse(mtof(m), dur, duty, f_end=mtof(slide) if slide else None)
    s *= env(len(s), 0.001, dur * 0.6, 0.0, 0.01)
    sfx.add(t, s, vol, pan)


def s_unlock(t, level=1, idx=0):
    base = 72 + (idx % 5)
    seq = [0, 4, 7, 12, 16] if level == 1 else [0, 7, 12, 19, 24]
    for k, iv in enumerate(seq):
        s_blip(t + k * 0.045, base + iv, vol=0.1, dur=0.09, duty=0.25, pan=0.35)
    sh = hp(white(0.5), 6000) * exp_env(int(0.5 * SR), 0.12)
    sfx.add(t + 0.2, sh * np.abs(np.sin(np.arange(len(sh)) / SR * 90)), 0.05, 0.4)
    verb.add(t, pulse(mtof(base + 24), 0.3, 0.25) * exp_env(int(0.3 * SR), 0.1), 0.05)


def s_whoosh(t, dur=0.5, f0=300, f1=6000, vol=0.18, pan=0.0, rev=False):
    n = int(dur * SR)
    x = white(dur)
    fr = np.geomspace(f0, f1, n)
    # time-varying bandpass via short block processing
    out = np.zeros(n)
    blk = 512
    for i in range(0, n, blk):
        f = fr[min(n - 1, i)]
        seg_ = x[max(0, i - 256):i + blk]
        y = bp(seg_, f, 1.2)[-min(blk, n - i):]
        out[i:i + len(y)] = y
    e = np.sin(np.linspace(0, math.pi, n)) ** 1.5
    if rev:
        e = np.linspace(0, 1, n) ** 3
    sfx.add(t, out * e * 2.0, vol, pan)
    verb.add(t, out * e, vol * 0.3)


def s_glitch(t, dur=0.18, vol=0.16):
    s = crush(white(dur) * 0.8 + pulse(rng.uniform(200, 900), dur, 0.3), bits=3, hold=12)
    s *= env(len(s), 0.001, dur, 0.5, 0.02)
    sfx.add(t, s, vol, rng.uniform(-0.5, 0.5))


def s_thud(t, vol=0.35):
    s = sine(90, 0.2, f_end=40) * exp_env(int(0.2 * SR), 0.06)
    sfx.add(t, s, vol)


def s_impact(t, vol=0.7):
    n = int(1.2 * SR)
    s = sine(80, 1.2, f_end=28) * exp_env(n, 0.35)
    s += lp(white(1.2), 1800) * exp_env(n, 0.12) * 0.6
    sfx.add(t, s, vol)
    verb.add(t, s, 0.25)


def s_zap(t, f0=1600, f1=200, dur=0.15, vol=0.12, pan=0.0):
    s = pulse(f0, dur, 0.5, f_end=f1) * exp_env(int(dur * SR), dur / 2)
    sfx.add(t, s, vol, pan)


def s_chime(t, m=84, vol=0.14, pan=0.0):
    i_bell(sfx, t, m, 1.2, vol, pan)
    i_bell(verb, t, m, 1.2, vol * 0.5, pan)


def s_stone(t, vol=0.3, pan=0.0):
    n = int(0.08 * SR)
    s = bp(white(0.08), 3200, 3) * exp_env(n, 0.012) * 2
    s += sine(1400, 0.08)[:n] * exp_env(n, 0.01) * 0.5
    sfx.add(t, s, vol, pan)
    verb.add(t, s, vol * 0.2)


def s_wind(t0, t1, vol=0.12):
    dur = t1 - t0
    n = int(dur * SR)
    x = white(dur)
    y = bp(x, 700, 0.8) * 0.6 + bp(x, 1500, 2) * 0.4
    tt = np.arange(n) / SR
    e = (0.55 + 0.45 * np.sin(tt * 1.7) * np.sin(tt * 0.6 + 1)) * np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.3)
    sfx.add(t0, y * e, vol, -0.3)
    sfx.add(t0 + 0.03, y * e, vol * 0.8, 0.3)


def s_hum(t0, t1, vol=0.05):
    dur = t1 - t0
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = sine(60, dur) * 0.6 + sine(120, dur) * 0.3 + lp(white(dur), 400) * 0.6
    e = np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.4)
    sfx.add(t0, s * e, vol)


def s_sea(t0, t1, vol=0.08):
    dur = t1 - t0
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = lp(white(dur), 900)
    swell = 0.55 + 0.45 * np.sin(tt * 2 * np.pi / 5.5) ** 2
    e = np.minimum(1, tt / 1.2) * np.minimum(1, (dur - tt) / 1.0)
    sfx.add(t0, x * swell * e, vol, -0.25)
    sfx.add(t0 + 0.05, lp(white(dur), 700) * swell * e, vol, 0.25)


def s_tape_stop(bus, t0, t1):
    """Pitch-and-speed ramp to zero on a bus between t0 and t1, silence after."""
    i0, i1 = int(t0 * SR), int(t1 * SR)
    n = i1 - i0
    rate = np.linspace(1, 0, n) ** 1.3
    pos = i0 + np.cumsum(rate)
    for ch in range(2):
        src = bus.x[ch].copy()
        bus.x[ch, i0:i1] = np.interp(pos, np.arange(N), src) * np.linspace(1, 0.2, n)
        bus.x[ch, i1:] = 0


# ------------------------------------------------------------------ harmony
CH = {
    'Am': [57, 60, 64], 'F': [53, 57, 60], 'C': [48, 52, 55], 'G': [55, 59, 62],
    'E': [52, 56, 59], 'Dm': [50, 53, 57], 'Em': [52, 55, 59],
}
PROG = [
    (4, 6, 'Am'), (6, 8, 'F'), (8, 10, 'C'), (10, 12, 'G'), (12, 13, 'Am'), (13, 14, 'E'),
    (14, 16, 'Am'),
    (16, 17, 'Dm'), (17, 18, 'E'),
    (18, 19, 'Am'), (19, 20, 'G'), (20, 21, 'F'), (21, 22, 'E'),
    (22, 23, 'Am'), (23, 24, 'F'), (24, 25, 'C'), (25, 26, 'G'), (26, 27, 'Am'), (27, 28, 'F'),
    (28, 29, 'C'), (29, 30, 'G'), (30, 31, 'F'),
    (31, 32, 'G'), (32, 33, 'Am'), (33, 34, 'G'),
    (34, 35, 'F'), (35, 36, 'G'), (36, 37, 'Em'), (37, 38, 'Am'), (38, 39, 'F'), (39, 40, 'G'),
    (40, 41, 'Am'),
    (41, 42, 'F'), (42, 43, 'C'), (43, 44, 'G'), (44, 45, 'Am'),
    (48, 50, 'F'), (50, 52, 'C'), (52, 54, 'G'), (54, 56, 'Am'), (56, 58, 'F'), (58, 60, 'C'),
]
S16 = tl.BEAT / 4
S8 = tl.BEAT / 2


def chords_in(a, b):
    return [(max(a, x), min(b, y), c) for (x, y, c) in PROG if x < b and y > a]


def arp(bus, a, b, step, octave, inst, pattern=(0, 1, 2, 1), **kw):
    for (x, y, c) in chords_in(a, b):
        notes = CH[c]
        t = x
        k = 0
        while t < y - 1e-6:
            m = notes[pattern[k % len(pattern)] % 3] + 12 * octave + 12 * (pattern[k % len(pattern)] // 3)
            inst(bus, t, m, step * 0.9, **kw)
            t += step
            k += 1


def bassline(bus, a, b, step, inst, pattern=(0, 0, 12, 0), **kw):
    for (x, y, c) in chords_in(a, b):
        root = CH[c][0] - 12
        if root > 48:
            root -= 12
        t = x
        k = 0
        while t < y - 1e-6:
            inst(bus, t, root + pattern[k % len(pattern)], step * 0.92, **kw)
            t += step
            k += 1


# ------------------------------------------------------------------ score
def score():
    B = tl.BEAT
    # --- intro (0-4): room hum, boot beep
    s_hum(0.0, 4.1, 0.09)
    s_blip(0.25, 96, 0.08, 0.08, 0.5)
    s_whoosh(3.3, 0.7, 200, 3000, 0.1, rev=True)

    # --- paper era 4-14: 1-bit arps, pulse bass, clock tick
    arp(early, 4, 14, S16, 1, i_pulse, pattern=(0, 1, 2, 3, 2, 1), duty=0.125, vol=0.15, dec=0.06, sus=0.0)
    bassline(early, 4, 14, B, i_pulse, pattern=(0, 0, 7, 0), duty=0.5, vol=0.17, dec=0.2, sus=0.2)
    t = 4.0
    while t < 14.0 - 1e-6:
        s_tick_bus(early, t, 0.1 if (round(t / S8) % 2 == 0) else 0.06)
        t += S8
    for b in range(2, 7):
        d_kick(early, b * 2.0, 0.5, 'nes')
        d_kick(early, b * 2.0 + 1.0, 0.3, 'nes')
    melody(early, [(8.0, .5, 76), (8.5, .5, 79), (9.0, 1.0, 84), (10.0, .5, 83), (10.5, .5, 79),
                   (11.0, 1.0, 74), (12.0, .5, 76), (12.5, .5, 72), (13.0, 1.0, 71)],
           i_pulse, duty=0.5, vol=0.11, dec=0.3, sus=0.4)
    s_tape_stop(early, 13.92, 14.35)

    # --- winter 14-16: wind, frozen bells, soft pad
    s_wind(14.0, 16.1, 0.22)
    i_pad(music, 14.05, [57, 64, 71], 1.9, vol=0.1, cutoff=1200, a=0.3, r=0.3, kind='tri')
    for (tt, m) in ((14.3, 88), (14.75, 83), (15.2, 84), (15.55, 79)):
        i_bell(music, tt, m, 1.0, 0.13, pan=rng.uniform(-0.6, 0.6))
        i_bell(verb, tt, m, 1.0, 0.06)

    # --- amber 16-18: NES band kicks in
    nes_drums(16, 18)
    bassline(music, 16, 18, S8, i_tri, pattern=(0, 12, 0, 12), vol=0.3, dec=0.3, sus=0.5)
    arp(music, 16, 18, S16, 1, i_pulse, pattern=(0, 1, 2, 3), duty=0.25, vol=0.06, dec=0.08, sus=0.1)

    # --- green 18-22: lead melody appears
    nes_drums(18, 22)
    bassline(music, 18, 22, S8, i_tri, pattern=(0, 12, 0, 12), vol=0.3, dec=0.3, sus=0.5)
    arp(music, 18, 22, S16, 1, i_pulse, pattern=(0, 1, 2, 3, 2, 1), duty=0.25, vol=0.05, dec=0.08, sus=0.1)
    melody(music, [(18.0, .25, 69), (18.25, .25, 72), (18.5, .5, 76), (19.0, .25, 74), (19.25, .25, 71),
                   (19.5, .5, 67), (20.0, .25, 69), (20.25, .25, 72), (20.5, .5, 77), (21.0, .25, 76),
                   (21.25, .25, 71), (21.5, .5, 68)],
           i_pulse, duty=0.25, vol=0.09, dec=0.2, sus=0.5, vib=0.004)

    # --- neon 22-31: 16-bit, echoes
    modern_drums(22, 31, hats16=True, kick_pat=(0, 2.5), vol=0.7)
    bassline(music, 22, 31, S8, i_tri, pattern=(0, 12, 0, 7), vol=0.32, dec=0.25, sus=0.5)
    arp(music, 22, 31, S16, 1, i_pulse, pattern=(0, 1, 2, 3, 4, 3, 2, 1), duty=0.5, vol=0.04, dec=0.08, sus=0.1)
    arp(echo, 22, 31, S8, 2, i_pulse, pattern=(2, 1, 0, 1), duty=0.25, vol=0.035, dec=0.1, sus=0.1)
    melody(music, [(26.0, .25, 81), (26.25, .25, 79), (26.5, .25, 76), (26.75, .25, 72), (27.0, .5, 77),
                   (27.5, .25, 76), (27.75, .25, 72), (28.0, .25, 79), (28.25, .25, 76), (28.5, .5, 72),
                   (29.0, .25, 74), (29.25, .25, 79), (29.5, .5, 83), (30.0, .5, 81), (30.5, .5, 77)],
           i_pulse, duty=0.5, vol=0.08, dec=0.2, sus=0.5, vib=0.005, echo_send=0.5)

    # --- synth build 31-34
    modern_drums(31, 33.5, hats16=True, kick_pat=(0, 1, 2, 3), vol=0.7)
    bassline(music, 31, 34, S8, i_saw, pattern=(0, 12, 0, 12), vol=0.12, cutoff=900, dec=0.2, sus=0.5)
    arp(echo, 31, 34, S16, 1, i_saw, pattern=(0, 1, 2, 3), vol=0.05, cutoff=2600, dec=0.08, sus=0.2)
    i_pad(music, 31.0, [55, 62, 67], 3.0, vol=0.04, cutoff=1500)
    # snare roll + riser into the drop
    t = 32.0
    k = 0
    while t < 34.0 - 1e-6:
        step = S8 if t < 33.0 else (S16 if t < 33.5 else S16 / 2)
        d_snare(music, t, 0.12 + 0.2 * (t - 32) / 2, pan=0.1)
        t += step
    s_whoosh(32.2, 1.8, 200, 9000, 0.14, rev=True)
    riser = saw(110, 2.0, f_end=880)
    music.add(32.0, lp(riser, 3000) * np.linspace(0, 1, len(riser)) ** 2, 0.14)

    # --- drop 34-41
    d_crash(music, 34.0, 0.35)
    modern_drums(34, 41, hats16=True, kick_pat=(0, 1, 2, 3), snare=(1, 3), vol=0.85)
    bassline(music, 34, 41, S8, i_saw, pattern=(0, 12, 0, 12), vol=0.15, cutoff=1200, dec=0.15, sus=0.5)
    bassline(music, 34, 41, B, i_sub, pattern=(0,), vol=0.22)
    for (x, y, c) in chords_in(34, 41):
        i_pad(music, x, [n + 12 for n in CH[c]], y - x, vol=0.035, cutoff=2600, a=0.05, r=0.2)
    arp(echo, 34, 41, S16, 2, i_pulse, pattern=(0, 1, 2, 1), duty=0.25, vol=0.03, dec=0.06, sus=0.1)
    lead = [(34.0, .25, 81), (34.25, .25, 84), (34.5, .25, 81), (34.75, .25, 79), (35.0, .5, 83),
            (35.5, .25, 86), (35.75, .25, 83), (36.0, .25, 79), (36.25, .25, 83), (36.5, .5, 88),
            (37.0, .25, 84), (37.25, .25, 83), (37.5, .5, 81), (38.0, .25, 81), (38.25, .25, 84),
            (38.5, .5, 89), (39.0, .25, 86), (39.25, .25, 83), (39.5, .5, 79), (40.0, 1.0, 81)]
    melody(music, lead, i_saw, vol=0.075, cutoff=4200, dec=0.2, sus=0.6, echo_send=0.4)
    melody(music, [(t_, d_, m_ - 12) for (t_, d_, m_) in lead], i_pulse, duty=0.5, vol=0.05, dec=0.2, sus=0.5)

    # --- clean 41-45: lighter, plucky
    for tt in np.arange(41.0, 45.0, B):
        d_kick(music, tt, 0.45 if (tt - 41) % 1.0 < 1e-6 else 0.25)
        d_hat(music, tt + S8, 0.06)
    bassline(music, 41, 45, B, i_tri, pattern=(0, 0, 7, 0), vol=0.25, dec=0.3, sus=0.4)
    arp(echo, 41, 45, S8, 2, i_pulse, pattern=(0, 2, 1, 2), duty=0.125, vol=0.035, dec=0.05, sus=0.0)
    melody(music, [(41.0, .5, 84), (41.5, .5, 81), (42.0, .25, 79), (42.25, .25, 84), (42.5, .5, 88),
                   (43.0, .5, 86), (43.5, .5, 83), (44.0, .25, 81), (44.25, .25, 84), (44.5, .5, 88)],
           i_pulse, duty=0.25, vol=0.07, dec=0.12, sus=0.1, echo_send=0.4)

    # --- question 45-48: breath
    i_pad(music, 45.0, [45, 52, 57, 64], 3.0, vol=0.08, cutoff=900, a=0.4, r=0.5, kind='tri')
    s_whoosh(47.25, 0.75, 300, 8000, 0.16, rev=True)

    # --- dusk 48-60: bells, warm pad, sea
    s_sea(47.9, 60.0, 0.12)
    for (x, y, c) in chords_in(48, 60):
        notes = CH[c]
        i_pad(music, x, [n for n in notes] + [notes[0] + 12], y - x + (0.8 if y >= 60 else 0),
              vol=0.06, cutoff=1500, a=0.6, r=1.0)
        i_sub(music, x, notes[0] - 24 if notes[0] >= 48 else notes[0] - 12, y - x, 0.14)
        # slow bell arpeggio
        pat = [0, 1, 2, 3, 2, 1, 2, 3]
        t = x
        k = 0
        while t < y - 1e-6 and t < 59.0:
            m = notes[pat[k] % 3] + 24 + (12 if pat[k] == 3 else 0)
            i_bell(music, t, m, 1.4, 0.055, pan=0.3 * math.sin(k))
            i_bell(verb, t, m, 1.4, 0.03)
            t += S8
            k += 1
    for (tt, d_, m) in ((48.5, 1.0, 81), (49.5, .5, 84), (50.5, 1.0, 79), (51.5, .5, 76), (52.5, 1.0, 83),
                        (53.5, .5, 86), (54.5, 1.0, 84), (55.5, .5, 81)):
        i_bell(music, tt, m, 2.0, 0.1)
        i_bell(verb, tt, m, 2.0, 0.06)
    # end card: resolved Cmaj9 chord
    for m in (60, 64, 67, 71, 74, 79):
        i_bell(music, tl.END_T0, m, 3.5, 0.05)
        i_bell(verb, tl.END_T0, m, 3.5, 0.06)
    for m in (72, 76, 79, 84):
        i_bell(music, 58.0, m, 2.2, 0.04)
        i_bell(verb, 58.0, m, 2.2, 0.05)


def s_tick_bus(bus, t, vol):
    s = hp(white(0.02), 5000) * exp_env(int(0.02 * SR), 0.004)
    bus.add(t, s, vol, 0.3)


def melody(bus, notes, inst, echo_send=0.0, **kw):
    for (t, d, m) in notes:
        inst(bus, t, m, d, **kw)
        if echo_send:
            inst(echo, t, m, d, **{**kw, 'vol': kw.get('vol', 0.1) * echo_send})


def nes_drums(a, b):
    B = tl.BEAT
    t = a
    k = 0
    while t < b - 1e-6:
        if k % 4 in (0, 2):
            d_kick(music, t, 0.55, 'nes')
        if k % 4 in (1, 3):
            d_snare(music, t, 0.22, 'nes')
        d_hat(music, t + S8, 0.05, 'nes')
        t += B
        k += 1


def modern_drums(a, b, hats16=False, kick_pat=(0, 2), snare=(1, 3), vol=0.7):
    B = tl.BEAT
    t = a
    k = 0
    while t < b - 1e-6:
        beat = k % 4
        if any(abs(beat - kp) < 1e-6 for kp in kick_pat):
            d_kick(music, t, vol)
        if 2.5 in kick_pat and beat == 2:
            d_kick(music, t + B / 2, vol * 0.7)
        if beat in snare:
            d_snare(music, t, 0.3 * vol / 0.7)
            verb.add(t, hp(white(0.1), 2000) * exp_env(int(0.1 * SR), 0.04), 0.05)
        for h in range(4 if hats16 else 2):
            d_hat(music, t + h * (B / (4 if hats16 else 2)), 0.05 if h % 2 else 0.08, pan=0.25)
        t += B
        k += 1


# ------------------------------------------------------------------ SFX from the timeline
# ------------------------------------------------------------------ battle SFX
def s_step(t, vol=0.08):
    n = int(0.05 * SR)
    s = lp(white(0.05), 700) * exp_env(n, 0.012) + sine(70, 0.05)[:n] * exp_env(n, 0.015) * 0.6
    sfx.add(t, s, vol, -0.3)


def s_hit(t, vol=0.25, crit=False):
    n = int(0.18 * SR)
    s = crush(white(0.18), 4, 6) * exp_env(n, 0.04) * 0.8
    s += sine(160, 0.18, f_end=60)[:n] * exp_env(n, 0.05)
    sfx.add(t, s, vol, 0.2)
    if crit:
        s_blip(t + 0.02, 96, 0.08, 0.12, 0.5, slide=84)
        verb.add(t, s, vol * 0.3)


def s_hurt(t, vol=0.14):
    s = pulse(420, 0.22, 0.5, f_end=90) * env(int(0.22 * SR), 0.001, 0.2, 0.3, 0.03)
    sfx.add(t, crush(s, 4, 4), vol, -0.3)


def s_burst(t, vol=0.22, big=False):
    d = 0.7 if big else 0.45
    n = int(d * SR)
    s = crush(white(d), 3, 10 if big else 6) * exp_env(n, d / 3.5)
    s += sine(120, d, f_end=40)[:n] * exp_env(n, d / 4) * 0.7
    sfx.add(t, s, vol, 0.25)
    verb.add(t, s, vol * 0.25)
    for k in range(4):
        s_blip(t + 0.05 + k * 0.04, 84 - k * 5, 0.04, 0.05, 0.5, pan=0.4)


def s_levelup(t):
    for k, m in enumerate((72, 76, 79, 84)):
        s_blip(t + k * 0.055, m, 0.07, 0.11, 0.125, pan=-0.3)


def s_evolve(t0, dur):
    """Pokemon-style evolution: two pitches alternating ever faster, then a chord."""
    t = t0
    k = 0
    while t < t0 + dur:
        f = (t - t0) / dur
        per = 0.16 * (1 - f) + 0.03
        s_blip(t, 79 + 12 * f + (5 if k % 2 else 0), 0.06, per * 0.9, 0.5, pan=0.0)
        t += per
        k += 1
    for m in (72, 79, 84, 88, 91):
        s_blip(t0 + dur, m, 0.05, 0.5, 0.25)
        i_bell(verb, t0 + dur, m, 1.5, 0.05)
    s_whoosh(t0, dur, 300, 8000, 0.08, rev=True)


def s_roar(t, dur=0.6, vol=0.2):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = lp(white(dur), 500) * (0.6 + 0.4 * np.sin(tt * 60)) + saw(70, dur, f_end=45)[:n] * 0.5
    s *= env(n, 0.05, dur, 0.6, 0.15)
    sfx.add(t, crush(s, 5, 3), vol, 0.35)
    verb.add(t, s, vol * 0.3)


def s_shatter(t, vol=0.15):
    for k in range(10):
        s_blip(t + k * 0.012, 96 + rng.integers(-5, 8), 0.04, 0.05, 0.5, pan=rng.uniform(-0.5, 0.5))
    sfx.add(t, hp(white(0.3), 5000) * exp_env(int(0.3 * SR), 0.08), vol)


def s_heal(t, vol=0.06):
    for k, m in enumerate((72, 79, 84, 88, 91, 96)):
        s_blip(t + k * 0.05, m, vol, 0.08, 0.125, pan=-0.2)


def s_boing(t, vol=0.07):
    s_blip(t, 60, vol, 0.18, 0.5, slide=84)


def s_laser(t, dur=0.22, vol=0.1):
    s = pulse(1200, dur, 0.25, f_end=300) * env(int(dur * SR), 0.001, dur, 0.6, 0.02)
    sfx.add(t, s, vol, 0.3)


def s_fanfare(t, notes=(72, 76, 79, 84, 79, 84), step=0.08, vol=0.08):
    for k, m in enumerate(notes):
        s_blip(t + k * step, m, vol, step * 1.6 if k < len(notes) - 1 else 0.5, 0.25, pan=0.1)


def sfx_from_timeline():
    # intro typing
    for k in range(len(tl.INTRO_Q)):
        s_key(tl.INTRO_Q_T + k / tl.INTRO_Q_CPS, 0.3)
    for k in range(0, len(tl.INTRO_SUB), 2):
        s_click(tl.INTRO_SUB_T + k / tl.INTRO_SUB_CPS, 0.09)
    s_whoosh(3.7, 0.4, 800, 5000, 0.08)

    # log typing
    for sc in tl.SCENES:
        for (li, ts, n, cps) in tl.text_events(sc):
            for k in range(0, n, 1 if li == 0 else 2):
                if sc['era'] == 'paper':
                    s_key(ts + k / cps, 0.04 if li == 0 else 0.025)
                else:
                    s_click(ts + k / cps, 0.035 if li == 0 else 0.02, pitch=1.0 + 0.2 * li)
    # year odometer
    for (te, a, b) in tl.year_events():
        steps = min(14, abs(b - a))
        for k in range(steps):
            f = (k + 1) / steps
            s_tick(te + tl.YEAR_ROLL * (1 - (1 - f) ** (1 / 3)) * 0.9, 0.05, 1.0 + 0.3 * f)
    # walking into each room
    for sc in tl.SCENES[1:]:
        for k in range(3):
            s_step(sc['t0'] + 0.03 + k * 0.1)
    # loot and levels
    unlocks = tl.unlock_events()
    for i, (t, name, lvl) in enumerate(unlocks):
        s_unlock(t, lvl, i)
        s_blip(t + 0.42, 96, 0.06, 0.05, 0.5, pan=0.5)
    for w in tl.wins()[1:]:
        if all(abs(w - t) > 0.3 for (t, _, _) in unlocks):
            s_levelup(w)
    for (te, name) in tl.EVOLVE:
        s_evolve(te, tl.EVOLVE_DUR)

    # era transitions
    s_whoosh(13.85, 0.5, 4000, 400, 0.12)
    s_zap(15.9, 800, 60, 0.12, 0.12)
    s_thud(16.0, 0.4)
    sfx.add(16.0, sine(15600, 0.5) * exp_env(int(0.5 * SR), 0.15), 0.015)
    s_glitch(17.95, 0.2)
    s_whoosh(22.8, 0.6, 400, 9000, 0.16)
    s_glitch(30.95, 0.16, 0.18)
    s_impact(34.0, 0.75)
    s_whoosh(40.85, 0.3, 2000, 9000, 0.12)
    s_thud(41.0, 0.3)

    T = {sc['id']: sc['t0'] for sc in tl.SCENES}
    # 1943: the neuron fires and hatches; the gate opens
    t0 = T['neuron']
    s_blip(t0 + 0.75, 79, 0.06, 0.05)
    s_blip(t0 + 0.83, 83, 0.06, 0.05)
    s_zap(t0 + 1.1, 400, 1800, 0.12, 0.1)
    s_fanfare(t0 + 1.2, (72, 79, 84), 0.07, 0.07)
    s_roar(t0 + 1.35, 0.5, 0.08)
    # 1950: the mimic
    t0 = T['turing']
    for d in (0.3, 0.55):
        s_blip(t0 + d, 84, 0.06, 0.2, 0.5, slide=91)
    for k in range(6):
        s_click(t0 + 0.5 + k * 0.07, 0.08, pitch=0.5)
    s_roar(t0 + 0.95, 0.35, 0.16)
    s_hurt(t0 + 1.05)
    s_hit(t0 + 1.26)
    s_burst(t0 + 1.34)
    # 1956: naming the field
    t0 = T['dartmouth']
    for k in range(len('ARTIFICIAL INTELLIGENCE')):
        s_blip(t0 + 0.15 + k * 0.05, 88 + (k % 3) * 2, 0.04, 0.03, 0.5, pan=0.3)
    s_fanfare(t0 + 1.4, (79, 84, 91), 0.06, 0.07)
    # 1958: the tangled swarm
    t0 = T['perceptron']
    for k in range(8):
        s_blip(t0 + 0.25 + k * 0.03, 60 + (k % 4) * 3, 0.03, 0.05, 0.5, slide=72)
    for k, d in enumerate((0.55, 0.72, 0.88, 1.03, 1.18)):
        s_blip(t0 + d, 72 + k * 2, 0.07, 0.05, 0.25)
    s_laser(t0 + 1.22)
    s_burst(t0 + 1.28)
    # 1966: ELIZA's dialogue
    t0 = T['eliza']
    for i, (line, who) in enumerate((('HUMAN: Men are all alike.', 0), ('AI: IN WHAT WAY?', 1),
                                     ("HUMAN: They're always bugging us.", 0),
                                     ('AI: CAN YOU THINK OF A SPECIFIC EXAMPLE?', 1))):
        st = t0 + 0.3 + 0.25 * i
        for k in range(0, len(line), 2):
            s_blip(st + k / 70, 79 if who else 67, 0.025, 0.02, 0.5, pan=0.3 if who else -0.2)
    # 1973: the AI winter
    t0 = T['winter']
    s_roar(t0 + 0.05, 0.5, 0.2)
    s_whoosh(t0 + 0.45, 0.4, 3000, 600, 0.14)
    s_hurt(t0 + 0.55, 0.16)
    s_shatter(t0 + 0.75, 0.08)
    # 1986: thaw, miss, error flows back, critical hit
    t0 = T['backprop']
    s_shatter(t0 + 0.05)
    s_heal(t0 + 0.2)
    s_whoosh(t0 + 0.45, 0.25, 800, 3000, 0.06)
    s_zap(t0 + 0.68, 200, 180, 0.2, 0.08)
    for k in range(6):
        s_blip(t0 + 0.72 + k * 0.045, 84 - k * 3, 0.04, 0.04, 0.5)
    for k in range(3):
        s_blip(t0 + 0.9 + k * 0.06, 76 + k * 3, 0.05, 0.05, 0.25)
    s_hit(t0 + 1.1, 0.3, crit=True)
    s_burst(t0 + 1.2)
    # 1997: the chess king
    t0 = T['deepblue']
    for d in (0.42, 0.78, 1.06):
        s_boing(t0 + d)
    s_hit(t0 + 0.55)
    s_hit(t0 + 0.9)
    s_zap(t0 + 0.86, 300, 900, 0.18, 0.08)
    s_hurt(t0 + 0.9)
    s_fanfare(t0 + 1.1, (72, 79, 84, 88), 0.07, 0.09)
    s_thud(t0 + 1.3, 0.35)
    s_burst(t0 + 1.36, big=True)
    # 1998: the scrawl wraith
    t0 = T['lenet']
    w = sine(440, 0.5, f_end=330) * (0.5 + 0.5 * np.sin(np.arange(int(0.5 * SR)) / SR * 40))
    sfx.add(t0 + 0.02, w * env(len(w), 0.1, 0.5, 0.5, 0.1), 0.05, 0.3)
    for k in range(18):
        s_blip(t0 + 0.35 + k * 0.03, 84 + (k * 5) % 12, 0.025, 0.02, 0.5)
    s_blip(t0 + 1.02, 81, 0.09, 0.08, 0.25)
    s_blip(t0 + 1.1, 88, 0.09, 0.12, 0.25)
    s_burst(t0 + 1.2)
    # 2009: the image horde
    t0 = T['imagenet']
    for k in range(40):
        s_click(t0 + k * 0.013, 0.03, pitch=1.5 + rng.random())
    for d in (0.35, 0.55, 0.8, 1.0):
        s_blip(t0 + d, 91, 0.04, 0.04, 0.5, pan=0.4)
    s_blip(t0 + 0.45, 72, 0.08, 0.08, 0.5)
    s_blip(t0 + 0.53, 67, 0.08, 0.12, 0.5)
    # 2012: GPUs, evolution, the beam
    t0 = T['alexnet']
    s_thud(t0 + 0.28, 0.25)
    s_thud(t0 + 0.36, 0.25)
    s_heal(t0 + 0.3, 0.05)
    s_laser(t0 + 0.98, 0.25, 0.14)
    s_burst(t0 + 1.05, 0.28, big=True)
    s_blip(t0 + 1.15, 60, 0.05, 0.3, 0.5, slide=72)
    s_blip(t0 + 1.18, 55, 0.05, 0.3, 0.5, slide=79)
    # 2014: the doppelganger
    t0 = T['gan']
    for k, r in enumerate((0.3, 0.55, 0.8, 1.05, 1.3)):
        s_whoosh(t0 + r - 0.18, 0.18, 800, 3000, 0.04, pan=-0.4)
        if k < 4:
            s_blip(t0 + r + 0.02, 55, 0.05, 0.08, 0.5)
        else:
            s_chime(t0 + r + 0.02, 88, 0.08)
    s_burst(t0 + 1.36)
    # 2016: the go dragon
    t0 = T['alphago']
    s_roar(t0 + 0.05, 0.4, 0.12)
    s_stone(t0 + 0.42, 0.2)
    s_hurt(t0 + 0.55)
    s_whoosh(t0 + 0.85, 0.23, 600, 3000, 0.06)
    s_stone(t0 + 1.08, 0.4)
    i_bell(verb, t0 + 1.08, 57, 2.5, 0.12)
    i_bell(sfx, t0 + 1.08, 57, 2.5, 0.07)
    for k in range(14):
        s_stone(t0 + 1.2 + k * 0.03, 0.08, pan=rng.uniform(-0.5, 0.5))
    # 2017: attention
    t0 = T['transformer']
    for k in range(10):
        s_blip(t0 + 0.85 + 0.025 * k, 72 + (k % 5) * 3, 0.03, 0.12, 0.25, slide=84 + (k % 5) * 3)
    s_burst(t0 + 1.32)
    # 2020: parameters and the protein serpent
    t0 = T['gpt3']
    s_whoosh(t0, 1.0, 200, 6000, 0.08, rev=True)
    for k in range(24):
        s_click(t0 + 0.1 + k * 0.032, 0.03, pitch=2.0)
    t0 = T['alphafold']
    s_blip(t0 + 0.3, 60, 0.04, 0.7, 0.5, slide=84)
    s_chime(t0 + 1.0, 88, 0.08)
    s_burst(t0 + 1.2)
    # 2022: the world joins; the noise beast is purified
    t0 = T['chatgpt']
    crowd = lp(white(0.9), 2500) * np.sin(np.linspace(0, math.pi, int(0.9 * SR)))
    sfx.add(t0 + 0.2, crowd, 0.06, 0.1)
    for k in range(10):
        s_blip(t0 + 0.55 + k * 0.03, 88 + (k % 3) * 4, 0.03, 0.04, 0.5)
    t0 = T['diffusion']
    s_roar(t0 + 0.1, 0.35, 0.08)
    for k in range(17):
        s_key(t0 + 0.05 + k * 0.021, 0.04)
    hiss = hp(white(1.0), 3000) * np.linspace(1, 0, int(1.0 * SR)) ** 1.5
    sfx.add(t0 + 0.45, hiss, 0.05, 0.2)
    s_chime(t0 + 1.42, 91, 0.1)
    # 2023: rivals race past; 2024: the labyrinth
    t0 = T['frontier']
    for k in range(18):
        s_step(t0 + k * 0.075, 0.05)
    s_blip(t0 + 0.1, 76, 0.06, 0.08, 0.25)
    s_blip(t0 + 0.18, 79, 0.06, 0.12, 0.25)
    t0 = T['reasoning']
    for k in range(8):
        s_tick(t0 + 0.1 + k * 0.09, 0.05, 0.8 if k % 2 else 1.1)
    s_blip(t0 + 0.82, 88, 0.08, 0.1, 0.25)
    for k, m in enumerate((72, 76, 79, 84, 88)):
        s_blip(t0 + 0.85 + k * 0.05, m, 0.05, 0.06, 0.25)
    s_chime(t0 + 1.3, 84, 0.07)
    s_chime(t0 + 1.38, 91, 0.07)
    # 2025-26: the bug swarm
    t0 = T['agents']
    for k in range(50):
        s_key(t0 + 0.35 + k * 0.06 + rng.uniform(0, 0.015), 0.025, pan=0.2)
    for d in (0.75, 1.45, 2.3, 3.05):
        s_blip(t0 + d, 88, 0.06, 0.06, 0.25)
    for (ta, tz) in ((0.55, 0.95), (0.7, 1.2), (0.85, 1.5), (1.0, 1.8), (1.15, 2.1), (1.3, 2.4)):
        s_laser(t0 + tz - 0.15, 0.12, 0.06)
        s_burst(t0 + tz, 0.1)
    s_click(t0 + 2.25, 0.2, pitch=0.6)
    s_chime(t0 + 2.7, 88, 0.07)
    s_fanfare(t0 + 3.2, (72, 76, 79, 84, 88, 91), 0.07, 0.09)
    s_whoosh(t0 + 3.65, 0.3, 3000, 500, 0.06)

    # the closing question
    for k in range(len(tl.INTRO_Q)):
        s_key(tl.Q_LINE1_T + k / tl.Q_LINE1_CPS, 0.1)
    for i in range(7):
        s_blip(tl.Q_FORMS_T + i * tl.Q_FORM_STEP, [60, 64, 67, 72, 76, 79, 84][i], 0.08, 0.12, 0.25,
               pan=-0.6 + 0.2 * i)
    scale = [72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96, 98, 100, 103, 105]
    for i in range(len(tl.SKILLS)):
        s_blip(tl.Q_ICONS_T + i * tl.Q_ICON_STEP, scale[i], 0.045, 0.05, 0.125, pan=-0.6 + 1.2 * i / 14)
    for k in range(len(tl.Q_LINE2)):
        s_key(tl.Q_LINE2_T + k / tl.Q_LINE2_CPS, 0.08, pan=0.1)

    # the evening calm: Lotus AI Lab on Yunagi.Cloud
    brush = bp(white(0.5), 1200, 0.8) * np.sin(np.linspace(0, math.pi, int(0.5 * SR)))
    sfx.add(48.45, brush, 0.07, -0.2)
    for k in range(12):
        s_click(48.8 + k / 30, 0.03)
    for i, tt in enumerate(tl.CARD_TIMES):
        s_chime(tt, [79, 84, 88][i], 0.08)
        for k in range(5):
            s_blip(tt + 0.05 + k * 0.035, 91 + k * 2, 0.025, 0.04, 0.125, pan=0.3)
    for i in range(6):
        s_blip(tl.MAP_T + 0.4 + i * 0.12, 96, 0.04, 0.03, 0.5, pan=-0.6 + 0.24 * i)
    s_chime(tl.END_T0, 84, 0.08)


# ------------------------------------------------------------------ mix
def limit(x, ceiling=0.89, look=0.005, release=0.08):
    """Look-ahead brick-wall limiter."""
    L = int(look * SR)
    peak = np.max(np.abs(x), axis=0)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    # hold the minimum gain over the look-ahead window, then smooth the release
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(need, size=2 * L + 1)
    a = math.exp(-1 / (release * SR))
    g = signal.lfilter([1 - a], [1, -a], g - 1) + 1
    g = np.minimum(g, minimum_filter1d(need, size=2 * L + 1))
    g = np.concatenate([g[L:], np.full(L, g[-1])])
    y = x * g
    return np.clip(y, -ceiling, ceiling)


def mixdown():
    score()
    sfx_from_timeline()
    ech = delay(echo.x, tl.BEAT * 0.75, fb=0.45, mix=0.8)
    rev_src = verb.x + 0.15 * music.x + 0.08 * early.x + 0.25 * ech
    rev = reverb(rev_src, 2.8)
    early_x = crush(early.x[0], 6, 2)[None, :].repeat(2, 0) * 0.5 + early.x * 0.5
    mix = music.x + early_x + ech + sfx.x + rev * 0.5
    # gentle glue compressor + limiter
    mix = hp(mix, 25)
    env_ = np.max(np.abs(mix), axis=0)
    env_ = signal.lfilter([0.002], [1, -0.998], env_)
    gain = np.minimum(1.0, 0.5 / np.maximum(env_, 1e-6)) ** 0.5
    mix *= gain
    mix = limit(mix / np.max(np.abs(mix)) * 1.6, ceiling=0.89)
    # fades
    fi = int(0.05 * SR)
    mix[:, :fi] *= np.linspace(0, 1, fi)
    fo = int(0.9 * SR)
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
    return mix


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'score.wav'
    mix = mixdown()
    wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))
    print('wrote', out, mix.shape, 'peak', np.max(np.abs(mix)))


if __name__ == '__main__':
    main()
