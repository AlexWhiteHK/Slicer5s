"""Pixel sprites: the evolving AI hero and the dungeon's monsters.

Sprites are ASCII grids of colour roles:
  o outline   b body   s shade   h highlight   a accent   e eye/glow   g glow
Roles are mapped to real colours per era, so 1-bit and phosphor eras draw the
same sprite in their own limited palette.
"""
import math
import numpy as np

from gfx import W, H, hexc, mix

# ------------------------------------------------------------------ hero forms
FORMS = ['SPARK', 'PERCEPTRON', 'NEURAL KNIGHT', 'DEEP SEER', 'TRANSFORMER DRAKE',
         'FOUNDATION TITAN', 'AGENT']

HERO = {
    'SPARK': [
        '...g.....g...',
        '....o...o....',
        '.....ooo.....',
        '....obhbo....',
        'g..obebebo..g',
        '.ooobbbbbooo.',
        '...obbsbbo...',
        '....osbso....',
        '.....ooo.....',
        '....o...o....',
        '...g.....g...',
    ],
    'PERCEPTRON': [
        '.....g.....',
        '.....o.....',
        '...ooooo...',
        '..obbhbbo..',
        '.obbbbbhbo.',
        '.obebbbebo.',
        '.obbbbbbbo.',
        '.obbsasbbo.',
        '..osbbbso..',
        '...ooooo...',
        '...o...o...',
        '..oo...oo..',
    ],
    'NEURAL KNIGHT': [
        '......aa........',
        '.....aaoo....h..',
        '.....oooooo..h..',
        '....obbbbbbo.h..',
        '....obhbbbbo.h..',
        '....oeeeeeeo.h..',
        '....obbbbbbo.h..',
        '.....oooooo..h..',
        '..ooo.obbo..aaa.',
        '.obbbooobbooobo.',
        '.obabobbbbbbbo..',
        '.obaaobsbbsbo...',
        '.obabobbbbbbo...',
        '..ooo.obbbbo....',
        '......osbbso....',
        '......ob..bo....',
        '.....obb..bbo...',
        '.....ooo..ooo...',
    ],
    'DEEP SEER': [
        '............ggg.',
        '......ooo...gag.',
        '.....obbbo..ggg.',
        '....obbhbbo..o..',
        '...obbbbbbbo.o..',
        '...obossssbo.o..',
        '...obseesebo.o..',
        '...obsssssbo.o..',
        '..obbbbbbbbbooo.',
        '..obbabbbbabbo..',
        '.obbbabbbbbabo..',
        '.obbbbaaaaabbo..',
        '.obbbbbbbbbbbo..',
        '.obsbbbbbbbbso..',
        '.obssbbbbbbsso..',
        'obbssbbbbbbssbo.',
        'ooooooooooooooo.',
    ],
    'TRANSFORMER DRAKE': [
        '.......o................',
        '......oao...............',
        '.....oaaao..........ooo.',
        '....oaaaaao........obbbo',
        '...oaaaaaaao......obebbo',
        '..oaaaaaaaaao....obbbbho',
        '...ooaaaaaaoo...obbbooo.',
        '.....ooaaaoboo.obbbo....',
        '.......oobbbbbobbbo.....',
        '.....ooobbbbbbbbbo......',
        '...oobbbbhhbbbbbo.......',
        '..obbbbbbbbbbbbso.......',
        '.obbo.obssbbbssbo.......',
        '.obo..obo.ooobo.o.......',
        '..o...obo...obo.........',
        '.....oobo..oobo.........',
        '.....ooo...ooo..........',
    ],
    'FOUNDATION TITAN': [
        '.......gggggg.......',
        '......g......g......',
        '........oooo........',
        '.......obbbbo.......',
        '.......obebeo.......',
        '.......obbbbo.......',
        '........oooo........',
        '....ooooobboooooo...',
        '...obbbbbbbbbbbbbo..',
        '..obbhbbbabbabbbbbo.',
        '..obobbbbaaabbbbobo.',
        '..obobbbbbabbbbbobo.',
        '..ob.obbbbbbbbbo.bo.',
        '..ob.obsbbbbbsbo.bo.',
        '..oa.obbbbbbbbbo.ao.',
        '..g..obbbbbbbbbo..g.',
        '.....obbbo.obbbo....',
        '.....obbbo.obbbo....',
        '.....obbbo.obbbo....',
        '....obbbbo.obbbbo...',
        '....oooooo.oooooo...',
    ],
    'AGENT': [
        '......oooo..........',
        '.....obbbbo.........',
        '....obbhbbbo........',
        '....oeeeeeeo........',
        '....obbbbbbo........',
        '.....oooooo.........',
        '..aaaaobbo......o...',
        'aaaaaaaoooooo...oo..',
        '..aa.obbbbbbboo.oho.',
        '.....obbhbbbbbooohho',
        '.....obbbbbbbbo.ohhh',
        '.....obbsbbbbo..ohho',
        '.....obbbbbbo...o.oo',
        '......obbbbo........',
        '......osbbso........',
        '......ob..bo........',
        '......ob..bo........',
        '.....obb..bbo.......',
        '.....ooo..ooo.......',
    ],
}

SCHEME = {   # full-colour roles per form (used from the 16-bit era on)
    'SPARK': dict(o='#2a1a08', b='#ffe066', s='#e0a030', h='#fff6c0', a='#ff7a5a', e='#2a1a08', g='#fff1a0'),
    'PERCEPTRON': dict(o='#0e2238', b='#7fd4ff', s='#3a8ac8', h='#e0f6ff', a='#ff5fa2', e='#0e2238', g='#bff0ff'),
    'NEURAL KNIGHT': dict(o='#161a2a', b='#c8d0e0', s='#7a84a0', h='#ffffff', a='#ff5a4a', e='#3de0ff', g='#ffffff'),
    'DEEP SEER': dict(o='#140c34', b='#6a4cff', s='#3a2a9a', h='#b8a8ff', a='#3de0ff', e='#7ffcff', g='#bff8ff'),
    'TRANSFORMER DRAKE': dict(o='#082a22', b='#3de0a0', s='#1a8a6a', h='#c8ffe8', a='#ff4fd8', e='#ffe066', g='#ffb0f0'),
    'FOUNDATION TITAN': dict(o='#3a2408', b='#ffd23d', s='#c89a2a', h='#fff4c0', a='#ff5fa2', e='#ffffff', g='#ffe9a0'),
    'AGENT': dict(o='#1c1a16', b='#f5f1e8', s='#a39a88', h='#ffffff', a='#b1352a', e='#b1352a', g='#ff8a6a'),
}

_mask_cache = {}


def _masks(rows):
    key = tuple(rows)
    if key in _mask_cache:
        return _mask_cache[key]
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, '.') for r in rows]
    out = {}
    for ch in set(''.join(rows)):
        if ch == '.':
            continue
        out[ch] = np.array([[c == ch for c in r] for r in rows], dtype=bool)
    _mask_cache[key] = (out, w, len(rows))
    return _mask_cache[key]


def role_colors(P, era, scheme=None):
    """Map roles to colours for this era."""
    if era == 'paper':
        return dict(o=P['ink'], b=hexc('#fbf7ee'), s=P['dim'], h=hexc('#ffffff'),
                    a=P['acc'], e=P['ink'], g=P['acc'])
    if era in ('winter', 'amber', 'green', 'term'):
        return dict(o=mix(P['bg'], P['faint'], 0.3), b=P['sub'], s=P['dim'], h=P['ink'],
                    a=P['acc'], e=P['hot'], g=P['hot'])
    sch = scheme or SCHEME['AGENT']
    return {k: hexc(v) for k, v in sch.items()}


def draw_sprite(c, rows, x, y, colors, scale=2, alpha=1.0, flip=False, silhouette=None,
                anchor='bottom'):
    if colors is None and silhouette is None:
        return
    """x = horizontal centre, y = feet (anchor bottom) or top."""
    masks, w, h = _masks(rows)
    x0 = int(round(x - w * scale / 2))
    y0 = int(round(y - h * scale)) if anchor == 'bottom' else int(round(y))
    for ch, m in masks.items():
        if flip:
            m = m[:, ::-1]
        if scale != 1:
            m = np.kron(m, np.ones((scale, scale), bool))
        col = silhouette if silhouette is not None else colors.get(ch)
        if col is None:
            continue
        c.put_mask(m, x0, y0, col, alpha)
    return x0, y0, w * scale, h * scale


def sprite_size(rows, scale=2):
    _, w, h = _masks(rows)
    return w * scale, h * scale


# ------------------------------------------------------------------ monsters (ASCII)
SLIME = ['..ooo..', '.obbbo.', 'obebebo', 'obbbbbo', 'obbsbbo', 'ooooooo']
BUG = ['o.....o', '.o...o.', '..ooo..', '.obbbo.', 'obebebo', 'obbabbo', '.obbbo.', 'o.o.o.o']
CHESS_KING = [
    '......o......',
    '.....oho.....',
    '....oohhoo...',
    '......o......',
    '....ooooo....',
    '...obbbbbo...',
    '..obbebebbo..',
    '..obbbbbbbo..',
    '...obsasbo...',
    '....obbbo....',
    '...obbbbbo...',
    '...obhbbbo...',
    '..obbbbbbbo..',
    '.obbbbbbbbbo.',
    'ooooooooooooo',
]
ELIZA_NPC = [
    '.ooooooooooo.',
    'obbbbbbbbbbbo',
    'ob.........bo',
    'ob..e...e..bo',
    'ob.........bo',
    'ob...aaa...bo',
    'ob.........bo',
    'obbbbbbbbbbbo',
    '.ooooooooooo.',
    '.....obo.....',
    '...ooooooo...',
    '..obbbbbbbo..',
    '..ooooooooo..',
]
DUMMY = [
    '....ooooo....',
    '..oobbbbboo..',
    '.obbaaaaabbo.',
    '.obaabbbaabo.',
    'obbabbabbabbo',
    'obbabbbbbabbo',
    '.obaabbbaabo.',
    '.obbaaaaabbo.',
    '..oobbbbboo..',
    '....ooooo....',
    '......o......',
    '....ooooo....',
    '.....obo.....',
    '.....obo.....',
    '.....obo.....',
    '...ooooooo...',
]
RUNNER = ['..ooo..', '.obbbo.', '.obebo.', '..ooo..', '.obbbo.', 'obbbbbo', '.obbbo.', '.ob.bo.', 'oo...oo']
PERSON = ['.o.', 'obo', '.o.', 'obo', 'o.o']


# ------------------------------------------------------------------ procedural monsters
def chest(c, cx, feet, P, open_=0.0, scale=2, cols=None, teeth=True):
    """A treasure chest; open_ in [0,1] lifts the lid."""
    s = scale
    wv, hv = 16 * s, 9 * s
    x0, y0 = cx - wv // 2, feet - hv
    o, b, a, h = cols['o'], cols['b'], cols['a'], cols['h']
    c.rect(x0, y0, wv, hv, o)
    c.rect(x0 + s, y0 + s, wv - 2 * s, hv - 2 * s, b)
    c.rect(x0 + s, y0 + 3 * s, wv - 2 * s, s, o)
    c.rect(cx - s, y0 + s * 2, 2 * s, 3 * s, a)
    lid_h = 6 * s
    lift = int(open_ * 8 * s)
    ly = y0 - lid_h - lift
    if open_ > 0:
        c.rect(x0 + s, y0 - lift, wv - 2 * s, lift + s, hexc('#1a0808'))
        if teeth:
            for k in range(0, wv - 2 * s, 3 * s):
                c.rect(x0 + s + k, y0 - lift, 2 * s, s * 2, hexc('#fff4e0'))
                c.rect(x0 + s + k + s, y0 - 2 * s, 2 * s, s * 2, hexc('#fff4e0'))
            c.rect(cx - 5 * s, y0 - lift + 3 * s, 2 * s, 2 * s, hexc('#ffe066'))
            c.rect(cx + 3 * s, y0 - lift + 3 * s, 2 * s, 2 * s, hexc('#ffe066'))
            c.rect(cx - s, y0 - s, 2 * s, lift // 2 + s, hexc('#e0506a'))
    c.rect(x0, ly, wv, lid_h, o)
    c.rect(x0 + s, ly + s, wv - 2 * s, lid_h - 2 * s, b)
    c.rect(x0 + s, ly + s, wv - 2 * s, s, h)
    c.rect(cx - s, ly + lid_h - 2 * s, 2 * s, 2 * s, a)


def ice_golem(c, cx, feet, P, t, rise=1.0):
    blocks = [(-20, 0, 40, 26), (-26, -30, 52, 32), (-16, -52, 32, 22), (-40, -26, 14, 30),
              (26, -26, 14, 30), (-22, 0, 16, 18), (6, 0, 16, 18)]
    ice, ice2, hi = hexc('#9fd4ff'), hexc('#5f98d8'), hexc('#eaf6ff')
    off = int((1 - rise) * 70)
    for (dx, dy, w, h) in blocks:
        x, y = cx + dx, feet + dy - 18 + off
        if dy == 0 and w == 16:
            y = feet - 18 + off
        c.rect(x, y - h + 18, w, h, ice2)
        c.rect(x + 2, y - h + 20, w - 4, h - 6, ice)
        c.rect(x + 2, y - h + 20, w - 4, 2, hi)
    ey = feet - 76 + off
    glow = 0.6 + 0.4 * math.sin(t * 9)
    c.rect(cx - 9, ey, 5, 4, hexc('#ffffff'), glow)
    c.rect(cx + 4, ey, 5, 4, hexc('#ffffff'), glow)
    for k in range(5):
        c.line(cx - 12 + k * 6, feet - 62 + off, cx - 12 + k * 6 + 2, feet - 56 + off, hi)


def ghost(c, cx, top, P, t, body, glyph=None, alpha=1.0):
    w, h = 44, 56
    x0 = cx - w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx - w / 2) ** 2 + (yy - 22) ** 2 < 22 ** 2) | ((yy >= 22) & (yy < h - 6))
    wave = (np.sin(xx / 4 + t * 10) * 3 + h - 6)
    m &= yy < wave
    c.put_mask(m, x0, top, body, alpha)
    edge = m & ~np.roll(m, 1, 0) | m & ~np.roll(m, -1, 1)
    c.put_mask(edge, x0, top, P.get('hot', body), alpha * 0.8)
    c.rect(cx - 10, top + 16, 5, 7, hexc('#10081a'), alpha)
    c.rect(cx + 5, top + 16, 5, 7, hexc('#10081a'), alpha)
    if glyph is not None:
        c.put_mask(glyph, cx - glyph.shape[1] // 2, top + 26, P['acc'], alpha)


def medal(c, x, y, a=1.0):
    c.line(x - 3, y - 9, x, y - 1, hexc('#3d6ae0'), a)
    c.line(x + 3, y - 9, x, y - 1, hexc('#e0503d'), a)
    c.disc(x, y + 4, 6, hexc('#ffd23d'), a)
    c.disc(x, y + 4, 3, hexc('#c89a2a'), a)
    c.pset(x - 2, y + 2, hexc('#fff4c0'), a)


GPU = ['################', '#..............#', '#.####....####.#', '#.#..#....#..#.#',
       '#.####....####.#', '#..............#', '################', '.#.#.#.#.#.#.#..']


# ------------------------------------------------------------------ burst
def burst(c, layer, f, seed=0, cx=None, cy=None, power=70):
    """Explode the non-transparent pixels of `layer` outward (f in 0..1)."""
    ys, xs = np.nonzero(layer.a[..., 0] >= 0)
    if len(xs) == 0:
        return
    cols = layer.a[ys, xs]
    if cx is None:
        cx, cy = xs.mean(), ys.mean()
    rng = np.random.default_rng(seed)
    ang = np.arctan2(ys - cy, xs - cx) + rng.normal(0, 0.5, len(xs))
    sp = rng.uniform(0.3, 1.0, len(xs)) * power
    nx = xs + np.cos(ang) * sp * f
    ny = ys + np.sin(ang) * sp * f + 90 * f * f
    keep = rng.random(len(xs)) > f * 0.9
    nx, ny, cols = nx[keep], ny[keep], cols[keep]
    ix, iy = np.round(nx).astype(int), np.round(ny).astype(int)
    ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    c.a[iy[ok], ix[ok]] = cols[ok]
