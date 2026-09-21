# -*- coding: utf-8 -*-
"""実験130 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "130_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows, edge = data["rows"], data["edge"]
    main_rows = [r for r in rows if abs(r["cusp"] - r["turn"]) > 0.02 or r["cusp"] == r["turn"]]
    ok = sum((r["split_ratio"] > 0.5) == r["expect_split"] for r in main_rows)
    series = []
    for i, k in enumerate((4, 8, 24)):
        sub = [e for e in edge if e["k"] == k]
        series.append({"label": f"{k}角柱（曲がり角 {360 / k:g}°）",
                       "points": [(e["delta"], e["split_ratio"]) for e in sub], "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "130_cusp.png"), series,
               title="Cusp Angle を曲がり角より δ だけ小さくしたとき、法線が分かれるか（1=分かれる）",
               x_label="δ（度）", y_label="分かれた点の割合")
    print("130_cusp.png")

    def first_split(k):
        sub = sorted((e for e in edge if e["k"] == k), key=lambda e: e["delta"])
        prev = 0.0
        for e in sub:
            if e["split_ratio"] > 0.5:
                return prev, e["delta"]
            prev = e["delta"]
        return prev, None

    b = {k: first_split(k) for k in (4, 8, 24)}
    payload = {
        "title": "normal の Cusp Angle は「曲がり角がこれより大きければ角を立てる」 — ちょうど等しいと、なめらか",
        "summary":
            "k 角柱の側面では、隣り合う面の向きが 360/k 度ずつ変わる。normal で頂点ごとの法線を作り、"
            "Cusp Angle を振って、側面の角の点で法線が分かれる（角がくっきりする）かを数えた。\n\n"
            f"**{len(main_rows)} 通りのうち {ok} 通りで、「曲がり角 > Cusp Angle なら分かれる」とおりだった。** "
            "4・6・8・12・24 角柱のすべてで、境目は曲がり角そのもの。"
            "既定の 60° なら、6角柱（60°）までは丸く、4角柱（90°）は角が立つ。\n\n"
            "**ちょうど等しいときは、分かれない（なめらか）。** さらに、Cusp Angle を曲がり角より少しだけ"
            "小さくしても、まだ分かれない幅があった: 90° では "
            f"{b[4][0]:g}° 小さくしても分かれず {b[4][1]:g}° で分かれ、45° では {b[8][0]:g}°／{b[8][1]:g}°、"
            f"15° では {b[24][0]:g}°／{b[24][1]:g}°。"
            "どれも曲がり角の 0.1〜0.2% ほどの幅で、計算の誤差を見込んだ余裕と考えられる（中の計算は確かめていない）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "角柱の曲がり角と Cusp Angle",
             "note": "Add Normals to = Vertices。側面の中ほどの点で、頂点ごとの法線が2つ以上あるものを「分かれた」とした。",
             "images": [{"path": "130_cusp.png",
                         "caption": "曲がり角のすぐ下では、まだ分かれない。少し離れると全部の点で分かれる。"}],
             "per_row": 1,
             "columns": ["角柱", "曲がり角", "Cusp Angle", "分かれた点の割合", "式（曲がり角 > Cusp）"],
             "rows": [[f"{r['k']}", f"{r['turn']:g}°", f"{r['cusp']:g}°", f"{r['split_ratio']:.2f}",
                       "分かれる" if r["expect_split"] else "なめらか"] for r in main_rows]},
        ],
        "notes": [
            "<strong>Cusp Angle は「角と見なす曲がり」のしきい値。</strong>曲がり角がこれより大きい所だけ角が立つ。",
            "<strong>既定の 60° では、6角柱までは丸く見える。</strong>六角ナットの角を立てたいなら 60° 未満にする。",
            "<strong>しきい値ちょうどの形は、丸いほうに倒れる。</strong>わずかに小さくしても同じ。確実に角を立てるなら、1°以上下げる。",
        ],
        "next": [
            "Weighting Method（均等・角度・面積）で、なめらかな法線の向きがどう変わるか",
            "箱（90°）の角を、Cusp Angle を変えずに丸く見せる方法（面取り）",
        ],
    }
    with open(os.path.join(OUT, "130_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 130_report.json")


if __name__ == "__main__":
    main()
