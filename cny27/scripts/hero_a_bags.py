#!/usr/bin/env python3
"""Bags-only input for hero A (cans are added after restaging). usage: hero_a_bags.py clean_dir out.jpg"""
import sys, json
from PIL import Image
d = sys.argv[1]; W, H, BH, gap, base = 1536, 1024, 520, 34, 700
names = ('bag_bamboo_02222', 'bag_red_02223', 'bag_pink_02220'); bags = []
for n in names:
    im = Image.open(f'{d}/{n}.png').convert('RGBA'); im = im.crop(im.getchannel('A').getbbox())
    bags.append(im.resize((round(im.width * BH / im.height), BH), Image.LANCZOS))
x = (W - (sum(b.width for b in bags) + 2 * gap)) // 2; c = Image.new('RGB', (W, H), 'white'); L = []
for n, b in zip(names, bags): c.paste(b, (x, base - b.height), b); L.append(dict(png=f'{d}/{n}.png', x=x, y=base - b.height, w=b.width, h=b.height, smin=.85, smax=1.25)); x += b.width + gap
c.save(sys.argv[2], quality=95); json.dump(L, open(sys.argv[2].rsplit('.', 1)[0] + '_layout.json', 'w'))
