import sys, os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
E_ = os.environ.get
src, bgp, out = sys.argv[1], sys.argv[2], sys.argv[3]
x0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
W, H = 1536, 1024
bg = Image.open(bgp).convert('RGB'); bw, bh = bg.size
cw = int(bh*1.5); x0 = min(x0, bw-cw)
bg = bg.crop((x0, 0, x0+cw, bh)).resize((W, H), Image.LANCZOS)
if E_('INPAINT'):
    b = np.array(bg); mk = np.zeros(b.shape[:2], np.uint8)
    for r in E_('INPAINT').split(';'):
        a, c_, d_, e_ = map(int, r.split(',')); mk[c_:e_, a:d_] = 255
    bg = Image.fromarray(cv2.inpaint(b, mk, 7, cv2.INPAINT_TELEA))
if E_('TABLE'):
    r = [int(v) for v in E_('TABLE').split(',')]
    b = np.array(bg); mk = np.zeros(b.shape[:2], np.uint8); mk[r[1]:r[3], r[0]:r[2]] = 255
    sm = cv2.resize(b, (W//3, H//3), interpolation=cv2.INTER_AREA); mm = cv2.resize(mk, (W//3, H//3), interpolation=cv2.INTER_NEAREST)
    ip = cv2.inpaint(sm, mm, 12, cv2.INPAINT_TELEA)
    ip = cv2.resize(cv2.GaussianBlur(ip, (0, 0), 2), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    ip += np.random.default_rng(5).normal(0, 2.5, ip.shape)
    mf = cv2.GaussianBlur(mk.astype(np.float32)/255, (0, 0), 6)[..., None]
    b = (b.astype(np.float32)*(1-mf) + ip*mf).clip(0, 255).astype(np.uint8); bg = Image.fromarray(b)
bga = np.array(bg).astype(np.float32)
im = np.array(Image.open(src).convert('RGB'))
white = (im.min(2) > 242).astype(np.uint8); bgmask = np.zeros_like(white)
for p in [(0,0),(im.shape[1]-1,0),(0,im.shape[0]-1),(im.shape[1]-1,im.shape[0]-1)]:
    t = white.copy(); mm = np.zeros((im.shape[0]+2, im.shape[1]+2), np.uint8); cv2.floodFill(t, mm, p, 2, flags=4)
    bgmask |= (t == 2).astype(np.uint8)
alpha = (1-bgmask).astype(np.uint8)*255
alpha = cv2.erode(alpha, np.ones((3,3), np.uint8)); alpha = cv2.GaussianBlur(alpha, (0,0), 1.0)
ys, xs = np.where(alpha > 128)
rgb = im[ys.min():ys.max()+1, xs.min():xs.max()+1].astype(np.float32); al = alpha[ys.min():ys.max()+1, xs.min():xs.max()+1]
pw = int(E_('SC', 1000)); ph = int(rgb.shape[0]*pw/rgb.shape[1])
rgb = cv2.resize(rgb, (pw, ph), interpolation=cv2.INTER_AREA); al = cv2.resize(al, (pw, ph), interpolation=cv2.INTER_AREA)
base = int(E_('BASE', 800)); px = (W-pw)//2 + int(E_('DX', 0)); py = base-ph
# scene stats (table/wall) -> partial colour transfer
reg = bga[300:900, 200:1300].reshape(-1, 3); mu, sd = reg.mean(0), reg.std(0)
pm = rgb[al > 128].mean(0); ps = rgb[al > 128].std(0)
rgb = rgb + 0.35*(((rgb-pm)/ps*sd + mu) - rgb)
rgb *= np.array([1.0, 0.95, 0.86]); rgb = rgb*0.90 + 14
# window-light gradient (brighter right/top), warm wood bounce at the bottom
yy = np.linspace(0, 1, ph)[:, None, None]; xx = np.linspace(0, 1, pw)[None, :, None]
rgb *= (0.96 + 0.08*xx - 0.03*yy)
bounce = np.clip((yy-0.78)/0.22, 0, 1)*0.30
rgb = rgb*(1-bounce) + np.array([205, 150, 95])*bounce
rgb = cv2.GaussianBlur(rgb, (0, 0), 0.8)
rgb += np.random.default_rng(3).normal(0, 2.0, rgb.shape)
rgb = np.clip(rgb, 0, 255)
canvas = bga.copy()
def over(layer_rgb, layer_a, x, y):
    h, w = layer_a.shape; x_, y_ = max(x, 0), max(y, 0)
    x2, y2 = min(x+w, W), min(y+h, H)
    sa = layer_a[y_-y:y2-y, x_-x:x2-x][..., None]/255.0
    canvas[y_:y2, x_:x2] = canvas[y_:y2, x_:x2]*(1-sa) + layer_rgb[y_-y:y2-y, x_-x:x2-x]*sa
# per-column foot line (bags and cans stand at different depths)
cols = np.where((al > 128).any(0))[0]
foot = np.array([np.where(al[:, c] > 128)[0].max() for c in cols])
fm = np.zeros((H, W), np.float32)
for c, f in zip(cols, foot):
    fm[py+f-3:py+f+10, px+c] = 1.0
sh = cv2.GaussianBlur(fm, (0, 0), 7)*0.9
M = np.float32([[1, 0, 70], [0, 1, 8]]); cs = cv2.warpAffine(fm, M, (W, H)); cs = cv2.GaussianBlur(cs, (0, 0), 16)*0.55
shadow = np.clip(sh+cs, 0, 0.75)[..., None]
canvas = canvas*(1-shadow) + np.array([55, 28, 12])*shadow
# glossy reflection about each column's foot
L = 130; rl_rgb = np.zeros((H, W, 3), np.float32); rl_a = np.zeros((H, W), np.float32)
for r in range(1, L):
    sy = foot-r; ok = sy >= 0; dy = py+foot+r
    ok &= dy < H
    rl_rgb[dy[ok], px+cols[ok]] = rgb[sy[ok], cols[ok]]
    rl_a[dy[ok], px+cols[ok]] = al[sy[ok], cols[ok]]*0.30*(1-r/L)**1.5
rl_rgb = cv2.GaussianBlur(rl_rgb, (0, 0), 3); rl_a = cv2.GaussianBlur(rl_a, (0, 0), 3)
canvas = canvas*(1-rl_a[..., None]/255.0) + rl_rgb*(rl_a[..., None]/255.0)
over(rgb, al, px, py)
ao = cv2.GaussianBlur(fm, (0, 0), 2.5)*0.35
canvas = canvas*(1-ao[..., None]) + np.array([40, 20, 8])*ao[..., None]
canvas = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).convert('RGBA')
# caption on top: festive brush lettering, bounced/tilted, gold gradient + crimson outline + glow
fpath = E_('FONT', '/home/user/secondshift/cny27/work/fonts/MaShanZheng-Regular.ttf')
size = int(E_('CAP_SZ', 190)); txt = '喜气羊羊'
f = ImageFont.truetype(fpath, size)
ty = int(E_('CAP_Y', 20)); cx = W/2 + int(E_('CAP_DX', 0))
tilts = [-7, 5, -4, 8]; dys = [10, -14, 4, -8]; scl = [1.05, 0.95, 1.0, 1.08]
step = size*0.80; n = len(txt); x_start = cx - step*(n-1)/2
glyphs = []
for i, ch in enumerate(txt):
    g = Image.new('L', (size*2, size*2), 0); gd = ImageDraw.Draw(g)
    bb = gd.textbbox((0, 0), ch, font=f); gd.text((size-(bb[0]+bb[2])/2, size-(bb[1]+bb[3])/2), ch, font=f, fill=255)
    g = g.resize((int(g.width*scl[i]), int(g.height*scl[i])), Image.LANCZOS).rotate(tilts[i], resample=Image.BICUBIC, expand=False)
    glyphs.append((g, int(x_start+i*step), ty+size//2+dys[i]))
mask = Image.new('L', (W, H), 0)
for g, gx, gy in glyphs:
    mask.paste(255, (gx-g.width//2, gy-g.height//2), g)
m = np.array(mask)
# gold gradient fill (bright top -> deep gold bottom) with a highlight band
ys_, xs_ = np.where(m > 0); y0_, y1_ = ys_.min(), ys_.max()
t = np.clip((np.arange(H)-y0_)/(y1_-y0_), 0, 1)[:, None, None]
gold = (1-t)*np.array([255, 238, 150]) + t*np.array([222, 150, 30])
gold = np.broadcast_to(gold, (H, W, 3)).astype(np.float32)
band = np.exp(-((t-0.38)/0.07)**2)*60; gold = np.clip(gold+band, 0, 255)
sm = np.array(mask).astype(np.float32)/255
red = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))   # crimson outline
gl = cv2.GaussianBlur(cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(np.float32)/255, (0, 0), 14)
cv = np.array(canvas.convert('RGB')).astype(np.float32)
sd = cv2.GaussianBlur(np.roll(np.roll(red, 10, 0), 8, 1).astype(np.float32)/255, (0, 0), 7)[..., None]*0.65
cv = cv*(1-sd) + np.array([50, 8, 8])*sd                                      # drop shadow
cv = cv + gl[..., None]*np.array([255, 190, 70])*0.55                          # warm glow
ra = (cv2.GaussianBlur(red.astype(np.float32)/255, (0, 0), 0.8))[..., None]
cv = cv*(1-ra) + np.array([172, 14, 24])*ra                                    # outline
inner = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
gm = cv2.GaussianBlur(inner.astype(np.float32)/255, (0, 0), 0.8)[..., None]
cv = cv*(1-gm) + gold*gm
cv = np.clip(cv, 0, 255)
canvas = Image.fromarray(cv.astype(np.uint8)).convert('RGBA')
# sparkles
dr = ImageDraw.Draw(canvas)
for (sx, sy, r) in [(cx-step*1.9, ty+40, 22), (cx+step*1.9, ty+30, 26), (cx+step*1.2, ty+size*0.95, 14), (cx-step*1.2, ty+size*0.9, 16)]:
    dr.polygon([(sx, sy-r), (sx+r*0.22, sy-r*0.22), (sx+r, sy), (sx+r*0.22, sy+r*0.22), (sx, sy+r), (sx-r*0.22, sy+r*0.22), (sx-r, sy), (sx-r*0.22, sy-r*0.22)], fill=(255, 244, 190))
canvas.convert('RGB').save(out, quality=92)
print((pw, ph), (px, py))
