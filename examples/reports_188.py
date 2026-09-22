# -*- coding: utf-8 -*-
"""実験188 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "188_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    free = [r for r in rows if r["force"] == 0]
    for r in free:
        r["ratio"] = r["per_area"] / r["density"]
        r["poisson"] = 1 / math.sqrt(r["density"] * r["area"])
    skins = ["grid 1×1", "grid 2×2", "球 半径1"]
    line_chart(os.path.join(OUT, "188_density.png"),
               [{"label": s, "points": [(math.log10(r["density"]), r["ratio"]) for r in free if r["skin"] == s], "color": PALETTE[i]}
                for i, s in enumerate(skins)]
               + [{"label": "Density どおり", "points": [(2, 1), (math.log10(5000), 1)], "color": PALETTE[4], "dash": True}],
               title="hairgen: 面積あたりの毛の本数 ÷ Density（横は log10 Density）",
               x_label="log10（Density）", y_label="本数 ÷ 面積 ÷ Density")
    forced = [r for r in rows if r["force"] == 1]
    ok_force = all(r["curves"] == 2500 for r in forced)
    big = [r for r in free if r["density"] == 5000.0]
    payload = {
        "title": "hairgen の毛の本数は Density × 面積 — 1本は Segments + 1 点、長さは Length ちょうど",
        "summary":
            "grid（面積 1・4）と球（半径 1）を皮にして、hairgen（ガイドなし）を Density 100・1000・5000 で生やし、毛（線）の本数・点の数・長さを数えた。\n\n"
            "**本数 ÷ 面積 は Density に合う。**Density 5000 では "
            + "・".join(f"{r['skin']} で {r['per_area']:g}" for r in big)
            + "。本数が少ないほどずれが大きく（Density 100・面積 1 で 118 本、+18%）、でたらめに撒いたときの揺れ（1/√本数、ここでは ±10%）くらいの大きさ。\n\n"
            f"**Force Count を入れると、面積によらず指定の本数ちょうど**（{'3通りとも 2,500 本' if ok_force else '合わないものがあった'}）。面積あたりの密度は、面の広さで変わる。\n\n"
            "**1本の毛は 9 点（既定の Segments 8 + 1）、長さは既定の Length 0.05 ちょうど。**grid ではどの毛も 0.05000、"
            "球では 0.04998 前後（ばらつき 0.00005 未満）。\n\n"
            f"**速い。**球に 62,456 本でも {big[-1]['sec']:.3f} 秒。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "皮・Density と毛",
            "images": [{"path": "188_density.png", "caption": "本数が多いほど 1 に近づく。"}],
            "per_row": 1,
            "columns": ["皮", "面積", "Density", "Force Count", "毛の本数", "面積あたり", "1本の点", "長さの平均", "長さの差", "秒"],
            "rows": [[r["skin"], f"{r['area']:g}", f"{r['density']:g}", "入" if r["force"] else "切", f"{r['curves']:,}", f"{r['per_area']:g}",
                      "・".join(map(str, r["pts_per_curve"])), f"{r['length_mean']:.5f}", f"{r['length_spread']:.5f}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>毛の本数は Density × 面積で見積もれる。</strong>面積 4 の板に Density 1000 なら約 4,000 本。",
            "<strong>皮を大きくしても毛の密度を保つなら Density、本数を決めたいなら Force Count。</strong>",
            "<strong>1本の点の数は Segments + 1。</strong>点の総数は 本数 × 9 で、重さの見積もりに使える。",
        ],
        "next": ["ガイドを使ったとき（guide から生やす）の本数", "Density 属性で場所ごとに変えたときの本数"],
    }
    with open(os.path.join(OUT, "188_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 188_report.json", ok_force)


if __name__ == "__main__":
    main()
