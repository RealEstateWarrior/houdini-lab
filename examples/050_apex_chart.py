"""実験050 の図 — APEX の部品を名前空間ごとに数えた棒グラフ。

Houdini は要らない。out/050_stats.json を読んで描くだけ。

    python examples/050_apex_chart.py
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")

W, H = 860, 456
BG = (245, 245, 247)
INK = (29, 29, 31)
DIM = (134, 134, 139)
BAR = (0, 102, 204)
BAR2 = (154, 75, 0)


def font(size, bold=False):
    for name in (("meiryob.ttc" if bold else "meiryo.ttc"),
                 "YuGothB.ttc" if bold else "YuGothR.ttc", "msgothic.ttc"):
        path = os.path.join(os.environ.get("WINDIR", "C:/Windows"),
                            "Fonts", name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main():
    with open(os.path.join(OUT, "050_stats.json"), encoding="utf-8") as fp:
        stats = json.load(fp)
    rows = stats["groups"]
    plain = stats["plain_parts"]
    total = stats["total_parts"]

    items = [("（名前空間なし）", plain)] + [(r["group"], r["count"])
                                            for r in rows]
    biggest = max(v for _, v in items)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = font(22, True)
    f_label = font(14)
    f_num = font(13)
    f_note = font(12)

    d.text((28, 22), "APEX の部品 2,220種を、名前空間ごとに数える",
           font=f_title, fill=INK)
    d.text((28, 54),
           f"apex.Registry().findMatchingNames('*') で得た {total:,}件の内訳"
           "（上位12と、名前空間の付いていないもの）",
           font=f_note, fill=DIM)

    top = 86
    row_h = 25
    left = 190
    right = W - 90
    for i, (name, value) in enumerate(items):
        y = top + i * row_h
        d.text((left - 10 - d.textlength(name, font=f_label), y + 3),
               name, font=f_label, fill=INK)
        width = int((right - left) * value / biggest)
        color = BAR2 if name == "（名前空間なし）" else BAR
        d.rectangle([left, y + 2, left + max(width, 2), y + row_h - 8],
                    fill=color)
        d.text((left + max(width, 2) + 8, y + 3), f"{value:,}",
               font=f_num, fill=DIM)

    d.text((28, H - 30),
           "geo と sop で 715種。APEX の中から SOP の処理をそのまま呼べる。",
           font=f_note, fill=DIM)

    path = os.path.join(OUT, "050_parts.png")
    img.save(path)
    print("保存:", path)


if __name__ == "__main__":
    sys.exit(main())
