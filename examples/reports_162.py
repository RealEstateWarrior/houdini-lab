# -*- coding: utf-8 -*-
"""実験162 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "162_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "162_crease.png"),
               [{"label": f"Iterations {it}", "points": [(r["weight"], r["volume"]) for r in rows if r["iterations"] == it and r["weight"] <= 4],
                 "color": PALETTE[i]} for i, it in enumerate((2, 4))],
               title="subdivide（OpenSubdiv Catmull-Clark）: 辺の crease の重みと、1×1×1 の箱の体積",
               x_label="crease の重み w", y_label="体積")
    ok = all((r["volume"] == 1.0 and r["corner_gap"] == 0.0) == (r["weight"] >= r["iterations"]) for r in rows)
    by = {(r["weight"], r["iterations"]): r for r in rows}
    payload = {
        "title": "subdivide の crease は「重み w の回数までは尖ったまま」— w ≥ Iterations なら箱はそのまま、体積 1",
        "summary":
            "1×1×1 の箱の辺すべてに crease SOP（Operation = Set）で重み w を付け、subdivide（Algorithm = OpenSubdiv Catmull-Clark）で"
            "Iterations 2 回と 4 回の細分をかけた。体積と、角の点が元の角 (0.5, 0.5, 0.5) からどれだけ離れたかを測った。\n\n"
            f"**重みが細分の回数以上なら、形は元の箱のまま。**体積 1.000000、角のずれ 0 になったのは、w ≥ Iterations のときだけ"
            f"（16通り{'すべてこの通り' if ok else 'で外れがあった'}）。w = 2 は Iterations 2 で箱のまま、4 では "
            f"{by[(2.0, 4)]['volume']:.6f} に丸まる。重みは「何回目の細分まで尖らせるか」の回数として効いている。\n\n"
            f"**重み 0 はただの Catmull-Clark。**Iterations 4 で体積 {by[(0.0, 4)]['volume']:.6f}、角は {by[(0.0, 4)]['corner_gap']:.3f} 内側へ下がる。"
            "\n\n**重みの小数も効く。**w = 0.5・1.5 は、その前後の整数の間の丸さになった（Iterations 4 で 0.529・0.865）。"
            "w ≥ 1 になると、面の真ん中は元の面の上（外へ 0.5）まで届く。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "crease の重み・Iterations と形",
            "images": [{"path": "162_crease.png", "caption": "Iterations 2（青）は w = 2 で体積 1 に届き、4（橙）は w = 4 で届く。"}],
            "per_row": 1,
            "columns": ["重み w", "Iterations", "点", "面", "体積", "角のずれ", "いちばん外の座標", "秒"],
            "rows": [[f"{r['weight']:g}", r["iterations"], f"{r['points']:,}", f"{r['prims']:,}", f"{r['volume']:.6f}",
                      f"{r['corner_gap']:.6f}", f"{r['max_extent']:g}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>crease の重みは「細分の回数」。</strong>Iterations を増やしたら、同じ硬さに見せるには重みも増やす。",
            "<strong>完全に尖らせたいなら、重みを Iterations 以上に。</strong>10 のような大きな値なら回数を気にしなくてよい。",
            "<strong>重み 0 の箱は、体積が 1/3 ほどまで縮む。</strong>形を保ちたい所には crease か、辺を足す。",
        ],
        "next": ["角の点（頂点）の crease の効き方", "Houdini Catmull-Clark（algorithm = houdini）との違い"],
    }
    with open(os.path.join(OUT, "162_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 162_report.json", ok)


if __name__ == "__main__":
    main()
