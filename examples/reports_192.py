# -*- coding: utf-8 -*-
"""実験192 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "192_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "192_inset.png"),
               [{"label": f"Distance {d:g}（測った体積）", "points": [(r["inset"], r["volume"]) for r in rows if r["dist"] == d], "color": PALETTE[i]}
                for i, d in enumerate((0.5, 1.0))]
               + [{"label": f"角錐台の式（Distance {d:g}）", "points": [(r["inset"], r["want_volume"]) for r in rows if r["dist"] == d],
                   "color": PALETTE[4], "dash": True} for d in (0.5, 1.0)],
               title="polyextrude（1×1 の正方形）: Inset と押し出した体積",
               x_label="Inset", y_label="体積")
    ok = [r for r in rows if r["inset"] <= 0.5]
    worst = max(abs(r["volume"] - r["want_volume"]) for r in ok)
    over = [r for r in rows if r["inset"] > 0.5]
    payload = {
        "title": "polyextrude の Inset は上の面を i だけ内側へ寄せる — 体積は角錐台の式どおり、i ≥ 0.5 で四角錐になり、それ以上は裏返らない",
        "summary":
            "1 × 1 の正方形1枚を polyextrude（Output Back 入）で押し出し、Distance d と Inset i を変えて、上の面の大きさと体積を測った。\n\n"
            f"**上の面は、辺が 1 − 2i の正方形になった。**体積は角錐台の式 d/3 · (A₁ + A₂ + √(A₁A₂))（A₁ = 1、A₂ = (1 − 2i)²）と、"
            f"i ≤ 0.5 の 10 通りすべてで差 {worst:.0e} 以内。上の面は、Distance の高さにちょうど乗る。\n\n"
            "**i = 0.5 で上の面が点になり、四角錐になる**（体積 d/3、d = 1 で 0.333333）。\n\n"
            f"**i を 0.5 より大きくしても、上の面は裏返らない。**i = 0.6 で上の面は 0.0001 の小さな正方形のまま止まり、体積は "
            f"{over[-1]['volume']:.6f}（四角錐とほぼ同じ）。点の数も 8 のまま（上の4点がほぼ重なる）。"
            "Inset を大きくしすぎると、見た目は尖っていても、点が重なった形になる。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Distance・Inset と形",
            "images": [{"path": "192_inset.png", "caption": "測った体積（実線）は式（点線）に重なり、0.5 から先は平らになる。"}],
            "per_row": 1,
            "columns": ["Distance", "Inset", "点", "面", "上の面の辺", "1 − 2i", "体積", "角錐台の式", "秒"],
            "rows": [[f"{r['dist']:g}", f"{r['inset']:g}", r["points"], r["prims"], f"{r['top_side']:g}", f"{r['want_side']:g}",
                      f"{r['volume']:.6f}", f"{r['want_volume']:.6f}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>Inset は面の縁から内側へ寄せる距離。</strong>上の面の辺は 1 − 2i。",
            "<strong>押し出した体積は角錐台の式で出せる。</strong>i = 0.25・d = 1 で 0.583333。",
            "<strong>Inset を面の半分より大きくすると、上の点が重なる。</strong>尖らせたいなら、あとで fuse してまとめる。",
        ],
        "next": ["三角形・六角形の面での Inset", "Individual Elements を切ったとき（隣り合う面をまとめて押し出す）の体積"],
    }
    with open(os.path.join(OUT, "192_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 192_report.json", worst)


if __name__ == "__main__":
    main()
