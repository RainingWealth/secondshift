import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, bgp, out = sys.argv[1], sys.argv[2], sys.argv[3]
x0 = int(sys.argv[4]) if len(sys.argv) > 4 else 224
W, H = 1536, 1024
bg = Image.open(bgp).convert('RGB'); bw, bh = bg.size
cw = int(bh*1.5); x0 = min(x0, bw-cw)
bg = bg.crop((x0, 0, x0+cw, bh)).resize((W, H), Image.LANCZOS)
import os
if os.environ.get('INPAINT'):
    b=np.array(bg); mk=np.zeros(b.shape[:2],np.uint8)
    for r in os.environ['INPAINT'].split(';'):
        a,b_,c,d=map(int,r.split(',')); mk[b_:d,a:c]=255
    bg=Image.fromarray(cv2.inpaint(b,mk,9,cv2.INPAINT_TELEA))
im = np.array(Image.open(src).convert('RGB'))
# product mask: flood-fill near-white from borders
white = (im.min(2) > 242).astype(np.uint8)
ff = white.copy(); m = np.zeros((im.shape[0]+2, im.shape[1]+2), np.uint8)
bgmask = np.zeros_like(white)
for p in [(0,0),(im.shape[1]-1,0),(0,im.shape[0]-1),(im.shape[1]-1,im.shape[0]-1)]:
    t = white.copy(); mm = np.zeros_like(m); cv2.floodFill(t, mm, p, 2, flags=4)
    bgmask |= (t == 2).astype(np.uint8)
alpha = (1 - bgmask).astype(np.uint8)*255
alpha = cv2.erode(alpha, np.ones((3,3), np.uint8))
alpha = cv2.GaussianBlur(alpha, (0,0), 0.8)
ys, xs = np.where(alpha > 128); x1, x2, y1, y2 = xs.min(), xs.max(), ys.min(), ys.max()
prod = Image.fromarray(np.dstack([im, alpha])).crop((x1, y1, x2+1, y2+1))
sc = 820 / prod.width; prod = prod.resize((int(prod.width*sc), int(prod.height*sc)), Image.LANCZOS)
# warm grade
a = np.array(prod).astype(np.float32); a[..., :3] *= [1.0, 0.95, 0.88]; a[..., :3] = a[..., :3]*0.94 + 6
prod = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
base = int(os.environ.get('BASE',905)); px = (W - prod.width)//2 + 20; py = base - prod.height
canvas = bg.convert('RGBA')
# shadow
sh = Image.new('L', (W, H), 0); d = ImageDraw.Draw(sh)
d.ellipse([px+10, base-22, px+prod.width-10, base+30], fill=150)
sh = sh.filter(ImageFilter.GaussianBlur(16))
cs = Image.new('RGBA', (W, H), (60, 30, 10, 0)); cs.putalpha(sh.point(lambda v: int(v*0.7)))
canvas = Image.alpha_composite(canvas, cs)
# soft reflection on wood
refl = prod.transpose(Image.FLIP_TOP_BOTTOM); ra = np.array(refl).astype(np.float32)
fade = np.linspace(0.20, 0, ra.shape[0])[:, None]; ra[..., 3] *= fade
refl = Image.fromarray(ra.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))
canvas.alpha_composite(refl, (px, base))
canvas.alpha_composite(prod, (px, py))
# caption
f = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', int(os.environ.get('CAP_SZ',120)))
txt = '喜气羊羊'; d = ImageDraw.Draw(canvas)
tw = d.textlength(txt, font=f); tx = (W - tw)/2; ty = int(os.environ.get("CAP_Y",80))
lay = Image.new('RGBA', (W, H), (0,0,0,0)); dl = ImageDraw.Draw(lay)
dl.text((tx+3, ty+5), txt, font=f, fill=(60,10,10,170), stroke_width=4, stroke_fill=(60,10,10,170))
lay = lay.filter(ImageFilter.GaussianBlur(3)); canvas.alpha_composite(lay)
d = ImageDraw.Draw(canvas)
d.text((tx, ty), txt, font=f, fill=(196, 28, 36), stroke_width=5, stroke_fill=(236, 190, 90))
canvas.convert('RGB').save(out, quality=92)
print(prod.size, (px, py))
