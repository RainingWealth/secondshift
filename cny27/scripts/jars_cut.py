"""Cut the 4 cookie jars out of the open-box photo as round cylinders with full round gold lids.
usage: jars_cut.py cookies_box.jpg out.png"""
import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1:3]
im = Image.open(src).crop((370, 620, 1310, 1010)).convert('RGB'); OY = 36
W, H = im.size
base = Image.new('RGB', (W, H+OY)); base.paste(im, (0, OY))
a = np.array(base).copy()
# fill the padded top by mirroring the first rows (only matters behind the new lid)
for y in range(OY): a[y] = a[2*OY-y-1] if 2*OY-y-1 < H+OY else a[OY]
base = Image.fromarray(a)
JARS = [(24, 248, 264, (125, 183)), (262, 482, 270, (340, 397)), (496, 703, 256, (568, 625)), (722, 930, 280, (832, 890))]
S = 3                                              # supersample factor
mask = Image.new('L', (W*S, (H+OY)*S), 0); md = ImageDraw.Draw(mask)
lid = Image.new('RGBA', (W*S, (H+OY)*S), (0, 0, 0, 0)); ld = ImageDraw.Draw(lid)
tagpix = []
for x0, x1, yb, (tx0, tx1) in JARS:
    cx = (x0+x1)/2; w = x1-x0; yb += OY
    ryb = w*0.085                                   # elliptical bottom
    lid_c = OY+22; lrx = w*0.485; lry = w*0.115     # lid top ellipse
    lid_b = OY+64                                    # lid bottom (front)
    # silhouette: lid ellipse + lid band + body + bottom ellipse
    def el(draw, cx_, cy_, rx, ry, **k): draw.ellipse([(cx_-rx)*S, (cy_-ry)*S, (cx_+rx)*S, (cy_+ry)*S], **k)
    el(md, cx, lid_c, lrx, lry, fill=255)
    md.rectangle([(cx-lrx)*S, lid_c*S, (cx+lrx)*S, (lid_b)*S], fill=255)
    md.rectangle([x0*S, (lid_b-8)*S, x1*S, (yb-ryb)*S], fill=255)
    el(md, cx, yb-ryb, w/2, ryb, fill=255)
    el(md, cx, lid_b, lrx, lry*0.9, fill=255)
    # gold lid top (drawn over the photo): rim, top surface, recessed centre, highlight
    el(ld, cx, lid_c, lrx, lry, fill=(168, 108, 34, 255))
    el(ld, cx, lid_c, lrx-3, lry-2.5, fill=(226, 168, 70, 255))
    el(ld, cx, lid_c+0.5, lrx*0.78, lry*0.68, fill=(210, 148, 52, 255))
    el(ld, cx-lrx*0.22, lid_c-lry*0.25, lrx*0.40, lry*0.30, fill=(246, 206, 120, 200))
    tagpix.append((tx0, tx1))
lid = lid.filter(ImageFilter.GaussianBlur(1.0*S/3))
base_r = base.resize((W*S, (H+OY)*S), Image.LANCZOS).convert('RGBA')
base_r.alpha_composite(lid)
# lid front band: extend photo's gold band upward is replaced by synthetic ribbed gold under the ellipse
arr = np.array(base_r)
for x0, x1, yb, _ in JARS:
    cx = (x0+x1)/2; w = x1-x0; lrx = w*0.485; lid_c = OY+22; lid_b = OY+64
    ys = np.arange(int((lid_c)*S), int(lid_b*S)); xs = np.arange(int((cx-lrx)*S), int((cx+lrx)*S))
    X, Y = np.meshgrid(xs, ys); t = (Y/S-lid_c)/(lid_b-lid_c)
    shade = 0.78+0.22*np.cos((X/S-cx)/lrx*1.2)                 # cylinder shading across the lid
    rib = 0.93+0.07*np.sin(X/S*1.9)                            # vertical ribs
    col = np.stack([196*shade*rib, 128*shade*rib, 40*shade*rib], -1)
    keep = Y/S > lid_c+0.25*(lid_b-lid_c)                      # keep the real photo near the lid's lower edge
    blend = np.clip((Y/S-(lid_b-14))/14, 0, 1)[..., None]*0.0
    cur = arr[ys[0]:ys[-1]+1, xs[0]:xs[-1]+1, :3].astype(np.float32)
    region_w = np.clip(1-(Y/S-(lid_b-16))/16, 0, 1)[..., None]  # fade synthetic into the real lid edge
    new = col*region_w + cur*(1-region_w)
    # do not paint over the lid top ellipse (already drawn): only below its centre line
    m = (Y/S > lid_c)[..., None]
    arr[ys[0]:ys[-1]+1, xs[0]:xs[-1]+1, :3] = np.where(m, new, cur).astype(np.uint8)
out_im = Image.fromarray(arr).convert('RGB')
# restore the maroon label tags on top of the lid (and extend them over the lid top)
orig = np.array(im)
o = np.array(out_im.resize((W, H+OY), Image.LANCZOS))
for (tx0, tx1) in tagpix:
    patch = orig[26:130, tx0:tx1]
    o[OY+26:OY+130, tx0:tx1] = patch
    mar = np.median(orig[30:40, tx0+8:tx1-8].reshape(-1, 3), 0)
    o[OY+8:OY+26, tx0:tx1] = mar
alpha = np.array(mask.resize((W, H+OY), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8)))
# remove the white box-floor fringe along the lower silhouette edge
rgb = o.astype(np.int16); a2 = alpha.copy()
band = (a2 > 0) & (cv2.erode(a2, np.ones((15, 15), np.uint8)) == 0)
light = (rgb.min(2) > 190) & ((rgb.max(2)-rgb.min(2)) < 40)
a2[band & light] = 0
res = Image.fromarray(np.dstack([o, a2]))
res = res.crop(Image.fromarray(a2).getbbox()); res.save(out); print(res.size)
bg = Image.new('RGB', res.size, (150, 30, 40)); bg.paste(res, (0, 0), res); bg.save(out.replace('.png', '_prev.jpg'), quality=88)
