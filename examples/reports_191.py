# -*- coding: utf-8 -*-
"""実験191 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "191_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "191_gap.png"),
               [{"label": "いちばん深いへこみ（測った値）", "points": [(math.log2(r["rows"] - 1), math.log10(r["max_gap"])) for r in rows], "color": PALETTE[0]},
                {"label": "sin²(Δ/2)", "points": [(math.log2(r["rows"] - 1), math.log10(r["face_formula"])) for r in rows], "color": PALETTE[4], "dash": True},
                {"label": "平均のへこみ", "points": [(math.log2(r["rows"] - 1), math.log10(r["mean_gap"])) for r in rows], "color": PALETTE[1]}],
               title="半径 1 の球（Polygon Mesh）と本当の球の差。縦は log10、横は log2（Rows − 1）",
               x_label="log2（Rows − 1）", y_label="log10（へこみ）")
    r97, r13 = rows[-1], rows[1]
    ratio = [round(rows[i]["max_gap"] / rows[i + 1]["max_gap"], 2) for i in range(len(rows) - 1)]
    mean_over_max = [round(r["mean_gap"] / r["max_gap"], 3) for r in rows]
    payload = {
        "title": "多角形の球のいちばん深いへこみは sin²(Δ/2) — 分割を倍にするたびに 1/4、平均はその 0.56 倍",
        "summary":
            "半径 1 の本当の球の上に 2 万点を一様に撒き、VEX の xyzdist で多角形の球（Polygon Mesh、Columns = 2 × (Rows − 1)）までの距離を測った。"
            "多角形は球の内側に入るので、距離は「その場所のへこみ」になる。\n\n"
            "**いちばん深いへこみは、四角形の真ん中の sin²(Δ/2) に合った。**Δ = π/(Rows − 1) は隣の点どうしの角度。"
            f"Rows 97 で {r97['max_gap']:.7f}（式 {r97['face_formula']:.7f}）、Rows 13 で {r13['max_gap']:.5f}（式 {r13['face_formula']:.5f}）。"
            "辺の真ん中だけのへこみ 1 − cos(Δ/2) の、ほぼ 2 倍（縦と横の両方向ぶん）。\n\n"
            f"**分割を倍にすると、へこみは約 1/4**（Rows を倍にするごとに {' → '.join(f'{x}' for x in ratio)} 分の 1）。\n\n"
            f"**平均のへこみは、いちばん深いへこみの約 0.56 倍**（{'・'.join(map(str, mean_over_max))}）。\n\n"
            f"**xyzdist は速い。**2 万点で {r97['sec'] * 1000:.0f} ミリ秒（Rows 97、面 18,432 枚）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "分割と、へこみ",
            "images": [{"path": "191_gap.png", "caption": "測った値（青）は点線の式にほぼ重なる。"}],
            "per_row": 1,
            "columns": ["Rows", "Columns", "いちばん深いへこみ", "sin²(Δ/2)", "辺の真ん中 1 − cos(Δ/2)", "平均", "秒"],
            "rows": [[r["rows"], r["cols"], f"{r['max_gap']:.7f}", f"{r['face_formula']:.7f}", f"{r['edge_formula']:.7f}",
                      f"{r['mean_gap']:.7f}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>球のへこみは sin²(π/(2(Rows − 1)))。</strong>欲しい精度から分割を逆算できる（へこみ 0.001 なら Rows 約 50）。",
            "<strong>分割を倍にすると誤差は 1/4、点の数は 4 倍。</strong>",
            "<strong>表面までの距離をはかるなら xyzdist。</strong>2 万点で数ミリ秒。",
        ],
        "next": ["Polygon（測地球）のへこみ", "subdivide した球のへこみ"],
    }
    with open(os.path.join(OUT, "191_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 191_report.json", ratio, mean_over_max)


if __name__ == "__main__":
    main()
