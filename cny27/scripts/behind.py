"""Put a cut-out hamper BEHIND the main product as background decor.
usage: behind.py backdrop.jpg hamper_cut.png out.jpg   env: FIX='x0,y0,x1,y1;..' (inpaint rects), HW width px, TILT deg (ccw), CX,BY (x centre / table y of lowest point), BLUR"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter
E_ = os.environ.get
bgp, hp, out = sys.argv[1:4]
W, H = 1536, 1024
bg = np.array(Image.open(bgp).convert('RGB').resize((W, H)))
rng = np.random.default_rng(7)
for r in (E_('FIX') or '').split(';'):
    if not r: continue
    x0, y0, x1, y1 = map(int, r.split(','))
    mk = np.zeros(bg.shape[:2], np.uint8); mk[y0:y1, x0:x1] = 255
    sm = cv2.resize(bg, (W//3, H//3), interpolation=cv2.INTER_AREA); mm = cv2.resize(mk, (W//3, H//3), interpolation=cv2.INTER_NEAREST)
    ip = cv2.resize(cv2.GaussianBlur(cv2.inpaint(sm, mm, 12, cv2.INPAINT_TELEA), (0, 0), 2), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    ip += rng.normal(0, 2.5, ip.shape); mf = cv2.GaussianBlur(mk.astype(np.float32)/255, (0, 0), 6)[..., None]
    bg = (bg.astype(np.float32)*(1-mf) + ip*mf).clip(0, 255).astype(np.uint8)
h = Image.open(hp).convert('RGBA'); h = h.crop(h.getchannel('A').getbbox())
hw = int(E_('HW', 600)); h = h.resize((hw, int(h.height*hw/h.width)), Image.LANCZOS)
h = h.rotate(float(E_('TILT', 16)), resample=Image.BICUBIC, expand=True)
a = np.array(h).astype(np.float32); al = a[..., 3]; rgb = a[..., :3]
# blend into the scene: warm/crimson grade, haze toward the wall, softer contrast, depth blur
wall = bg[250:420, 300:1250].reshape(-1, 3).mean(0)
rgb = rgb*np.array([1.0, 0.88, 0.84]); rgb = rgb*0.88 + 12
rgb = rgb*(1-0.18) + wall*0.18
rgb = cv2.GaussianBlur(rgb, (0, 0), float(E_('BLUR', 1.8))); al = cv2.GaussianBlur(al, (0, 0), float(E_('BLUR', 1.8))*0.7)
rgb += rng.normal(0, 2.0, rgb.shape)
ys, xs = np.where(al > 128); low_y, low_x = ys.max(), xs[ys.argmax()]
cx, by = int(E_('CX', 520)), int(E_('BY', 775))
px, py = (int(E_('LEFT'))-xs.min() if E_('LEFT') else cx-low_x), by-low_y
cv = bg.astype(np.float32)
# contact + cast shadow on the table
sh = np.zeros((H, W), np.float32); m_ = np.zeros((H, W), np.float32)
x0_, y0_ = max(px, 0), max(py, 0); x1_, y1_ = min(px+al.shape[1], W), min(py+al.shape[0], H)
m_[y0_:y1_, x0_:x1_] = al[y0_-py:y1_-py, x0_-px:x1_-px]/255
foot = np.zeros((H, W), np.float32)
for xx in range(x0_, x1_):
    col = np.where(m_[:, xx] > 0.5)[0]
    if len(col): foot[col.max()-2:col.max()+10, xx] = 1
sh = cv2.GaussianBlur(foot, (0, 0), 9)*0.85 + cv2.GaussianBlur(cv2.warpAffine(foot, np.float32([[1, 0, 60], [0, 1, 10]]), (W, H)), (0, 0), 16)*0.5
sh = np.clip(sh, 0, 0.8)[..., None]
cv = cv*(1-sh) + np.array([50, 18, 10])*sh
sa = m_[y0_:y1_, x0_:x1_, None]
cv[y0_:y1_, x0_:x1_] = cv[y0_:y1_, x0_:x1_]*(1-sa) + rgb[y0_-py:y1_-py, x0_-px:x1_-px]*sa
Image.fromarray(cv.clip(0, 255).astype(np.uint8)).save(out, quality=95)
print('hamper', al.shape, 'at', (px, py))
