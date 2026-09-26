/* Frame renderer: drives index.html?render=1 in headless Chromium and encodes with ffmpeg.
   node tools/render.cjs stills 3.2,12.5,...  -> dist/stills/t_XXX.png
   node tools/render.cjs video [--fps 60] [--workers 4] [--from 0 --to 120]
   Needs a static server on :8123 serving this folder (python3 -m http.server 8123). */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

const ROOT = path.resolve(__dirname, '..');
const URL = process.env.TEASER_URL || 'http://127.0.0.1:8123/index.html?render=1';
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('pageerror', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console', m.text()); });
  await page.goto(URL, { waitUntil: 'load' });
  await page.evaluate(() => window.__ready);
  const cdp = await page.context().newCDPSession(page);
  return { page, cdp };
}
async function frame({ page, cdp }, t, format = 'png') {
  await page.evaluate(t => window.__render(t), t);
  const r = await cdp.send('Page.captureScreenshot', format === 'png' ? { format: 'png' } : { format: 'jpeg', quality: 94, optimizeForSpeed: true });
  return Buffer.from(r.data, 'base64');
}
const launch = () => chromium.launch({ args: ['--font-render-hinting=none', '--disable-lcd-text', '--force-color-profile=srgb', '--hide-scrollbars'] });

(async () => {
  const mode = args[0];
  if (mode === 'stills') {
    const ts = args[1].split(',').map(Number);
    const out = path.join(ROOT, 'dist', 'stills'); fs.mkdirSync(out, { recursive: true });
    const browser = await launch(); const p = await openPage(browser);
    for (const t of ts) {
      const t0 = Date.now(); const buf = await frame(p, t);
      const f = path.join(out, `t_${t.toFixed(2).padStart(6, '0')}.png`); fs.writeFileSync(f, buf);
      console.log(f, Date.now() - t0, 'ms');
    }
    await browser.close(); return;
  }
  if (mode === 'video') {
    const fps = +opt('fps', 60), workers = +opt('workers', 4), from = +opt('from', 0), to = +opt('to', 120);
    const N0 = Math.round(from * fps), N1 = Math.round(to * fps), per = Math.ceil((N1 - N0) / workers);
    const segDir = path.join(ROOT, 'dist', 'seg'); fs.mkdirSync(segDir, { recursive: true });
    const started = Date.now(); let done = 0;
    const jobs = Array.from({ length: workers }, async (_, w) => {
      const a = N0 + w * per, b = Math.min(N1, a + per); if (a >= b) return null;
      const file = path.join(segDir, `seg_${String(w).padStart(2, '0')}.mp4`);
      const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-r', String(fps), file],
        { stdio: ['pipe', 'inherit', 'inherit'] });
      const closed = new Promise(res => ff.on('close', res));
      const browser = await launch(); const p = await openPage(browser);
      for (let n = a; n < b; n++) {
        const buf = await frame(p, n / fps, 'jpeg');
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        done++;
        if (w === 0 && done % 120 === 0) { const el = (Date.now() - started) / 1000; console.log(`${done}/${N1 - N0} frames, ${el.toFixed(0)} s, eta ${((N1 - N0 - done) * el / done).toFixed(0)} s`); }
      }
      ff.stdin.end(); await closed; await browser.close(); return file;
    });
    const files = (await Promise.all(jobs)).filter(Boolean);
    fs.writeFileSync(path.join(segDir, 'list.txt'), files.map(f => `file '${f}'`).join('\n') + '\n');
    console.log('segments', files.length, 'in', ((Date.now() - started) / 1000).toFixed(0), 's');
  }
})();
