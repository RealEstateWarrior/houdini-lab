# -*- coding: utf-8 -*-
"""実験154 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

ORDER = ["none", "tris", "trifan", "quadfan", "quads", "gridquads"]


def main():
    with open(os.path.join(OUT, "154_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, sm = d["rows"], d["gridquads_smooth"]
    by = {(r["n"], r["mode"]): r for r in rows}
    line_chart(os.path.join(OUT, "154_counts.png"),
               [{"label": f"n = {n}", "points": [(i, by[(n, m)]["added_prims"]) for i, m in enumerate(ORDER)], "color": PALETTE[k]}
                for k, n in enumerate((12, 13))],
               title="polyfill: 上下2つの穴を塞いだ面の数（0 Single / 1 Tris / 2 Tri Fan / 3 Quad Fan / 4 Quads / 5 Grid）",
               x_label="Fill Mode の番号", y_label="足された面の数")
    t12 = by[(12, "tris")]
    q12 = by[(12, "quads")]
    g12 = by[(12, "gridquads")]
    payload = {
        "title": "polyfill の四角形の塞ぎ方は、辺が奇数の穴を塞がない — 三角形は 1つの穴に n−2 枚、Grid は少しふくらむ",
        "summary":
            "蓋のない tube（半径1・高さ1・Columns = n）の上下の穴を polyfill で塞ぎ、Fill Mode ごとに足された面を数えた。"
            "穴は正 n 角形なので、塞いだ面積は2つで n·sin(2π/n)（n = 12 で 6）のはず。\n\n"
            "**n = 12（偶数）では、6通りとも穴が塞がった。**1つの穴あたり Single Polygon は 1 枚、Triangles は n−2 枚"
            f"（計 {t12['added_prims']}）、Triangle Fan は中心に点を1つ足して n 枚、Quadrilateral Fan は n/2 枚、"
            f"Quadrilaterals は {q12['added_prims'] // 2} 枚（点を {q12['added_points'] // 2} 個足す）。"
            "面積は Grid 以外の5通りで 6.000000、体積は正12角柱の 3.000000 とぴったり合った。\n\n"
            "**n = 13（奇数）では、四角形の3通りが何も足さなかった。**Single・Triangles・Triangle Fan は塞がる。"
            "ノードには「Some patches were not created because they contain an odd number of edges」という警告が出る"
            "（エラーではないので、ネットワークを流れる形は穴があいたまま進む）。\n\n"
            f"**Quadrilateral Grid は、蓋が外へふくらむ。**既定（Smooth 入り・強さ {sm[0]['strength']:g}）で上の蓋の点が y = {sm[0]['top_y_max']:g}"
            f"（縁は 0.5）まで出て、面積 {sm[0]['cap_area']:.6f}、体積 {g12['volume']:.6f}（+{(g12['volume'] / 3 - 1) * 100:.2f}%）。"
            f"Smooth を切るとさらにふくらみ、y = {sm[1]['top_y_max']:g}・面積 {sm[1]['cap_area']:.6f} になった。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Fill Mode ごとの塞がり方",
             "images": [{"path": "154_counts.png", "caption": "n = 13 では Quad Fan・Quads・Grid が 0 枚。"}],
             "per_row": 1,
             "columns": ["n", "Fill Mode", "足した面", "足した点", "面の形", "蓋の面積", "式", "体積", "正 n 角柱の式", "上下の広がり", "警告", "秒"],
             "rows": [[r["n"], r["label"], r["added_prims"], r["added_points"],
                       " / ".join(f"{k}角形 {v}" for k, v in r["sides"].items()) or "—",
                       f"{r['cap_area']:.6f}", f"{r['want_cap']:.6f}", f"{r['volume']:.6f}", f"{r['want_volume']:.6f}",
                       f"{r['cap_y_spread']:g}", "あり" if r["warning"] else "—", f"{r['sec']:.4f}"] for r in rows]},
            {"label": "Quadrilateral Grid の Smooth（n = 12）",
             "columns": ["Smooth", "強さ", "蓋の面積", "上の蓋の y（最小〜最大）"],
             "rows": [["入" if x["smooth"] else "切", f"{x['strength']:g}", f"{x['cap_area']:.6f}",
                       f"{x['top_y_min']:g}〜{x['top_y_max']:g}"] for x in sm]},
        ],
        "notes": [
            "<strong>奇数の穴に四角形の塞ぎ方を使うと、穴のまま進む。</strong>警告は出るが、止まらない。",
            "<strong>平らに塞ぎたいなら Single Polygon・Triangles・Triangle Fan・Quadrilateral Fan・Quadrilaterals。</strong>Grid だけ中がふくらむ。",
            "<strong>Triangles は 1つの穴に n−2 枚。</strong>divide（実験125）の三角形分割と同じ枚数。",
        ],
        "next": ["Grid のふくらみを抑えるつまみ（Tangent Strength など）", "平らでない穴を塞いだときの形"],
    }
    with open(os.path.join(OUT, "154_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 154_report.json")


if __name__ == "__main__":
    main()
