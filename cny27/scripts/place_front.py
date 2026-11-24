#!/usr/bin/env python3
"""Paste ORIGINAL cut-outs in a centred row in front of the set, blended into the scene:
warm colour grade, red table bounce, directional cast shadow + contact AO, glossy reflection, slight DOF blur, matched grain.
usage: place_front.py base.jpg out.jpg base_y cut_h gap png1 png2 ..."""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageChops
base = Image.open(sys.argv[1]).convert('RGB'); W, H = base.size
by, ch, gap = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); items = []
for p in sys.argv[6:]:
    im = Image.open(p).convert('RGBA'); im = im.crop(im.getchannel('A').getbbox()); items.append(im.resize((round(im.width * ch / im.height), ch), Image.LANCZOS))
def squash_lid(im, frac=0.15, k=0.5):
    w, h = im.size; lid = int(h * frac); nl = max(1, int(lid * k))
    out = Image.new('RGBA', (w, h - lid + nl), (0, 0, 0, 0)); out.paste(im.crop((0, lid, w, h)), (0, nl)); out.paste(im.crop((0, 0, w, lid)).resize((w, nl), Image.LANCZOS), (0, 0)); return out
_reg = np.asarray(base).astype('float32')[470:900, 300:1250].reshape(-1, 3); MU, SD = _reg.mean(0), _reg.std(0)
def grade(im):
    a = np.asarray(im.convert('RGB')).astype('float32'); al = im.getchannel('A')
    m = np.asarray(al) > 128; mu, sd = a[m].mean(0), a[m].std(0) + 1e-3
    a = a + 0.38 * ((a - mu) / sd * SD * 1.15 + MU - a)                         # pull palette toward the scene
    gr = a.mean(2, keepdims=True); a = gr + (a - gr) * 0.88                      # tame saturation
    a *= np.array([1.00, 0.91, 0.82]); a = a * 0.92 + 8                          # warm key, lifted blacks
    h = a.shape[0]; g = np.linspace(0, 1, h)[:, None, None] ** 2.2               # red lacquer bounce toward the base
    a = a * (1 - 0.30 * g) + np.array([205, 35, 25]) * 0.30 * g
    w = a.shape[1]; side = np.linspace(1, 0, w)[None, :, None]; a += 14 * side * np.array([1.0, 0.85, 0.6])  # key light from left
    out = Image.fromarray(np.clip(a, 0, 255).astype('uint8')); out.putalpha(al.filter(ImageFilter.GaussianBlur(0.7)))
    return out.filter(ImageFilter.GaussianBlur(0.55))
items = [grade(squash_lid(i)) for i in items]
x = (W - (sum(i.width for i in items) + gap * (len(items) - 1))) // 2
cast = Image.new('L', (W, H), 0); ao = Image.new('L', (W, H), 0); dc = ImageDraw.Draw(cast); da = ImageDraw.Draw(ao)
refl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); pos = []
for i in items:
    ry = max(7, int(i.width * 0.075))
    da.ellipse((x - 4, by - 2 * ry + 3, x + i.width + 4, by + 5), fill=255)                      # footprint: base ellipse sits ON the table
    da.ellipse((x - 14, by - 2 * ry - 4, x + i.width + 14, by + 16), fill=120)                   # soft AO ring
    dc.polygon([(x + 8, by - 4), (x + i.width * .9, by - 4), (x + i.width + 140, by + 10), (x + i.width * .3 + 60, by + 26)], fill=110)  # cast to the right (key from left)
    f = i.transpose(Image.FLIP_TOP_BOTTOM); fade = Image.linear_gradient('L').resize((1, f.height)).transpose(Image.FLIP_TOP_BOTTOM).resize(f.size).point(lambda v: int(v * 0.38))
    f.putalpha(ImageChops.multiply(f.getchannel('A'), fade)); refl.alpha_composite(f.filter(ImageFilter.GaussianBlur(2.2)), (x, by - ry)); pos.append(x); x += i.width + gap
sh = ImageChops.lighter(ao.filter(ImageFilter.GaussianBlur(7)), cast.filter(ImageFilter.GaussianBlur(16)))
base = Image.composite(Image.new('RGB', (W, H), (25, 0, 0)), base, sh.point(lambda v: int(v * 0.72))); base.paste(refl, (0, 0), refl)
layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for i, px in zip(items, pos): layer.alpha_composite(i, (px, by - i.height))
base.paste(layer, (0, 0), layer)
n = np.asarray(base).astype('float32'); rng = np.random.default_rng(7); m = np.asarray(layer.getchannel('A')).astype('float32')[..., None] / 255
n += rng.normal(0, 2.2, n.shape) * m                                                          # grain on pasted pixels to match AI noise
Image.fromarray(np.clip(n, 0, 255).astype('uint8')).save(sys.argv[2], quality=93)
