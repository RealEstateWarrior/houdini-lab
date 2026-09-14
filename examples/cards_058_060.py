"""実験058・059・060 のサムネイル用の図を作る。

この3回は「何かを描いた」回ではなく「調べた」回なので、
レンダした画が1枚も無い。カード一覧でそこだけ穴が空いていた。
表の中身をそのまま1枚の図にする。数字はすべて記事から引いたもの。

    python examples/cards_058_060.py
"""

import os

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

# 幅 1120・4:3 の板に収まるよう、行の高さを決めてから全体を組む
WIDTH = 1120


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def card(name, title, lede, columns, rows, footer):
    """見出し＋表＋一言の図を1枚作る。"""
    head, row_h, foot = 118, 58, 56
    height = head + row_h * (len(rows) + 1) + foot
    image = Image.new("RGB", (WIDTH, height), GROUND)
    draw = ImageDraw.Draw(image)

    f_title = font(FONT_UI, 34)
    f_sub = font(FONT_UI, 19)
    f_head = font(FONT_UI, 17)
    f_body = font(FONT_UI, 21)
    f_note = font(FONT_UI, 17)

    draw.text((44, 32), title, font=f_title, fill=INK)
    draw.text((46, 76), lede, font=f_sub, fill=DIM)

    xs = [44 + x for x in columns[1]]
    y = head
    draw.rectangle([44, y, WIDTH - 44, y + row_h - 18], fill=PLATE)
    for label, x in zip(columns[0], xs):
        draw.text((x, y + 6), label, font=f_head, fill=DIM)
    y += row_h - 18
    draw.line([44, y, WIDTH - 44, y], fill=(210, 210, 215))

    for index, cells in enumerate(rows):
        if index % 2 == 1:
            draw.rectangle([44, y, WIDTH - 44, y + row_h], fill=PLATE)
        draw.line([44, y, WIDTH - 44, y], fill=WIRE)
        for cell, x in zip(cells, xs):
            text, kind = (cell if isinstance(cell, tuple) else (cell, ""))
            colour = {"ok": OK, "ng": NG, "dim": DIM}.get(kind, INK)
            draw.text((x, y + 17), text, font=f_body, fill=colour)
        y += row_h

    draw.line([44, y, WIDTH - 44, y], fill=WIRE)
    draw.text((46, y + 18), footer, font=f_note, fill=DIM)

    path = os.path.join(OUT, name)
    image.save(path)
    print(f"{path}  {image.size[0]}x{image.size[1]}")


def main():
    card(
        "058_formats.png",
        "実験058 — Apprentice で外へ出せる形式",
        "9通り試して、通ったのは5通り。止まったものはすべて明確に断られる。",
        (["形式", "やり方", "結果", "バイト"], [18, 240, 430, 640]),
        [
            ["bgeo.sc", "直接保存", ("通った", "ok"), "6,231"],
            ["geo", "直接保存", ("通った", "ok"), "46,506"],
            ["obj", "直接保存", ("通った", "ok"), "20,568"],
            ["ply", "直接保存", ("通った", "ok"), "50,448"],
            ["stl", "直接保存", ("通った", "ok"), "207,899"],
            ["fbx", "ROP", ("止まった", "ng"), ("0", "dim")],
            ["gltf", "ROP", ("止まった", "ng"), ("0", "dim")],
            ["abc", "ROP", ("止まった", "ng"), ("0", "dim")],
            ["usd", "LOP", ("拡張子が変わる", "ng"), (".usdnc", "dim")],
        ],
        "Unreal へ渡すにはライセンスを上げるしかない。工夫では回避できない。",
    )

    card(
        "059_obj.png",
        "実験059 — obj で渡せる範囲",
        "位置のずれは 0。ただし自作のアトリビュートとグループは全部落ちる。",
        (["置き場所", "書き出す前", "読み直した後"], [18, 300, 660]),
        [
            ["点", "Cd, P, myfloat, myint,",
             ("Cd, N, P", "ng")],
            ["", "mystring, myvec, pscale", ""],
            ["バーテックス", "N, uv", ("uv", "ng")],
            ["点のグループ", "firstten", ("（なし）", "ng")],
            ["NURBS の球", "312点 / 1面", ("2,232点 / 2,160面", "ng")],
        ],
        "色と UV は残る。NURBS は 2,160面に刻まれ、点が 7.2倍になる。",
    )

    card(
        "060_audit.png",
        "実験060 — 031〜059 を測り直す",
        "6件すべて一致。1件は「もっと強い結論」に変わった。",
        (["実験", "確かめたこと", "結果"], [18, 130, 800]),
        [
            ["042", "球（40×40）の表面積 12.53039", ("一致", "ok")],
            ["042", "density は面積1あたりの本数", ("一致", "ok")],
            ["045", "width は直径（比 ≒ 1.0）", ("一致", "ok")],
            ["052", "体積の減り = 27.1284 × (1 − cos θ)", ("形によらない", "ok")],
            ["056", "届く距離 = 骨の長さの合計", ("一致", "ok")],
            ["057", "ノード数＝点数、配線数＝面数", ("枝分かれでも成立", "ok")],
        ],
        "052 の係数 27.1284 は、形の大きさによらない定数だと分かった。",
    )


if __name__ == "__main__":
    main()
