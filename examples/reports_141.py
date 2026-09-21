# -*- coding: utf-8 -*-
"""実験141 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "141_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    box_grid = [r for r in rows if r["shape"] == "box" and r["init"] == "grid"]
    for r in box_grid:
        r["want"] = round((2 / r["sep"] + 1) * (1 / r["sep"] + 1) ** 2)
    sph = {i: [r for r in rows if r["shape"] == "sphere" and r["init"] == i] for i in ("grid", "tetrahedral")}
    line_chart(os.path.join(OUT, "141_points.png"),
               [{"label": "格子: 点の数 × s³", "points": [(r["sep"], r["grid_est"]) for r in sph["grid"]],
                 "color": PALETTE[0]},
                {"label": "四面体: 点の数 × s³/√2", "points": [(r["sep"], r["fcc_est"]) for r in sph["tetrahedral"]],
                 "color": PALETTE[1]},
                {"label": "球の体積 4π/3", "points": [(r["sep"], r["volume"]) for r in sph["grid"]],
                 "color": PALETTE[4], "dash": True}],
               title="球（半径1）: 点の数から体積を逆算すると、式に近づく",
               x_label="点の間隔 s", y_label="体積の見積もり")
    print("141_points.png")
    g, t = sph["grid"][-1], sph["tetrahedral"][-1]
    payload = {
        "title": "pointsfromvolume の点は、格子なら1点 s³・四面体なら s³/√2 — 箱では面の上にも並ぶ",
        "summary":
            "箱（2×1×1）と球（半径1）の中を、pointsfromvolume で間隔 s の点で埋め、点の数を数えた。\n\n"
            "**格子（Grid）で埋めると、1点あたりの体積は s³。** 球では、点の数 × s³ が s = 0.025 で "
            f"{g['grid_est']:.4f}（体積 {g['volume']:.4f}、{(g['grid_est'] / g['volume'] - 1) * 100:+.2f}%）。\n\n"
            "**四面体（Tetrahedral）で埋めると、同じ間隔で約1.41倍の点が入る。** 点の数 × s³/√2 が "
            f"{t['fcc_est']:.4f}（{(t['fcc_est'] / t['volume'] - 1) * 100:+.2f}%）。面心立方の詰め方と同じ密度。\n\n"
            "**箱を格子で埋めると、点は面の上にも並ぶ。** 点の数は (2/s + 1)·(1/s + 1)² と"
            f"{'3通りすべて一致' if all(r['points'] == r['want'] for r in box_grid) else '一致しないものがあった'}"
            f"（s = 0.1 で {box_grid[0]['points']:,} = 21×11×11）。そのため、点の数 × s³ は箱の体積より多い"
            f"（s = 0.1 で {box_grid[0]['grid_est']:g}、体積は 2）。点を粒とみなすと、粒の中心が面の上に来る。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "形・並べ方・間隔と、点の数",
             "note": "球は polymesh 96×192。",
             "images": [{"path": "141_points.png",
                         "caption": "間隔を細かくすると、格子（s³）も四面体（s³/√2）も球の体積に近づく。"}],
             "per_row": 1,
             "columns": ["形", "並べ方", "間隔", "点の数", "点×s³", "点×s³/√2", "体積", "秒"],
             "rows": [[r["shape"], r["init"], f"{r['sep']:g}", f"{r['points']:,}", f"{r['grid_est']:.4f}",
                       f"{r['fcc_est']:.4f}", f"{r['volume']:.4f}", f"{r['sec']:.3f}"] for r in rows]},
        ],
        "notes": [
            "<strong>格子は s³、四面体は s³/√2。</strong>同じ間隔なら四面体のほうが約1.41倍詰まる。",
            "<strong>箱では面の上にも点が並ぶ。</strong>粒のシミュレーションで体積をそろえたいときは注意。",
            "<strong>間隔を半分にすると点は8倍。</strong>0.025 で球の中に約27万〜38万点。",
        ],
        "next": ["Jitter Scale を入れたときの点の数", "SDF を渡したとき（Source = SDF）に数が変わるか"],
    }
    with open(os.path.join(OUT, "141_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 141_report.json")


if __name__ == "__main__":
    main()
