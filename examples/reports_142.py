# -*- coding: utf-8 -*-
"""実験142 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

KEYS = ["tetrahedron", "cube", "octahedron", "icosahedron", "dodecahedron"]


def main():
    with open(os.path.join(OUT, "142_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, f = d["rows"], d["formula"]
    for r, k in zip(rows, KEYS):
        r["want_area"], r["want_vol"] = f[k]["area"], f[k]["volume"]
    line_chart(os.path.join(OUT, "142_ratio.png"),
               [{"label": "中心から頂点まで（1 なら Radius どおり）",
                 "points": [(r["type"], r["rmax"]) for r in rows], "color": PALETTE[0]},
                {"label": "面積 ÷ 外接半径1の式", "points": [(r["type"], r["area"] / r["want_area"]) for r in rows],
                 "color": PALETTE[1]},
                {"label": "体積 ÷ 外接半径1の式", "points": [(r["type"], r["volume"] / r["want_vol"]) for r in rows],
                 "color": PALETTE[2]}],
               title="Radius = 1 の platonic（0 四面体 / 1 立方体 / 2 八面体 / 3 二十面体 / 4 十二面体）",
               x_label="Solid Type の番号", y_label="式に対する比")
    by = {r["label"]: r for r in rows}
    cube, dod = by["Cube"], by["Dodecahedron"]
    payload = {
        "title": "platonic の Radius は、四面体・八面体・二十面体では頂点までの距離 — 立方体は辺が1、十二面体は0.9933",
        "summary":
            "platonic で Radius = 1 にして5種類を作り、中心から頂点までの距離・辺・面積・体積を測った。"
            "外接球の半径が 1 のときの式と比べる。\n\n"
            "**四面体・八面体・二十面体は、Radius がそのまま頂点までの距離。**面積と体積も式と6桁一致した"
            f"（二十面体の面積 {by['Icosahedron']['area']:.6f}、体積 {by['Icosahedron']['volume']:.6f}）。\n\n"
            f"**立方体は違う。**頂点までは {cube['rmax']:.6f}（= √3/2）で、辺が {cube['edge_max']:g}。"
            "Radius = 1 は「一辺 1 の立方体」になる。面積 6・体積 1。\n\n"
            f"**十二面体も1からずれる。**頂点までは {dod['rmax']:.6f}、辺は {dod['edge_max']:.6f}。"
            f"外接半径 1 の式（辺 {f['dodecahedron']['edge']:.6f}）より {(dod['rmax'] - 1) * 100:+.2f}% 小さい。"
            "形は正十二面体のまま（どの頂点も同じ距離）で、大きさだけが違う。なぜ 0.9933 なのかは確かめていない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Radius = 1 の5種類",
            "note": "式は外接半径1のとき。Solid Type の 5（Soccer Ball）と 6（Utah Teapot）は正多面体ではないので外した。",
            "images": [{"path": "142_ratio.png", "caption": "青が1からずれるのは立方体（0.866）と十二面体（0.993）だけ。"}],
            "per_row": 1,
            "columns": ["形", "点", "面", "頂点まで", "辺", "面積", "式の面積", "体積", "式の体積", "秒"],
            "rows": [[r["label"], r["points"], r["prims"], f"{r['rmax']:.6f}", f"{r['edge_max']:.6f}",
                      f"{r['area']:.6f}", f"{r['want_area']:.6f}", f"{r['volume']:.6f}", f"{r['want_vol']:.6f}",
                      f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>Radius は形によって意味が違う。</strong>四面体・八面体・二十面体は外接半径、立方体は一辺。",
            "<strong>十二面体を大きさ合わせに使うなら、頂点までを測ってから。</strong>Radius=1 で 0.9933。",
            "<strong>どれも一瞬で作れる。</strong>1個 0.01 秒以下。",
        ],
        "next": ["十二面体の 0.9933 の出どころ", "Soccer Ball の面の数と面積"],
    }
    with open(os.path.join(OUT, "142_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 142_report.json")


if __name__ == "__main__":
    main()
