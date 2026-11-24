#!/usr/bin/env python3
"""Photoroom result -> exactly 1536x1024 sRGB JPEG <=1MB (centre crop to 3:2, resize).
usage: finish.py in.jpg out.jpg"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
tw = min(W, round(H * 1.5)); th = round(tw / 1.5)
im = im.crop(((W - tw) // 2, (H - th) // 2, (W - tw) // 2 + tw, (H - th) // 2 + th)).resize((1536, 1024), Image.LANCZOS)
for q in (92, 88, 84, 80, 75):
    im.save(sys.argv[2], quality=q, optimize=True)
    import os
    if os.path.getsize(sys.argv[2]) <= 1_000_000: break
