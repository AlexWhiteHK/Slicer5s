/* Lotus V7 teaser: a 120 s storyboard rendered as a pure function of time.
   render(t) draws one frame; the player and the frame renderer both call it. */
'use strict';
window.__ready = (async () => {
const W = 1920, H = 1080, DUR = 120;
const Q = new URLSearchParams(location.search);
const RENDER = Q.has('render');
if (RENDER) document.body.classList.add('render');

/* ───────────── easing & math ───────────── */
function bez(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const X = t => ((ax * t + bx) * t + cx) * t, Y = t => ((ay * t + by) * t + cy) * t;
  const dX = t => (3 * ax * t + 2 * bx) * t + cx;
  return x => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 8; i++) {
      const e = X(t) - x; if (Math.abs(e) < 1e-7) return Y(t);
      const d = dX(t); if (Math.abs(d) < 1e-6) break; t -= e / d;
    }
    let lo = 0, hi = 1; t = x;
    for (let i = 0; i < 40; i++) { const v = X(t); if (Math.abs(v - x) < 1e-7) break; if (v < x) lo = t; else hi = t; t = (lo + hi) / 2; }
    return Y(t);
  };
}
const E = {
  std: bez(.2, 0, 0, 1), emph: bez(.05, .7, .1, 1), acc: bez(.3, 0, .8, .15),
  io: bez(.65, 0, .35, 1), soft: bez(.4, 0, .2, 1), lin: x => x, sine: x => .5 - .5 * Math.cos(Math.PI * x),
};
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const lerp = (a, b, p) => a + (b - a) * p;
const seg = (t, a, b, e = E.std) => e(clamp((t - a) / (b - a)));
const win = (t, a, b, c, d, ei = E.std, eo = E.std) => seg(t, a, b, ei) * (1 - seg(t, c, d, eo));
const spring = p => p <= 0 ? 0 : p >= 1 ? 1 : 1 - Math.pow(1 - p, 3) * Math.cos(p * Math.PI * 1.5);
function mixv(a, b, p) {
  if (typeof a === 'number') return lerp(a, b, p);
  if (Array.isArray(a)) return a.map((v, i) => lerp(v, b[i], p));
  const o = {}; for (const k in a) o[k] = lerp(a[k], b[k], p); return o;
}
function keys(t, ks) {
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) {
    if (t <= ks[i][0]) {
      const [t0, v0] = ks[i - 1], [t1, v1, e = E.io] = ks[i];
      return mixv(v0, v1, e((t - t0) / (t1 - t0 || 1)));
    }
  }
  return ks[ks.length - 1][1];
}
function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function gauss(r) { let u = 0; while (u === 0) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r()); }
const hex = c => { const n = parseInt(c.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; };
const rgba = (a, al = 1) => `rgba(${a[0] | 0},${a[1] | 0},${a[2] | 0},${al})`;

/* ───────────── DOM helpers ───────────── */
const stage = document.getElementById('stage'), ui = document.getElementById('ui');
function h(tag, attrs, parent, html) {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) {
    if (k === 'class') e.className = attrs[k];
    else if (k === 'style') e.style.cssText = attrs[k];
    else e.setAttribute(k, attrs[k]);
  }
  if (html != null) e.innerHTML = html;
  (parent === undefined ? ui : parent)?.appendChild(e);
  return e;
}
const NS = 'http://www.w3.org/2000/svg';
function sv(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent && parent.appendChild(e); return e;
}
function vis(e, a) {
  if (a <= 0.002) { if (!e.classList.contains('hid')) e.classList.add('hid'); return false; }
  if (e.classList.contains('hid')) e.classList.remove('hid');
  e.style.opacity = a >= 0.999 ? '' : a.toFixed(3);
  return true;
}
function tr(e, x, y, sc = 1, rot = 0) {
  e.style.transform = `translate(${x.toFixed(2)}px,${y.toFixed(2)}px)` + (sc !== 1 ? ` scale(${sc.toFixed(4)})` : '') + (rot ? ` rotate(${rot.toFixed(2)}deg)` : '');
}
function fblur(e, b) { const v = b > 0.05 ? `blur(${b.toFixed(2)}px)` : ''; if (e.style.filter !== v) e.style.filter = v; }

/* per-unit text reveal: CJK per character, Latin per word */
const CJK = /[⺀-鿿　-〿＀-￯]/;
function tokenize(line, perChar) {
  const out = []; let buf = '';
  for (const ch of line) {
    if (perChar) { out.push(ch); continue; }
    if (CJK.test(ch)) { if (buf) { out.push(buf); buf = ''; } out.push(ch); }
    else if (ch === ' ') { buf += ch; out.push(buf); buf = ''; }
    else buf += ch;
  }
  if (buf) out.push(buf);
  return out;
}
class Words {
  constructor(parent, text, cls, style, perChar) {
    this.el = h('div', { class: cls, style }, parent);
    this.u = [];
    text.split('\n').forEach(line => {
      const row = h('div', { class: 'row' }, this.el);
      tokenize(line, perChar).forEach(tk => { const sp = h('span', { class: 'u' }, row); sp.textContent = tk; this.u.push(sp); });
    });
  }
  update(t, tin, tout, o = {}) {
    const st = o.st ?? 0.03, dur = o.dur ?? 0.95, dy = o.dy ?? 20, bl = o.blur ?? 9, od = o.outDur ?? 0.5, ost = o.ost ?? 0.006;
    const n = this.u.length;
    if (t < tin || t > tout + od + n * ost + 0.02) { vis(this.el, 0); return; }
    vis(this.el, 1);
    for (let i = 0; i < n; i++) {
      const a = seg(t, tin + i * st, tin + i * st + dur, E.emph);
      const b = seg(t, tout + i * ost, tout + i * ost + od, E.acc);
      const sp = this.u[i];
      sp.style.opacity = (a * (1 - b)).toFixed(3);
      const y = (1 - a) * dy - b * dy * 0.5;
      sp.style.transform = Math.abs(y) > 0.01 ? `translateY(${y.toFixed(2)}px)` : '';
      fblur(sp, (1 - a) * bl + b * bl * 0.7);
    }
  }
}
class Cap {
  constructor(parent, o) {
    this.el = h('div', { class: 'cap', style: `left:${o.x}px;top:${o.y}px;width:${o.w}px;text-align:${o.align || 'left'}` }, parent);
    this.zh = o.zh ? new Words(this.el, o.zh, 'zh', `position:relative;font-size:${o.zs || 40}px;line-height:${o.zl || 1.42}`) : null;
    this.en = o.en ? new Words(this.el, o.en, 'en', `position:relative;font-size:${o.es || 24}px;line-height:1.45;margin-top:${o.gap ?? 14}px`) : null;
  }
  update(t, tin, tout, d = 0.22) {
    const on = t >= tin - 0.01 && t <= tout + 1.4;
    vis(this.el, on ? 1 : 0); if (!on) return;
    this.zh && this.zh.update(t, tin, tout, { st: 0.028 });
    this.en && this.en.update(t, tin + d, tout + 0.04, { st: 0.035, dy: 14, blur: 7 });
  }
}

/* ───────────── canvas helpers ───────────── */
function cnv(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; }
function drawTo(src, w, h, filter) {
  const c = cnv(w, h), x = c.getContext('2d');
  x.imageSmoothingQuality = 'high'; if (filter) x.filter = filter;
  x.drawImage(src, 0, 0, c.width, c.height); return c;
}
function downscale(src, w, h) {
  let cur = src, cw = src.width, ch = src.height;
  while (cw / 2 > w && ch / 2 > h) { cw = Math.round(cw / 2); ch = Math.round(ch / 2); cur = drawTo(cur, cw, ch); }
  return drawTo(cur, w, h);
}
function padClamp(base, p) {
  const w = base.width, h = base.height, c = cnv(w + 2 * p, h + 2 * p), x = c.getContext('2d');
  x.drawImage(base, p, p);
  x.drawImage(base, 0, 0, 1, h, 0, p, p, h); x.drawImage(base, w - 1, 0, 1, h, w + p, p, p, h);
  x.drawImage(base, 0, 0, w, 1, p, 0, w, p); x.drawImage(base, 0, h - 1, w, 1, p, h + p, w, p);
  x.drawImage(base, 0, 0, 1, 1, 0, 0, p, p); x.drawImage(base, w - 1, 0, 1, 1, w + p, 0, p, p);
  x.drawImage(base, 0, h - 1, 1, 1, 0, h + p, p, p); x.drawImage(base, w - 1, h - 1, 1, 1, w + p, h + p, p, p);
  return c;
}
function blurred(base, b) {
  if (b <= 0) return drawTo(base, base.width, base.height);
  const p = Math.ceil(b * 3), pc = padClamp(base, p), c = cnv(base.width, base.height), x = c.getContext('2d');
  x.filter = `blur(${b}px)`; x.drawImage(pc, -p, -p); return c;
}
function noiseTile(w, h, seed, mean = 150, sd = 52) {
  const c = cnv(w, h), x = c.getContext('2d'), d = x.createImageData(w, h), r = rng(seed);
  for (let i = 0; i < w * h; i++) {
    const o = i * 4;
    d.data[o] = clamp(mean + gauss(r) * sd, 0, 255); d.data[o + 1] = clamp(mean + gauss(r) * sd, 0, 255);
    d.data[o + 2] = clamp(mean + 8 + gauss(r) * sd, 0, 255); d.data[o + 3] = 255;
  }
  x.putImageData(d, 0, 0); return c;
}
function lineart(src, { lo = 0.07, hi = 0.30, col = [58, 48, 66], pre = 0.8 } = {}) {
  const w = src.width, h = src.height, b = blurred(src, pre);
  const d = b.getContext('2d').getImageData(0, 0, w, h).data;
  const L = new Float32Array(w * h);
  for (let i = 0; i < w * h; i++) L[i] = (0.299 * d[4 * i] + 0.587 * d[4 * i + 1] + 0.114 * d[4 * i + 2]) / 255;
  const out = cnv(w, h), ox = out.getContext('2d'), od = ox.createImageData(w, h), D = od.data;
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
    const i = y * w + x;
    const gx = -L[i - w - 1] - 2 * L[i - 1] - L[i + w - 1] + L[i - w + 1] + 2 * L[i + 1] + L[i + w + 1];
    const gy = -L[i - w - 1] - 2 * L[i - w] - L[i - w + 1] + L[i + w - 1] + 2 * L[i + w] + L[i + w + 1];
    const a = Math.pow(clamp((Math.hypot(gx, gy) - lo) / (hi - lo)), 0.85);
    D[4 * i] = col[0]; D[4 * i + 1] = col[1]; D[4 * i + 2] = col[2]; D[4 * i + 3] = a * 235;
  }
  ox.putImageData(od, 0, 0); return out;
}
function latentize(small) {
  const w = small.width, h = small.height, x = small.getContext('2d'), d = x.getImageData(0, 0, w, h), D = d.data;
  for (let i = 0; i < w * h; i++) {
    const r = D[4 * i], g = D[4 * i + 1], b = D[4 * i + 2], L = 0.3 * r + 0.59 * g + 0.11 * b;
    const c1 = r - g, c2 = b - (r + g) / 2;
    const l = L / 255;
    D[4 * i] = clamp(lerp(112, 236, l) + 0.35 * c1, 0, 255);
    D[4 * i + 1] = clamp(lerp(132, 214, l) - 0.25 * c1 + 0.2 * c2, 0, 255);
    D[4 * i + 2] = clamp(lerp(186, 176, l) + 0.5 * c2, 0, 255);
  }
  const c = cnv(w, h); c.getContext('2d').putImageData(d, 0, 0); return c;
}
function toonify(src, w, h) {
  const c = drawTo(src, w, h, 'saturate(1.5) brightness(1.08) contrast(1.05)'), x = c.getContext('2d');
  const d = x.getImageData(0, 0, w, h), D = d.data;
  for (let i = 0; i < D.length; i += 4) {
    for (let k = 0; k < 3; k++) D[i + k] = Math.round(D[i + k] / 255 * 4) / 4 * 255;
    D[i] = clamp(D[i] * 0.86 + 40, 0, 255); D[i + 1] = clamp(D[i + 1] * 0.86 + 18, 0, 255); D[i + 2] = clamp(D[i + 2] * 0.86 + 34, 0, 255);
  }
  x.putImageData(d, 0, 0);
  x.drawImage(lineart(c, { lo: 0.10, hi: 0.40, col: [70, 40, 70], pre: 0.4 }), 0, 0);
  return c;
}
function drawCover(ctx, img, x, y, w, h) {
  const iw = img.width, ih = img.height, s = Math.max(w / iw, h / ih), dw = iw * s, dh = ih * s;
  ctx.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
}
const shadowCache = new Map();
function shadowImg(r, blur, alpha) {
  r = Math.max(0, Math.round(r));
  const key = r + '|' + blur + '|' + alpha; let s = shadowCache.get(key); if (s) return s;
  const pad = Math.ceil(blur * 2.5), inner = 2 * r + 4, size = inner + 2 * pad;
  const c = cnv(size, size), x = c.getContext('2d');
  x.shadowColor = `rgba(60,64,67,${alpha})`; x.shadowBlur = blur; x.shadowOffsetX = 6000;
  x.fillStyle = '#000'; x.beginPath(); x.roundRect(pad - 6000, pad, inner, inner, r); x.fill();
  s = { c, pad, k: pad + r + 1, size }; shadowCache.set(key, s); return s;
}
function drawShadow(ctx, x, y, w, h, r, blur, alpha, oy) {
  const { c, pad, k, size } = shadowImg(r, blur, alpha);
  const X = x - pad, Y = y - pad + oy, Wd = w + 2 * pad, Hd = h + 2 * pad, m = size - 2 * k;
  const kw = Math.min(k, Wd / 2), kh = Math.min(k, Hd / 2);
  const cols = [[0, k, X, kw], [k, m, X + kw, Wd - 2 * kw], [size - k, k, X + Wd - kw, kw]];
  const rows = [[0, k, Y, kh], [k, m, Y + kh, Hd - 2 * kh], [size - k, k, Y + Hd - kh, kh]];
  for (const [sx, sw, dx, dw] of cols) for (const [sy, sh, dy, dh] of rows)
    if (dw > 0.5 && dh > 0.5) ctx.drawImage(c, sx, sy, sw, sh, dx, dy, dw, dh);
}
function drawCard(ctx, x, y, w, h, r, alpha, content, o = {}) {
  if (alpha <= 0.002 || w < 1 || h < 1) return;
  r = Math.min(r, w / 2, h / 2);
  ctx.save(); ctx.globalAlpha = alpha;
  const e = o.elev ?? 1;
  if (e > 0) { drawShadow(ctx, x, y, w, h, r, 34, 0.15 * e, 14 * e); drawShadow(ctx, x, y, w, h, r, 5, 0.10 * Math.min(1, e), 1.5); }
  ctx.beginPath(); ctx.roundRect(x, y, w, h, o.radii || r); ctx.fillStyle = o.fill || '#fff'; ctx.fill();
  if (content) { ctx.save(); ctx.clip(); content(ctx, x, y, w, h); ctx.restore(); }
  ctx.restore();
}

/* ───────────── copy ───────────── */
const PROMPT = 'a penguin running across water';
const COPY = {
  p1: ['每一张图，都从一句话开始。', 'Every image begins with a sentence.'],
  p2: ['教会机器读懂它，用了十二年。', 'Teaching a machine to read it took twelve years.'],
  p3: ['如果，质量本就该属于模型？', 'What if the quality belonged to the model?'],
  h14: ['生成对抗网络登场：\n一个网络负责画，另一个负责挑错。', 'GANs arrive: one network draws,\nanother points out what is wrong.'],
  h15: ['第一次，机器照着一句话作画。\n只有几十个像素见方，勉强看出轮廓。', 'For the first time, pictures from a caption:\na few dozen pixels across, barely a silhouette.'],
  h20a: ['扩散模型：先学会把一张图\n一点点变成噪声，', 'Diffusion: learn how an image dissolves into noise,'],
  h20b: ['再学会把这条路\n一步一步走回来。', 'then learn to walk the path back, step by step.'],
  h21: ['CLIP 把文字和图像\n放进同一个空间，\n模型开始真正听懂描述。', 'CLIP places words and pictures in one space.\nModels begin to actually listen.'],
  h22a: ['在压缩后的潜空间里去噪，\n一张消费级显卡就能运行。', 'Denoise in a compressed latent space,\nsmall enough for a consumer GPU.'],
  h22b: ['权重开源。社区微调遍地开花，\n二次元模型也由此兴起。', 'Open weights. Community fine-tunes bloom,\nand anime models with them.'],
  h23: ['Transformer 接手去噪：\n图像被切成小块，\n每一块都是一个 token。', 'Transformers take over denoising.\nThe image is cut into patches,\nand each patch becomes a token.'],
  h24: ['文字与图像并入同一条序列，\n参数从数亿走向百亿。', 'Text and image share one sequence,\nand models grow from hundreds of millions\nof parameters to over ten billion.'],
  h25: ['模型越来越强，\n好图却依然藏在提示词里。', 'Models grew stronger.\nThe good images still hid inside the prompt.'],
  r1: ['基于 Diffusion Transformer 的照片级写实模型。', 'Photoreal generation on a diffusion transformer.'],
  r2: ['把能力花在光线、材质与每一处细节上。', 'Capacity spent on light, material and every detail.'],
  r3: ['同一个主角，任意一个世界。', 'One subject. Any world.'],
  a1: ['朴素的提示词，也能得到完成度很高的插画。', 'Plain prompts, finished illustration.'],
  a2: ['画风由实验室设计，而不是数据的平均值。', 'A look designed in the lab, not an average of the data.'],
  a3: ['换一个角色、一个场景，风格依旧稳定。', 'New character, new scene. The same steady hand.'],
  g1: ['一个实验室，两条图像产品线。', 'One lab. Two lines of image models.'],
};
const CHIPS = ['masterpiece', 'best quality', 'ultra-detailed', '8k', 'photorealistic', 'cinematic lighting', '(sharp focus:1.3)',
  'highres', 'intricate details', 'volumetric light', 'award-winning', 'RAW photo', 'HDR', 'depth of field', 'trending on artstation',
  'hyper-realistic', '(extremely detailed:1.2)', 'octane render', 'studio quality', 'dramatic', 'vivid colors', 'sharp', 'professional', '4k wallpaper'];
const CHIPS_X = ['negative: blurry', 'lowres', 'bad anatomy', 'worst quality', 'jpeg artifacts', 'watermark', 'deformed', 'extra limbs',
  '(detailed feathers:1.4)', 'golden hour', 'bokeh', 'unreal engine', '35mm', 'f/1.8', 'ray tracing', 'perfect composition'];
const CHAPTERS = [[0, '序章 · Prologue'], [12, '十二年 · Twelve years'], [66, '转折 · The turn'], [78, 'Lotus Realistic V7'], [96, 'Lotus Anime Diffusion V7'], [111, '即将推出 · Coming soon']];

/* cue times shared with the score (tools/compose_music.py mirrors these formulas) */
const TYPE_T = [...PROMPT].map((_, i) => 2.45 + i * 0.058 + 0.012 * Math.sin(i * 2.7));
const CHIP_T = CHIPS.map((_, i) => 60.8 + 5.4 * (1 - Math.pow(1 - i / CHIPS.length, 1.6)));
const CHIPX_T = CHIPS_X.map((_, j) => 66.2 + 2.6 * (1 - Math.pow(1 - j / CHIPS_X.length, 1.4)));

/* ───────────── load fonts & images ───────────── */
await Promise.all(['400 20px "Google Sans Flex"', '500 20px "Google Sans Flex"', '600 20px "Google Sans Flex"',
  '400 20px "Noto Sans SC"', '500 20px "Noto Sans SC"', 'italic 300 20px "Source Serif 4"', '400 20px "Source Serif 4"',
  '400 20px "Google Sans Code"'].map(f => document.fonts.load(f, 'aA中蓮')));
await document.fonts.ready;
const loadImg = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
const [IM_DESERT, IM_JUNGLE, IM_SAKURA, IM_MOON] = await Promise.all(
  ['realistic-desert', 'realistic-jungle', 'anime-sakura', 'anime-moon'].map(n => loadImg(`assets/img/${n}.webp`)));

/* derived imagery */
const HC = { x: 880, y: 292, w: 900, h: 375, r: 28 };            // history card
const RC = { x: 120, y: 110, w: 1680, h: 700, r: 36 };           // realistic card
const A1 = { x: 300, y: 90, w: 1320, h: 748, r: 36 };            // anime card, large
const A1S = { x: 154, y: 170, w: 860, h: 487, r: 28 };           // anime pair, left
const A2S = { x: 1054, y: 170, w: 712, h: 487, r: 28 };          // anime pair, right

const hBase = downscale(IM_DESERT, HC.w, HC.h);
const hSoft = {}; for (const b of [10, 6, 5, 4, 3, 2.5]) hSoft[b] = blurred(hBase, b);
const hPx = {}; for (const [w, hh] of [[12, 5], [24, 10], [48, 20], [96, 40]]) hPx[w] = downscale(IM_DESERT, w, hh);
const hBlob = blurred(drawTo(downscale(IM_DESERT, 10, 4), HC.w, HC.h), 26);
const hNoise = [0, 1, 2].map(i => noiseTile(450, 188, 11 + i));
const hLatent = latentize(downscale(IM_DESERT, 60, 25));
const lNoise = [0, 1, 2].map(i => noiseTile(60, 25, 31 + i, 140, 60));
const thumbSrc = hSoft[2.5];
const VARIANTS = [
  drawTo(thumbSrc, 240, 100, 'blur(1px)'), drawTo(thumbSrc, 240, 100, 'grayscale(1) contrast(1.1) blur(.6px)'),
  drawTo(thumbSrc, 240, 100, 'sepia(.7) saturate(1.3) blur(.6px)'), drawTo(thumbSrc, 240, 100, 'hue-rotate(170deg) saturate(1.2) blur(.6px)'),
  drawTo(thumbSrc, 240, 100, 'saturate(1.9) contrast(1.15) blur(.6px)'), drawTo(thumbSrc, 240, 100, 'hue-rotate(-35deg) saturate(1.4) brightness(1.06) blur(.6px)'),
  drawTo(thumbSrc, 240, 100, 'contrast(1.25) brightness(1.12) saturate(.55) blur(.6px)'), drawTo(thumbSrc, 240, 100, 'hue-rotate(210deg) saturate(.9) brightness(1.05) blur(.6px)'),
];
const TOON = toonify(thumbSrc, 240, 100);
const rBase = { desert: downscale(IM_DESERT, RC.w, RC.h), jungle: downscale(IM_JUNGLE, RC.w, RC.h) };
const rSoft = blurred(rBase.desert, 7);
const rNoise = [0, 1, 2].map(i => noiseTile(840, 350, 51 + i));
const a1Img = downscale(IM_SAKURA, A1.w, A1.h), a1Line = lineart(a1Img);
const moonFlat = (() => { const c = cnv(IM_MOON.width, IM_MOON.height), x = c.getContext('2d'); x.fillStyle = '#e9eef8'; x.fillRect(0, 0, c.width, c.height); x.drawImage(IM_MOON, 0, 0); return c; })();
const a2Img = downscale(moonFlat, A2S.w, A2S.h), a2Line = lineart(a2Img);
const tmpR = cnv(RC.w, RC.h), tmpRX = tmpR.getContext('2d');
const rcC = cnv(RC.w, RC.h), rcX = rcC.getContext('2d');
const hcC = cnv(HC.w, HC.h), hcX = hcC.getContext('2d');
const a1C = cnv(A1.w, A1.h), a1X = a1C.getContext('2d'), tmpA = cnv(A1.w, A1.h), tmpAX = tmpA.getContext('2d');
const a2C = cnv(A2S.w, A2S.h), a2X = a2C.getContext('2d'), tmpB = cnv(A2S.w, A2S.h), tmpBX = tmpB.getContext('2d');

/* grain */
const grainEl = document.getElementById('grain');
{
  const c = cnv(256, 256), x = c.getContext('2d'), d = x.createImageData(256, 256), r = rng(7);
  for (let i = 0; i < 256 * 256; i++) { const v = clamp(128 + gauss(r) * 26, 0, 255); d.data[4 * i] = d.data[4 * i + 1] = d.data[4 * i + 2] = v; d.data[4 * i + 3] = 255; }
  x.putImageData(d, 0, 0);
  grainEl.style.backgroundImage = `url(${c.toDataURL()})`;
}

/* ───────────── background ───────────── */
const BGX = document.getElementById('bg').getContext('2d');
const PAL = [
  [0, ['#f8d8cf', '#cfe0fb', '#fbe6c0', '#e6dcf7']],
  [12, ['#d3e3fb', '#d5eee0', '#f4ddd6', '#e9e2f8']],
  [66, ['#efe3dd', '#e4e2ef', '#f5ecdd', '#dfe9f2']],
  [79, ['#f6e1c3', '#f2d3c2', '#dce6f5', '#f7ead2']],
  [95.5, ['#f9d1dd', '#e2d6fb', '#d4e2fd', '#fde4ec']],
  [110.5, ['#f8d8cf', '#d3e3fb', '#fbe6c0', '#d5eee0']],
].map(([t, c]) => [t, c.map(hex)]);
const BLOBS = [
  { x: .16, y: .20, r: 430, ax: 60, ay: 40, w: .13, ph: 0 },
  { x: .86, y: .16, r: 400, ax: 50, ay: 45, w: .10, ph: 1.7 },
  { x: .80, y: .88, r: 450, ax: 70, ay: 35, w: .09, ph: 3.1 },
  { x: .18, y: .92, r: 380, ax: 55, ay: 40, w: .12, ph: 4.4 },
];
function palette(t) {
  let i = 0; while (i + 1 < PAL.length && t >= PAL[i + 1][0]) i++;
  if (i === 0) return PAL[0][1];
  const p = seg(t, PAL[i][0], PAL[i][0] + 3.5, E.io);
  return PAL[i][1].map((c, k) => mixv(PAL[i - 1][1][k], c, p));
}
function drawBG(t) {
  const x = BGX; x.fillStyle = '#f7f6f2'; x.fillRect(0, 0, 960, 540);
  const pal = palette(t), breath = 1 - 0.25 * win(t, 69, 70.2, 71.6, 73.4, E.io, E.io);
  BLOBS.forEach((b, i) => {
    const cx = b.x * 960 + Math.sin(t * b.w + b.ph) * b.ax, cy = b.y * 540 + Math.cos(t * b.w * .8 + b.ph * 1.3) * b.ay;
    const g = x.createRadialGradient(cx, cy, 0, cx, cy, b.r);
    g.addColorStop(0, rgba(pal[i], .78 * breath)); g.addColorStop(.5, rgba(pal[i], .34 * breath)); g.addColorStop(1, rgba(pal[i], 0));
    x.fillStyle = g; x.fillRect(0, 0, 960, 540);
  });
}

/* ───────────── shared SVG marks ───────────── */
let sparkN = 0;
const sparkSVG = () => { const id = 'sg' + (++sparkN); return `<svg viewBox="0 0 24 24" width="100%" height="100%"><defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d4553f"/><stop offset=".55" stop-color="#f28b82"/><stop offset="1" stop-color="#8ab4f8"/></linearGradient></defs><path d="M12 0C12.9 6.3 17.7 11.1 24 12C17.7 12.9 12.9 17.7 12 24C11.1 17.7 6.3 12.9 0 12C6.3 11.1 11.1 6.3 12 0Z" fill="url(#${id})"/></svg>`; };
const PETALS = [
  { a: -64, c: '#8ab4f8', L: 74, w: 30, d: .26 }, { a: 64, c: '#81c995', L: 74, w: 30, d: .26 },
  { a: -33, c: '#f28b82', L: 88, w: 34, d: .13 }, { a: 33, c: '#fbbc5d', L: 88, w: 34, d: .13 },
  { a: 0, c: '#d4553f', L: 100, w: 38, d: 0 },
];
const petalPath = (L, w) => `M0 0C${-w} ${-L * .3} ${-w * .62} ${-L * .82} 0 ${-L}C${w * .62} ${-L * .82} ${w} ${-L * .3} 0 0Z`;
function makeLotus(parent, px) {
  const el = h('div', { class: 'abs', style: `width:${px}px;height:${px * 0.7}px` }, parent);
  el.k = px / 260;
  const svg = sv('svg', { viewBox: '-130 -140 260 182', width: px, height: px * 0.7 }, null);
  el.appendChild(svg);
  const ps = PETALS.map(p => sv('path', { d: petalPath(p.L, p.w), fill: p.c, style: 'mix-blend-mode:multiply', opacity: .92 }, svg));
  return { el, ps, px };
}
function bloom(lotus, t, t0, dur = 1.25) {
  PETALS.forEach((p, i) => {
    const q = clamp((t - t0 - p.d) / dur), sp = spring(q), op = seg(t, t0 + p.d, t0 + p.d + .35);
    lotus.ps[i].setAttribute('transform', `rotate(${(p.a * sp).toFixed(2)}) scale(${(0.25 + 0.75 * Math.min(1.06, sp)).toFixed(4)})`);
    lotus.ps[i].setAttribute('opacity', (0.92 * op).toFixed(3));
  });
}
function higanSVG(px) {
  const cells = [[2, 0], [4, 0], [1, 1], [3, 1], [5, 1], [0, 2], [1, 2], [5, 2], [6, 2], [1, 3], [3, 3], [5, 3], [2, 4], [4, 4]];
  const r = cells.map(([x, y]) => `<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="#2f7fe0"/>`).join('');
  const d = [[3.5, -1.25], [3.5, 6.25], [-1.35, 2.5], [8.35, 2.5]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r=".36" fill="#2f7fe0"/>`).join('');
  return `<svg viewBox="-2 -2 11 9" width="${px}" height="${px * 9 / 11}">${r}${d}</svg>`;
}

/* ───────────── measure ───────────── */
const mctx = cnv(10, 10).getContext('2d');
const measure = (txt, font) => { mctx.font = font; return mctx.measureText(txt).width; };
const PF = '400 26px "Google Sans Flex"';

/* ═════════════════ UI components ═════════════════ */

/* prompt pill */
const PILL_C = { x: 580, y: 504, w: 760, h: 72 }, PILL_H = { x: 880, y: 196, w: 900, h: 72 };
const pill = h('div', { class: 'abs pill' });
const pillBg = h('div', { class: 'pill-bg' }, pill);
const pillShine = h('div', { class: 'pill-shine' }, pill); const shineBar = h('i', null, pillShine);
const spark = h('div', { class: 'spark' }, pill, sparkSVG());
const ptext = h('div', { class: 'ptext gs' }, pill);
const pWords = []; {
  let idx = 0;
  PROMPT.split(' ').forEach((w, i) => { const s = (i ? ' ' : '') + w; const sp = h('span', { class: 'pw' }, ptext); pWords.push({ sp, start: idx, s, w }); idx += s.length; });
}
const caret = h('span', { class: 'caret' }, ptext);
const send = h('div', { class: 'send' }, pill, `<svg width="24" height="24" viewBox="0 0 24 24"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
const ripple = h('div', { class: 'ripple' }, send);
const wordX = (() => { const o = {}; pWords.forEach(p => { const pre = PROMPT.slice(0, p.start + (p.start ? 1 : 0)); const x0 = measure(pre, PF), x1 = x0 + measure(p.w, PF); o[p.w] = [x0, x1]; }); return o; })();
const freeSpark = h('div', { class: 'abs', style: 'width:26px;height:26px' }, ui, sparkSVG());

/* 2025 chips (inside pill) */
const chipEls = []; {
  let x = 66, row = 0; const maxX = PILL_H.w - 22;
  CHIPS.forEach((c, i) => {
    const w = measure(c, '400 18px "Google Sans Flex"') + 32;
    if (x + w > maxX) { row++; x = 66; }
    const el = h('div', { class: 'chipx gs' }, pill); el.textContent = c;
    chipEls.push({ el, x, y: 72 + row * 50, row, t: CHIP_T[i], r: rng(100 + i)() });
    x += w + 10;
  });
}
const ROWS = chipEls.reduce((m, c) => Math.max(m, c.row), 0) + 1;
const rowT = Array.from({ length: ROWS }, (_, k) => chipEls.find(c => c.row === k).t);
const chipXEls = CHIPS_X.map((c, j) => {
  const r = rng(300 + j);
  const el = h('div', { class: 'chipx spill gs' + (j < 6 ? ' neg' : '') }); el.textContent = c;
  return { el, x: 900 + r() * 700, y: 500 + r() * 230 + (j % 3) * 18, rot: (r() - .5) * 26, t: CHIPX_T[j], r: r() };
});

/* captions */
const cap = (o) => new Cap(ui, o);
const LC = { x: 130, y: 492, w: 700 };
const CP = {
  p1: cap({ x: 360, y: 360, w: 1200, align: 'center', zh: COPY.p1[0], en: COPY.p1[1], zs: 50, es: 28 }),
  p2: cap({ x: 360, y: 360, w: 1200, align: 'center', zh: COPY.p2[0], en: COPY.p2[1], zs: 50, es: 28 }),
  p3: cap({ x: 360, y: 360, w: 1200, align: 'center', zh: COPY.p3[0], en: COPY.p3[1], zs: 50, es: 28 }),
  h14: cap({ ...LC, zh: COPY.h14[0], en: COPY.h14[1] }),
  h15: cap({ ...LC, zh: COPY.h15[0], en: COPY.h15[1] }),
  h20a: cap({ ...LC, zh: COPY.h20a[0], en: null }),
  h20b: cap({ ...LC, y: LC.y + 114, zh: COPY.h20b[0], en: null }),
  h20ea: cap({ ...LC, y: LC.y + 246, zh: null, en: COPY.h20a[1], gap: 0 }),
  h20eb: cap({ ...LC, y: LC.y + 281, zh: null, en: COPY.h20b[1], gap: 0 }),
  h21: cap({ ...LC, zh: COPY.h21[0], en: COPY.h21[1] }),
  h22a: cap({ ...LC, zh: COPY.h22a[0], en: COPY.h22a[1] }),
  h22b: cap({ ...LC, zh: COPY.h22b[0], en: COPY.h22b[1] }),
  h23: cap({ ...LC, zh: COPY.h23[0], en: COPY.h23[1] }),
  h24: cap({ ...LC, zh: COPY.h24[0], en: COPY.h24[1] }),
  h25: cap({ ...LC, zh: COPY.h25[0], en: COPY.h25[1] }),
  r1: cap({ x: 260, y: 896, w: 1400, align: 'center', zh: COPY.r1[0], en: COPY.r1[1], zs: 30, es: 22, gap: 8 }),
  r2: cap({ x: 260, y: 896, w: 1400, align: 'center', zh: COPY.r2[0], en: COPY.r2[1], zs: 30, es: 22, gap: 8 }),
  r3: cap({ x: 260, y: 896, w: 1400, align: 'center', zh: COPY.r3[0], en: COPY.r3[1], zs: 30, es: 22, gap: 8 }),
  a1: cap({ x: 260, y: 896, w: 1400, align: 'center', zh: COPY.a1[0], en: COPY.a1[1], zs: 30, es: 22, gap: 8 }),
  a2: cap({ x: 260, y: 896, w: 1400, align: 'center', zh: COPY.a2[0], en: COPY.a2[1], zs: 30, es: 22, gap: 8 }),
  a3: cap({ x: 260, y: 896, w: 1400, align: 'center', zh: COPY.a3[0], en: COPY.a3[1], zs: 30, es: 22, gap: 8 }),
  g1: cap({ x: 260, y: 700, w: 1400, align: 'center', zh: COPY.g1[0], en: COPY.g1[1], zs: 34, es: 24, gap: 8 }),
};
const nameReal = new Words(ui, 'Lotus Realistic V7', 'abs gs', 'left:0;top:846px;width:1920px;text-align:center;font-size:30px;font-weight:500;letter-spacing:-.01em');
const nameAnime = new Words(ui, 'Lotus Anime Diffusion V7', 'abs gs', 'left:0;top:846px;width:1920px;text-align:center;font-size:30px;font-weight:500;letter-spacing:-.01em');

/* year odometer + method tags */
const YS = 172;
const odo = h('div', { class: 'abs odo', style: `left:${LC.x - 6}px;top:236px;font-size:${YS}px;line-height:${YS}px;height:${YS}px` });
const digits = [3, 2, 1, 0].map(k => {
  const d = h('div', { class: 'd', style: `width:${YS * .6}px;height:${YS}px` }, odo);
  const s = h('div', { class: 's' }, d, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map(n => `<span style="height:${YS}px">${n}</span>`).join(''));
  return { k, s };
});
const YEAR_K = [[11.2, 2014], [18.3, 2014], [19.2, 2015, E.emph], [21.0, 2015], [21.9, 2016, E.emph], [24.1, 2016], [25.6, 2020, E.emph],
  [33.1, 2020], [34.0, 2021, E.emph], [39.1, 2021], [40.0, 2022, E.emph], [48.1, 2022], [49.0, 2023, E.emph], [54.1, 2023], [55.0, 2024, E.emph],
  [60.1, 2024], [61.0, 2025, E.emph], [74.8, 2025], [76.4, 2026, E.emph]];
const yearAt = t => keys(t, YEAR_K);
const digitVal = (y, k) => { if (k === 0) return y; const p = 10 ** k, base = Math.floor(y / p); return base + Math.max(0, (y % p) - (p - 1)); };
const TAGS = [
  [12.2, 17.9, 'GAN · Goodfellow et al.', '#4c8df6'],
  [18.3, 20.9, 'alignDRAW · Mansimov et al.', '#f2a93b'],
  [21.1, 23.9, 'Text-to-Image GAN · Reed et al.', '#f2a93b'],
  [24.3, 32.9, 'DDPM · Ho, Jain & Abbeel', '#9b8cf2'],
  [33.3, 38.9, 'CLIP · DALL·E', '#3fae6a'],
  [39.3, 47.9, 'Latent Diffusion · Stable Diffusion', '#4c8df6'],
  [48.3, 53.9, 'DiT · Peebles & Xie', '#d4553f'],
  [54.3, 59.9, 'MMDiT · Rectified Flow', '#f28b82'],
  [60.3, 69.1, 'Prompt engineering', '#9aa0a6'],
].map(([a, b, txt, c]) => ({ a, b, el: h('div', { class: 'abs tag mono', style: `left:${LC.x}px;top:446px` }, ui, `<i style="background:${c}"></i>${txt}`) }));

/* timeline */
const TLX0 = 130, TLX1 = 1790, TLY = 968;
const yx = y => TLX0 + (y - 2014) * (TLX1 - TLX0) / 12;
const tl = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const tlBase = h('div', { class: 'tl-base', style: `left:${TLX0}px;top:${TLY}px;width:${yx(2025) - TLX0}px;transform-origin:${(960 - TLX0)}px 50%` }, tl);
const tlDash = h('div', { class: 'tl-dash', style: `left:${yx(2025)}px;top:${TLY}px;width:${yx(2026) - yx(2025)}px` }, tl);
const tlProg = h('div', { class: 'tl-prog', style: `left:${TLX0}px;top:${TLY}px;width:${TLX1 - TLX0}px` }, tl);
const STATIONS = [2014, 2015, 2016, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
const tlTicks = [];
for (let y = 2014; y <= 2026; y++) {
  const st = STATIONS.includes(y);
  const tk = h('div', { class: 'tl-tick', style: `left:${yx(y)}px;top:${TLY}px` + (st ? '' : ';width:5px;height:5px;margin:-1.5px 0 0 -2.5px;background:#dadce0') }, tl);
  const lb = y === 2026 ? null : h('div', { class: 'tl-lab mono', style: `left:${yx(y)}px;top:${TLY + 16}px` }, tl, String(y));
  tlTicks.push({ y, tk, lb, st });
}
const tlV7 = h('div', { class: 'tl-v7 gs', style: `left:${yx(2026)}px;top:${TLY + 14}px` }, tl, '2026 · V7');
const tlMark = h('div', { class: 'tl-mark' }, tl);

/* 2014 · GAN diagram */
const gan = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const ganG = h('div', { class: 'chip gs', style: 'left:1010px;top:700px' }, gan, '<i style="background:#4c8df6"></i>生成器 · Generator');
const ganD = h('div', { class: 'chip gs', style: 'left:1400px;top:700px' }, gan, '<i style="background:#d4553f"></i>判别器 · Discriminator');
const ganSvg = sv('svg', { class: 'full' }, gan);
const ganArc1 = sv('path', { d: 'M1240 700 C1290 660 1350 660 1398 700', fill: 'none', stroke: '#9aa0a6', 'stroke-width': 1.6, 'stroke-dasharray': '4 6' }, ganSvg);
const ganArc2 = sv('path', { d: 'M1398 744 C1350 786 1290 786 1240 744', fill: 'none', stroke: '#9aa0a6', 'stroke-width': 1.6, 'stroke-dasharray': '4 6' }, ganSvg);
const ganDot = sv('circle', { r: 6, fill: '#d4553f' }, ganSvg);
const ganLbl1 = h('div', { class: 'lbl gs', style: 'left:1270px;top:650px' }, gan, '画一张');
const ganLbl2 = h('div', { class: 'lbl gs', style: 'left:1280px;top:776px' }, gan, '挑错');

/* 2015/16 · resolution chip + falling words */
const resChip = h('div', { class: 'chip glass mono', style: `left:${HC.x + 20}px;top:${HC.y + 20}px;height:38px` });
const resTxt = [h('span', null, resChip, '≈ 32 × 32'), h('span', { style: 'display:none' }, resChip, '≈ 64 × 64')];
const fallWords = pWords.map((p, i) => ({ el: h('div', { class: 'abs gs', style: 'font-size:26px;color:#1f1f1f;white-space:pre' }, ui, p.w), p, i }));

/* 2020 · DDPM strip */
const TH = { y: 700, w: 150, h: 62.5, gap: 37.5 };
const ddpm = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const thumbX = i => HC.x + i * (TH.w + TH.gap);
const ddLbl = ['x<sub>0</sub>', 'x<sub>250</sub>', 'x<sub>500</sub>', 'x<sub>750</sub>', 'x<sub>1000</sub>'].map((s, i) =>
  h('div', { class: 'eq serif', style: `left:${thumbX(i) + TH.w / 2}px;top:${TH.y + TH.h + 6}px;font-size:20px;transform:translateX(-50%)` }, ddpm, s));
const ddArrows = [0, 1, 2, 3].map(i => h('div', { class: 'abs', style: `left:${thumbX(i) + TH.w + 6}px;top:${TH.y + TH.h / 2 - 12}px;width:26px;height:24px` }, ddpm,
  `<svg width="26" height="24" viewBox="0 0 26 24"><path d="M3 12h19M15 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`));
const ddFwd = h('div', { class: 'chip gs', style: `left:${HC.x}px;top:812px;height:40px;font-size:17px` }, ddpm, '<i style="background:#9aa0a6"></i>加噪 · forward　x<sub style="font-size:.7em">0</sub> → x<sub style="font-size:.7em">T</sub>');
const ddRev = h('div', { class: 'chip gs', style: `left:${HC.x}px;top:812px;height:40px;font-size:17px;color:#b1352a` }, ddpm, '<i style="background:#d4553f"></i>去噪 · reverse　x<sub style="font-size:.7em">T</sub> → x<sub style="font-size:.7em">0</sub>');
const ddEq = h('div', { class: 'eq serif', style: `left:${HC.x + 340}px;top:814px` }, ddpm, 'x<sub>t</sub> = √<span class="bar">α</span><sub>t</sub> · x<sub>0</sub> + √(1 − <span class="bar">α</span><sub>t</sub>) · ε');
const tChip = h('div', { class: 'chip glass mono', style: `left:${HC.x + 20}px;top:${HC.y + 20}px;height:38px` }, ui, 't = 0');

/* 2021 · CLIP links + shared-space vectors */
const clipSvg = sv('svg', { class: 'full' }, ui);
const CLIP_L = [
  { w: 'penguin', c: '#4c8df6', to: [930, 400] }, { w: 'running', c: '#f2a93b', to: [775, 520] }, { w: 'water', c: '#3fae6a', to: [1160, 655] },
].map(o => {
  const [x0, x1] = wordX[o.w], sx = PILL_H.x + 66 + (x0 + x1) / 2, sy = PILL_H.y + 54;
  const tx = HC.x + o.to[0] * HC.w / 2000, ty = HC.y + o.to[1] * HC.h / 833;
  const path = sv('path', { d: `M${sx} ${sy} C${sx} ${sy + 90} ${tx} ${ty - 110} ${tx} ${ty}`, fill: 'none', stroke: o.c, 'stroke-width': 2.4, 'stroke-linecap': 'round' }, clipSvg);
  const len = path.getTotalLength();
  const ring = sv('circle', { cx: tx, cy: ty, r: 16, fill: rgba(hex(o.c), .18), stroke: o.c, 'stroke-width': 2 }, clipSvg);
  const dot = sv('circle', { cx: tx, cy: ty, r: 5, fill: o.c }, clipSvg);
  return { ...o, path, len, ring, dot, span: pWords.find(p => p.w === o.w).sp };
});
const vecWrap = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const VEC_BASE = Array.from({ length: 16 }, (_, i) => { const r = rng(900 + i); return [r(), r(), r()]; });
const vecPal = ['#8ab4f8', '#aecbfa', '#f6aea9', '#fdd663', '#81c995', '#c58af9', '#e8eaed'];
const vecRows = ['文字 · Text', '图像 · Image'].map((lab, ri) => {
  const row = h('div', { class: 'vec gs', style: `left:${HC.x + 40}px;top:${708 + ri * 44}px` }, vecWrap);
  h('b', null, row, lab);
  const cells = h('div', { class: 'cells' }, row);
  const cs = VEC_BASE.map((b, i) => { const k = Math.floor((b[0] + (ri ? (b[1] - .5) * .18 : 0)) * vecPal.length) % vecPal.length; return h('i', { style: `background:${vecPal[(k + vecPal.length) % vecPal.length]}` }, cells); });
  return { row, cs };
});
const vecEq = h('div', { class: 'abs gs', style: `left:${HC.x + 40 + 134 + 16 * 26 + 18}px;top:722px;font-size:40px;color:#3fae6a;font-weight:300` }, vecWrap, '≈');
const vecLbl = h('div', { class: 'lbl gs', style: `left:${HC.x + 40 + 134 + 16 * 26 + 64}px;top:735px` }, vecWrap, '同一空间 · one space');

/* 2022 · latent labels */
const ldm = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const LAT = { x: HC.x + 300, y: HC.y + 125, w: 300, h: 125 };
const ldmEnc = h('div', { class: 'chip gs', style: `left:${HC.x + 36}px;top:${HC.y + 166}px;height:40px;font-size:17px` }, ldm, '<i style="background:#4c8df6"></i>编码 · Encoder');
const ldmDec = h('div', { class: 'chip gs', style: `left:${HC.x + 676}px;top:${HC.y + 166}px;height:40px;font-size:17px` }, ldm, '<i style="background:#3fae6a"></i>解码 · Decoder');
const ldmLat = h('div', { class: 'lbl mono', style: `left:${LAT.x + LAT.w / 2}px;top:${LAT.y - 32}px;transform:translateX(-50%)` }, ldm, 'latent · 1/8 × 1/8');
const ldmDn = h('div', { class: 'lbl gs', style: `left:${LAT.x + LAT.w / 2}px;top:${LAT.y + LAT.h + 12}px;transform:translateX(-50%);color:#b1352a` }, ldm, '在这里去噪 · denoise here');
const animeTag = h('div', { class: 'chip gs', style: `left:${HC.x + 610}px;top:${HC.y + HC.h + 26}px` }, ui, '<i style="background:#f28b82"></i>二次元 · Anime');
const openTag = h('div', { class: 'chip gs', style: `left:${HC.x}px;top:${HC.y + HC.h + 26}px` }, ui, '<i style="background:#3fae6a"></i>开源权重 · Open weights');

/* 2023/24 · tokens, attention, parameters */
const tokSvg = sv('svg', { class: 'full' }, ui);
const TK = { n: 12, s: 46, gap: 10, y: 712 };
const tokX0 = HC.x + (HC.w - (TK.n * TK.s + (TK.n - 1) * TK.gap)) / 2;
const ARCS = [[0, 5], [2, 9], [4, 7], [1, 11], [6, 10], [3, 8], [5, 11], [0, 3], [7, 9], [2, 6]];
const arcEls = ARCS.map(() => sv('path', { fill: 'none', stroke: '#4c8df6', 'stroke-width': 1.6, 'stroke-linecap': 'round' }, tokSvg));
const ditLbl = h('div', { class: 'lbl mono', style: `left:${HC.x}px;top:${TK.y + 13}px` }, ui, 'tokens');
const ditAttn = h('div', { class: 'lbl gs', style: `left:${HC.x}px;top:${TK.y + 58}px` }, ui, '注意力 · attention');
const patchLbl = h('div', { class: 'chip glass mono', style: `left:${HC.x + 20}px;top:${HC.y + 20}px;height:38px` }, ui, 'patchify · 16 × 7');
const MM = { s: 34, gap: 7 };
const txtTok = PROMPT.split(' ').map(w => { const el = h('div', { class: 'tok gs' }, ui, w); return { el, w: measure(w, '400 15px "Google Sans Flex"') + 24 }; });
const mmLayout = (() => {
  const total = txtTok.reduce((s, t) => s + t.w, 0) + TK.n * MM.s + (txtTok.length + TK.n - 1) * MM.gap;
  let x = HC.x + (HC.w - total) / 2; const txt = [], img = [];
  txtTok.forEach(t => { txt.push(x); x += t.w + MM.gap; });
  for (let i = 0; i < TK.n; i++) { img.push(x); x += MM.s + MM.gap; }
  return { txt, img };
})();
const MARCS = [[0, 7], [1, 9], [2, 12], [4, 14], [3, 10], [1, 15], [6, 16], [8, 13]];
const marcEls = MARCS.map((_, i) => sv('path', { fill: 'none', stroke: i % 2 ? '#f28b82' : '#8ab4f8', 'stroke-width': 1.6, 'stroke-linecap': 'round' }, tokSvg));
const params = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const PB = { x: HC.x + 170, y: 866, w: HC.w - 170 };
h('div', { class: 'lbl gs', style: `left:${HC.x}px;top:${PB.y - 8}px;color:#5f6368` }, params, '参数 · Parameters');
h('div', { class: 'abs', style: `left:${PB.x}px;top:${PB.y}px;width:${PB.w}px;height:8px;border-radius:4px;background:#e8eaed` }, params);
const pbFill = h('div', { class: 'abs', style: `left:${PB.x}px;top:${PB.y}px;width:${PB.w}px;height:8px;border-radius:4px;background:linear-gradient(90deg,#8ab4f8,#f28b82 70%,#d4553f);transform-origin:0 50%` }, params);
const logX = e => PB.x + (e - 8) / 2.4 * PB.w;
[['10⁸', 8], ['10⁹', 9], ['10¹⁰', 10]].forEach(([s, e]) => {
  h('div', { class: 'abs', style: `left:${logX(e)}px;top:${PB.y - 6}px;width:1px;height:20px;background:#bdc1c6` }, params);
  h('div', { class: 'lbl mono', style: `left:${logX(e)}px;top:${PB.y + 18}px;transform:translateX(-50%)` }, params, s);
});

/* illustration note */
const note = h('div', { class: 'lbl mono', style: `left:${HC.x + HC.w}px;top:916px;transform:translateX(-100%);font-size:13px;color:#b0b4b9` }, ui, '示意动画，非模型输出 · illustration, not model output');

/* lotus + title */
const lotus = makeLotus(ui, 340);
const LOTUS_O = { x: 960, y: 380 };   // petal base
const title = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const wmWrap = h('div', { class: 'abs', style: 'left:0;top:404px;width:1920px;text-align:center' }, title);
const wm = new Words(wmWrap, 'Lotus V7', 'wordmark', 'position:relative;font-size:150px;line-height:150px', true);
wm.u.slice(-2).forEach(u => u.classList.add('v7'));
const tagRow = h('div', { class: 'abs', style: 'left:0;top:582px;width:1920px;display:flex;justify-content:center;align-items:baseline;gap:18px' }, title);
const tagZh = new Words(tagRow, '更高的下限。', 'gs', 'position:relative;font-size:36px;font-weight:500');
const tagEn = new Words(tagRow, 'A higher floor.', 'serif', 'position:relative;font-size:32px;font-weight:300;color:#5f6368');
const TCH = (() => {
  const f = '500 24px "Google Sans Flex"', w1 = 22 + 10 + 10 + measure('Realistic V7', f) + 24, w2 = 22 + 10 + 10 + measure('Anime Diffusion V7', f) + 24, gap = 20;
  const x1 = 960 - (w1 + w2 + gap) / 2; return { r: { x: x1, y: 666, w: w1, h: 58 }, a: { x: x1 + w1 + gap, y: 666, w: w2, h: 58 } };
})();
const chipR = h('div', { class: 'chip gs', style: `left:${TCH.r.x}px;top:${TCH.r.y}px;width:${TCH.r.w}px;height:58px;border-radius:29px;font-size:24px;font-weight:500;padding:0 24px 0 22px` }, title, '<i style="background:#4c8df6;width:10px;height:10px"></i>Realistic V7');
const chipA = h('div', { class: 'chip gs', style: `left:${TCH.a.x}px;top:${TCH.a.y}px;width:${TCH.a.w}px;height:58px;border-radius:29px;font-size:24px;font-weight:500;padding:0 24px 0 22px` }, title, '<i style="background:#f28b82;width:10px;height:10px"></i>Anime Diffusion V7');
const soon = h('div', { class: 'abs', style: 'left:0;top:762px;width:1920px;display:flex;justify-content:center' }, title);
const soonPill = h('div', { class: 'soon gs' }, soon, '<i></i>V7 系列 · 即将推出<span class="mono" style="font-size:17px;letter-spacing:.14em;opacity:.8;margin-left:6px">COMING SOON</span>');

/* header during product chapters */
const header = h('div', { class: 'abs header', style: 'left:120px;top:36px' });
const hdLotus = h('div', { style: 'width:44px;height:31px' }, header, `<svg viewBox="-130 -140 260 182" width="44" height="31">${PETALS.map(p => `<path d="${petalPath(p.L, p.w)}" fill="${p.c}" opacity=".92" style="mix-blend-mode:multiply" transform="rotate(${p.a})"/>`).join('')}</svg>`);
h('div', { class: 'gs', style: 'font-size:24px;font-weight:500;letter-spacing:-.02em' }, header, 'Lotus <span class="v7">V7</span>');
h('div', { class: 'gs', style: 'height:30px;line-height:30px;padding:0 14px;border-radius:15px;background:#fbe4de;color:#b1352a;font-size:15px' }, header, '即将推出 · Coming soon');
const chapR = h('div', { class: 'abs mono', style: 'left:1800px;top:46px;transform:translateX(-100%);font-size:16px;color:#5f6368;letter-spacing:.04em;white-space:nowrap' }, ui, '01 / Realistic V7');
const chapA = h('div', { class: 'abs mono', style: 'left:1800px;top:46px;transform:translateX(-100%);font-size:16px;color:#5f6368;letter-spacing:.04em;white-space:nowrap' }, ui, '02 / Anime Diffusion V7');

/* realistic overlays */
const sigma = h('div', { class: 'chip glass mono', style: `left:${RC.x + 24}px;top:${RC.y + 24}px;height:40px` }, ui, 'σ 1.00');
const ditBadge = h('div', { class: 'chip glass gs', style: `left:${RC.x + RC.w - 24}px;top:${RC.y + 24}px;height:40px;transform:translateX(-100%)` }, ui, '<i style="background:#d4553f"></i>Diffusion Transformer · denoising');
const LOUPES = [[1440, 150, '光线 · Light'], [470, 640, '材质 · Material'], [930, 690, '倒影 · Reflection']].map(([x, y, s], i) => {
  const l = h('div', { class: 'loupe' }, ui), lab = h('div', { class: 'loupe-l gs' }, ui, s); return { x, y, l, lab, i };
});

/* anime chart */
const CH = { x: 360, y: 140, w: 1200, h: 600 };
const chart = h('div', { class: 'panel', style: `left:${CH.x}px;top:${CH.y}px;width:${CH.w}px;height:${CH.h}px` });
const chSvg = sv('svg', { width: CH.w, height: CH.h, viewBox: `0 0 ${CH.w} ${CH.h}`, style: 'position:absolute;left:0;top:0' }, chart);
const O = { x: 150, y: 470, x1: 1110, y1: 120 };
sv('line', { x1: O.x, y1: O.y, x2: O.x1, y2: O.y, stroke: '#dadce0', 'stroke-width': 1.5 }, chSvg);
sv('line', { x1: O.x, y1: O.y, x2: O.x, y2: O.y1, stroke: '#dadce0', 'stroke-width': 1.5 }, chSvg);
const typC = `M${O.x} 420 C 520 412 800 290 ${O.x1} 172`, v7C = `M${O.x} 200 C 520 192 800 182 ${O.x1} 164`;
const band = (d, w) => { const p = sv('path', { d, fill: 'none', 'stroke-width': w, 'stroke-linecap': 'round' }, chSvg); return p; };
const typBand = band(typC, 90); typBand.setAttribute('stroke', 'rgba(154,160,166,.16)');
const v7Band = band(v7C, 28); v7Band.setAttribute('stroke', 'rgba(212,85,63,.14)');
const typLine = sv('path', { d: typC, fill: 'none', stroke: '#9aa0a6', 'stroke-width': 3, 'stroke-linecap': 'round' }, chSvg);
const v7Line = sv('path', { d: v7C, fill: 'none', stroke: '#d4553f', 'stroke-width': 3.5, 'stroke-linecap': 'round' }, chSvg);
const typLen = typLine.getTotalLength(), v7Len = v7Line.getTotalLength();
const typDot = sv('circle', { cx: O.x, cy: 420, r: 8, fill: '#9aa0a6' }, chSvg);
const v7Dot = sv('circle', { cx: O.x, cy: 200, r: 9, fill: '#d4553f' }, chSvg);
const chText = (x, y, s, o = {}) => { const e = h('div', { class: 'abs ' + (o.cls || 'gs'), style: `left:${x}px;top:${y}px;font-size:${o.fs || 17}px;color:${o.c || '#5f6368'};white-space:nowrap;${o.st || ''}` }, chart, s); return e; };
chText(64, 44, 'Where the quality lives <span style="color:#9aa0a6;font-weight:400;margin-left:10px">质量在哪里</span>', { fs: 24, c: '#1f1f1f', st: 'font-weight:500' });
chText(1136, 50, '<span style="display:inline-block;width:18px;height:3px;background:#9aa0a6;vertical-align:middle;margin-right:8px"></span>典型图像模型 · Typical model<span style="display:inline-block;width:18px;height:3px;background:#d4553f;vertical-align:middle;margin:0 8px 0 26px"></span>Anime Diffusion V7', { st: 'transform:translateX(-100%)', fs: 16 });
chText(O.x, O.y + 16, '朴素 · Plain', { st: 'transform:translateX(-50%)' });
chText(O.x1, O.y + 16, '精雕 · Engineered', { st: 'transform:translateX(-50%)' });
chText((O.x + O.x1) / 2, O.y + 46, '提示词投入 · Prompt effort', { st: 'transform:translateX(-50%)', c: '#9aa0a6', fs: 16 });
chText(58, (O.y + O.y1) / 2, '成品质量 · Quality', { st: 'transform:translate(-50%,-50%) rotate(-90deg)', c: '#9aa0a6', fs: 16 });
const chRough = chText(O.x + 22, 406, '粗糙 · rough', { fs: 17 });
const chFin = chText(O.x + 22, 214, '完成 · finished', { fs: 17, c: '#b1352a' });
chText(O.x1, O.y + 80, '示意图，非实测数据 · schematic, not measured data', { cls: 'mono', fs: 13, c: '#b0b4b9', st: 'transform:translateX(-100%)' });
const DOT_PAGE = { x: CH.x + O.x, y: CH.y + 200 };
const animeChips = h('div', { class: 'abs', style: 'left:0;top:690px;width:1920px;display:flex;justify-content:center;gap:16px' });
const aChips = ['<i style="background:#d4553f"></i>更高的下限 · Raised floor', '<i style="background:#f28b82"></i>一致的画风 · House style', '<i style="background:#c58af9"></i>独有的审美 · Its own look']
  .map(s => h('div', { class: 'chip gs', style: 'position:relative' }, animeChips, s));

/* gallery labels + end card */
const end = h('div', { class: 'abs', style: 'width:1920px;height:1080px' });
const endWm = new Words(h('div', { class: 'abs', style: 'left:0;top:404px;width:1920px;text-align:center' }, end), 'Lotus V7', 'wordmark', 'position:relative;font-size:150px;line-height:150px', true);
endWm.u.slice(-2).forEach(u => u.classList.add('v7'));
const endLine = new Words(h('div', { class: 'abs', style: 'left:0;top:584px;width:1920px;text-align:center' }, end), 'Realistic V7  ·  Anime Diffusion V7', 'gs', 'position:relative;font-size:30px;color:#5f6368');
const endSoon = h('div', { class: 'abs', style: 'left:0;top:656px;width:1920px;display:flex;justify-content:center' }, end);
h('div', { class: 'soon gs' }, endSoon, '<i></i>即将推出<span class="mono" style="font-size:17px;letter-spacing:.14em;opacity:.8;margin-left:6px">COMING SOON</span>');
const endFoot = h('div', { class: 'abs gs', style: 'left:0;top:950px;width:1920px;display:flex;justify-content:center;align-items:center;gap:24px;font-size:22px;color:#5f6368;white-space:nowrap' }, end,
  `<span class="seal" style="width:40px;height:40px;font-size:23px;border-radius:10px">蓮</span><span style="color:#1f1f1f;font-weight:500">Lotus AI Lab</span><span style="color:#c9ccd1">|</span>${higanSVG(40)}<span>A <span class="roman" style="font-size:25px;color:#1f1f1f">Higan</span> Holdings company</span><span style="color:#c9ccd1">|</span><span class="mono" style="font-size:19px">lotuslab.ai</span>`);

/* ═════════════════ canvas scenes ═════════════════ */
const FX = document.getElementById('fx').getContext('2d');
const FX2 = document.getElementById('fx2').getContext('2d');
/* ε is held fixed along one sampling trajectory, so noise only changes strength; fps > 0 lets it flicker (GAN era) */
const nz = (t, arr, fps) => fps ? arr[Math.floor(t * fps) % arr.length] : arr[0];
function drawNoise(c, a, t, arr, x, y, w, hh, fps = 0) {
  if (a <= 0.001) return;
  const g = c.globalAlpha; c.globalAlpha = g * a; c.imageSmoothingEnabled = false;
  c.drawImage(nz(t, arr, fps), x, y, w, hh); c.imageSmoothingEnabled = true; c.globalAlpha = g;
}
function pix(c, img, x, y, w, hh, a = 1) {
  const g = c.globalAlpha; c.globalAlpha = g * a; c.imageSmoothingEnabled = false;
  c.drawImage(img, x, y, w, hh); c.imageSmoothingEnabled = true; c.globalAlpha = g;
}
function img(c, im, a = 1, x = 0, y = 0, w = im.width, hh = im.height) {
  if (a <= 0.001) return; const g = c.globalAlpha; c.globalAlpha = g * a; c.drawImage(im, x, y, w, hh); c.globalAlpha = g;
}

/* history card content: one continuous image evolving era by era */
const PGRID = { c: 16, r: 7 }; const pw = HC.w / PGRID.c, ph = HC.h / PGRID.r;
function histContent(t) {
  const c = hcX; c.globalAlpha = 1; c.fillStyle = '#fff'; c.fillRect(0, 0, HC.w, HC.h);
  if (t < 18.5) {                                           // 2014 GAN: noise that argues itself into a blob
    const blobA = seg(t, 14.0, 16.6, E.io);
    if (blobA > 0) {
      const j = Math.sin(t * 9) * 7 + Math.sin(t * 23) * 3, k = 1 + Math.sin(t * 6.3) * 0.025;
      c.save(); c.translate(HC.w / 2 + j, HC.h / 2); c.scale(k, k * (1 + Math.sin(t * 4.1) * 0.02));
      img(c, hBlob, blobA, -HC.w / 2 - 20, -HC.h / 2 - 10, HC.w + 40, HC.h + 20); c.restore();
    }
    drawNoise(c, 1 - 0.68 * blobA, t, hNoise, 0, 0, HC.w, HC.h, 6);
    pix(c, hPx[12], 0, 0, HC.w, HC.h, seg(t, 18.0, 18.45));
  } else if (t < 24.9) {                                    // 2015–16: caption-conditioned pixels
    const L = [[18.0, 12], [19.0, 24], [19.8, 48], [21.3, 96]];
    let cur = L[0]; for (const l of L) if (t >= l[0]) cur = l;
    const i = L.indexOf(cur);
    if (i > 0) { pix(c, hPx[L[i - 1][1]], 0, 0, HC.w, HC.h); pix(c, hPx[cur[1]], 0, 0, HC.w, HC.h, seg(t, cur[0], cur[0] + 0.22)); }
    else pix(c, hPx[12], 0, 0, HC.w, HC.h);
    img(c, hSoft[6], seg(t, 24.0, 24.85, E.io));
  } else if (t < 33.3) {                                    // 2020 DDPM: forward then reverse
    img(c, hSoft[6]);
    const s = seg(t, 25.0, 28.4, E.io) * (1 - seg(t, 29.2, 32.4, E.io));
    drawNoise(c, Math.pow(s, 0.8), t, hNoise, 0, 0, HC.w, HC.h);
  } else if (t < 39.4) {                                    // 2021 CLIP
    img(c, hSoft[6]); img(c, hSoft[5], seg(t, 33.4, 34.8, E.io));
  } else if (t < 48.3) {                                    // 2022 LDM → mosaic
    const enc = seg(t, 39.4, 40.6, E.io), dec = seg(t, 41.9, 43.1, E.io), sh = enc * (1 - dec);
    const r = mixv({ x: 0, y: 0, w: HC.w, h: HC.h }, { x: LAT.x - HC.x, y: LAT.y - HC.y, w: LAT.w, h: LAT.h }, sh);
    if (sh > 0.001) { c.fillStyle = '#f4f5f7'; c.fillRect(0, 0, HC.w, HC.h); }
    c.save(); c.beginPath(); c.roundRect(r.x, r.y, r.w, r.h, 14 * sh); c.clip();
    const latA = seg(t, 39.6, 40.5) * (1 - seg(t, 42.0, 42.8));
    img(c, dec > 0 ? hSoft[4] : hSoft[5], 1, r.x, r.y, r.w, r.h);
    if (dec > 0 && dec < 1) img(c, hSoft[5], 1 - seg(t, 41.9, 42.9), r.x, r.y, r.w, r.h);
    pix(c, hLatent, r.x, r.y, r.w, r.h, latA);
    const ln = seg(t, 40.6, 40.9) * (1 - seg(t, 40.9, 41.9, E.io));
    drawNoise(c, ln * latA, t, lNoise, r.x, r.y, r.w, r.h);
    c.restore();
    if (t > 43.1) img(c, hSoft[4]);
  } else if (t < 54.4) {                                    // 2023 DiT: patchify, attend, sharpen
    const grid = seg(t, 48.4, 49.2), gap = 6 * win(t, 49.2, 50.2, 52.9, 53.8, E.std, E.io);
    const wave = lerp(-3, PGRID.c + 3, seg(t, 52.5, 53.9, E.io));
    c.fillStyle = '#eef0f3'; c.fillRect(0, 0, HC.w, HC.h);
    for (let j = 0; j < PGRID.r; j++) for (let i = 0; i < PGRID.c; i++) {
      const sx = i * pw, sy = j * ph, dx = sx + gap / 2, dy = sy + gap / 2, dw = pw - gap, dh = ph - gap;
      const passed = clamp((wave - i) * 0.9 + 0.5);
      c.globalAlpha = 1; c.drawImage(hSoft[4], sx, sy, pw, ph, dx, dy, dw, dh);
      if (passed > 0) { c.globalAlpha = passed; c.drawImage(hSoft[3], sx, sy, pw, ph, dx, dy, dw, dh); }
      const glow = Math.exp(-Math.pow(wave - i - 0.5, 2) / 1.2) * 0.38 * (wave > -2 && wave < PGRID.c + 2 ? 1 : 0);
      if (glow > 0.01) { c.globalAlpha = glow; c.fillStyle = '#fff'; c.fillRect(dx, dy, dw, dh); }
    }
    c.globalAlpha = 1;
    if (grid > 0 && gap < 0.5) {
      c.strokeStyle = `rgba(255,255,255,${0.7 * grid})`; c.lineWidth = 1.5; c.beginPath();
      for (let i = 1; i < PGRID.c; i++) { c.moveTo(i * pw, 0); c.lineTo(i * pw, HC.h * grid); }
      for (let j = 1; j < PGRID.r; j++) { c.moveTo(0, j * ph); c.lineTo(HC.w * grid, j * ph); }
      c.stroke();
    }
  } else {                                                  // 2024 → 2025
    img(c, hSoft[3]); img(c, hSoft[2.5], seg(t, 54.6, 56.2, E.io));
  }
}
function drawHist(t) {
  if (t < 11.7 || t > 61.3) return;
  const pIn = seg(t, 11.8, 12.9, E.emph), pOut = seg(t, 60.0, 61.1, E.acc);
  const hide = win(t, 43.6, 43.9, 47.95, 48.25, E.lin, E.lin);
  const a = pIn * (1 - pOut) * (1 - hide);
  if (a <= 0.002) return;
  histContent(t);
  const s = 1 - 0.035 * pOut, w = HC.w * s, x = HC.x + (HC.w - w) / 2, y = HC.y + 8 * pOut, hh = Math.max(1, HC.h * pIn * s);
  drawCard(FX, x, y, w, hh, HC.r, a, (c, X, Y) => { c.drawImage(hcC, X, Y, w, HC.h * s); });
}
function drawDDPM(t) {
  if (t < 25 || t > 33.6) return;
  const out = seg(t, 32.7, 33.4);
  const lv = [0, .35, .6, .82, 1];
  for (let i = 0; i < 5; i++) {
    const a = seg(t, 25.3 + i * 0.62, 25.8 + i * 0.62, E.emph) * (1 - out);
    if (a <= 0) continue;
    const x = thumbX(i), y = TH.y + (1 - a) * 10;
    drawCard(FX, x, y, TH.w, TH.h, 12, a, (c, X, Y) => {
      c.drawImage(hSoft[6], X, Y, TH.w, TH.h);
      drawNoise(c, Math.pow(lv[i], .8), t, hNoise, X, Y, TH.w, TH.h);
    }, { elev: .5 });
    const hl = win(t, 29.2 + (4 - i) * 0.62, 29.5 + (4 - i) * 0.62, 29.9 + (4 - i) * 0.62, 30.6 + (4 - i) * 0.62) * (1 - out);
    if (hl > 0) { FX.save(); FX.globalAlpha = hl; FX.strokeStyle = '#d4553f'; FX.lineWidth = 3; FX.beginPath(); FX.roundRect(x - 4, y - 4, TH.w + 8, TH.h + 8, 15); FX.stroke(); FX.restore(); }
  }
}
function drawMosaic(t) {
  if (t < 43.5 || t > 48.35) return;
  const C = 7, R = 5, tw = HC.w / C, th = HC.h / R;
  const ANIME = new Set([3, 9, 16, 19, 26, 31]);
  for (let j = 0; j < R; j++) for (let i = 0; i < C; i++) {
    const k = j * C + i, rr = rng(500 + k), d = Math.hypot(i - 3, (j - 2) * 1.4) / 4.4;
    const ps = seg(t, 43.55 + d * 0.5, 44.55 + d * 0.5, E.emph), pm = seg(t, 47.2 + (1 - d) * 0.3, 47.95 + (1 - d) * 0.3, E.io);
    const p = ps * (1 - pm);
    const fl = Math.sin(t * 1.6 + k) * 3 * p;
    const sc = lerp(1, 0.82, p), cx = HC.x + i * tw + tw / 2 + (rr() - .5) * 18 * p, cy = HC.y + j * th + th / 2 + (rr() - .5) * 14 * p + fl;
    const w = tw * sc, hh = th * sc, x = cx - w / 2, y = cy - hh / 2;
    const va = seg(t, 44.0 + d * 0.5, 44.8 + d * 0.5) * (1 - seg(t, 47.1, 47.6));
    const R0 = lerp(0, 12, p), rad = [i === 0 && j === 0 ? lerp(28, 12, p) : R0, i === C - 1 && j === 0 ? lerp(28, 12, p) : R0,
      i === C - 1 && j === R - 1 ? lerp(28, 12, p) : R0, i === 0 && j === R - 1 ? lerp(28, 12, p) : R0];
    const isA = ANIME.has(k);
    drawCard(FX, x, y, w, hh, 12, 1, (c, X, Y, Wd, Hd) => {
      c.drawImage(hSoft[4], i * tw, j * th, tw, th, X, Y, Wd, Hd);
      if (va > 0) { c.globalAlpha = va; drawCover(c, isA ? TOON : VARIANTS[k % VARIANTS.length], X, Y, Wd, Hd); c.globalAlpha = 1; }
      if (isA && va > 0) { c.globalAlpha = va; c.fillStyle = '#f28b82'; c.beginPath(); c.arc(X + Wd - 12, Y + 12, 5, 0, 7); c.fill(); c.globalAlpha = 1; }
    }, { elev: p * 0.6, radii: rad });
  }
}
function tokenRect(i) { return { x: tokX0 + i * (TK.s + TK.gap), y: TK.y, w: TK.s, h: TK.s }; }
const TOK_PATCH = Array.from({ length: TK.n }, (_, i) => [2 + i, 3]);
function drawTokens(t) {
  if (t < 49.9 || t > 60.5) return;
  const out = seg(t, 59.3, 60.2);
  const mm = seg(t, 54.2, 55.3, E.io);
  for (let i = 0; i < TK.n; i++) {
    const [pi, pj] = TOK_PATCH[i];
    const p = seg(t, 50.0 + i * 0.06, 50.9 + i * 0.06, E.emph);
    if (p <= 0) continue;
    const src = { x: HC.x + pi * pw + 3, y: HC.y + pj * ph + 3, w: pw - 6, h: ph - 6 };
    const a1 = tokenRect(i), a2 = { x: mmLayout.img[i], y: TK.y + 6, w: MM.s, h: MM.s };
    const r = mixv(src, mixv(a1, a2, mm), p);
    drawCard(FX, r.x, r.y, r.w, r.h, lerp(3, 9, p), 1 - out, (c, X, Y, Wd, Hd) => {
      c.drawImage(hSoft[3], pi * pw, pj * ph, pw, ph, X, Y, Wd, Hd);
    }, { elev: 0.35 * p });
  }
}

/* realistic card: noise → DiT patch resolve → desert → jungle bloom */
const RP = { c: 48, r: 20 }; const rpw = RC.w / RP.c, rph = RC.h / RP.r;
const RP_T = []; { const r = rng(77); for (let j = 0; j < RP.r; j++) for (let i = 0; i < RP.c; i++) RP_T.push(0.62 * (i / RP.c) + 0.2 * (j / RP.r) + 0.18 * r()); }
const PEN = { x: 930 * RC.w / 2000, y: 440 * RC.h / 833 };
const zoomR = t => lerp(1, 1.06, seg(t, 86.6, 96, E.io));
function realContent(t) {
  const c = rcX; c.globalAlpha = 1; c.fillStyle = '#fff'; c.fillRect(0, 0, RC.w, RC.h);
  const z = zoomR(t);
  c.save(); c.translate(PEN.x, PEN.y); c.scale(z, z); c.translate(-PEN.x, -PEN.y);
  if (t < 87.2) {
    drawNoise(c, seg(t, 82.0, 82.8), t, rNoise, 0, 0, RC.w, RC.h);
    const T0 = 83.2, SPAN = 2.9;
    for (let k = 0; k < RP_T.length; k++) {
      const i = k % RP.c, j = (k / RP.c) | 0, st = T0 + RP_T[k] * SPAN, p = seg(t, st, st + 0.9, E.soft);
      if (p <= 0) continue;
      const x = i * rpw, y = j * rph;
      c.globalAlpha = Math.min(1, p * 2); c.drawImage(rSoft, x, y, rpw, rph, x, y, rpw, rph);
      if (p > 0.5) { c.globalAlpha = (p - 0.5) * 2; c.drawImage(rBase.desert, x, y, rpw, rph, x, y, rpw, rph); }
      const g = Math.sin(Math.PI * p) * 0.5;
      if (g > 0.02) { c.globalAlpha = g; c.strokeStyle = '#fff'; c.lineWidth = 1; c.strokeRect(x + .5, y + .5, rpw - 1, rph - 1); }
    }
    c.globalAlpha = 1;
  } else c.drawImage(rBase.desert, 0, 0);
  const jr = seg(t, 90.0, 92.8, E.io);
  if (jr > 0) {
    const R = lerp(0, 2100, jr), F = 300, x = tmpRX;
    x.globalCompositeOperation = 'source-over'; x.clearRect(0, 0, RC.w, RC.h); x.drawImage(rBase.jungle, 0, 0);
    x.globalCompositeOperation = 'destination-in';
    const g = x.createRadialGradient(PEN.x, PEN.y, Math.max(0, R - F), PEN.x, PEN.y, Math.max(1, R));
    g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = g; x.fillRect(0, 0, RC.w, RC.h); x.globalCompositeOperation = 'source-over';
    c.drawImage(tmpR, 0, 0);
    if (jr < 1) { c.globalAlpha = 0.45 * (1 - jr); c.strokeStyle = '#fff'; c.lineWidth = 3; c.beginPath(); c.arc(PEN.x, PEN.y, Math.max(1, R - F * 0.45), 0, Math.PI * 2); c.stroke(); c.globalAlpha = 1; }
  }
  c.restore();
}
function drawRealistic(t) {
  if (t < 81.7 || t > 96.6) return;
  const pT = seg(t, 81.8, 83.2, E.emph);
  const ex = seg(t, 95.4, 96.4, E.acc);
  let r = mixv(TCH.r, RC, pT);
  const rad = lerp(29, RC.r, pT);
  const sc = 1 - 0.05 * ex; r = { x: r.x + r.w * (1 - sc) / 2, y: r.y - 50 * ex, w: r.w * sc, h: r.h * sc };
  realContent(t);
  // above the UI while it grows over the title, below it once overlays (σ, loupes) need to sit on top
  drawCard(t < 83.25 ? FX2 : FX, r.x, r.y, r.w, r.h, rad, 1 - ex, (c, X, Y, Wd, Hd) => {
    const ca = seg(t, 82.1, 82.9);
    if (ca > 0) { c.globalAlpha *= ca; drawCover(c, rcC, X, Y, Wd, Hd); c.globalAlpha /= ca; }
    const la = 1 - seg(t, 81.8, 82.2);
    if (la > 0) {
      c.globalAlpha *= la; c.fillStyle = '#4c8df6'; c.beginPath(); c.arc(X + 27, Y + Hd / 2, 5, 0, 7); c.fill();
      c.fillStyle = '#1f1f1f'; c.font = '500 24px "Google Sans Flex"'; c.textBaseline = 'middle'; c.fillText('Realistic V7', X + 42, Y + Hd / 2 + 1);
    }
  }, { elev: lerp(0.4, 1.2, pT) });
}

/* anime cards (above the UI layer) */
const A1_FACE = { x: 1110 * A1.w / 1920, y: 330 * A1.h / 1088 }, A2_FACE = { x: 610 * A2S.w / 1216, y: 400 * A2S.h / 832 };
function bloomInto(dst, dx, tmp, tx, src, line, face, F, colR, sweep) {
  const w = dst.width, hh = dst.height;
  if (colR - F > Math.hypot(w, hh)) return src;
  dx.globalAlpha = 1; dx.globalCompositeOperation = 'source-over'; dx.fillStyle = '#fcfbf8'; dx.fillRect(0, 0, w, hh);
  const rad = () => { const g = tx.createRadialGradient(face.x, face.y, Math.max(0, colR - F), face.x, face.y, Math.max(1, colR)); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)'); return g; };
  if (colR > 0) {
    tx.globalCompositeOperation = 'source-over'; tx.clearRect(0, 0, w, hh); tx.drawImage(src, 0, 0);
    tx.globalCompositeOperation = 'destination-in'; tx.fillStyle = rad(); tx.fillRect(0, 0, w, hh);
    tx.globalCompositeOperation = 'source-over'; dx.drawImage(tmp, 0, 0);
  }
  if (sweep > 0) {
    tx.globalCompositeOperation = 'source-over'; tx.clearRect(0, 0, w, hh); tx.drawImage(line, 0, 0);
    if (sweep < 1) {
      tx.globalCompositeOperation = 'destination-in';
      const s = lerp(-0.3, 1.3, sweep), g = tx.createLinearGradient(0, 0, w, hh);
      g.addColorStop(clamp(s - 0.25), 'rgba(0,0,0,1)'); g.addColorStop(clamp(s), 'rgba(0,0,0,0)'); tx.fillStyle = g; tx.fillRect(0, 0, w, hh);
    }
    if (colR > 0) { tx.globalCompositeOperation = 'destination-out'; tx.fillStyle = rad(); tx.fillRect(0, 0, w, hh); }
    tx.globalCompositeOperation = 'source-over'; dx.drawImage(tmp, 0, 0);
  }
  return dst;
}
function drawAnime(t) {
  if (t < 99.8 || t > 115.6) return;
  // card 2: moon
  const e2 = seg(t, 105.0, 106.4, E.emph);
  if (e2 > 0) {
    const k2 = lerp(.9, 1, e2); let r2 = { x: A2S.x + A2S.w * (1 - k2) / 2 + 40 * (1 - e2), y: A2S.y + A2S.h * (1 - k2) / 2, w: A2S.w * k2, h: A2S.h * k2 };
    const a2Src = bloomInto(a2C, a2X, tmpB, tmpBX, a2Img, a2Line, A2_FACE, 320, lerp(0, 1300, seg(t, 105.3, 106.9, E.io)), seg(t, 104.95, 105.45, E.io));
    const G2 = galleryRect(t, 3); let rad2 = A2S.r;
    if (G2) { r2 = mixv(r2, G2, G2.p); rad2 = lerp(rad2, 22, G2.p); }
    drawCard(FX2, r2.x, r2.y, r2.w, r2.h, rad2, e2 * (G2 ? G2.a : 1), (c, X, Y, Wd, Hd) => drawCover(c, a2Src, X, Y, Wd, Hd));
  }
  // card 1: dot → large card → left slot → gallery
  const pT = seg(t, 99.9, 101.3, E.emph), toPair = seg(t, 104.4, 106.0, E.io);
  const dot = { x: DOT_PAGE.x - 9, y: DOT_PAGE.y - 9, w: 18, h: 18 };
  let r1 = mixv(mixv(dot, A1, pT), A1S, toPair), rad1 = lerp(9, lerp(A1.r, A1S.r, toPair), pT);
  const a1Src = bloomInto(a1C, a1X, tmpA, tmpAX, a1Img, a1Line, A1_FACE, 460, lerp(0, 2100, seg(t, 101.5, 103.8, E.io)), seg(t, 100.2, 101.6, E.io));
  const G = galleryRect(t, 2), gp = G ? G.p : 0;
  if (G) { r1 = mixv(r1, G, gp); rad1 = lerp(rad1, 22, gp); }
  const cv = G ? G.a : 1;
  drawCard(FX2, r1.x, r1.y, r1.w, r1.h, rad1, cv, (c, X, Y, Wd, Hd) => {
    drawCover(c, a1Src, X, Y, Wd, Hd);
    const f = 1 - seg(t, 99.95, 100.25); if (f > 0) { c.globalAlpha *= f; c.fillStyle = '#d4553f'; c.fillRect(X, Y, Wd, Hd); }
  }, { elev: lerp(0.3, 1.1, pT) });
}

/* finale gallery: four cards drift in a row, then gather into the lotus */
const GH = 300, GY = 318, GW = [720, 720, 529, 438], GG = 32;
const GROW = GW.reduce((a, b) => a + b, 0) + GG * 3;
function galleryRect(t, i) {
  if (t < 110.4) return null;
  const pan = lerp(180, -140, seg(t, 110.4, 114.4, E.io));
  let x = (1920 - GROW) / 2 + pan; for (let k = 0; k < i; k++) x += GW[k] + GG;
  const p = seg(t, 110.4 + (i < 2 ? 0.2 : 0), 111.9 + (i < 2 ? 0.2 : 0), E.emph);
  const order = [0, 3, 1, 2][i], cg = seg(t, 113.7 + order * 0.09, 114.8 + order * 0.09, E.acc);
  let r = { x, y: GY + Math.sin(t * 1.3 + i) * 4, w: GW[i], h: GH };
  if (cg > 0) { const s = lerp(1, 0.12, cg), cx = lerp(x + GW[i] / 2, 960, cg), cy = lerp(GY + GH / 2, 330, cg); r = { x: cx - GW[i] * s / 2, y: cy - GH * s / 2, w: GW[i] * s, h: GH * s }; }
  return { ...r, p, a: 1 - seg(t, 114.2 + order * 0.09, 114.8 + order * 0.09) };
}
function drawGallery(t) {
  if (t < 110.3 || t > 115.6) return;
  [rBase.desert, rBase.jungle].forEach((im, i) => {
    const G = galleryRect(t, i); if (!G) return;
    const from = { x: -760 + i * 100, y: GY + 40, w: GW[i] * .9, h: GH * .9 };
    const r = mixv(from, G, G.p);
    drawCard(FX2, r.x, r.y, r.w, r.h, 22, G.p * G.a, (c, X, Y, Wd, Hd) => drawCover(c, im, X, Y, Wd, Hd));
  });
  const la = win(t, 111.4, 112.2, 113.3, 113.9);
  if (la > 0) {
    FX2.save(); FX2.globalAlpha = la; FX2.font = '400 17px "Google Sans Flex"'; FX2.fillStyle = '#5f6368'; FX2.textAlign = 'left';
    ['Realistic V7', 'Realistic V7', 'Anime Diffusion V7', 'Anime Diffusion V7'].forEach((s, i) => { const G = galleryRect(t, i); FX2.fillText(s, G.x + 4, GY + GH + 34); });
    FX2.restore();
  }
}
/* cherry petals */
const PET = Array.from({ length: 16 }, (_, i) => { const r = rng(700 + i); return { x: 260 + r() * 1500, t0: 100.9 + i * 0.42 + r() * 0.3, d: 5.5 + r() * 2.5, s: 11 + r() * 13, sw: 40 + r() * 70, rot: r() * 6, sp: (r() - .5) * 3, ph: r() * 6 }; });
function drawPetals(t) {
  if (t < 100.8 || t > 110.5) return;
  const fade = 1 - seg(t, 109.2, 110.3);
  for (const p of PET) {
    const q = (t - p.t0) / p.d; if (q < 0 || q > 1) continue;
    const x = p.x + Math.sin(q * 5 + p.ph) * p.sw - q * 160, y = lerp(-40, 1120, q), a = Math.min(1, q * 6, (1 - q) * 5) * fade;
    FX2.save(); FX2.globalAlpha = 0.85 * a; FX2.translate(x, y); FX2.rotate(p.rot + q * p.sp * 6); FX2.scale(1, 0.6 + 0.4 * Math.sin(q * 9 + p.ph));
    const g = FX2.createLinearGradient(0, -p.s, 0, p.s); g.addColorStop(0, '#fbd3dc'); g.addColorStop(1, '#f3a6b8');
    FX2.fillStyle = g; FX2.beginPath(); FX2.moveTo(0, p.s); FX2.bezierCurveTo(-p.s, p.s * .2, -p.s * .7, -p.s * .9, -p.s * .12, -p.s);
    FX2.lineTo(0, -p.s * .7); FX2.lineTo(p.s * .12, -p.s); FX2.bezierCurveTo(p.s * .7, -p.s * .9, p.s, p.s * .2, 0, p.s); FX2.fill(); FX2.restore();
  }
}

/* ═════════════════ DOM updates ═════════════════ */
const SHU = hex('#d4553f');
function updPill(t) {
  let r, dotMode = false, a = 1;
  if (t < 1.1) {
    const d = 22 * spring(seg(t, 0.2, 1.0, E.lin)); dotMode = true; a = seg(t, 0.2, 0.4);
    r = { x: 960 - d / 2, y: 540 - d / 2, w: d, h: d };
  } else if (t < 2.3) {
    const p = seg(t, 1.1, 2.3, E.emph); r = mixv({ x: 949, y: 529, w: 22, h: 22 }, PILL_C, p);
  } else if (t < 10.4) r = PILL_C;
  else if (t < 60.6) r = mixv(PILL_C, PILL_H, seg(t, 10.4, 12.2, E.io));
  else if (t < 70.6) {
    let ex = 0; rowT.forEach(rt => { ex += 50 * seg(t, rt - 0.05, rt + 0.45, E.emph); }); ex += 14 * seg(t, rowT[0], rowT[0] + 0.4);
    ex *= 1 - seg(t, 69.3, 70.5, E.io);
    const sh = Math.sin(t * 31) * 1.4 * win(t, 66.4, 67.4, 68.6, 69.0);
    r = { ...PILL_H, x: PILL_H.x + sh, h: 72 + ex };
  } else if (t < 75.0) r = mixv(PILL_H, PILL_C, seg(t, 70.6, 72.0, E.io));
  else {
    const p = seg(t, 75.0, 75.9, E.acc), w = lerp(PILL_C.w, 72, p);
    r = { x: 960 - w / 2, y: PILL_C.y, w, h: 72 }; a = 1 - seg(t, 75.5, 76.1);
  }
  if (!vis(pill, a)) return;
  pill.style.left = r.x + 'px'; pill.style.top = r.y + 'px'; pill.style.width = r.w + 'px'; pill.style.height = r.h + 'px';
  const m = seg(t, 1.1, 1.8);
  pillBg.style.background = dotMode ? '#d4553f' : rgba(mixv(SHU, [255, 255, 255], m));
  pillBg.style.borderRadius = Math.min(36, r.w / 2, r.h / 2) + 'px';
  const shA = dotMode ? 0 : m;
  pillBg.style.boxShadow = `0 1px 3px rgba(60,64,67,${(0.12 * shA).toFixed(3)}),0 10px 30px rgba(60,64,67,${(0.13 * shA).toFixed(3)})`;
  // children
  const inner = seg(t, 1.8, 2.4) * (1 - seg(t, 75.0, 75.4));
  vis(spark, inner * (t > 75 ? 0 : 1)); spark.style.transform = `rotate(${(seg(t, 1.8, 2.8, E.emph) * 90 + (t > 60 ? Math.sin(t * 3) * 6 : 0)).toFixed(2)}deg)`;
  const n = TYPE_T.filter(x => x <= t).length;
  pWords.forEach(p => { p.sp.textContent = p.s.slice(0, clamp(n - p.start, 0, p.s.length)); });
  const dim = 1 - 0.5 * win(t, 12.0, 12.8, 18.2, 19.0);
  vis(ptext, inner * dim);
  caret.style.opacity = (t < 4.4 || Math.floor(t * 1.8) % 2 === 0) ? 1 : 0;
  vis(send, seg(t, 2.1, 2.6) * (1 - seg(t, 74.9, 75.3)));
  const tap = win(t, 4.42, 4.52, 4.52, 4.8);
  send.style.transform = `scale(${(1 - 0.1 * tap).toFixed(3)})`;
  const rp = seg(t, 4.45, 5.1); ripple.style.transform = `scale(${(rp * 2.4).toFixed(3)})`; ripple.style.opacity = rp > 0 && rp < 1 ? (1 - rp).toFixed(3) : 0;
  const sh = seg(t, 4.5, 5.6, E.io); vis(pillShine, sh > 0 && sh < 1 ? 1 : 0); shineBar.style.transform = `translateX(${lerp(-280, r.w + 20, sh).toFixed(1)}px)`;
  // CLIP highlights
  CLIP_L.forEach((o, i) => {
    const hl = win(t, 33.6 + i * 0.25, 34.2 + i * 0.25, 38.2, 38.9);
    o.span.style.backgroundImage = `linear-gradient(${rgba(hex(o.c), .28)},${rgba(hex(o.c), .28)})`;
    o.span.style.backgroundSize = `100% ${(hl * 38).toFixed(1)}%`;
  });
  // chips
  chipEls.forEach(c => {
    const p = seg(t, c.t, c.t + 0.4, E.lin), fa = seg(t, 69.0 + c.r * 0.7, 70.2 + c.r * 0.7, E.std);
    if (!vis(c.el, Math.min(1, p * 3) * (1 - fa))) return;
    const jit = Math.sin(t * 13 + c.r * 40) * 1.6 * win(t, 66, 67, 68.8, 69.1);
    tr(c.el, c.x + jit, c.y - fa * (50 + 60 * c.r), lerp(0.7, 1, spring(p)), jit * 0.6); fblur(c.el, fa * 6);
  });
}
function updChipsX(t) {
  chipXEls.forEach(c => {
    const p = seg(t, c.t, c.t + 0.4, E.lin), fa = seg(t, 69.0 + c.r * 0.6, 70.1 + c.r * 0.6, E.std);
    if (!vis(c.el, Math.min(1, p * 3) * (1 - fa))) return;
    const jit = Math.sin(t * 11 + c.r * 30) * 2 * win(t, 66.6, 67.4, 68.8, 69.1);
    tr(c.el, c.x + jit, c.y - fa * (60 + 80 * c.r), lerp(0.6, 1, spring(p)), c.rot * spring(p)); fblur(c.el, fa * 6);
  });
}
function updFreeSpark(t) {
  const p = seg(t, 75.0, 76.3, E.emph), a = seg(t, 74.95, 75.05) * (1 - seg(t, 76.0, 76.6));
  if (!vis(freeSpark, a)) return;
  const x0 = PILL_C.x + 24 + 13, y0 = 540, x1 = 960, y1 = 305;
  const x = lerp(x0, x1, p), y = lerp(y0, y1, p) - Math.sin(Math.PI * p) * 60, s = lerp(1, 3.2, p) * (1 - 0.6 * seg(t, 76.0, 76.6));
  tr(freeSpark, x - 13, y - 13, s, 90 + p * 180);
}
function updYear(t) {
  TAGS.forEach(g => {
    const q = win(t, g.a, g.a + 0.5, g.b, g.b + 0.35, E.emph, E.acc);
    if (vis(g.el, q)) { g.el.style.transform = `translateY(${((1 - seg(t, g.a, g.a + 0.5, E.emph)) * 10).toFixed(2)}px)`; }
  });
  const a = seg(t, 11.3, 12.3, E.emph) * (1 - seg(t, 69.2, 70.0));
  if (!vis(odo, a)) return;
  odo.style.transform = `translateY(${((1 - a) * 18).toFixed(2)}px)`; fblur(odo, (1 - seg(t, 11.3, 12.3)) * 8);
  const y = Math.min(2025, yearAt(t));
  digits.forEach(d => { const v = digitVal(y, d.k) % 10; d.s.style.transform = `translateY(${(-v * YS).toFixed(2)}px)`; });
}
function updTimeline(t) {
  const a = seg(t, 10.2, 11.0) * (1 - seg(t, 76.9, 77.8));
  if (!vis(tl, a)) return;
  const draw = seg(t, 10.2, 12.0, E.emph);
  tlBase.style.transform = `scaleX(${draw.toFixed(4)})`;
  const y = yearAt(t), px = yx(Math.max(2014, y));
  tlProg.style.transform = `scaleX(${((px - TLX0) / (TLX1 - TLX0) * seg(t, 11.6, 12.4)).toFixed(4)})`;
  vis(tlDash, seg(t, 11.4, 12.2) * (1 - seg(t, 75.6, 76.4)));
  tlTicks.forEach((k, i) => {
    const d = Math.abs(yx(k.y) - 960) / 830, ap = seg(t, 10.5 + d * 1.1, 11.2 + d * 1.1, E.emph);
    vis(k.tk, ap); if (k.lb) vis(k.lb, ap);
    const reached = y >= k.y - 0.02 && k.st;
    k.tk.style.background = reached ? '#d4553f' : (k.st ? '#c9ccd1' : '#dadce0');
    if (k.lb) k.lb.style.color = Math.abs(y - k.y) < 0.5 ? '#1f1f1f' : '#9aa0a6';
  });
  vis(tlV7, seg(t, 11.6, 12.4)); tlV7.style.transform = `translateX(-50%) scale(${(1 + 0.12 * win(t, 75.8, 76.4, 76.6, 77.2)).toFixed(3)})`;
  vis(tlMark, seg(t, 11.8, 12.4)); tlMark.style.left = px + 'px'; tlMark.style.top = TLY + 'px';
  const pulse = (t * 0.9) % 1; tlMark.style.boxShadow = `0 0 0 ${(4 + pulse * 10).toFixed(1)}px rgba(212,85,63,${(0.22 * (1 - pulse)).toFixed(3)})`;
}
function updEras(t) {
  // 2014 GAN
  const ga = win(t, 13.0, 13.8, 17.4, 18.0);
  if (vis(gan, ga)) {
    const q = (t * 0.7) % 1, fw = q < 0.5;
    const path = fw ? ganArc1 : ganArc2, L = path.getTotalLength(), pt = path.getPointAtLength(L * E.io((q % 0.5) * 2));
    ganDot.setAttribute('cx', pt.x); ganDot.setAttribute('cy', pt.y); ganDot.setAttribute('fill', fw ? '#4c8df6' : '#d4553f');
  }
  // 2015/16 resolution + words fall into the card
  const ra = win(t, 18.4, 18.9, 23.6, 24.2);
  if (vis(resChip, ra)) { const two = t >= 21.3; resTxt[0].style.display = two ? 'none' : ''; resTxt[1].style.display = two ? '' : 'none'; }
  fallWords.forEach(f => {
    const p = seg(t, 18.35 + f.i * 0.12, 19.6 + f.i * 0.12, E.io);
    if (!vis(f.el, p > 0 && p < 1 ? Math.sin(Math.PI * p) * 0.9 : 0)) return;
    const [x0] = wordX[f.p.w], sx = PILL_H.x + 66 + x0, sy = PILL_H.y + 18;
    const tx = HC.x + 330 + f.i * 50, ty = HC.y + 170;
    tr(f.el, lerp(sx, tx, p), lerp(sy, ty, p), lerp(1, 0.7, p)); fblur(f.el, p * 5);
  });
  // 2020 DDPM
  const da = win(t, 25.2, 25.8, 32.7, 33.4);
  if (vis(ddpm, da)) {
    ddLbl.forEach((l, i) => vis(l, seg(t, 25.4 + i * 0.62, 25.9 + i * 0.62)));
    const flip = seg(t, 28.7, 29.2, E.io);
    ddArrows.forEach((a, i) => { vis(a, seg(t, 25.6 + i * 0.62, 26.1 + i * 0.62)); a.style.transform = `rotate(${(flip * 180).toFixed(1)}deg)`; a.style.color = flip > 0.5 ? '#d4553f' : '#9aa0a6'; });
    vis(ddFwd, seg(t, 25.3, 25.8) * (1 - seg(t, 28.6, 28.9))); vis(ddRev, seg(t, 28.9, 29.3));
    vis(ddEq, seg(t, 26.0, 26.8));
  }
  const s = seg(t, 25.0, 28.4, E.io) * (1 - seg(t, 29.2, 32.4, E.io));
  if (vis(tChip, win(t, 24.9, 25.3, 32.5, 33.0))) tChip.textContent = 't = ' + Math.round(s * 1000);
  // 2021 CLIP
  CLIP_L.forEach((o, i) => {
    const p = seg(t, 34.0 + i * 0.3, 35.2 + i * 0.3, E.io), out = seg(t, 38.2, 38.9);
    o.path.setAttribute('stroke-dasharray', `${o.len} ${o.len}`); o.path.setAttribute('stroke-dashoffset', (o.len * (1 - p)).toFixed(1));
    o.path.setAttribute('opacity', (p > 0.002 ? 1 - out : 0).toFixed(3));
    const ra2 = seg(t, 34.9 + i * 0.3, 35.4 + i * 0.3) * (1 - out), pul = ((t - 35) * 0.8 + i * .3) % 1;
    o.ring.setAttribute('opacity', ra2.toFixed(3)); o.ring.setAttribute('r', (16 + 6 * Math.max(0, pul)).toFixed(2)); o.dot.setAttribute('opacity', ra2.toFixed(3));
  });
  const va = win(t, 34.6, 35.2, 38.4, 39.0);
  if (vis(vecWrap, va)) {
    vecRows.forEach((r, ri) => r.cs.forEach((c, i) => { const p = seg(t, 34.8 + ri * 0.35 + i * 0.04, 35.2 + ri * 0.35 + i * 0.04, E.emph); c.style.transform = `scale(${p.toFixed(3)})`; }));
    vis(vecEq, seg(t, 36.2, 36.8)); vis(vecLbl, seg(t, 36.5, 37.1));
  }
  // 2022
  const la = win(t, 39.6, 40.2, 42.6, 43.2);
  if (vis(ldm, la)) { vis(ldmEnc, win(t, 39.6, 40.1, 42.6, 43.1)); vis(ldmDec, seg(t, 41.6, 42.1)); vis(ldmLat, seg(t, 40.3, 40.8)); vis(ldmDn, win(t, 40.6, 41.0, 41.9, 42.3)); }
  const at = win(t, 45.0, 45.6, 47.0, 47.5); if (vis(animeTag, at)) animeTag.style.transform = `translateY(${((1 - seg(t, 45, 45.6, E.emph)) * 12).toFixed(1)}px)`;
  const ot = win(t, 44.4, 45.0, 47.0, 47.5); if (vis(openTag, ot)) openTag.style.transform = `translateY(${((1 - seg(t, 44.4, 45, E.emph)) * 12).toFixed(1)}px)`;
  // 2023 DiT / 2024 MMDiT
  vis(patchLbl, win(t, 48.5, 49.0, 53.3, 53.9));
  vis(ditLbl, win(t, 50.6, 51.1, 53.9, 54.3)); vis(ditAttn, win(t, 51.4, 51.9, 53.9, 54.3));
  const mm = seg(t, 54.2, 55.3, E.io), tout = seg(t, 59.3, 60.2);
  ARCS.forEach(([i, j], k) => {
    const p = seg(t, 51.2 + k * 0.14, 51.9 + k * 0.14, E.io) * (1 - seg(t, 53.9, 54.4));
    const el = arcEls[k]; if (p <= 0) { el.setAttribute('opacity', 0); return; }
    const a = tokenRect(i), b = tokenRect(j), x0 = a.x + TK.s / 2, x1 = b.x + TK.s / 2, y0 = TK.y + TK.s + 4, dep = 16 + Math.abs(j - i) * 5;
    el.setAttribute('d', `M${x0} ${y0} C${x0} ${y0 + dep} ${x1} ${y0 + dep} ${x1} ${y0}`);
    const L = el.getTotalLength(); el.setAttribute('stroke-dasharray', `${L} ${L}`); el.setAttribute('stroke-dashoffset', (L * (1 - p)).toFixed(1));
    el.setAttribute('opacity', (0.35 + 0.4 * ((k * 37) % 10) / 10).toFixed(2));
  });
  txtTok.forEach((tk, i) => {
    const p = seg(t, 54.3 + i * 0.1, 55.4 + i * 0.1, E.io);
    if (!vis(tk.el, Math.min(1, p * 2.5) * (1 - tout))) return;
    const [x0] = wordX[PROMPT.split(' ')[i]], sx = PILL_H.x + 66 + x0 - 12, sy = PILL_H.y + 18;
    tr(tk.el, lerp(sx, mmLayout.txt[i], p), lerp(sy, TK.y + 6, p) - Math.sin(Math.PI * p) * 30);
  });
  const allX = i => i < 5 ? mmLayout.txt[i] + txtTok[i].w / 2 : mmLayout.img[i - 5] + MM.s / 2;
  MARCS.forEach(([i, j], k) => {
    const p = seg(t, 55.6 + k * 0.16, 56.4 + k * 0.16, E.io) * (1 - tout);
    const el = marcEls[k]; if (p <= 0) { el.setAttribute('opacity', 0); return; }
    const x0 = allX(i), x1 = allX(j), y0 = TK.y + 6 + 38, dep = 18 + Math.abs(j - i) * 4;
    el.setAttribute('d', `M${x0} ${y0} C${x0} ${y0 + dep} ${x1} ${y0 + dep} ${x1} ${y0}`);
    const L = el.getTotalLength(); el.setAttribute('stroke-dasharray', `${L} ${L}`); el.setAttribute('stroke-dashoffset', (L * (1 - p)).toFixed(1));
    el.setAttribute('opacity', '0.7');
  });
  if (vis(params, win(t, 55.4, 56.0, 59.3, 60.2))) {
    const e = lerp(8.78, 10.1, seg(t, 55.8, 58.6, E.io));
    pbFill.style.transform = `scaleX(${((e - 8) / 2.4).toFixed(4)})`;
  }
  vis(note, win(t, 12.9, 13.6, 59.6, 60.4));
}
function updCaps(t) {
  CP.p1.update(t, 4.7, 7.25); CP.p2.update(t, 7.6, 10.2); CP.p3.update(t, 72.1, 74.7);
  CP.h14.update(t, 12.4, 17.55); CP.h15.update(t, 18.35, 23.6);
  CP.h20a.update(t, 24.4, 32.55); CP.h20b.update(t, 28.9, 32.55); CP.h20ea.update(t, 24.4, 32.6, 0.25); CP.h20eb.update(t, 28.9, 32.6, 0.25);
  CP.h21.update(t, 33.4, 38.6); CP.h22a.update(t, 39.4, 43.0); CP.h22b.update(t, 43.5, 47.65);
  CP.h23.update(t, 48.4, 53.6); CP.h24.update(t, 54.4, 59.6); CP.h25.update(t, 60.4, 69.1);
  nameReal.update(t, 83.3, 95.2, { st: 0.02 });
  CP.r1.update(t, 83.6, 86.8); CP.r2.update(t, 87.3, 89.8); CP.r3.update(t, 90.7, 95.2);
  nameAnime.update(t, 96.6, 110.0, { st: 0.02 });
  CP.a1.update(t, 96.9, 100.9); CP.a2.update(t, 101.7, 104.6); CP.a3.update(t, 105.9, 110.0);
  CP.g1.update(t, 111.4, 113.5);
}
function updTitle(t) {
  // lotus bloom + drift
  let la = 0, lx = LOTUS_O.x, ly = LOTUS_O.y, ls = 1;
  if (t > 75.8 && t < 83) {
    la = seg(t, 75.8, 76.2) * (1 - seg(t, 81.4, 81.95)); bloom(lotus, t, 76.0);
    ly -= 30 * seg(t, 81.4, 81.95, E.acc);
  } else if (t >= 114.0) { la = seg(t, 114.2, 114.6); bloom(lotus, t, 114.35); ls = 1; }
  if (vis(lotus.el, la)) tr(lotus.el, lx - 130 * lotus.el.k, ly - 140 * lotus.el.k, ls);
  const tv = t > 77 && t < 83;
  if (vis(title, tv ? 1 : 0)) {
    const out = seg(t, 81.45, 81.95, E.acc);
    wm.update(t, 77.7, 81.4, { st: 0.04, dur: 1.1, dy: 40, blur: 14, outDur: 0.45 });
    wmWrap.style.transform = `translateY(${(-out * 30).toFixed(1)}px)`;
    tagZh.update(t, 78.5, 81.4); tagEn.update(t, 78.75, 81.4, { dy: 14 });
    const cr = seg(t, 79.1, 79.8, E.emph), ca = seg(t, 79.3, 80.0, E.emph);
    vis(chipR, cr * (t < 81.8 ? 1 : 0)); tr(chipR, 0, (1 - cr) * 16);
    vis(chipA, ca * (1 - out)); tr(chipA, 0, (1 - ca) * 16 - out * 20);
    const so = seg(t, 79.8, 80.5, E.emph); vis(soonPill, so * (1 - out)); tr(soonPill, 0, (1 - so) * 14 - out * 20);
  }
}
function updHeader(t) {
  const a = seg(t, 82.6, 83.4, E.emph) * (1 - seg(t, 113.4, 114.1));
  if (vis(header, a)) tr(header, 0, (1 - seg(t, 82.6, 83.4, E.emph)) * -12);
  vis(chapR, win(t, 83.0, 83.6, 95.2, 95.8)); vis(chapA, win(t, 96.4, 97.0, 110.0, 110.6));
}
function updReal(t) {
  const sa = win(t, 82.7, 83.2, 87.0, 87.5);
  if (vis(sigma, sa)) { const k = RP_T.reduce((s, v) => s + seg(t, 83.2 + v * 2.9, 84.1 + v * 2.9, E.soft), 0) / RP_T.length; sigma.textContent = 'σ ' + (1 - k).toFixed(2); }
  vis(ditBadge, win(t, 83.0, 83.5, 87.0, 87.5));
  const z = zoomR(t);
  LOUPES.forEach(L => {
    const a = win(t, 87.4 + L.i * 0.35, 87.9 + L.i * 0.35, 89.5, 90.0);
    const ix = L.x * RC.w / 2000, iy = L.y * RC.h / 833;
    const x = RC.x + PEN.x + (ix - PEN.x) * z, y = RC.y + PEN.y + (iy - PEN.y) * z;
    if (vis(L.l, a)) tr(L.l, x, y, lerp(0.6, 1, spring(seg(t, 87.4 + L.i * 0.35, 88.2 + L.i * 0.35, E.lin))));
    if (vis(L.lab, a)) tr(L.lab, x + 36, y - 20 + (1 - a) * 8);
  });
}
function updAnime(t) {
  const a = seg(t, 96.0, 97.0, E.emph), out = seg(t, 99.9, 100.6, E.acc);
  if (vis(chart, a * (1 - out))) {
    chart.style.transform = `translateY(${((1 - a) * 50).toFixed(1)}px) scale(${(1 - 0.03 * out).toFixed(4)})`;
    const p1 = seg(t, 96.8, 98.4, E.io), p2 = seg(t, 97.2, 98.8, E.io);
    typLine.setAttribute('stroke-dasharray', `${typLen} ${typLen}`); typLine.setAttribute('stroke-dashoffset', (typLen * (1 - p1)).toFixed(1)); typLine.setAttribute('opacity', p1 > 0.002 ? 1 : 0);
    v7Line.setAttribute('stroke-dasharray', `${v7Len} ${v7Len}`); v7Line.setAttribute('stroke-dashoffset', (v7Len * (1 - p2)).toFixed(1)); v7Line.setAttribute('opacity', p2 > 0.002 ? 1 : 0);
    typBand.setAttribute('opacity', seg(t, 97.6, 98.6).toFixed(3)); v7Band.setAttribute('opacity', seg(t, 98.0, 98.9).toFixed(3));
    const d1 = spring(seg(t, 98.3, 99.0, E.lin)), d2 = spring(seg(t, 98.6, 99.3, E.lin));
    typDot.setAttribute('r', (8 * d1).toFixed(2)); v7Dot.setAttribute('r', (9 * d2 + 3 * Math.max(0, Math.sin((t - 99.3) * 5)) * seg(t, 99.3, 99.5)).toFixed(2));
    vis(chRough, seg(t, 98.6, 99.1)); vis(chFin, seg(t, 98.9, 99.4));
  }
  const ca = win(t, 106.6, 107.3, 110.0, 110.6);
  if (vis(animeChips, ca)) aChips.forEach((c, i) => { const p = seg(t, 106.6 + i * 0.15, 107.3 + i * 0.15, E.emph); c.style.opacity = p; c.style.transform = `translateY(${((1 - p) * 12).toFixed(1)}px)`; });
}
function updEnd(t) {
  if (!vis(end, t > 114.6 ? 1 : 0)) return;
  endWm.update(t, 114.9, 999, { st: 0.05, dur: 1.2, dy: 40, blur: 14 });
  endLine.update(t, 115.5, 999, { st: 0.04 });
  const so = seg(t, 115.9, 116.6, E.emph); endSoon.style.opacity = so; endSoon.style.transform = `translateY(${((1 - so) * 14).toFixed(1)}px)`;
  const fo = seg(t, 116.4, 117.2, E.emph); endFoot.style.opacity = fo; endFoot.style.transform = `translateY(${((1 - fo) * 10).toFixed(1)}px)`;
}

/* ═════════════════ frame ═════════════════ */
let lastT = -1;
function render(t) {
  t = clamp(t, 0, DUR); lastT = t;
  drawBG(t);
  FX.clearRect(0, 0, W, H); FX2.clearRect(0, 0, W, H);
  drawHist(t); drawDDPM(t); drawMosaic(t); drawTokens(t); drawRealistic(t);
  drawAnime(t); drawGallery(t); drawPetals(t);
  updPill(t); updChipsX(t); updFreeSpark(t); updYear(t); updTimeline(t); updEras(t); updCaps(t);
  updTitle(t); updHeader(t); updReal(t); updAnime(t); updEnd(t);
}
window.__render = render;
window.__meta = { DUR, CHAPTERS, TYPE_T, CHIP_T, CHIPX_T };
document.getElementById('loading').remove();

/* ═════════════════ player ═════════════════ */
if (!RENDER) {
  const fit = () => { const s = Math.min(innerWidth / W, innerHeight / H); stage.style.transform = `translate(${(innerWidth - W * s) / 2}px,${(innerHeight - H * s) / 2}px) scale(${s})`; };
  addEventListener('resize', fit); fit();
  const audio = new Audio('assets/music.m4a'); audio.preload = 'auto';
  const pl = h('div', { id: 'player' }, document.body);
  const bar = h('div', { class: 'bar' }, pl), fill = h('b', null, bar);
  CHAPTERS.forEach(([s]) => h('s', { style: `left:${s / DUR * 100}%` }, bar));
  const ctl = h('div', { class: 'ctl' }, pl);
  const play = h('button', null, ctl, '▶ 播放'), time = h('span', { class: 'time' }, ctl, '0:00 / 2:00');
  const chBtns = CHAPTERS.map(([s, n]) => { const b = h('button', null, ctl, n); b.onclick = () => seek(s); return b; });
  let playing = false, t0 = 0, clock0 = 0, cur = Q.has('t') ? +Q.get('t') : 0;
  const now = () => performance.now() / 1000;
  const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  function seek(s) { cur = clamp(s, 0, DUR); t0 = cur; clock0 = now(); try { audio.currentTime = cur; } catch (e) {} if (!playing) render(cur); }
  function toggle() {
    playing = !playing; play.textContent = playing ? '❚❚ 暂停' : '▶ 播放';
    if (playing) { if (cur >= DUR) cur = 0; t0 = cur; clock0 = now(); audio.currentTime = cur; audio.play().catch(() => {}); } else audio.pause();
  }
  play.onclick = toggle;
  addEventListener('keydown', e => {
    if (e.code === 'Space') { e.preventDefault(); toggle(); }
    const i = CHAPTERS.findIndex(([s], k) => cur >= s && (k === CHAPTERS.length - 1 || cur < CHAPTERS[k + 1][0]));
    if (e.code === 'ArrowRight') seek(CHAPTERS[Math.min(CHAPTERS.length - 1, i + 1)][0]);
    if (e.code === 'ArrowLeft') seek(cur - CHAPTERS[i][0] > 1.5 ? CHAPTERS[i][0] : CHAPTERS[Math.max(0, i - 1)][0]);
  });
  bar.onclick = e => { const r = bar.getBoundingClientRect(); seek((e.clientX - r.left) / r.width * DUR); };
  let idle; addEventListener('mousemove', () => { pl.classList.remove('hide'); clearTimeout(idle); idle = setTimeout(() => playing && pl.classList.add('hide'), 2200); });
  (function loop() {
    if (playing) {
      cur = !audio.paused && audio.readyState > 2 ? audio.currentTime : t0 + (now() - clock0);
      if (cur >= DUR) { cur = DUR; playing = false; play.textContent = '▶ 播放'; audio.pause(); }
      render(cur);
    }
    fill.style.width = (cur / DUR * 100) + '%'; time.textContent = `${fmt(cur)} / ${fmt(DUR)}`;
    chBtns.forEach((b, k) => b.classList.toggle('on', cur >= CHAPTERS[k][0] && (k === CHAPTERS.length - 1 || cur < CHAPTERS[k + 1][0])));
    requestAnimationFrame(loop);
  })();
  render(cur);
} else render(+(Q.get('t') || 0));
return true;
})();
