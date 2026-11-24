#!/usr/bin/env python3
"""Restaged Photoroom JPEG -> final. usage (from cny27/work): single_post.py name gen_raw.jpg
Writes ../out/CNY27_v2_<name>.jpg ; prints restore score (flag if < 0.45)."""
import sys, subprocess
name, gen = sys.argv[1], sys.argv[2]
subprocess.run(['python3', '../scripts/finish.py', gen, f'gen/{name}_1536.jpg'], check=True)
r = subprocess.run(['python3', '../scripts/restore.py', f'gen/{name}_1536.jpg', f'gen/{name}_layout.json', f'../out/CNY27_v2_{name}.jpg'], capture_output=True, text=True)
print(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.stdout)
