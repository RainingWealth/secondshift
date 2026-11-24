#!/usr/bin/env python3
"""Keep only the main object of a Photoroom cut-out (drops leftover v1 background bits).
Main = largest alpha component whose bbox centre is within 8% of the image centre line. usage: cutclean.py in.png out.png [x0 x1]"""
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED); a = im[:, :, 3]
n, lab, st, _ = cv2.connectedComponentsWithStats((a > 12).astype('uint8'), connectivity=8)
H, W = a.shape; best, ba = 0, 0
for i in range(1, n):
    x, y, w, h, ar = st[i]
    cx = x + w / 2
    if abs(cx - W / 2) < W * 0.08 and ar > ba: best, ba = i, ar   # centroid in centre band
keep = (lab == best)
# also keep small satellites touching the main bbox (e.g. handle straps, glass edges)
x, y, w, h, _ = st[best]; pad = 12
for i in range(1, n):
    xi, yi, wi, hi, ai = st[i]
    if i != best and ai > 40 and xi >= x - pad and yi >= y - pad and xi + wi <= x + w + pad and yi + hi <= y + h + pad: keep |= (lab == i)
if len(sys.argv) > 4:  # optional hard x-range (fractions) for objects touching leftover debris
    cols = np.zeros_like(keep); cols[:, int(W * float(sys.argv[3])):int(W * float(sys.argv[4]))] = True; keep &= cols
im[:, :, 3] = np.where(keep, a, 0); cv2.imwrite(sys.argv[2], im)
