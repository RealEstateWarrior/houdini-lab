"""実験030 の点検結果を1枚の図にする。

接続図を作らない回なので、サムネイルになる画がない。
測り直した7項目と、その結果を並べた表を描く。

    python examples/030_card.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")

FONT_UI = "C:/Windows/Fonts/meiryo.ttc"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"

GROUND = (255, 255, 255)
PLATE = (245, 245, 247)
INK = (29, 29, 31)
MID = (74, 74, 79)
DIM = (134, 134, 139)
WIRE = (232, 232, 237)
OK = (0, 102, 204)
NG = (179, 38, 30)

ROWS = [
    ("002", "点数はいつも「面数 + 2」か", "○", "7通りすべて成立"),
    ("002", "縮みは外挿値 0.83951 に収束するか", "○", "8回で差 0.000006"),
    ("004", "パラメータ名は rough / oct / lac か", "○", "roughness は存在しない"),
    ("009", "rand(@ptnum) は毎回同じか", "○", "400点で差 0.000000000000"),
    ("011", "重み N は分割 N 回まで角を保つか", "○", "分割4回・5回でも成立"),
    ("008", "scatter の出力はいつも N を持つか", "✗", "N は作らない。引き継ぐだけ"),
    ("012", "sphere の rows / cols は効かないのか", "✗", "Polygon Mesh なら効く"),
]


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def main():
    width = 1120
    head = 120
    row_h = 62
    height = head + row_h * len(ROWS) + 52

    image = Image.new("RGB", (width, height), GROUND)
    draw = ImageDraw.Draw(image)

    f_title = font(FONT_UI, 34)
    f_sub = font(FONT_UI, 19)
    f_body = font(FONT_UI, 21)
    f_note = font(FONT_UI, 17)
    f_no = font(FONT_MONO, 20)
    f_mark = font(FONT_UI, 26)

    draw.text((44, 34), "実験030 — 過去29回を測り直す", font=f_title, fill=INK)
    draw.text((46, 78), "7項目を再測定。5つは確認、2つは書き方が不正確だった。",
              font=f_sub, fill=DIM)

    y = head
    for index, (no, question, mark, note) in enumerate(ROWS):
        if index % 2 == 0:
            draw.rectangle([44, y, width - 44, y + row_h], fill=PLATE)
        draw.line([44, y, width - 44, y], fill=WIRE)

        draw.text((62, y + 20), no, font=f_no, fill=DIM)
        draw.text((122, y + 17), question, font=f_body, fill=INK)
        colour = OK if mark == "○" else NG
        draw.text((616, y + 15), mark, font=f_mark, fill=colour)
        draw.text((660, y + 21), note, font=f_note, fill=MID)
        y += row_h

    draw.line([44, y, width - 44, y], fill=WIRE)
    draw.text((46, y + 18),
              "訂正はどちらも「自分の組み方では正しいが、一般化すると間違い」だった。",
              font=f_note, fill=DIM)

    path = os.path.join(OUT, "030_audit.png")
    image.save(path)
    print(path)


if __name__ == "__main__":
    main()
