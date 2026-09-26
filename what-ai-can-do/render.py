"""Frame compositor + encoder.

  python3 render.py video out.mp4          # render all frames (no audio)
  python3 render.py stills DIR t1 t2 ...   # full-res PNGs at given times
  python3 render.py sheet out.png t0 t1 n  # contact sheet of n frames
"""
import math
import os
import subprocess
import sys
import multiprocessing as mp

import numpy as np
from PIL import Image

import gfx
from gfx import W, H, seg, ease_io, ease_out, BAYER
import hud
import battles
import dungeon
import ending
import timeline as tl
import pixfont as pf

ERA_NAMES = [e[0] for e in tl.ERAS]


def era_at(t):
    for (n, a, b) in tl.ERAS:
        if a <= t < b:
            return n
    return tl.ERAS[-1][0]


def era_neighbors(tc):
    for i, (n, a, b) in enumerate(tl.ERAS):
        if abs(a - tc) < 1e-6:
            return tl.ERAS[i - 1][0], n
    raise ValueError(tc)


def _layer():
    c = gfx.Canvas()
    c.a[:] = -1
    return c


def _stamp(dst, layer, alpha):
    m = layer.a[..., 0] >= 0
    if alpha < 1:
        m &= BAYER < alpha
    dst.a[m] = layer.a[m]


def render_era(era, t):
    P = hud.PAL[era]
    c = gfx.Canvas(P['bg'])
    if era == 'term':
        hud.bg_term(c, P, t)
        ending.intro(c, P, t)
        return c
    if era == 'dusk':
        ending.yunagi(c, P, t)
        return c

    # the dungeon floor for this era, with its encounters
    world = gfx.Canvas(P['bg'])
    active = [s for s in tl.SCENES if era in (s['era'], s.get('era2'))
              and -0.001 <= t - s['t0'] <= s['t1'] - s['t0'] + 0.22]
    floor = 'tiles'
    for s in active:
        if s['id'] in battles.FLOORS and t - s['t0'] >= 0:
            floor = battles.FLOORS[s['id']]
    dungeon.stage(world, era, P, t, floor=floor)
    hero = dict(show=t >= tl.BIRTH_T)
    primary = max([s for s in tl.SCENES if s['t0'] <= t], key=lambda s: s['t0'], default=None)
    for s in active:
        u = t - s['t0']
        dur = s['t1'] - s['t0']
        a = 1 - seg(u, dur - 0.04, dur + 0.2)
        lay = _layer()
        ret = battles.FUNCS[s['id']](lay, P, u, s, era) or {}
        _stamp(world, lay, a)
        if s is primary:
            hero.update(ret)
    if hero.pop('show', True):
        dungeon.draw_hero(world, P, era, t, **{k: v for k, v in hero.items() if k in ('dx', 'dy', 'pose')})
    for w in tl.wins():
        if w > tl.BIRTH_T:
            dungeon.float_text(world, P, 'LV UP!', dungeon.HERO_X, dungeon.FLOOR_Y - 64, t, w, 0.8, P['acc'])
    for (te, name) in tl.EVOLVE:
        dungeon.float_text(world, P, 'EVOLVING...', dungeon.HERO_X, 66, t, te, tl.EVOLVE_DUR, P['hot'])
        dungeon.float_text(world, P, name, dungeon.HERO_X, 66, t, te + tl.EVOLVE_DUR, 0.9, P['acc'])

    # HUD
    in_era = [s for s in tl.SCENES if era in (s['era'], s.get('era2'))]
    hud_a = 1 - seg(t, tl.QUESTION_T0, tl.QUESTION_T0 + 0.3)
    head_a = seg(t, 3.9, 4.2) * hud_a
    hud.draw_panel(world, P, era, alpha=1.0)
    yv = hud.year_value(t)
    hud.draw_ruler(world, P, t, yv if yv is not None else 1940, alpha=head_a)
    if t < 4.3:
        # the intro question travels to its header slot
        f = ease_io(seg(t, 3.85, 4.25))
        q = tl.INTRO_Q
        x0 = 240 - pf.text_width(q, bold=True) * 2 // 2
        x = x0 + (16 - x0) * f
        y = 116 + (19 - 116) * f
        if f < 0.6:
            world.text(q, x, y, P['ink'], bold=True, scale=2)
        else:
            world.text(q, x, y, P['sub'])
    else:
        hud.draw_header(world, P, t)
    hud.draw_year(world, P, t, era)
    hud.draw_textlog(world, P, t, in_era)
    if t >= 4.0:
        hud.draw_stats(world, P, t, era)
        hud.draw_hotbar(world, P, t, era, alpha=seg(t, 4.0, 4.4))
        hud.draw_skill_counter(world, P, t, alpha=seg(t, 4.0, 4.4))
        hud.draw_unlock_popups(world, P, t, era)
    if hud_a >= 1:
        return world
    # the closing question takes over the screen
    hud.bg_paper(c, P, t, clean=True)
    ending.question(c, P, t)
    lay = _layer()
    lay.a[:] = world.a
    _stamp(c, lay, hud_a)
    return c


def glitch(c, amount, seed):
    rng = np.random.default_rng(seed)
    out = c.copy()
    for _ in range(int(7 * amount) + 1):
        y = int(rng.integers(0, H))
        h = int(rng.integers(2, 20))
        dx = int(rng.integers(-30, 30) * amount)
        out.a[y:y + h] = np.roll(out.a[y:y + h], dx, axis=1)
    return out


def post_params(t):
    era = era_at(t)
    p = dict(hud.POST[era])
    extra = {}
    for (tc, kind, hw) in tl.TRANSITIONS:
        if tc - hw <= t < tc + hw:
            a, b = era_neighbors(tc)
            f = (t - (tc - hw)) / (2 * hw)
            pa, pb = hud.POST[a], hud.POST[b]
            p = {k: pa[k] * (1 - f) + pb[k] * f for k in pa}
            if kind in ('glitch', 'glitchdissolve'):
                extra['aberr'] = 6 * (1 - abs(f - 0.5) * 2)
            if kind == 'flash':
                extra['flash'] = 1 - abs(f - 0.5) * 2
            if kind == 'crt':
                extra['flash'] = max(0, 1 - abs(f - 0.5) * 8) * 0.8
    # accents
    if 34.0 <= t < 34.45:
        f = seg(t, 34.0, 34.45)
        extra['flash'] = max(extra.get('flash', 0), (1 - f) ** 2 * 0.85)
        extra['flash_color'] = (255, 200, 230)
        extra['shake'] = (int(4 * (1 - f) * math.sin(t * 120)), int(3 * (1 - f) * math.cos(t * 97)))
    for s in tl.SCENES:
        if s['era'] in ('neon', 'synth') and 0 <= t - s['t0'] < 0.1:
            extra['aberr'] = max(extra.get('aberr', 0), 4)
    if 47.95 - 0.4 <= t < 47.95 + 0.4:
        pass
    if t > 59.2:
        extra['brightness'] = 1 - seg(t, 59.2, 59.95)
    if t < 0.35:
        extra['brightness'] = seg(t, 0.0, 0.35)
    p.update(extra)
    return p


def render_frame(t):
    for (tc, kind, hw) in tl.TRANSITIONS:
        if tc - hw <= t < tc + hw:
            a_era, b_era = era_neighbors(tc)
            f = (t - (tc - hw)) / (2 * hw)
            A = render_era(a_era, t)
            B = render_era(b_era, t)
            if kind == 'wipe':
                return gfx.composite(A, B, gfx.wipe_mask(ease_io(f), 'diag', soft=60))
            if kind == 'dissolve':
                return gfx.composite(A, B, gfx.dissolve_mask(ease_io(f)))
            if kind == 'glitchdissolve':
                out = gfx.composite(A, B, gfx.dissolve_mask(ease_io(f)))
                return glitch(out, 1 - abs(f - 0.5) * 2, int(t * 1000))
            if kind == 'glitch':
                src = A if f < 0.5 else B
                return glitch(src, 1 - abs(f - 0.5) * 2, int(t * 1000))
            if kind == 'flash':
                return A if f < 0.5 else B
            if kind == 'flood':
                yy, xx = np.mgrid[0:H, 0:W]
                d = np.hypot(xx - 338, (yy - 130) * 1.3) / 330
                edge = ease_io(f) * 1.15
                m = BAYER < np.clip((edge - d) / 0.12, 0, 1)
                return gfx.composite(A, B, m)
            if kind == 'crt':
                blank = gfx.Canvas((0, 0, 0))
                ys = np.arange(H)[:, None].repeat(W, 1)
                if f < 0.5:
                    h = (1 - ease_io(f * 2)) * H / 2
                    m = np.abs(ys - H / 2) <= max(0.5, h)
                    out = gfx.composite(blank, A, m)
                    if h < 6:
                        out.a[int(H / 2) - 1:int(H / 2) + 1] = hud.PAL['amber']['acc']
                    return out
                h = ease_out((f - 0.5) * 2) * H / 2
                m = np.abs(ys - H / 2) <= max(0.5, h)
                out = gfx.composite(blank, B, m)
                if h < 8:
                    out.a[int(H / 2) - 1:int(H / 2) + 1] = hud.PAL['amber']['acc']
                return out
    return render_era(era_at(t), t)


def frame_rgb(i):
    t = i / tl.FPS
    c = render_frame(t)
    return gfx.post(c, **post_params(t))


def _worker(i):
    return i, frame_rgb(i).tobytes()


def ffmpeg_bin():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_video(out, start=0, end=None, procs=4):
    n_total = int(tl.DURATION * tl.FPS)
    end = n_total if end is None else end
    cmd = [ffmpeg_bin(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', '%dx%d' % (W * gfx.SCALE, H * gfx.SCALE), '-r', str(tl.FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.Pool(procs) as pool:
        for k, (i, buf) in enumerate(pool.imap(_worker, range(start, end), chunksize=2)):
            p.stdin.write(buf)
            if k % 60 == 0:
                print('frame', i, '/', end, flush=True)
    p.stdin.close()
    p.wait()


def main():
    mode = sys.argv[1]
    if mode == 'video':
        out = sys.argv[2]
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        end = int(sys.argv[4]) if len(sys.argv) > 4 else None
        render_video(out, start, end)
    elif mode == 'stills':
        d = sys.argv[2]
        os.makedirs(d, exist_ok=True)
        for ts in sys.argv[3:]:
            t = float(ts)
            img = gfx.post(render_frame(t), **post_params(t))
            Image.fromarray(img).save(os.path.join(d, 't%06.2f.png' % t))
    elif mode == 'sheet':
        out, t0, t1, n = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
        cols = 4
        rows = math.ceil(n / cols)
        tw, th = 480, 270
        sheet = Image.new('RGB', (tw * cols, (th + 12) * rows), (40, 40, 40))
        from PIL import ImageDraw
        d = ImageDraw.Draw(sheet)
        for k in range(n):
            t = t0 + (t1 - t0) * k / max(1, n - 1)
            img = gfx.post(render_frame(t), **post_params(t))
            im = Image.fromarray(img).resize((tw, th), Image.BILINEAR)
            x, y = (k % cols) * tw, (k // cols) * (th + 12)
            sheet.paste(im, (x, y + 12))
            d.text((x + 4, y), '%.2fs' % t, fill=(255, 255, 0))
        sheet.save(out)


if __name__ == '__main__':
    main()
