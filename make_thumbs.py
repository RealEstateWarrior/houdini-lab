"""カード用のサムネイルを作り直す。

カードは 16:10 の枠に画像を流し込む。ところが元の画をそのまま入れると
2つの問題が起きる。

  1. 正方形（620×620）の画を 16:10 に切り抜くと、上下 37.5% が消える。
     実験055・056 のように「何をしているか分からない」のはこれ。
  2. 被写体が画の真ん中に小さく写っているものが多い。
     一覧で並ぶと、ただの白い箱に見える。

どちらも元の画を撮り直さなくても直せる。被写体の外接矩形を取って、
余白を詰めてから 16:10 の板に貼り直せばよい。

    python make_thumbs.py            出力して一覧を出す
    python make_thumbs.py --check    作らずに、いまの状態だけ調べる

出力は out/thumb_NNN.png。build_site.py はこれがあれば優先して使う。
"""

import argparse
import ast
import io
import os
import re

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# カードの縦横比。base.css の .thumb .thumb-img と合わせる。
# 16:10 だと正方形の被写体が幅の 46% しか埋められず、一覧が寂しくなる。
# 4:3 なら 75% まで埋まり、横長の跡（760×260）もまだ収まる。
TARGET = (880, 660)
# 被写体の周りに残す余白（短いほうの辺に対する割合）
MARGIN = 0.06
# 被写体が板のなかで占める割合の上限。これ以上は拡大しない
MAX_FILL = 0.94
# Apprentice が焼き込む Houdini ロゴ。外接矩形を取るときだけ無視する
LOGO_BOX = (0.62, 0.80)   # 右 62% より右、下 80% より下


def load_done():
    src = io.open(os.path.join(HERE, "build_site.py"), encoding="utf-8").read()
    m = re.search(r"^DONE = (\[.*?\n\])\n", src, re.S | re.M)
    return ast.literal_eval(m.group(1))


# Apprentice が右下に焼き込む Houdini ロゴ。
#
# 型を1枚から取って照合する方法は、ロゴの大きさが画の解像度で変わるため
# 360px の画などで当たらなかった。そこでロゴ右端の「オレンジの渦」を
# 手がかりにする。色がはっきりしていて、どの解像度でも必ず1つある。
#
# 渦が見つかったら、そこから左へ「文字の分」をまとめて消す。
# 下に何が写っていようと、ロゴが上書きしている時点で元の絵は失われている。
# だから遠慮なく消してよい（実験062で、砂に被ったロゴを残してしまった）。
LOGO_PAD_RIGHT = 0.25     # 渦の右に残す余白（渦の幅に対する割合）
LOGO_TEXT_SPAN = 9.0      # 渦の幅の何倍ぶん左に文字があるか
LOGO_HALF_HEIGHT = 1.2    # 渦の中心から上下へ、渦の幅の何倍を消すか


# 渦の大きさと位置は、どの解像度でも画の幅に対してほぼ一定だった。
# 実測: 渦の幅 = 幅の 4.3〜5.0%、右端・下端からの距離 = 幅の 6.6〜7.5%
MARK_W = 0.047
MARK_INSET = 0.075


def find_logo_mark(arr):
    """右下にあるオレンジの渦の右下角を探し、(右端, 下端, 渦の幅) を返す。

    外接矩形をそのまま使うと、実験068のように砂の色が条件に引っかかって
    横 200px の箱になってしまう。渦がいる場所は決まっているので、
    探す範囲をそこに絞ってから、いちばん右下の画素を角とみなす。
    """
    H, W = arr.shape[:2]
    x0 = int(W * (1.0 - MARK_INSET - MARK_W - 0.03))
    y0 = max(0, H - int(W * (MARK_INSET + MARK_W + 0.03)))
    r = arr[y0:, x0:]
    if r.size == 0:
        return None
    rgb, alpha = r[:, :, :3], r[:, :, 3]
    # 実測した渦の色は (242, 102, 34)。赤が強く、青との差が大きい
    mark = ((alpha > 120) & (rgb[:, :, 0] > 150) &
            (rgb[:, :, 0] - rgb[:, :, 2] > 60) &
            (rgb[:, :, 1] < rgb[:, :, 0] - 30))
    if mark.sum() < 25:
        return None
    ys, xs = np.nonzero(mark)
    return (x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1, W * MARK_W)


def erase_logo(im):
    """右下のロゴを消す。渦を見つけて、そこから左へ文字の分を透明にする。"""
    if im.mode != "RGBA":
        return im
    arr = np.asarray(im).astype(np.uint8).copy()
    H, W = arr.shape[:2]
    box = find_logo_mark(arr)
    if box is None:
        return im
    mx1, my1, mw = box
    if mw < 6:
        return im
    cy = my1 - mw / 2.0
    x1 = min(W, int(mx1 + mw * LOGO_PAD_RIGHT))
    x0 = max(0, int(x1 - mw * (LOGO_TEXT_SPAN + 1)))
    y0 = max(0, int(cy - mw * LOGO_HALF_HEIGHT))
    y1 = min(H, int(cy + mw * LOGO_HALF_HEIGHT))

    # 何で埋めるか。
    # 透明で抜くと、不透明な板の上にロゴがある画（実験062）で白い穴が空く。
    # 上の行を引き伸ばすと、被写体が上にある画（実験018・067）で筋が伸びる。
    # 箱のまわり1周の色を取って、その中央値で平らに塗るのがいちばん素直だった。
    ring = []
    pad = 4
    ry0, ry1 = max(0, y0 - pad), min(H, y1 + pad)
    rx0, rx1 = max(0, x0 - pad), min(W, x1 + pad)
    if ry0 < y0:
        ring.append(arr[ry0:y0, rx0:rx1].reshape(-1, 4))
    if ry1 > y1:
        ring.append(arr[y1:ry1, rx0:rx1].reshape(-1, 4))
    if rx0 < x0:
        ring.append(arr[y0:y1, rx0:x0].reshape(-1, 4))
    if rx1 > x1:
        ring.append(arr[y0:y1, x1:rx1].reshape(-1, 4))
    if ring:
        fill = np.median(np.concatenate(ring), axis=0)
        if fill[3] < 40:
            fill = np.zeros(4)
    else:
        fill = np.zeros(4)
    arr[y0:y1, x0:x1] = fill.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def subject_mask(im):
    """被写体の画素だけ True にした板を返す。

    透明度があればそれを使う。無ければ四隅の色を背景と見なす。
    OpenGL ROP の出力は透明度つき、コンタクトシートは不透明。
    """
    W, H = im.size
    if im.mode in ("RGBA", "LA"):
        mask = np.asarray(im.convert("RGBA"))[:, :, 3] > 8
        if mask.mean() < 0.995:
            return mask
    rgb = np.asarray(im.convert("RGB")).astype(np.int16)
    corner = np.median(
        np.stack([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]]), axis=0)
    return np.abs(rgb - corner).max(axis=2) > 20


def subject_box(im):
    """被写体の外接矩形。ロゴは数に入れない。"""
    W, H = im.size
    mask = subject_mask(im).copy()
    mask[int(H * LOGO_BOX[1]):, int(W * LOGO_BOX[0]):] = False
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return (0, 0, W, H), 0.0
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    fill = min((box[2] - box[0]) / W, (box[3] - box[1]) / H)
    return box, fill


def background_of(im):
    """貼り付ける板の色。透明度があるなら透明のまま返す。"""
    if im.mode in ("RGBA", "LA"):
        a = np.asarray(im.convert("RGBA"))[:, :, 3]
        if a.min() < 250:
            return None
    rgb = np.asarray(im.convert("RGB"))
    corner = np.median(
        np.stack([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]]),
        axis=0).astype(int)
    return tuple(int(v) for v in corner)


def make_thumb(path, out_path):
    im = Image.open(path)
    im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    im = erase_logo(im)
    W, H = im.size
    box, fill = subject_box(im)

    # 余白を足す。短いほうの辺を基準にするので、細長い画でも比が崩れない
    pad = int(min(box[2] - box[0], box[3] - box[1]) * MARGIN)
    box = (max(0, box[0] - pad), max(0, box[1] - pad),
           min(W, box[2] + pad), min(H, box[3] + pad))
    crop = im.crop(box)

    tw, th = TARGET
    cw, ch = crop.size
    scale = min(tw * MAX_FILL / cw, th * MAX_FILL / ch)
    # 元より大きくはしない。引き伸ばすと粒が見えるだけで情報は増えない
    scale = min(scale, max(1.0, min(tw / cw, th / ch)))
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    crop = crop.resize((nw, nh), Image.LANCZOS)

    bg = background_of(im)
    if bg is None:
        canvas = Image.new("RGBA", TARGET, (0, 0, 0, 0))
    else:
        canvas = Image.new("RGB", TARGET, bg)
    canvas.paste(crop, ((tw - nw) // 2, (th - nh) // 2),
                 crop if crop.mode == "RGBA" else None)
    canvas.save(out_path, optimize=True)
    return fill, (nw / tw, nh / th)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    done = load_done()
    print(f"{'no':>4} {'元の画':<26} {'元の占有':>9} {'後の占有':>17} {'出力':<18}")
    made = skipped = 0
    for item in done:
        name = item.get("thumb") or ""
        src = os.path.join(OUT, name) if name else ""
        if not name or not os.path.exists(src):
            print(f"{item['no']:>4} {'(元の画がない)':<26}")
            skipped += 1
            continue
        out_name = f"thumb_{item['no']}.png"
        dst = os.path.join(OUT, out_name)
        if args.check:
            im = Image.open(src)
            _, fill = subject_box(im)
            print(f"{item['no']:>4} {name:<26} {fill:>9.2f}")
            continue
        fill, after = make_thumb(src, dst)
        print(f"{item['no']:>4} {name:<26} {fill:>9.2f} "
              f"{after[0]:>8.2f} ×{after[1]:>7.2f} {out_name:<18}")
        made += 1
    print(f"\n作った {made} 件 / 元の画がない {skipped} 件")


if __name__ == "__main__":
    main()
