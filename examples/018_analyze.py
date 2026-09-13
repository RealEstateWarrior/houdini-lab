"""描き直さずに、出来ている画像だけで測り直す。

2つ分かっていない点がある。

A. ノイズが 8.4 あたりで下げ止まった。サンプル数を増やしても減らない床がある。
   床の正体が「基準画自身のノイズ」なら、高サンプル同士を比べたときの差は小さいはず。
   逆に高サンプル同士も 8 前後離れているなら、床は基準画のせいではない。

B. OpenGL と Karma の違いを、階調の数では捉えられなかった。
   画像に透明度が付いていて、背景の画素まで数えていたため。
   中心を横切る1本の線の明るさを並べて、形の違いとして見る。
"""

import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
SAMPLES = [2, 4, 8, 16, 32, 64, 128, 256]


def load(path):
    """透明度を白で埋めてから灰色にする。見たときの見え方に合わせる。"""
    img = Image.open(path)
    if img.mode in ("RGBA", "LA"):
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(white, img.convert("RGBA"))
    gray = img.convert("L")
    return gray.size, list(gray.getdata())


def rms(a, b, mask):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in mask) / len(mask))


size, ref = load(os.path.join(OUT, "018_karma_ref.png"))
width, height = size
# 煙の本体だけ。白い背景（250以上）と、右下のウォーターマークを外す。
mask = [i for i, v in enumerate(ref)
        if v < 250 and not (i % width > width * 0.70 and i // width > height * 0.82)]
print(f"基準画 {size} / 煙とみなした画素 {len(mask)}"
      f"（全体の {100.0 * len(mask) / len(ref):.1f}%）")

images = {}
for spp in SAMPLES:
    images[spp] = load(os.path.join(OUT, f"018_karma_spp{spp:04d}.png"))[1]

print("\nA. どの2枚を比べても、どれくらい離れているか")
print(f"{'':>8}" + "".join(f"{s:>8}" for s in SAMPLES) + f"{'基準':>8}")
for a in SAMPLES:
    row = f"{a:>8}"
    for b in SAMPLES:
        row += f"{rms(images[a], images[b], mask):8.2f}" if a != b else f"{'—':>8}"
    row += f"{rms(images[a], ref, mask):8.2f}"
    print(row)

print("\n  高サンプル同士（128 対 256）:", f"{rms(images[128], images[256], mask):.2f}")
print("  128 対 基準:", f"{rms(images[128], ref, mask):.2f}")
print("  256 対 基準:", f"{rms(images[256], ref, mask):.2f}")

print("\nB. 中心を横切る線の明るさ（左端から右端まで16点）")
row_y = height // 2
_, gl = load(os.path.join(OUT, "018_opengl.png"))
for name, px in (("OpenGL", gl), ("Karma ", ref)):
    xs = [int(width * k / 15) for k in range(16)]
    values = [px[row_y * width + min(x, width - 1)] for x in xs]
    print(f"  {name}: " + " ".join(f"{v:3d}" for v in values))

print("\n  煙の内側だけの統計（背景を除く）")
for name, px in (("OpenGL", gl), ("Karma ", ref)):
    inside = [px[i] for i in range(len(px))
              if px[i] < 250
              and not (i % width > width * 0.70 and i // width > height * 0.82)]
    if not inside:
        print(f"  {name}: 煙の画素なし")
        continue
    mean = sum(inside) / len(inside)
    sd = math.sqrt(sum((v - mean) ** 2 for v in inside) / len(inside))
    print(f"  {name}: {len(inside):6d}画素 / 階調 {len(set(inside)):3d}段 / "
          f"平均 {mean:6.1f} / ばらつき {sd:6.2f} / 最暗 {min(inside):3d}")
