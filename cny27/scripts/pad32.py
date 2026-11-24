#!/usr/bin/env python3
"""Cut-out (RGBA PNG) -> 1536x1024 white canvas, product centred. Feed result to Photoroom subject-edits.
usage: pad32.py in.png out.jpg [--h 0.60] [--w 0.62] [--base 0.80]"""
import sys, argparse
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--h', type=float, default=0.60); ap.add_argument('--w', type=float, default=0.62)
ap.add_argument('--base', type=float, default=0.80, help='y of product bottom, fraction of canvas height')
a = ap.parse_args()
W, H = 1536, 1024
im = Image.open(a.src).convert('RGBA'); im = im.crop(im.getchannel('A').getbbox())
s = min(a.h * H / im.height, a.w * W / im.width); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
c = Image.new('RGB', (W, H), 'white'); c.paste(im, ((W - im.width) // 2, round(a.base * H) - im.height), im)
c.save(a.dst, quality=95)
