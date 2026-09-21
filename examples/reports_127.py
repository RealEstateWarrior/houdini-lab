# -*- coding: utf-8 -*-
"""実験127 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "127_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = sorted(data["rows"], key=lambda r: r["manhattan"])
    for r in rows:
        r["euclid"] = math.hypot(*r["target"])
    same = all(r["cost"] == r["path_length"] == r["manhattan"] == r["edge_dist"] for r in rows)
    line_chart(
        os.path.join(OUT, "127_path.png"),
        [{"label": "findshortestpath の道の長さ", "points": [(r["euclid"], r["path_length"]) for r in rows],
          "color": PALETTE[0]},
         {"label": "|x|+|z|", "points": [(r["euclid"], r["manhattan"]) for r in rows],
          "color": PALETTE[1], "dash": True},
         {"label": "まっすぐの距離", "points": [(r["euclid"], r["euclid"]) for r in rows],
          "color": PALETTE[4], "dash": True}],
        title="四角の網の最短経路は、縦横の道のり（まっすぐより長い）",
        x_label="まっすぐの距離", y_label="道の長さ")
    print("127_path.png")
    payload = {
        "title": "findshortestpath の道のりは Edge の距離と同じ — 四角の網では |x|+|z|",
        "summary":
            "実験119 で、distancealonggeometry の Edge は「辺をたどった道のり」だと分かった。"
            "findshortestpath の道の長さも同じになるかを確かめた。2×2 の四角の網（41×41点）の真ん中から、"
            "4つの点へ道を引いた。\n\n"
            f"**4本すべてで、cost・道の線の長さ・Edge の距離・|x|+|z| の4つが{'完全に一致' if same else '一致しなかった'}。**"
            "たとえば (1, 1) までは 2.0（まっすぐなら √2 ≒ 1.414）。道は縦横の辺だけを通る。\n\n"
            f"道の長さは点の属性 {data['cost_attr']} にも入る。4本の道を出すのに {data['sec'] * 1000:.0f} ミリ秒。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "行き先ごとの道の長さ",
             "note": "Output Paths = From any start to each end。道の長さは measure の Perimeter。",
             "images": [{"path": "127_path.png",
                         "caption": "道の長さは |x|+|z| の線に乗り、まっすぐの距離より長い。"}],
             "per_row": 1,
             "columns": ["行き先", "道の点", "道の長さ", "cost", "Edge の距離", "|x|+|z|", "まっすぐ"],
             "rows": [[f"({r['target'][0]:g}, {r['target'][1]:g})", str(r["points_on_path"]),
                       f"{r['path_length']:.6f}", f"{r['cost']:.6f}", f"{r['edge_dist']:.6f}",
                       f"{r['manhattan']:.6f}", f"{r['euclid']:.6f}"] for r in rows]},
        ],
        "notes": [
            "<strong>findshortestpath・Edge・attribfill の到着時間は、同じ「辺の道のり」。</strong>"
            "（実験115・119 とあわせて）",
            "<strong>四角の網では、斜めの行き先ほど遠回りになる。</strong>45°の向きで約1.41倍。",
            "<strong>まっすぐに近い道がほしいなら、網を三角形や remesh にする。</strong>"
            "（実験119 では remesh で Edge のずれが約1/6 になった）",
        ],
        "next": [
            "三角の網・remesh した網で、道が斜めに通るか",
            "コスト属性（坂の急さ）を付けて、山を避ける道になるか",
        ],
    }
    with open(os.path.join(OUT, "127_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 127_report.json")


if __name__ == "__main__":
    main()
