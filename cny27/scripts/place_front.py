#!/usr/bin/env python3
"""Paste original cut-outs (RGBA) in a centred row in front, with contact shadow + glossy-table reflection.
usage: place_front.py base.jpg out.jpg base_y cut_h gap png1 png2 ..."""
import sys
from PIL import Image, ImageFilter, ImageDraw
base = Image.open(sys.argv[1]).convert('RGB'); by, ch, gap = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
items = []
for p in sys.argv[6:]:
    im = Image.open(p).convert('RGBA'); im = im.crop(im.getchannel('A').getbbox()); items.append(im.resize((round(im.width * ch / im.height), ch), Image.LANCZOS))
x = (base.width - (sum(i.width for i in items) + gap * (len(items) - 1))) // 2
sh = Image.new('L', base.size, 0); d = ImageDraw.Draw(sh); refl = Image.new('RGBA', base.size, (0, 0, 0, 0)); pos = []
for i in items:
    d.ellipse((x - 6, by - 14, x + i.width + 6, by + 16), fill=150)
    f = i.transpose(Image.FLIP_TOP_BOTTOM); a = f.getchannel('A'); g = Image.linear_gradient('L').resize((1, f.height)).transpose(Image.FLIP_TOP_BOTTOM).resize(f.size)
    fade = g.point(lambda v: int(v * 0.42)); a = Image.composite(Image.new('L', f.size, 0), a, Image.new('L', f.size, 0)) if False else Image.eval(a, lambda v: v)
    from PIL import ImageChops
    f.putalpha(ImageChops.multiply(a, fade)); refl.alpha_composite(f.filter(ImageFilter.GaussianBlur(1.2)), (x, by - 2)); pos.append(x); x += i.width + gap
sh = sh.filter(ImageFilter.GaussianBlur(9)); dark = Image.new('RGB', base.size, (20, 0, 0))
base = Image.composite(dark, base, sh.point(lambda v: int(v * 0.6))); base.paste(refl, (0, 0), refl)
for i, px in zip(items, pos): base.paste(i, (px, by - i.height), i)
base.save(sys.argv[2], quality=93)
