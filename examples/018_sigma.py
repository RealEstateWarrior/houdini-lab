"""各サンプル数のノイズ量を、基準画に頼らずに求める。

独立な2枚を比べたときの差は、それぞれのノイズが重なったものになる。

    差(a,b)² = σ(a)² + σ(b)²

3枚あれば連立方程式になり、1枚ずつのノイズが解ける。

    σ(a)² = ( 差(a,b)² + 差(a,c)² − 差(b,c)² ) / 2

こうすれば「基準画にもノイズが残っている」問題を回避できる。
基準画の良し悪しに結果が左右されない。
"""

import json
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
SAMPLES = [2, 4, 8, 16, 32, 64, 128, 256]


def load(path):
    img = Image.open(path)
    if img.mode in ("RGBA", "LA"):
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(white, img.convert("RGBA"))
    gray = img.convert("L")
    return gray.size, list(gray.getdata())


size, ref = load(os.path.join(OUT, "018_karma_ref.png"))
width, height = size
mask = [i for i, v in enumerate(ref)
        if v < 250 and not (i % width > width * 0.70 and i // width > height * 0.82)]

px = {s: load(os.path.join(OUT, f"018_karma_spp{s:04d}.png"))[1] for s in SAMPLES}


def sq(a, b):
    return sum((px[a][i] - px[b][i]) ** 2 for i in mask) / len(mask)


rows = []
print(f"煙とみなした画素: {len(mask)}")
print(f"\n{'サンプル':>8} {'ノイズ σ':>10} {'前段との比':>10} {'予測':>8} {'ずれ%':>8}")
prev = None
for i, spp in enumerate(SAMPLES):
    # 近い3枚で連立させる（離れすぎると差が飽和して精度が落ちる）
    trio = SAMPLES[max(0, min(i - 1, len(SAMPLES) - 3)):][:3]
    if spp not in trio:
        trio = SAMPLES[i:i + 3] if i + 3 <= len(SAMPLES) else SAMPLES[-3:]
    a = spp
    b, c = [t for t in trio if t != a][:2]
    value = (sq(a, b) + sq(a, c) - sq(b, c)) / 2.0
    sigma = math.sqrt(max(value, 0.0))
    ratio = None if prev is None else sigma / prev
    gap = None if ratio is None else 100.0 * (ratio - 0.70711) / 0.70711
    rows.append({"spp": spp, "sigma": sigma, "ratio": ratio, "gap_pct": gap,
                 "solved_with": [a, b, c]})
    print(f"{spp:8d} {sigma:10.3f} "
          f"{('' if ratio is None else f'{ratio:.4f}'):>10} "
          f"{('' if ratio is None else '0.7071'):>8} "
          f"{('' if gap is None else f'{gap:+.1f}'):>8}")
    prev = sigma

print("\nサンプル数を4倍にしたときの比（式なら 0.5000）")
for i in range(len(SAMPLES) - 2):
    a, b = rows[i], rows[i + 2]
    print(f"  {a['spp']:4d} → {b['spp']:4d}: {b['sigma'] / a['sigma']:.4f}")

with open(os.path.join(OUT, "018_sigma.json"), "w", encoding="utf-8") as fp:
    json.dump({"mask_pixels": len(mask), "rows": rows}, fp,
              ensure_ascii=False, indent=2)
print("\n保存: out/018_sigma.json")
