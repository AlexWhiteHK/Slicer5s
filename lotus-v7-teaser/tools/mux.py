"""Join rendered segments, add the score and chapter markers.

    python3 tools/mux.py [ffmpeg] [crf]  -> dist/lotus-v7-teaser.mp4
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FF = sys.argv[1] if len(sys.argv) > 1 else 'ffmpeg'
CRF = sys.argv[2] if len(sys.argv) > 2 else '22'   # segments are a CRF 16 intermediate; this is the delivery encode
DIST = ROOT / 'dist'
CHAPTERS = [(0, '序章 · Prologue'), (12, '十二年 · Twelve years'), (66, '转折 · The turn'),
            (78, 'Lotus Realistic V7'), (96, 'Lotus Anime Diffusion V7'), (111, '即将推出 · Coming soon')]
meta = [';FFMETADATA1', 'title=Lotus V7 · Coming soon', 'artist=Lotus AI Lab · Higan Holdings', 'comment=Realistic V7 · Anime Diffusion V7']
for i, (s, name) in enumerate(CHAPTERS):
    e = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 120
    meta += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={s * 1000}', f'END={e * 1000}', f'title={name}']
(DIST / 'chapters.txt').write_text('\n'.join(meta) + '\n', 'utf-8')
out = DIST / 'lotus-v7-teaser.mp4'
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(DIST / 'seg' / 'list.txt'),
                '-i', str(DIST / 'music.wav'), '-i', str(DIST / 'chapters.txt'), '-map', '0:v', '-map', '1:a', '-map_metadata', '2', '-map_chapters', '2',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', CRF, '-tune', 'film', '-g', '120', '-pix_fmt', 'yuv420p',
                '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', '256k', '-t', '120', '-movflags', '+faststart', str(out)], check=True)
print('wrote', out, round(out.stat().st_size / 1e6, 1), 'MB')
