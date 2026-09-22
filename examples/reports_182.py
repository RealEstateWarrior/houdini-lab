# -*- coding: utf-8 -*-
"""実験182 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "182_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, multi = d["rows"], d["multi"]
    line_chart(os.path.join(OUT, "182_kernel.png"),
               [{"label": "w(d) ÷ w(0.5)（log10）", "points": [(r["d"], math.log10(r["weight_ratio"])) for r in rows], "color": PALETTE[0]}],
               title="pcfilter: 距離 0.5 の点に対する、距離 d の点の重み（半径 1、点は2つだけ）",
               x_label="中心からの距離 d", y_label="log10（重みの比）")
    near, far = rows[0], rows[-1]
    best = {}
    for m in multi:
        for k, v in m["pred"].items():
            best.setdefault(k, []).append(abs(v - m["a"]))
    ranking = sorted(((max(v), k) for k, v in best.items()))
    payload = {
        "title": "pcfilter の重みは「半径に対する距離」だけでは決まらない — 見つかった点どうしの並びで変わり、式は分からなかった",
        "summary":
            "pcopen（半径 1）→ pcfilter で、点の重みが距離とともにどう下がるかを調べた。中心から 0.5 の所に val = 0 の点、距離 d に val = 1 の点を置き、"
            "結果 a から重みの比 w(d)/w(0.5) = a/(1 − a) を出した。\n\n"
            f"**近い点ほど重いが、形は単純な式にならない。**d = 0.05 で {near['weight_ratio']:.1f} 倍、d = 0.95 でも {far['weight_ratio']:.3f} 倍"
            "（半径の端でも 0 にならない）。d = 0.5 をはさんで急に変わり、両端では平らになる。\n\n"
            "**3〜4 点で候補の式と比べても、ぴったり合うものは無かった。**d を「いちばん遠く見つかった点の距離」で割った 1 − t が"
            f"いちばん近かったが、それでも最大 {ranking[0][0]:.3f} ずれた（{ranking[0][1]}）。次が半径で割った (1 − t²)² で、最大 {ranking[1][0]:.3f}。"
            "重みは、見つかった点の並び（いちばん遠い点など）で決まっているとみられるが、確かめていない。\n\n"
            "**中心ぴったりの点は特別に重い。**最初に val = 0 の点を中心（d = 0）に置くと、B をどこに置いても結果が同じ 0.0228 になり、形が読めなかった。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "2点での重みの比",
             "images": [{"path": "182_kernel.png", "caption": "d = 0.5 の前後で急に下がり、両端では平ら。"}],
             "per_row": 1,
             "columns": ["d", "pcfilter の結果 a", "w(d) ÷ w(0.5)"],
             "rows": [[f"{r['d']:g}", f"{r['a']:.6f}", f"{r['weight_ratio']:.4f}"] for r in rows]},
            {"label": "3〜4 点で、候補の重みの式と比べる",
             "columns": ["点（距離, val）", "pcfilter の結果"] + [k for _, k in ranking[:4]],
             "rows": [[" / ".join(f"({p[0]:g}, {p[1]:g})" for p in m["points"]), f"{m['a']:.4f}"] + [f"{m['pred'][k]:.4f}" for _, k in ranking[:4]]
                      for m in multi]},
        ],
        "notes": [
            "<strong>pcfilter は「近いほど重い平均」だが、重みの形は点の並びしだい。</strong>決まった重みで混ぜたいなら、pcfind で番号を取り、自分で重みを掛けて足す。",
            "<strong>中心ぴったりに点があると、その点の値にほぼなる。</strong>自分の点を含めて探すときは注意。",
            "<strong>ただの平均が欲しいなら pcfilter は使わない</strong>（実験181）。",
        ],
        "next": ["pcfilter の重みを、点を増やして形から推定する", "pcfarthest（いちばん遠い点の距離）との関係"],
    }
    with open(os.path.join(OUT, "182_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 182_report.json", ranking[:3])


if __name__ == "__main__":
    main()
