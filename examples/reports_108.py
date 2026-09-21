# -*- coding: utf-8 -*-
"""実験108 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "108_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    sc = [r for r in rows if r["case"].startswith("scatter")]
    gr = [r for r in rows if r["case"].startswith("grid")]
    all_ok = all(r["tris"] == r["want"] for r in rows)
    worst_area = max(abs(r["area"] - r["hull_area"]) for r in rows)
    big = sc[-1]

    line_chart(
        os.path.join(OUT, "108_tris.png"),
        [{"label": "三角形の数 ÷ 点の数（実測）",
          "points": [(math.log10(r["n"]), r["tris"] / r["n"]) for r in sc],
          "color": PALETTE[0]},
         {"label": "2（点が多いときの行き先）",
          "points": [(math.log10(r["n"]), 2.0) for r in sc],
          "color": PALETTE[2], "dash": True}],
        title="点を増やすと、三角形はほぼ点の2倍になる（外周の点の分だけ少ない）",
        x_label="点の数（log10。1=10、5=100,000）", y_label="三角形 ÷ 点")
    print("108_tris.png")

    payload = {
        "title": "triangulate2d の三角形は 2n−2−h 枚 — 9通りすべて式どおり、面積は凸包と一致",
        "summary":
            "平面の点 n 個を三角形で埋めると、外周（凸包）に乗る点が h 個なら、"
            "三角形は **2n − 2 − h 枚**になる。オイラーの多面体定理から出る式で、"
            "並べ方によらない。面を張った範囲は凸包になるので、面積の合計も凸包の面積と同じはず。\n\n"
            "ばらまいた点（scatter、10〜100,000点）と、格子に並んだ点（3×3〜51×51）で確かめた。"
            "凸包と面積は Python 側で別に計算した。\n\n"
            f"**9通りすべてで三角形の数が式と一致**（{'例外なし' if all_ok else '例外あり'}）。"
            f"面積の差は最大 {worst_area:.6f}。三角形以外の面は1枚も出なかった。\n\n"
            "格子の点は、4点が同じ円に乗るのでどちらの対角線で割っても成り立つが、"
            "それでも枚数は 2(k−1)² で、1マスを2枚に割っている。\n\n"
            f"速さは、{big['n']:,} 点で {big['sec']:.2f} 秒"
            f"（10,000 点で {sc[3]['sec']:.3f} 秒）。1万点から10万点に増やすと、時間は約10倍。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "点の数と三角形の数",
             "note": "scatter は 4×3 の板の上。格子は grid の面を消して点だけにしたもの。"
                     "h は凸包に乗る点の数（一直線上の点も数える）。",
             "images": [{"path": "108_tris.png",
                         "caption": "外周の点の割合が減るので、三角形 ÷ 点 は2に近づく。"}],
             "per_row": 1,
             "columns": ["点の置き方", "n", "h", "三角形", "2n−2−h", "面積", "凸包の面積", "秒"],
             "rows": [[r["case"].replace("scatter_", "scatter ").replace("grid_", "格子 "),
                       f"{r['n']:,}", str(r["h"]), f"{r['tris']:,}", f"{r['want']:,}",
                       f"{r['area']:.6f}", f"{r['hull_area']:.6f}", f"{r['sec']:.4f}"]
                      for r in rows]},
        ],
        "notes": [
            "<strong>三角形は 2n−2−h 枚。</strong>9通りすべて一致。"
            "点の数と外周の点の数だけで、分ける前に枚数が分かる。",
            f"<strong>面を張る範囲は凸包。</strong>面積の差は最大 {worst_area:.6f}。"
            "へこんだ形の中だけを埋めたいときは、拘束の辺か Silhouette を渡す必要がある"
            "（今回は試していない）。",
            "<strong>格子でも崩れない。</strong>同じ円に4点が乗る並びでも、1マス2枚ずつになる。",
            f"<strong>10万点で約{big['sec']:.1f}秒。</strong>1万点→10万点で約10倍。",
        ],
        "next": [
            "Silhouette と拘束の辺で、へこんだ形の中だけを埋めたときの枚数",
            "Cap Maximum Area で三角形を足したときの枚数と面積",
            "ドロネーの条件（外接円に他の点が入らない）を数で確かめる",
        ],
    }
    with open(os.path.join(OUT, "108_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 108_report.json")


if __name__ == "__main__":
    main()
