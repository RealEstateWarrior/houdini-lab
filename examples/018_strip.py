"""サンプル数を変えたときのザラつきを、目で見える形に並べる。

数値表だけだと「ノイズが減った」が実感できない。同じ場所を切り出して横に並べる。
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

from graph_report import FONT_MONO, FONT_UI, _font  # noqa: E402

SHOTS = [2, 8, 32, 256]
CROP = (215, 85, 425, 295)     # 煙の中心あたり
SCALE = 2                       # ザラつきが見えるように拡大
GAP = 14
LABEL_H = 66
BG = (255, 255, 255)
INK = (29, 29, 31)
DIM = (134, 134, 139)


def load(path):
    img = Image.open(path)
    if img.mode in ("RGBA", "LA"):
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(white, img.convert("RGBA"))
    return img.convert("RGB")


def main():
    tiles = []
    for spp in SHOTS:
        img = load(os.path.join(OUT, f"018_karma_spp{spp:04d}.png")).crop(CROP)
        img = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
        tiles.append((spp, img))

    tile_w, tile_h = tiles[0][1].size
    width = tile_w * len(tiles) + GAP * (len(tiles) - 1)
    sheet = Image.new("RGB", (width, tile_h + LABEL_H), BG)
    draw = ImageDraw.Draw(sheet)
    f_name = _font(FONT_UI, 22)
    f_sub = _font(FONT_UI, 16)

    sigma = {2: 18.316, 8: 6.516, 32: 3.413, 256: 2.088}
    for index, (spp, img) in enumerate(tiles):
        x = index * (tile_w + GAP)
        sheet.paste(img, (x, 0))
        draw.rectangle([x, 0, x + tile_w - 1, tile_h - 1], outline=(226, 226, 232))
        draw.text((x, tile_h + 8), f"{spp} サンプル", font=f_name, fill=INK)
        draw.text((x, tile_h + 34), f"ノイズ {sigma[spp]:.2f}", font=f_sub, fill=DIM)

    path = os.path.join(OUT, "018_noise_strip.png")
    sheet.save(path)
    print("保存:", path, sheet.size)


if __name__ == "__main__":
    main()
