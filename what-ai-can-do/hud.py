"""Era palettes, backgrounds and the persistent HUD (ruler, year odometer,
text log, skill hotbar, unlock pop-ups)."""
import math
import numpy as np

import gfx
from gfx import W, H, hexc, seg, ease_out, ease_io, clamp01
import pixfont as pf
import timeline as tl

# ------------------------------------------------------------------ palettes
def _p(**kw):
    return {k: hexc(v) for k, v in kw.items()}

PAL = {
    'term':   _p(bg='#07080a', ink='#ece6d8', sub='#8c877c', dim='#4a4740', faint='#16171a',
                 acc='#e0503c', acc2='#ece6d8', acc3='#ece6d8', panel='#101114', hot='#ffffff'),
    'paper':  _p(bg='#ece5d3', ink='#1c1a16', sub='#5e574a', dim='#8f8674', faint='#d8cfba',
                 acc='#b1352a', acc2='#2b4a6f', acc3='#1c1a16', panel='#e2dac6', hot='#b1352a'),
    'winter': _p(bg='#081230', ink='#eef5ff', sub='#a9c3ea', dim='#5a77a8', faint='#1a2c58',
                 acc='#8fd0ff', acc2='#cfe8ff', acc3='#ffffff', panel='#112046', hot='#ffffff'),
    'amber':  _p(bg='#0c0600', ink='#ffb42a', sub='#c9861a', dim='#6e4507', faint='#2a1802',
                 acc='#ffe7a0', acc2='#ff8a1a', acc3='#fff4d6', panel='#1c0f01', hot='#fff4d6'),
    'green':  _p(bg='#010803', ink='#46ff86', sub='#2cc463', dim='#137034', faint='#062a12',
                 acc='#d2ffe0', acc2='#9dff7a', acc3='#eafff0', panel='#03150a', hot='#eafff0'),
    'neon':   _p(bg='#0b0826', ink='#f3f0ff', sub='#a9a2e8', dim='#5a52a6', faint='#1f1850',
                 acc='#3de0ff', acc2='#ff4fd8', acc3='#ffd23d', panel='#151040', hot='#ffffff'),
    'synth':  _p(bg='#1c0724', ink='#fff0f6', sub='#e0a0c4', dim='#94507a', faint='#3a1240',
                 acc='#ff5fa2', acc2='#ffb347', acc3='#9b6bff', panel='#2a0b30', hot='#ffe066'),
    'clean':  _p(bg='#f5f1e8', ink='#1c1a16', sub='#5e574a', dim='#a39a88', faint='#e4ddcf',
                 acc='#b1352a', acc2='#2e6b4f', acc3='#1c1a16', panel='#ebe5d8', hot='#b1352a'),
    'dusk':   _p(bg='#0d0b18', ink='#f5f1e8', sub='#c9bfae', dim='#7d7466', faint='#2a2330',
                 acc='#b1352a', acc2='#e98a3c', acc3='#f5f1e8', panel='#1c1a16', hot='#ff7a4a'),
}

POST = {
    'term':   dict(bloom=0.55, grid=0.10, scan=0.18, vignette=0.65),
    'paper':  dict(bloom=0.0, grid=0.05, scan=0.0, vignette=0.35),
    'winter': dict(bloom=0.50, grid=0.08, scan=0.05, vignette=0.55),
    'amber':  dict(bloom=0.85, grid=0.14, scan=0.30, vignette=0.65),
    'green':  dict(bloom=0.85, grid=0.14, scan=0.30, vignette=0.65),
    'neon':   dict(bloom=0.60, grid=0.08, scan=0.06, vignette=0.55),
    'synth':  dict(bloom=0.70, grid=0.08, scan=0.04, vignette=0.55),
    'clean':  dict(bloom=0.0, grid=0.04, scan=0.0, vignette=0.22),
    'dusk':   dict(bloom=0.55, grid=0.06, scan=0.02, vignette=0.55),
}


# ------------------------------------------------------------------ backgrounds
_rng = np.random.default_rng(7)
_SNOW = np.stack([_rng.uniform(0, W, 260), _rng.uniform(0, H, 260),
                  _rng.uniform(8, 30, 260), _rng.uniform(0, 6.28, 260),
                  _rng.integers(0, 3, 260)], axis=1)
_STARS = np.stack([_rng.uniform(0, W, 200), _rng.uniform(0, H, 200),
                   _rng.uniform(0, 6.28, 200), _rng.uniform(1, 4, 200),
                   _rng.uniform(-6, 6, 200)], axis=1)
_PAPER_NOISE = _rng.random((H, W))
_DOTGRID = np.zeros((H, W), bool)
_DOTGRID[::6, ::6] = True

FLAKE5 = np.array([[c == '#' for c in r] for r in
                   ['#.#.#', '.###.', '#####', '.###.', '#.#.#']], dtype=bool)
FLAKE7 = np.array([[c == '#' for c in r] for r in
                   ['...#...', '.#.#.#.', '..###..', '#######', '..###..', '.#.#.#.', '...#...']],
                  dtype=bool)


def bg_term(c, P, t):
    c.a[:] = P['bg']
    c.a[_PAPER_NOISE < 0.03] = P['faint']


def bg_paper(c, P, t, clean=False):
    c.a[:] = P['bg']
    if not clean:
        c.a[_PAPER_NOISE < 0.06] = P['panel']
        c.a[_PAPER_NOISE > 0.994] = P['faint']
    c.a[_DOTGRID] = P['faint']


def draw_snow(c, P, t, alpha=1.0, big=True):
    for (x0, y0, sp, ph, kind) in _SNOW:
        y = (y0 + sp * t) % (H + 12) - 6
        x = (x0 + 6 * math.sin(t * 0.9 + ph)) % W
        if kind == 0:
            c.pset(x, y, P['ink'], alpha)
        elif kind == 1:
            c.pset(x, y, P['sub'], alpha)
            c.pset(x + 1, y, P['sub'], alpha * 0.6)
        elif big:
            c.put_mask(FLAKE5, x - 2, y - 2, P['acc2'], alpha * 0.9)


def bg_winter(c, P, t):
    c.vgrad([hexc('#040818'), hexc('#0a1636'), hexc('#162a5a')])
    for (cx, cy, r) in ((40, 30, 26), (455, 250, 30), (470, 20, 18), (20, 240, 16)):
        _flake(c, cx, cy, r, P['faint'], rot=t * 0.1)
    draw_snow(c, P, t)


def bg_crt(c, P, t, grid=False):
    c.a[:] = P['bg']
    band = (t * 80) % (H + 60) - 30
    ys = np.arange(H)
    m = np.abs(ys - band) < 18
    c.a[m] = gfx.mix(P['bg'], P['faint'], 0.45)
    if grid:
        c.a[::16, :][:, ::2] = P['faint']
        c.a[:, ::16][::2, :] = P['faint']
    c.a[_PAPER_NOISE < 0.02] = P['faint']


def bg_neon(c, P, t):
    c.vgrad([hexc('#05041a'), hexc('#0c0930'), hexc('#1a1250')])
    for (x0, y0, ph, sp, dr) in _STARS:
        tw = 0.5 + 0.5 * math.sin(t * sp + ph)
        x = (x0 + dr * t) % W
        col = P['acc'] if ph > 5 else P['sub']
        c.pset(x, y0, col, 0.25 + 0.6 * tw)


def bg_synth(c, P, t):
    c.vgrad([hexc('#10031a'), hexc('#1f0828'), hexc('#3a0d34'), hexc('#4a1236')])
    for (x0, y0, ph, sp, dr) in _STARS[:120]:
        tw = 0.5 + 0.5 * math.sin(t * sp + ph)
        x = (x0 + dr * t * 1.5) % W
        y = (y0 - 4 * t) % H
        col = P['acc'] if ph > 4 else P['dim']
        c.pset(x, y, col, 0.2 + 0.5 * tw)


def _flake(c, cx, cy, r, color, rot=0.0, alpha=1.0, t=1.0):
    for k in range(6):
        a = rot + k * math.pi / 3
        ex, ey = cx + r * math.cos(a) * t, cy + r * math.sin(a) * t
        c.line(cx, cy, ex, ey, color, alpha)
        for f, L in ((0.38, 0.36), (0.62, 0.30), (0.84, 0.18)):
            if t < f:
                continue
            bx, by = cx + r * f * math.cos(a), cy + r * f * math.sin(a)
            for s in (-1, 1):
                b = a + s * math.pi / 3
                ll = r * L * min(1, (t - f) / 0.15)
                c.line(bx, by, bx + ll * math.cos(b), by + ll * math.sin(b), color, alpha)


# ------------------------------------------------------------------ icons (9x9)
ICONS_SRC = {
    'LEARN': ['.......##', '.......##', '....##.##', '....##.##', '.##.##.##',
              '.##.##.##', '.##.##.##', '.........', '#########'],
    'TALK': ['.........', '.#######.', '#.......#', '#.#.#.#.#', '#.......#',
             '.#######.', '..##.....', '.#.......', '.........'],
    'PLAY': ['...###...', '..#####..', '...###...', '....#....', '...###...',
             '...###...', '..#####..', '.#######.', '.#######.'],
    'READ': ['.........', '.###.###.', '#...#...#', '#.#.#.#.#', '#...#...#',
             '#.#.#.#.#', '#...#...#', '.###.###.', '.........'],
    'SEE': ['.........', '.........', '..#####..', '.#.....#.', '#..###..#',
            '#..###..#', '.#.....#.', '..#####..', '.........'],
    'IMAGINE': ['....#....', '....#....', '...###...', '..#####..', '#########',
                '..#####..', '...###...', '....#....', '....#....'],
    'INTUIT': ['.###.....', '#####....', '#####....', '.###.....', '....###..',
               '...#...#.', '...#...#.', '...#...#.', '....###..'],
    'ATTEND': ['..#####..', '.#.....#.', '#..###..#', '..#...#..', '.#.....#.',
               '.........', '#.#.#.#.#', '.........', '.........'],
    'WRITE': ['.......##', '......###', '.....###.', '....###..', '...###...',
              '..###....', '.###.....', '#.#......', '##.......'],
    'FOLD': ['.##...##.', '#..#.#..#', '....#....', '#..#.#..#', '.##...##.',
             '#..#.#..#', '....#....', '#..#.#..#', '.##...##.'],
    'CHAT': ['#####....', '#...#....', '#...#....', '#####....', '.#.#####.',
             '...#...#.', '...#...#.', '...#####.', '......#..'],
    'DRAW': ['#########', '#.....#.#', '#.......#', '#...#...#', '#..###..#',
             '#.#####.#', '#########', '.........', '.........'],
    'REASON': ['..#####..', '.#.....#.', '#.......#', '#...#...#', '.#..#..#.',
               '..#.#.#..', '...###...', '...###...', '....#....'],
    'CODE': ['#########', '#.......#', '#.#.....#', '#..#....#', '#.#.....#',
             '#...###.#', '#.......#', '#########', '.........'],
    'ACT': ['#........', '##.......', '###......', '####.....', '#####....',
            '######...', '###......', '#.##.....', '...##....'],
}
ICONS = {k: np.array([[c == '#' for c in r] for r in v], dtype=bool)
         for k, v in ICONS_SRC.items()}

SLOT = 13
PITCH = 14
HOT_X0 = 466 - len(tl.SKILLS) * PITCH + 1
HOT_Y = 251

UNLOCKS = tl.unlock_events()
_first_unlock = {}
for (t_, n_, l_) in UNLOCKS:
    _first_unlock.setdefault(n_, t_)
_levelups = [(t_, n_, l_) for (t_, n_, l_) in UNLOCKS if l_ > 1]
ICON_FLY = 0.42


def slot_xy(i, layout=None):
    if layout is None:
        return HOT_X0 + i * PITCH, HOT_Y
    return layout(i)


def skill_count(t):
    return sum(1 for (tt, n, l) in UNLOCKS if l == 1 and tt + ICON_FLY <= t)


def draw_hotbar(c, P, t, era, alpha=1.0, layout=None, scale=1, pop_times=None):
    """Draw the skill slots. layout(i)->(x,y) overrides positions (question scene)."""
    frozen = era == 'winter'
    for i, name in enumerate(tl.SKILLS):
        x, y = slot_xy(i, layout)
        s = SLOT * scale
        tu = _first_unlock.get(name, 99)
        arrived = t >= tu + ICON_FLY
        pop = 1.0
        if pop_times is not None:
            pop = seg(t, pop_times[i], pop_times[i] + 0.12)
            if pop <= 0:
                c.frame(x, y, s, s, P['faint'], alpha)
                continue
        if arrived:
            c.rect(x, y, s, s, P['panel'], alpha)
            c.frame(x, y, s, s, P['dim'], alpha)
            col = P['acc2'] if frozen else P['ink']
            flash = seg(t, tu + ICON_FLY, tu + ICON_FLY + 0.25)
            if 0 < flash < 1:
                c.rect(x, y, s, s, P['hot'], alpha * (1 - flash))
            if pop_times is not None:
                col = P['ink'] if pop >= 1 else P['hot']
            m = ICONS[name]
            if scale != 1:
                m = np.kron(m, np.ones((scale, scale), bool))
            c.put_mask(m, x + 2 * scale, y + 2 * scale, col, alpha)
            if frozen:
                rng = np.random.default_rng(i)
                for _ in range(6):
                    c.pset(x + rng.integers(1, s - 1), y + rng.integers(1, s - 1), P['ink'], alpha)
            lv = max([l for (tt, n, l) in UNLOCKS if n == name and tt + ICON_FLY <= t] + [1])
            if lv > 1:
                c.rect(x + s - 5 * scale, y - 1, 5 * scale, 7 * scale, P['acc'], alpha)
                c.tiny(str(lv), x + s - 4 * scale, y, P['bg'], alpha, scale=scale)
        else:
            c.frame(x, y, s, s, P['faint'] if era not in ('paper', 'clean') else P['dim'], alpha * 0.9)
            c.pset(x + s // 2, y + s // 2, P['dim'], alpha)


def draw_unlock_popups(c, P, t, era):
    for (tu, name, lvl) in UNLOCKS:
        if not (tu - 0.01 <= t <= tu + 1.25):
            continue
        u = t - tu
        label = ('NEW SKILL  ' + name) if lvl == 1 else (name + '  LV ' + str(lvl))
        tw = pf.text_width(label, bold=True)
        bx, by = HOT_X0, 229
        bw = tw + 22
        grow = ease_out(seg(u, 0, 0.12))
        fade = 1 - seg(u, 1.0, 1.25)
        if fade <= 0:
            continue
        w_now = max(2, int(bw * grow))
        c.rect(bx, by, w_now, 13, P['acc'], fade)
        if grow >= 1:
            c.put_mask(ICONS[name], bx + 3, by + 2, P['bg'], fade)
            c.text(label, bx + 16, by + 3, P['bg'], bold=True, alpha=fade,
                   n=int((u - 0.1) * 40))
        i = tl.SKILLS.index(name)
        sx, sy = slot_xy(i)
        f = seg(u, 0.12, ICON_FLY)
        if lvl == 1 and 0 < f < 1:
            e = ease_io(f)
            x = bx + 3 + (sx + 2 - bx - 3) * e
            y = by + 2 + (sy + 2 - by - 2) * e - 18 * math.sin(math.pi * e)
            c.put_mask(ICONS[name], x, y, P['hot'])
            for k in range(1, 4):
                e2 = ease_io(max(0, f - 0.06 * k))
                x2 = bx + 3 + (sx + 2 - bx - 3) * e2
                y2 = by + 2 + (sy + 2 - by - 2) * e2 - 18 * math.sin(math.pi * e2)
                c.pset(x2 + 4, y2 + 4, P['acc'], 1 - 0.25 * k)
        if 0.3 < u < 0.7:
            rng = np.random.default_rng(int(tu * 100))
            for k in range(10):
                a = rng.uniform(0, 6.28)
                r = (u - 0.3) * 60 * rng.uniform(0.5, 1)
                c.pset(sx + 6 + r * math.cos(a), sy + 6 + r * math.sin(a), P['hot'], 1 - (u - 0.3) / 0.4)


def draw_skill_counter(c, P, t, alpha=1.0):
    n = skill_count(t)
    s = 'SKILLS %02d/%02d' % (n, len(tl.SKILLS))
    c.tiny(s, 466, 243, P['sub'], alpha, align='right')


# ------------------------------------------------------------------ ruler
R_X0, R_X1, R_Y = 16, 464, 11
Y0, Y1 = 1940, 2030


def year_x(y):
    return R_X0 + (y - Y0) / (Y1 - Y0) * (R_X1 - R_X0)


def draw_ruler(c, P, t, yv, alpha=1.0):
    c.line(R_X0, R_Y, R_X1, R_Y, P['faint'] if P is not PAL['paper'] else P['dim'], alpha)
    xv = year_x(yv)
    c.line(R_X0, R_Y, xv, R_Y, P['sub'], alpha)
    for yr in range(Y0, Y1 + 1, 10):
        x = year_x(yr)
        c.line(x, R_Y - 2, x, R_Y, P['dim'], alpha)
        c.tiny(str(yr), x, 3, P['dim'] if yr > yv else P['sub'], alpha, align='center')
    for s in tl.SCENES:
        if s['t0'] <= t:
            x = year_x(s['year'])
            c.pset(x, R_Y + 1, P['ink'], alpha)
            c.pset(x, R_Y + 2, P['ink'], alpha)
    c.put_mask(np.array([[1, 1, 1, 1, 1], [0, 1, 1, 1, 0], [0, 0, 1, 0, 0]], bool),
               xv - 2, R_Y - 5, P['acc'], alpha)


def draw_header(c, P, t, alpha=1.0):
    c.text(tl.INTRO_Q, 16, 19, P['sub'], alpha=alpha)
    if int(t * 2.5) % 2 == 0:
        w = pf.text_width(tl.INTRO_Q)
        c.rect(16 + w + 2, 19, 4, 7, P['acc'], alpha)


# ------------------------------------------------------------------ year odometer
YEAR_X, YEAR_Y, YEAR_S = 16, 206, 6
YEAR_EVENTS = tl.year_events()


def year_value(t):
    v = None
    for (te, a, b) in YEAR_EVENTS:
        if t < te:
            break
        f = ease_out(seg(t, te, te + tl.YEAR_ROLL))
        v = a + (b - a) * f
    return v


_DIG = {d: pf.glyph(str(d))[:7] for d in range(10)}


def _digit_strip(d, off, style):
    """Rows of a rolling digit: offset in [0,1) moves to the next digit."""
    g0 = _DIG[d % 10]
    g1 = _DIG[(d + 1) % 10]
    gap = np.zeros((2, 5), bool)
    strip = np.concatenate([g0, gap, g1], axis=0)
    r0 = int(round(off * 9))
    return strip[r0:r0 + 7]


def draw_year(c, P, t, era, alpha=1.0, v=None):
    if v is None:
        v = year_value(t)
    if v is None:
        return
    S = YEAR_S
    iv = int(math.floor(v + 1e-6))
    frac = v - iv
    digits = []
    for k in (3, 2, 1, 0):
        d = (iv // 10 ** k) % 10
        low = iv % (10 ** k) if k > 0 else 0
        off = frac if (k == 0 or low == 10 ** k - 1) else 0.0
        digits.append((d, off))
    led = era in ('amber', 'green', 'winter', 'term')
    for i, (d, off) in enumerate(digits):
        x = YEAR_X + i * 6 * S
        g = _digit_strip(d, off, era)
        if led:
            # LED matrix: every cell drawn, lit cells bright
            cell = np.zeros((S, S), bool)
            cell[:S - 1, :S - 1] = True
            full = np.kron(np.ones((7, 5), bool), cell)
            c.put_mask(full, x, YEAR_Y, P['faint'], alpha)
            m = np.kron(g, cell)
            c.put_mask(m, x, YEAR_Y, P['ink'], alpha)
        else:
            m = np.kron(g, np.ones((S, S), bool))
            if era in ('neon', 'synth', 'dusk'):
                c.put_mask(m, x + 2, YEAR_Y + 2, P['acc2'] if era == 'neon' else P['acc'], alpha)
            elif era in ('paper', 'clean'):
                c.put_mask(m, x + 2, YEAR_Y + 2, P['faint'], alpha)
            c.put_mask(m, x, YEAR_Y, P['ink'], alpha)


# ------------------------------------------------------------------ text log
TXT_X = 16
TITLE_Y, SUB_Y0, SUB_DY = 170, 182, 10


def draw_textlog(c, P, t, scenes_in_era, alpha=1.0):
    idx = [i for i, s in enumerate(tl.SCENES)]
    for i, s in enumerate(tl.SCENES):
        if s not in scenes_in_era:
            continue
        if t < s['t0']:
            continue
        nxt = tl.SCENES[i + 1]['t0'] if i + 1 < len(tl.SCENES) else tl.QUESTION_T0
        if t > nxt + 0.35:
            continue
        out = seg(t, nxt, nxt + 0.3)
        dy = -int(round(26 * ease_out(out)))
        a = alpha * (1 - out)
        if a <= 0:
            continue
        nsub = len(s['sub'])
        base = TITLE_Y + (2 - nsub) * SUB_DY
        for (li, ts, n, cps) in tl.text_events(s):
            k = int((t - ts) * cps)
            if k <= 0:
                continue
            if li == 0:
                c.text(s['title'], TXT_X, base + dy, P['ink'], bold=True, n=k, alpha=a)
                if k < n:
                    w = pf.text_width(s['title'][:k], bold=True)
                    c.rect(TXT_X + w + 1, base + dy, 5, 7, P['acc'], a)
            else:
                c.text(s['sub'][li - 1], TXT_X, base + 12 + (li - 1) * SUB_DY + dy,
                       P['sub'], n=k, alpha=a)
