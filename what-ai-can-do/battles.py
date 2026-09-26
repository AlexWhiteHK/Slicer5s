"""One dungeon encounter per milestone.

Each function draws the room's monsters and effects for local time u and
returns how the hero should be posed: dict(dx, dy, pose, show).
"""
import math
import numpy as np

import gfx
from gfx import W, hexc, mix, seg, ease_out, ease_in, ease_io, ease_back, clamp01
import pixfont as pf
import sprites as S
import dungeon as D
import assets as A
import timeline as tl

HX, FY = D.HERO_X, D.FLOOR_Y


def _layer():
    c = gfx.Canvas()
    c.a[:] = -1
    return c


def _stamp(c, lay):
    m = lay.a[..., 0] >= 0
    c.a[m] = lay.a[m]


def _mon(c, lay, u, t_burst, seed=0, dur=0.5):
    if u < t_burst:
        _stamp(c, lay)
    else:
        f = seg(u, t_burst, t_burst + dur)
        if f < 1:
            S.burst(c, lay, f, seed)


def _enter_x(u, base=D.MON_X):
    return base + (1 - ease_out(seg(u, 0, tl.WALK))) * 70


def _mcols(era, P, scheme):
    return S.role_colors(P, era, scheme)


MON = {   # monster colour schemes (full-colour eras)
    'chest': dict(o='#1a0a04', b='#c8783a', s='#8a4a20', h='#ffd8a0', a='#ffd23d', e='#fff', g='#fff'),
    'slime_a': dict(o='#10200c', b='#6ad06a', s='#3a8a3a', h='#c8ffc8', a='#ffd23d', e='#10200c', g='#fff'),
    'slime_b': dict(o='#2a0c18', b='#ff8ab0', s='#c84a78', h='#ffd0e0', a='#ffd23d', e='#2a0c18', g='#fff'),
    'king': dict(o='#0a1a0c', b='#2a3a2e', s='#141e16', h='#8affb0', a='#ff5a4a', e='#ff5a4a', g='#fff'),
    'villager': dict(o='#2a1a10', b='#e0b080', s='#a07050', h='#fff0d0', a='#5a8ae0', e='#2a1a10', g='#fff'),
    'dummy': dict(o='#2a1606', b='#d8a860', s='#8a6030', h='#fff0c0', a='#e0503d', e='#fff', g='#fff'),
    'shadow': dict(o='#05030c', b='#1a1238', s='#0c0820', h='#3a2a70', a='#ff4fd8', e='#ff4fd8', g='#ff4fd8'),
    'bug': dict(o='#1c1a16', b='#2e6b4f', s='#1e4a36', h='#8ad0a8', a='#b1352a', e='#f5f1e8', g='#fff'),
}


# ================================================================= 1943 — birth
def neuron(c, P, u, s, era):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    cx, cy, R = HX, 112, 12
    born = u >= 1.2
    if not born:
        ins = [(HX - 70, 76, '+1', 1), (HX - 80, 112, '+1', 1), (HX - 70, 148 - 4, '-1', 0)]
        for i, (x, y, w, val) in enumerate(ins):
            p = ease_out(seg(u, 0.05 + 0.08 * i, 0.45 + 0.08 * i))
            ang = math.atan2(y - cy, x - cx)
            ex, ey = cx + (R + 2) * math.cos(ang), cy + (R + 2) * math.sin(ang)
            c.circle(x, y, 3, ink, t=p)
            c.line(x + 4 * math.cos(ang + math.pi), y + 4 * math.sin(ang + math.pi), ex, ey, ink, t=p)
            if p > 0.6:
                c.text(w, (x + ex) / 2 - 4, (y + ey) / 2 - 11, acc, alpha=seg(u, 0.4, 0.6))
                c.text(str(val), x - 12, y - 3, sub, alpha=seg(u, 0.3, 0.5))
            pp = seg(u, 0.7, 1.05)
            if val and 0 < pp < 1:
                c.rect(x + (ex - x) * pp - 1, y + (ey - y) * pp - 1, 3, 3, acc)
        c.circle(cx, cy, R, ink, t=ease_out(seg(u, 0.3, 0.7)))
        fire = seg(u, 1.05, 1.2)
        if u > 0.5:
            c.disc(cx, cy, R - 2, acc if fire > 0 else dim, alpha=0.35 + 0.65 * fire)
            c.text('θ=2', cx + R + 4, cy - 3, sub, alpha=seg(u, 0.5, 0.7))
        c.text('fires when the sum reaches θ', 240, 44, sub, align='center',
               n=int(seg(u, 0.6, 1.1) * 28))
    else:
        f = seg(u, 1.2, 1.5)
        if f < 1:
            c.circle(cx, FY - 12, 6 + 40 * f, acc, alpha=1 - f)
            c.circle(cx, FY - 12, 4 + 28 * f, ink, alpha=1 - f)
        D.float_text(c, P, 'A NEURON AWAKENS', HX, 72, u, 1.25, 0.75, acc)
    # the dungeon gate opens
    gx = 372
    op = ease_io(seg(u, 1.35, 1.8))
    c.rect(gx - 34, 58, 68, FY - 58, P['ink'] if era == 'paper' else P['faint'])
    c.rect(gx - 30, 62, 60, FY - 62, hexc('#0c0a08'))
    dw = int(30 * (1 - op))
    c.rect(gx - 30, 62, dw, FY - 62, P['dim'])
    c.rect(gx + 30 - dw, 62, dw, FY - 62, P['dim'])
    for k in range(3):
        c.line(gx - 30 + dw - 1, 66 + k * 26, gx - 30 + dw - 1, 80 + k * 26, P['ink'])
    c.text('FLOOR 1943', gx, 48, P['ink'], bold=True, align='center')
    if op > 0:
        for k in range(6):
            c.line(gx - 26 + k * 10, 64, gx - 60 + k * 16, FY, acc, alpha=0.25 * op)
    return dict(show=born, pose='idle')


# ================================================================= 1950 — the mimic
def turing(c, P, u, s, era):
    x = _enter_x(u)
    cols = _mcols(era, P, MON['chest'])
    lay = _layer()
    op = ease_back(seg(u, 0.95, 1.07)) if u < 1.3 else 1.0
    wob = int(2 * math.sin(u * 50)) if 0.5 < u < 0.9 else 0
    bite = int(10 * math.sin(math.pi * seg(u, 1.0, 1.15)))
    S.chest(lay, x + wob - bite, FY, P, open_=clamp01(op), scale=3, cols=cols, teeth=True)
    if 1.3 <= u < 1.36:
        m = lay.a[..., 0] >= 0
        lay.a[m] = P['hot']
    _mon(c, lay, u, 1.34, seed=50)
    for t0 in (0.3, 0.55):
        f = seg(u, t0, t0 + 0.28)
        if 0 < f < 1:
            c.text('?', HX + 16 + (x - HX - 30) * f, 96 - 22 * math.sin(math.pi * f), P['acc'], bold=True, scale=2)
    D.float_text(c, P, 'HUMAN OR MACHINE?', x, 74, u, 0.45, 0.55, P['ink'])
    if u >= 0.95:
        D.encounter(c, P, u, x, 70, 0.95)
        D.monster_bar(c, P, 'MIMIC', x, 52, 1.0 - seg(u, 1.26, 1.32), alpha=1 - seg(u, 1.35, 1.5))
    D.slash(c, P, x - 10, FY - 26, u, 1.26)
    D.float_text(c, P, '-120', x, 70, u, 1.28, 0.6, P['acc'])
    pose = 'hurt' if 1.05 <= u < 1.2 else 'idle'
    return dict(dx=D.lunge(u, [1.12]) - (6 if pose == 'hurt' else 0), pose=pose)


# ================================================================= 1956 — name entry
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NAME = 'ARTIFICIAL INTELLIGENCE'


def dartmouth(c, P, u, s, era):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    x0, y0, w, h = 190, 40, 276, 100
    close = ease_in(seg(u, 1.45, 1.62))
    op = ease_out(seg(u, 0.0, 0.15))
    hh = int(h * op * (1 - close))
    if hh > 2:
        yy = y0 + (h - hh) // 2
        c.rect(x0, yy, w, hh, P['bg'])
        c.frame(x0, yy, w, hh, ink)
        c.frame(x0 + 2, yy + 2, w - 4, hh - 4, dim)
    if op >= 1 and close <= 0:
        c.text('NAME THE NEW FIELD', x0 + 10, y0 + 8, sub, bold=True)
        step = 0.05
        n = int(clamp01((u - 0.15) / (step * len(NAME))) * len(NAME))
        c.rect(x0 + 10, y0 + 30, w - 20, 1, dim)
        c.text(NAME[:n], x0 + 10, y0 + 20, ink, bold=True)
        if n < len(NAME) and int(u * 8) % 2 == 0:
            c.rect(x0 + 10 + pf.text_width(NAME[:n], bold=True) + 1, y0 + 20, 5, 7, acc)
        cur = NAME[min(n, len(NAME) - 1)] if n < len(NAME) else None
        for i, ch in enumerate(LETTERS + '_'):
            cx = x0 + 14 + (i % 9) * 28
            cy = y0 + 42 + (i // 9) * 16
            lab = ch if ch != '_' else 'END'
            sel = (ch == cur) or (cur == ' ' and ch == '_' and False)
            if n >= len(NAME) and ch == '_':
                sel = True
            if sel:
                c.frame(cx - 4, cy - 3, 24 if lab == 'END' else 14, 13, acc)
                c.text(lab, cx, cy, acc, bold=True)
            else:
                c.text(lab, cx, cy, sub)
        if 1.36 < u < 1.45:
            c.rect(x0 + 14 + 8 * 28 - 4, y0 + 42 + 2 * 16 - 3, 24, 13, acc)
    if u >= 1.55:
        c.text('A.I.', HX, FY - 40, ink, bold=True, align='center', alpha=seg(u, 1.55, 1.65))
    D.float_text(c, P, 'NAME SET!', HX, 70, u, 1.5, 0.6, acc)
    return dict(pose='idle')


# ================================================================= 1958 — the tangled swarm
_sr = np.random.default_rng(58)
_SA = np.stack([_sr.normal(318, 16, 9), _sr.normal(128, 8, 9)], 1)
_SB = np.stack([_sr.normal(412, 16, 9), _sr.normal(82, 8, 9)], 1)
_S0 = np.stack([_sr.uniform(250, 450, 18), _sr.uniform(70, 140, 18)], 1)


def perceptron(c, P, u, s, era):
    acc, sub = P['acc'], P['sub']
    shift = (1 - ease_out(seg(u, 0, tl.WALK))) * 70
    sort = ease_io(seg(u, 0.25, 0.5))
    angs = [-35, 70, 18, 55, 42, 45]
    ep_t = [0.55, 0.72, 0.88, 1.03, 1.18]
    k = sum(1 for e in ep_t if u >= e)
    a = angs[min(k, 5)]
    if 0 < k <= 5:
        f = ease_out(seg(u, ep_t[k - 1], ep_t[k - 1] + 0.07))
        a = angs[k - 1] + (angs[k] - angs[k - 1]) * f
    th = math.radians(a)
    mx, my = 365 + shift, 105
    lay = _layer()
    cA = _mcols(era, P, MON['slime_a'])
    cB = _mcols(era, P, MON['slime_b'])
    if era == 'paper':
        cB = dict(cA)
        cB['b'] = P['acc']
    for grp, pts, cols, sign in ((0, _SA, cA, 1), (1, _SB, cB, -1)):
        for j, (px, py) in enumerate(pts):
            x0, y0 = _S0[grp * 9 + j]
            x = x0 + (px - x0) * sort + shift
            y = y0 + (py - y0) * sort - abs(math.sin(u * 9 + j)) * 3
            side = (x - mx) * math.cos(th + math.pi / 2) + (y - my) * math.sin(th + math.pi / 2)
            wrong = (side > 0) != (sign > 0)
            if wrong and u > 0.5 and int(u * 12) % 2 == 0 and k < 5:
                S.draw_sprite(lay, S.SLIME, x, y, None, 2, silhouette=P['hot'])
            else:
                S.draw_sprite(lay, S.SLIME, x, y, cols, 2)
    _mon(c, lay, u, 1.28, seed=58)
    if 0.5 < u < 1.3:
        L = 110
        for d in (0, 1):
            c.line(mx - L * math.cos(th) + d, my - L * math.sin(th), mx + L * math.cos(th) + d,
                   my + L * math.sin(th), acc)
        c.text('epoch %d' % min(k + 1, 5), mx + 40, 44, sub)
        c.rect(HX + 14, FY - 26, 3, 3, P['hot'] if int(u * 20) % 2 else acc)
    if u > 0.3:
        D.monster_bar(c, P, 'TANGLED SWARM', 365 + shift, 40, 1 - min(1, k / 5), alpha=1 - seg(u, 1.3, 1.45))
    D.float_text(c, P, 'SPLIT!', mx, 90, u, 1.22, 0.6, acc, scale=2)
    return dict(pose='idle')


# ================================================================= 1966 — ELIZA
VILLAGER = ['..ooo..', '.obbbo.', '.obebo.', '.obbbo.', '..ooo..', '.oaaao.', 'oaaaaao',
            'oaoaoao', '.oaaao.', '.ob.bo.', '.ob.bo.', 'oo...oo']
DIALOG = [('HUMAN: Men are all alike.', 0), ('AI: IN WHAT WAY?', 1),
          ("HUMAN: They're always bugging us.", 0),
          ('AI: CAN YOU THINK OF A SPECIFIC EXAMPLE?', 1)]


def eliza(c, P, u, s, era):
    ink, acc, dim = P['ink'], P['acc'], P['dim']
    x = _enter_x(u, 400)
    S.draw_sprite(c, VILLAGER, x, FY, _mcols(era, P, MON['villager']), 2, flip=True)
    op = ease_out(seg(u, 0.15, 0.3))
    bx, by, bw, bh = 150, 44, 316, 66
    if op > 0:
        hh = int(bh * op)
        c.rect(bx, by, bw, hh, P['bg'])
        c.frame(bx, by, bw, hh, ink)
        c.frame(bx + 2, by + 2, bw - 4, hh - 4, dim)
    if op >= 1:
        for i, (line, who) in enumerate(DIALOG):
            t0 = 0.3 + 0.25 * i
            n = int((u - t0) * 70)
            if n > 0:
                c.text(line, bx + 10, by + 9 + i * 12, acc if who else ink, n=n)
        if u > 1.3 and int(u * 4) % 2 == 0:
            c.text('v', bx + bw - 14, by + bh - 12, acc, bold=True)
    talking = any(0.3 + 0.25 * i < u < 0.55 + 0.25 * i for i in (1, 3))
    return dict(pose='idle', dy=-1 if talking and int(u * 16) % 2 else 0)


# ================================================================= 1973 — the AI winter
def winter(c, P, u, s, era):
    import hud
    x = D.MON_X + 10
    rise = ease_out(seg(u, 0.05, 0.4))
    S.ice_golem(c, x, FY, P, u + s['t0'], rise=rise)
    if u > 0.1:
        D.encounter(c, P, u, x, 50, 0.1)
        D.monster_bar(c, P, 'AI WINTER', x, 40, 1.0)
    f = seg(u, 0.45, 0.85)
    if 0 < f < 1:
        rng = np.random.default_rng(int(u * 60))
        for k in range(60):
            q = clamp01(f * 1.4 - rng.random() * 0.4)
            px = x - 20 + (HX + 10 - x + 20) * q
            py = 76 + (FY - 30 - 76) * q + rng.normal(0, 8)
            c.rect(px, py, 2, 2, P['ink'] if k % 3 else P['acc2'])
    hud.draw_snow(c, P, u + s['t0'], alpha=0.9, big=False)
    D.float_text(c, P, '-95%', HX, 80, u, 0.6, 0.6, hexc('#ff6a5a'), scale=2)
    D.float_text(c, P, 'FUNDING FROZEN', HX, 64, u, 0.95, 0.8, P['ink'])
    if u > 1.3:
        for k in range(3):
            q = ((u - 1.3) * 1.2 + k * 0.33) % 1
            c.text('z', HX + 20 + q * 14 + k * 3, FY - 48 - q * 22, P['sub'], alpha=1 - q, scale=1 + (k == 2))
    pose = 'hurt' if 0.55 <= u < 0.75 else ('frozen' if u >= 0.75 else 'idle')
    return dict(pose=pose)


# ================================================================= 1986 — backprop
MINI_NET = [[(-10, -8), (-10, 0), (-10, 8)], [(0, -10), (0, -3), (0, 4), (0, 11)], [(10, -5), (10, 5)]]


def backprop(c, P, u, s, era):
    acc, sub, hot = P['acc'], P['sub'], P['hot']
    x = _enter_x(u)
    lay = _layer()
    hitf = 1.1 <= u < 1.16
    S.draw_sprite(lay, S.DUMMY, x, FY, _mcols(era, P, MON['dummy']), 3,
                  silhouette=hot if hitf else None)
    _mon(c, lay, u, 1.2, seed=86)
    if u < 1.25:
        D.monster_bar(c, P, 'TRAINING DUMMY', x, 40, 1 - seg(u, 1.1, 1.16))
    # thaw
    if u < 0.3:
        rng = np.random.default_rng(int(u * 40))
        for k in range(20):
            a = rng.uniform(0, 6.28)
            r = 20 * seg(u, 0.1, 0.3) + rng.uniform(0, 10)
            c.rect(HX + r * math.cos(a), FY - 20 + r * math.sin(a), 2, 2, P['acc2'])
    D.float_text(c, P, '+FUNDING', HX, 70, u, 0.2, 0.7, P['acc3'])
    # first shot misses
    f = seg(u, 0.45, 0.7)
    if 0 < f < 1:
        c.rect(HX + 20 + (x - HX) * f, 100 - 30 * f, 5, 2, hot)
    D.float_text(c, P, 'MISS', x, 60, u, 0.62, 0.6, sub)
    D.float_text(c, P, 'ERROR!', x, 76, u, 0.68, 0.6, acc)
    # the error flows back
    g = seg(u, 0.72, 1.0)
    if 0 < g < 1:
        n = 40
        ts = np.linspace(0, 1, n)
        xs = x - 10 + (HX + 10 - x + 10) * ts
        ys = 90 - 40 * np.sin(np.pi * ts)
        dash = (np.arange(n) // 2) % 2 == 0
        c.points(xs[dash], ys[dash], acc, 0.7)
        k = int(g * n)
        c.rect(xs[min(k, n - 1)] - 1, ys[min(k, n - 1)] - 1, 4, 4, hot)
    # mini network above the hero, lit right to left
    if 0.7 < u < 1.3:
        ox, oy = HX, 52
        for l in range(2):
            for (ax, ay) in MINI_NET[l]:
                for (bx, by) in MINI_NET[l + 1]:
                    c.line(ox + ax, oy + ay, ox + bx, oy + by, P['dim'])
        for l, layer in enumerate(MINI_NET):
            lit = u > 0.9 + (2 - l) * 0.06
            for (ax, ay) in layer:
                c.rect(ox + ax - 1, oy + ay - 1, 3, 3, hot if lit else sub)
    D.slash(c, P, x - 8, FY - 30, u, 1.1)
    D.float_text(c, P, 'CRITICAL!', x, 66, u, 1.12, 0.6, hot, scale=2)
    D.float_text(c, P, '-999', x, 86, u, 1.14, 0.6, acc)
    return dict(dx=D.lunge(u, [0.42, 1.02]), pose='idle')


# ================================================================= 1997 — the chess king
def deepblue(c, P, u, s, era):
    ink, acc, hot = P['ink'], P['acc'], P['hot']
    x = _enter_x(u)
    lay = _layer()
    cols = _mcols(era, P, MON['king'])
    hit = any(t0 <= u < t0 + 0.06 for t0 in (0.55, 0.9, 1.18))
    topple = ease_in(seg(u, 1.2, 1.34))
    rows = S.CHESS_KING
    if topple > 0.5:
        rows = [''.join(r[i] for r in rows[::-1]) for i in range(len(rows[0]))]
    S.draw_sprite(lay, rows, x + (14 * topple), FY, cols, 4, silhouette=hot if hit else None)
    _mon(c, lay, u, 1.36, seed=97)
    hpv = 1 - 0.35 * (u >= 0.55) - 0.35 * (u >= 0.9) - 0.3 * (u >= 1.18)
    if u < 1.4:
        D.monster_bar(c, P, 'CHESS KING', x, 34, hpv, w=90)
    # the king strikes back
    f = seg(u, 0.86, 1.02)
    if 0 < f < 1:
        c.circle(x - 10, FY - 40, 10 + 80 * f, acc, alpha=1 - f)
    for t0, dmg in ((0.55, '-350'), (0.9, '-350')):
        D.slash(c, P, x - 18, FY - 40, u, t0)
        D.float_text(c, P, dmg, x - 10, 70, u, t0 + 0.02, 0.55, acc)
    D.float_text(c, P, 'CHECKMATE!', 290, 64, u, 1.1, 0.8, hot, scale=2)
    D.float_text(c, P, '3.5 - 2.5', 290, 92, u, 1.3, 0.7, ink)
    # knight's L-shaped hop
    dx = D.lunge(u, [0.42, 0.78, 1.06], dist=60, dur=0.3)
    dy = 0
    for t0 in (0.42, 0.78, 1.06):
        g = seg(u, t0, t0 + 0.3)
        if 0 < g < 1:
            dy = -26 * math.sin(math.pi * min(1, g * 1.6))
    pose = 'hurt' if 0.9 <= u < 1.02 else 'idle'
    return dict(dx=dx, dy=dy, pose=pose)


# ================================================================= 1998 — the scrawl wraith
def lenet(c, P, u, s, era):
    ink, acc, sub, dim, hot = P['ink'], P['acc'], P['sub'], P['dim'], P['hot']
    x = _enter_x(u)
    top = 44 + 4 * math.sin(u * 5)
    digit = A._digit_img(1.0)
    glyph = np.kron(digit > 0.4, np.ones((2, 2), bool))
    lay = _layer()
    S.ghost(lay, x, top, P, u, P['dim'] if era != 'paper' else P['panel'], glyph=None)
    lay.put_mask(glyph, x - 16, top + 18, P['ink'])
    _mon(c, lay, u, 1.2, seed=98)
    if u < 1.25:
        D.monster_bar(c, P, 'SCRAWL WRAITH', x, 32, 1 - seg(u, 1.05, 1.15))
    sc = seg(u, 0.35, 0.9)
    if 0 < sc < 1:
        k = int(sc * 196)
        sx, sy = k % 14, k // 14
        wx, wy = x - 16 + sx * 2, top + 18 + sy * 2
        c.frame(wx - 1, wy - 1, 8, 8, acc)
        c.line(HX + 8, FY - 30, wx, wy + 3, acc, alpha=0.5)
    # the network's verdict
    if u > 0.85:
        ox, oy = 170, 56
        c.rect(ox - 4, oy - 4, 96, 32, P['bg'])
        c.frame(ox - 4, oy - 4, 96, 32, dim)
        g = ease_out(seg(u, 0.85, 1.05))
        for d in range(10):
            hgt = int(20 * A._SCORES[d] * g)
            c.rect(ox + d * 9, oy + 20 - hgt, 6, hgt, acc if d == 5 else sub)
            c.tiny(str(d), ox + d * 9 + 1, oy + 22, ink if d == 5 else dim)
    D.float_text(c, P, "IT'S A 5!", x, 36, u, 1.02, 0.7, hot, scale=2)
    return dict(pose='idle')


# ================================================================= 2009 / 2012 — the image horde
HCOLS, HROWS = 33, 12
HX0, HY0 = 200, 46
_hr = np.random.default_rng(9)
_H_ORDER = _hr.permutation(HCOLS * HROWS)
_H_RANK = np.empty_like(_H_ORDER)
_H_RANK[_H_ORDER] = np.arange(len(_H_ORDER))
_H_BLINK = _hr.uniform(0, 6.28, HCOLS * HROWS)


def _horde(c, P, t, era, color, drift, eyes=True):
    greens = [P['faint'], P['dim'], P['sub'], P['ink']]
    pal = np.stack(greens)
    n_show = int(HCOLS * HROWS * ease_out(seg(t, 22.0, 22.5)))
    for idx in range(HCOLS * HROWS):
        if _H_RANK[idx] >= n_show:
            continue
        col, row = idx % HCOLS, idx // HCOLS
        x = int(HX0 + col * 8 - drift)
        y = int(HY0 + row * 8 + (1 if int(t * 6 + col) % 2 else 0))
        if x < 150 or x + 7 > W:
            continue
        tile = A.TILES[idx % len(A.TILES)]
        if color:
            c.a[y:y + 7, x:x + 7] = tile
        else:
            q = np.clip((A.TILE_LUM[idx % len(A.TILES)] * 4).astype(int), 0, 3)
            c.a[y:y + 7, x:x + 7] = pal[q]
        if eyes and math.sin(t * 3 + _H_BLINK[idx]) > -0.8:
            c.pset(x + 2, y + 2, hexc('#000000'))
            c.pset(x + 4, y + 2, hexc('#000000'))


def imagenet(c, P, u, s, era):
    t = s['t0'] + u
    color = era != 'green'
    _horde(c, P, t, era, color, drift=6 * u)
    for (t0, idx, lab) in ((0.35, 40, 'cat'), (0.55, 150, 'boat'), (0.8, 300, 'dog'), (1.0, 95, 'kite')):
        if u > t0:
            col, row = idx % HCOLS, idx // HCOLS
            x, y = HX0 + col * 8 - 6 * u - 1, HY0 + row * 8 - 1
            fc = P['acc'] if color else P['ink']
            c.frame(x, y, 9, 9, fc)
            wl = pf.text_width(lab) + 4
            c.rect(x, y - 10, wl, 10, fc)
            c.text(lab, x + 2, y - 9, P['bg'], n=int((u - t0) * 40))
    cnt = int(14_197_122 * ease_out(seg(u, 0.0, 1.1)))
    c.rect(HX0 + 60, 36, 200, 10, P['bg'])
    c.text('IMAGE HORDE ×{:,}'.format(cnt), 466, 37, P['ink'], bold=True, align='right')
    D.float_text(c, P, '!?', HX, 70, u, 0.45, 0.6, P['acc'], scale=2)
    return dict(pose='idle')


def alexnet(c, P, u, s, era):
    ink, acc, sub, dim, hot = P['ink'], P['acc'], P['sub'], P['dim'], P['hot']
    t = s['t0'] + u
    lay = _layer()
    _horde(lay, P, t, era, True, drift=6 * (u + 1.3))
    _mon(c, lay, u, 1.05, seed=12, dur=0.6)
    if u < 1.1:
        c.rect(HX0 + 60, 36, 200, 10, P['bg'])
        c.text('IMAGE HORDE ×14,197,122', 466, 37, ink, bold=True, align='right')
    # two GPUs drop in
    for k in range(2):
        f = seg(u, 0.02 + 0.08 * k, 0.28 + 0.08 * k)
        if 0 < f < 1:
            gy = 30 + (FY - 60) * ease_in(f)
            S.draw_sprite(c, S.GPU, HX - 20 + k * 40, gy, {'#': acc}, 1, anchor='top')
    D.float_text(c, P, '+2 GPU', HX, 66, u, 0.3, 0.7, acc)
    # the beam
    b = seg(u, 0.98, 1.2)
    if 0 < b < 1:
        yb = 92
        for d in range(-3, 4):
            c.line(HX + 22, yb + d, W, yb + d, hot if abs(d) < 2 else acc, alpha=1 - abs(d) / 4)
    # the scoreboard
    if u > 1.12:
        ox, oy = 250, 50
        a = seg(u, 1.12, 1.25)
        c.rect(ox - 6, oy - 6, 214, 46, P['bg'], a)
        c.frame(ox - 6, oy - 6, 214, 46, dim, a)
        c.tiny('TOP-5 ERROR', ox, oy - 1, sub, a)
        g = ease_out(seg(u, 1.15, 1.45))
        c.text('AlexNet', ox, oy + 8, ink, bold=True, alpha=a)
        c.rect(ox + 58, oy + 9, int(80 * g), 6, acc)
        if g >= 1:
            c.text('15.3%', ox + 142, oy + 8, acc, bold=True)
        c.text('runner-up', ox, oy + 21, sub, alpha=a)
        c.rect(ox + 58, oy + 22, int(137 * g), 6, dim)
        if g >= 1:
            c.text('26.2%', ox + 195, oy + 30, sub, align='right')
    return dict(pose='idle')


# ================================================================= 2014 — the doppelganger
def gan(c, P, u, s, era):
    ink, acc, acc2 = P['ink'], P['acc'], P['acc2']
    x = _enter_x(u, 400)
    lay = _layer()
    form = tl.form(s['t0'] + u)
    S.draw_sprite(lay, S.HERO[form], x, FY, _mcols(era, P, MON['shadow']), 2, flip=True)
    _mon(c, lay, u, 1.36, seed=14)
    rounds = [0.3, 0.55, 0.8, 1.05, 1.3]
    k = sum(1 for r in rounds if u >= r)
    if u < 1.4:
        D.monster_bar(c, P, 'DOPPELGANGER', x, 40, 1 - k / 5)
    fx, fy = 212, 50
    sigma = [1.0, 0.8, 0.55, 0.32, 0.14, 0.0][k]
    img = A._noisy(A.GAN_TARGET, sigma, k * 7 + 1) if sigma > 0 else A.GAN_TARGET
    if u > 0.12:
        c.a[fy:fy + 80, fx:fx + 80] = np.repeat(np.repeat(img, 2, 0), 2, 1)
        c.frame(fx - 2, fy - 2, 84, 84, ink)
        c.brackets(fx - 5, fy - 5, 90, 90, acc)
    for r in rounds:
        p = seg(u, r - 0.18, r)
        if 0 < p < 1:
            for j in range(5):
                q = clamp01(p * 1.3 - j * 0.07)
                c.rect(HX + 10 + (fx - HX - 10) * q, 100 + j * 2 + math.sin(q * 6) * 6, 2, 2, acc2)
        p2 = seg(u, r, r + 0.15)
        if 0 < p2 < 1:
            for j in range(5):
                q = clamp01(p2 * 1.3 - j * 0.07)
                c.rect(fx + 80 + (x - 10 - fx - 80) * q, 100 + j * 2 + math.sin(q * 6) * 6, 2, 2, acc)
    if 0 < k < 5:
        c.text('fake!', x, 66, hexc('#ff6a7a'), bold=True, align='center')
    D.float_text(c, P, 'REAL...?', x, 66, u, 1.3, 0.6, acc)
    c.tiny('G', HX - 3, FY + 4, acc2)
    if u < 1.4:
        c.tiny('D', x - 1, FY + 4, acc)
    return dict(pose='idle')


# ================================================================= 2016 — the go dragon
def _dragon_pts(u, x0):
    n = 16
    out = []
    for i in range(n):
        x = x0 + i * 13
        y = 96 + 26 * math.sin(i * 0.55 - u * 5) * (0.4 + 0.6 * i / n)
        out.append((x, y))
    return out


def alphago(c, P, u, s, era):
    ink, acc, sub, dim, hot = P['ink'], P['acc'], P['sub'], P['dim'], P['hot']
    x0 = _enter_x(u, 268)
    pts = _dragon_pts(u, x0)
    lay = _layer()
    for i in range(len(pts) - 1, -1, -1):
        x, y = pts[i]
        r = 7 if i else 11
        black = i % 2 == 0
        lay.disc(x, y, r + 1, sub)
        lay.disc(x, y, r, hexc('#0c0a22') if black else ink)
        if black:
            lay.pset(x - r * 0.4, y - r * 0.4, dim)
    hx, hy = pts[0]
    lay.rect(hx - 6, hy - 4, 3, 3, hexc('#ff5a4a'))
    lay.rect(hx + 1, hy - 4, 3, 3, hexc('#ff5a4a'))
    lay.line(hx - 6, hy - 11, hx - 10, hy - 18, sub)
    lay.line(hx + 4, hy - 11, hx + 8, hy - 18, sub)
    _mon(c, lay, u, 1.2, seed=16, dur=0.6)
    if u < 1.25:
        D.monster_bar(c, P, 'GO DRAGON', 360, 36, 1 - 0.1 * (u > 0.5) - 0.9 * seg(u, 1.08, 1.12), w=90)
    f = seg(u, 0.42, 0.55)
    if 0 < f < 1:
        c.disc(hx + (HX + 10 - hx) * f, hy + (FY - 30 - hy) * f, 4, hexc('#0c0a22'))
    D.float_text(c, P, '-14', HX, 80, u, 0.55, 0.5, hexc('#ff6a7a'))
    g = seg(u, 0.85, 1.08)
    if 0 < g < 1:
        sx = HX + 16 + (hx - HX - 16) * g
        sy = FY - 30 + (hy - FY + 30) * g - 40 * math.sin(math.pi * g)
        c.disc(sx, sy, 5, hexc('#0c0a22'))
        c.circle(sx, sy, 7, acc)
    if u >= 1.08:
        p = (u - 1.08) * 2 % 1
        c.circle(hx, hy, 10 + 20 * p, acc, alpha=1 - p)
    D.float_text(c, P, 'MOVE 37!', 300, 60, u, 1.08, 0.8, acc, scale=2)
    D.float_text(c, P, '4-1', HX, 64, u, 1.3, 0.6, hot, scale=2)
    return dict(pose='hurt' if 0.55 <= u < 0.68 else 'idle', dx=D.lunge(u, [0.8], dist=18))


# ================================================================= 2017 — the word swarm
TOKENS = ['Attention', 'Is', 'All', 'You', 'Need']


def transformer(c, P, u, s, era):
    ink, acc, dim, hot = P['ink'], P['acc'], P['dim'], P['hot']
    cols = [P['acc'], P['acc2'], P['acc3'], hexc('#9b6bff'), P['acc']]
    shift = (1 - ease_out(seg(u, 0, tl.WALK))) * 70
    boxes = []
    x = 226 + shift
    lay = _layer()
    for k, tok in enumerate(TOKENS):
        w = pf.text_width(tok, bold=True) + 8
        y = 116 - 12 * math.sin(k * 1.3 + u * 3) - (k % 2) * 16
        lay.rect(x, y, w, 15, P['panel'])
        lay.frame(x, y, w, 15, dim)
        lay.text(tok, x + 4, y + 4, ink, bold=True)
        lay.rect(x + w // 2 - 4, y - 3, 2, 2, hexc('#ff5a4a'))
        lay.rect(x + w // 2 + 2, y - 3, 2, 2, hexc('#ff5a4a'))
        boxes.append((x + w / 2, y))
        x += w + 8
    _mon(c, lay, u, 1.32, seed=17)
    if u < 1.35:
        D.monster_bar(c, P, 'WORD SWARM', 350, 38, 1 - seg(u, 0.9, 1.25), w=90)
    if 0.85 < u < 1.34:
        k = 0
        for i in range(5):
            for j in range(i + 1, 5):
                (x0, y0), (x1, y1) = boxes[i], boxes[j]
                p = ease_out(seg(u, 0.85 + 0.025 * k, 1.05 + 0.025 * k))
                n = 50
                ts = np.linspace(0, p, n)
                xs = x0 + (x1 - x0) * ts
                ys = min(y0, y1) - 3 - (14 + (x1 - x0) * 0.35) * 4 * ts * (1 - ts)
                c.points(xs, ys, cols[i], 0.4 + 0.6 * A._ARCW[i, j])
                k += 1
        for (bx, by) in boxes:
            c.line(HX + 20, 100, bx, by + 7, hot, alpha=0.35)
    D.float_text(c, P, 'ATTENTION!', 350, 56, u, 0.85, 0.7, acc, scale=2)
    return dict(pose='idle')


# ================================================================= 2020 — GPT-3 and AlphaFold
def gpt3(c, P, u, s, era):
    ink, acc, acc2, acc3 = P['ink'], P['acc'], P['acc2'], P['acc3']
    e = ease_in(seg(u, 0.2, 1.0))
    gx, gy = 320 + (HX - 320) * e, 92 + (FY - 22 - 92) * e
    th = A._G_R / 92 * 4.2 + A._G_ARM * math.pi + A._G_JIT + u * 2.5
    r = A._G_R * 1.6 * (1 - 0.88 * e) + 2
    xs = gx + r * np.cos(th)
    ys = gy + r * np.sin(th) * 0.45
    colsg = [hexc('#fff6d0'), acc2, acc, acc3]
    band = np.clip((A._G_R / 92 * 4).astype(int), 0, 3)
    for b in range(4):
        m = band == b
        tw = 0.5 + 0.5 * np.sin(u * 6 + A._G_TW[m])
        keep = tw > 0.25
        c.points(xs[m][keep], ys[m][keep], colsg[b])
    n = int(175_000_000_000 * ease_out(seg(u, 0.1, 0.9)))
    c.text('+{:,} PARAMS'.format(n), 300, 44, ink, bold=True, align='center')
    return dict(pose='idle')


def alphafold(c, P, u, s, era):
    acc, sub, acc2, acc3 = P['acc'], P['sub'], P['acc2'], P['acc3']
    f = ease_io(seg(u, 0.3, 1.0))
    shift = (1 - ease_out(seg(u, 0, tl.WALK))) * 70
    pos = A._LINEAR * (1 - f) + A._FOLD * 1.6 * f
    ang = u * 1.6 * f + 0.4 * f
    ca, sa = math.cos(ang), math.sin(ang)
    x = pos[:, 0] * ca + pos[:, 2] * sa
    z = -pos[:, 0] * sa + pos[:, 2] * ca
    y = pos[:, 1] + (1 - f) * 20 * np.sin(np.arange(len(x)) * 0.4 + u * 8)
    sx = 344 + shift + x * 1.05
    sy = 94 + y * 0.9
    n = len(A.SEQ)
    stops = [hexc('#ffe066'), acc2, acc, acc3]
    lay = _layer()
    for i in sorted(range(n - 1), key=lambda i: -(z[i] + z[i + 1])):
        q = i / (n - 1) * 3
        b = min(2, int(q))
        col = mix(stops[b], stops[b + 1], q - b)
        depth = clamp01(0.55 + (-(z[i] + z[i + 1]) / 2) / 60)
        cc = mix(P['bg'], col, 0.35 + 0.65 * depth)
        A.thick_line(lay, sx[i], sy[i], sx[i + 1], sy[i + 1], cc)
    lay.disc(sx[0], sy[0], 4, hexc('#ffe066'))
    if f < 0.2:
        lay.rect(sx[0] - 3, sy[0] - 2, 2, 2, hexc('#000000'))
        lay.rect(sx[0] + 1, sy[0] - 2, 2, 2, hexc('#000000'))
    if f < 0.35:
        for i in range(0, n, 2):
            lay.tiny(A.SEQ[i], sx[i] - 1, sy[i] - 12, sub)
    _mon(c, lay, u, 1.2, seed=20, dur=0.4)
    if u < 1.25:
        D.monster_bar(c, P, 'PROTEIN SERPENT', 344 + shift, 34, 1 - f, w=90)
    D.float_text(c, P, 'FOLDED!', 344, 64, u, 1.0, 0.7, P['hot'], scale=2)
    if 0.3 < u < 1.0:
        c.line(HX + 14, 96, 344 + shift, 94, acc, alpha=0.3)
    return dict(pose='idle')


# ================================================================= 2022 — ChatGPT and diffusion
def chatgpt(c, P, u, s, era):
    ink, acc, acc2, acc3 = P['ink'], P['acc'], P['acc2'], P['acc3']
    cx, cy = 300, 84
    cols = [acc, acc2, P['hot'], acc3]
    for k in range(A._NB):
        ph = (A._B_OFF[k] + u * A._B_SPD[k] * 0.9) % 1
        r0 = 10 + ph ** 1.6 * 260
        r1 = r0 + 6 + ph * 34
        a = A._B_ANG[k]
        y0 = cy + r0 * math.sin(a) * 0.6
        y1 = cy + r1 * math.sin(a) * 0.6
        if max(y0, y1) > D.FLOOR_Y:
            continue
        c.line(cx + r0 * math.cos(a), y0, cx + r1 * math.cos(a), y1, cols[A._B_COL[k]], alpha=0.35 + 0.65 * ph)
    punch = seg(u, 0.05, 0.2)
    if punch > 0:
        sc = 5 if punch < 1 else 4
        shake = int(3 * (1 - seg(u, 0.2, 0.6)) * math.sin(u * 90))
        c.text('ChatGPT', cx + 3 + shake, cy - 14 + 3, acc, bold=True, scale=sc, align='center')
        c.text('ChatGPT', cx + shake, cy - 14, ink, bold=True, scale=sc, align='center')
    rng = np.random.default_rng(22)
    crowd = [hexc(h) for h in ('#ff9ab8', '#ffd23d', '#7fd4ff', '#b8a8ff', '#8affb0', '#ffb347')]
    for k in range(70):
        side = 1 if k % 2 else -1
        t0 = 0.2 + rng.uniform(0, 0.8)
        f = ease_out(seg(u, t0, t0 + 0.5))
        if f <= 0:
            continue
        tx = HX + 40 + rng.uniform(-10, 330) if side > 0 else HX - 20 - rng.uniform(0, 90)
        sx = W + 10 if side > 0 else -10
        x = sx + (tx - sx) * f
        y = FY - 4 - rng.integers(0, 3) * 5 + (-1 if int(u * 10 + k) % 2 else 0)
        c.sprite(S.PERSON, x, y - 1, {'o': crowd[k % 6], 'b': crowd[(k + 2) % 6]})
    D.float_text(c, P, '+100,000,000 PLAYERS', 300, 130, u, 0.55, 1.0, acc3)
    return dict(pose='idle')


def diffusion(c, P, u, s, era):
    ink, acc, sub, dim = P['ink'], P['acc'], P['sub'], P['dim']
    x = _enter_x(u)
    fx, fy = int(x - 48), 38
    steps = 28
    k = int(seg(u, 0.45, 1.42) * steps)
    sigma = (1 - k / steps) ** 1.4
    if sigma > 0.001:
        r = np.random.default_rng(k + 5)
        img = A.LOTUS * (1 - sigma) + (128 + r.normal(0, 1, A.LOTUS.shape) * 90) * sigma
        img = np.clip(np.round(img / 42) * 42, 0, 255)
    else:
        img = A.LOTUS
    big = np.repeat(np.repeat(img, 2, 0), 2, 1)
    x0, x1 = max(0, fx), min(W, fx + 96)
    if x1 > x0:
        c.a[fy:fy + 96, x0:x1] = big[:, x0 - fx:x1 - fx]
    c.frame(fx - 2, fy - 2, 100, 100, sub if sigma < 0.01 else ink)
    if sigma > 0.25:
        a = clamp01((sigma - 0.25) / 0.5)
        c.rect(fx + 22, fy + 30, 12, 10, hexc('#ffe066'), a)
        c.rect(fx + 62, fy + 30, 12, 10, hexc('#ffe066'), a)
        for j in range(6):
            c.rect(fx + 24 + j * 9, fy + 64, 6, 8, hexc('#ffffff'), a)
        D.monster_bar(c, P, 'NOISE BEAST', x, 26 + 4, sigma, alpha=seg(u, 0.1, 0.2))
    else:
        c.brackets(fx - 5, fy - 5, 106, 106, acc)
    c.tiny('STEP %02d/%d' % (max(1, k), steps), fx + 104, fy + 2, sub)
    c.text('σ %.2f' % sigma, fx + 104, fy + 10, dim)
    prompt = '> a lotus at dusk'
    c.text(prompt, HX - 30, 60, ink, n=int(seg(u, 0.05, 0.4) * len(prompt)))
    D.float_text(c, P, 'PURIFIED!', x, 34, u, 1.42, 0.7, P['hot'], scale=2)
    if u > 1.5:
        c.text('out of the noise, a lotus', x, fy + 102 - 4, sub, align='center', n=int((u - 1.5) * 50))
    return dict(pose='idle')


# ================================================================= 2023 — the race, 2024 — the labyrinth
def frontier(c, P, u, s, era):
    ink, acc, acc2, acc3 = P['ink'], P['acc'], P['acc2'], P['acc3']
    names = [('Llama', acc3, 2), ('Claude', acc2, 1), ('GPT-4', acc, 0)]
    for (nm, col, k) in names:
        f = seg(u, 0.0, 1.4)
        x = -40 - k * 50 + f * (470 - k * 40)
        feet = FY - k * 6
        cols = {'o': mix(col, hexc('#000000'), 0.6), 'b': col, 'e': hexc('#ffffff'),
                's': col, 'h': col, 'a': col, 'g': col}
        bob = -2 if int(u * 14 + k) % 2 else 0
        S.draw_sprite(c, S.RUNNER, x, feet + bob, cols, 3)
        c.text(nm, x, feet - 40 + bob, col, bold=True, align='center')
        for j in range(3):
            c.rect(x - 12 - j * 6, feet - 2 - j, 2, 2, P['dim'], 0.8 - j * 0.25)
    D.float_text(c, P, 'RIVALS APPEAR!', 300, 50, u, 0.1, 0.9, ink)
    return dict(pose='idle', dx=8 * math.sin(u * 3))


def _maze(cols=15, rows=9, seed=24):
    rng = np.random.default_rng(seed)
    walls_r = np.ones((rows, cols), bool)
    walls_d = np.ones((rows, cols), bool)
    seen = np.zeros((rows, cols), bool)
    stack = [(rows // 2, 0)]
    seen[rows // 2, 0] = True
    while stack:
        r, c_ = stack[-1]
        nb = [(r + dr, c_ + dc) for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
              if 0 <= r + dr < rows and 0 <= c_ + dc < cols and not seen[r + dr, c_ + dc]]
        if not nb:
            stack.pop()
            continue
        nr, nc = nb[rng.integers(len(nb))]
        if nr == r:
            walls_r[r, min(c_, nc)] = False
        else:
            walls_d[min(r, nr), c_] = False
        seen[nr, nc] = True
        stack.append((nr, nc))
    # BFS from the entrance
    from collections import deque
    start, goal = (rows // 2, 0), (rows // 2, cols - 1)
    dist = {start: 0}
    prev = {}
    order = [start]
    q = deque([start])
    while q:
        r, c_ = q.popleft()
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nr, nc = r + dr, c_ + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or (nr, nc) in dist:
                continue
            if dr == 0 and walls_r[r, min(c_, nc)]:
                continue
            if dc == 0 and walls_d[min(r, nr), c_]:
                continue
            dist[(nr, nc)] = dist[(r, c_)] + 1
            prev[(nr, nc)] = (r, c_)
            order.append((nr, nc))
            q.append((nr, nc))
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return walls_r, walls_d, order, path[::-1]


MAZE = _maze()


def reasoning(c, P, u, s, era):
    ink, sub, hot = P['ink'], P['sub'], P['hot']
    walls_r, walls_d, order, path = MAZE
    rows, cols = walls_r.shape
    cs = 9
    shift = (1 - ease_out(seg(u, 0, tl.WALK))) * 70
    ox, oy = int(262 + shift), 52
    c.rect(ox - 4, oy - 4, cols * cs + 8, rows * cs + 8, P['panel'])
    nv = int(seg(u, 0.1, 0.8) * len(order))
    for (r, c_) in order[:nv]:
        c.rect(ox + c_ * cs + 1, oy + r * cs + 1, cs - 1, cs - 1, P['faint'])
    hp_ = seg(u, 0.8, 1.1)
    if hp_ > 0:
        pts = [(ox + c_ * cs + cs / 2, oy + r * cs + cs / 2) for (r, c_) in path]
        c.polyline(pts, P['hot'], t=hp_)
    for r in range(rows):
        for c_ in range(cols):
            x, y = ox + c_ * cs, oy + r * cs
            if walls_r[r, c_] and c_ < cols - 1:
                c.line(x + cs, y, x + cs, y + cs, sub)
            if walls_d[r, c_] and r < rows - 1:
                c.line(x, y + cs, x + cs, y + cs, sub)
    c.frame(ox, oy, cols * cs + 1, rows * cs + 1, ink)
    c.rect(ox, oy + (rows // 2) * cs + 1, 1, cs - 1, P['panel'])
    c.rect(ox + cols * cs, oy + (rows // 2) * cs + 1, 1, cs - 1, P['panel'])
    if u < 1.25:
        D.monster_bar(c, P, 'LABYRINTH', ox + cols * cs / 2, 34, 1 - hp_, w=90)
    # thought bubble
    bx, by = HX + 18, 58
    if u > 0.08:
        c.rect(bx, by, 30, 16, P['bg'])
        c.frame(bx, by, 30, 16, sub)
        c.pset(bx + 2, by + 18, sub)
        c.pset(bx, by + 21, sub)
        txt = '.' * (1 + int(u * 6) % 3) if u < 0.82 else '!'
        c.text(txt, bx + 15, by + 4, hot if txt == '!' else ink, bold=True, align='center')
    for k in range(2):
        f = seg(u, 1.05 + 0.08 * k, 1.35 + 0.08 * k)
        if f > 0:
            y = 40 + (FY - 52) * ease_out(f) - 10 * abs(math.sin(f * 6)) * (1 - f)
            S.medal(c, HX + 38 + k * 16, y)
    D.float_text(c, P, '+2 NOBEL', HX + 46, 60, u, 1.3, 0.6, hot)
    return dict(pose='idle')


# ================================================================= 2025-26 — the bug swarm
TASKS = ['read the repo', 'write the fix', 'run the tests', 'open a PR']
TASK_T = [0.75, 1.45, 2.3, 3.05]
CODE = [[(2, 'k'), (6, 'i'), (10, 'v')], [(4, 'i'), (5, 'k'), (8, 'v'), (4, 'i')],
        [(6, 'i'), (12, 's'), (3, 'i')], [(4, 'k'), (9, 'i')], [(6, 'i'), (5, 'k'), (10, 's')],
        [(8, 'c')], [(4, 'k'), (7, 'v'), (6, 'i')], [(6, 'i'), (4, 'k'), (11, 'v')], [(10, 'i'), (6, 's')]]
BUG_T = [(0.55, 0.95), (0.7, 1.2), (0.85, 1.5), (1.0, 1.8), (1.15, 2.1), (1.3, 2.4)]


def agents(c, P, u, s, era):
    ink, acc, sub, dim, faint, green = P['ink'], P['acc'], P['sub'], P['dim'], P['faint'], P['acc2']
    wx, wy, ww, wh = 218, 38, 248, 104
    open_ = ease_out(seg(u, 0.05, 0.3))
    close = ease_in(seg(u, 3.65, 3.9))
    hh = int(wh * open_ * (1 - close))
    if hh > 2:
        yy = wy + (wh - hh) // 2
        c.rect(wx + 3, yy + 3, ww, hh, faint)
        c.rect(wx, yy, ww, hh, hexc('#fbf8f2'))
        c.frame(wx, yy, ww, hh, ink)
    if open_ >= 1 and close <= 0:
        c.rect(wx + 1, wy + 1, ww - 2, 10, P['panel'])
        c.line(wx, wy + 11, wx + ww - 1, wy + 11, ink)
        for k, col in enumerate((acc, dim, dim)):
            c.disc(wx + 6 + k * 7, wy + 5, 2, col)
        c.tiny('QUEST LOG · AGENT SESSION', wx + ww // 2 + 10, wy + 3, sub, align='center')
        split = wx + 124
        c.line(split, wy + 12, split, wy + wh - 1, faint)
        colmap = {'k': acc, 'i': ink, 'v': hexc('#2b4a6f'), 's': green, 'c': dim}
        nch = (u - 0.3) * 40
        y = wy + 16
        done = 0
        for line in CODE:
            x = wx + 6
            for (L, kind) in line:
                show = max(0, min(L, nch - done))
                if show > 0:
                    c.rect(x, y + 1, int(show * 3) - 1, 3, colmap[kind])
                done += L
                x += L * 3 + 3
            y += 7
            if nch <= done:
                break
        if u > 2.45:
            c.line(wx + 1, wy + 80, split - 1, wy + 80, faint)
            c.text('$ run tests', wx + 5, wy + 84, sub, n=int((u - 2.45) * 40))
            if u > 2.7:
                c.text('14 passed ✓', wx + 5, wy + 93, green, bold=True, n=int((u - 2.7) * 40))
        for k, task in enumerate(TASKS):
            ty = wy + 17 + k * 13
            c.frame(split + 6, ty, 7, 7, ink)
            dn = u >= TASK_T[k]
            c.text(task, split + 17, ty, ink if dn else dim)
            if dn:
                c.text('✓', split + 7, ty - 1, acc, bold=True)
        bx, by = split + 30, wy + 76
        pressed = 2.25 <= u < 2.4
        c.rect(bx, by + pressed, 40, 13, acc if not pressed else hexc('#8a2a20'))
        c.text('RUN', bx + 20, by + 3 + pressed, hexc('#fbf8f2'), bold=True, align='center')
    # bugs crawl out and get zapped
    for k, (ta, tz) in enumerate(BUG_T):
        if u < ta:
            continue
        f = seg(u, ta, ta + 1.2)
        bx0 = wx + 30 + k * 30
        x = bx0 - (bx0 - HX - 40) * f * 0.8
        y = FY if f > 0.15 else wy + wh + (FY - wy - wh) * f / 0.15
        lay = _layer()
        S.draw_sprite(lay, S.BUG, x, y, _mcols(era, P, MON['bug']), 2)
        _mon(c, lay, u, tz, seed=k)
        g = seg(u, tz - 0.15, tz)
        if 0 < g < 1:
            px = HX + 22 + (x - HX - 22) * g
            c.sprite(A.CURSOR, px, FY - 30 + (y - 8 - FY + 30) * g, {'#': acc, 'o': hexc('#fbf8f2')})
        D.float_text(c, P, 'FIXED', x, FY - 30, u, tz, 0.5, green)
    D.float_text(c, P, 'QUEST COMPLETE!', HX + 20, 58, u, 3.2, 0.9, acc)
    return dict(pose='idle', dx=D.lunge(u, [tz - 0.18 for (ta, tz) in BUG_T], dist=10, dur=0.15))


FUNCS = {
    'neuron': neuron, 'turing': turing, 'dartmouth': dartmouth, 'perceptron': perceptron,
    'eliza': eliza, 'winter': winter, 'backprop': backprop, 'deepblue': deepblue,
    'lenet': lenet, 'imagenet': imagenet, 'alexnet': alexnet, 'gan': gan, 'alphago': alphago,
    'transformer': transformer, 'gpt3': gpt3, 'alphafold': alphafold, 'chatgpt': chatgpt,
    'diffusion': diffusion, 'frontier': frontier, 'reasoning': reasoning, 'agents': agents,
}
FLOORS = {'deepblue': 'chess'}
