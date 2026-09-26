"""Intro terminal, the closing question and the Yunagi.Cloud sequence."""
import math
import os
import numpy as np

import gfx
from gfx import W, H, hexc, seg, ease_out, ease_in, ease_io, ease_back, clamp01, mix
import pixfont as pf
import timeline as tl
import hud
import scenes

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ intro
def intro(c, P, t):
    q = tl.INTRO_Q
    n = int((t - tl.INTRO_Q_T) * tl.INTRO_Q_CPS)
    n = max(0, min(len(q), n))
    x = 240 - pf.text_width(q, bold=True) * 2 // 2
    y = 116
    c.text(q, x, y, P['ink'], bold=True, scale=2, n=n)
    w = pf.text_width(q[:n], bold=True) * 2 if n else 0
    blink = (int(t * 2.2) % 2 == 0) or (0 < n < len(q))
    if blink:
        c.rect(x + w + (3 if n else 0), y, 9, 14, P['acc'])
    k = int((t - tl.INTRO_SUB_T) * tl.INTRO_SUB_CPS)
    if k > 0:
        c.text(tl.INTRO_SUB, 240, 142, P['sub'], n=k, align='center')
    # boot line
    if t < 0.5:
        c.text('READY.', 16, 16, P['dim'])


# ------------------------------------------------------------------ question
def q_layout(i):
    n = len(tl.SKILLS)
    pitch = 28
    x0 = 240 - (n * pitch - 2) // 2
    return x0 + i * pitch, 108


def question(c, P, t):
    u = t - tl.QUESTION_T0
    # line 1
    q = tl.INTRO_Q
    n = int((t - tl.Q_LINE1_T) * tl.Q_LINE1_CPS)
    n = max(0, min(len(q), n))
    x = 240 - pf.text_width(q, bold=True) * 2 // 2
    c.text(q, x, 72, P['ink'], bold=True, scale=2, n=n)
    if n < len(q) and n > 0:
        c.rect(x + pf.text_width(q[:n], bold=True) * 2 + 3, 72, 9, 14, P['acc'])
    # icons row
    pops = [tl.Q_ICONS_T + i * tl.Q_ICON_STEP for i in range(len(tl.SKILLS))]
    if t >= tl.Q_ICONS_T - 0.3:
        hud.draw_hotbar(c, P, t, 'clean', layout=q_layout, scale=2, pop_times=pops)
        for i, name in enumerate(tl.SKILLS):
            if t >= pops[i] + 0.05:
                x, y = q_layout(i)
                c.tiny(name, x + 13, y + 31, P['sub'], align='center',
                       alpha=seg(t, pops[i], pops[i] + 0.1))
    last = pops[-1] + 0.15
    if t > last:
        f = seg(t, last, last + 0.25)
        c.tiny('ALL %d SKILLS UNLOCKED' % len(tl.SKILLS), 240, 150, P['acc'], align='center', alpha=f)
    # line 2
    k = int((t - tl.Q_LINE2_T) * tl.Q_LINE2_CPS)
    if k > 0:
        L2 = tl.Q_LINE2
        x2 = 240 - pf.text_width(L2) * 2 // 2
        c.text(L2, x2, 176, P['acc'], scale=2, n=k)
        if k < len(L2) or int(t * 2.5) % 2 == 0:
            c.rect(x2 + pf.text_width(L2[:min(k, len(L2))]) * 2 + 3, 176, 9, 14, P['acc'])


# ------------------------------------------------------------------ dusk sea
_rng = np.random.default_rng(48)
HORIZON = 168
SUN_X, SUN_Y, SUN_R = 356, 168, 17
_STAR = np.stack([_rng.uniform(0, W, 120), _rng.uniform(0, 110, 120),
                  _rng.uniform(0, 6.28, 120), _rng.uniform(0.5, 2.5, 120)], 1)
_xs = np.arange(W)
RIDGE_FAR = HORIZON - (10 + 16 * np.clip(np.sin(_xs / 60 + 0.7), 0, None) + 5 * np.sin(_xs / 17)
                       + 3 * np.sin(_xs / 7.3)) * np.clip((300 - _xs) / 120, 0, 1)
RIDGE_NEAR = HORIZON - (4 + 12 * np.clip(np.sin(_xs / 38 + 2.1), 0, None) + 3 * np.sin(_xs / 11)) \
    * np.clip((220 - _xs) / 90, 0, 1)
_SHIM = _rng.uniform(0, 6.28, (H, 8))


def dusk_bg(c, P, t):
    sky = [hexc('#0b0d22'), hexc('#1a1638'), hexc('#3a1c44'), hexc('#6e2640'),
           hexc('#a8382e'), hexc('#d9612f')]
    c.vgrad(sky, 0, HORIZON)
    for (x, y, ph, sp) in _STAR:
        a = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * sp + ph))
        a *= clamp01(1 - y / 110)
        c.pset(x, y, P['ink'], a)
    # sun
    c.disc(SUN_X, SUN_Y, SUN_R + 3, hexc('#c2452c'), 0.5)
    c.disc(SUN_X, SUN_Y, SUN_R, hexc('#e2502e'))
    c.disc(SUN_X - 3, SUN_Y - 3, SUN_R - 7, hexc('#f07a45'))
    # ridges (the farther shore)
    for x in range(W):
        yf = int(RIDGE_FAR[x])
        if yf < HORIZON:
            c.a[yf:HORIZON, x] = hexc('#3a2040')
        yn = int(RIDGE_NEAR[x])
        if yn < HORIZON:
            c.a[yn:HORIZON, x] = hexc('#22162c')
    # mist
    for k, (y0, sp, a) in enumerate(((HORIZON - 14, 6, 0.3), (HORIZON - 6, -4, 0.25))):
        for x in range(0, W, 2):
            yy = y0 + 2 * math.sin(x / 30 + t * 0.4 + k)
            if (x + int(t * sp)) % 90 < 60:
                c.rect(x, yy, 2, 2, hexc('#c98a80'), a)
    # sea
    c.vgrad([hexc('#2a1a34'), hexc('#150f22'), hexc('#0b0916')], HORIZON, H)
    c.a[HORIZON] = hexc('#e07048')
    for y in range(HORIZON + 2, H, 2):
        d = (y - HORIZON) / (H - HORIZON)
        # sun glitter column
        wcol = SUN_R * (1.0 + d * 1.6)
        for k in range(3):
            ph = _SHIM[y, k] + t * (0.8 + k * 0.3)
            x0 = SUN_X + math.sin(ph) * wcol * 0.8
            L = 3 + 8 * (1 - d) * (0.5 + 0.5 * math.sin(ph * 1.7))
            col = hexc('#f0a060') if d < 0.3 else hexc('#c2452c')
            c.rect(x0 - L / 2, y, L, 1, col, 1 - d * 0.8)
        # sky reflection streaks
        if y % 6 == 0:
            ph = _SHIM[y, 5] + t * 0.3
            x0 = (_SHIM[y, 6] * 70 + t * 3) % W
            c.rect(x0, y, 10 + 8 * math.sin(ph), 1, hexc('#3e2a48'))
    # ridge reflection
    for x in range(0, 300, 1):
        h = int((HORIZON - RIDGE_FAR[x]) * 0.5)
        if h > 0:
            c.rect(x, HORIZON + 1, 1, h, hexc('#1c1226'), 0.6)
    # boat
    bx = 150 + t * 3.2
    by = HORIZON + 5
    boat = ['....#....', '....##...', '....###..', '....####.', '#########', '.#######.']
    c.sprite(boat, bx, by - 6, {'#': hexc('#0b0916')})
    c.rect(bx + 1, by + 1, 8, 1, hexc('#2a1a34'))


def dusk(c, P, t):
    dusk_bg(c, P, t)
    c.tiny('BEAUFORT 0 · CALM', 16, 259, P['dim'])
    c.tiny('52 21N 0 31E', 464, 259, P['dim'], align='right')


# ------------------------------------------------------------------ Yunagi overlay
def _panel(c, x, y, w, h, P, alpha=1.0):
    c.rect_blend(x, y, w, h, hexc('#110e16'), 0.82 * alpha)
    c.frame(x, y, w, h, hexc('#4a4250'), alpha)
    c.brackets(x - 1, y - 1, w + 2, h + 2, P['acc'], n=5, alpha=alpha)


CARDS = [
    ('雲', 'COMPUTE', 'VPS · VDS · Dedicated', 'from', '$4.20/mo'),
    ('名', 'DOMAINS', '312 TLDs · SSL', '.com', '$10.20/yr'),
    ('画', 'AI INFERENCE', 'Lotus Diffusion-1', 'per image', '$0.012'),
]

_MAP = [l.rstrip('\n') for l in open(os.path.join(HERE, 'worldmap.txt')) if not l.startswith('#')]
_MAP = np.array([[ch == '#' for ch in r] for r in _MAP], bool)
MAP_X, MAP_Y, MAP_P = 48, 88, 4
METROS = [('LHR-1', 51.5, -0.1), ('JFK-1', 40.6, -73.8), ('LAX-1', 33.9, -118.4),
          ('HND-1', 35.5, 139.8), ('SEL-1', 37.5, 127.0), ('HKG-1', 22.3, 114.2)]
LABEL_OFF = {'LHR-1': (4, -24), 'JFK-1': (5, -8), 'LAX-1': (-5, 2), 'HND-1': (6, -22),
             'SEL-1': (-5, -26), 'HKG-1': (-5, 3)}
KANJI = {'LHR-1': '倫敦', 'JFK-1': '紐育', 'LAX-1': '羅府', 'HND-1': '東京', 'SEL-1': 'ソウル',
         'HKG-1': '香港'}


def metro_xy(lat, lon):
    col = ((lon + 30) % 360) / 3.75
    row = (72 - lat) / (128 / 31)
    return MAP_X + col * MAP_P + 1, MAP_Y + row * MAP_P + 1


def _ring_segments():
    pts = [metro_xy(la, lo) for (_, la, lo) in METROS]
    W_MAP = 96 * MAP_P
    segs = []
    order = list(range(6)) + [0]
    for a, b in zip(order, order[1:]):
        (x0, y0), (x1, y1) = pts[a], pts[b]
        if a == 0 and b == 1:          # LHR -> JFK across the Atlantic seam
            segs.append(((x0, y0), (x1 - W_MAP, y1), True))
            segs.append(((x0 + W_MAP, y0), (x1, y1), True))
        else:
            segs.append(((x0, y0), (x1, y1), False))
    return pts, segs


METRO_PTS, RING = _ring_segments()


def network(c, P, t, alpha):
    u = t - tl.MAP_T
    a = alpha
    _panel(c, MAP_X - 10, MAP_Y - 16, 96 * MAP_P + 20, 32 * MAP_P + 30, P, a)
    c.tiny('YUNAGI NETWORK · RING 4×100G · AS207214', MAP_X, MAP_Y - 11, P['sub'], a)
    rev = seg(u, 0.0, 0.5)
    ys, xs = np.nonzero(_MAP)
    order = (xs * 0.8 + ys * 0.2) / 96
    keep = order <= rev * 1.05
    for y_, x_ in zip(ys[keep], xs[keep]):
        c.rect(MAP_X + x_ * MAP_P, MAP_Y + y_ * MAP_P, 2, 2, hexc('#6e6474'), a)
    rp = seg(u, 0.35, 1.2)
    total = len(RING)
    xl, xr = MAP_X - 6, MAP_X + 96 * MAP_P + 6
    for k, ((x0, y0), (x1, y1), wrap) in enumerate(RING):
        f = clamp01(rp * total - k)
        if f <= 0:
            continue
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        s = np.linspace(0, f, max(2, int(n * f)))
        lx = x0 + (x1 - x0) * s
        ly = y0 + (y1 - y0) * s - np.sin(s * math.pi) * (0 if wrap else 10)
        ok = (lx >= xl) & (lx <= xr)
        dash = ((np.arange(len(lx)) + int(u * 30)) // 3) % 2 == 0
        c.points(lx[ok & dash], ly[ok & dash], P['acc'], a)
        c.points(lx[ok & ~dash], ly[ok & ~dash], hexc('#6a2a24'), a)
    # travelling light
    if rp >= 1:
        q = (u * 0.35) % 1
        k = int(q * total)
        ff = q * total - k
        (x0, y0), (x1, y1), wrap = RING[k]
        px = x0 + (x1 - x0) * ff
        py = y0 + (y1 - y0) * ff - math.sin(ff * math.pi) * (0 if wrap else 10)
        if xl <= px <= xr:
            c.rect(px - 1, py - 1, 3, 3, P['hot'], a)
    for i, ((name, la, lo), (x, y)) in enumerate(zip(METROS, METRO_PTS)):
        ti = 0.4 + i * 0.12
        f = seg(u, ti, ti + 0.1)
        if f <= 0:
            continue
        pulse = ((u - ti) * 1.2) % 1
        c.circle(x, y, 3 + 6 * pulse, P['acc'], alpha=a * (1 - pulse))
        c.rect(x - 1, y - 1, 3, 3, P['ink'], a * f)
        kx, ky = LABEL_OFF[name]
        kw = pf.uni_mask(KANJI[name]).shape[1]
        lx = x + kx if kx >= 0 else x + kx - kw
        c.rect_blend(lx - 1, y + ky - 1, kw + 2, 24, hexc('#110e16'), 0.6 * a * f)
        c.uni(KANJI[name], lx, y + ky, P['ink'], alpha=a * f)
        gpu = name in ('HND-1', 'HKG-1')
        c.tiny(name + (' GPU' if gpu else ''), lx, y + ky + 17, P['acc2'] if gpu else P['sub'], a * f)
    st = seg(u, 1.2, 1.5)
    stats = '6 metros · 99.9% SLA · 38s deploy · 312 TLDs'
    c.text(stats, 240, MAP_Y + 32 * MAP_P + 2, P['ink'], align='center',
           n=int(seg(u, 1.2, 1.9) * len(stats)), alpha=a)


def lotus_thumb(c, x, y, a=1.0):
    img = scenes.LOTUS[::3, ::3]
    if a >= 1:
        c.a[y:y + 16, x:x + 16] = img
    c.frame(x - 1, y - 1, 18, 18, hexc('#4a4250'), a)


def yunagi(c, P, t):
    dusk(c, P, t)
    # wordmark
    k1 = seg(t, 48.45, 48.95)
    fade_top = 1 - seg(t, tl.END_T0 - 0.25, tl.END_T0)
    if k1 > 0 and fade_top > 0:
        m = pf.uni_mask('夕凪')
        m = np.kron(m, np.ones((3, 3), bool))
        cols = int(m.shape[1] * ease_io(k1))
        c.put_mask(m[:, :cols], 22, 24, P['ink'], fade_top)
    if t > 48.8:
        a = seg(t, 48.8, 49.0) * fade_top
        c.text('Yunagi.Cloud', 128, 28, P['ink'], bold=True, scale=2,
               n=int((t - 48.8) * 30), alpha=a)
        c.tiny('YUNAGI · THE EVENING CALM · A HIGAN HOLDINGS COMPANY', 128, 47, P['sub'], alpha=a)
        tag = 'Compute, names and inference from six metros.'
        c.text(tag, 128, 57, P['ink'], n=int((t - 49.25) * 55), alpha=a)
    if t < tl.END_T0:
        # cards
        card_out = seg(t, tl.MAP_T - 0.35, tl.MAP_T - 0.05)
        for i, (kj, title, line, lab, price) in enumerate(CARDS):
            ti = tl.CARD_TIMES[i]
            f = ease_out(seg(t, ti, ti + 0.25))
            if f <= 0 or card_out >= 1:
                continue
            a = f * (1 - card_out)
            x = 20 + i * 148
            y = 84 + int((1 - f) * 10) - int(card_out * 8)
            w, h = 144, 72
            _panel(c, x, y, w, h, P, a)
            c.rect(x + 7, y + 7, 20, 20, P['acc'], a)
            c.uni(kj, x + 9, y + 9, P['ink'], alpha=a)
            c.text(title, x + 33, y + 8, P['ink'], bold=True, alpha=a)
            c.text(line, x + 33, y + 19, P['sub'], alpha=a, n=int((t - ti) * 60))
            c.tiny(lab.upper(), x + 8, y + 38, P['dim'], alpha=a)
            c.text(price, x + 8, y + 46, P['ink'], scale=2, alpha=a)
            if i == 2 and a > 0:
                lotus_thumb(c, x + w - 24, y + 40, a)
            sweep = seg(t, ti + 0.1, ti + 0.45)
            if 0 < sweep < 1:
                sx = x + int(w * sweep)
                c.rect(sx, y + 1, 2, h - 2, P['hot'], 0.5)
        if t >= tl.MAP_T - 0.1:
            na = seg(t, tl.MAP_T - 0.1, tl.MAP_T + 0.15) * (1 - seg(t, tl.END_T0 - 0.35, tl.END_T0 - 0.05))
            if na > 0:
                network(c, P, t, na)
    # end card
    e = seg(t, tl.END_T0, tl.END_T0 + 0.3)
    if e > 0:
        u = t - tl.END_T0
        # vertical seal, 夕 over 凪
        sf = ease_back(seg(u, 0.0, 0.3))
        if sf > 0:
            sw, sh = int(24 * sf), int(42 * sf)
            c.rect(240 - sw // 2, 60 - sh // 2, sw, sh, P['acc'])
            if sf >= 0.95:
                c.uni('夕', 232, 42, P['ink'])
                c.uni('凪', 232, 60, P['ink'])
        big = 'Build on Yunagi.'
        c.text(big, 240, 90, P['ink'], bold=True, scale=3, align='center',
               n=int(seg(u, 0.2, 0.75) * len(big)))
        c.text('yunagi.cloud', 240, 124, P['acc2'], bold=True, scale=2, align='center',
               alpha=seg(u, 0.8, 1.0))
        c.text('Cloud · Domains · AI Inference', 240, 146, P['sub'], align='center',
               alpha=seg(u, 1.0, 1.2))
        c.text('Design, animation, music & sound: written entirely in code.', 240, 226,
               P['dim'], align='center', alpha=seg(u, 1.4, 1.7))


def seal(c, P, x, y, s=28):
    c.rect(x, y, s, s, P['acc'])
