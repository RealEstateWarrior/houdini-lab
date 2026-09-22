# -*- coding: utf-8 -*-
"""実験155 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "155_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, free = d["rows"], d["free"]
    for r in rows:
        r["sd_ratio"] = r["sd_count"] / r["binom_sd"]
    line_chart(os.path.join(OUT, "155_share.png"),
               [{"label": f"N = {N:,}（20 通りの平均）", "points": [(r["k"], r["mean"]) for r in rows if r["N"] == N], "color": PALETTE[i]}
                for i, N in enumerate((1000, 10000))]
               + [{"label": "k/(1+k)", "points": [(k, k / (1 + k)) for k in (1.0, 3.0, 9.0)], "color": PALETTE[4], "dash": True}],
               title="scatter: 右の面の density = k、左 = 1 のときの、右に落ちた点の割合",
               x_label="k（右の density）", y_label="右の点の割合")
    worst = max(abs(r["mean"] - r["want"]) for r in rows)
    lo, hi = min(r["sd_ratio"] for r in rows), max(r["sd_ratio"] for r in rows)
    payload = {
        "title": "scatter の density 属性は点を k/(1+k) に分ける — 数を決めないと Density Scale × 面積のあたりで揺れる",
        "summary":
            "2×1 の板を左右2枚の面に分け、右の面の density を k、左を 1 にして、Force Total Count = N で撒いた。"
            "Global Seed を 20 通り変え、右に落ちた点の割合を数えた（Relax は切った）。\n\n"
            f"**割合は k/(1+k) に合った。**6通りで、20 通りの平均と式の差は最大 {worst:.4f}。"
            "density は「面積あたりの濃さ」として、面ごとに点を配っている。\n\n"
            f"**ばらつきは、二項分布の幅と同じか少し小さい。**点の数の標準偏差 ÷ √(N·p·(1−p)) は {lo:.2f}〜{hi:.2f}。"
            "完全にでたらめに配るより、少しだけ揃う傾向がある（ばらつきの推定は 20 通りなので、±16% ほどの幅がある）。\n\n"
            "**Force Total Count を切ると、数はおよそ Density Scale × 面積。**ぴったりではない: "
            + "、".join(f"Density Scale {x['densityscale']:g} で {x['points']:,}（{x['want']:g}）" for x in free) + "。"
            "決まった数が要るなら Force Total Count を入れる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "density の比と、右に落ちた割合（Force Total Count 入り）",
             "images": [{"path": "155_share.png", "caption": "点線 k/(1+k) に、N = 1,000 も 10,000 も乗る。"}],
             "per_row": 1,
             "columns": ["k", "N", "k/(1+k)", "平均", "最小〜最大", "点の数の標準偏差", "二項分布の幅", "比", "1回の秒"],
             "rows": [[f"{r['k']:g}", f"{r['N']:,}", f"{r['want']:.4f}", f"{r['mean']:.4f}", f"{r['min']:.4f}〜{r['max']:.4f}",
                       f"{r['sd_count']:.1f}", f"{r['binom_sd']:.1f}", f"{r['sd_ratio']:.2f}", f"{r['sec']:.4f}"] for r in rows]},
            {"label": "Force Total Count を切ったとき（面積 2、Seed 0）",
             "columns": ["Density Scale", "点の数", "Density Scale × 面積"],
             "rows": [[f"{x['densityscale']:g}", f"{x['points']:,}", f"{x['want']:g}"] for x in free]},
        ],
        "notes": [
            "<strong>density は比で効く。</strong>右を 3 倍にすれば、右に 3/4。",
            "<strong>点の数を決めたいなら Force Total Count。</strong>切ると Density Scale × 面積のあたりで毎回揺れる。",
            "<strong>Seed を変えたときの揺れは √(N·p·(1−p)) くらい。</strong>N = 10,000・半々なら ±50 点ほど。",
        ],
        "next": ["Relax を入れたときに割合が変わるか", "density を点の属性（頂点ごと）で与えたときの分け方"],
    }
    with open(os.path.join(OUT, "155_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 155_report.json", worst, lo, hi)


if __name__ == "__main__":
    main()
