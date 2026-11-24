#!/usr/bin/env python3
"""Photoroom remove-background PNG -> cleaned cut-out -> 1536x1024 white input + layout.json for restore.
usage (from cny27/work): single_prep.py name cut.png [x0 x1]   -> gen/<name>_in.jpg, gen/<name>_layout.json, clean/<name>.png"""
import sys, json, subprocess, os
name, cut = sys.argv[1], sys.argv[2]; xr = sys.argv[3:5]
os.makedirs('clean', exist_ok=True); os.makedirs('gen', exist_ok=True)
subprocess.run(['python3', '../scripts/cutclean.py', cut, f'clean/{name}.png', *xr], check=True)
subprocess.run(['python3', '../scripts/pad32.py', f'clean/{name}.png', f'gen/{name}_in.jpg'], check=True)
from PIL import Image
im = Image.open(f'clean/{name}.png').convert('RGBA'); im = im.crop(im.getchannel('A').getbbox())
W, H, hf, wf, base = 1536, 1024, 0.60, 0.62, 0.80
s = min(hf * H / im.height, wf * W / im.width); w, h = round(im.width * s), round(im.height * s)
json.dump([dict(png=f'clean/{name}.png', x=(W - w) // 2, y=round(base * H) - h, w=w, h=h, smin=0.8, smax=1.3)], open(f'gen/{name}_layout.json', 'w'))
print(f'{name}: product {w}x{h} (bbox of cut-out {im.width}x{im.height})')
