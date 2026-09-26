/* Lotus V7 teaser — "What the noise was hiding".
   One continuous camera move through a classical gallery, drawn as pseudo-3D:
   a perspective camera projects the architecture and a 38k-point marble sculpture
   onto 2D canvases, and paintings hang on the walls as CSS matrix3d planes
   driven by the same camera. render(t) is a pure function of time. */
'use strict';
window.__ready = (async () => {
const W = 1920, H = 1080, CX = 960, CY = 540, DUR = 120;
const Q = new URLSearchParams(location.search);
const RENDER = Q.has('render');
if (RENDER) document.body.classList.add('render');

/* ───────── easing, math ───────── */
function bez(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const X = t => ((ax * t + bx) * t + cx) * t, Y = t => ((ay * t + by) * t + cy) * t, dX = t => (3 * ax * t + 2 * bx) * t + cx;
  return x => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let t = x; for (let i = 0; i < 8; i++) { const e = X(t) - x; if (Math.abs(e) < 1e-7) return Y(t); const d = dX(t); if (Math.abs(d) < 1e-6) break; t -= e / d; }
    let lo = 0, hi = 1; t = x; for (let i = 0; i < 40; i++) { const v = X(t); if (Math.abs(v - x) < 1e-7) break; if (v < x) lo = t; else hi = t; t = (lo + hi) / 2; }
    return Y(t);
  };
}
const E = { std: bez(.2, 0, 0, 1), emph: bez(.05, .7, .1, 1), acc: bez(.3, 0, .8, .15), io: bez(.65, 0, .35, 1), soft: bez(.4, 0, .2, 1), lin: x => x };
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const lerp = (a, b, p) => a + (b - a) * p;
const seg = (t, a, b, e = E.std) => e(clamp((t - a) / (b - a)));
const win = (t, a, b, c, d, ei = E.std, eo = E.std) => seg(t, a, b, ei) * (1 - seg(t, c, d, eo));
const rgb = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function gauss(r) { let u = 0; while (u === 0) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r()); }
const hash = (a, b) => { let h = Math.imul(a ^ 0x9E3779B9, 0x85EBCA6B) ^ Math.imul(b + 0x632BE5AB, 0xC2B2AE35); h ^= h >>> 16; h = Math.imul(h, 0x7FEB352D); h ^= h >>> 15; return (h >>> 0) / 4294967296; };
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]], sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s], dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const nrm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const lerp3 = (a, b, p) => [lerp(a[0], b[0], p), lerp(a[1], b[1], p), lerp(a[2], b[2], p)];
const rotY = (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c]; };
function keys1(t, ks) {
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) if (t <= ks[i][0]) { const [a, va] = ks[i - 1], [b, vb, e = E.io] = ks[i]; return lerp(va, vb, e((t - a) / (b - a))); }
  return ks[ks.length - 1][1];
}

/* ───────── palette: ivory, stone, ink; clay and brass as accents ───────── */
const P = {
  wall: [236, 229, 216], floor: [219, 210, 195], ceil: [196, 187, 172], stone: [214, 205, 190], plinth: [222, 214, 200],
  dark: [23, 19, 15], walnut: [58, 42, 31], terracotta: [190, 118, 86],
};

/* ───────── camera: Hermite path through keyframes (stop = 1 holds velocity at zero) ───────── */
const CK = [
  [0, [0, 2.05, 7.4], [0, 1.66, 0], 1750, 1],
  [6.2, [0, 1.86, 5.1], [0, 1.66, 0], 1750],
  [11.4, [0.28, 1.76, 3.05], [0, 1.64, 0], 1750],
  [14.6, [0.4, 1.52, 4.15], [0, 1.36, 0], 1750],
  [20.2, [-0.1, 1.52, 3.4], [-1.2, 1.32, -0.8], 1750],
  [23.2, [-1.5, 1.55, 0.45], [-2.9, 1.3, -2.45], 1750],
  [32.0, [-1.65, 1.55, 0.55], [-2.85, 1.28, -2.4], 1750],
  [35.2, [0.2, 2.2, 3.6], [0, 1.35, 0], 1750],
  [44.4, [0.9, 2.3, 3.2], [0, 1.3, 0], 1750],
  [47.2, [1.0, 2.2, 3.15], [0.05, 1.32, 0], 1750],
  [53.6, [1.3, 2.2, 3.3], [0.3, 1.32, 0], 1750],
  [56.4, [1.3, 1.55, 0.8], [2.55, 1.02, -2.3], 1750],
  [58.8, [2.3, 2.1, 2.9], [1.2, 1.2, -1.0], 1750],
  [62.4, [1.0, 2.2, 4.6], [0.25, 1.4, 0.1], 1750],
  [64.2, [0, 2.0, 3.7], [0, 1.36, 0], 1750, 1],
  [71.4, [-0.3, 2.1, 4.1], [0, 1.4, 0], 1750],
  [73.4, [0.05, 0.98, 2.3], [0, 0.66, 0], 1750],
  [79.4, [0, 1.02, 2.45], [0, 0.7, 0], 1750],
  [81.6, [0, 1.72, 4.4], [0, 1.6, 0], 1750],
  [85.2, [0, 2.3, 6.5], [0, 4.45, -5], 1750, 1],
  [87.6, [-1.4, 1.95, 3.2], [-5.5, 2.0, -0.2], 1750],
  [89.4, [-2.05, 1.95, 1.4], [-5.5, 2.02, -1.1], 1750],
  [95.0, [-2.15, 1.95, 1.2], [-5.5, 2.02, -1.0], 1750],
  [97.3, [-2.1, 1.95, 5.2], [-5.5, 2.02, 2.8], 1750],
  [98.9, [-2.05, 1.95, 5.3], [-5.5, 2.02, 2.9], 1750],
  [101.4, [2.05, 1.95, 1.4], [5.5, 2.02, -1.1], 1750],
  [105.0, [2.15, 1.95, 1.2], [5.5, 2.02, -1.0], 1750],
  [107.3, [2.1, 1.95, 5.2], [5.5, 2.02, 2.8], 1750],
  [110.5, [2.05, 1.95, 5.3], [5.5, 2.02, 2.9], 1750],
  [113.6, [0, 2.3, 7.9], [0, 2.45, 0], 1400],
  [117.0, [0, 2.08, 7.0], [0, 2.7, 0], 1400],
  [120, [0, 2.0, 6.6], [0, 2.76, 0], 1400, 1],
];
function camAt(t) {
  const n = CK.length;
  if (t <= CK[0][0]) return [CK[0][1], CK[0][2], CK[0][3]];
  if (t >= CK[n - 1][0]) return [CK[n - 1][1], CK[n - 1][2], CK[n - 1][3]];
  let i = 0; while (i < n - 2 && t > CK[i + 1][0]) i++;
  const k0 = CK[i], k1 = CK[i + 1], h = k1[0] - k0[0], u = (t - k0[0]) / h;
  const tan = (j, c) => {
    const k = CK[j]; if (k[4] || j === 0 || j === n - 1) return c === 3 ? 0 : [0, 0, 0];
    const a = CK[j - 1], b = CK[j + 1], dt = b[0] - a[0];
    return c === 3 ? (b[3] - a[3]) / dt * 0.85 : mul(sub(b[c], a[c]), 0.85 / dt);
  };
  const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
  const hv = c => { const m0 = tan(i, c), m1 = tan(i + 1, c); return [0, 1, 2].map(q => h00 * k0[c][q] + h10 * h * m0[q] + h01 * k1[c][q] + h11 * h * m1[q]); };
  return [hv(1), hv(2), h00 * k0[3] + h10 * h * tan(i, 3) + h01 * k1[3] + h11 * h * tan(i + 1, 3)];
}
let CAM = null;
function setCam(C, T, f) { const F = nrm(sub(T, C)); const R = nrm(cross(F, [0, 1, 0])); const U = cross(R, F); CAM = { C, F, R, U, f }; }
function toCam(p) { const d = [p[0] - CAM.C[0], p[1] - CAM.C[1], p[2] - CAM.C[2]]; return [dot(d, CAM.R), dot(d, CAM.U), dot(d, CAM.F)]; }
function proj(p) { const c = toCam(p); return [CX + CAM.f * c[0] / c[2], CY - CAM.f * c[1] / c[2], c[2]]; }
const NEAR = 0.12;
function projPoly(pts) {
  const cs = pts.map(toCam), out = [];
  for (let i = 0; i < cs.length; i++) {
    const a = cs[i], b = cs[(i + 1) % cs.length], ia = a[2] >= NEAR, ib = b[2] >= NEAR;
    if (ia) out.push(a);
    if (ia !== ib) { const k = (NEAR - a[2]) / (b[2] - a[2]); out.push([a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, NEAR]); }
  }
  return out.map(c => [CX + CAM.f * c[0] / c[2], CY - CAM.f * c[1] / c[2], c[2]]);
}
function poly(ctx, pts, fill, stroke, lw = 1) {
  if (pts.length < 3) return;
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
}
function line3(ctx, a, b, style, lw = 1) {
  let A = toCam(a), B = toCam(b);
  if (A[2] < NEAR && B[2] < NEAR) return;
  if (A[2] < NEAR) { const k = (NEAR - A[2]) / (B[2] - A[2]); A = [A[0] + (B[0] - A[0]) * k, A[1] + (B[1] - A[1]) * k, NEAR]; }
  if (B[2] < NEAR) { const k = (NEAR - B[2]) / (A[2] - B[2]); B = [B[0] + (A[0] - B[0]) * k, B[1] + (A[1] - B[1]) * k, NEAR]; }
  ctx.strokeStyle = style; ctx.lineWidth = lw; ctx.beginPath();
  ctx.moveTo(CX + CAM.f * A[0] / A[2], CY - CAM.f * A[1] / A[2]); ctx.lineTo(CX + CAM.f * B[0] / B[2], CY - CAM.f * B[1] / B[2]); ctx.stroke();
}
function polyline3(ctx, pts, style, lw = 1) { for (let i = 0; i + 1 < pts.length; i++) line3(ctx, pts[i], pts[i + 1], style, lw); }
function boxFaces(c, hs) {
  const [x, y, z] = c, [a, b, d] = hs;
  const v = (sx, sy, sz) => [x + sx * a, y + sy * b, z + sz * d];
  return [
    { n: [0, 1, 0], p: [v(-1, 1, -1), v(1, 1, -1), v(1, 1, 1), v(-1, 1, 1)] },
    { n: [0, -1, 0], p: [v(-1, -1, 1), v(1, -1, 1), v(1, -1, -1), v(-1, -1, -1)] },
    { n: [0, 0, 1], p: [v(-1, 1, 1), v(1, 1, 1), v(1, -1, 1), v(-1, -1, 1)] },
    { n: [0, 0, -1], p: [v(1, 1, -1), v(-1, 1, -1), v(-1, -1, -1), v(1, -1, -1)] },
    { n: [1, 0, 0], p: [v(1, 1, 1), v(1, 1, -1), v(1, -1, -1), v(1, -1, 1)] },
    { n: [-1, 0, 0], p: [v(-1, 1, -1), v(-1, 1, 1), v(-1, -1, 1), v(-1, -1, -1)] },
  ].filter(f => dot(f.n, sub(CAM.C, f.p[0])) > 0);
}
const LIGHT = nrm([-0.45, 0.82, 0.55]);
function faceShade(n, base, k = 1) { const l = 0.62 + 0.3 * Math.max(0, dot(n, LIGHT)) + 0.12 * Math.max(0, n[1]); return mul(base, l * k); }

/* ───────── DOM planes on the same camera ───────── */
const world = document.getElementById('world');
const PX = 100; // css px per world unit
function planeCss(O, Ux, Vy, wu, hu, wpx, hpx) {
  const u = mul(Ux, wu / wpx), v = mul(Vy, hu / hpx), n = mul(nrm(cross(Vy, Ux)), 0.01), o = sub(O, CAM.C);
  const col = w => [PX * dot(w, CAM.R), -PX * dot(w, CAM.U), -PX * dot(w, CAM.F)];
  const a = col(u), b = col(v), c = col(n);
  const tx = CX + PX * dot(o, CAM.R), ty = CY - PX * dot(o, CAM.U), tz = CAM.f - PX * dot(o, CAM.F);
  return `matrix3d(${a[0]},${a[1]},${a[2]},0,${b[0]},${b[1]},${b[2]},0,${c[0]},${c[1]},${c[2]},0,${tx},${ty},${tz},1)`;
}
const planes = [];
function addPlane(el, center, normal, wu, hu, wpx, hpx) {
  el.classList.add('plane'); el.style.width = wpx + 'px'; el.style.height = hpx + 'px'; world.appendChild(el);
  const Nn = nrm(normal), Ux = nrm(cross([0, 1, 0], Nn)), Vy = [0, -1, 0];
  const O = add(add(center, mul(Ux, -wu / 2)), mul(Vy, -hu / 2));
  const pl = { el, O, Ux, Vy, N: Nn, wu, hu, wpx, hpx, center, alpha: 1 };
  planes.push(pl); return pl;
}
function updPlanes() {
  world.style.perspective = CAM.f + 'px';
  for (const pl of planes) {
    const corners = [pl.O, add(pl.O, mul(pl.Ux, pl.wu)), add(pl.O, mul(pl.Vy, pl.hu)), add(add(pl.O, mul(pl.Ux, pl.wu)), mul(pl.Vy, pl.hu))];
    const minD = Math.min(...corners.map(c => toCam(c)[2]));
    const facing = dot(pl.N, sub(CAM.C, pl.center)) > 0;
    if (!(minD > 0.25 && facing && pl.alpha > 0.002)) { pl.el.classList.add('hid'); continue; }
    pl.el.classList.remove('hid');
    pl.el.style.transform = planeCss(pl.O, pl.Ux, pl.Vy, pl.wu, pl.hu, pl.wpx, pl.hpx);
    pl.el.style.opacity = pl.alpha >= 0.999 ? '' : pl.alpha.toFixed(3);
    const br = lerp(0.14, 1, EXPO); pl.el.style.filter = br > 0.995 ? '' : `brightness(${br.toFixed(3)})`;
  }
}

/* ───────── text ───────── */
const ui = document.getElementById('ui');
function h(tag, attrs, parent, html) {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) { if (k === 'class') e.className = attrs[k]; else if (k === 'style') e.style.cssText = attrs[k]; else e.setAttribute(k, attrs[k]); }
  if (html != null) e.innerHTML = html;
  (parent === undefined ? ui : parent)?.appendChild(e); return e;
}
function vis(e, a) {
  if (a <= 0.002) { if (!e.classList.contains('hid')) e.classList.add('hid'); return false; }
  if (e.classList.contains('hid')) e.classList.remove('hid');
  e.style.opacity = a >= 0.999 ? '' : a.toFixed(3); return true;
}
function fblur(e, b) { const v = b > 0.05 ? `blur(${b.toFixed(2)}px)` : ''; if (e.style.filter !== v) e.style.filter = v; }
class Words {
  constructor(parent, text, cls, style) {
    this.el = h('div', { class: cls, style }, parent); this.u = [];
    text.split('\n').forEach(line => {
      const row = h('div', { class: 'row' }, this.el);
      line.split(/(?<= )/).forEach(tk => { const sp = h('span', { class: 'u' }, row); sp.textContent = tk; this.u.push(sp); });
    });
  }
  update(t, tin, tout, o = {}) {
    const st = o.st ?? 0.045, dur = o.dur ?? 1.0, dy = o.dy ?? 16, bl = o.blur ?? 8, od = o.outDur ?? 0.55;
    const n = this.u.length;
    if (t < tin || t > tout + od + n * 0.01 + 0.02) { vis(this.el, 0); return; }
    vis(this.el, 1);
    this.u.forEach((sp, i) => {
      const a = seg(t, tin + i * st, tin + i * st + dur, E.emph), b = seg(t, tout + i * 0.01, tout + i * 0.01 + od, E.acc);
      sp.style.opacity = (a * (1 - b)).toFixed(3);
      const y = (1 - a) * dy - b * dy * 0.4;
      sp.style.transform = Math.abs(y) > 0.01 ? `translateY(${y.toFixed(2)}px)` : '';
      fblur(sp, (1 - a) * bl + b * bl * 0.6);
    });
  }
}
// chapter supers: small caps label + one serif line at a time
const SUPS = [
  { lab: null, dark: true, lines: [['Every block of marble holds a statue.', 2.6, 6.4], ['Every field of noise holds an image.', 7.4, 11.3]] },
  { lab: '01 — Noise and a sentence', lines: [['An image model begins with two things:', 12.6, 16.3], ['pure noise, and a sentence.', 16.7, 20.6]] },
  { lab: '02 — Learning', lines: [['First, it studies millions of pictures\nas they dissolve into noise…', 21.6, 26.4], ['…and learns to undo a single step.', 26.9, 32.3]] },
  { lab: '03 — Carving', lines: [['Then it starts from pure noise\nand repeats that one step, over and over.', 33.6, 38.6], ['Each pass removes a little noise,\nuntil only the image is left.', 39.0, 44.4]] },
  { lab: '04 — Steering', lines: [['At every step, the sentence decides what to keep.', 45.6, 49.2], ['Change a word, and the same noise\nbecomes something else.', 49.6, 53.6]] },
  { lab: '05 — The sketch', lines: [['Carving at full size is slow, so it first shapes\na small, compressed sketch…', 54.6, 58.4], ['…then a decoder restores the detail.', 58.8, 62.5]] },
  { lab: '06 — The workshop', lines: [['Modern models cut the picture into patches…', 63.6, 66.8], ['…and let every patch consult every other,\nso the whole stays coherent.', 67.2, 71.5]] },
  { lab: '07 — The catch', lines: [['Yet most models are only as good as the prompt.', 72.6, 75.6], ['Plain words, rough work. Magic words, fine work.', 76.0, 79.3]] },
  { lab: 'Lotus V7', lines: [['Lotus V7 moves the quality into the model.', 81.4, 84.6], ['Two new models. Coming soon.', 85.0, 87.3]] },
  { lab: 'Realistic V7', lines: [['Photoreal images on a diffusion transformer.', 88.6, 92.2], ['Built for light, material and texture.', 92.6, 95.4], ['One subject. Any world.', 96.2, 98.8]] },
  { lab: 'Anime Diffusion V7', lines: [['Finished illustration from a plain sentence.', 100.8, 104.2], ['A house style — designed, not averaged.', 104.6, 107.2], ['Consistent across characters and scenes.', 107.6, 110.4]] },
];
const scrim = h('div', { style: 'position:absolute;left:0;top:700px;width:1500px;height:380px;pointer-events:none' });
const supEls = SUPS.map(s => {
  const two = s.lines.some(l => l[0].includes('\n'));
  const box = h('div', { class: 'sup', style: `top:${two ? 800 : 858}px` });
  const lab = s.lab ? h('div', { class: 'lab' }, box, `<i></i>${s.lab}`) : null;
  const lines = s.lines.map(([txt]) => new Words(box, txt, 'ln', `position:absolute;left:0;top:${s.lab ? 33 : 0}px;width:1300px;color:${s.dark ? '#f3eee4' : '#1e1c19'}`));
  return { s, box, lab, lines };
});
function updSups(t) {
  const on = SUPS.some(s => t >= s.lines[0][1] - 0.3 && t <= s.lines[s.lines.length - 1][2] + 0.8);
  const dark = EXPO < 0.5, c = dark ? '20,16,12' : '243,238,228', a = dark ? 0.55 : 0.62;
  vis(scrim, on ? 1 : 0); scrim.style.background = `radial-gradient(ellipse 60% 75% at 26% 88%, rgba(${c},${a}) 0%, rgba(${c},${a * 0.5}) 45%, rgba(${c},0) 100%)`;
  supEls.forEach(({ s, box, lab, lines }) => {
    const t0 = s.lines[0][1], t1 = s.lines[s.lines.length - 1][2];
    if (!vis(box, t >= t0 - 0.05 && t <= t1 + 1 ? 1 : 0)) return;
    if (lab) { const a = win(t, t0, t0 + 0.7, t1, t1 + 0.6, E.emph, E.acc); lab.style.opacity = a.toFixed(3); lab.style.transform = `translateX(${((1 - seg(t, t0, t0 + 0.8, E.emph)) * -14).toFixed(1)}px)`; }
    lines.forEach((w, i) => w.update(t, s.lines[i][1], s.lines[i][2]));
  });
}
// end card, under the carved title
const endShade = h('div', { style: 'position:absolute;left:0;top:0;width:1920px;height:200px;background:linear-gradient(180deg,rgba(30,24,18,.5),rgba(30,24,18,0))' }, ui);
const endL = h('div', { class: 'sans', style: 'position:absolute;left:0;top:64px;width:1920px;font-size:16px;letter-spacing:.32em;color:#f3eee4;display:flex;justify-content:center;align-items:center;gap:22px' }, ui,
  '<span style="font-weight:600">LOTUS AI LAB</span><i style="display:block;width:40px;height:1px;background:#d3b47e"></i><span>A HIGAN HOLDINGS COMPANY</span>');
const endR = endL;

/* ───────── load fonts & images ───────── */
await Promise.all(['500 20px "Cormorant Garamond"', 'italic 500 20px "Cormorant Garamond"', '600 20px "Cormorant Garamond"', '600 20px "Cinzel"',
  '400 20px "Instrument Sans"', '600 20px "Instrument Sans"', '400 20px "IBM Plex Mono"'].map(f => document.fonts.load(f, 'Aa')));
await document.fonts.ready;
const loadImg = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
const [IM_DESERT, IM_JUNGLE, IM_SAKURA, IM_MOON] = await Promise.all(['realistic-desert', 'realistic-jungle', 'anime-sakura', 'anime-moon'].map(n => loadImg(`assets/img/${n}.webp`)));

/* ───────── 2D image helpers ───────── */
function cnv(w, hh) { const c = document.createElement('canvas'); c.width = Math.round(w); c.height = Math.round(hh); return c; }
function drawTo(src, w, hh, filter) { const c = cnv(w, hh), x = c.getContext('2d'); x.imageSmoothingQuality = 'high'; if (filter) x.filter = filter; x.drawImage(src, 0, 0, c.width, c.height); return c; }
function downscale(src, w, hh) { let cur = src, cw = src.width, ch = src.height; while (cw / 2 > w && ch / 2 > hh) { cw = Math.round(cw / 2); ch = Math.round(ch / 2); cur = drawTo(cur, cw, ch); } return drawTo(cur, w, hh); }
function padClamp(base, p) {
  const w = base.width, hh = base.height, c = cnv(w + 2 * p, hh + 2 * p), x = c.getContext('2d');
  x.drawImage(base, p, p); x.drawImage(base, 0, 0, 1, hh, 0, p, p, hh); x.drawImage(base, w - 1, 0, 1, hh, w + p, p, p, hh);
  x.drawImage(base, 0, 0, w, 1, p, 0, w, p); x.drawImage(base, 0, hh - 1, w, 1, p, hh + p, w, p); return c;
}
function blurred(base, b) { const p = Math.ceil(b * 3), pc = padClamp(base, p), c = cnv(base.width, base.height), x = c.getContext('2d'); x.filter = `blur(${b}px)`; x.drawImage(pc, -p, -p); return c; }
function warmNoise(w, hh, seed) {
  const c = cnv(w, hh), x = c.getContext('2d'), d = x.createImageData(w, hh), r = rng(seed);
  for (let i = 0; i < w * hh; i++) { const g = clamp(0.62 + gauss(r) * 0.2, 0.1, 1); d.data[4 * i] = 232 * g; d.data[4 * i + 1] = 222 * g; d.data[4 * i + 2] = 206 * g; d.data[4 * i + 3] = 255; }
  x.putImageData(d, 0, 0); return c;
}
function lineart(src, { lo = 0.07, hi = 0.30, col = [52, 44, 40] } = {}) {
  const w = src.width, hh = src.height, b = blurred(src, 0.8), d = b.getContext('2d').getImageData(0, 0, w, hh).data;
  const L = new Float32Array(w * hh); for (let i = 0; i < w * hh; i++) L[i] = (0.299 * d[4 * i] + 0.587 * d[4 * i + 1] + 0.114 * d[4 * i + 2]) / 255;
  const out = cnv(w, hh), ox = out.getContext('2d'), od = ox.createImageData(w, hh), D = od.data;
  for (let y = 1; y < hh - 1; y++) for (let x = 1; x < w - 1; x++) {
    const i = y * w + x;
    const gx = -L[i - w - 1] - 2 * L[i - 1] - L[i + w - 1] + L[i - w + 1] + 2 * L[i + 1] + L[i + w + 1];
    const gy = -L[i - w - 1] - 2 * L[i - w] - L[i - w + 1] + L[i + w - 1] + 2 * L[i + w] + L[i + w + 1];
    const a = Math.pow(clamp((Math.hypot(gx, gy) - lo) / (hi - lo)), 0.85);
    D[4 * i] = col[0]; D[4 * i + 1] = col[1]; D[4 * i + 2] = col[2]; D[4 * i + 3] = a * 230;
  }
  ox.putImageData(od, 0, 0); return out;
}

/* the study piece for chapter 02: an amphora, drawn from scratch */
function drawAmphora(w, hh) {
  const c = cnv(w, hh), x = c.getContext('2d');
  const g = x.createLinearGradient(0, 0, 0, hh); g.addColorStop(0, '#efe8dc'); g.addColorStop(1, '#e2d8c8'); x.fillStyle = g; x.fillRect(0, 0, w, hh);
  x.fillStyle = 'rgba(120,96,70,.10)'; x.fillRect(0, hh * 0.8, w, hh * 0.2);
  const cx = w / 2, top = hh * 0.14, H2 = hh * 0.66, S = H2;
  const prof = [[0, .085], [.04, .07], [.12, .075], [.22, .16], [.34, .215], [.46, .225], [.6, .19], [.76, .12], [.9, .07], [.95, .075], [1, .11]];
  const pt = (k, s) => [cx + s * prof[k][1] * S, top + prof[k][0] * H2];
  x.beginPath(); x.moveTo(...pt(0, -1));
  for (let k = 1; k < prof.length; k++) x.lineTo(...pt(k, -1));
  for (let k = prof.length - 1; k >= 0; k--) x.lineTo(...pt(k, 1)); x.closePath();
  x.save(); x.shadowColor = 'rgba(70,50,30,.35)'; x.shadowBlur = 30; x.shadowOffsetX = 18; x.shadowOffsetY = 10;
  const body = x.createLinearGradient(cx - .24 * S, 0, cx + .24 * S, 0);
  body.addColorStop(0, '#8e4428'); body.addColorStop(.32, '#d98a5f'); body.addColorStop(.55, '#c4633f'); body.addColorStop(1, '#6e321d');
  x.fillStyle = body; x.fill(); x.restore();
  x.save(); x.clip();
  x.fillStyle = '#2b211c'; x.fillRect(0, top + .4 * H2, w, .2 * H2);
  x.strokeStyle = '#c4633f'; x.lineWidth = 3; const y0 = top + .455 * H2, st = 22;
  x.beginPath(); for (let k = -12; k < 12; k++) { const X = cx + k * st; x.moveTo(X, y0 + 26); x.lineTo(X, y0); x.lineTo(X + 16, y0); x.lineTo(X + 16, y0 + 18); x.lineTo(X + 8, y0 + 18); x.lineTo(X + 8, y0 + 8); } x.stroke();
  x.fillStyle = 'rgba(255,240,220,.18)'; x.fillRect(cx - .13 * S, top, .05 * S, H2);
  x.restore();
  x.strokeStyle = '#7e3a22'; x.lineWidth = 9; x.lineCap = 'round';
  for (const s of [-1, 1]) { x.beginPath(); x.moveTo(cx + s * .075 * S, top + .06 * H2); x.bezierCurveTo(cx + s * .2 * S, top + .02 * H2, cx + s * .27 * S, top + .12 * H2, cx + s * .19 * S, top + .26 * H2); x.stroke(); }
  x.strokeStyle = 'rgba(96,110,70,.9)'; x.lineWidth = 3;
  x.beginPath(); x.moveTo(cx + .06 * S, top - 6); x.quadraticCurveTo(cx + .18 * S, top - .1 * H2, cx + .3 * S, top - .05 * H2); x.stroke();
  x.fillStyle = 'rgba(96,110,70,.9)';
  for (let k = 0; k < 6; k++) { const p = k / 6, X = cx + (.08 + .21 * p) * S, Y = top - .06 * H2 * Math.sin(Math.PI * p) - 6; x.beginPath(); x.ellipse(X, Y - 10, 5, 13, -0.6, 0, 7); x.fill(); x.beginPath(); x.ellipse(X + 6, Y + 8, 5, 12, 0.7, 0, 7); x.fill(); }
  return c;
}
const AMPH = drawAmphora(720, 560), AMPH_SOFT = blurred(AMPH, 3), AMPH_NOISE = warmNoise(360, 280, 5);

/* ───────── marble sculpture: 38k points, three states (block, noise, lotus) ───────── */
const NPET = 28000, NPOD = 2600, NPAD = 7400, NPT = NPET + NPOD + NPAD;
const RINGS = [
  { n: 5, L: .24, w: .13, tb: 12, tc: 3, off: 0, r0: .03 }, { n: 7, L: .30, w: .15, tb: 26, tc: 6, off: .5, r0: .045 },
  { n: 9, L: .35, w: .165, tb: 42, tc: 9, off: .25, r0: .06 }, { n: 10, L: .38, w: .17, tb: 58, tc: 13, off: .75, r0: .075 },
];
const pshape = u => Math.sqrt(Math.sin(Math.PI * Math.pow(u, 0.55))) * (1 - 0.22 * u);
const LS = 1.2, PAD_R = 0.55, POD_R = 0.09, FLOWER_Y = 1.14, BLOCK = { c: [0, 1.1 + 0.575, 0], hs: [0.45, 0.575, 0.45] };
const pRing = new Uint8Array(NPT), pK = new Uint8Array(NPT), pU = new Float32Array(NPT), pV = new Float32Array(NPT), kind = new Uint8Array(NPT);
const Lp = new Float32Array(NPT * 3), Ln = new Float32Array(NPT * 3), Bp = new Float32Array(NPT * 3), Bn = new Float32Array(NPT * 3), Np = new Float32Array(NPT * 3);
const gray = new Float32Array(NPT), rnd = new Float32Array(NPT), dir = new Float32Array(NPT * 3), vein = new Float32Array(NPT), tint = new Float32Array(NPT);
function petalPt(ring, k, u, v, open) {
  const R = RINGS[ring], tilt = (R.tc + (R.tb - R.tc) * open) * Math.PI / 180;
  const wu = R.w * pshape(u) + 0.006;
  const x = v * wu, y = u * R.L, cup = 1.25 * (0.6 + 0.4 * (1 - open));
  const z0 = -cup * v * v * wu * (0.5 + 0.5 * Math.sin(Math.PI * Math.min(1, u * 1.2))) + (0.08 * open - 0.03) * R.L * u * u * u;
  const ct = Math.cos(tilt), st = Math.sin(tilt), y1 = y * ct - z0 * st, z1 = y * st + z0 * ct + R.r0;
  const phi = (k + R.off) / R.n * Math.PI * 2 + ring * 0.21, cp = Math.cos(phi), sp = Math.sin(phi);
  return [(z1 * sp + x * cp) * LS, FLOWER_Y + y1 * LS, (z1 * cp - x * sp) * LS];
}
let openCached = -1;
function buildLotus(open) {
  if (Math.abs(open - openCached) < 1e-4) return; openCached = open;
  for (let i = 0; i < NPET; i++) {
    const r = pRing[i], k = pK[i], u = pU[i], v = pV[i], p = petalPt(r, k, u, v, open);
    const du = sub(petalPt(r, k, Math.min(1, u + 0.01), v, open), p), dv = sub(petalPt(r, k, u, clamp(v + 0.02, -1, 1), open), p);
    const n = nrm(cross(du, dv));
    Lp[3 * i] = p[0]; Lp[3 * i + 1] = p[1]; Lp[3 * i + 2] = p[2]; Ln[3 * i] = n[0]; Ln[3 * i + 1] = n[1]; Ln[3 * i + 2] = n[2];
  }
}
{
  const r = rng(42);
  const area = RINGS.map(R => R.n * R.L * R.w), atot = area.reduce((a, b) => a + b, 0);
  let i = 0;
  RINGS.forEach((R, ri) => {
    const cnt = ri === RINGS.length - 1 ? NPET - i : Math.round(NPET * area[ri] / atot);
    for (let c = 0; c < cnt; c++, i++) {
      let u, v; do { u = r(); v = r() * 2 - 1; } while (r() > pshape(u));
      pRing[i] = ri; pK[i] = Math.floor(r() * R.n); pU[i] = u; pV[i] = v; kind[i] = 0; tint[i] = Math.pow(1 - u, 2.2) * (ri < 2 ? 0.5 : 0.3);
    }
  });
  for (; i < NPET + NPOD; i++) {                      // seed pod: short drum with seed holes on top
    kind[i] = 1; const a = r() * Math.PI * 2, top = r() < 0.55;
    let p, n;
    if (top) { const rr = Math.sqrt(r()) * POD_R; p = [Math.cos(a) * rr, FLOWER_Y + 0.15, Math.sin(a) * rr]; n = [0, 1, 0]; }
    else { const yy = r() * 0.14; p = [Math.cos(a) * POD_R, FLOWER_Y + 0.01 + yy, Math.sin(a) * POD_R]; n = [Math.cos(a), 0, Math.sin(a)]; }
    Lp.set(p, 3 * i); Ln.set(n, 3 * i);
    if (top) { let hole = 0; for (let s = 0; s < 7; s++) { const sa = s / 7 * Math.PI * 2, sr = s === 0 ? 0 : 0.054; if (Math.hypot(p[0] - Math.cos(sa) * sr, p[2] - Math.sin(sa) * sr) < 0.013) hole = 1; } tint[i] = hole ? -0.45 : 0.1; }
  }
  for (; i < NPT; i++) {                              // lily pad: wavy disc with veins and a notch
    kind[i] = 2; let a, rr;
    do { a = r() * Math.PI * 2; rr = Math.sqrt(r()) * PAD_R; } while (Math.abs(((a + Math.PI) % (Math.PI * 2)) - Math.PI) < 0.09 && rr > 0.08);
    const y = 1.1 + 0.035 + 0.012 * Math.sin(6 * a) * (rr / PAD_R) - 0.02 * (rr / PAD_R) ** 2;
    Lp.set([Math.cos(a) * rr, y, Math.sin(a) * rr], 3 * i); Ln.set(nrm([0.05 * Math.cos(a) * rr, 1, 0.05 * Math.sin(a) * rr]), 3 * i);
    const va = (a / (Math.PI * 2)) * 14; tint[i] = Math.abs(va - Math.round(va)) < 0.06 && rr > 0.06 ? -0.25 : 0;
  }
  // block surface (five faces, by area) and the noise volume
  const faces = [[[0, 1, 0], 0.9 * 0.9], [[0, 0, 1], 0.9 * 1.15], [[0, 0, -1], 0.9 * 1.15], [[1, 0, 0], 0.9 * 1.15], [[-1, 0, 0], 0.9 * 1.15]];
  const ftot = faces.reduce((a, f) => a + f[1], 0);
  for (let j = 0; j < NPT; j++) {
    let q = r() * ftot, f = 0; while (q > faces[f][1]) { q -= faces[f][1]; f++; }
    const n = faces[f][0], [hx, hy, hz] = BLOCK.hs, c = BLOCK.c;
    let p;
    if (n[1]) p = [(r() * 2 - 1) * hx, hy, (r() * 2 - 1) * hz];
    else if (n[2]) p = [(r() * 2 - 1) * hx, (r() * 2 - 1) * hy, n[2] * hz];
    else p = [n[0] * hx, (r() * 2 - 1) * hy, (r() * 2 - 1) * hz];
    Bp.set(add(p, c), 3 * j); Bn.set(n, 3 * j);
    Np.set([(r() * 2 - 1) * 0.55, 1.05 + r() * 1.3, (r() * 2 - 1) * 0.55], 3 * j);
    gray[j] = clamp(0.62 + gauss(r) * 0.2, 0.2, 1); rnd[j] = r();
    dir.set(nrm([gauss(r), gauss(r), gauss(r)]), 3 * j);
  }
  for (let j = 0; j < NPT; j++) { const x = Bp[3 * j], y = Bp[3 * j + 1], z = Bp[3 * j + 2]; vein[j] = Math.pow(Math.abs(Math.sin((x * 3.1 + y * 2.3 + z * 2.7) * 5.5 + Math.sin(x * 9 + z * 7) * 0.9)), 22); }
  buildLotus(1);
}
const petalTip = (k, open, rot) => rotY(petalPt(3, k, 1, 0, open), rot);

/* sculpture state as a function of time */
const openAt = t => keys1(t, [[0, 1], [49.8, 1], [51.4, 0.08, E.io], [52.6, 0.08], [54.0, 1, E.io]]);
const rotAt = t => t < 33 ? 0 : (t - 33) * 0.07 - Math.max(0, t - 63.8) * 0.07 + Math.max(0, t - 71.6) * 0.07;   // turntable, paused while the patches are out
const CARVE0 = 33.9, CARVE1 = 44.1, STEPS = 40;
function sigmaAt(t) {
  if (t < CARVE0) return 1; if (t >= CARVE1) return 0;
  const g = (t - CARVE0) / (CARVE1 - CARVE0) * STEPS, k = Math.floor(g), f = E.emph(clamp((g - k) / 0.6));
  return Math.pow(1 - (k + f) / STEPS, 1.5);
}
const stepAt = t => clamp(Math.floor((t - CARVE0) / (CARVE1 - CARVE0) * STEPS) + 1, 0, STEPS);
const roughAt = t => keys1(t, [[0, 0], [72.2, 0], [73.0, 1], [75.4, 1], [77.6, 0], [78.6, 0], [80.2, 1], [81.0, 1], [82.8, 0]]);
const quantAt = t => win(t, 54.6, 55.6, 58.8, 61.6, E.io, E.io);
const dimAt = t => win(t, 64.4, 65.2, 70.8, 71.8, E.io, E.io);

/* solid marble mesh of the lotus (drawn once carving is nearly done) */
const MESH_U = 12, MESH_V = 8;
function deform(p, t, id) {
  let [x, y, z] = p;
  const q = quantAt(t); if (q > 0) { const g = 0.075, qq = clamp(q * 1.6 - (y - 1.1) * 1.2); x = lerp(x, Math.round(x / g) * g, qq); y = lerp(y, Math.round(y / g) * g, qq); z = lerp(z, Math.round(z / g) * g, qq); }
  const r = roughAt(t); if (r > 0) { const a = r * 0.03; x += (hash(id, 11) - .5) * 2 * a; y += (hash(id, 12) - .5) * 2 * a; z += (hash(id, 13) - .5) * 2 * a; }
  return rotY([x, y, z], rotAt(t));
}
function shadeQuad(q, n, base, extra = 0) {
  const c = [(q[0][0] + q[2][0]) / 2, (q[0][1] + q[2][1]) / 2, (q[0][2] + q[2][2]) / 2];
  if (dot(n, sub(CAM.C, c)) < 0) n = mul(n, -1);
  const d = Math.max(0, dot(n, LIGHT)), b = clamp(0.64 + 0.34 * d + 0.08 * Math.max(0, n[1]) + extra, 0.3, 1.1);
  return rgb([base[0] * b, base[1] * b, base[2] * b]);
}
function drawLotusMesh(x, t, alpha) {
  if (alpha <= 0.002) return;
  const open = openAt(t), polys = [];
  x.save(); x.globalAlpha = alpha; x.lineJoin = 'round';
  // lily pad first: it always lies beneath the flower
  const RA = 40, RR = 5;
  const padP = (ai, ri) => { const a = ai / RA * Math.PI * 2 + 0.05, rr = 0.08 + ri / RR * (PAD_R - 0.08); return deform([Math.cos(a) * rr, 1.1 + 0.035 + 0.012 * Math.sin(6 * a) * (rr / PAD_R) - 0.02 * (rr / PAD_R) ** 2, Math.sin(a) * rr], t, 5000 + ai * 10 + ri); };
  for (let ai = 1; ai < RA - 1; ai++) for (let ri = 0; ri < RR; ri++) {
    const q = [padP(ai, ri), padP(ai + 1, ri), padP(ai + 1, ri + 1), padP(ai, ri + 1)], pp = projPoly(q); if (pp.length < 3) continue;
    const col = shadeQuad(q, [0, 1, 0], [226, 220, 208], (ri % 2 ? -0.02 : 0)); poly(x, pp, col, col, 0.8);
  }
  for (let ai = 2; ai < RA - 1; ai += 3) polyline3(x, [padP(ai, 0), padP(ai, RR)], 'rgba(120,108,92,.35)', 1);
  // petals and seed pod, painter-sorted
  RINGS.forEach((R, ri) => { for (let k = 0; k < R.n; k++) {
    const G = [];
    for (let iu = 0; iu <= MESH_U; iu++) { const row = []; for (let iv = 0; iv <= MESH_V; iv++) row.push(deform(petalPt(ri, k, Math.pow(iu / MESH_U, 0.9), iv / MESH_V * 2 - 1, open), t, ri * 1000 + k * 100 + iu * 10 + iv)); G.push(row); }
    for (let iu = 0; iu < MESH_U; iu++) for (let iv = 0; iv < MESH_V; iv++) {
      const q = [G[iu][iv], G[iu + 1][iv], G[iu + 1][iv + 1], G[iu][iv + 1]], n = nrm(cross(sub(q[1], q[0]), sub(q[3], q[0])));
      const u = iu / MESH_U, blush = Math.pow(1 - u, 2.2) * (ri === 0 ? 0.55 : 0.35), edge = (iv === 0 || iv === MESH_V - 1) ? 0.04 : 0;
      const base = [lerp(241, 214, blush), lerp(236, 158, blush), lerp(227, 128, blush)];
      const ed = []; if (iv === 0) ed.push([0, 1]); if (iv === MESH_V - 1) ed.push([3, 2]); if (iu === MESH_U - 1) ed.push([1, 2]);
      polys.push({ q, n, base, extra: -0.14 * Math.pow(1 - u, 2) + edge, ed });
    }
  } });
  const PS = 20;
  for (let s2 = 0; s2 < PS; s2++) {
    const a0 = s2 / PS * Math.PI * 2, a1 = (s2 + 1) / PS * Math.PI * 2, r0 = POD_R, y0 = FLOWER_Y + 0.01, y1 = FLOWER_Y + 0.15;
    const P0 = [Math.cos(a0) * r0, y0, Math.sin(a0) * r0], P1 = [Math.cos(a1) * r0, y0, Math.sin(a1) * r0], P2 = [Math.cos(a1) * r0, y1, Math.sin(a1) * r0], P3 = [Math.cos(a0) * r0, y1, Math.sin(a0) * r0];
    const q = [P0, P1, P2, P3].map((p, i) => deform(p, t, 9000 + s2 * 4 + i));
    polys.push({ q, n: nrm([Math.cos((a0 + a1) / 2), 0, Math.sin((a0 + a1) / 2)]), base: [228, 214, 190], extra: 0 });
    const tq = [deform([0, y1, 0], t, 9900), q[3], q[2], q[2]];
    polys.push({ q: tq, n: [0, 1, 0], base: [222, 206, 178], extra: 0 });
  }
  for (const pg of polys) pg.d = toCam([(pg.q[0][0] + pg.q[2][0]) / 2, (pg.q[0][1] + pg.q[2][1]) / 2, (pg.q[0][2] + pg.q[2][2]) / 2])[2];
  polys.sort((a, b) => b.d - a.d);
  for (const pg of polys) {
    const pp = projPoly(pg.q); if (pp.length < 3) continue;
    const col = shadeQuad(pg.q, pg.n, pg.base, pg.extra); poly(x, pp, col, col, 0.8);
    if (pg.ed && pp.length === 4) { x.strokeStyle = 'rgba(112,100,86,.5)'; x.lineWidth = 1.1; x.beginPath(); for (const [a, b] of pg.ed) { x.moveTo(pp[a][0], pp[a][1]); x.lineTo(pp[b][0], pp[b][1]); } x.stroke(); }
  }
  // seed holes
  for (let s3 = 0; s3 < 7; s3++) {
    const a = s3 / 7 * Math.PI * 2, rr = s3 === 0 ? 0 : 0.054, p = deform([Math.cos(a) * rr, FLOWER_Y + 0.151, Math.sin(a) * rr], t, 9950 + s3), pr = proj(p);
    if (pr[2] < NEAR) continue; const r = CAM.f * 0.013 / pr[2];
    x.fillStyle = 'rgba(96,78,58,.55)'; x.beginPath(); x.ellipse(pr[0], pr[1], r, r * clamp(Math.abs(CAM.F[1]) + 0.25, 0.3, 1), 0, 0, 7); x.fill();
  }
  x.restore();
}
const meshAlphaAt = t => t < CARVE0 ? 0 : clamp((1 - sigmaAt(t) - 0.7) / 0.28);
const pointAlphaAt = t => lerp(1, 0.32, meshAlphaAt(t));

/* point splats with a z-buffer */
const spC = cnv(W, H), spX = spC.getContext('2d'), spImg = spX.createImageData(W, H), spU = new Uint32Array(spImg.data.buffer), zb = new Float32Array(W * H);
let dirty = [0, 0, W, H];
function renderSculpture(t) {
  const [x0, y0, x1, y1] = dirty;
  for (let y = y0; y < y1; y++) { spU.fill(0, y * W + x0, y * W + x1); zb.fill(1e9, y * W + x0, y * W + x1); }
  buildLotus(openAt(t));
  const rot = rotAt(t), cr = Math.cos(rot), sr = Math.sin(rot);
  const sig = sigmaAt(t), rough = roughAt(t), q = quantAt(t), step = Math.floor((t - CARVE0) / (CARVE1 - CARVE0) * STEPS);
  const { C, R, U, F, f } = CAM, lx = LIGHT[0], ly = LIGHT[1], lz = LIGHT[2];
  let mx0 = W, my0 = H, mx1 = 0, my1 = 0;
  for (let i = 0; i < NPT; i++) {
    const i3 = 3 * i, ri = rnd[i];
    const nx = Np[i3] + 0.02 * Math.sin(t * 0.7 + ri * 40), ny = Np[i3 + 1] + 0.02 * Math.sin(t * 0.5 + ri * 70), nz = Np[i3 + 2] + 0.02 * Math.cos(t * 0.6 + ri * 55);
    const bl = 1 - seg(t, 6.9 + ri * 1.8, 9.2 + ri * 1.8, E.io);           // the stone loosens into noise
    let lxp = Lp[i3], lyp = Lp[i3 + 1], lzp = Lp[i3 + 2];
    if (q > 0) { const g = 0.075, qq = clamp(q * 1.6 - (lyp - 1.1) * 1.2); lxp = lerp(lxp, Math.round(lxp / g) * g, qq); lyp = lerp(lyp, Math.round(lyp / g) * g, qq); lzp = lerp(lzp, Math.round(lzp / g) * g, qq); }
    if (rough > 0) { const a = rough * 0.045 * (0.4 + ri); lxp += dir[i3] * a; lyp += dir[i3 + 1] * a; lzp += dir[i3 + 2] * a; }
    const rx = lxp * cr + lzp * sr, rz = -lxp * sr + lzp * cr;
    let px, py, pz;
    if (bl > 0) { px = lerp(nx, Bp[i3], bl); py = lerp(ny, Bp[i3 + 1], bl); pz = lerp(nz, Bp[i3 + 2], bl); }
    else if (sig > 0) {
      const js = sig * 0.035;
      px = rx + (nx - rx) * sig + (hash(i, step) - 0.5) * js; py = lyp + (ny - lyp) * sig + (hash(i, step + 999) - 0.5) * js; pz = rz + (nz - rz) * sig + (hash(i + 7, step) - 0.5) * js;
    } else { px = rx; py = lyp; pz = rz; }
    const g = gray[i], ncol = 0.62 * g + 0.2;
    let cl = ncol;
    if (bl > 0) {
      const n0 = Bn[i3], n1 = Bn[i3 + 1], n2 = Bn[i3 + 2];
      const d = 0.5 + 0.38 * Math.max(0, n0 * lx + n1 * ly + n2 * lz) + 0.12 * Math.max(0, n1);
      cl = lerp(ncol, d * (0.93 + 0.07 * g) - vein[i] * 0.18, bl);
    }
    let fr = 241 * cl, fg = 236 * cl, fb = 227 * cl;
    if (sig < 1 && bl <= 0) {
      const n0 = Ln[i3] * cr + Ln[i3 + 2] * sr, n1 = Ln[i3 + 1], n2 = -Ln[i3] * sr + Ln[i3 + 2] * cr;
      const nd = n0 * lx + n1 * ly + n2 * lz, kd = kind[i] === 0 ? Math.abs(nd) : Math.max(0, nd);
      let b = 0.64 + 0.34 * kd + 0.08 * Math.max(0, n1);
      if (kind[i] === 0) b -= 0.14 * (1 - pU[i]) ** 2;
      b += (g - 0.62) * 0.1 - rough * (g - 0.62) * 0.35;
      const tn = tint[i];
      let r2 = 241 * b, g2 = 236 * b, b2 = 227 * b;
      if (tn > 0) { r2 = lerp(r2, 214 * b, tn); g2 = lerp(g2, 150 * b, tn); b2 = lerp(b2, 120 * b, tn); }
      else if (tn < 0) { r2 *= 1 + tn; g2 *= 1 + tn; b2 *= 1 + tn; }
      const s2 = 1 - sig; fr = lerp(fr, r2, s2); fg = lerp(fg, g2, s2); fb = lerp(fb, b2, s2);
    }
    const dx = px - C[0], dy = py - C[1], dz = pz - C[2];
    const cz = dx * F[0] + dy * F[1] + dz * F[2]; if (cz < NEAR) continue;
    const sx = CX + f * (dx * R[0] + dy * R[1] + dz * R[2]) / cz, sy = CY - f * (dx * U[0] + dy * U[1] + dz * U[2]) / cz;
    const s = clamp(Math.round(0.0052 * f / cz), 1, 4), ix = Math.round(sx - s / 2), iy = Math.round(sy - s / 2);
    if (ix < 0 || iy < 0 || ix + s > W || iy + s > H) continue;
    const col = (255 << 24) | (clamp(fb, 0, 255) << 16) | (clamp(fg, 0, 255) << 8) | clamp(fr, 0, 255);
    for (let yy = 0; yy < s; yy++) { let o = (iy + yy) * W + ix; for (let xx = 0; xx < s; xx++, o++) if (cz < zb[o]) { zb[o] = cz; spU[o] = col; } }
    if (ix < mx0) mx0 = ix; if (iy < my0) my0 = iy; if (ix + s > mx1) mx1 = ix + s; if (iy + s > my1) my1 = iy + s;
  }
  const nd = mx1 > mx0 ? [mx0, my0, mx1, my1] : [0, 0, 1, 1];
  const ux0 = Math.min(nd[0], x0), uy0 = Math.min(nd[1], y0), ux1 = Math.max(nd[2], x1), uy1 = Math.max(nd[3], y1);
  spX.putImageData(spImg, 0, 0, ux0, uy0, Math.max(1, ux1 - ux0), Math.max(1, uy1 - uy0));
  dirty = nd;
}

/* ───────── the room ───────── */
const BG = document.getElementById('bg').getContext('2d'), FX = document.getElementById('fx').getContext('2d');
const HALL = { x0: -5.5, x1: 5.5, zb: -5, zf: 8.8, h: 6.8, cor: 6.2 };
const NICHE = { w: 1.45, spring: 3.3, depth: 0.75 };
const EASEL = { c: [-2.6, 1.42, -2.6], n: nrm([0.35, 0, 0.94]) };
const STAND = [2.6, 0, -2.4];
const exposureAt = t => keys1(t, [[0, 0.1], [3, 0.16], [9, 0.3], [13.5, 0.72], [17, 1], [79.4, 1], [80.4, 0.86], [81.2, 1.04], [84, 1]]);
const beamAt = t => keys1(t, [[0, 0.2], [2.4, 1.0], [13, 1], [17, 0.45], [79.4, 0.45], [80.4, 0.9], [82, 0.5], [87, 0.35], [111, 0.35], [114, 0.6], [120, 0.6]]);
let EXPO = 1, BEAM = 1;
function lit(c, k) { return [lerp(P.dark[0], c[0] * k, EXPO), lerp(P.dark[1], c[1] * k, EXPO), lerp(P.dark[2], c[2] * k, EXPO)]; }
const archPts = (z, inset = 0) => {
  const w = NICHE.w - inset, pts = [[-w, 0, z]];
  for (let k = 0; k <= 24; k++) { const a = Math.PI - k / 24 * Math.PI; pts.push([Math.cos(a) * w, NICHE.spring + Math.sin(a) * w, z]); }
  pts.push([w, 0, z]); return pts;
};
const SLABS = []; { const r = rng(9); for (let i = 0; i < 10; i++) for (let j = 0; j < 13; j++) SLABS.push({ x: HALL.x0 + i * 1.1, z: HALL.zb + j * 1.1, v: 0.96 + r() * 0.06 }); }
function drawBoxLit(x, c, hs, base, k) { for (const f of boxFaces(c, hs)) poly(x, projPoly(f.p), rgb(lit(faceShade(f.n, base, 1), k)), rgb(lit([110, 96, 78], 1), .2), 1); }
function drawRoom(t) {
  const x = BG;
  x.fillStyle = rgb(lit([120, 110, 98], 1)); x.fillRect(0, 0, W, H);
  poly(x, projPoly([[HALL.x0, HALL.h, HALL.zb], [HALL.x1, HALL.h, HALL.zb], [HALL.x1, HALL.h, HALL.zf], [HALL.x0, HALL.h, HALL.zf]]), rgb(lit(P.ceil, 0.78)));
  for (let z = HALL.zb + 1.5; z < HALL.zf; z += 1.5) line3(x, [HALL.x0, HALL.h - 0.01, z], [HALL.x1, HALL.h - 0.01, z], rgb(lit([150, 140, 126], 1), .55), 2);
  for (const s of [-1, 1]) {
    const X = s < 0 ? HALL.x0 : HALL.x1;
    poly(x, projPoly([[X, 0, HALL.zb], [X, HALL.h, HALL.zb], [X, HALL.h, HALL.zf], [X, 0, HALL.zf]]), rgb(lit(P.wall, 0.92)));
    poly(x, projPoly([[X, HALL.cor, HALL.zb], [X, HALL.h, HALL.zb], [X, HALL.h, HALL.zf], [X, HALL.cor, HALL.zf]]), rgb(lit(P.wall, 0.8)));
    for (const [yy, a] of [[0.22, .5], [1.0, .35], [1.04, .2], [HALL.cor, .5], [HALL.cor + 0.08, .3]]) line3(x, [X, yy, HALL.zb], [X, yy, HALL.zf], rgb(lit([120, 104, 84], 1), a), 1.5);
  }
  const Z = HALL.zb;
  poly(x, projPoly([[HALL.x0, 0, Z], [HALL.x0, HALL.h, Z], [HALL.x1, HALL.h, Z], [HALL.x1, 0, Z]]), rgb(lit(P.wall, 1)));
  poly(x, projPoly([[HALL.x0, HALL.cor, Z], [HALL.x0, HALL.h, Z], [HALL.x1, HALL.h, Z], [HALL.x1, HALL.cor, Z]]), rgb(lit(P.wall, 0.86)));
  for (const [yy, a] of [[0.22, .5], [1.0, .35], [HALL.cor, .5], [HALL.cor + 0.08, .3]]) line3(x, [HALL.x0, yy, Z + 0.001], [HALL.x1, yy, Z + 0.001], rgb(lit([120, 104, 84], 1), a), 1.5);
  const front = archPts(Z), back = archPts(Z - NICHE.depth);
  poly(x, projPoly(back), rgb(lit([206, 197, 182], 0.9)));
  for (let k = 0; k + 1 < front.length; k++) {
    const q = [front[k], front[k + 1], back[k + 1], back[k]], n = nrm(cross(sub(q[1], q[0]), sub(q[3], q[0])));
    if (dot(n, sub(CAM.C, q[0])) < 0) continue;
    const sh = 0.72 + 0.2 * Math.max(0, dot(mul(n, -1), LIGHT));
    poly(x, projPoly(q), rgb(lit([214, 205, 190], sh)), rgb(lit([214, 205, 190], sh), 1), 1);
  }
  polyline3(x, archPts(Z + 0.002, -0.08), rgb(lit([130, 112, 90], 1), .45), 1.5);
  polyline3(x, archPts(Z + 0.002, -0.16), rgb(lit([255, 255, 255], 1), .35), 1.2);
  for (const s of [-1, 1]) {
    drawBoxLit(x, [s * 2.35, HALL.cor / 2, Z + 0.07], [0.28, HALL.cor / 2, 0.07], P.wall, 1.02);
    drawBoxLit(x, [s * 2.35, HALL.cor - 0.12, Z + 0.11], [0.36, 0.12, 0.11], P.wall, 1.0);
    drawBoxLit(x, [s * 2.35, 0.14, Z + 0.1], [0.34, 0.14, 0.1], P.wall, 0.96);
  }
  for (const s of SLABS) {
    const dd = Math.hypot(s.x + 0.55, s.z + 0.55), k = s.v * (1 - 0.22 * clamp((dd - 1.5) / 9));
    poly(x, projPoly([[s.x, 0, s.z], [s.x + 1.1, 0, s.z], [s.x + 1.1, 0, s.z + 1.1], [s.x, 0, s.z + 1.1]]), rgb(lit(P.floor, k)), rgb(lit([150, 136, 118], 1), .22), 1);
  }
  for (const [r, a] of [[1.35, .35], [1.5, .22]]) { const c = []; for (let k = 0; k <= 64; k++) { const an = k / 64 * Math.PI * 2; c.push([Math.cos(an) * r, 0.002, Math.sin(an) * r]); } polyline3(x, c, rgb(lit([140, 120, 96], 1), a), 1.5); }
  const pc = proj([0, 0, 0]);
  if (pc[2] > NEAR) {
    const sq = 0.3 + 0.4 * clamp((CAM.C[1] - 0.5) / 4), rr = CAM.f * 2.2 / pc[2];
    const g = x.createRadialGradient(pc[0], pc[1], 0, pc[0], pc[1], rr); g.addColorStop(0, `rgba(255,236,206,${0.22 * BEAM})`); g.addColorStop(1, 'rgba(255,236,206,0)');
    x.save(); x.translate(pc[0], pc[1]); x.scale(1, sq); x.translate(-pc[0], -pc[1]); x.fillStyle = g; x.fillRect(pc[0] - rr, pc[1] - rr, rr * 2, rr * 2); x.restore();
    const r2 = CAM.f * 0.95 / pc[2], g2 = x.createRadialGradient(pc[0], pc[1], 0, pc[0], pc[1], r2); g2.addColorStop(0, 'rgba(40,30,20,.35)'); g2.addColorStop(1, 'rgba(40,30,20,0)');
    x.save(); x.translate(pc[0], pc[1]); x.scale(1, sq); x.translate(-pc[0], -pc[1]); x.fillStyle = g2; x.fillRect(pc[0] - r2, pc[1] - r2, r2 * 2, r2 * 2); x.restore();
  }
  // easel for the study piece
  const ez = EASEL.c, en = EASEL.n, er = nrm(cross([0, 1, 0], en));
  const top = add(ez, [0, 0.52, 0]), bk = add(add(ez, mul(en, -0.5)), [0, -1.42, 0]);
  const fl = add(add(ez, mul(er, -0.42)), [0, -1.42, 0]), fr = add(add(ez, mul(er, 0.42)), [0, -1.42, 0]);
  for (const [a, b] of [[top, fl], [top, fr], [top, bk]]) line3(x, a, b, rgb(lit(P.walnut, 1), 1), 5);
  line3(x, add(add(ez, mul(er, -0.5)), [0, -0.37, 0]), add(add(ez, mul(er, 0.5)), [0, -0.37, 0]), rgb(lit(P.walnut, 1.1), 1), 7);
  drawColumnEnds(x);
  const pw = proj([0, 1.8, -0.5]);
  if (pw[2] > NEAR) { const rw = CAM.f * 5.5 / pw[2], gw = x.createRadialGradient(pw[0], pw[1], 0, pw[0], pw[1], rw); gw.addColorStop(0, `rgba(255,238,212,${0.16 * EXPO})`); gw.addColorStop(1, 'rgba(255,238,212,0)'); x.fillStyle = gw; x.fillRect(0, 0, W, H); }
  const g3 = x.createLinearGradient(0, 0, 0, H * 0.55); g3.addColorStop(0, `rgba(32,26,20,${0.42 - 0.12 * EXPO})`); g3.addColorStop(1, 'rgba(32,26,20,0)');
  x.fillStyle = g3; x.fillRect(0, 0, W, H);
}

/* ───────── DOM planes: study canvas, strip, inscription, paintings ───────── */
function canvasPlane(w, hh, center, normal, wu, hu) {
  const el = h('div', null, null), c = h('canvas', { width: w, height: hh, style: `display:block;width:${w}px;height:${hh}px` }, el);
  const pl = addPlane(el, center, normal, wu, hu, w, hh); pl.c = c; pl.x = c.getContext('2d'); return pl;
}
const study = canvasPlane(720, 560, EASEL.c, EASEL.n, 0.92, 0.716);
study.el.style.boxShadow = '0 0 0 14px #3a2a1f, 0 18px 30px rgba(40,28,18,.35)';
const strip = canvasPlane(1100, 250, add(add(EASEL.c, [0, -0.5, 0]), mul(EASEL.n, 0.03)), EASEL.n, 0.88, 0.2);
const inscr = h('div', { class: 'inscr' }, null, '<div class="t">LOTUS V7</div><div class="m">REALISTIC V7 · ANIME DIFFUSION V7</div><div class="s">COMING SOON</div>');
addPlane(inscr, [0, 5.47, HALL.zb + 0.01], [0, 0, 1], 4.0, 1.25, 1600, 500);
const sweep = h('div', { style: 'position:absolute;inset:0;background:linear-gradient(100deg,rgba(255,244,220,0) 35%,rgba(255,244,220,.75) 50%,rgba(255,244,220,0) 65%);background-size:300% 100%;mix-blend-mode:soft-light' }, inscr);
function framePlane(img, cw, chh, imgW, center, normal, label, subl) {
  const ppm = cw / imgW, mat = Math.round(0.15 * ppm), fr = Math.round(0.11 * ppm);
  const el = h('div', { class: 'frame', style: `padding:${fr}px` }, null), m = h('div', { class: 'mat', style: `padding:${mat}px` }, el);
  const c = h('canvas', { width: cw, height: chh, style: `width:${cw}px;height:${chh}px` }, m);
  const wpx = cw + 2 * mat + 2 * fr, hpx = chh + 2 * mat + 2 * fr;
  const pl = addPlane(el, center, normal, wpx / ppm, hpx / ppm, wpx, hpx); pl.c = c; pl.x = c.getContext('2d'); pl.img = img;
  const lab = h('div', { class: 'brass' }, null, `<b>${label}</b><span>${subl}</span>`);
  const labCenter = add(center, [0, -(hpx / ppm) / 2 - 0.22, 0]);
  addPlane(lab, add(labCenter, mul(nrm(cross([0, 1, 0], normal)), -(wpx / ppm) / 2 + 0.45)), normal, 0.9, 0.2, 540, 120);
  pl.x.fillStyle = '#f4efe6'; pl.x.fillRect(0, 0, cw, chh);
  return pl;
}
const RW = 2.5, AW1 = 1.96, AW2 = 1.62;
const fR1 = framePlane(downscale(IM_DESERT, 1500, 625), 1500, 625, RW, [HALL.x0 + 0.02, 2.02, -1.1], [1, 0, 0], 'REALISTIC V7', 'Photoreal · diffusion transformer');
const fR2 = framePlane(downscale(IM_JUNGLE, 1500, 625), 1500, 625, RW, [HALL.x0 + 0.02, 2.02, 2.9], [1, 0, 0], 'REALISTIC V7', 'One subject, any world');
const fA1 = framePlane(downscale(IM_SAKURA, 1330, 754), 1330, 754, AW1, [HALL.x1 - 0.02, 2.02, -1.1], [-1, 0, 0], 'ANIME DIFFUSION V7', 'Plain sentence, finished work');
const moonFlat = (() => { const c = cnv(IM_MOON.width, IM_MOON.height), x = c.getContext('2d'); x.fillStyle = '#e9eef8'; x.fillRect(0, 0, c.width, c.height); x.drawImage(IM_MOON, 0, 0); return c; })();
const fA2 = framePlane(downscale(moonFlat, 1100, 753), 1100, 753, AW2, [HALL.x1 - 0.02, 2.02, 2.9], [-1, 0, 0], 'ANIME DIFFUSION V7', 'A house style, held steady');
const fR1soft = blurred(fR1.img, 6), rNoise = warmNoise(750, 313, 21), fR2base = downscale(IM_DESERT, 1500, 625);
const fA1line = lineart(fA1.img), fA2line = lineart(fA2.img);
const tmpA = cnv(1500, 800), tmpX = tmpA.getContext('2d');

function updStudy(t) {
  // 02 · forward: amphora → noise; reverse: noise → amphora
  const x = study.x, s = seg(t, 22.2, 25.8, E.io) * (1 - seg(t, 27.2, 31.6, E.io));
  x.globalAlpha = 1; x.drawImage(AMPH, 0, 0);
  if (s > 0) { x.globalAlpha = Math.min(1, s * 1.6) * 0.9; x.drawImage(AMPH_SOFT, 0, 0); x.globalAlpha = Math.pow(s, 0.85); x.imageSmoothingEnabled = false; x.drawImage(AMPH_NOISE, 0, 0, 720, 560); x.imageSmoothingEnabled = true; x.globalAlpha = 1; }
  x.fillStyle = 'rgba(244,239,230,.88)'; x.fillRect(22, 22, 160, 40); x.fillStyle = '#1e1c19'; x.font = '400 22px "IBM Plex Mono"'; x.fillText(`t = ${String(Math.round(s * 1000)).padStart(4, ' ')}`, 34, 50);
  const y = strip.x; y.fillStyle = '#f4efe6'; y.fillRect(0, 0, 1100, 250);
  const lv = [0, .3, .55, .8, 1], flip = seg(t, 26.6, 27.2, E.io);
  for (let k = 0; k < 5; k++) {
    const X = 30 + k * 214;
    y.globalAlpha = t > 26 ? 1 : seg(t, 22.4 + k * 0.7, 22.9 + k * 0.7); y.drawImage(AMPH, X, 30, 170, 132);
    if (lv[k] > 0) { y.globalAlpha *= Math.pow(lv[k], .85); y.imageSmoothingEnabled = false; y.drawImage(AMPH_NOISE, X, 30, 170, 132); y.imageSmoothingEnabled = true; }
    const hl = win(t, 27.3 + (4 - k) * 0.85, 27.6 + (4 - k) * 0.85, 27.9 + (4 - k) * 0.85, 28.6 + (4 - k) * 0.85);
    y.globalAlpha = 1;
    if (hl > 0) { y.strokeStyle = `rgba(196,99,63,${hl})`; y.lineWidth = 4; y.strokeRect(X - 4, 26, 178, 140); }
    y.fillStyle = '#5a5249'; y.font = '400 20px "IBM Plex Mono"'; y.textAlign = 'center'; y.fillText(['0', '250', '500', '750', '1000'][k], X + 85, 200); y.textAlign = 'left';
    if (k < 4) {
      y.save(); y.translate(X + 192, 96); if (flip > 0.5) y.scale(-1, 1); y.strokeStyle = flip > 0.5 ? '#c4633f' : '#8f8577'; y.lineWidth = 3;
      y.beginPath(); y.moveTo(-10, 0); y.lineTo(10, 0); y.moveTo(3, -7); y.lineTo(10, 0); y.lineTo(3, 7); y.stroke(); y.restore();
    }
  }
  y.fillStyle = flip > 0.5 ? '#c4633f' : '#8f8577'; y.font = '600 17px "Instrument Sans"';
  y.fillText(flip > 0.5 ? 'LEARN TO UNDO EACH STEP  ←' : 'ADD NOISE, STEP BY STEP  →', 30, 238);
}
function bloomInto(dst, src, line, face, F, colR, sweepP) {
  const x = dst.x, w = dst.c.width, hh = dst.c.height;
  if (colR - F > Math.hypot(w, hh)) { if (dst.done !== 1) { x.drawImage(src, 0, 0, w, hh); dst.done = 1; } return; }
  dst.done = 0;
  x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.fillStyle = '#f7f3ec'; x.fillRect(0, 0, w, hh);
  const rad = () => { const g = tmpX.createRadialGradient(face[0], face[1], Math.max(0, colR - F), face[0], face[1], Math.max(1, colR)); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)'); return g; };
  if (colR > 0) { tmpX.globalCompositeOperation = 'source-over'; tmpX.clearRect(0, 0, w, hh); tmpX.drawImage(src, 0, 0, w, hh); tmpX.globalCompositeOperation = 'destination-in'; tmpX.fillStyle = rad(); tmpX.fillRect(0, 0, w, hh); tmpX.globalCompositeOperation = 'source-over'; x.drawImage(tmpA, 0, 0, w, hh, 0, 0, w, hh); }
  if (sweepP > 0) {
    tmpX.globalCompositeOperation = 'source-over'; tmpX.clearRect(0, 0, w, hh); tmpX.drawImage(line, 0, 0);
    if (sweepP < 1) { tmpX.globalCompositeOperation = 'destination-in'; const s = lerp(-0.3, 1.3, sweepP), g = tmpX.createLinearGradient(0, 0, w, hh); g.addColorStop(clamp(s - 0.25), 'rgba(0,0,0,1)'); g.addColorStop(clamp(s), 'rgba(0,0,0,0)'); tmpX.fillStyle = g; tmpX.fillRect(0, 0, w, hh); }
    if (colR > 0) { tmpX.globalCompositeOperation = 'destination-out'; tmpX.fillStyle = rad(); tmpX.fillRect(0, 0, w, hh); }
    tmpX.globalCompositeOperation = 'source-over'; x.drawImage(tmpA, 0, 0, w, hh, 0, 0, w, hh);
  }
}
const RP = { c: 30, r: 12 }, RP_T = []; { const r = rng(77); for (let j = 0; j < RP.r; j++) for (let i = 0; i < RP.c; i++) RP_T.push(0.64 * (i / RP.c) + 0.18 * (j / RP.r) + 0.18 * r()); }
function updFrames(t) {
  { // Realistic 1: patch-by-patch denoise
    const x = fR1.x, w = 1500, hh = 625, pw = w / RP.c, ph = hh / RP.r;
    if (t < 88.4) { if (fR1.state !== 0) { x.fillStyle = '#f4efe6'; x.fillRect(0, 0, w, hh); fR1.state = 0; } }
    else if (t < 93.2) {
      fR1.state = 1; x.fillStyle = '#f4efe6'; x.fillRect(0, 0, w, hh);
      x.globalAlpha = seg(t, 88.4, 88.9); x.imageSmoothingEnabled = false; x.drawImage(rNoise, 0, 0, w, hh); x.imageSmoothingEnabled = true;
      for (let k = 0; k < RP_T.length; k++) {
        const i = k % RP.c, j = (k / RP.c) | 0, st = 89.0 + RP_T[k] * 3.0, p = seg(t, st, st + 0.8, E.soft); if (p <= 0) continue;
        const X = i * pw, Y = j * ph;
        x.globalAlpha = Math.min(1, p * 2); x.drawImage(fR1soft, X, Y, pw, ph, X, Y, pw, ph);
        if (p > 0.5) { x.globalAlpha = (p - 0.5) * 2; x.drawImage(fR1.img, X, Y, pw, ph, X, Y, pw, ph); }
        const g = Math.sin(Math.PI * p) * 0.45; if (g > 0.02) { x.globalAlpha = g; x.strokeStyle = '#fff'; x.lineWidth = 1; x.strokeRect(X + .5, Y + .5, pw - 1, ph - 1); }
      }
      x.globalAlpha = 1;
    } else if (fR1.state !== 2) { x.globalAlpha = 1; x.drawImage(fR1.img, 0, 0); fR1.state = 2; }
  }
  { // Realistic 2: the jungle opens out from the penguin
    const x = fR2.x, w = 1500, hh = 625, jr = seg(t, 97.0, 98.8, E.io);
    if (t < 97.0) { x.globalAlpha = 1; x.fillStyle = '#f4efe6'; x.fillRect(0, 0, w, hh); x.globalAlpha = seg(t, 95.6, 96.6); if (x.globalAlpha > 0) x.drawImage(fR2base, 0, 0); x.globalAlpha = 1; fR2.state = 0; }
    else if (jr < 1) {
      fR2.state = 1; x.drawImage(fR2base, 0, 0);
      const cx = 930 / 2000 * w, cy = 440 / 833 * hh, R = lerp(0, 1800, jr), F = 260;
      tmpX.globalCompositeOperation = 'source-over'; tmpX.clearRect(0, 0, w, hh); tmpX.drawImage(fR2.img, 0, 0);
      tmpX.globalCompositeOperation = 'destination-in'; const g = tmpX.createRadialGradient(cx, cy, Math.max(0, R - F), cx, cy, Math.max(1, R)); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)'); tmpX.fillStyle = g; tmpX.fillRect(0, 0, w, hh); tmpX.globalCompositeOperation = 'source-over';
      x.drawImage(tmpA, 0, 0, w, hh, 0, 0, w, hh);
      x.globalAlpha = 0.5 * (1 - jr); x.strokeStyle = '#fff'; x.lineWidth = 3; x.beginPath(); x.arc(cx, cy, Math.max(1, R - F * 0.45), 0, 7); x.stroke(); x.globalAlpha = 1;
    } else if (fR2.state !== 2) { x.drawImage(fR2.img, 0, 0); fR2.state = 2; }
  }
  // Anime 1 and 2: line art first, then colour flows out from the face
  if (t < 100.2) { if (fA1.state !== 0) { fA1.x.fillStyle = '#f4efe6'; fA1.x.fillRect(0, 0, 1330, 754); fA1.state = 0; fA1.done = 0; } }
  else { fA1.state = 1; bloomInto(fA1, fA1.img, fA1line, [1110 / 1920 * 1330, 330 / 1088 * 754], 420, lerp(0, 2000, seg(t, 101.9, 104.3, E.io)), seg(t, 100.3, 101.9, E.io)); }
  if (t < 106.4) { if (fA2.state !== 0) { fA2.x.fillStyle = '#f4efe6'; fA2.x.fillRect(0, 0, 1100, 753); fA2.state = 0; fA2.done = 0; } }
  else { fA2.state = 1; bloomInto(fA2, fA2.img, fA2line, [610 / 1216 * 1100, 400 / 832 * 753], 320, lerp(0, 1500, seg(t, 107.4, 109.4, E.io)), seg(t, 106.5, 107.6, E.io)); }
  inscr.children[0].style.opacity = (0.3 + 0.7 * seg(t, 81.2, 83.2)).toFixed(3);
  inscr.children[1].style.opacity = (0.2 + 0.8 * seg(t, 82.4, 84.0)).toFixed(3);
  inscr.children[2].style.opacity = (0.15 + 0.85 * seg(t, 83.0, 84.6)).toFixed(3);
  sweep.style.backgroundPosition = `${lerp(100, -50, seg(t, 81.6, 84.6, E.io))}% 0`;
}

/* ───────── fx layer: plinth, columns, sculpture, cards, patches, labels ───────── */
const COLS = []; for (const s of [-1, 1]) for (const z of [-3.3, 0.9, 4.9]) COLS.push([s * 4.8, z]);
const colPlanes = COLS.map(([cx, cz]) => {
  const el = h('div', { style: 'background:linear-gradient(90deg,#b9ad9b 0%,#e7dfd1 22%,#f1eadf 38%,#ddd4c5 62%,#b3a794 100%)' }, null);
  h('div', { style: 'position:absolute;inset:0;background:repeating-linear-gradient(90deg,rgba(90,76,58,.10) 0 2px,rgba(0,0,0,0) 2px 17px)' }, el);
  const pl = addPlane(el, [cx, 3.05, cz], [0, 0, 1], 0.48, 5.5, 96, 1100); pl.cx = cx; pl.cz = cz; return pl;
});
function faceColumns() {
  for (const pl of colPlanes) {
    const n = nrm([CAM.C[0] - pl.cx, 0, CAM.C[2] - pl.cz]), Ux = nrm(cross([0, 1, 0], n));
    pl.N = n; pl.Ux = Ux; pl.center = [pl.cx, 3.05, pl.cz]; pl.O = add(add(pl.center, mul(Ux, -pl.wu / 2)), [0, pl.hu / 2, 0]);
  }
}
function drawColumnEnds(x) { for (const [cx, cz] of COLS) { drawBoxLit(x, [cx, 0.15, cz], [0.34, 0.15, 0.34], P.stone, 1); drawBoxLit(x, [cx, 5.95, cz], [0.36, 0.15, 0.36], P.stone, 1.02); } }
function drawColumn(x, cx, cz) {
  const r = 0.24, y0 = 0.3, y1 = 5.8;
  const toC = nrm([CAM.C[0] - cx, 0, CAM.C[2] - cz]), side = [toC[2], 0, -toC[0]];
  drawBoxLit(x, [cx, 0.15, cz], [0.34, 0.15, 0.34], P.stone, 1);
  drawBoxLit(x, [cx, 5.95, cz], [0.36, 0.15, 0.36], P.stone, 1.02);
  const a = projPoly([add([cx, y0, cz], mul(side, -r)), add([cx, y1, cz], mul(side, -r)), add([cx, y1, cz], mul(side, r)), add([cx, y0, cz], mul(side, r))]);
  if (a.length < 4) return;
  const g = x.createLinearGradient(a[0][0], 0, a[3][0], 0);
  const sL = Math.max(0, dot(mul(side, -1), LIGHT)), sR = Math.max(0, dot(side, LIGHT));
  g.addColorStop(0, rgb(lit(P.stone, 0.7 + 0.25 * sL))); g.addColorStop(0.35, rgb(lit(P.stone, 1.0))); g.addColorStop(0.7, rgb(lit(P.stone, 0.88))); g.addColorStop(1, rgb(lit(P.stone, 0.66 + 0.25 * sR)));
  poly(x, a, g);
  for (let k = -3; k <= 3; k++) { const o = add([cx, 0, cz], mul(side, r * k / 3.6)); line3(x, [o[0], y0, o[2]], [o[0], y1, o[2]], rgb(lit([120, 104, 84], 1), .16), 1); }
}
function drawPlinth(x) {
  for (const f of boxFaces([0, 0.06, 0], [0.66, 0.06, 0.66])) poly(x, projPoly(f.p), rgb(faceShade(f.n, P.plinth, 0.95)), 'rgba(90,76,60,.25)', 1);
  for (const f of boxFaces([0, 0.55, 0], [0.5, 0.43, 0.5])) {
    const pp = projPoly(f.p); if (pp.length < 3) continue;
    const c = faceShade(f.n, P.plinth, 1), top = Math.min(...pp.map(p => p[1])), bot = Math.max(...pp.map(p => p[1]));
    const g = x.createLinearGradient(0, top, 0, bot); g.addColorStop(0, rgb(mul(c, 1.04))); g.addColorStop(1, rgb(mul(c, 0.9)));
    poly(x, pp, g, 'rgba(90,76,60,.25)', 1);
  }
  for (const f of boxFaces([0, 1.04, 0], [0.6, 0.06, 0.6])) poly(x, projPoly(f.p), rgb(faceShade(f.n, P.plinth, 1.02)), 'rgba(90,76,60,.25)', 1);
}
// the uncut block: solid shaded marble under the point grain, dissolving as the stone loosens
const VEINS = (() => { const r = rng(12), v = []; for (let k = 0; k < 7; k++) { const pts = []; let a = r() * 6.28, px = r() * 2 - 1, py = r() * 2 - 1; for (let s = 0; s < 14; s++) { pts.push([px, py]); a += (r() - 0.5) * 0.9; px += Math.cos(a) * 0.16; py += Math.sin(a) * 0.16; } v.push({ pts, w: 0.6 + r() * 1.4 }); } return v; })();
function drawBlock(x, t) {
  const a = 1 - seg(t, 6.6, 8.6, E.io); if (a <= 0) return;
  const { c, hs } = BLOCK;
  x.save(); x.globalAlpha = a;
  for (const f of boxFaces(c, hs)) {
    const pp = projPoly(f.p); if (pp.length < 3) continue;
    const base = faceShade(f.n, [236, 231, 222], 1.02), top = Math.min(...pp.map(p => p[1])), bot = Math.max(...pp.map(p => p[1]));
    const g = x.createLinearGradient(0, top, 0, bot); g.addColorStop(0, rgb(mul(base, 1.05))); g.addColorStop(1, rgb(mul(base, 0.9)));
    poly(x, pp, g, 'rgba(120,108,92,.35)', 1);
    // veins drawn in face coordinates
    const [o, e1, , e3] = f.p, U = sub(e1, o), V = sub(e3, o);
    x.save(); x.beginPath(); x.moveTo(pp[0][0], pp[0][1]); for (const q of pp) x.lineTo(q[0], q[1]); x.closePath(); x.clip();
    for (const vn of VEINS) {
      const sp = vn.pts.map(([u, v]) => proj(add(add(o, mul(U, (u + 1) / 2)), mul(V, (v + 1) / 2))));
      x.strokeStyle = 'rgba(128,116,100,.28)'; x.lineWidth = vn.w; x.beginPath(); sp.forEach((q, i) => i ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1])); x.stroke();
    }
    x.restore();
  }
  x.restore();
}
// affine blit of a small flat rectangle in 3D (plaque, cards)
function withRect(x, O, Ux, Vy, wu, hu, lw, lh, fn) {
  const a = proj(O), b = proj(add(O, mul(Ux, wu))), c = proj(add(O, mul(Vy, hu)));
  if (a[2] < NEAR || b[2] < NEAR || c[2] < NEAR) return;
  x.save(); x.setTransform((b[0] - a[0]) / lw, (b[1] - a[1]) / lw, (c[0] - a[0]) / lh, (c[1] - a[1]) / lh, a[0], a[1]); fn(x); x.restore();
}
const MAGIC = ['masterpiece, best quality, ultra-detailed, 8k,', 'award-winning, trending on artstation, intricate,', 'cinematic lighting, sharp focus, (perfect petals:1.4),', 'hyperrealistic, HDR, octane render, volumetric light'];
const MAGIC_CH = []; { const mx = cnv(10, 10).getContext('2d'); mx.font = 'italic 500 30px "Cormorant Garamond"'; MAGIC.forEach((ln, li) => { let xx = 310 - mx.measureText(ln).width / 2; for (const ch of ln) { MAGIC_CH.push({ ch, x: xx, y: 340 + li * 42, r: rng(MAGIC_CH.length + 5)() }); xx += mx.measureText(ch).width; } }); }
function plaqueText(t) {
  if (t < 12.8) return '';
  const full = t > 49.7 && t < 52.9 ? 'A lotus in bud.' : 'A lotus in full bloom.';
  return t < 16 ? full.slice(0, Math.floor(clamp((t - 13.2) / 1.3) * full.length)) : full;
}
function drawPlaque(x, t) {
  withRect(x, [-0.31, 0.78, 0.503], [1, 0, 0], [0, -1, 0], 0.62, 0.3, 620, 300, c => {
    const g = c.createLinearGradient(0, 0, 620, 300); g.addColorStop(0, '#d7b986'); g.addColorStop(.45, '#a8854c'); g.addColorStop(.7, '#c9a772'); g.addColorStop(1, '#8e6f3a');
    c.fillStyle = g; c.fillRect(0, 0, 620, 300); c.strokeStyle = 'rgba(60,44,20,.5)'; c.lineWidth = 3; c.strokeRect(12, 12, 596, 276);
    c.font = '600 22px "Instrument Sans"'; c.textAlign = 'center'; c.fillStyle = 'rgba(59,44,22,.8)'; c.letterSpacing = '5px'; c.fillText('THE SENTENCE', 310, 78); c.letterSpacing = '0px';
    const txt = plaqueText(t); c.font = 'italic 500 50px "Cormorant Garamond"';
    c.fillStyle = 'rgba(255,238,200,.45)'; c.fillText(txt, 311, 176); c.fillStyle = '#2e2210'; c.fillText(txt, 310, 174);
    if (t > 12.8 && t < 16.5 && Math.floor(t * 2.2) % 2 === 0) { const w = c.measureText(txt).width; c.fillRect(310 + w / 2 + 4, 136, 3, 46); }
    if (t > 75.2 && t < 81) {                                   // the magic words spill off the plaque, then crumble
      c.font = 'italic 500 30px "Cormorant Garamond"'; c.textAlign = 'left';
      const shown = Math.floor(clamp((t - 75.3) / 2.2) * MAGIC_CH.length);
      for (let k = 0; k < shown; k++) {
        const m = MAGIC_CH[k], fall = Math.max(0, t - (78.5 + m.r * 1.2)); if (fall > 1.6) continue;
        c.save(); c.globalAlpha = 1 - clamp(fall / 1.4); c.translate(m.x, m.y + 380 * fall * fall); c.rotate(fall * (m.r - 0.5) * 3);
        c.fillStyle = '#3b2c16'; c.fillText(m.ch, 0, 0); c.restore();
      }
    }
  });
}
function card3(x, center, wu, hu, ang, front, back, alpha) {
  const Ux = [Math.cos(ang), 0, -Math.sin(ang)], O = add(add(center, mul(Ux, -wu / 2)), [0, hu / 2, 0]), showBack = Math.cos(ang) < 0;
  withRect(x, O, Ux, [0, -1, 0], wu, hu, 460, 140, c => {
    c.globalAlpha = alpha; if (showBack) { c.translate(460, 0); c.scale(-1, 1); }
    c.shadowColor = 'rgba(40,28,18,.25)'; c.shadowBlur = 16; c.shadowOffsetY = 8;
    c.fillStyle = 'rgba(247,243,236,.97)'; c.fillRect(0, 0, 460, 140); c.shadowColor = 'transparent';
    c.strokeStyle = '#b08d57'; c.lineWidth = 3; c.strokeRect(8, 8, 444, 124);
    c.fillStyle = '#1e1c19'; c.font = 'italic 500 64px "Cormorant Garamond"'; c.textAlign = 'center'; c.fillText(showBack ? back : front, 230, 92);
  });
}
function curve(x, a, b, bend, style, lw, p = 1) {
  if (a[2] < NEAR || b[2] < NEAR || p <= 0) return;
  const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 - bend, N = 24, n = Math.max(1, Math.round(N * p));
  x.strokeStyle = style; x.lineWidth = lw; x.beginPath(); x.moveTo(a[0], a[1]);
  for (let k = 1; k <= n; k++) { const u = k / N, q = 1 - u; x.lineTo(q * q * a[0] + 2 * q * u * mx + u * u * b[0], q * q * a[1] + 2 * q * u * my + u * u * b[1]); }
  x.stroke();
}
function label(x, anchor, dx, dy, text, a) {
  if (a <= 0.01) return; const p = proj(anchor); if (p[2] < NEAR) return;
  x.save(); x.globalAlpha = a;
  x.fillStyle = '#c4633f'; x.beginPath(); x.arc(p[0], p[1], 4, 0, 7); x.fill();
  const e = seg(a, 0, 1);
  x.strokeStyle = 'rgba(30,28,25,.55)'; x.lineWidth = 1.2; x.beginPath(); x.moveTo(p[0], p[1]); x.lineTo(p[0] + dx * e, p[1] + dy * e); x.lineTo(p[0] + dx * e + (dx < 0 ? -26 : 26), p[1] + dy * e); x.stroke();
  x.font = '600 15px "Instrument Sans"'; x.fillStyle = '#1e1c19'; x.textAlign = dx < 0 ? 'right' : 'left'; x.letterSpacing = '2.6px';
  x.fillText(text, p[0] + dx + (dx < 0 ? -34 : 34), p[1] + dy + 5); x.restore();
}
// latent sketch: coarse clay voxels on a side stand
const VOX = []; {
  const g = 0.032, seen = new Set(), r = rng(3);
  for (let i = 0; i < NPT; i += 3) {
    const p = [Lp[3 * i] * 0.3, (Lp[3 * i + 1] - 1.1) * 0.3, Lp[3 * i + 2] * 0.3], k = [Math.round(p[0] / g), Math.round(p[1] / g), Math.round(p[2] / g)], key = k.join(',');
    if (seen.has(key)) continue; seen.add(key); VOX.push({ c: mul(k, g), r: r(), y: p[1], id: VOX.length });
  }
}
function drawStand(x, t) {
  const [sx, , sz] = STAND;
  drawBoxLit(x, [sx, 0.05, sz], [0.2, 0.05, 0.2], P.stone, 0.98);
  drawBoxLit(x, [sx, 0.5, sz], [0.12, 0.4, 0.12], P.stone, 1.0);
  drawBoxLit(x, [sx, 0.93, sz], [0.22, 0.03, 0.22], P.stone, 1.02);
  if (t < 54.8) return;
  const base = [sx, 0.97, sz], g = 0.032, rot = rotAt(t);
  const list = [];
  for (const v of VOX) {
    const pa = seg(t, 54.9 + v.r * 0.8 + v.y * 6, 55.8 + v.r * 0.8 + v.y * 6, E.emph); if (pa <= 0) continue;
    const c = add(base, add(rotY(v.c, rot), [0, 0.012, 0])), off = mul([hash(v.id, 1) - .5, hash(v.id, 2) * .8, hash(v.id, 3) - .5], (1 - pa) * 0.5);
    list.push({ c: add(c, off), d: toCam(c)[2] });
  }
  list.sort((a, b) => b.d - a.d).forEach(v => drawBoxLit(x, v.c, [g / 2, g / 2, g / 2], P.terracotta, 1.0));
}
// patches for chapter 06: snapshot of the sculpture from the fixed front camera
const TILE_NX = 6, TILE_NY = 3, TILE_W = 0.22, TILE_H = 0.17, TILE_O = [-0.66, 1.62, 0], NT = TILE_NX * TILE_NY;
let tileSnap = null;
function makeTileSnap() {
  setCam([0, 2.0, 3.7], [0, 1.36, 0], 1750); EXPO = 1; dirty = [0, 0, W, H]; renderSculpture(64.0);
  const c = cnv(W, H), x = c.getContext('2d'); x.fillStyle = '#e9e2d6'; x.fillRect(0, 0, W, H);
  drawLotusMesh(x, 64.0, 1); x.globalAlpha = pointAlphaAt(64.0); x.drawImage(spC, 0, 0);
  tileSnap = { c, a: proj(TILE_O), b: proj(add(TILE_O, [TILE_W * TILE_NX, -TILE_H * TILE_NY, 0])) }; dirty = [0, 0, W, H];
}
function tileState(t, i) {
  const gx = i % TILE_NX, gy = (i / TILE_NX) | 0, home = add(TILE_O, [TILE_W * (gx + 0.5), -TILE_H * (gy + 0.5), 0.02]);
  const ang = i / NT * Math.PI * 2 + (t - 64) * 0.22, ring = [Math.sin(ang) * 1.35, 1.5 + 0.24 * Math.sin(ang * 2 + 1), Math.cos(ang) * 1.35];
  const p = seg(t, 64.5 + i * 0.045, 65.8 + i * 0.045, E.io) * (1 - seg(t, 70.5 + (NT - 1 - i) * 0.04, 71.6 + (NT - 1 - i) * 0.04, E.io));
  return { pos: add(lerp3(home, ring, p), [0, Math.sin(Math.PI * p) * 0.12, 0]), p, gx, gy };
}
function drawTiles(x, t) {
  if (t < 63.4 || t > 72.2) return;
  const grid = win(t, 63.4, 64.1, 71.6, 72.2);
  if (grid > 0 && t < 64.8) {
    x.save(); x.globalAlpha = grid;
    for (let k = 0; k <= TILE_NX; k++) line3(x, add(TILE_O, [k * TILE_W, 0, 0.02]), add(TILE_O, [k * TILE_W, -TILE_H * TILE_NY, 0.02]), 'rgba(176,141,87,.9)', 1.2);
    for (let k = 0; k <= TILE_NY; k++) line3(x, add(TILE_O, [0, -k * TILE_H, 0.02]), add(TILE_O, [TILE_W * TILE_NX, -k * TILE_H, 0.02]), 'rgba(176,141,87,.9)', 1.2);
    x.restore();
  }
  if (t < 64.45 || t > 71.9) return;
  const all = Array.from({ length: NT }, (_, i) => { const s = tileState(t, i); return { i, ...s, pr: proj(s.pos) }; });
  const thr = seg(t, 66.0, 67.6, E.io) * (1 - seg(t, 70.3, 70.9));
  if (thr > 0) {                                         // attention: every patch linked to every other
    for (let i = 0; i < NT; i++) for (let j = i + 1; j < NT; j++) {
      const w = hash(i * 16 + j, 5), pp = clamp((thr - hash(i, j) * 0.5) * 2); if (pp <= 0) continue;
      const a = all[i].pr, b = all[j].pr; x.strokeStyle = `rgba(176,141,87,${(0.12 + 0.4 * w * w) * pp})`; x.lineWidth = 1 + w;
      x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(lerp(a[0], b[0], pp), lerp(a[1], b[1], pp)); x.stroke();
    }
    if (t > 66.8) for (let m = 0; m < 10; m++) {
      const i = Math.floor(hash(m, 1) * NT), j = (i + 1 + Math.floor(hash(m, 2) * (NT - 1))) % NT, ph = ((t - 66.5) * 0.6 + hash(m, 3)) % 1, a = all[i].pr, b = all[j].pr;
      x.fillStyle = `rgba(196,99,63,${0.9 * thr})`; x.beginPath(); x.arc(lerp(a[0], b[0], ph), lerp(a[1], b[1], ph), 3.2, 0, 7); x.fill();
    }
  }
  const { a: A0, b: B0 } = tileSnap, sw = (B0[0] - A0[0]) / TILE_NX, shh = (B0[1] - A0[1]) / TILE_NY;
  all.sort((a, b) => b.pr[2] - a.pr[2]).forEach(s => {
    const k = CAM.f / s.pr[2] * lerp(1, 0.9, s.p), wz = TILE_W * k * 0.98, hz = TILE_H * k * 0.98;
    x.save(); x.translate(s.pr[0], s.pr[1]);
    if (s.p > 0.02) { x.shadowColor = 'rgba(40,28,18,.25)'; x.shadowBlur = 14; x.shadowOffsetY = 6; }
    x.fillStyle = '#efe9df'; x.fillRect(-wz / 2, -hz / 2, wz, hz); x.shadowColor = 'transparent';
    x.drawImage(tileSnap.c, A0[0] + s.gx * sw, A0[1] + s.gy * shh, sw, shh, -wz / 2, -hz / 2, wz, hz);
    x.strokeStyle = 'rgba(176,141,87,.9)'; x.lineWidth = 1.2; x.strokeRect(-wz / 2, -hz / 2, wz, hz);
    x.restore();
  });
}
// light shaft and dust
const DUST = Array.from({ length: 220 }, (_, i) => { const r = rng(1000 + i); return { a: r() * 6.28, rr: Math.sqrt(r()) * 0.95, y: r() * 5.6 + 0.8, s: 0.2 + r() * 0.6, ph: r() * 6 }; });
function drawBeam(x) {
  const top = [0, 7.2, 0.15], toC = nrm([CAM.C[0], 0, CAM.C[2]]), side = [toC[2], 0, -toC[0]];
  const pts = projPoly([add(top, mul(side, -0.12)), add(top, mul(side, 0.12)), add([0, 0.98, 0], mul(side, 0.98)), add([0, 0.98, 0], mul(side, -0.98))]);
  if (pts.length < 3) return;
  const ys = pts.map(p => p[1]), g = x.createLinearGradient(0, Math.min(...ys), 0, Math.max(...ys));
  g.addColorStop(0, `rgba(255,238,210,${0.02 * BEAM})`); g.addColorStop(0.55, `rgba(255,238,210,${0.1 * BEAM})`); g.addColorStop(1, `rgba(255,238,210,${0.16 * BEAM})`);
  x.save(); x.globalCompositeOperation = 'lighter'; poly(x, pts, g); x.restore();
}
function drawDust(x, t) {
  x.save(); x.globalCompositeOperation = 'lighter';
  for (const d of DUST) {
    const y = 0.8 + ((d.y + t * 0.05 * d.s) % 5.6), a = d.a + t * 0.03 * d.s, p = proj([Math.cos(a) * d.rr + 0.05 * Math.sin(t * .4 + d.ph), y, Math.sin(a) * d.rr]);
    if (p[2] < NEAR) continue;
    const s = clamp(CAM.f * 0.006 / p[2], 0.6, 3), al = (0.25 + 0.5 * BEAM) * (0.4 + 0.6 * Math.sin(t * 0.8 + d.ph) ** 2);
    x.fillStyle = `rgba(255,236,205,${al * 0.6})`; x.fillRect(p[0], p[1], s, s);
  }
  x.restore();
}
function drawFX(t) {
  const x = FX; x.clearRect(0, 0, W, H);
  drawBeam(x);
  const objs = [];
  objs.push({ d: toCam([0, 1, 0])[2], fn: () => {
    drawPlinth(x); drawPlaque(x, t); drawBlock(x, t);
    const dim = 1 - 0.72 * dimAt(t);
    drawLotusMesh(x, t, meshAlphaAt(t) * dim);
    x.save(); x.globalAlpha = pointAlphaAt(t) * dim; x.drawImage(spC, 0, 0); x.restore();
  } });
  objs.push({ d: toCam([STAND[0], 0.8, STAND[2]])[2], fn: () => drawStand(x, t) });
  objs.filter(o => o.d > NEAR).sort((a, b) => b.d - a.d).forEach(o => o.fn());
  drawDust(x, t);
  // 04 · word cards lift from the plaque and steer the form
  const ca = win(t, 45.6, 46.6, 53.8, 54.5), rot = rotAt(t);
  if (ca > 0) {
    const lift = seg(t, 45.6, 46.8, E.emph);
    const cL = lerp3([-0.1, 0.62, 0.52], [-0.92, 2.05, 0.45], lift), cR = lerp3([0.14, 0.62, 0.52], [0.95, 1.98, 0.42], lift);
    const flip = seg(t, 49.4, 50.0, E.io) * (1 - seg(t, 52.4, 53.0, E.io)), thread = seg(t, 46.6, 47.8, E.io);
    curve(x, proj(add(cL, [0.23, 0, 0])), proj([0, FLOWER_Y + 0.16, 0]), 40, `rgba(176,141,87,${0.9 * ca})`, 1.6, thread);
    const open = openAt(t), pb = proj(add(cR, [-0.23, 0, 0]));
    for (const k of [0, 2, 4, 6, 8]) curve(x, pb, proj(petalTip(k, open, rot)), 30 + k * 4, `rgba(176,141,87,${0.75 * ca})`, 1.3, thread);
    card3(x, cL, 0.46, 0.14, 0.25, 'lotus', 'lotus', ca);
    card3(x, cR, 0.46, 0.14, -0.25 + flip * Math.PI, 'full bloom', 'bud', ca);
  }
  drawTiles(x, t);
  const dec = win(t, 58.6, 59.2, 61.2, 62.0);                 // 05 · decoder from sketch to sculpture
  if (dec > 0) {
    const a = proj([STAND[0], 1.12, STAND[2]]), b = proj([0, 1.45, 0]);
    for (let k = 0; k < 7; k++) { const o = (k - 3) * 10; curve(x, a, [b[0] + o * 2, b[1] + o, b[2]], 60 + k * 4, `rgba(176,141,87,${0.55 * dec})`, 1.2, seg(t, 58.6 + k * 0.05, 59.6 + k * 0.05, E.io)); }
    const ph = ((t - 58.6) * 0.9) % 1;
    x.fillStyle = `rgba(196,99,63,${dec})`; x.beginPath(); x.arc(lerp(a[0], b[0], ph), lerp(a[1], b[1], ph) - Math.sin(Math.PI * ph) * 60, 4, 0, 7); x.fill();
  }
  label(x, [0.4, 2.05, 0.3], 150, -90, 'NOISE', win(t, 14.2, 15.0, 20.2, 20.8));
  label(x, [0.25, 0.62, 0.51], 190, 40, 'SENTENCE', win(t, 16.8, 17.6, 20.2, 20.8));
  label(x, add(EASEL.c, [0.25, 0.34, 0.05]), 130, -70, 'TRAINING', win(t, 22.0, 22.8, 31.6, 32.2));
  label(x, [0.45, 2.1, 0.2], 170, -60, `STEP ${String(stepAt(t)).padStart(2, '0')} / ${STEPS}`, win(t, 33.8, 34.4, 44.6, 45.2));
  label(x, [STAND[0], 1.14, STAND[2]], -160, -80, 'LATENT SKETCH · 1/8 SCALE', win(t, 55.4, 56.2, 61.8, 62.4));
  label(x, [0.9, 1.75, 0.4], 140, -60, 'DECODER', win(t, 59.0, 59.6, 61.8, 62.4));
  label(x, [1.55, 1.7, 0.3], 120, -80, 'PATCH → TOKEN', win(t, 65.6, 66.2, 70.2, 70.8));
  label(x, [-1.2, 1.9, 0.9], -120, -60, 'ATTENTION', win(t, 67.0, 67.6, 70.2, 70.8));
}

/* ───────── grain ───────── */
{ const c = cnv(256, 256), x = c.getContext('2d'), d = x.createImageData(256, 256), r = rng(7);
  for (let i = 0; i < 256 * 256; i++) { const v = clamp(128 + gauss(r) * 24, 0, 255); d.data[4 * i] = d.data[4 * i + 1] = d.data[4 * i + 2] = v; d.data[4 * i + 3] = 255; }
  x.putImageData(d, 0, 0); document.getElementById('grain').style.backgroundImage = `url(${c.toDataURL()})`; }

/* ───────── frame ───────── */
makeTileSnap();
function render(t) {
  t = clamp(t, 0, DUR);
  const [C, T, f] = camAt(t); setCam(C, T, f);
  EXPO = exposureAt(t); BEAM = beamAt(t);
  drawRoom(t);
  updStudy(t); updFrames(t); faceColumns(); updPlanes();
  renderSculpture(t); drawFX(t);
  updSups(t);
  const ef = seg(t, 116.6, 117.8, E.emph);
  vis(endShade, seg(t, 115.6, 117.4)); vis(endL, ef); vis(endR, ef);
  endL.style.transform = `translateY(${((1 - ef) * -10).toFixed(1)}px)`;
}
window.__render = render;
const CHAPTERS = [[0, 'Prologue'], [12, 'How it works'], [72, 'The catch'], [81, 'Lotus V7'], [87.5, 'Realistic V7'], [99, 'Anime Diffusion V7'], [111, 'Coming soon']];
window.__meta = { DUR, CHAPTERS };
document.getElementById('loading').remove();

/* ───────── player ───────── */
const stage = document.getElementById('stage');
if (!RENDER) {
  const fit = () => { const s = Math.min(innerWidth / W, innerHeight / H); stage.style.transform = `translate(${(innerWidth - W * s) / 2}px,${(innerHeight - H * s) / 2}px) scale(${s})`; };
  addEventListener('resize', fit); fit();
  const audio = new Audio('assets/music.m4a'); audio.preload = 'auto';
  const pl = h('div', { id: 'player' }, document.body), bar = h('div', { class: 'bar' }, pl), fill = h('b', null, bar);
  CHAPTERS.forEach(([s]) => h('s', { style: `left:${s / DUR * 100}%` }, bar));
  const ctl = h('div', { class: 'ctl' }, pl), play = h('button', null, ctl, '▶ Play'), time = h('span', { class: 'time' }, ctl, '0:00 / 2:00');
  const chB = CHAPTERS.map(([s, n]) => { const b = h('button', null, ctl, n); b.onclick = () => seek(s); return b; });
  let playing = false, t0 = 0, c0 = 0, cur = Q.has('t') ? +Q.get('t') : 0;
  const now = () => performance.now() / 1000, fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  function seek(s) { cur = clamp(s, 0, DUR); t0 = cur; c0 = now(); try { audio.currentTime = cur; } catch (e) {} if (!playing) render(cur); }
  function toggle() { playing = !playing; play.textContent = playing ? '❚❚ Pause' : '▶ Play'; if (playing) { if (cur >= DUR) cur = 0; t0 = cur; c0 = now(); audio.currentTime = cur; audio.play().catch(() => {}); } else audio.pause(); }
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
    if (playing) { cur = !audio.paused && audio.readyState > 2 ? audio.currentTime : t0 + (now() - c0); if (cur >= DUR) { cur = DUR; playing = false; play.textContent = '▶ Play'; audio.pause(); } render(cur); }
    fill.style.width = (cur / DUR * 100) + '%'; time.textContent = `${fmt(cur)} / ${fmt(DUR)}`;
    chB.forEach((b, k) => b.classList.toggle('on', cur >= CHAPTERS[k][0] && (k === CHAPTERS.length - 1 || cur < CHAPTERS[k + 1][0])));
    requestAnimationFrame(loop);
  })();
  render(cur);
} else render(+(Q.get('t') || 0));
return true;
})();
