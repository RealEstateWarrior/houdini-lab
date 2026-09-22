# -*- coding: utf-8 -*-
"""実験147 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"twist": "Twist", "bend": "Bend", "shear": "Shear", "taper": "Taper",
         "ltaper": "Linear Taper", "squash": "Squash"}


def main():
    with open(os.path.join(OUT, "147_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows = d["rows"]
    one = [r for r in rows if r["length"] == 1.0]
    line_chart(os.path.join(OUT, "147_volume.png"),
               [{"label": LABEL[op], "points": [(r["strength"], r["ratio"]) for r in one if r["op"] == op],
                 "color": PALETTE[i % 5], "dash": i >= 5} for i, op in enumerate(LABEL)],
               title="twist SOP: 1×1×1 の箱の体積 ÷ 元の体積（Strength 0.5 と 1）",
               x_label="Strength", y_label="体積の比")
    g = {(r["op"], r["strength"], r["length"]): r for r in rows}
    tp = 2 ** 0.5 - 2 ** -0.5
    taper_want = tp / math.log(2)
    payload = {
        "title": "twist SOP の6つの操作 — 体積を保つのは Shear だけ。Squash は長さ (1+s) 倍・太さ 1/(1+s) 倍",
        "summary":
            "x が 0〜1（または 0〜2）の箱に、Primary Axis = X で6つの Operation をかけ、体積と端の点の動きを測った。\n\n"
            "**Shear はぴったり体積を保つ。**y が Strength × x だけずれ、囲む箱の高さは 1 + s × 長さ"
            f"（長さ 2・s = 1 で {g[('shear', 1.0, 2.0)]['bbox'][1]:g}）。\n\n"
            "**Twist の Strength は、x が 1 進むごとの回転角（度）。**x = 1 の角の点が s = 2 で 2° 回った。"
            f"体積は {g[('twist', 1.0, 1.0)]['ratio']:.6f} 倍と、わずかに増えた。側面の四角形がねじれて平らでなくなるため。\n\n"
            "**Squash は長さを (1 + s) 倍、太さを 1/(1 + s) 倍にする。**体積は 1/(1 + s) 倍"
            f"（s = 0.5 で {g[('squash', 0.5, 1.0)]['ratio']:.6f}、s = 1 で {g[('squash', 1.0, 1.0)]['ratio']:g}）。"
            "名前と違い、体積は保たれない。\n\n"
            "**Taper と Linear Taper は、Secondary Axis（Y）の位置で x 方向の長さを変える。Strength = 1 で変化なし。**"
            "Linear Taper は y = −0.5 で s 倍、+0.5 で 1/s 倍、その間は直線（s = 0.5 で 0.5〜2 倍、体積 "
            f"{g[('ltaper', 0.5, 1.0)]['ratio']:g} 倍）。Taper は s^(−y) 倍（y = +0.5 で 1.4142、−0.5 で 0.7071）。"
            f"ただし Taper の体積 {g[('taper', 0.5, 1.0)]['ratio']:.6f} 倍は、この倍率を y で平均した値 {taper_want:.6f} と "
            f"{(g[('taper', 0.5, 1.0)]['ratio'] / taper_want - 1) * 100:.2f}% 合わない。理由は確かめていない。\n\n"
            "**Bend の Strength の単位は確かめていない。**s = 2 で端の点が 0.05 ほど動くだけで、弧の角度として読めなかった。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "操作・Strength・体積",
             "images": [{"path": "147_volume.png", "caption": "Shear と Twist はほぼ 1。Squash は下がり、Taper 系は s = 1 で 1 に戻る。"}],
             "per_row": 1,
             "columns": ["長さ", "Operation", "Strength", "元の体積", "体積", "比", "囲む箱", "秒"],
             "rows": [[f"{r['length']:g}", LABEL[r["op"]], f"{r['strength']:g}", f"{r['v0']:g}", f"{r['volume']:.6f}",
                       f"{r['ratio']:.6f}", " × ".join(f"{v:g}" for v in r["bbox"]), f"{r['sec']:.4f}"] for r in rows]},
            {"label": "x = 1・z = 0.5 の端の点の行き先（長さ 1 の箱）",
             "columns": ["Operation", "Strength", "元の y", "行き先 (x, y, z)"],
             "rows": [[LABEL[p["op"]], f"{p['strength']:g}", f"{p['y']:g}", ", ".join(f"{v:g}" for v in p["to"])]
                      for p in d["profile"]]},
        ],
        "notes": [
            "<strong>体積を保ちたいなら Shear。</strong>Twist もほぼ保つ（ねじれた面の分だけずれる）。",
            "<strong>Squash は体積を保たない。</strong>伸ばして細くする量が、同じ (1+s) で釣り合っていない。",
            "<strong>Taper 系は Strength = 1 が「何もしない」。</strong>0 にすると片側がつぶれる。",
        ],
        "next": ["Taper の体積が平均と合わない理由", "Bend の Strength と曲がる角度の関係"],
    }
    with open(os.path.join(OUT, "147_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 147_report.json")


if __name__ == "__main__":
    main()
