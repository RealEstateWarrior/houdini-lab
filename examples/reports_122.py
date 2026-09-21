# -*- coding: utf-8 -*-
"""実験122 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "122_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows, multi, sharp = data["rows"], data["multi"], data["sharp"]
    worst_sq = max(abs(r["perimeters"][0] - r["mitre"]) for r in rows)
    worst_tri = max(abs(r["perimeters"][0] - r["mitre"]) for r in sharp)
    tip = 0.2 / math.sin(math.radians(10))

    line_chart(
        os.path.join(OUT, "122_offset.png"),
        [{"label": "測った周の長さ（頂角20°の三角形）",
          "points": [(0, sharp[0]["per0"])] + [(r["d"], r["perimeters"][0]) for r in sharp],
          "color": PALETTE[0]},
         {"label": "角を尖らせる式",
          "points": [(0, sharp[0]["per0"])] + [(r["d"], r["mitre"]) for r in sharp],
          "color": PALETTE[2], "dash": True},
         {"label": "角を丸める式",
          "points": [(0, sharp[0]["per0"])] + [(r["d"], r["round"]) for r in sharp],
          "color": PALETTE[1], "dash": True}],
        title="外へずらした線は、鋭い角でも尖ったまま（丸めない）",
        x_label="ずらす距離 d", y_label="周の長さ")
    print("122_offset.png")

    inner = [p for p in multi["perimeters"] if p < 8]
    outer = [p for p in multi["perimeters"] if p > 8]
    payload = {
        "title": "polyexpand2d は角を丸めずに尖らせる — 20°の鋭い角でも。Divisions は距離を等分する",
        "summary":
            "1辺2の正方形を polyexpand2d で外と内へずらし、できた線の周の長さを測った。"
            "外へ d ずらしたとき、角を尖らせる（留め継ぎ）なら 4·(2+2d)、"
            "角を丸めるなら 8 + 2πd になるので、周の長さでどちらか分かる。\n\n"
            f"**角は尖らせていた。** 3通りの d で、外へずらした周は 4·(2+2d) と一致"
            f"（差は最大 {worst_sq:.6f}）。点の数も4のまま。内へずらした周も 4·(2−2d) どおり。\n\n"
            "**頂角20°の鋭い三角形でも、尖らせたまま。** 外へずらした線は元と相似な三角形になり、"
            "周の長さは (内接円の半径 + d)/(内接円の半径) 倍の式と一致した"
            f"（差は最大 {worst_tri:.6f}）。d = 0.2 だと、先端は {tip:.3f} も外へ伸びる"
            "（d ÷ sin(10°)）。角を丸める道具ではないので、鋭い角の縁取りは先が大きく飛び出す。\n\n"
            "**Divisions は、ずらす距離を等分する。** Offset 0.2・Divisions 4 にすると、"
            "0.2 ずつ4本ではなく、0.05 刻みで 0.05・0.1・0.15・0.2 の4本ができた"
            f"（内側の周 {', '.join(f'{p:g}' for p in inner)}、外側 {', '.join(f'{p:g}' for p in outer)}）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "正方形（1辺2）をずらしたときの周の長さ",
             "note": "Output = Offset Curves。周の長さは measure の Perimeter。",
             "images": [{"path": "122_offset.png",
                         "caption": "鋭い三角形でも、測った値は「尖らせる式」に重なる。"}],
             "per_row": 1,
             "columns": ["d", "向き", "周の長さ", "尖らせる式", "丸める式", "点"],
             "rows": [[f"{r['d']:g}", "外" if r["side"] == "outside" else "内",
                       f"{r['perimeters'][0]:.6f}", f"{r['mitre']:.6f}",
                       f"{r['round']:.6f}" if r["round"] else "—", str(r["points"])] for r in rows]},
            {"label": "頂角20°の二等辺三角形（高さ2）を外へずらす",
             "note": "尖らせる式 = 元の周 × (r + d)/r（r は内接円の半径）。",
             "images": [],
             "per_row": 1,
             "columns": ["d", "周の長さ", "尖らせる式", "丸める式"],
             "rows": [[f"{r['d']:g}", f"{r['perimeters'][0]:.6f}", f"{r['mitre']:.6f}",
                       f"{r['round']:.6f}"] for r in sharp]},
        ],
        "notes": [
            "<strong>角は尖らせる。</strong>丸い縁取りがほしいときは、別の方法（VDB で太らせて戻すなど）を使う"
            "（今回は試していない）。",
            f"<strong>鋭い角ほど先が伸びる。</strong>頂角20°で d=0.2 なら、先端は {tip:.2f} 外へ出る。",
            "<strong>Divisions は Offset を等分。</strong>「0.2 間隔で4本」なら Offset 0.8・Divisions 4 にする。",
        ],
        "next": [
            "Output を Offset Surfaces にしたときの面積（輪の帯の面積）",
            "へこんだ角（凹の角）を外へずらしたとき、線が重なるか",
            "内へずらしすぎて形が消えるときの振る舞い",
        ],
    }
    with open(os.path.join(OUT, "122_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 122_report.json")


if __name__ == "__main__":
    main()
