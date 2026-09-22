# -*- coding: utf-8 -*-
"""実験151 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "151_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    poly, mesh, A, V = d["rows"], d["mesh"], d["area"], d["volume"]
    for r in poly + mesh:
        r["dv"] = (1 - r["volume"] / V) * 100
        r["da"] = (1 - r["area"] / A) * 100
        r["k"] = r["dv"] * r["points"]
    line_chart(os.path.join(OUT, "151_deficit.png"),
               [{"label": "Polygon（Frequency）", "points": [(math.log10(r["points"]), r["dv"]) for r in poly], "color": PALETTE[0]},
                {"label": "Polygon Mesh（Rows × Columns）", "points": [(math.log10(r["points"]), r["dv"]) for r in mesh], "color": PALETTE[1]}],
               title="半径1の球: 体積の足りなさ（%）と点の数（横は log10）",
               x_label="log10（点の数）", y_label="4π/3 に対して足りない %")
    ok = all(r["points"] == r["want_points"] and r["prims"] == r["want_prims"] for r in poly)
    kp = sum(r["k"] for r in poly[3:]) / len(poly[3:])
    km = sum(r["k"] for r in mesh[3:]) / len(mesh[3:])
    p12, m48 = poly[-1], [r for r in mesh if r["cols"] == 48][0]
    payload = {
        "title": "sphere の Polygon は点 10f²+2・面 20f² の測地球 — 同じ点の数なら Polygon Mesh より体積の不足が約3割小さい",
        "summary":
            "半径 1 の sphere を Primitive Type = Polygon にして Frequency f を 1〜12 と変え、"
            "同じくらいの点の数の Polygon Mesh（Rows = Columns/2 + 1）と比べた。\n\n"
            f"**Polygon は二十面体を分けた測地球。**点は 10f²+2、面は 20f²（すべて三角形）で、7通り{'すべて一致' if ok else 'で一致しないものがあった'}。"
            "f = 1 は正二十面体そのもの（面積 9.574541・体積 2.536151 は実験142 の二十面体と同じ値）。頂点はどれも半径 1 ちょうどの上にある。\n\n"
            "**同じ点の数なら、Polygon のほうが丸い。**体積の不足（%）× 点の数 は、点が 160 を超えたあたりから Polygon で"
            f" 約 {kp:.1f}、Polygon Mesh で 約 {km:.1f}。どちらも「点の数に反比例して近づく」が、係数は Polygon のほうが"
            f" {(1 - kp / km) * 100:.0f}% 小さい。f = 12（{p12['points']:,} 点）で不足 {p12['dv']:.3f}%、"
            f"Mesh 48 列（{m48['points']:,} 点）で {m48['dv']:.3f}%。\n\n"
            "**Polygon Mesh は極に三角形が集まる。**面は四角形と三角形が混ざる。Polygon は三角形だけで、大きさがそろっている。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "Polygon（Frequency）",
             "images": [{"path": "151_deficit.png", "caption": "青（Polygon）が、同じ点の数でいつも下（不足が小さい）。"}],
             "per_row": 1,
             "columns": ["Frequency", "点", "10f²+2", "面", "20f²", "面の形", "面積", "体積", "体積の不足 %", "不足 × 点", "秒"],
             "rows": [[r["freq"], f"{r['points']:,}", f"{r['want_points']:,}", f"{r['prims']:,}", f"{r['want_prims']:,}",
                       "・".join(map(str, r["sides"])) + "角形", f"{r['area']:.6f}", f"{r['volume']:.6f}",
                       f"{r['dv']:.3f}", f"{r['k']:.1f}", f"{r['sec']:.4f}"] for r in poly]},
            {"label": "Polygon Mesh（比べる相手）",
             "columns": ["Rows × Columns", "点", "面", "面の形", "面積", "体積", "体積の不足 %", "不足 × 点", "秒"],
             "rows": [[f"{r['rows']} × {r['cols']}", f"{r['points']:,}", f"{r['prims']:,}", "・".join(map(str, r["sides"])) + "角形",
                       f"{r['area']:.6f}", f"{r['volume']:.6f}", f"{r['dv']:.3f}", f"{r['k']:.1f}", f"{r['sec']:.4f}"] for r in mesh]},
        ],
        "notes": [
            "<strong>Frequency f で点は 10f²+2。</strong>f を倍にすると点も面も約4倍。",
            "<strong>少ない点で丸く見せたいなら Polygon。</strong>体積の不足が同じ点の数で約3割小さい。",
            "<strong>UV や行列で扱いたいなら Polygon Mesh。</strong>Rows と Columns の格子になっている。",
        ],
        "next": ["Polygon の球を UV 展開したときのゆがみ", "remesh にかけたときに点の数がどれだけ変わるか"],
    }
    with open(os.path.join(OUT, "151_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 151_report.json", ok, round(kp, 2), round(km, 2))


if __name__ == "__main__":
    main()
