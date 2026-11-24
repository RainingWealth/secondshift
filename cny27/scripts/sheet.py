#!/usr/bin/env python3
"""Contact sheet, <=12 thumbs, 1600px wide. usage: sheet.py out.jpg img1 img2 ..."""
import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:14]
cols = 3; tw = 1600 // cols; th = round(tw * 2 / 3); rows = -(-len(files) // cols)
S = Image.new('RGB', (1600, rows * (th + 16)), 'white'); d = ImageDraw.Draw(S)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB'); im.thumbnail((tw - 4, th)); x, y = (i % cols) * tw, (i // cols) * (th + 16)
    S.paste(im, (x + 2, y)); d.text((x + 4, y + th + 2), f.split('/')[-1][:40], fill='black')
S.save(out, quality=82)
