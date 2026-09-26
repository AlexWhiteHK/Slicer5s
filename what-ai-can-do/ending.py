"""Intro terminal, the closing question and the Lotus AI Lab / Yunagi.Cloud ending."""
import math
import os
import numpy as np

from gfx import W, H, hexc, seg, ease_out, ease_io, ease_back, clamp01
import pixfont as pf
import timeline as tl
import hud
import sprites as S

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
SHORT = {'SPARK': 'SPARK', 'PERCEPTRON': 'PERCEPTRON', 'NEURAL KNIGHT': 'KNIGHT',
         'DEEP SEER': 'SEER', 'TRANSFORMER DRAKE': 'DRAKE', 'FOUNDATION TITAN': 'TITAN',
         'AGENT': 'AGENT'}
FORM_POP = [tl.Q_FORMS_T + i * tl.Q_FORM_STEP for i in range(len(S.FORMS))]
ICON_POP = [tl.Q_ICONS_T + i * tl.Q_ICON_STEP for i in range(len(tl.SKILLS))]


def q_layout(i):
    n = len(tl.SKILLS)
    x0 = 240 - (n * 14 - 1) // 2
    return x0 + i * 14, 138


def question(c, P, t):
    q = tl.INTRO_Q
    n = max(0, min(len(q), int((t - tl.Q_LINE1_T) * tl.Q_LINE1_CPS)))
    x = 240 - pf.text_width(q, bold=True) * 2 // 2
    c.text(q, x, 40, P['ink'], bold=True, scale=2, n=n)
    if 0 < n < len(q):
        c.rect(x + pf.text_width(q[:n], bold=True) * 2 + 3, 40, 9, 14, P['acc'])
    # the evolution line, left to right
    slot = 64
    x0 = 240 - slot * 3
    for i, name in enumerate(S.FORMS):
        f = seg(t, FORM_POP[i], FORM_POP[i] + 0.12)
        if f <= 0:
            continue
        cx = x0 + i * slot
        hop = int(-6 * math.sin(math.pi * f)) if f < 1 else 0
        if f < 1:
            S.draw_sprite(c, S.HERO[name], cx, 112 + hop, None, 2, silhouette=P['acc'])
        else:
            S.draw_sprite(c, S.HERO[name], cx, 112, S.role_colors(P, 'neon', S.SCHEME[name]), 2)
        c.tiny(SHORT[name], cx, 117, P['sub'], align='center')
        if i:
            c.text('→', cx - slot // 2 - 3, 94, P['dim'])
    # every skill, in one row
    if t >= tl.Q_ICONS_T - 0.05:
        hud.draw_hotbar(c, P, t, 'clean', layout=q_layout, scale=1, pop_times=ICON_POP)
    last = ICON_POP[-1] + 0.1
    if t > last:
        c.tiny('LV %d · %d SKILLS · 7 FORMS' % (tl.level(t), len(tl.SKILLS)), 240, 156, P['acc'],
               align='center', alpha=seg(t, last, last + 0.2))
    k = int((t - tl.Q_LINE2_T) * tl.Q_LINE2_CPS)
    if k > 0:
        L2 = tl.Q_LINE2
        x2 = 240 - pf.text_width(L2) * 2 // 2
        c.text(L2, x2, 178, P['acc'], scale=2, n=k)
        if k < len(L2) or int(t * 2.5) % 2 == 0:
            c.rect(x2 + pf.text_width(L2[:min(k, len(L2))]) * 2 + 3, 178, 9, 14, P['acc'])


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


CARDS = [   # Lotus AI Lab, served on Yunagi.Cloud
    dict(tag='IMAGE', big='V7', name='Realistic V7', l1='photoreal on a DiT', l2='skin, light, material',
         thumb='real'),
    dict(tag='IMAGE', big='V7', name='Anime Diffusion V7', l1='stylised anime', l2='a higher floor',
         thumb='anime'),
    dict(tag='LANGUAGE', big='LM', name='OSIMM LM Series', l1='built on GLM & Kimi', l2='dialogue · coding',
         thumb='osimm'),
]


def _sphere(kind, n=40):
    """The same sphere, lit two ways: photoreal (many dithered tones) and cel-shaded."""
    img = np.zeros((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n] + 0.5
    img[:] = hexc('#1a1422') if kind == 'real' else hexc('#f3e6f0')
    fy = yy > n * 0.78
    img[fy] = hexc('#2a2030') if kind == 'real' else hexc('#e0c8dc')
    cx, cy, r = n / 2, n * 0.46, n * 0.34
    dx, dy = (xx - cx) / r, (yy - cy) / r
    inside = dx * dx + dy * dy <= 1
    dz = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1))
    L = np.array([-0.55, -0.6, 0.58])
    L /= np.linalg.norm(L)
    lam = np.clip(dx * L[0] + dy * L[1] + dz * L[2], 0, 1)
    shadow = ((xx - cx - 3) / (r * 1.05)) ** 2 + ((yy - n * 0.82) / (r * 0.28)) ** 2 < 1
    if kind == 'real':
        img[shadow & ~inside] *= 0.45
        base = hexc('#e2502e')
        spec = np.clip(lam, 0, 1) ** 28
        rim = np.clip(1 - dz, 0, 1) ** 3 * 0.35
        col = base[None, None] * (0.12 + 0.88 * lam[..., None]) + 255 * spec[..., None] * 0.9
        col += np.array([60, 80, 140]) * rim[..., None]
        levels = 10
        b = (np.arange(n)[:, None] % 4 * 4 + np.arange(n)[None, :] % 4 + 0.5) / 16
        q = np.floor(col / 255 * levels + b[..., None] * 0.9) / levels * 255
        img[inside] = np.clip(q, 0, 255)[inside]
    else:
        img[shadow & ~inside] = hexc('#c8a8c4')
        tone = np.where(lam > 0.45, 1, 0)
        img[inside & (tone == 1)] = hexc('#ff8aa8')
        img[inside & (tone == 0)] = hexc('#c85078')
        hl = ((xx - cx + r * 0.38) ** 2 / 9 + (yy - cy + r * 0.42) ** 2 / 5) < 1
        img[inside & hl] = hexc('#ffffff')
        edge = inside & ~(np.roll(inside, 1, 0) & np.roll(inside, -1, 0) & np.roll(inside, 1, 1) & np.roll(inside, -1, 1))
        img[edge] = hexc('#3a1a2a')
    return img


THUMBS = {'real': _sphere('real'), 'anime': _sphere('anime')}


def _thumb(c, kind, x, y, a):
    if kind == 'osimm':
        c.rect(x, y, 40, 40, hexc('#f5f1e8'), a)
        red = hexc('#b1352a')
        c.frame(x, y, 40, 40, red, a)
        c.line(x, y, x + 39, y + 39, red, a * 0.6, dash=2)
        c.line(x + 39, y, x, y + 39, red, a * 0.6, dash=2)
        c.line(x + 20, y, x + 20, y + 39, red, a * 0.6, dash=2)
        c.line(x, y + 20, x + 39, y + 20, red, a * 0.6, dash=2)
        m = np.kron(pf.uni_mask('蓮'), np.ones((2, 2), bool))
        c.put_mask(m, x + 4, y + 4, hexc('#1c1a16'), a)
        c.rect(x + 31, y + 31, 7, 7, red, a)
    else:
        if a >= 1:
            c.a[y:y + 40, x:x + 40] = THUMBS[kind]
        c.frame(x - 1, y - 1, 42, 42, hexc('#4a4250'), a)


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
    c.tiny('HOSTED API ON YUNAGI.CLOUD · GPU ROWS IN TOKYO & HONG KONG', MAP_X, MAP_Y - 11, P['sub'], a)
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
    stats = 'metered per request · L40S & H100 by the hour · open weights'
    c.text(stats, 240, MAP_Y + 32 * MAP_P + 2, P['ink'], align='center',
           n=int(seg(u, 1.2, 1.9) * len(stats)), alpha=a)


def yunagi(c, P, t):
    dusk(c, P, t)
    # the hero rests on the shore
    S.draw_sprite(c, S.HERO['AGENT'], 40, HORIZON + 4, S.role_colors(P, 'dusk', S.SCHEME['AGENT']), 2)
    fade_top = 1 - seg(t, tl.END_T0 - 0.25, tl.END_T0)
    k1 = seg(t, 48.45, 48.95)
    if k1 > 0 and fade_top > 0:
        m = np.kron(pf.uni_mask('蓮'), np.ones((3, 3), bool))
        cols = int(m.shape[1] * ease_io(k1))
        c.put_mask(m[:, :cols], 22, 22, P['ink'], fade_top)
    if t > 48.8:
        a = seg(t, 48.8, 49.0) * fade_top
        c.text('Lotus AI Lab', 78, 26, P['ink'], bold=True, scale=2, n=int((t - 48.8) * 30), alpha=a)
        c.tiny('A HIGAN HOLDINGS COMPANY · MODELS SERVED ON YUNAGI.CLOUD', 78, 45, P['sub'], alpha=a)
        tag = 'Frontier models, with a higher floor.'
        c.text(tag, 78, 55, P['ink'], n=int((t - 49.2) * 55), alpha=a)
    if t < tl.END_T0:
        card_out = seg(t, tl.MAP_T - 0.35, tl.MAP_T - 0.05)
        if t > tl.CARD_TIMES[0] - 0.2 and card_out < 1:
            c.tiny('ONE LOTUS, THREE MODELS', 20, 72, P['acc2'], alpha=(1 - card_out) * seg(t, tl.CARD_TIMES[0] - 0.2, tl.CARD_TIMES[0]))
        for i, cd in enumerate(CARDS):
            ti = tl.CARD_TIMES[i]
            f = ease_out(seg(t, ti, ti + 0.25))
            if f <= 0 or card_out >= 1:
                continue
            a = f * (1 - card_out)
            x = 20 + i * 148
            y = 82 + int((1 - f) * 12) - int(card_out * 8)
            w, h = 144, 92
            _panel(c, x, y, w, h, P, a)
            _thumb(c, cd['thumb'], x + 8, y + 8, a)
            c.tiny(cd['tag'], x + 56, y + 10, P['sub'], a)
            c.text(cd['big'], x + 56, y + 18, P['acc2'], bold=True, scale=2, alpha=a)
            c.tiny('LEGENDARY', x + 56, y + 38, P['hot'], a)
            c.text(cd['name'], x + 8, y + 55, P['ink'], bold=True, alpha=a)
            c.text(cd['l1'], x + 8, y + 67, P['sub'], alpha=a, n=int((t - ti) * 70))
            c.text(cd['l2'], x + 8, y + 77, P['sub'], alpha=a, n=int((t - ti - 0.15) * 70))
            sp = seg(t, ti, ti + 0.45)
            if 0 < sp < 1:
                rng = np.random.default_rng(i)
                for k in range(16):
                    ang = rng.uniform(0, 6.28)
                    r = 10 + 70 * sp * rng.uniform(0.5, 1)
                    c.rect(x + w / 2 + r * math.cos(ang), y + h / 2 + r * math.sin(ang) * 0.6, 2, 2,
                           P['hot'], 1 - sp)
                c.rect(x + int(w * sp), y + 1, 2, h - 2, P['hot'], 0.5)
        if t >= tl.MAP_T - 0.1:
            na = seg(t, tl.MAP_T - 0.1, tl.MAP_T + 0.15) * (1 - seg(t, tl.END_T0 - 0.35, tl.END_T0 - 0.05))
            if na > 0:
                network(c, P, t, na)
    # end card
    e = seg(t, tl.END_T0, tl.END_T0 + 0.3)
    if e > 0:
        u = t - tl.END_T0
        sf = ease_back(seg(u, 0.0, 0.3))
        if sf > 0:
            s_ = int(24 * sf)
            c.rect(240 - s_ // 2, 60 - s_ // 2, s_, s_, P['acc'])
            if sf >= 0.95:
                c.uni('蓮', 232, 52, P['ink'])
        big = 'Build on Yunagi.'
        c.text(big, 240, 86, P['ink'], bold=True, scale=3, align='center',
               n=int(seg(u, 0.2, 0.75) * len(big)))
        c.text('yunagi.cloud', 240, 120, P['acc2'], bold=True, scale=2, align='center',
               alpha=seg(u, 0.8, 1.0))
        c.text('Lotus AI Lab: Realistic V7 · Anime Diffusion V7 · OSIMM LM', 240, 142, P['sub'],
               align='center', alpha=seg(u, 1.0, 1.2))
        c.text('Design, animation, music & sound: written entirely in code.', 240, 226,
               P['dim'], align='center', alpha=seg(u, 1.4, 1.7))
