# -*- coding: utf-8 -*-
"""実験166 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "166_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, conv, G = d["rows"], d["convergence"], d["g"]
    for c in conv:
        c["gap"] = (1 - c["vy_2s"] / c["sqrt_g_over_k"]) * 100
    line_chart(os.path.join(OUT, "166_drag.png"),
               [{"label": f"Air Resistance {k:g}", "points": [(math.log2(c["substeps"]), c["gap"]) for c in conv if c["k"] == k], "color": PALETTE[i]}
                for i, k in enumerate((1.0, 4.0))],
               title="popdrag: 2 秒後の落下の速さが √(g/k) に足りない割合（横は log2 Substeps）",
               x_label="log2（Substeps）", y_label="√(g/k) に足りない %")
    f97 = {(r["k"], r["substeps"]): r for r in rows if r["frame"] == 97}
    k1 = f97[(1.0, 1)]
    payload = {
        "title": "popdrag の終端速度は g/k ではなく √(g/k) に近づく — 速さの2乗に比例する抵抗と同じ振る舞い",
        "summary":
            "実験165 と同じ 1 粒を重力で落とし、popsolver の力の入力に popdrag（Wind Velocity 0、Ignore Mass 入）をつないだ。"
            "Air Resistance k を変えて、何秒たっても変わらなくなった落下の速さ（終端速度）を読んだ。\n\n"
            f"**終端速度は g/k にならなかった。**k = 1 なら、速さに比例する抵抗の式では 9.80665 になるはずが、4 秒後で {k1['vy']:.4f}。"
            "k = 0.5・1・2・5 のどれでも、g/k よりずっと遅いところで頭打ちになった（1 秒前後でもう止まる）。\n\n"
            "**Substeps を増やすと、√(g/k) に近づいた。**k = 1 では √9.80665 = 3.1316 へ、k = 4 では 1.5658 へ。"
            "足りない割合は Substeps 1 → 4 → 16 → 64 で "
            + "、".join(f"k = {k:g} で " + " → ".join(f"{c['gap']:.2f}%" for c in conv if c["k"] == k) for k in (1.0, 4.0))
            + "（Substeps を4倍にすると約1/4）。2つの k の両方で √(g/k) に向かうので、速さの2乗に比例する抵抗と同じ終端速度になっている。"
            "中の計算式そのものは確かめていない。\n\n"
            "**時間は 97 フレームで 0.4〜0.6 秒。**",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Substeps を増やしたときの 2 秒後の速さ",
             "images": [{"path": "166_drag.png", "caption": "どちらの k も、Substeps を4倍にするたびに足りない分が約1/4になる。"}],
             "per_row": 1,
             "columns": ["Air Resistance k", "Substeps", "2 秒後の v.y", "−√(g/k)", "足りない割合", "−g/k（比例の抵抗なら）"],
             "rows": [[f"{c['k']:g}", c["substeps"], f"{c['vy_2s']:.5f}", f"{c['sqrt_g_over_k']:.5f}", f"{c['gap']:.2f}%", f"{c['g_over_k']:.4f}"] for c in conv]},
            {"label": "k・Substeps と、1・2・4 秒後の速さ",
             "columns": ["k", "Substeps", "経った秒", "v.y", "−g/k", "比例の抵抗の式", "97 フレームの秒"],
             "rows": [[f"{r['k']:g}", r["substeps"], f"{r['t']:g}", f"{r['vy']:.4f}", f"{r['terminal']:.4f}", f"{r['exact_linear']:.4f}",
                       f"{r['sec_97f']:.3f}"] for r in rows]},
        ],
        "notes": [
            "<strong>popdrag の終端速度は √(g/k)。</strong>k を4倍にしても、落ちる速さは半分にしかならない。",
            "<strong>Substeps が少ないと、終端速度はさらに遅い。</strong>Substeps 1 で 6% ほど遅い（k = 1）。",
            "<strong>Air Resistance は「速さに比例する係数」ではない。</strong>欲しい終端速度 v から k = g/v² で逆算できる（Substeps を十分とったとき）。",
        ],
        "next": ["Wind Velocity を入れたときに、風の速さへ近づく速さ", "Ignore Mass を切り、mass を変えたとき"],
    }
    with open(os.path.join(OUT, "166_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 166_report.json")


if __name__ == "__main__":
    main()
