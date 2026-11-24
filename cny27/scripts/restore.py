#!/usr/bin/env python3
"""Restore ORIGINAL product pixels onto a Photoroom-restaged image (AI may garble labels).
For each item in layout.json ([{png,x,y,w,h}] in 1536x1024 composite coords, drawn in order) find its best
scale/position in the generated image by edge template matching inside a window around the expected spot,
then paste the original cut-out with a softened alpha edge.
usage: restore.py gen_1536.jpg layout.json out.jpg [smin smax]"""
import sys, json, cv2, numpy as np
gen = cv2.imread(sys.argv[1]); L = json.load(open(sys.argv[2])); out = gen.copy()
smin, smax = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else (0.75, 1.6)
def edges(img):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 1.2)
    return cv2.GaussianBlur(cv2.Canny(g, 40, 120), (0, 0), 1.5).astype('float32')
for it in L:
    cut = cv2.imread(it['png'], cv2.IMREAD_UNCHANGED); ys, xs = np.where(cut[:, :, 3] > 12)
    cut = cut[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; ge = edges(out)
    cx, cy = it['x'] + it['w'] / 2, it['y'] + it['h'] / 2; best = (-1, None)
    for s in np.linspace(it.get('smin', smin), it.get('smax', smax), 41):
        w, h = round(it['w'] * s), round(it['h'] * s); t = cv2.resize(cut, (w, h), interpolation=cv2.INTER_AREA)
        pad = 0.35 * max(w, h); x0, y0 = int(max(0, cx - w / 2 - pad)), int(max(0, cy - h / 2 - pad))
        x1, y1 = int(min(out.shape[1], cx + w / 2 + pad)), int(min(out.shape[0], cy + h / 2 + pad))
        if x1 - x0 <= w or y1 - y0 <= h: continue
        te = edges(t[:, :, :3]); m = cv2.erode((t[:, :, 3] > 200).astype('float32'), np.ones((5, 5)))
        r = cv2.matchTemplate(ge[y0:y1, x0:x1], te * m, cv2.TM_CCORR_NORMED, mask=m)
        _, mx, _, loc = cv2.minMaxLoc(r)
        if mx > best[0]: best = (mx, (x0 + loc[0], y0 + loc[1], w, h, s))
    x, y, w, h, s = best[1]; t = cv2.resize(cut, (w, h), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(cv2.erode(t[:, :, 3], np.ones((3, 3), 'uint8')), (0, 0), 0.9).astype('float32')[..., None] / 255
    roi = out[y:y + h, x:x + w].astype('float32'); out[y:y + h, x:x + w] = (t[:, :, :3] * a + roi * (1 - a)).astype('uint8')
    print(f"{it['png'].split('/')[-1]}: score={best[0]:.3f} scale={s:.2f} at ({x},{y}) {w}x{h}", file=sys.stderr)
cv2.imwrite(sys.argv[3], out, [cv2.IMWRITE_JPEG_QUALITY, 92])
