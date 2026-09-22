# -*- coding: utf-8 -*-
"""実験149 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def lines_inside(s, off):
    """-0.5〜0.5 の内側にある、左端 −0.5 + off + k·s の線の数。"""
    return sum(1 for k in range(-40, 40) if -0.5 + 1e-9 < -0.5 + off + k * s < 0.5 - 1e-9)


def main():
    with open(os.path.join(OUT, "149_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    bricks, convex = d["rows"], d["convex"]
    for b in bricks:
        b["want"] = (lines_inside(b["size"], b["offset"]) + 1) ** 2
    for c in convex:
        c["want"] = c["n"] - 2 if c["max_edges"] == 3 else math.ceil((c["n"] - 2) / 2)
    line_chart(os.path.join(OUT, "149_convex.png"),
               [{"label": f"Maximum Edges = {k}", "points": [(c["n"], c["prims"]) for c in convex if c["max_edges"] == k],
                 "color": PALETTE[i]} for i, k in enumerate((3, 4))],
               title="divide（Convex Polygons）: 正 n 角形を割った枚数", x_label="n（角の数）", y_label="枚数")
    ok_b = all(b["prims"] == b["want"] for b in bricks)
    ok_c = all(c["prims"] == c["want"] for c in convex)
    payload = {
        "title": "divide の Bricker は形の端（＋ Offset）から Size おきに線を引く — Convex は n 角形を n−2 枚の三角形か、その半分の四角形に",
        "summary":
            "1×1 の正方形1枚（中心が原点）を Bricker Polygons で、正 n 角形を Convex Polygons で割り、枚数を数えた。\n\n"
            "**Bricker は、形の囲む箱の端（＋ Offset）から Size おきに切る線を引く。**"
            "枚数は「正方形の内側を通る線の数 + 1」の2乗で、8通り"
            f"{'すべて一致' if ok_b else 'で一致しないものがあった'}。"
            "Size 0.3 だと線は −0.2・0.1・0.4 の3本で 16 枚（右端の升だけ 0.1 幅）。Offset 0.05 だと −0.45・−0.15・0.15・0.45 の4本で 25 枚。"
            "Size 0.5 は線が 0 の1本だけで 4 枚、Offset 0.05 だと −0.45・0.05 の2本で 9 枚。\n\n"
            "**Convex で Maximum Edges = 3 なら n − 2 枚の三角形、4 なら (n − 2)/2 枚（切り上げ）。**"
            f"8通り{'すべてこの数' if ok_c else 'で違うものがあった'}。"
            "奇数角形を 4 で割ると、三角形が1枚だけ混ざる（13角形で三角形1＋四角形5）。\n\n"
            "**どちらも面積は変わらない。**割る前と後で6桁一致した。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Bricker: Size・Offset と枚数（1×1 の正方形）",
             "note": "Offset は x・y・z に同じ値。線は −0.5 + Offset + k·Size。予測 = (内側を通る線の数 + 1)²。",
             "columns": ["Size", "Offset", "面", "予測", "点", "何角形か", "面積", "秒"],
             "rows": [[f"{b['size']:g}", f"{b['offset']:g}", b["prims"], b["want"], b["points"],
                       "・".join(map(str, b["sides"])), f"{b['area']:g}", f"{b['sec']:.4f}"] for b in bricks]},
            {"label": "Convex: 正 n 角形を割る",
             "images": [{"path": "149_convex.png", "caption": "3 で割ると n − 2 枚、4 で割るとその約半分。"}],
             "per_row": 1,
             "columns": ["n", "Maximum Edges", "面", "予測", "面ごとの角の数", "面積", "割る前"],
             "rows": [[c["n"], c["max_edges"], c["prims"], c["want"], "・".join(map(str, c["sides"])),
                       f"{c['area']:.6f}", f"{c['area0']:.6f}"] for c in convex]},
        ],
        "notes": [
            "<strong>Bricker の升目は形の端から並ぶ。</strong>Offset はその始まりをずらす量（Offset 0 でも端に線は増えない）。",
            "<strong>割り切れない Size だと、反対側の端に細い升が残る。</strong>1 ÷ 0.3 なら 0.1 幅の列。",
            "<strong>Maximum Edges = 4 は、奇数角形だと三角形が1枚混ざる。</strong>全部四角にはならない。",
        ],
        "next": ["Bricker を立体（box）にかけたときの枚数", "Compute Dual で出る面の数"],
    }
    with open(os.path.join(OUT, "149_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 149_report.json", ok_b, ok_c)


if __name__ == "__main__":
    main()
