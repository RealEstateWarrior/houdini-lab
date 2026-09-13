"""連番画像を、1枚に並べたコンタクトシートと、動くGIFにまとめる。

レポートはPDFとHTMLの両方で使うので、両方の形が要る。
PDFには動きを載せられないのでコンタクトシート、HTMLにはGIFを置く。

Houdini に依存しないので通常の Python（Pillow だけ）で動く。

    python sequence_report.py out/013_pop out/013_sheet.png out/013.gif
"""

import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

BG = (34, 36, 40)
LABEL = (170, 179, 192)
FONT_MONO = "C:/Windows/Fonts/consola.ttf"


def _font(size):
    try:
        return ImageFont.truetype(FONT_MONO, size)
    except OSError:
        return ImageFont.load_default()


def contact_sheet(paths, out_png, columns=5, label_height=18, gap=6):
    """連番を格子状に並べ、各コマにフレーム番号を振る。"""
    if not paths:
        raise ValueError("画像がない")

    with Image.open(paths[0]) as first:
        width, height = first.size

    rows = (len(paths) + columns - 1) // columns
    sheet_width = columns * width + (columns + 1) * gap
    sheet_height = rows * (height + label_height) + (rows + 1) * gap

    sheet = Image.new("RGB", (sheet_width, sheet_height), BG)
    draw = ImageDraw.Draw(sheet)
    font = _font(12)

    for index, path in enumerate(paths):
        column = index % columns
        row = index // columns
        x = gap + column * (width + gap)
        y = gap + row * (height + label_height + gap)
        with Image.open(path) as frame:
            sheet.paste(frame.convert("RGB"), (x, y))
        name = os.path.splitext(os.path.basename(path))[0]
        draw.text((x + 2, y + height + 3), name.split("_")[-1], font=font,
                  fill=LABEL)

    sheet.save(out_png)
    return out_png


def make_gif(paths, out_gif, duration=90, scale=0.7):
    """動きをそのまま見せるためのGIF。HTMLページに置ける。"""
    if not paths:
        raise ValueError("画像がない")

    frames = []
    for path in paths:
        with Image.open(path) as image:
            frame = image.convert("RGB")
            if scale != 1.0:
                size = (int(frame.width * scale), int(frame.height * scale))
                frame = frame.resize(size, Image.LANCZOS)
            frames.append(frame.convert("P", palette=Image.ADAPTIVE))

    frames[0].save(out_gif, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True)
    return out_gif


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    pattern = sys.argv[1]
    paths = sorted(glob.glob(pattern + "_*.png") if not pattern.endswith(".png")
                   else glob.glob(pattern))
    if not paths:
        print(f"該当する画像がない: {pattern}")
        return 1

    print(f"{len(paths)} 枚")
    print(contact_sheet(paths, sys.argv[2]))
    if len(sys.argv) > 3:
        print(make_gif(paths, sys.argv[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
