# -*- coding: utf-8 -*-
"""実験140 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, _font  # noqa: E402

LABEL = {"none": "何も付けない", "N": "N = (1,0,0)", "N_up": "N と up = (0,0,1)",
         "orient_and_N": "orient（x軸90°）と N", "orient_only": "orient（x軸90°）だけ",
         "pscale": "pscale = 2", "scale_pscale": "scale = (1,2,3) と pscale 2"}


def fmt(v):
    return "(" + ", ".join(f"{x:g}" for x in v) + ")"


def main():
    with open(os.path.join(OUT, "140_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    img = Image.new("RGB", (1000, 470), (255, 255, 255))
    d = ImageDraw.Draw(img)
    font, small = _font(24), _font(18)
    d.text((24, 14), "コピーされた矢の向き（z 軸 = 青、y 軸 = 橙。横から見た x–y と、上から見た x–z）", fill=(30, 30, 30), font=small)
    for i, r in enumerate(rows):
        cx, cy = 80 + i * 138, 200
        label = LABEL[r["case"]]
        d.text((cx - 60, 50), label[:10], fill=(40, 40, 46), font=_font(13))
        d.text((cx - 60, 68), label[10:22], fill=(40, 40, 46), font=_font(13))
        for vec, col in ((r["z_axis_to"], PALETTE[0]), (r["y_axis_to"], PALETTE[1])):
            s = 16
            d.line([cx, cy, cx + vec[0] * s, cy - vec[1] * s], fill=col, width=4)
            d.line([cx, cy + 150, cx + vec[0] * s, cy + 150 + vec[2] * s], fill=col, width=4)
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(60, 60, 60))
        d.ellipse([cx - 4, cy + 146, cx + 4, cy + 154], fill=(60, 60, 60))
    d.text((24, 110), "x–y", fill=(120, 120, 128), font=small)
    d.text((24, 300), "x–z", fill=(120, 120, 128), font=small)
    img.save(os.path.join(OUT, "140_copy.png"))
    print("140_copy.png")

    r = {x["case"]: x for x in rows}
    payload = {
        "title": "copytopoints の向きは orient が N に勝つ — N は +z を、up は +y を合わせる。scale と pscale は掛け算",
        "summary":
            "+z 方向の矢（原点・(0,0,1)・(0,1,0) の3点）を、属性を変えた点1つにコピーして、"
            "矢の z 軸と y 軸がどこを向いたか・どれだけ伸びたかを調べた。\n\n"
            f"**N だけなら、元の +z が N の向きになる**（N = (1,0,0) で z 軸 → {fmt(r['N']['z_axis_to'])}）。"
            f"y 軸は {fmt(r['N']['y_axis_to'])} のまま。\n\n"
            f"**up を足すと、元の +y が up の向きになる**（up = (0,0,1) で y 軸 → {fmt(r['N_up']['y_axis_to'])}）。"
            "N だけでは決まらない「ひねり」を up で決める。\n\n"
            "**orient があると、N より orient が勝つ。** N = (1,0,0) と、x 軸まわり 90° の orient を両方付けると、"
            f"z 軸は {fmt(r['orient_and_N']['z_axis_to'])}（orient だけのときと同じ）。N の向き (1,0,0) は無視された。\n\n"
            f"**pscale は全体の倍率、scale は軸ごとの倍率で、両方あれば掛け算。** pscale 2 で矢の長さ "
            f"{r['pscale']['z_len']:g}、scale (1,2,3) と pscale 2 で z 軸 {r['scale_pscale']['z_len']:g}・y 軸 "
            f"{r['scale_pscale']['y_len']:g}（= 3×2、2×2）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "点の属性と、コピーの向き・大きさ",
             "note": "矢の z 軸 = 原点から (0,0,1) だった点へのベクトル。y 軸 = (0,1,0) だった点へのベクトル。",
             "images": [{"path": "140_copy.png",
                         "caption": "N は z 軸を、up は y 軸を動かす。orient があれば N は効かない。"}],
             "per_row": 1,
             "columns": ["点の属性", "z 軸の行き先", "y 軸の行き先", "z の長さ", "y の長さ"],
             "rows": [[LABEL[x["case"]], fmt(x["z_axis_to"]), fmt(x["y_axis_to"]),
                       f"{x['z_len']:g}", f"{x['y_len']:g}"] for x in rows]},
        ],
        "notes": [
            "<strong>N は +z、up は +y を合わせる。</strong>コピーする形は、+z を「前」にして作っておく。",
            "<strong>orient があれば N と up は使われない。</strong>向きがおかしいときは、上流で orient が残っていないかを見る。",
            "<strong>pscale × scale。</strong>全体の大きさと、軸ごとの伸びを別々に付けられる。",
        ],
        "next": ["rot 属性や transform（行列）属性があるときの優先順位", "v（速度）だけがあるとき、向きに使われるか"],
    }
    with open(os.path.join(OUT, "140_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 140_report.json")


if __name__ == "__main__":
    main()
