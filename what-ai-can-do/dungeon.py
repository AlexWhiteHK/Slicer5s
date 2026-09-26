"""The dungeon stage: scrolling walls per era, the hero, battle UI helpers."""
import math
import numpy as np

from gfx import W, hexc, mix, seg, ease_out, ease_io, clamp01
import sprites as S
import timeline as tl

STAGE_TOP, FLOOR_Y, STAGE_BOT = 30, 146, 168
HERO_X = 112
MON_X = 344

# ------------------------------------------------------------------ scroll
_WALK_STARTS = [s['t0'] for s in tl.SCENES]


def scroll(t):
    s = 0.0
    for t0 in _WALK_STARTS:
        s += 70 * ease_io(seg(t, t0, t0 + tl.WALK))
    return s


def walking(t):
    return any(t0 <= t < t0 + tl.WALK for t0 in _WALK_STARTS)


# ------------------------------------------------------------------ walls
WALLS = {
    'paper':  dict(wall='#ece5d3', mortar='#b9ae98', hi='#f6f1e4', floor='#ddd4bf', edge='#1c1a16',
                   seam='#b9ae98', ceil='#1c1a16', flame='#b1352a', glow=0.0),
    'winter': dict(wall='#12264e', mortar='#0a1634', hi='#24427a', floor='#1c3a70', edge='#9fd4ff',
                   seam='#0a1634', ceil='#0a1634', flame='#9fd4ff', glow=0.25),
    'amber':  dict(wall='#120900', mortar='#4a2c04', hi='#2a1802', floor='#1a0e02', edge='#ffb42a',
                   seam='#4a2c04', ceil='#2a1802', flame='#ffe7a0', glow=0.35),
    'green':  dict(wall='#020d05', mortar='#0c4a20', hi='#06260f', floor='#031408', edge='#46ff86',
                   seam='#0c4a20', ceil='#06260f', flame='#d2ffe0', glow=0.35),
    'neon':   dict(wall='#120d38', mortar='#2a2170', hi='#1c1650', floor='#0e0a2c', edge='#3de0ff',
                   seam='#2a2170', ceil='#08061c', flame='#ff4fd8', glow=0.4),
    'synth':  dict(wall='#260a2e', mortar='#4a1a4c', hi='#361040', floor='#1c0622', edge='#ff5fa2',
                   seam='#4a1a4c', ceil='#12031a', flame='#ffb347', glow=0.4),
    'clean':  dict(wall='#f1ece2', mortar='#ddd5c6', hi='#f8f5ee', floor='#e6dfd1', edge='#1c1a16',
                   seam='#cfc6b4', ceil='#1c1a16', flame='#b1352a', glow=0.0),
}
WALLS = {k: {kk: (hexc(v) if isinstance(v, str) else v) for kk, v in d.items()} for k, d in WALLS.items()}

_yy, _xx = np.mgrid[STAGE_TOP:FLOOR_Y, 0:W]
_fy, _fx = np.mgrid[FLOOR_Y:STAGE_BOT, 0:W]


def stage(c, era, P, t, floor='tiles'):
    Wc = WALLS[era]
    s = scroll(t)
    # bricks
    xs = (_xx + s * 0.6).astype(int)
    row = (_yy - STAGE_TOP) // 11
    mort = ((_yy - STAGE_TOP) % 11 == 0) | ((xs + (row % 2) * 13) % 26 == 0)
    hi = ((_yy - STAGE_TOP) % 11 == 1) & ~mort
    reg = c.a[STAGE_TOP:FLOOR_Y]
    reg[:] = Wc['wall']
    reg[hi] = Wc['hi']
    reg[mort] = Wc['mortar']
    # pillars with torches
    px0 = -((s * 0.6) % 170)
    for k in range(4):
        px = int(px0 + k * 170 + 60)
        if -30 < px < W + 30:
            c.rect(px - 8, STAGE_TOP, 16, FLOOR_Y - STAGE_TOP, mix(Wc['wall'], Wc['ceil'], 0.35))
            c.rect(px - 8, STAGE_TOP, 1, FLOOR_Y - STAGE_TOP, Wc['mortar'])
            c.rect(px + 7, STAGE_TOP, 1, FLOOR_Y - STAGE_TOP, Wc['mortar'])
            c.rect(px - 10, STAGE_TOP + 6, 20, 4, Wc['mortar'])
            c.rect(px - 10, FLOOR_Y - 8, 20, 8, Wc['mortar'])
            _torch(c, px, 76, t + k, Wc, P, era)
    # ceiling
    c.rect(0, STAGE_TOP, W, 5, Wc['ceil'])
    c.rect(0, STAGE_TOP + 5, W, 1, Wc['mortar'])
    if era == 'winter':
        rng = np.random.default_rng(3)
        for k in range(24):
            x = (rng.uniform(0, W + 40) - s * 0.6) % (W + 40) - 20
            L = int(rng.uniform(4, 14))
            for j in range(L):
                w = max(1, 3 - j * 3 // L)
                c.rect(x - w // 2, STAGE_TOP + 6 + j, w, 1, hexc('#bfe4ff'))
    # floor
    fl = c.a[FLOOR_Y:STAGE_BOT]
    fs = (_fx + s).astype(int)
    if floor == 'chess':
        chk = ((fs // 22) + ((_fy - FLOOR_Y) // 11)) % 2 == 0
        fl[:] = Wc['floor']
        fl[chk] = mix(Wc['floor'], Wc['edge'], 0.35)
    else:
        fl[:] = Wc['floor']
        fl[(fs % 32 == 0)] = Wc['seam']
        fl[(_fy - FLOOR_Y) == 11] = Wc['seam']
    c.rect(0, FLOOR_Y, W, 1, Wc['edge'])
    c.rect(0, FLOOR_Y + 1, W, 1, mix(Wc['floor'], Wc['edge'], 0.3))


def _torch(c, x, y, t, Wc, P, era):
    c.rect(x - 2, y, 4, 8, Wc['mortar'])
    c.rect(x - 4, y - 1, 8, 2, Wc['edge'] if era in ('amber', 'green') else Wc['mortar'])
    fl = int(t * 12) % 3
    flame = [['.#.', '###', '.#.'], ['#..', '##.', '###', '.#.'], ['..#', '.##', '###', '.#.']][fl]
    col = Wc['flame']
    for j, r in enumerate(flame):
        for i, ch in enumerate(r):
            if ch == '#':
                c.rect(x - 3 + i * 2, y - 2 - (len(flame) - j) * 2, 2, 2, col)
    if Wc['glow'] > 0:
        for r in (10, 16):
            c.disc(x, y - 6, r, col, alpha=Wc['glow'] * (0.5 if r == 16 else 0.35) * (0.8 + 0.2 * math.sin(t * 17)))
        c.rect(x - 1, y - 6, 2, 2, hexc('#ffffff'))


# ------------------------------------------------------------------ hero
def hp(t):
    ks = tl.HP_KEYS
    for (a, va), (b, vb) in zip(ks, ks[1:]):
        if a <= t < b:
            return va + (vb - va) * (t - a) / (b - a)
    return ks[-1][1]


def _colors(P, era, form):
    return S.role_colors(P, era, S.SCHEME[form])


def draw_hero(c, P, era, t, dx=0, dy=0, pose='idle', x=None, feet=None, scale=3, alpha=1.0):
    x = HERO_X if x is None else x
    feet = FLOOR_Y if feet is None else feet
    bob = 0
    if walking(t):
        bob = -1 if int(t * 12) % 2 else 0
    elif int(t * 2.2) % 2 == 0:
        bob = -1
    X, Y = x + dx, feet + dy + bob
    # evolution: flicker between old and new silhouettes
    for (te, name) in tl.EVOLVE:
        if te <= t < te + tl.EVOLVE_DUR:
            f = (t - te) / tl.EVOLVE_DUR
            prev = S.FORMS[S.FORMS.index(name) - 1]
            period = 0.16 * (1 - f) + 0.03
            show_new = int((t - te) / period) % 2 == 1
            cur = name if show_new else prev
            S.draw_sprite(c, S.HERO[cur], X, Y, None, scale, silhouette=P['hot'] if era not in ('paper', 'clean') else P['ink'])
            for k in range(10):
                a = k * 0.628 + t * 4
                r = 40 * (1 - f) + 8
                c.rect(X + r * math.cos(a), Y - 26 + r * math.sin(a) * 0.7, 2, 2, P['hot'])
            return
        if te + tl.EVOLVE_DUR <= t < te + tl.EVOLVE_DUR + 0.45:
            f = (t - te - tl.EVOLVE_DUR) / 0.45
            c.circle(X, Y - 26, 12 + 44 * f, P['hot'], alpha=1 - f)
            c.circle(X, Y - 26, 10 + 34 * f, P['acc'], alpha=1 - f)
    form = tl.form(t)
    rows = S.HERO[form]
    cols = _colors(P, era, form)
    if pose == 'hurt' and int(t * 20) % 2 == 0:
        S.draw_sprite(c, rows, X, Y, None, scale, silhouette=P['hot'], alpha=alpha)
    else:
        S.draw_sprite(c, rows, X, Y, cols, scale, alpha=alpha)
    if pose == 'frozen':
        w, h = S.sprite_size(rows, scale)
        c.rect_blend(X - w // 2 - 5, Y - h - 6, w + 10, h + 6, hexc('#9fd4ff'), 0.45)
        c.frame(X - w // 2 - 5, Y - h - 6, w + 10, h + 6, hexc('#eaf6ff'))
        c.line(X - w // 2 - 2, Y - h - 3, X - w // 2 + 6, Y - h - 3, hexc('#ffffff'))
        c.line(X - w // 2 - 2, Y - h - 3, X - w // 2 - 2, Y - h + 6, hexc('#ffffff'))
    if form == 'FOUNDATION TITAN':
        rng = np.random.default_rng(5)
        for k in range(22):
            a = rng.uniform(0, 6.28) + t * rng.uniform(0.5, 1.5)
            r = rng.uniform(36, 46)
            c.pset(X + r * math.cos(a), Y - 32 + r * math.sin(a) * 0.6, P['acc'] if k % 2 else P['hot'], 0.8)


def lunge(u, times, dist=34, dur=0.26):
    """Forward dash-and-return offset for attacks at local times `times`."""
    dx = 0.0
    for t0 in times:
        f = seg(u, t0, t0 + dur)
        if 0 < f < 1:
            dx = max(dx, dist * math.sin(math.pi * f) ** 0.7)
    return dx


# ------------------------------------------------------------------ battle UI
def float_text(c, P, text, x, y, u, t0, dur=0.8, color=None, scale=1, bold=True, align='center'):
    f = seg(u, t0, t0 + dur)
    if f <= 0 or f >= 1:
        return
    pop = 1 if f > 0.08 else 2
    yy = y - 14 * ease_out(f)
    a = 1 - seg(f, 0.7, 1.0)
    col = P['hot'] if color is None else color
    sc = scale * (2 if (pop == 2 and scale == 1) else 1)
    c.text(text, x + 1, yy + 1, P['bg'], scale=sc, bold=bold, align=align, alpha=a)
    c.text(text, x, yy, col, scale=sc, bold=bold, align=align, alpha=a)


def monster_bar(c, P, name, x, y, hp_, alpha=1.0, w=64):
    if alpha <= 0:
        return
    c.text(name, x, y, P['ink'], bold=True, align='center', alpha=alpha)
    bx = int(x - w / 2)
    c.rect(bx - 1, y + 10, w + 2, 5, P['bg'], alpha)
    c.frame(bx - 1, y + 10, w + 2, 5, P['dim'], alpha)
    col = hexc('#e0503d') if hp_ < 0.35 else (P['acc'] if P is not None else None)
    c.rect(bx, y + 11, int(w * clamp01(hp_)), 3, col, alpha)


def encounter(c, P, u, x, y, t0=0.0):
    """A '!' pop when a monster appears."""
    f = seg(u, t0, t0 + 0.35)
    if 0 < f < 1:
        c.text('!', x, y - 6 * math.sin(math.pi * f), P['acc'], bold=True, scale=2, align='center')


def slash(c, P, x, y, u, t0, color=None, size=18):
    f = seg(u, t0, t0 + 0.16)
    if 0 < f < 1:
        col = P['hot'] if color is None else color
        a = -0.9 + 1.8 * f
        for k in range(3):
            r = size - k * 3
            c.line(x + r * math.cos(a + 2.2), y + r * math.sin(a + 2.2), x + r * math.cos(a), y + r * math.sin(a), col)
        c.circle(x, y, size * 0.6 * f + 2, col, alpha=1 - f)


def spark_hit(c, P, x, y, u, t0, n=10, color=None):
    f = seg(u, t0, t0 + 0.3)
    if 0 < f < 1:
        rng = np.random.default_rng(int(t0 * 100) + int(x))
        col = P['hot'] if color is None else color
        for k in range(n):
            a = rng.uniform(0, 6.28)
            r = 4 + 26 * f * rng.uniform(0.5, 1)
            c.rect(x + r * math.cos(a), y + r * math.sin(a), 2, 2, col, 1 - f)
