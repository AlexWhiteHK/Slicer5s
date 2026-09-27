"""Join rendered segments, add the score and chapter markers.

    python3 tools/mux.py [ffmpeg] [crf]  -> dist/lotus-v7-teaser.mp4
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FF = sys.argv[1] if len(sys.argv) > 1 else 'ffmpeg'
RATE = sys.argv[2] if len(sys.argv) > 2 else '5600k'   # segments are a CRF 16 intermediate; this is the delivery encode
# a value ending in k is a two-pass target bitrate (keeps the file under GitHub's 100 MB limit); a bare number is a CRF
DIST = ROOT / 'dist'
CHAPTERS = [(0, 'Prologue'), (12, 'How it works'), (72, 'The catch'), (81, 'Lotus V7'), (87.5, 'Realistic V7'),
            (99, 'Anime Diffusion V7'), (111, 'Coming soon')]
meta = [';FFMETADATA1', 'title=Lotus V7 · Coming soon', 'artist=Lotus AI Lab · Higan Holdings', 'comment=Realistic V7 · Anime Diffusion V7']
for i, (s, name) in enumerate(CHAPTERS):
    e = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 120
    meta += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={int(s * 1000)}', f'END={int(e * 1000)}', f'title={name}']
(DIST / 'chapters.txt').write_text('\n'.join(meta) + '\n', 'utf-8')
out = DIST / 'lotus-v7-teaser.mp4'
inp = ['-f', 'concat', '-safe', '0', '-i', str(DIST / 'seg' / 'list.txt'), '-i', str(DIST / 'music.wav'), '-i', str(DIST / 'chapters.txt')]
venc = ['-c:v', 'libx264', '-preset', 'slow', '-tune', 'film', '-g', '120', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709']
tail = ['-map', '0:v', '-map', '1:a', '-map_metadata', '2', '-map_chapters', '2', '-c:a', 'aac', '-b:a', '224k', '-t', '120', '-movflags', '+faststart', str(out)]
if RATE.endswith('k'):
    log = str(DIST / 'x264pass')
    subprocess.run([FF, '-y', '-loglevel', 'error', *inp, '-map', '0:v', *venc, '-b:v', RATE, '-pass', '1', '-passlogfile', log, '-an', '-f', 'mp4', '/dev/null'], check=True)
    subprocess.run([FF, '-y', '-loglevel', 'error', *inp, *venc, '-b:v', RATE, '-maxrate', '14M', '-bufsize', '20M', '-pass', '2', '-passlogfile', log, *tail], check=True)
else:
    subprocess.run([FF, '-y', '-loglevel', 'error', *inp, *venc, '-crf', RATE, *tail], check=True)
print('wrote', out, round(out.stat().st_size / 1e6, 1), 'MB')
