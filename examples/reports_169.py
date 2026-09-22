# -*- coding: utf-8 -*-
"""実験169 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "169_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, base, cells = d["rows"], d["base_sum"], d["cells"]
    for r in rows:
        r["total"] = r["height_sum"] + r["sediment_sum"] + r["debris_sum"]
        r["mean_h"] = r["height_sum"] / cells
    line_chart(os.path.join(OUT, "169_mass.png"),
               [{"label": "height の合計", "points": [(r["frame"], r["height_sum"]) for r in rows], "color": PALETTE[0]},
                {"label": "height + sediment + debris", "points": [(r["frame"], r["total"]) for r in rows], "color": PALETTE[1]},
                {"label": "最初の height の合計", "points": [(r["frame"], base) for r in rows], "color": PALETTE[4], "dash": True}],
               title="heightfield_erode（125×125 の升）: 高さの合計と、積もった層を足した合計",
               x_label="フレーム", y_label="升の値の合計")
    r40 = rows[-1]
    peak = max(rows, key=lambda r: r["total"])
    payload = {
        "title": "heightfield_erode は土の量を保たない — 40 フレームで height の平均が 5 下がり、削れた分の大半は地形から消える",
        "summary":
            "1000 × 1000 の heightfield（125 × 125 の升）に heightfield_noise（Amplitude 500）で山を作り、heightfield_erode（既定。Freeze は切った）を"
            "フレーム 1 から 40 まで進めた。height と、erode が作る層（sediment・debris など）を升ごとに足し合わせた。\n\n"
            f"**height の合計は減り続けた。**最初は {base:,.0f}、フレーム 40 で {r40['height_sum']:,.0f}。升1つあたりの平均では "
            f"{base / cells:.2f} → {r40['mean_h']:.2f}（{r40['mean_h'] - base / cells:+.2f}）。最高点は {d['base_max']:g} → {r40['height_max']:g}、"
            f"最低点は {d['base_min']:g} → {r40['height_min']:g} と、山は低く、谷は浅くなった。\n\n"
            f"**削れた分を sediment と debris に足しても、元の量にならない。**3つを足した合計は、フレーム {peak['frame']} まではむしろ最初より多く"
            f"（{peak['total']:,.0f}）、そのあと減って、フレーム 40 で {r40['total']:,.0f}（最初の {r40['total'] / base * 100:.0f}%）。"
            "流れる水と一緒に端から出ていく、か、層の値が「量」ではなく「濃さ」を表している、かのどちらかとみられるが、確かめていない。\n\n"
            f"**速い。**125 × 125 の升で、40 フレームを {r40['elapsed']:.1f} 秒。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "フレームごとの合計",
            "images": [{"path": "169_mass.png", "caption": "青（height）は直線的に減り、橙（層を足したもの）も途中から下がる。"}],
            "per_row": 1,
            "columns": ["フレーム", "経った秒", "height の合計", "平均", "最低", "最高", "sediment", "debris", "3つの合計", "flow"],
            "rows": [[r["frame"], f"{r['elapsed']:.2f}", f"{r['height_sum']:,.0f}", f"{r['mean_h']:.2f}", f"{r['height_min']:g}", f"{r['height_max']:g}",
                      f"{r['sediment_sum']:,.0f}", f"{r['debris_sum']:,.0f}", f"{r['total']:,.0f}", f"{r['flow_sum']:,.0f}"] for r in rows]},
        ],
        "notes": [
            "<strong>erode をかけると、地形全体が低くなる。</strong>40 フレームで平均 5 ほど。海面や建物の高さを決めるのは erode のあと。",
            "<strong>山は削れ、谷は埋まる。</strong>最高点も最低点も真ん中へ寄る。",
            "<strong>sediment・debris の値を「土の量」として足しても合わない。</strong>",
        ],
        "next": ["端を閉じたとき（Border の扱い）に量が保たれるか", "sediment の値の単位"],
    }
    with open(os.path.join(OUT, "169_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 169_report.json")


if __name__ == "__main__":
    main()
