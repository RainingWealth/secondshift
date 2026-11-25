"""Box (cut-out) + 4 copies of the standalone jar in front, graded to the warm scene. usage: jars_combo.py box.png jar.png out.png"""
import sys, numpy as np, cv2
from PIL import Image
def tight(p):
    im = Image.open(p).convert('RGBA'); a = np.array(im)[..., 3]; ys, xs = np.where(a > 100)
    return im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))
box = tight(sys.argv[1]); jar = tight(sys.argv[2])
a = np.array(jar).astype(np.float32); rgb = a[..., :3]; al = a[..., 3]/255
mn = rgb.min(2); mx = rgb.max(2)
w = np.clip((mn-165)/55, 0, 1)*np.clip(1-(mx-mn)/38, 0, 1); w = cv2.GaussianBlur(w, (0, 0), 1.2)
rgb = np.clip(rgb*np.array([1.06, 0.97, 0.84]), 0, 255)                     # cool studio light -> warm scene
H, W = al.shape; yy, xx = np.mgrid[0:H, 0:W]; u = (xx/W-0.5)*2; v = yy/H
rgb = rgb*(1-0.16*np.abs(u)**2.2+0.06*(-u))[..., None]                       # cylinder shading, window light from the left
side = np.clip((np.abs(u)-0.65)/0.35, 0, 1)[..., None]
rgb = rgb*(1-0.22*side)+np.array([205, 95, 50])*0.22*side                    # orange bounce from the box
rgb = rgb+(np.exp(-((u+0.62)/0.07)**2)*np.clip(1-v*1.1, 0, 1))[..., None]*38  # specular streak
rgb = rgb*(1-0.18*np.clip((v-0.88)/0.12, 0, 1))[..., None]
alpha = al*(1-0.72*w)
edge = np.clip(cv2.GaussianBlur(al, (0, 0), 3)-cv2.GaussianBlur(al, (0, 0), 9), 0, 1)
alpha = np.clip(alpha+edge*0.5, 0, 1)*(al > 0.02)
jar = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha*255]).astype(np.uint8))
bw = 960; box = box.resize((bw, int(box.height*bw/box.width)), Image.LANCZOS)
canvas = np.zeros((1024, 1536, 4), np.float32); top = 150; bx = (1536-bw)//2
canvas[top:top+box.height, bx:bx+bw] = np.array(box).astype(np.float32)
ba = np.array(box)[..., 3]; rows = np.where((ba > 128).sum(1) > 0.6*bw)[0]; body_bottom = top+rows.max()
spec = [(288, -12, 0.96), (302, 6, 1.02), (296, -4, 1.00), (284, -14, 0.97)]; order = [0, 3, 2, 1]; ov = -8
imgs = []
for h, dy, br in spec:
    j = jar.resize((int(jar.width*h/jar.height), h), Image.LANCZOS)
    ja = np.array(j).astype(np.float32); ja[..., :3] *= br; imgs.append((Image.fromarray(np.clip(ja, 0, 255).astype(np.uint8)), dy))
tw = sum(j.width for j, _ in imgs)+3*ov; x = (1536-tw)//2; xs = []
for j, dy in imgs: xs.append(x); x += j.width+ov
box_mask = canvas[..., 3]/255; shadow = np.zeros((1024, 1536), np.float32)
for i in order:                                    # contact / ambient-occlusion shadow of each jar on the box wall
    j, dy = imgs[i]; ja = np.array(j)[..., 3].astype(np.float32)/255; y0 = body_bottom+82-j.height+dy
    layer = np.zeros((1024, 1536), np.float32); layer[y0:y0+j.height, xs[i]:xs[i]+j.width] = ja
    shadow = np.maximum(shadow, cv2.warpAffine(layer, np.float32([[1, 0, 14], [0, 1, -10]]), (1536, 1024)))
shadow = cv2.GaussianBlur(shadow, (0, 0), 13)*0.42*box_mask
canvas[..., :3] = canvas[..., :3]*(1-shadow[..., None])+np.array([90, 35, 20])*shadow[..., None]
im = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
for i in order:
    j, dy = imgs[i]; im.alpha_composite(j, (xs[i], body_bottom+82-j.height+dy))
im.save(sys.argv[3]); print('jars width', tw)
