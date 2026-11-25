#!/usr/bin/env python3
"""Composite 喜气羊羊 hero: 3 bags in a row + 4 cans in front, on white 1536x1024. usage: hero_a.py cut_dir out.jpg"""
import sys, json, os
from PIL import Image
d = sys.argv[1]
def load(n):
    im = Image.open(f'{d}/{n}.png').convert('RGBA'); return im.crop(im.getchannel('A').getbbox())
bags = [load(n) for n in ('bag_bamboo_02222', 'bag_red_02223', 'bag_pink_02220')]
cans = [load(n) for n in ('can_brine_02209', 'can_babyBB_02215', 'can_clear5_02208', 'can_braised_02211')]
W, H = 1536, 1024; BH = int(os.environ.get('BH', 470)); CH = int(os.environ.get('CH', 235))
sc = lambda im, h: im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
bags = [sc(b, BH) for b in bags]; cans = [sc(c, CH) for c in cans]
gap = 30; bw = sum(b.width for b in bags) + 2 * gap; x = (W - bw) // 2; base = 660
c = Image.new('RGB', (W, H), 'white'); L = []
bn = ('bag_bamboo_02222', 'bag_red_02223', 'bag_pink_02220'); cn = ('can_brine_02209', 'can_babyBB_02215', 'can_clear5_02208', 'can_braised_02211')
for n, b in zip(bn, bags): c.paste(b, (x, base - b.height), b); L.append(dict(png=f'{d}/{n}.png', x=x, y=base - b.height, w=b.width, h=b.height)); x += b.width + gap
cw = sum(k.width for k in cans) + 3 * 14; x = (W - cw) // 2; cb = base + int(os.environ.get('CBO', 85))
for n, k in zip(cn, cans): c.paste(k, (x, cb - k.height), k); L.append(dict(png=f'{d}/{n}.png', x=x, y=cb - k.height, w=k.width, h=k.height, smin=1.05, smax=1.25)); x += k.width + 14
c.save(sys.argv[2], quality=95); json.dump(L, open(sys.argv[2].rsplit('.', 1)[0] + '_layout.json', 'w'))
