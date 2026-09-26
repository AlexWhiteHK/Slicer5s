"""Contact sheet of dist/stills/*.png (3 columns, half size) for quick review."""
import glob, sys
from PIL import Image, ImageDraw
files = sorted(glob.glob('dist/stills/t_*.png'))
W, H, C = 960, 540, 3
rows = (len(files) + C - 1) // C
sheet = Image.new('RGB', (W * C, H * rows), 'white')
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
    ImageDraw.Draw(im).text((10, 10), f.split('t_')[1][:-4], fill=(255, 0, 0))
    sheet.paste(im, ((i % C) * W, (i // C) * H))
sheet.save(sys.argv[1], quality=88)
