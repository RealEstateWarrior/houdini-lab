# -*- coding: utf-8 -*-
"""実験143 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "143_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, arcs = d["rows"], d["arcs"]
    line_chart(os.path.join(OUT, "143_circle.png"),
               [{"label": "周 ÷ 2π", "points": [(math.log2(r["divs"]), r["perimeter"] / (2 * math.pi)) for r in rows],
                 "color": PALETTE[0]},
                {"label": "面積 ÷ π", "points": [(math.log2(r["divs"]), r["area"] / math.pi) for r in rows],
                 "color": PALETTE[1]}],
               title="circle（Polygon・半径1）: 分割を増やすと円に近づく（横は log2 n）",
               x_label="log2(Divisions)", y_label="円の値に対する比")
    worst = max(max(abs(r["perimeter"] - r["want_perimeter"]), abs(r["area"] - r["want_area"])) for r in rows)
    r12, r768 = [r for r in rows if r["divs"] == 12][0], rows[-1]
    a = {(x["arc"], x["divs"]): x for x in arcs}
    payload = {
        "title": "circle の Polygon は頂点が円周に乗る正 n 角形 — 弧の Divisions は辺の数",
        "summary":
            "半径 1 の circle を Polygon にして、Divisions を 3〜768 と変え、周と面積を測った。\n\n"
            "**頂点は全部ちょうど半径1の上。周は 2n·sin(π/n)、面積は (n/2)·sin(2π/n) と一致した**"
            f"（7通りで差は最大 {worst:.0e}）。n = 12 で面積は {r12['area']:g}（π より "
            f"{(r12['area'] / math.pi - 1) * 100:+.1f}%）、n = 768 で {r768['area']:.6f}。"
            "円より少し小さく出るのは、辺が円の内側を通るから。\n\n"
            "**弧（0〜90°）にすると、Divisions は辺の数になる。**Open Arc で Divisions = 4 なら点は "
            f"{a[('openarc', 4)]['points']}、12 なら {a[('openarc', 12)]['points']}。"
            f"Closed Arc は中心に1点足して閉じた扇形（周 {a[('closedarc', 4)]['perimeter']:.6f} = 弧 + 半径2本）、"
            f"Sliced Arc は中心から切った三角形が Divisions 枚（4 なら {a[('slicedarc', 4)]['prims']} 枚）になる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "閉じた円: Divisions と周・面積",
             "images": [{"path": "143_circle.png", "caption": "面積のほうが周より遅れて近づく。"}],
             "per_row": 1,
             "columns": ["Divisions", "点", "半径（最小〜最大）", "周", "式の周", "面積", "式の面積", "秒"],
             "rows": [[r["divs"], r["points"], f"{r['rmin']:g}〜{r['rmax']:g}", f"{r['perimeter']:.6f}",
                       f"{r['want_perimeter']:.6f}", f"{r['area']:.6f}", f"{r['want_area']:.6f}",
                       f"{r['sec']:.4f}"] for r in rows]},
            {"label": "弧（Arc Angles 0〜90）の3種類",
             "note": "Sliced Arc の面積は1枚目の三角形だけ。",
             "columns": ["Arc Type", "Divisions", "点", "面", "閉じている", "周（1枚目）", "面積（1枚目）"],
             "rows": [[x["arc"], x["divs"], x["points"], x["prims"], "はい" if x["closed"] else "いいえ",
                       f"{x['perimeter']:.6f}", f"{x['area']:.6f}"] for x in arcs]},
        ],
        "notes": [
            "<strong>円の Polygon は内接多角形。</strong>面積は必ず π より小さい（12分割で −4.5%）。",
            "<strong>弧の Divisions は辺の数。</strong>点は Divisions + 1（Closed Arc はさらに中心の1点）。",
            "<strong>Sliced Arc はバラバラの三角形。</strong>ピザを切り分けた形で、面の数 = Divisions。",
        ],
        "next": ["NURBS の円を convert したときの点の並び", "Rows/Columns が効く楕円（Radius を2つ別にする）"],
    }
    with open(os.path.join(OUT, "143_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 143_report.json")


if __name__ == "__main__":
    main()
