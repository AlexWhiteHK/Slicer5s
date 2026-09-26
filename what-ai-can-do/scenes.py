"""Illustrations for each milestone. Every function draws onto a Canvas with
the era palette P at local time u (seconds since the scene's t0)."""
import math
import numpy as np

import gfx
from gfx import W, H, hexc, seg, ease_out, ease_in, ease_io, ease_back, clamp01, mix
import pixfont as pf


def poly_fill(c, pts, color, alpha=1.0):
    """Convex polygon fill via half-plane tests."""
    pts = np.asarray(pts, np.float32)
    x0, y0 = np.floor(pts.min(0)).astype(int)
    x1, y1 = np.ceil(pts.max(0)).astype(int)
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    px, py = xx + 0.5, yy + 0.5
    n = len(pts)
    sgn = None
    inside = np.ones_like(px, bool)
    area = 0
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        area += ax * by - bx * ay
    s = 1 if area > 0 else -1
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        cr = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        inside &= (cr * s) >= 0
    c.put_mask(inside, x0, y0, color, alpha)


def line_clip(c, x0, y0, x1, y1, rect, color, alpha=1.0):
    rx0, ry0, rx1, ry1 = rect
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    s = np.linspace(0, 1, n)
    xs, ys = x0 + (x1 - x0) * s, y0 + (y1 - y0) * s
    ok = (xs >= rx0) & (xs <= rx1) & (ys >= ry0) & (ys <= ry1)
    c.points(xs[ok], ys[ok], color, alpha)


def thick_line(c, x0, y0, x1, y1, color, alpha=1.0, t=1.0):
    c.line(x0, y0, x1, y1, color, alpha, t=t)
    c.line(x0 + 1, y0, x1 + 1, y1, color, alpha, t=t)
    c.line(x0, y0 + 1, x1, y1 + 1, color, alpha, t=t)


def arrow_head(c, x, y, color, direction='right', alpha=1.0):
    if direction == 'right':
        for k in range(4):
            c.line(x - k, y - k, x - k, y + k, color, alpha)
    else:
        for k in range(4):
            c.line(x + k, y - k, x + k, y + k, color, alpha)


PERSON = ['...###...', '..#####..', '..#####..', '...###...', '.........',
          '.#######.', '#########', '#.#####.#', '#.#####.#', '..##.##..', '..##.##..']
COMPUTER = ['###########', '#.........#', '#.#######.#', '#.#.....#.#', '#.#.....#.#',
            '#.#######.#', '#.........#', '###########', '....###....', '..#######..']


# ================================================================= 1943
def neuron(c, P, u, s):
    ink, dim, acc, sub = P['ink'], P['dim'], P['acc'], P['sub']
    cx, cy, R = 352, 118, 18
    ins = [(246, 74, '+1', 1), (232, 118, '+1', 1), (246, 162, '-1', 0)]
    for i, (x, y, w, val) in enumerate(ins):
        p = ease_out(seg(u, 0.05 + 0.08 * i, 0.5 + 0.08 * i))
        ang = math.atan2(y - cy, x - cx)
        ex, ey = cx + (R + 2) * math.cos(ang), cy + (R + 2) * math.sin(ang)
        sx, sy = x + 5 * math.cos(ang + math.pi), y + 5 * math.sin(ang + math.pi)
        c.circle(x, y, 4, ink, t=p)
        c.line(sx, sy, ex, ey, ink, t=p)
        if p > 0.6:
            mx, my = (x + ex) / 2, (y + ey) / 2
            c.text(w, mx - 6, my - 12, acc, alpha=seg(u, 0.4, 0.6))
            c.text(str(val), x - 18, y - 3, sub, alpha=seg(u, 0.3, 0.5))
        # pulse along active inputs
        pp = seg(u, 0.75, 1.1)
        if val and 0 < pp < 1:
            px, py = sx + (ex - sx) * pp, sy + (ey - sy) * pp
            c.rect(px - 1, py - 1, 3, 3, acc)
        if val and u > 0.72:
            c.disc(x, y, 2, acc)
    ring = ease_out(seg(u, 0.3, 0.75))
    c.circle(cx, cy, R, ink, t=ring)
    fire = seg(u, 1.1, 1.18)
    if u > 0.5:
        if fire > 0:
            c.disc(cx, cy, R - 2, acc, alpha=0.5 + 0.5 * fire)
            b = seg(u, 1.1, 1.5)
            if b < 1:
                c.circle(cx, cy, R + 4 + 20 * b, acc, alpha=1 - b)
        else:
            c.disc(cx, cy, R - 2, dim, alpha=0.3)
        c.text('Σ', cx - 2, cy - 3, P['bg'] if fire > 0 else ink)
        c.text('θ = 2', cx, cy + R + 6, sub, align='center', alpha=seg(u, 0.5, 0.7))
    ax = ease_out(seg(u, 0.5, 0.9))
    c.line(cx + R + 2, cy, 452, cy, ink, t=ax)
    if ax >= 1:
        arrow_head(c, 454, cy, ink)
    op = seg(u, 1.18, 1.55)
    if 0 < op < 1:
        px = cx + R + 2 + (450 - cx - R - 2) * op
        c.rect(px - 1, cy - 1, 3, 3, acc)
    if op >= 1:
        c.text('1', 460, cy - 3, acc, bold=True)
    c.text('fires if the sum reaches θ', 232, 40, sub, n=int(seg(u, 0.9, 1.6) * 26))


# ================================================================= 1950
def turing(c, P, u, s):
    ink, dim, acc, sub = P['ink'], P['dim'], P['acc'], P['sub']
    boxes = [('C', 222, 96, 62, 52, PERSON), ('A', 330, 60, 74, 52, PERSON),
             ('B', 330, 128, 74, 52, COMPUTER)]
    for i, (lab, x, y, w, h, spr) in enumerate(boxes):
        p = ease_out(seg(u, 0.05 + 0.1 * i, 0.4 + 0.1 * i))
        pts = [(x, y), (x + w - 1, y), (x + w - 1, y + h - 1), (x, y + h - 1), (x, y)]
        c.polyline(pts, ink, t=p)
        if p >= 1:
            c.text(lab, x + 3, y + 3, ink, bold=True)
            sw = len(spr[0])
            c.sprite(spr, x + w // 2 - sw // 2, y + h // 2 - 4, {'#': dim if lab != 'B' else ink})
    # wall
    wp = ease_out(seg(u, 0.2, 0.5))
    wx, wy0, wy1 = 304, 52, 188
    hh = int((wy1 - wy0) * wp)
    c.rect(wx, wy0, 8, hh, P['panel'])
    c.frame(wx, wy0, 8, max(1, hh), ink)
    for k in range(0, hh, 4):
        c.line(wx + 1, wy0 + k + 6, wx + 6, wy0 + k + 1, dim)
    # messages
    for k, (t0, tgt) in enumerate(((0.6, (330, 86)), (0.8, (330, 154)), (1.05, (330, 86)), (1.2, (330, 154)))):
        p = seg(u, t0, t0 + 0.28)
        if 0 < p < 1:
            sx, sy = 284, 122
            if k >= 2:
                sx, sy, tx, ty = tgt[0], tgt[1], 284, 122
            else:
                tx, ty = tgt
            x = sx + (tx - sx) * p
            y = sy + (ty - sy) * p
            c.rect(x - 3, y - 2, 7, 5, P['bg'])
            c.frame(x - 3, y - 2, 7, 5, acc if k >= 2 else ink)
        if p > 0:
            c.line(284, 122, 304, 122 if k % 2 == 0 else 122, dim, dash=2)
    c.line(312, 122, 330, 86, dim, dash=2, t=seg(u, 0.6, 0.8))
    c.line(312, 122, 330, 154, dim, dash=2, t=seg(u, 0.8, 1.0))
    q = seg(u, 1.4, 1.55)
    if q > 0:
        bob = int(2 * math.sin(u * 12))
        c.text('?', 250, 76 + bob, acc, scale=2, bold=True, alpha=q)
        c.text('which one is the machine?', 222, 196, sub, n=int(seg(u, 1.45, 1.95) * 26))


# ================================================================= 1956
def dartmouth(c, P, u, s):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    c.text('Summer 1956 · Dartmouth College', 224, 48, sub, n=int(seg(u, 0.05, 0.5) * 31))
    lines = [('ARTIFICIAL', 70, 0.15, 0.055), ('INTELLIGENCE', 100, 0.62, 0.05)]
    for word, y, t0, step in lines:
        x = 224
        for k, ch in enumerate(word):
            g = pf.glyph(ch)
            gw = g.shape[1]
            tk = t0 + step * k
            if u >= tk:
                d = seg(u, tk, tk + 0.06)
                dy = int((1 - d) * -8)
                m = np.kron(g, np.ones((3, 3), bool))
                c.put_mask(m, x, y + dy, ink)
                if d >= 1 and u < tk + 0.25:
                    rng = np.random.default_rng(k + y)
                    for _ in range(4):
                        c.pset(x + rng.integers(-2, gw * 3 + 2), y + 21 + rng.integers(0, 3), dim)
            x += (gw + 1) * 3
    ul = ease_out(seg(u, 1.25, 1.55))
    c.rect(224, 125, int(226 * ul), 2, acc)
    c.text('term coined by John McCarthy', 224, 134, sub, n=int(seg(u, 1.45, 1.95) * 28))


# ================================================================= 1958
_rng = np.random.default_rng(58)
_PTS_A = np.stack([_rng.normal(360, 14, 9), _rng.normal(150, 12, 9)], 1)
_PTS_B = np.stack([_rng.normal(428, 14, 9), _rng.normal(78, 12, 9)], 1)


def perceptron(c, P, u, s):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    a0 = ease_out(seg(u, 0.0, 0.35))
    # diagram
    c.circle(222, 92, 5, ink, t=a0)
    c.circle(222, 136, 5, ink, t=a0)
    c.text('x1', 212, 76, sub, alpha=a0)
    c.text('x2', 212, 146, sub, alpha=a0)
    c.line(228, 94, 258, 110, ink, t=a0)
    c.line(228, 134, 258, 118, ink, t=a0)
    c.circle(266, 114, 9, ink, t=a0)
    c.text('Σ', 264, 111, ink, alpha=a0)
    c.line(276, 114, 286, 114, ink, t=a0)
    c.frame(287, 106, 16, 16, ink, alpha=a0)
    c.line(290, 118, 295, 118, ink, alpha=a0)
    c.line(295, 110, 295, 118, ink, alpha=a0)
    c.line(295, 110, 300, 110, ink, alpha=a0)
    c.text('w', 236, 92, acc, alpha=a0)
    c.text('w', 236, 128, acc, alpha=a0)
    # plot
    rx0, ry0, rx1, ry1 = 320, 44, 462, 182
    pa = ease_out(seg(u, 0.1, 0.4))
    c.line(rx0, ry1, rx0, ry0, ink, t=pa)
    c.line(rx0, ry1, rx1, ry1, ink, t=pa)
    angs = [-35, 70, 18, 55, 42, 45]
    ep_t = [0.55, 0.78, 0.98, 1.16, 1.34]
    k = sum(1 for e in ep_t if u >= e)
    if k < len(ep_t):
        a = angs[k]
        if k > 0:
            f = ease_out(seg(u, ep_t[k - 1], ep_t[k - 1] + 0.08))
            a = angs[k - 1] + (angs[k] - angs[k - 1]) * f
    else:
        a = angs[-1]
    th = math.radians(a)
    mx, my = 392, 113
    nx, ny = math.sin(th), -math.cos(th)
    done = u >= ep_t[-1] + 0.1
    for (pts, filled, sign) in ((_PTS_A, True, 1), (_PTS_B, False, -1)):
        for j, (x, y) in enumerate(pts):
            if u < 0.15 + j * 0.02:
                continue
            side = (x - mx) * math.cos(th + math.pi / 2) + (y - my) * math.sin(th + math.pi / 2)
            wrong = (side > 0) != (sign > 0)
            col = acc if (wrong and not done and u > 0.5 and int(u * 10) % 2 == 0) else ink
            if filled:
                c.rect(x - 1, y - 1, 4, 4, col)
            else:
                c.frame(x - 2, y - 2, 5, 5, col)
    if u > 0.45:
        L = 120
        line_clip(c, mx - L * math.cos(th), my - L * math.sin(th), mx + L * math.cos(th),
                  my + L * math.sin(th), (rx0 + 2, ry0, rx1, ry1 - 2), acc)
        line_clip(c, mx - L * math.cos(th) + 1, my - L * math.sin(th), mx + L * math.cos(th) + 1,
                  my + L * math.sin(th), (rx0 + 2, ry0, rx1, ry1 - 2), acc)
        c.text('epoch %d' % min(k + 1, 5), 330, 34, sub)
    if done:
        c.text('✓ learned', 396, 34, acc, bold=True, n=int((u - ep_t[-1] - 0.1) * 30))


# ================================================================= 1966
ELIZA_LINES = [('> Men are all alike.', 0), ('IN WHAT WAY?', 1),
               ('> Always bugging us.', 0), ('CAN YOU THINK OF A', 1),
               ('SPECIFIC EXAMPLE?', 1)]


def eliza(c, P, u, s):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    x0, x1 = 268, 458
    slide = ease_out(seg(u, 0.0, 0.3))
    bot = 222
    top = int(bot - 200 * slide)
    paper = hexc('#f7f3e8')
    c.rect(x0, top, x1 - x0, bot - top, paper)
    for yy in range(top, bot, 20):
        c.rect(x0 + 12, yy, x1 - x0 - 24, 10, hexc('#dfe8d6'), 0.6)
    for yy in range(top + 4, bot - 2, 10):
        c.circle(x0 + 5, yy, 2, dim)
        c.circle(x1 - 6, yy, 2, dim)
    c.line(x0 + 11, top, x0 + 11, bot - 1, dim, dash=2)
    c.line(x1 - 12, top, x1 - 12, bot - 1, dim, dash=2)
    rail = 176
    c.rect(x0 - 4, rail + 2, x1 - x0 + 8, 2, ink)
    starts = [0.3 + 0.28 * i for i in range(len(ELIZA_LINES))]
    cur = sum(1 for st in starts if u >= st)
    scroll = 0.0
    for i, st in enumerate(starts):
        if u >= st:
            scroll += ease_out(seg(u, st, st + 0.08))
    head_x = x0 + 18
    for i, (txt, who) in enumerate(ELIZA_LINES):
        if u < starts[i]:
            continue
        n = int((u - starts[i]) * 70)
        y = rail - 10 - (scroll - (i + 1)) * 11
        if y < top + 2:
            continue
        col = acc if who else ink
        c.text(txt, x0 + 18, y, col, n=n)
        if i == cur - 1:
            head_x = x0 + 18 + pf.text_width(txt[:min(n, len(txt))]) + 1
    c.rect(head_x, rail - 1, 6, 5, acc)
    c.rect(head_x + 1, rail, 4, 3, ink)


# ================================================================= 1973
def winter(c, P, u, s):
    import hud
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    grow = ease_out(seg(u, 0.05, 1.3))
    hud._flake(c, 372, 104, 58, ink, rot=0.2 + u * 0.12, t=grow)
    hud._flake(c, 372, 104, 58, acc, rot=0.2 + u * 0.12 + 0.02, t=grow, alpha=0.35)
    c.disc(372, 104, 3, ink)
    rng = np.random.default_rng(int(u * 8))
    for _ in range(6):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0, 58 * grow)
        c.pset(372 + r * math.cos(a), 104 + r * math.sin(a), P['hot'])
    # funding meter
    c.text('FUNDING', 224, 178, sub, bold=True)
    c.frame(224, 190, 104, 11, sub)
    segs = 10
    gone = int(seg(u, 0.35, 1.35) * segs + 0.001)
    for k in range(segs):
        if k < segs - gone:
            col = mix(acc, hexc('#ff6a5a'), clamp01(gone / 10 * 1.5)) if gone > 6 else acc
            c.rect(226 + k * 10, 192, 9, 7, col)
    if gone >= segs:
        c.text('0%', 334, 192, hexc('#ff6a5a'), bold=True, alpha=0.5 + 0.5 * (int(u * 6) % 2))
    c.text('and again in 1987', 224, 206, dim, n=int(seg(u, 1.2, 1.7) * 17))


# ================================================================= 1986
_NET = [3, 4, 4, 2]
_NX = [238, 298, 358, 418]


def _net_nodes():
    out = []
    for l, n in enumerate(_NET):
        ys = [116 + (k - (n - 1) / 2) * 30 for k in range(n)]
        out.append([(_NX[l], y) for y in ys])
    return out


_NODES = _net_nodes()
_wr = np.random.default_rng(86)
_W0 = [_wr.uniform(0.1, 1, (len(_NODES[l]), len(_NODES[l + 1]))) for l in range(3)]
_W1 = [np.clip(w + _wr.normal(0, 0.45, w.shape), 0.05, 1) for w in _W0]


def backprop(c, P, u, s):
    ink, acc, sub, dim, faint = P['ink'], P['acc'], P['sub'], P['dim'], P['faint']
    hot = P['acc3']
    for l in range(3):
        for i, (x0, y0) in enumerate(_NODES[l]):
            for j, (x1, y1) in enumerate(_NODES[l + 1]):
                # backward wave passes layer l at time tb
                tb = 1.1 + (2 - l) * 0.17
                f = seg(u, tb, tb + 0.12)
                w = _W0[l][i, j] * (1 - f) + _W1[l][i, j] * f
                col = mix(faint, P['sub'], w)
                c.line(x0 + 4, y0, x1 - 4, y1, col, t=ease_out(seg(u, 0.05 + 0.08 * l, 0.3 + 0.08 * l)))
                # forward pulse
                tf = 0.35 + l * 0.19
                p = seg(u, tf, tf + 0.19)
                if 0 < p < 1:
                    c.rect(x0 + (x1 - x0) * p - 1, y0 + (y1 - y0) * p - 1, 3, 3, ink)
                q = seg(u, tb, tb + 0.17)
                if 0 < q < 1:
                    c.rect(x1 + (x0 - x1) * q - 1, y1 + (y0 - y1) * q - 1, 3, 3, hot)
    for l, layer in enumerate(_NODES):
        a = seg(u, 0.02 + 0.06 * l, 0.15 + 0.06 * l)
        lit = u > 0.35 + l * 0.19
        for (x, y) in layer:
            c.disc(x, y, 4, P['bg'], alpha=a)
            c.circle(x, y, 4, ink, alpha=a)
            if lit:
                c.disc(x, y, 2, ink)
    e = seg(u, 0.95, 1.1)
    if e > 0:
        blink = (int(u * 12) % 2 == 0) or u > 1.25
        if blink:
            c.text('error', 432, 122, hot, bold=True)
        for (x, y) in _NODES[-1]:
            c.circle(x, y, 7, hot, alpha=1 - seg(u, 1.1, 1.4))
    c.text('forward →', 238, 44, sub, n=int(seg(u, 0.3, 0.6) * 9))
    c.text('← error flows back', 300, 190, hot, n=int(seg(u, 1.1, 1.5) * 18))


# ================================================================= 1997
PIECES = {
    'K': ['..#..', '.###.', '..#..', '.###.', '.###.', '..#..', '.###.', '#####'],
    'Q': ['#.#.#', '#####', '.###.', '.###.', '..#..', '.###.', '#####'],
    'R': ['#.#.#', '#####', '.###.', '.###.', '.###.', '#####'],
    'N': ['.##..', '####.', '#.##.', '..##.', '.###.', '#####'],
    'B': ['..#..', '.##..', '.#.#.', '.###.', '..#..', '#####'],
    'P': ['.#.', '###', '.#.', '###'],
}
BOARD = [('K', 6, 0, 1), ('R', 5, 0, 1), ('P', 5, 1, 1), ('P', 6, 1, 1), ('P', 7, 2, 1),
         ('Q', 4, 2, 1), ('N', 4, 4, 1), ('B', 2, 1, 1),
         ('K', 1, 7, 0), ('R', 5, 7, 0), ('P', 0, 6, 0), ('P', 2, 6, 0), ('B', 4, 6, 0),
         ('Q', 6, 4, 0), ('N', 3, 5, 0), ('P', 5, 5, 0)]
QUEEN_FROM, QUEEN_TO, BLACK_KING = (4.5, 2.5), (1.5, 5.5), (1.5, 7.5)


def _proj_board(i, j, ang, cx=338, cy=118, k=19.0, tilt=0.5):
    X, Y = i - 4, j - 4
    xr = X * math.cos(ang) - Y * math.sin(ang)
    yr = X * math.sin(ang) + Y * math.cos(ang)
    z = 1 - yr * 0.045
    return cx + xr * k / z, cy + yr * k * tilt / z, yr


def deepblue(c, P, u, s):
    ink, acc, sub, dim, faint = P['ink'], P['acc'], P['sub'], P['dim'], P['faint']
    ang = -0.55 + 0.22 * u
    appear = ease_out(seg(u, 0.0, 0.4))
    for i in range(8):
        for j in range(8):
            if (i + j) % 2 == 0:
                q = [_proj_board(i, j, ang), _proj_board(i + 1, j, ang),
                     _proj_board(i + 1, j + 1, ang), _proj_board(i, j + 1, ang)]
                poly_fill(c, [(p[0], p[1]) for p in q], faint, alpha=appear)
    for k in range(9):
        a = _proj_board(k, 0, ang)
        b = _proj_board(k, 8, ang)
        c.line(a[0], a[1], b[0], b[1], dim, t=appear)
        a = _proj_board(0, k, ang)
        b = _proj_board(8, k, ang)
        c.line(a[0], a[1], b[0], b[1], dim, t=appear)
    # queen move with capture
    mv = ease_io(seg(u, 0.75, 1.05))
    items = []
    for (p, i, j, white) in BOARD:
        ii, jj = i + 0.5, j + 0.5
        lift = 0
        if p == 'Q' and white:
            ii = QUEEN_FROM[0] + (QUEEN_TO[0] - QUEEN_FROM[0]) * mv
            jj = QUEEN_FROM[1] + (QUEEN_TO[1] - QUEEN_FROM[1]) * mv
            lift = 10 * math.sin(math.pi * mv)
        x, y, d = _proj_board(ii, jj, ang)
        items.append((d, p, x, y - lift, white))
    items.sort()
    for (d, p, x, y, white) in items:
        spr = PIECES[p]
        h = len(spr)
        w = len(spr[0])
        if u < 0.25:
            continue
        if white:
            c.sprite(spr, x - w, y - 2 * h + 2, {'#': ink}, scale=2)
        else:
            c.sprite(spr, x - w, y - 2 * h + 2, {'#': dim}, scale=2)
            c.sprite(spr, x - w + 2, y - 2 * h + 4, {'#': P['bg']}, scale=1)
    if u > 1.05:
        f = seg(u, 1.05, 1.4)
        x, y, _ = _proj_board(BLACK_KING[0], BLACK_KING[1], ang)
        c.circle(x, y - 6, 6 + 18 * f, acc, alpha=1 - f)
        c.text('CHECK', x + 14, y - 34, acc, bold=True, alpha=1 if int(u * 8) % 2 else 0.4)
    # score board
    sa = seg(u, 0.4, 0.6)
    c.frame(386, 186, 80, 24, dim, alpha=sa)
    c.text('DEEP BLUE', 390, 189, ink, alpha=sa)
    c.text('3.5', 446, 189, acc, bold=True, alpha=sa)
    c.text('KASPAROV', 390, 199, sub, alpha=sa)
    c.text('2.5', 446, 199, sub, alpha=sa)


# ================================================================= 1998
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


_FULL5 = _digit_img(1.0)
_KERN = [np.array(k, np.float32) for k in (
    [[-1, -1, -1], [2, 2, 2], [-1, -1, -1]],
    [[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]],
    [[2, -1, -1], [-1, 2, -1], [-1, -1, 2]],
    [[-1, -1, 2], [-1, 2, -1], [2, -1, -1]])]


def _conv(img, k):
    out = np.zeros((14, 14))
    for y in range(14):
        for x in range(14):
            out[y, x] = (img[y:y + 3, x:x + 3] * k).sum()
    return np.clip(out / 3, 0, 1)


_FMAPS = [_conv(_FULL5, k) for k in _KERN]
_POOL = [f.reshape(7, 2, 7, 2).max(axis=(1, 3)) for f in _FMAPS]
_SCORES = [0.03, 0.02, 0.05, 0.14, 0.02, 0.93, 0.08, 0.02, 0.11, 0.06]


def lenet(c, P, u, s):
    ink, acc, sub, dim, faint = P['ink'], P['acc'], P['sub'], P['dim'], P['faint']
    ix, iy, cs = 216, 72, 3
    img = _digit_img(seg(u, 0.05, 0.6))
    c.frame(ix - 2, iy - 2, 16 * cs + 4, 16 * cs + 4, dim)
    for y in range(16):
        for x in range(16):
            v = img[y, x]
            if v > 0.05:
                col = ink if v > 0.66 else (P['sub'] if v > 0.33 else dim)
                c.rect(ix + x * cs, iy + y * cs, cs - 1 if cs > 2 else cs, cs - 1, col)
            else:
                c.pset(ix + x * cs + 1, iy + y * cs + 1, faint)
    c.text('input', ix, iy + 54, sub)
    scan = seg(u, 0.6, 1.05)
    if 0 < scan < 1:
        k = int(scan * 196)
        sx, sy = k % 14, k // 14
        c.frame(ix + sx * cs - 1, iy + sy * cs - 1, 3 * cs + 2, 3 * cs + 2, acc)
    # feature maps
    fx = 284
    for m in range(4):
        y0 = 48 + m * 36
        c.frame(fx - 1, y0 - 1, 30, 30, dim, alpha=seg(u, 0.55, 0.65))
        rev = int(scan * 196) if scan < 1 else 196
        f = _FMAPS[m]
        for k in range(rev):
            yy, xx = k // 14, k % 14
            v = f[yy, xx]
            if v > 0.2:
                c.rect(fx + xx * 2, y0 + yy * 2, 2, 2, ink if v > 0.55 else P['sub'])
        # pooled
        pa = seg(u, 1.0, 1.15)
        if pa > 0:
            for yy in range(7):
                for xx in range(7):
                    v = _POOL[m][yy, xx]
                    if v > 0.2:
                        c.rect(fx + 38 + xx * 2, y0 + 7 + yy * 2, 2, 2, ink if v > 0.55 else P['sub'], pa)
            c.line(fx + 30, y0 + 14, fx + 36, y0 + 14, dim, alpha=pa)
        c.line(ix + 50, iy + 24, fx - 2, y0 + 14, faint, alpha=seg(u, 0.55, 0.7))
    c.text('features', fx, 194, sub, alpha=seg(u, 0.6, 0.8))
    # outputs
    ox = 350
    ba = seg(u, 1.1, 1.45)
    for d in range(10):
        y = 46 + d * 15
        c.text(str(d), ox, y, ink if d == 5 and u > 1.4 else sub, alpha=seg(u, 1.0, 1.1))
        L = int(70 * _SCORES[d] * ease_out(ba))
        col = acc if d == 5 else dim
        c.rect(ox + 9, y + 1, L, 5, col)
        c.line(fx + 54, 48 + (d % 4) * 36 + 14, ox - 3, y + 3, faint, alpha=seg(u, 1.05, 1.15) * 0.8)
    if u > 1.45:
        c.frame(ox - 3, 46 + 5 * 15 - 3, 86, 13, acc)
        c.text('it is a 5', ox + 26, 44 + 5 * 15 - 16, acc, bold=True, n=int((u - 1.45) * 30))


# ================================================================= 2009 / 2012
_tr = np.random.default_rng(2009)
TCOLS, TROWS, TP = 32, 25, 8
_TILE_ORDER = _tr.permutation(TCOLS * TROWS)
_TILE_RANK = np.empty_like(_TILE_ORDER)
_TILE_RANK[_TILE_ORDER] = np.arange(len(_TILE_ORDER))
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


TILES = [_make_tile(_tr) for _ in range(TCOLS * TROWS)]
TILE_LUM = [np.clip((t @ np.array([0.3, 0.55, 0.15])) / 255, 0, 1) for t in TILES]
LABELS = [(0.35, 7, 5, 'cat'), (0.6, 20, 9, 'boat'), (0.85, 12, 17, 'dog'), (1.05, 26, 4, 'kite')]


def _draw_tiles(c, P, u, era, shrink=0.0, color=False):
    ox, oy = 210, 26
    n_show = int(TCOLS * TROWS * ease_out(seg(u, 0.0, 0.55)))
    cx, cy = ox + TCOLS * TP / 2, oy + TROWS * TP / 2
    greens = [P['faint'], P['dim'], P['sub'], P['ink']]
    for idx in range(TCOLS * TROWS):
        if _TILE_RANK[idx] >= n_show:
            continue
        col, row = idx % TCOLS, idx // TCOLS
        x = ox + col * TP
        y = oy + row * TP
        if shrink > 0:
            x = cx + (x - cx) * (1 - shrink)
            y = cy + (y - cy) * (1 - shrink)
            if (1 - shrink) < 0.15:
                continue
        if color:
            tile = TILES[idx]
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi and xi + 7 <= W and 0 <= yi and yi + 7 <= H:
                if shrink > 0:
                    sz = max(1, int(round(7 * (1 - shrink))))
                    c.rect(xi, yi, sz, sz, tile[3, 3])
                else:
                    c.a[yi:yi + 7, xi:xi + 7] = tile
        else:
            lum = TILE_LUM[idx]
            q = np.clip((lum * 4).astype(int), 0, 3)
            xi, yi = int(round(x)), int(round(y))
            if shrink > 0:
                sz = max(1, int(round(7 * (1 - shrink))))
                c.rect(xi, yi, sz, sz, greens[q[3, 3]])
            elif 0 <= xi and xi + 7 <= W and 0 <= yi and yi + 7 <= H:
                pal = np.stack(greens)
                c.a[yi:yi + 7, xi:xi + 7] = pal[q]


def imagenet(c, P, u, s, era='green'):
    color = era != 'green'
    _draw_tiles(c, P, u, era, color=color)
    for (t0, col, row, lab) in LABELS:
        if u > t0:
            x = 210 + col * TP - 1
            y = 26 + row * TP - 1
            c.frame(x, y, 9, 9, P['acc'] if color else P['ink'])
            w = pf.text_width(lab) + 4
            c.rect(x, y - 10, w, 10, P['acc'] if color else P['ink'])
            c.text(lab, x + 2, y - 9, P['bg'], n=int((u - t0) * 40))
    cnt = int(14_197_122 * ease_out(seg(u, 0.0, 1.1)))
    txt = '{:,}'.format(cnt)
    c.text(txt + ' images', 466, 19, P['ink'], bold=True, align='right')


GPU = ['################', '#..............#', '#.####....####.#', '#.#..#....#..#.#',
       '#.####....####.#', '#..............#', '################', '.#.#.#.#.#.#.#..']


def alexnet(c, P, u, s):
    ink, acc, sub, dim, acc2 = P['ink'], P['acc'], P['sub'], P['dim'], P['acc2']
    sh = ease_in(seg(u, 0.0, 0.35))
    if sh < 1:
        _draw_tiles(c, P, 2.0, 'neon', shrink=sh, color=True)
    a = seg(u, 0.3, 0.45)
    c.text('ImageNet challenge · top-5 error', 222, 52, sub, n=int(seg(u, 0.3, 0.8) * 34))
    b1 = ease_out(seg(u, 0.45, 0.85))
    b2 = ease_out(seg(u, 0.5, 0.95))
    c.text('AlexNet', 222, 72, ink, bold=True, alpha=a)
    c.rect(222, 83, int(122 * b1), 9, acc)
    c.rect(222, 92, int(122 * b1), 1, P['faint'])
    if b1 >= 1:
        c.text('15.3%', 350, 84, acc, bold=True)
    c.text('runner-up', 222, 104, sub, alpha=a)
    c.rect(222, 115, int(210 * b2), 9, dim)
    if b2 >= 1:
        c.text('26.2%', 436, 116, sub, bold=True)
    g = seg(u, 1.0, 1.25)
    if g > 0:
        for k in range(2):
            c.sprite(GPU, 238 + k * 44, 150 - int((1 - ease_back(g)) * 10), {'#': acc}, scale=2, alpha=g)
            for fx in (0, 1):
                ph = u * 20 + k
                cxp = 238 + k * 44 + 8 + fx * 12 + 4
                c.pset(cxp + math.cos(ph) * 2, 157 + math.sin(ph) * 2, acc2)
        c.text('trained on two GPUs', 340, 158, ink, n=int((u - 1.0) * 40))
    # sparks
    rng = np.random.default_rng(12)
    for k in range(40):
        x = 222 + rng.uniform(0, 240)
        y = 196 - ((u * rng.uniform(20, 60) + rng.uniform(0, 60)) % 60)
        if u > 0.8:
            c.pset(x, y, acc if k % 3 else acc2, 0.6)


# ================================================================= 2014
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


def gan(c, P, u, s):
    ink, acc, sub, dim, acc2 = P['ink'], P['acc'], P['sub'], P['dim'], P['acc2']
    gx, gy, dx, dy = 244, 112, 440, 112
    rng = np.random.default_rng(14)
    ap = ease_out(seg(u, 0.0, 0.3))
    for k in range(70):
        r = rng.uniform(3, 22) * ap
        ph = rng.uniform(0, 6.28) + u * rng.uniform(1, 3)
        c.pset(gx + r * math.cos(ph), gy + r * math.sin(ph) * 0.8, acc2)
        r2 = rng.uniform(3, 22) * ap
        ph2 = rng.uniform(0, 6.28) - u * rng.uniform(1, 3)
        c.pset(dx + r2 * math.cos(ph2), dy + r2 * math.sin(ph2) * 0.8, acc)
    c.disc(gx, gy, 3, acc2, alpha=ap)
    c.disc(dx, dy, 3, acc, alpha=ap)
    c.text('G', gx - 2, gy + 26, acc2, bold=True, alpha=ap)
    c.text('makes', gx, gy + 37, sub, align='center', alpha=ap)
    c.text('D', dx - 2, dy + 26, acc, bold=True, alpha=ap)
    c.text('judges', dx, dy + 37, sub, align='center', alpha=ap)
    # canvas
    fx, fy = 302, 72
    rounds = [0.3, 0.55, 0.8, 1.05, 1.3]
    k = sum(1 for r in rounds if u >= r)
    sigma = [1.0, 0.8, 0.55, 0.32, 0.14, 0.0][k]
    img = _noisy(GAN_TARGET, sigma, k * 7 + 1) if sigma > 0 else GAN_TARGET
    if u > 0.15:
        big = np.repeat(np.repeat(img, 2, 0), 2, 1)
        c.a[fy:fy + 80, fx:fx + 80] = big
        c.frame(fx - 2, fy - 2, 84, 84, ink)
        c.brackets(fx - 5, fy - 5, 90, 90, acc)
    for i, r in enumerate(rounds):
        p = seg(u, r - 0.18, r)
        if 0 < p < 1:
            for j in range(5):
                q = clamp01(p * 1.3 - j * 0.07)
                c.rect(gx + (fx - gx) * q, gy - 4 + j * 2 + math.sin(q * 6) * 6, 2, 2, acc2)
        p2 = seg(u, r, r + 0.15)
        if 0 < p2 < 1:
            for j in range(5):
                q = clamp01(p2 * 1.3 - j * 0.07)
                c.rect(fx + 80 + (dx - fx - 80) * q, gy - 4 + j * 2 + math.sin(q * 6) * 6, 2, 2, acc)
    if k > 0:
        verdict = 'fake!' if k < 5 else 'real?'
        col = hexc('#ff6a7a') if k < 5 else acc
        c.text(verdict, dx, dy - 36, col, bold=True, align='center')
    c.text('round %d' % max(1, k), fx + 40, fy + 88, sub, align='center', alpha=seg(u, 0.3, 0.4))


# ================================================================= 2016
def _proj_go(i, j):
    X = (i - 9) / 9
    zd = 2.0 + (18 - j) / 18 * 2.2
    sx = 338 + X * 250 / zd
    sy = -78 + 560 / zd
    return sx, sy, zd / 2.0


GO_MOVES = [(3, 3, 1), (15, 15, 0), (15, 3, 1), (3, 15, 0), (2, 5, 1), (5, 2, 0), (13, 16, 1),
            (16, 13, 0), (9, 2, 1), (16, 5, 0), (14, 4, 1), (4, 13, 0), (10, 15, 1)]
MOVE37 = (13, 9, 1)


def _stone(c, P, i, j, black, alpha=1.0):
    x, y, z = _proj_go(i, j)
    rx = 6.0 / z
    ry = rx * 0.62
    if black:
        c.ellipse_fill(x, y, rx + 1, ry + 1, P['sub'], alpha)
        c.ellipse_fill(x, y, rx, ry, hexc('#0c0a22'), alpha)
        c.pset(x - rx * 0.4, y - ry * 0.4, P['sub'], alpha)
        c.pset(x - rx * 0.4 + 1, y - ry * 0.4, P['dim'], alpha)
    else:
        c.ellipse_fill(x, y + 1, rx, ry, P['dim'], alpha)
        c.ellipse_fill(x, y, rx, ry, P['ink'], alpha)


def alphago(c, P, u, s):
    ink, acc, sub, dim, faint = P['ink'], P['acc'], P['sub'], P['dim'], P['faint']
    ap = ease_out(seg(u, 0.0, 0.35))
    for k in range(19):
        a = _proj_go(k, 0)
        b = _proj_go(k, 18)
        c.line(a[0], a[1], b[0], b[1], faint if k % 6 else dim, t=ap)
        a = _proj_go(0, k)
        b = _proj_go(18, k)
        c.line(a[0], a[1], b[0], b[1], faint if k % 6 else dim, t=ap)
    for (i, j) in ((3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)):
        x, y, _ = _proj_go(i, j)
        c.pset(x, y, sub, ap)
    for k, (i, j, b) in enumerate(GO_MOVES):
        tk = 0.25 + 0.06 * k
        if u >= tk:
            _stone(c, P, i, j, b, alpha=seg(u, tk, tk + 0.04))
    t37 = 1.1
    if u >= t37:
        i, j, b = MOVE37
        x, y, z = _proj_go(i, j)
        pulse = (u - t37) * 1.8 % 1
        c.ellipse_fill(x, y, 16 + 6 * pulse, 9 + 3 * pulse, faint, 0.5)
        _stone(c, P, i, j, b)
        for r in (0, 1):
            c.circle(x, y, 9 + r + 12 * pulse, acc, alpha=1 - pulse)
        c.circle(x, y, 8, acc)
        lp = ease_out(seg(u, t37 + 0.1, t37 + 0.35))
        c.line(x + 7, y - 6, x + 7 + 30 * lp, y - 30 * lp, sub)
        c.line(x + 7 + 30 * lp, y - 30 * lp, x + 7 + 50 * lp, y - 30 * lp, sub)
        if lp >= 1:
            c.text('"Move 37"', x + 40, y - 40, ink, bold=True, n=int((u - t37 - 0.35) * 30))
    sa = seg(u, 0.4, 0.55)
    c.text('4-1', 16, 146, acc, bold=True, scale=2, alpha=sa)


# ================================================================= 2017
TOKENS = ['Attention', 'Is', 'All', 'You', 'Need']
_ARCW = np.random.default_rng(17).uniform(0.2, 1, (5, 5))


def transformer(c, P, u, s):
    ink, acc, sub, dim, faint = P['ink'], P['acc'], P['sub'], P['dim'], P['faint']
    cols = [P['acc'], P['acc2'], P['acc3'], hexc('#9b6bff'), P['acc']]
    ws = [pf.text_width(t, bold=True) + 8 for t in TOKENS]
    total = sum(ws) + 4 * (len(ws) - 1)
    x = 340 - total // 2
    boxes = []
    y = 150
    for k, (tok, w) in enumerate(zip(TOKENS, ws)):
        tk = 0.05 + 0.08 * k
        a = seg(u, tk, tk + 0.1)
        c.rect(x, y, w, 15, P['panel'], a)
        c.frame(x, y, w, 15, dim, a)
        c.text(tok, x + 4, y + 4, ink, bold=True, alpha=a, n=int((u - tk) * 60))
        boxes.append((x + w / 2, y))
        x += w + 4
    k = 0
    for i in range(5):
        for j in range(i + 1, 5):
            x0, y0 = boxes[i]
            x1, y1 = boxes[j]
            h = 16 + (x1 - x0) * 0.55
            tk = 0.45 + 0.06 * k
            p = ease_out(seg(u, tk, tk + 0.3))
            if p <= 0:
                k += 1
                continue
            n = 60
            ts = np.linspace(0, p, n)
            xs = x0 + (x1 - x0) * ts
            ys = y0 - 2 - h * 4 * ts * (1 - ts)
            col = cols[i]
            wgt = _ARCW[i, j]
            c.points(xs, ys, col, 0.35 + 0.65 * wgt)
            if wgt > 0.6:
                c.points(xs, ys - 1, col, 0.5)
            if p >= 1:
                q = ((u - tk) * 0.9 + i * 0.13) % 1
                c.rect(x0 + (x1 - x0) * q - 1, y0 - 2 - h * 4 * q * (1 - q) - 1, 3, 3, P['hot'])
            k += 1
    c.text('every word looks at every other word', 340, 176, sub, align='center',
           n=int(seg(u, 1.0, 1.7) * 38))


# ================================================================= 2020
_gr = np.random.default_rng(2020)
_NG = 900
_G_R = np.sqrt(_gr.random(_NG)) * 92
_G_ARM = _gr.integers(0, 2, _NG)
_G_JIT = _gr.normal(0, 0.28, _NG)
_G_TW = _gr.uniform(0, 6.28, _NG)


def gpt3(c, P, u, s):
    ink, acc, sub, acc2, acc3 = P['ink'], P['acc'], P['sub'], P['acc2'], P['acc3']
    cx, cy = 338, 104
    grow = ease_out(seg(u, 0.0, 0.6))
    rot = u * 0.9
    th = _G_R / 92 * 4.2 + _G_ARM * math.pi + _G_JIT + rot
    r = _G_R * grow
    xs = cx + r * np.cos(th)
    ys = cy + r * np.sin(th) * 0.45
    cols = [hexc('#fff6d0'), acc2, acc, acc3]
    band = np.clip((_G_R / 92 * 4).astype(int), 0, 3)
    for b in range(4):
        m = band == b
        tw = 0.5 + 0.5 * np.sin(u * 6 + _G_TW[m])
        keep = tw > 0.25
        c.points(xs[m][keep], ys[m][keep], cols[b])
    c.disc(cx, cy, 4 * grow, hexc('#fff6d0'))
    n = int(175_000_000_000 * ease_out(seg(u, 0.1, 0.85)))
    txt = '{:,}'.format(n)
    c.text(txt, cx, 170, ink, bold=True, scale=2, align='center')
    c.text('parameters', cx, 190, sub, align='center')
    # token stream
    words = 'the model reads the internet and learns to write the next word'.split()
    x = 470 - (u * 90) % 1000
    for k, w_ in enumerate(words * 2):
        ww = pf.text_width(w_) + 6
        if 205 <= x <= 470 - ww:
            col = [acc, acc2, acc3][k % 3]
            c.rect(x, 208, ww, 11, col, 0.35)
            c.text(w_, x + 3, 210, ink)
        x += ww + 3


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


def alphafold(c, P, u, s):
    ink, acc, sub, acc2, acc3 = P['ink'], P['acc'], P['sub'], P['acc2'], P['acc3']
    f = ease_io(seg(u, 0.3, 1.05))
    pos = _LINEAR * (1 - f) + _FOLD * 1.9 * f
    ang = u * 1.3 * f + 0.4 * f
    ca, sa = math.cos(ang), math.sin(ang)
    x = pos[:, 0] * ca + pos[:, 2] * sa
    z = -pos[:, 0] * sa + pos[:, 2] * ca
    y = pos[:, 1]
    persp = 1 / (1 + z * 0.004)
    sx = 340 + x * persp * 1.0
    sy = 112 + y * persp * 1.0
    n = len(SEQ)
    stops = [hexc('#ffe066'), acc2, acc, acc3]

    def col_at(i):
        q = i / (n - 1) * 3
        b = min(2, int(q))
        return mix(stops[b], stops[b + 1], q - b)

    segs = sorted(range(n - 1), key=lambda i: -(z[i] + z[i + 1]))
    appear = seg(u, 0.0, 0.3)
    for i in segs:
        if i / n > appear * 1.05:
            continue
        col = col_at(i)
        depth = clamp01(0.55 + (-(z[i] + z[i + 1]) / 2) / 60)
        cc = mix(P['bg'], col, 0.35 + 0.65 * depth)
        thick_line(c, sx[i], sy[i], sx[i + 1], sy[i + 1], cc)
    for i in range(n):
        if i / n > appear * 1.05:
            continue
        if f < 0.35:
            c.tiny(SEQ[i], sx[i] - 1, sy[i] - 12 - (i % 2) * 7, sub, alpha=1 - f / 0.35)
    if f >= 1:
        c.text('structure predicted', 340, 196, ink, align='center', n=int((u - 1.05) * 40))


# ================================================================= 2022
_br = np.random.default_rng(22)
_NB = 240
_B_ANG = _br.uniform(0, 6.28, _NB)
_B_SPD = _br.uniform(0.35, 1.0, _NB)
_B_OFF = _br.uniform(0, 1, _NB)
_B_COL = _br.integers(0, 4, _NB)


def chatgpt(c, P, u, s):
    ink, acc, sub, acc2, acc3 = P['ink'], P['acc'], P['sub'], P['acc2'], P['acc3']
    cx, cy = 338, 96
    cols = [acc, acc2, P['hot'], acc3]
    for k in range(_NB):
        ph = (_B_OFF[k] + u * _B_SPD[k] * 0.9) % 1
        r0 = 10 + ph ** 1.6 * 260
        r1 = r0 + 6 + ph * 34
        a = _B_ANG[k]
        c.line(cx + r0 * math.cos(a), cy + r0 * math.sin(a) * 0.8,
               cx + r1 * math.cos(a), cy + r1 * math.sin(a) * 0.8, cols[_B_COL[k]],
               alpha=0.35 + 0.65 * ph)
    punch = seg(u, 0.05, 0.2)
    if punch > 0:
        sc = 5 if punch < 1 else 4
        shake = int(3 * (1 - seg(u, 0.2, 0.6)) * math.sin(u * 90))
        w = pf.text_width('ChatGPT', bold=True) * sc
        c.rect(cx - w // 2 - 6, cy - 4 * sc - 4, w + 12, 7 * sc + 8, P['bg'], 0.7)
        c.text('ChatGPT', cx + 3 + shake, cy - 7 * sc // 2 + 3, acc, bold=True, scale=sc, align='center')
        c.text('ChatGPT', cx + shake, cy - 7 * sc // 2, ink, bold=True, scale=sc, align='center')
    # chat bubbles
    q = 'Can you explain AI?'
    a = 'Sure! Let me start...'
    t1 = 0.55
    if u > t1:
        w = pf.text_width(q) + 10
        c.rect(464 - w, 138, w, 13, acc)
        c.text(q, 464 - w + 5, 141, P['bg'], n=int((u - t1) * 50))
    t2 = 0.95
    if u > t2:
        w = pf.text_width(a) + 10
        c.rect(214, 158, w, 13, P['panel'])
        c.frame(214, 158, w, 13, sub)
        c.text(a, 219, 161, ink, n=int((u - t2) * 40))


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


def diffusion(c, P, u, s):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    fx, fy = 290, 30
    prompt = '> a lotus at dusk, pixel art'
    c.text(prompt, 290, 136, ink, n=int(seg(u, 0.0, 0.5) * len(prompt)), cursor=u < 0.6,
           cursor_color=acc)
    steps = 28
    k = int(seg(u, 0.5, 1.45) * steps)
    sigma = (1 - k / steps) ** 1.4
    if u > 0.05:
        if sigma > 0.001:
            r = np.random.default_rng(k + 5)
            eps = r.normal(0, 1, LOTUS.shape)
            img = LOTUS * (1 - sigma) + (128 + eps * 90) * sigma
            img = np.clip(np.round(img / 42) * 42, 0, 255)
        else:
            img = LOTUS
        big = np.repeat(np.repeat(img, 2, 0), 2, 1)
        c.a[fy:fy + 96, fx:fx + 96] = big
        c.frame(fx - 2, fy - 2, 100, 100, sub)
        c.brackets(fx - 5, fy - 5, 106, 106, acc)
    c.text('step %02d/%d' % (max(1, k), steps), fx + 104, fy + 2, sub)
    c.text('σ %.2f' % sigma, fx + 104, fy + 14, dim)
    c.text('x = x0 + σ·ε', fx + 104, fy + 84, dim, alpha=seg(u, 0.5, 0.7))
    if k >= steps:
        f = seg(u, 1.45, 1.8)
        rng = np.random.default_rng(3)
        for j in range(14):
            a = rng.uniform(0, 6.28)
            rr = 50 + 30 * f * rng.uniform(0.5, 1)
            c.pset(fx + 48 + rr * math.cos(a), fy + 48 + rr * math.sin(a), P['hot'], 1 - f)


# ================================================================= 2023 / 2024
def frontier(c, P, u, s):
    ink, acc, sub, dim, acc2, acc3 = P['ink'], P['acc'], P['sub'], P['dim'], P['acc2'], P['acc3']
    x0, y0, x1, y1 = 224, 40, 440, 196
    ap = ease_out(seg(u, 0.0, 0.25))
    c.line(x0, y1, x0, y0, dim, t=ap)
    c.line(x0, y1, x1, y1, dim, t=ap)
    c.tiny('CAPABILITY', x0 + 3, y0, sub)
    c.tiny('TIME', x1 - 14, y1 + 3, sub)
    names = [('GPT-4', acc, 0.0, 2.2), ('Claude', acc2, 1.3, 1.7), ('Llama', acc3, 2.6, 1.25)]
    p = ease_io(seg(u, 0.1, 1.2))
    for k, (nm, col, ph, rate) in enumerate(names):
        n = 90
        ts = np.linspace(0, p, n)
        g = (np.exp(ts * rate) - 1) / (math.exp(2.2) - 1)
        wig = 0.04 * np.sin(ts * 7 + ph) * ts
        xs = x0 + 2 + ts * (x1 - x0 - 50)
        ys = y1 - 2 - (g + wig) * (y1 - y0 - 24)
        c.points(xs, ys, col)
        c.points(xs, ys - 1, col, 0.5)
        if p > 0.05:
            c.rect(xs[-1] - 1, ys[-1] - 1, 3, 3, P['hot'])
            c.text(nm, xs[-1] + 5, ys[-1] - 4, col, bold=True)


_TREE = {}


def _build_tree():
    levels = [[(224, 118, None, True)]]
    rng = np.random.default_rng(24)
    best = [1, 2, 1, 1]
    for L in range(1, 5):
        prev = levels[-1]
        cur = []
        kids_per = [3, 2, 2, 2][L - 1]
        for pi, (px, py, _, pb) in enumerate(prev):
            for k in range(kids_per):
                spread = [42, 20, 10, 6][L - 1]
                y = py + (k - (kids_per - 1) / 2) * spread
                cur.append((224 + L * 58, y, pi, False))
        levels.append(cur)
    # best path
    path = [0]
    idx = 0
    for L in range(1, 5):
        kids = [i for i, n in enumerate(levels[L]) if n[2] == idx]
        idx = kids[min(len(kids) - 1, best[L - 1])]
        path.append(idx)
    return levels, path


TREE, TREE_PATH = _build_tree()


def reasoning(c, P, u, s):
    ink, acc, sub, dim, faint = P['ink'], P['acc'], P['sub'], P['dim'], P['faint']
    gold = P['hot']
    order = []
    for L in range(1, 5):
        for i, n in enumerate(TREE[L]):
            order.append((L, i))
    rng = np.random.default_rng(99)
    dead = set()
    for (L, i) in order:
        if L >= 2 and i != TREE_PATH[L] and rng.random() < 0.55:
            dead.add((L, i))
    n_vis = int(seg(u, 0.05, 0.85) * len(order))
    for k, (L, i) in enumerate(order[:n_vis]):
        x, y, pi, _ = TREE[L][i]
        px, py = TREE[L - 1][pi][0], TREE[L - 1][pi][1]
        parent_dead = (L - 1, pi) in dead
        if parent_dead:
            continue
        on_path = TREE_PATH[L] == i and TREE_PATH[L - 1] == pi
        col = dim
        c.line(px + 2, py, x - 2, y, col if (L, i) not in dead else faint)
        if (L, i) in dead and u > 0.5:
            c.line(x - 2, y - 2, x + 2, y + 2, hexc('#ff6a7a'))
            c.line(x - 2, y + 2, x + 2, y - 2, hexc('#ff6a7a'))
        else:
            c.rect(x - 1, y - 1, 3, 3, sub)
    c.rect(222, 116, 5, 5, ink)
    hp = seg(u, 0.85, 1.25)
    if hp > 0:
        pts = [(TREE[L][TREE_PATH[L]][0], TREE[L][TREE_PATH[L]][1]) for L in range(5)]
        c.polyline(pts, gold, t=hp)
        c.polyline([(x, y + 1) for x, y in pts], gold, t=hp)
        if hp >= 1:
            x, y = pts[-1]
            c.disc(x, y, 3, gold)
            c.text('answer ✓', x - 20, y + 8, gold, bold=True, n=int((u - 1.25) * 30))
    dots = '.' * (1 + int(u * 5) % 3)
    c.text('thinking' + dots if hp < 1 else 'thought for 12s', 224, 40, sub)
    m = seg(u, 1.05, 1.25)
    if m > 0:
        for k in range(2):
            x = 410 + k * 26
            yb = 44 - int((1 - ease_back(m)) * 8)
            c.line(x - 3, yb - 8, x, yb - 1, P['acc'], m)
            c.line(x + 3, yb - 8, x, yb - 1, P['acc3'], m)
            c.disc(x, yb + 4, 6, gold, m)
            c.disc(x, yb + 4, 3, hexc('#c89a2a'), m)
        c.text('Nobel', 422, 58, sub, align='center', alpha=m)


# ================================================================= 2025-26
CODE_LINES = [
    [(2, 'k'), (6, 'i'), (10, 'v')],
    [(4, 'i'), (5, 'k'), (8, 'v'), (4, 'i')],
    [(6, 'i'), (12, 's'), (3, 'i')],
    [(4, 'k'), (9, 'i')],
    [(6, 'i'), (5, 'k'), (10, 's')],
    [(8, 'c')],
    [(4, 'k'), (7, 'v'), (6, 'i')],
    [(6, 'i'), (4, 'k'), (11, 'v')],
    [(10, 'i'), (6, 's')],
    [(4, 'k'), (5, 'i')],
]
TASKS = ['read the repo', 'write the fix', 'run the tests', 'open a PR']
TASK_T = [0.75, 1.45, 2.3, 3.05]
CURSOR = ['#.......', '##......', '#o#.....', '#oo#....', '#ooo#...', '#oooo#..',
          '#oo###..', '#.#o#...', '...#o#..', '....#...']


def agents(c, P, u, s):
    ink, acc, sub, dim, faint, green = P['ink'], P['acc'], P['sub'], P['dim'], P['faint'], P['acc2']
    wx, wy, ww, wh = 214, 32, 254, 170
    open_ = ease_out(seg(u, 0.0, 0.3))
    close = ease_in(seg(u, 3.7, 3.95))
    hh = int(wh * open_ * (1 - close))
    if hh < 2:
        return
    yy0 = wy + (wh - hh) // 2
    c.rect(wx + 3, yy0 + 3, ww, hh, faint)
    c.rect(wx, yy0, ww, hh, hexc('#fbf8f2'))
    c.frame(wx, yy0, ww, hh, ink)
    if open_ < 1 or close > 0:
        return
    c.rect(wx + 1, wy + 1, ww - 2, 11, P['panel'])
    c.line(wx, wy + 12, wx + ww - 1, wy + 12, ink)
    for k, col in enumerate((acc, dim, dim)):
        c.disc(wx + 7 + k * 8, wy + 6, 2, col)
    c.tiny('AGENT · SESSION', wx + ww // 2, wy + 4, sub, align='center')
    split = wx + 142
    c.line(split, wy + 13, split, wy + wh - 1, faint)
    # code
    colmap = {'k': acc, 'i': ink, 'v': hexc('#2b4a6f'), 's': green, 'c': dim}
    n_chars = (u - 0.3) * 38
    y = wy + 18
    done_chars = 0
    for li, line in enumerate(CODE_LINES):
        x = wx + 8
        c.tiny(str(li + 1), wx + 4, y, faint, align='right')
        for (L, kind) in line:
            show = int(clamp01((n_chars - done_chars) / 1.0) * 0 + max(0, min(L, n_chars - done_chars)))
            if show > 0:
                c.rect(x + 4, y + 1, show * 3 - 1, 3, colmap[kind])
            done_chars += L
            x += L * 3 + 3
        y += 8
        if n_chars <= done_chars:
            c.rect(x + 2, y - 8, 2, 5, acc, 1 if int(u * 4) % 2 else 0)
            break
    # test output
    to = seg(u, 2.45, 2.6)
    if to > 0:
        c.line(wx + 1, wy + 112, split - 1, wy + 112, faint)
        c.text('$ run tests', wx + 6, wy + 118, sub, n=int((u - 2.45) * 40))
        if u > 2.7:
            c.text('14 passed ✓', wx + 6, wy + 130, green, bold=True, n=int((u - 2.7) * 40))
    # tasks
    for k, task in enumerate(TASKS):
        ty = wy + 22 + k * 16
        c.frame(split + 8, ty, 8, 8, ink)
        done = u >= TASK_T[k]
        c.text(task, split + 20, ty + 1, ink if done else dim)
        if done:
            f = seg(u, TASK_T[k], TASK_T[k] + 0.1)
            c.text('✓', split + 9, ty, acc, bold=True, alpha=f)
    # run button + cursor
    bx, by = split + 20, wy + 100
    pressed = 2.25 <= u < 2.4
    c.rect(bx, by + (1 if pressed else 0), 44, 14, acc if not pressed else hexc('#8a2a20'))
    c.text('RUN', bx + 22, by + 4 + (1 if pressed else 0), hexc('#fbf8f2'), bold=True, align='center')
    path = [(0.0, 440, 190), (1.2, 420, 150), (2.05, bx + 26, by + 8), (2.6, bx + 30, by + 10),
            (3.0, split + 12, wy + 72), (3.4, split + 60, wy + 150)]
    px, py = path[0][1], path[0][2]
    for (ta, xa, ya), (tb, xb, yb) in zip(path, path[1:]):
        if ta <= u:
            f = ease_io(seg(u, ta, tb))
            px, py = xa + (xb - xa) * f, ya + (yb - ya) * f
    c.sprite(CURSOR, px, py, {'#': ink, 'o': hexc('#fbf8f2')})
    if 2.25 <= u < 2.5:
        r = (u - 2.25) * 60
        c.circle(px, py, r, acc, alpha=1 - (u - 2.25) / 0.25)


FUNCS = {
    'neuron': neuron, 'turing': turing, 'dartmouth': dartmouth, 'perceptron': perceptron,
    'eliza': eliza, 'winter': winter, 'backprop': backprop, 'deepblue': deepblue,
    'lenet': lenet, 'imagenet': imagenet, 'alexnet': alexnet, 'gan': gan, 'alphago': alphago,
    'transformer': transformer, 'gpt3': gpt3, 'alphafold': alphafold, 'chatgpt': chatgpt,
    'diffusion': diffusion, 'frontier': frontier, 'reasoning': reasoning, 'agents': agents,
}
