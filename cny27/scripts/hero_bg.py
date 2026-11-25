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
# caption on top: raw ink-brush lettering (flat colour, dry-brush edges), small English sub-line, red seal
rng = np.random.default_rng(11)
fpath = E_('FONT', '/home/user/secondshift/cny27/work/fonts/MaShanZheng-Regular.ttf')
size = int(E_('CAP_SZ', 250)); txt = '喜气羊羊'; f = ImageFont.truetype(fpath, size)
ty = int(E_('CAP_Y', 20)); cx = W/2 + int(E_('CAP_DX', 0)); step = size*float(E_('CAP_STEP', 0.78))
cols_ = [(176, 18, 28), (158, 106, 22), (176, 18, 28), (158, 106, 22)] if E_('CAP_MIX', '1') == '1' else [(176, 18, 28)]*4
cv = np.array(canvas.convert('RGB')).astype(np.float32)
def dry(mask):
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(E_('BOLD', 9)),)*2))   # thicken strokes like the reference
    m = mask.astype(np.float32)/255
    nz = cv2.GaussianBlur(rng.normal(0, 1, m.shape).astype(np.float32), (0, 0), 2.2)       # ragged edge
    mr = cv2.GaussianBlur(m, (0, 0), 1.2) + nz*0.35*(1-np.abs(2*cv2.GaussianBlur(m, (0, 0), 3)-1)) 
    m2 = np.clip((mr-0.5)*6+0.5, 0, 1)
    st = cv2.GaussianBlur(rng.normal(0, 1, m.shape).astype(np.float32), (0, 0), 1.0)
    st = cv2.blur(st, (41, 1)); st = (st-st.mean())/st.std()                             # horizontal bristle streaks
    edge = np.clip(m2 - cv2.erode(m2, np.ones((9, 9), np.uint8)), 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 3); edge = np.clip(edge*2.2, 0, 1)
    return np.clip(m2*(1-edge*np.clip(st*0.55-0.05, 0, 1)), 0, 1)
x_start = cx - step*(len(txt)-1)/2; ink_all = np.zeros((H, W), np.float32)
for i, ch in enumerate(txt):
    g = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(g)
    bb = gd.textbbox((0, 0), ch, font=f)
    gd.text((x_start+i*step-(bb[0]+bb[2])/2, ty+size/2-(bb[1]+bb[3])/2), ch, font=f, fill=255)
    gm = dry(np.array(g))
    # soft wall shadow, then flat ink with slight tonal variation
    sdw = cv2.GaussianBlur(np.roll(np.roll(gm, 5, 0), 4, 1), (0, 0), 5)[..., None]*0.35
    cv = cv*(1-sdw) + np.array([60, 30, 20])*sdw
    tone = 1 + cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 14)[..., None]*0.10
    cv = cv*(1-gm[..., None]) + (np.array(cols_[i], np.float32)*tone)*gm[..., None]
canvas = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8)).convert('RGBA')
dr = ImageDraw.Draw(canvas)
sub = E_('CAP_SUB', 'GOOD  LUCK  ·  YEAR OF THE GOAT 2027')
try: sf = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf', 26)
except Exception: sf = ImageFont.load_default()
tr = 7; wsum = sum(dr.textlength(c, font=sf)+tr for c in sub)-tr
sx = cx-wsum/2; sy = ty+size*float(E_('SUB_Y', 1.0))
for c in sub:
    dr.text((sx, sy), c, font=sf, fill=(120, 20, 24)); sx += dr.textlength(c, font=sf)+tr
# red seal
sz_ = 54; sxp = cx+step*1.95; syp = ty+size*0.18
dr.rounded_rectangle([sxp, syp, sxp+sz_, syp+sz_], radius=6, fill=(176, 18, 28))
sealf = ImageFont.truetype('/home/user/secondshift/cny27/work/fonts/MaShanZheng-Regular.ttf', 44)
bb = dr.textbbox((0, 0), '羊', font=sealf); dr.text((sxp+sz_/2-(bb[0]+bb[2])/2, syp+sz_/2-(bb[1]+bb[3])/2), '羊', font=sealf, fill=(250, 236, 205))
canvas.convert('RGB').save(out, quality=92)
print((pw, ph), (px, py))
