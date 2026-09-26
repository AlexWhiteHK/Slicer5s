"""Shared pixel assets for the encounters: the handwritten digit, image tiles,
the GAN painting, the protein chain, the galaxy, the lotus painting and more."""
import math

import numpy as np

from gfx import hexc, mix

def thick_line(c, x0, y0, x1, y1, color, alpha=1.0, t=1.0):
    c.line(x0, y0, x1, y1, color, alpha, t=t)
    c.line(x0 + 1, y0, x1 + 1, y1, color, alpha, t=t)
    c.line(x0, y0 + 1, x1, y1 + 1, color, alpha, t=t)


# ---------------------------------------------------------------- the handwritten digit
_DIGIT_PATH = [(12, 2), (5, 2), (4, 7.5), (8, 7), (11.5, 8.5), (12.5, 11), (11, 13.5),
               (7.5, 14.5), (3.5, 13)]



def _digit_img(p):
    img = np.zeros((16, 16))
    pts = np.array(_DIGIT_PATH, np.float32)
    seglen = np.hypot(*(pts[1:] - pts[:-1]).T)
    total = seglen.sum() * p
    yy, xx = np.mgrid[0:16, 0:16] + 0.5
    acc = 0
    for i, L in enumerate(seglen):
        if acc >= total:
            break
        f = min(1, (total - acc) / L)
        a = pts[i]
        b = a + (pts[i + 1] - a) * f
        ab = b - a
        denom = max(1e-6, (ab ** 2).sum())
        tt = np.clip(((xx - a[0]) * ab[0] + (yy - a[1]) * ab[1]) / denom, 0, 1)
        d = np.hypot(xx - (a[0] + ab[0] * tt), yy - (a[1] + ab[1] * tt))
        img = np.maximum(img, np.clip(1.6 - d, 0, 1))
        acc += L
    return img


_SCORES = [0.03, 0.02, 0.05, 0.14, 0.02, 0.93, 0.08, 0.02, 0.11, 0.06]


# ---------------------------------------------------------------- ImageNet tiles
_tr = np.random.default_rng(2009)
N_TILES = 800
_NAT = [hexc(h) for h in ('#6fa8dc', '#8fc3e8', '#4f8a3a', '#7fb35a', '#8a5a3a', '#c28a50',
                          '#d8d0c0', '#606060', '#c04a3a', '#e8b840', '#2a4a7a', '#f0e6d0',
                          '#a0785a', '#3a3a3a', '#e07a9a')]



def _make_tile(r):
    t = np.zeros((7, 7, 3), np.float32)
    kind = r.integers(0, 4)
    a, b, cc = [_NAT[i] for i in r.choice(len(_NAT), 3, replace=False)]
    if kind == 0:
        h = r.integers(2, 5)
        t[:h] = a
        t[h:] = b
        t[h - 1:h + 2, 2:5] = cc
    elif kind == 1:
        t[:] = a
        yy, xx = np.mgrid[0:7, 0:7]
        m = (xx - 3) ** 2 + (yy - 3.5) ** 2 < r.uniform(4, 9)
        t[m] = b
    elif kind == 2:
        t[:] = a
        t[::2] = b
        t[3:6, 1:6] = cc
    else:
        t[:] = a
        t[2:6, 1:4] = b
        t[1:4, 3:6] = cc
    return t


TILES = [_make_tile(_tr) for _ in range(N_TILES)]
TILE_LUM = [np.clip((t @ np.array([0.3, 0.55, 0.15])) / 255, 0, 1) for t in TILES]


# ---------------------------------------------------------------- the GAN painting
def _synth_target():
    img = np.zeros((40, 40, 3), np.float32)
    top, mid, bot = hexc('#2a0a5a'), hexc('#c02a8a'), hexc('#ff9a4a')
    for y in range(26):
        f = y / 25
        col = mix(top, mid, min(1, f * 1.6)) if f < 0.62 else mix(mid, bot, (f - 0.62) / 0.38)
        img[y] = col
    yy, xx = np.mgrid[0:40, 0:40]
    sun = (xx - 20) ** 2 + (yy - 22) ** 2 < 100
    sun &= yy < 26
    img[sun] = hexc('#ffd23d')
    for sy in (18, 21, 24):
        img[sy][(xx[sy] - 20) ** 2 < 100 - (sy - 22) ** 2] = mix(hexc('#ffd23d'), mid, 0.6)
    img[26:] = hexc('#140628')
    for gy in (26, 28, 31, 35, 39):
        img[gy] = hexc('#ff4fd8')
    for gx in range(-40, 80, 8):
        for y in range(26, 40):
            x = int(20 + (gx - 20) * (1 + (y - 26) * 0.12))
            if 0 <= x < 40:
                img[y, x] = hexc('#ff4fd8')
    return img


GAN_TARGET = _synth_target()


def _noisy(img, sigma, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, img.shape) * 160 * sigma
    out = img * (1 - 0.5 * sigma) + n + 60 * sigma
    out = np.clip(out, 0, 255)
    return (np.round(out / 64) * 64).clip(0, 255)


# ---------------------------------------------------------------- attention weights
_ARCW = np.random.default_rng(17).uniform(0.2, 1, (5, 5))

# ---------------------------------------------------------------- GPT-3 galaxy
_gr = np.random.default_rng(2020)
_NG = 900
_G_R = np.sqrt(_gr.random(_NG)) * 92
_G_ARM = _gr.integers(0, 2, _NG)
_G_JIT = _gr.normal(0, 0.28, _NG)
_G_TW = _gr.uniform(0, 6.28, _NG)

# ---------------------------------------------------------------- the protein chain
SEQ = 'MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNL'


def _fold_coords():
    n = len(SEQ)
    out = np.zeros((n, 3))
    for i in range(n):
        if i < 20:
            a = i * math.radians(100)
            out[i] = (6 * math.cos(a), -28 + i * 2.6, 6 * math.sin(a) - 9)
        elif i < 27:
            f = (i - 20) / 6
            out[i] = (-4 + 10 * math.sin(f * math.pi), 24 + 6 * math.sin(f * math.pi), -9 + 18 * f)
        else:
            a = (i - 27) * math.radians(100)
            out[i] = (6 * math.cos(a), 24 - (i - 27) * 2.6, 6 * math.sin(a) + 9)
    return out


_FOLD = _fold_coords()
_LINEAR = np.stack([np.linspace(-100, 100, len(SEQ)), np.sin(np.arange(len(SEQ)) * 0.5) * 4,
                    np.zeros(len(SEQ))], 1)

# ---------------------------------------------------------------- ChatGPT burst
_br = np.random.default_rng(22)
_NB = 240
_B_ANG = _br.uniform(0, 6.28, _NB)
_B_SPD = _br.uniform(0.35, 1.0, _NB)
_B_OFF = _br.uniform(0, 1, _NB)
_B_COL = _br.integers(0, 4, _NB)


# ---------------------------------------------------------------- the lotus painting
def _lotus_target():
    n = 48
    img = np.zeros((n, n, 3), np.float32)
    sky = [hexc('#2a1446'), hexc('#6a2456'), hexc('#c0443a'), hexc('#f09a4a')]
    for y in range(28):
        q = y / 27 * 3
        b = min(2, int(q))
        img[y] = mix(sky[b], sky[b + 1], q - b)
    yy, xx = np.mgrid[0:n, 0:n]
    sun = ((xx - 32) ** 2 + (yy - 26) ** 2 < 42) & (yy < 28)
    img[sun] = hexc('#ffd27a')
    img[28:] = hexc('#1a1030')
    for y in range(29, n, 3):
        w = 6 - (y - 29) // 4
        if w > 0:
            img[y, 32 - w:32 + w] = mix(hexc('#ffd27a'), hexc('#c0443a'), (y - 29) / 19)
    ridge = 24 + 3 * np.sin(np.arange(n) * 0.25) + 2 * np.sin(np.arange(n) * 0.6)
    for x in range(0, 26):
        img[int(ridge[x]):28, x] = hexc('#3a1e40')
    pad = ((xx - 17) ** 2 / 90 + (yy - 40) ** 2 / 6) < 1
    img[pad] = hexc('#2e6b4f')
    petals = [((17, 33), 3.2, 6.5, hexc('#ff9ab8')), ((12, 35), 3, 5, hexc('#e86a94')),
              ((22, 35), 3, 5, hexc('#e86a94')), ((17, 36), 5, 3, hexc('#ffc4d6'))]
    for (px, py), rx, ry, col in petals:
        m = ((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2 < 1
        img[m] = col
    img[37:39, 16:19] = hexc('#ffe066')
    return img


LOTUS = _lotus_target()

# ---------------------------------------------------------------- mouse cursor
CURSOR = ['#.......', '##......', '#o#.....', '#oo#....', '#ooo#...', '#oooo#..',
          '#oo###..', '#.#o#...', '...#o#..', '....#...']

