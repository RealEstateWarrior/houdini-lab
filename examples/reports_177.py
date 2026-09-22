# -*- coding: utf-8 -*-
"""実験177 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "177_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "177_cost.png"),
               [{"label": f"Substeps {s}（点は Iterations 25・100・400・1600）",
                 "points": [(r["sec_49f"], math.log10(max(r["max_stretch"] - 1, 1e-6) * 100)) for r in rows if r["substeps"] == s],
                 "color": PALETTE[i]} for i, s in enumerate((1, 5))],
               title="Vellum の布（2 秒）: かかった時間と、いちばん伸びた辺の伸び（縦は log10 %）",
               x_label="49 フレームの秒", y_label="log10（伸び %）")
    by = {(r["iterations"], r["substeps"]): r for r in rows}
    a, b, c = by[(400, 1)], by[(100, 5)], by[(1600, 1)]
    payload = {
        "title": "Vellum の布の伸びは、Substeps より Constraint Iterations を上げる方が安く減る — 400 回で 0.2%、1600 回で 0.002%",
        "summary":
            "実験170 の続き。上の辺を留めた 1 × 1 の布（21 × 21 点、Stretch Stiffness は既定の 10^10）を 2 秒ぶら下げ、vellumsolver の Constraint Iterations"
            "（既定 100）と Substeps を変えて、いちばん伸びた辺の伸びと時間を測った。\n\n"
            "**Iterations を増やすほど、伸びは速く減った。**Substeps 1 で、25・100・400・1600 回のとき "
            + "・".join(f"{(by[(it, 1)]['max_stretch'] - 1) * 100:.3g}%" for it in (25, 100, 400, 1600))
            + "。4 倍にするたびに、伸びは 1/4 より大きく減っている。\n\n"
            f"**同じ時間なら、Iterations の方が伸びが小さい。**Iterations 400・Substeps 1 は {a['sec_49f']:.1f} 秒で {(a['max_stretch'] - 1) * 100:.2f}%。"
            f"既定の Iterations 100 で Substeps 5 にすると {b['sec_49f']:.1f} 秒で {(b['max_stretch'] - 1) * 100:.2f}%。"
            f"Iterations 1600・Substeps 1 は {c['sec_49f']:.1f} 秒で {(c['max_stretch'] - 1) * 100:.3f}%（ほぼ伸びない）。\n\n"
            "**Substeps は、動きの速い物（ぶつかる・跳ねる）のためにとっておく。**伸びを抑えるだけなら Iterations で足りる。"
            "（この布はゆっくりぶら下がるだけ。速く動く布では、確かめていない。）\n\n"
            f"**Iterations を 4 倍にしても、時間は 1.5〜2.8 倍**（決まった手間があるため。Substeps 5・1600 回で {by[(1600, 5)]['sec_49f']:.1f} 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Iterations・Substeps と、伸び・時間",
            "images": [{"path": "177_cost.png", "caption": "青（Substeps 1）の方が、同じ秒数で下（伸びが小さい）に来る。"}],
            "per_row": 1,
            "columns": ["Constraint Iterations", "Substeps", "いちばん伸びた辺", "辺の平均", "下の辺の下がり", "49 フレームの秒"],
            "rows": [[r["iterations"], r["substeps"], f"{(r['max_stretch'] - 1) * 100:.3f}%", f"{(r['mean_stretch'] - 1) * 100:.3f}%",
                      f"{r['sag']:.5f}", f"{r['sec_49f']:.2f}"] for r in rows]}],
        "notes": [
            "<strong>布が伸びるなら、まず Constraint Iterations を上げる。</strong>400 回で 0.2%、時間は 1.5 倍。",
            "<strong>Substeps 5 は同じくらいの伸びで時間が約 2.7 倍。</strong>",
            "<strong>既定（100 回・Substeps 1）では 2.3% 伸びる。</strong>ぶら下がる布では見て分かる差。",
        ],
        "next": ["速く動く布（風であおる）で Iterations と Substeps を比べる", "点の数を増やしたときに必要な Iterations"],
    }
    with open(os.path.join(OUT, "177_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 177_report.json", round(a["sec_49f"] / by[(100, 1)]["sec_49f"], 2), round(b["sec_49f"] / by[(100, 1)]["sec_49f"], 2))


if __name__ == "__main__":
    main()
