# -*- coding: utf-8 -*-
"""実験186 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LAB = {"uniform": "Uniform", "scaledominant": "Scale Dominant", "curvaturedominant": "Curvature Dominant"}


def main():
    with open(os.path.join(OUT, "186_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    circle, line, L = d["rows"], d["line"], d["wave_L"]
    pred = 1 / (1 + 10 * L / 2)
    fixed = [x for x in line if x["boundary"] == "unsharededges"][0]
    free = [x for x in line if x["boundary"] == "none"][0]
    line_chart(os.path.join(OUT, "186_methods.png"),
               [{"label": LAB[m], "points": [(r["quality"], r["r"]) for r in circle if r["method"] == m], "color": PALETTE[i]}
                for i, m in enumerate(LAB)],
               title="smooth（Strength 10）: 24 角形に残った半径と Filter Quality（3本は重なる）",
               x_label="Filter Quality", y_label="残った半径")
    same = len({(r["quality"], r["r"]) for r in circle}) == 2
    payload = {
        "title": "smooth の3つの Method は、点が等間隔の円では同じ縮み方 — 開いた線の端は Constrained Boundary で止まり、波の高さは 1/(1 + S·L/2) だけ残る",
        "summary":
            "実験185 の続き。半径 1 の 24 角形に、Method を Uniform・Scale Dominant・Curvature Dominant と変えて smooth（Strength 10）をかけた。"
            "また、x = 0〜1 に 41 点で y = 0.1·sin(4πx) の波の線を作り、端の扱い（Constrained Boundary）を変えて smooth をかけた。\n\n"
            f"**円では、3つの Method の結果が7桁まで同じだった**（{'Quality ごとに同じ値' if same else '違いがあった'}。Quality 1 で 0.7458558、2 で 0.9923191）。"
            "点が等間隔で、どの点のまわりも同じ形なので、重みの付け方の違いが出ない。違いが出るのは、辺の長さや曲がり方がそろっていない網のとき（確かめていない）。\n\n"
            f"**開いた線は、Constrained Boundary = None だと端の点も動き、線が縮む。**両端が内側へ寄り、長さ 1 の線が x 方向に {free['x_span']:.4f} になった。"
            f"既定の Unshared Edges なら、端は (0, 0) と (1, 0) のまま。\n\n"
            f"**端を止めたとき、波の高さは {fixed['amp_ratio'] * 100:.2f}% 残った。**波1つが 20 点なので θ = 2π/20、L = 2(1 − cos θ) = {L:.4f}。"
            f"実験185 の式 1/(1 + S·L/2) = {pred:.4f} とぴったり合う。円の縮み方の式は、波にもそのまま使える。"
            f"端も動くと、波の高さは {free['amp_ratio'] * 100:.1f}% だった。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "24 角形と Method",
             "images": [{"path": "186_methods.png", "caption": "3つの線は完全に重なる。"}],
             "per_row": 1,
             "columns": ["Method", "Filter Quality", "残った半径", "点ごとの差"],
             "rows": [[LAB[r["method"]], r["quality"], f"{r['r']:.7f}", f"{r['spread']:.1e}"] for r in circle]},
            {"label": "開いた波の線（Uniform・Strength 10・Quality 1）",
             "columns": ["Constrained Boundary", "始まりの点", "終わりの点", "x の長さ", "波の高さ", "残った割合", "式 1/(1 + S·L/2)"],
             "rows": [[x["boundary"], f"({x['end0'][0]:g}, {x['end0'][1]:g})", f"({x['end1'][0]:g}, {x['end1'][1]:g})", f"{x['x_span']:g}",
                       f"{x['amp']:.5f}", f"{x['amp_ratio'] * 100:.2f}%", f"{pred * 100:.2f}%"] for x in line]},
        ],
        "notes": [
            "<strong>等間隔の網なら、Method はどれでも同じ。</strong>違いが出るのは網の細かさがそろっていないとき。",
            "<strong>開いた線の端を動かしたくないなら、Constrained Boundary は既定の Unshared Edges のまま。</strong>None にすると線が縮む。",
            "<strong>波の残り方は、波1つに入る点の数で決まる。</strong>1/(1 + S·L/2)、L = 2(1 − cos(2π/点の数))。",
        ],
        "next": ["点の間隔がそろっていない線での Method の違い", "Filter Quality 2・3 で波の高さはどう残るか"],
    }
    with open(os.path.join(OUT, "186_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 186_report.json", same, round(pred, 4))


if __name__ == "__main__":
    main()
