"""Pixel canvas: primitives, ordered dithering and the 4x post pipeline."""
import math
import numpy as np
from PIL import Image, ImageFilter

import pixfont as pf

W, H = 480, 270          # base canvas, upscaled 4x to 1920x1080
SCALE = 4

# 8x8 Bayer matrix, normalised to (0,1)
_b2 = np.array([[0, 2], [3, 1]])
_b = _b2
for _ in range(2):
    _b = np.block([[4 * _b + 0, 4 * _b + 2], [4 * _b + 3, 4 * _b + 1]])
BAYER8 = (_b + 0.5) / 64.0
BAYER = np.tile(BAYER8, (H // 8 + 2, W // 8 + 2))[:H, :W]


def hexc(s):
    s = s.lstrip('#')
    if len(s) == 3:
        s = ''.join(ch * 2 for ch in s)
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def mix(c1, c2, t):
    return np.asarray(c1, np.float32) * (1 - t) + np.asarray(c2, np.float32) * t


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp01(t)
    return t * t * t


def ease_io(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def ease_back(t, s=1.7):
    t = clamp01(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def seg(t, a, b):
    """0..1 progress of t through [a, b]."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp01((t - a) / (b - a))


class Canvas:
    def __init__(self, bg=(0, 0, 0)):
        self.a = np.zeros((H, W, 3), dtype=np.float32)
        self.a[:] = np.asarray(bg, np.float32)

    # ------------------------------------------------------------ basics
    def copy(self):
        c = Canvas.__new__(Canvas)
        c.a = self.a.copy()
        return c

    def _dmask(self, alpha, y0, y1, x0, x1):
        if alpha >= 1:
            return None
        return BAYER[y0:y1, x0:x1] < alpha

    def put_mask(self, m, x, y, color, alpha=1.0):
        """Paint colour where bool mask m is set; alpha is dithered."""
        if alpha <= 0:
            return
        x, y = int(round(x)), int(round(y))
        h, w = m.shape
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        mm = m[y0 - y:y1 - y, x0 - x:x1 - x]
        d = self._dmask(alpha, y0, y1, x0, x1)
        if d is not None:
            mm = mm & d
        self.a[y0:y1, x0:x1][mm] = color

    def rect(self, x, y, w, h, color, alpha=1.0):
        x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0 or alpha <= 0:
            return
        if alpha >= 1:
            self.a[y0:y1, x0:x1] = color
        else:
            d = BAYER[y0:y1, x0:x1] < alpha
            self.a[y0:y1, x0:x1][d] = color

    def rect_blend(self, x, y, w, h, color, alpha):
        """True (non-dithered) blend, used sparingly for glass panels."""
        x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        reg = self.a[y0:y1, x0:x1]
        reg[:] = reg * (1 - alpha) + np.asarray(color, np.float32) * alpha

    def frame(self, x, y, w, h, color, alpha=1.0):
        self.rect(x, y, w, 1, color, alpha)
        self.rect(x, y + h - 1, w, 1, color, alpha)
        self.rect(x, y, 1, h, color, alpha)
        self.rect(x + w - 1, y, 1, h, color, alpha)

    def brackets(self, x, y, w, h, color, n=4, alpha=1.0):
        for (px, py, sx, sy) in ((x, y, 1, 1), (x + w - 1, y, -1, 1),
                                 (x, y + h - 1, 1, -1), (x + w - 1, y + h - 1, -1, -1)):
            for i in range(n):
                self.pset(px + sx * i, py, color, alpha)
                self.pset(px, py + sy * i, color, alpha)

    def pset(self, x, y, color, alpha=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            if alpha >= 1 or BAYER[y, x] < alpha:
                self.a[y, x] = color

    def points(self, xs, ys, color, alpha=1.0):
        xs = np.round(np.asarray(xs)).astype(int)
        ys = np.round(np.asarray(ys)).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        xs, ys = xs[ok], ys[ok]
        if alpha < 1:
            keep = BAYER[ys, xs] < alpha
            xs, ys = xs[keep], ys[keep]
        self.a[ys, xs] = color

    def line(self, x0, y0, x1, y1, color, alpha=1.0, dash=0, t=1.0, phase=0):
        """Pixel line; t<1 draws only the first fraction (draw-on)."""
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        if n <= 0 or t <= 0:
            return
        m = max(1, int(round(n * clamp01(t))))
        s = np.arange(m) / max(1, n - 1)
        xs = x0 + (x1 - x0) * s
        ys = y0 + (y1 - y0) * s
        if dash:
            keep = ((np.arange(m) + phase) // dash) % 2 == 0
            xs, ys = xs[keep], ys[keep]
        self.points(xs, ys, color, alpha)

    def polyline(self, pts, color, alpha=1.0, t=1.0):
        pts = np.asarray(pts, np.float32)
        if len(pts) < 2:
            return
        seglen = np.hypot(*(pts[1:] - pts[:-1]).T)
        total = seglen.sum()
        if total == 0:
            return
        want = total * clamp01(t)
        acc = 0
        for i, L in enumerate(seglen):
            if acc >= want:
                break
            f = 1.0 if acc + L <= want else (want - acc) / L
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], color, alpha, t=f)
            acc += L

    def circle(self, cx, cy, r, color, alpha=1.0, t=1.0, a0=-math.pi / 2):
        if r <= 0:
            self.pset(cx, cy, color, alpha)
            return
        n = int(max(8, 2 * math.pi * r * 1.6) * clamp01(t))
        if n <= 0:
            return
        th = a0 + np.linspace(0, 2 * math.pi * clamp01(t), n, endpoint=False)
        self.points(cx + r * np.cos(th), cy + r * np.sin(th), color, alpha)

    def disc(self, cx, cy, r, color, alpha=1.0):
        r = max(0.0, r)
        x0, x1 = int(math.floor(cx - r - 1)), int(math.ceil(cx + r + 1))
        y0, y1 = int(math.floor(cy - r - 1)), int(math.ceil(cy + r + 1))
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        m = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r + 0.3
        self.put_mask(m, x0, y0, color, alpha)

    def ellipse_fill(self, cx, cy, rx, ry, color, alpha=1.0):
        x0, x1 = int(math.floor(cx - rx - 1)), int(math.ceil(cx + rx + 1))
        y0, y1 = int(math.floor(cy - ry - 1)), int(math.ceil(cy + ry + 1))
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        m = ((xx - cx) / max(rx, .5)) ** 2 + ((yy - cy) / max(ry, .5)) ** 2 <= 1.02
        self.put_mask(m, x0, y0, color, alpha)

    def dither_rect(self, x, y, w, h, color, density):
        self.rect(x, y, w, h, color, alpha=density)

    # ------------------------------------------------------------ text
    def text(self, s, x, y, color, scale=1, bold=False, n=None, alpha=1.0,
             align='left', spacing=1, cursor=False, cursor_color=None):
        if n is not None:
            s_vis = s[:max(0, int(n))]
        else:
            s_vis = s
        m = pf.text_mask(s_vis, spacing=spacing, bold=bold) if s_vis else np.zeros((9, 0), bool)
        full_w = pf.text_width(s, spacing=spacing, bold=bold) * scale
        if align == 'center':
            x = x - full_w / 2
        elif align == 'right':
            x = x - full_w
        if scale != 1 and m.size:
            m = np.kron(m, np.ones((scale, scale), dtype=bool))
        if m.size:
            self.put_mask(m, x, y, color, alpha)
        if cursor:
            cx = x + (m.shape[1] + (spacing * scale if m.shape[1] else 0))
            self.rect(cx, y, 5 * scale, 7 * scale, cursor_color if cursor_color is not None else color, alpha)
        return m.shape[1]

    def tiny(self, s, x, y, color, alpha=1.0, align='left', scale=1):
        m = pf.tiny_mask(s)
        if scale != 1:
            m = np.kron(m, np.ones((scale, scale), dtype=bool))
        if align == 'center':
            x -= m.shape[1] / 2
        elif align == 'right':
            x -= m.shape[1]
        self.put_mask(m, x, y, color, alpha)
        return m.shape[1]

    def uni(self, s, x, y, color, scale=1, alpha=1.0, align='left'):
        m = pf.uni_mask(s)
        if scale != 1:
            m = np.kron(m, np.ones((scale, scale), dtype=bool))
        if align == 'center':
            x -= m.shape[1] / 2
        self.put_mask(m, x, y, color, alpha)
        return m.shape[1]

    def sprite(self, rows, x, y, colors, scale=1, alpha=1.0, flip=False):
        """rows: list of strings; colors: dict char->rgb ('.' transparent)."""
        for ch, col in colors.items():
            m = np.array([[c == ch for c in r] for r in rows], dtype=bool)
            if flip:
                m = m[:, ::-1]
            if scale != 1:
                m = np.kron(m, np.ones((scale, scale), dtype=bool))
            self.put_mask(m, x, y, col, alpha)

    # ------------------------------------------------------------ fills
    def vgrad(self, stops, y0=0, y1=H, x0=0, x1=W, levels=None):
        """Vertical gradient through colour stops, ordered-dithered between
        adjacent stops so it stays in a limited palette."""
        stops = [np.asarray(s, np.float32) for s in stops]
        n = len(stops)
        ys = np.arange(y0, y1)
        t = (ys - y0) / max(1, (y1 - y0 - 1))
        lv = t * (n - 1)
        base = np.clip(np.floor(lv).astype(int), 0, n - 2)
        frac = lv - base
        b = BAYER[y0:y1, x0:x1]
        pick_hi = b < frac[:, None]
        idx = base[:, None] + pick_hi
        pal = np.stack(stops)
        self.a[y0:y1, x0:x1] = pal[idx]

    def texture(self, color, density, seed=0, x0=0, y0=0, x1=W, y1=H):
        rng = np.random.default_rng(seed)
        m = rng.random((y1 - y0, x1 - x0)) < density
        self.a[y0:y1, x0:x1][m] = color


def composite(a, b, mask):
    """Return a where mask False, b where mask True."""
    out = a.copy()
    out.a[mask] = b.a[mask]
    return out


def dissolve_mask(p):
    """Ordered-dither dissolve: fraction p of pixels switched."""
    return BAYER < p


def wipe_mask(p, direction='right', soft=24):
    xs = np.arange(W)[None, :].repeat(H, 0).astype(np.float32)
    ys = np.arange(H)[:, None].repeat(W, 1).astype(np.float32)
    if direction == 'right':
        pos = xs / W
    elif direction == 'down':
        pos = ys / H
    elif direction == 'diag':
        pos = (xs / W * 0.7 + ys / H * 0.3)
    else:
        pos = 1 - xs / W
    edge = p * (1 + soft / W) - soft / W
    f = (edge - pos) / (soft / W) + 1
    return BAYER < np.clip(f, 0, 1)


def pixelate(c, block):
    if block <= 1:
        return c
    a = c.a
    h2, w2 = H // block, W // block
    small = a[:h2 * block, :w2 * block].reshape(h2, block, w2, block, 3).mean(axis=(1, 3))
    big = np.repeat(np.repeat(small, block, 0), block, 1)
    out = c.copy()
    out.a[:h2 * block, :w2 * block] = big
    return out


# ------------------------------------------------------------ post pipeline
_OW, _OH = W * SCALE, H * SCALE
_yy, _xx = np.mgrid[0:_OH, 0:_OW]
_GRID = ((_yy % SCALE == SCALE - 1) | (_xx % SCALE == SCALE - 1)).astype(np.float32)
_SCAN = (_yy % SCALE >= SCALE - 2).astype(np.float32)
_r = np.hypot((_xx - _OW / 2) / (_OW / 2), (_yy - _OH / 2) / (_OH / 2))
_VIG = np.clip(1 - 0.5 * np.clip(_r - 0.55, 0, None) ** 1.6, 0, 1).astype(np.float32)
del _yy, _xx, _r


def post(c, bloom=0.0, grid=0.06, scan=0.0, vignette=0.0, aberr=0, shake=(0, 0),
         brightness=1.0, flash=0.0, flash_color=(255, 255, 255)):
    a = np.clip(c.a, 0, 255)
    if shake != (0, 0):
        a = np.roll(a, (int(shake[1]), int(shake[0])), axis=(0, 1))
    big = np.repeat(np.repeat(a, SCALE, axis=0), SCALE, axis=1)
    if grid > 0:
        big *= (1 - grid * _GRID)[..., None]
    if scan > 0:
        big *= (1 - scan * _SCAN)[..., None]
    if bloom > 0:
        lum = a.max(axis=2, keepdims=True)
        hi = a * np.clip((lum - 90) / 120, 0, 1)
        im = Image.fromarray(hi.astype(np.uint8))
        b1 = im.filter(ImageFilter.GaussianBlur(2.2)).resize((_OW, _OH), Image.BILINEAR)
        b2 = im.filter(ImageFilter.GaussianBlur(7)).resize((_OW, _OH), Image.BILINEAR)
        big += bloom * (0.55 * np.asarray(b1, np.float32) + 0.8 * np.asarray(b2, np.float32))
    if aberr:
        k = int(aberr)
        big[..., 0] = np.roll(big[..., 0], k, axis=1)
        big[..., 2] = np.roll(big[..., 2], -k, axis=1)
    if vignette > 0:
        big *= (1 - vignette * (1 - _VIG))[..., None]
    if brightness != 1.0:
        big *= brightness
    if flash > 0:
        big = big * (1 - flash) + np.asarray(flash_color, np.float32) * flash
    return np.clip(big, 0, 255).astype(np.uint8)
