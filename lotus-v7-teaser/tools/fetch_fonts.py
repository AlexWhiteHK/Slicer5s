"""Download Google Fonts subsets containing exactly the glyphs the teaser uses.

Collects every character from teaser.js and index.html, asks the Google Fonts
css2 API for a `text=` subset of each family, and writes assets/fonts/*.woff2
plus assets/fonts/fonts.css. Re-run after changing any on-screen copy.
"""
import pathlib, re, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'fonts'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'

src = (ROOT / 'teaser.js').read_text('utf-8') + (ROOT / 'index.html').read_text('utf-8')
chars = set(src) | set(chr(c) for c in range(0x20, 0x7F)) | set('·—–’‘“”…×→←↑·')
chars.discard('\n'); chars.discard('\r'); chars.discard('\t')
latin = {c for c in chars if ord(c) < 0x2E80}

FAMILIES = [
    ('Cormorant Garamond', 'Cormorant+Garamond:ital,wght@0,500;0,600;1,500', ''.join(sorted(latin))),
    ('Cinzel', 'Cinzel:wght@500;600', ''.join(sorted(latin))),
    ('Instrument Sans', 'Instrument+Sans:wght@400;500;600', ''.join(sorted(latin))),
    ('IBM Plex Mono', 'IBM+Plex+Mono:wght@400', ''.join(sorted(latin))),
]

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

OUT.mkdir(parents=True, exist_ok=True)
css_out = []
for name, spec, text in FAMILIES:
    url = f'https://fonts.googleapis.com/css2?family={spec}&text={urllib.parse.quote(text)}&display=block'
    css = get(url).decode()
    for i, block in enumerate(re.findall(r'@font-face\s*{[^}]+}', css)):
        furl = re.search(r'url\((https://[^)]+)\)', block).group(1)
        style = re.search(r'font-style:\s*(\w+)', block).group(1)
        weight = re.search(r'font-weight:\s*([\d ]+);', block).group(1).strip()
        fname = f"{name.lower().replace(' ', '-')}-{style}-{weight.replace(' ', '-')}.woff2"
        (OUT / fname).write_bytes(get(furl))
        css_out.append(f"@font-face{{font-family:'{name}';font-style:{style};font-weight:{weight};font-display:block;src:url({fname}) format('woff2')}}")
        print(name, style, weight, fname, (OUT / fname).stat().st_size)
(OUT / 'fonts.css').write_text('\n'.join(css_out) + '\n', 'utf-8')
print(len(latin), 'glyphs')
