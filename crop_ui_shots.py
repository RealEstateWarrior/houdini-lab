"""撮った Houdini の画面から、手順ページに載せる部分を切り出す。

    guide_<id>_ui.png  → guide_<id>_net.png      ネットワークのノードがある範囲
    guide_<id>_p<n>.png → guide_<id>_p<n>_parm.png  右上のパラメータ欄

画面全体のままだと、ツールバーやタイムラインが大半を占めて肝心の部分が
小さくなる。サイトでは読める大きさで見せたいので切り出す。

    python crop_ui_shots.py
"""

import glob
import os
import re

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

NET_BG = np.array([48, 48, 48])     # ネットワークエディタの背景（実測）
# 標準レイアウトのパラメータ欄（実測。2578×1398 の画面で右上）
PARM_BOX = (0.678, 0.106, 0.998, 0.503)
MAX_W = 1400


def shrink(im, max_w=MAX_W):
    if im.width <= max_w:
        return im
    h = round(im.height * max_w / im.width)
    return im.resize((max_w, h), Image.LANCZOS)


def crop_network(src, dst):
    """最大化したネットワークエディタから、ノードがある範囲だけを切り出す。"""
    im = Image.open(src).convert("RGB")
    W, H = im.size
    a = np.asarray(im).astype(int)
    # 見出し（ツールバー）とタイムラインを除いた、網の描かれている帯
    y0, y1 = int(H * 0.23), int(H * 0.90)
    x0, x1 = int(W * 0.01), int(W * 0.79)
    region = a[y0:y1, x0:x1]
    diff = np.abs(region - NET_BG).max(axis=2) > 28
    ys, xs = np.nonzero(diff)
    if len(xs) < 50:
        return False
    pad = 60
    box = (max(0, x0 + xs.min() - pad), max(int(H * 0.17), y0 + ys.min() - pad),
           min(W, x0 + xs.max() + pad), min(H, y0 + ys.max() + pad))
    shrink(im.crop(box)).save(dst, optimize=True)
    return True


def crop_parm(src, dst):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    box = (int(W * PARM_BOX[0]), int(H * PARM_BOX[1]),
           int(W * PARM_BOX[2]), int(H * PARM_BOX[3]))
    shrink(im.crop(box), 900).save(dst, optimize=True)
    return True


def main():
    nets = parms = 0
    for src in sorted(glob.glob(os.path.join(OUT, "guide_*_ui.png"))):
        gid = re.match(r"guide_(.+)_ui\.png", os.path.basename(src)).group(1)
        if crop_network(src, os.path.join(OUT, f"guide_{gid}_net.png")):
            nets += 1
    for src in sorted(glob.glob(os.path.join(OUT, "guide_*_p[0-9]*.png"))):
        name = os.path.basename(src)
        if not re.match(r"guide_.+_p\d+\.png$", name):
            continue
        crop_parm(src, os.path.join(OUT, name.replace(".png", "_parm.png")))
        parms += 1
    print(f"ネットワーク {nets} 枚 / パラメータ {parms} 枚")


if __name__ == "__main__":
    main()
