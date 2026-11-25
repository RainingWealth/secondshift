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
if E_('ALLWHITE'): bgmask = white
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
rgb = rgb + float(E_('CT', 0.35))*(((rgb-pm)/ps*sd + mu) - rgb)
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
# caption on top: stretched, ragged ink-brush calligraphy (flat red, flying-white streaks, jagged ends), no stamp, no English
rng = np.random.default_rng(21)
fpath = E_('FONT', '/home/user/secondshift/cny27/work/fonts/MaShanZheng-Regular.ttf')
size = int(E_('CAP_SZ', 235)); txt = E_('CAP_TXT', '喜气羊羊'); f = ImageFont.truetype(fpath, size)
SX = float(E_('SX', 0.95)); SY = float(E_('SY', 1.3))
ty = int(E_('CAP_Y', 8)); cx = W/2 + int(E_('CAP_DX', 0)); step = size*float(E_('CAP_STEP', 1.0))
col = np.array([int(v) for v in E_('CAP_COL', '188,18,26').split(',')], np.float32)
cv = np.array(canvas.convert('RGB')).astype(np.float32)
def noise(sig, ks=None):
    n = rng.normal(0, 1, (H, W)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), sig) if ks is None else cv2.blur(cv2.GaussianBlur(n, (0, 0), sig), ks)
    return (n-n.mean())/n.std()
nh = noise(1.2, (71, 1)); nv = noise(1.2, (1, 71)); ni = noise(3.0)
def ink(mask):
    m0 = (mask > 128).astype(np.float32)
    m0 = cv2.dilate(m0, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(E_('BOLD', 13)),)*2))
    m0 = cv2.dilate(m0, cv2.getStructuringElement(cv2.MORPH_RECT, tuple(int(v) for v in E_('HD', '15,3').split(','))))   # horizontals heavier than verticals
    sm = cv2.GaussianBlur(m0, (0, 0), 5)
    gy = cv2.Sobel(sm, cv2.CV_32F, 0, 1, ksize=5); gx = cv2.Sobel(sm, cv2.CV_32F, 1, 0, ksize=5)
    wh = np.abs(gy)/(np.abs(gx)+np.abs(gy)+1e-6)                       # 1 where the edge is a horizontal stroke edge
    wh = cv2.GaussianBlur(wh, (0, 0), 4)
    streak = wh*nh + (1-wh)*nv                                          # bristle streaks run along the stroke
    edge = np.clip(cv2.GaussianBlur(m0, (0, 0), 2) - cv2.GaussianBlur(m0, (0, 0), 10) + 0.5, 0, 1)
    near = np.clip(1-np.abs(2*cv2.GaussianBlur(m0, (0, 0), 6)-1), 0, 1)  # 1 near a stroke edge
    body = cv2.GaussianBlur(m0, (0, 0), 1.0) + float(E_('RAG', 0.55))*ni*near + float(E_('RAG2', 0.35))*streak*near   # jagged, streak-driven edge
    shape = np.clip((body-0.5)*5+0.5, 0, 1)
    tail = cv2.dilate(m0, cv2.getStructuringElement(cv2.MORPH_RECT, (110, 3))) + cv2.dilate(m0, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 55)))
    tail = (tail > 0) & (m0 < 0.5) & (streak*near > 0.62)               # flying-white tails off stroke ends
    shape = np.maximum(shape, cv2.GaussianBlur(tail.astype(np.float32), (0, 0), 0.8)*0.9)
    shape *= 1-float(E_('INT', 0.5))*np.clip(streak*0.9-0.9, 0, 1)*(1-near*0.3)   # dry gaps inside the strokes
    return np.clip(shape, 0, 1)
x_start = cx - step*(len(txt)-1)/2
M = Image.new('L', (W, H), 0)
f0 = ImageFont.truetype(E_('FONT0'), size) if E_('FONT0') else f
for i, ch in enumerate(txt):
    gl = Image.new('L', (size*2, size*2), 0); gd = ImageDraw.Draw(gl)
    ff = f0 if i == 0 else f
    bb = gd.textbbox((0, 0), ch, font=ff); gd.text((size-(bb[0]+bb[2])/2, size-(bb[1]+bb[3])/2), ch, font=ff, fill=255)
    gl = gl.resize((int(gl.width*SX), int(gl.height*SY)), Image.LANCZOS)
    M.paste(255, (int(x_start+i*step-gl.width/2), int(ty+size*SY/2-gl.height/2)), gl)
gm = ink(np.array(M))
if E_('GOLD', '1') == '1':
    core = (gm > 0.3).astype(np.uint8)
    ow = int(E_('OUTW', 11))
    outl = cv2.GaussianBlur(cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ow, ow))).astype(np.float32), (0, 0), 1.0)
    halo = cv2.GaussianBlur(cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45))).astype(np.float32), (0, 0), 22)[..., None]*0.38
    cv = cv*(1-halo) + np.array([70, 14, 14])*halo                                   # darken the wall behind the lettering
    sdw = cv2.GaussianBlur(np.roll(np.roll(outl, 7, 0), 6, 1), (0, 0), 6)[..., None]*0.55
    cv = cv*(1-sdw) + np.array([30, 6, 6])*sdw
    cv = cv*(1-outl[..., None]) + np.array([112, 10, 20])*outl[..., None]            # deep crimson outline
    ys_, xs_ = np.where(core > 0); y0_, y1_ = ys_.min(), ys_.max()
    t = np.clip((np.arange(H)-y0_)/max(y1_-y0_, 1), 0, 1)[:, None, None]
    gold = ((1-t)*np.array([255, 236, 140]) + t*np.array([214, 142, 22]))
    gold = np.clip(np.broadcast_to(gold, (H, W, 3)) + np.exp(-((t-0.3)/0.08)**2)*45, 0, 255).astype(np.float32)
    gold = gold*(1-0.12*np.clip(cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 6), -1, 1)[..., None])
    cv = cv*(1-gm[..., None]) + gold*gm[..., None]
else:
    sdw = cv2.GaussianBlur(np.roll(np.roll(gm, 6, 0), 5, 1), (0, 0), 6)[..., None]*0.35
    cv = cv*(1-sdw) + np.array([60, 30, 20])*sdw
    tone = 1 + cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 14)[..., None]*0.10
    dark = np.clip(cv2.GaussianBlur(gm, (0, 0), 2)-cv2.GaussianBlur(gm, (0, 0), 7), 0, 1)[..., None]
    cv = cv*(1-gm[..., None]) + (col*tone*(1-0.25*dark))*gm[..., None]
canvas = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8)).convert('RGBA')
canvas.convert('RGB').save(out, quality=92)
print((pw, ph), (px, py))
