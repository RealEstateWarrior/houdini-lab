# -*- coding: utf-8 -*-
"""実験211 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import PALETTE, line_chart  # noqa: E402

NAMES = {"t020": "Thickness 0.02", "t010": "0.01（既定）", "t005": "0.005", "t0025": "0.0025", "calc": "Calculate Uniform"}


def main():
    with open(os.path.join(OUT, "211_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    with open(os.path.join(OUT, "211_section.json"), encoding="utf-8") as fp:
        sec = json.load(fp)
    t = {r["case"]: r for r in d["rows"]}
    top = d["top"]
    table_line = {"label": "机（天板の上面と縁）", "points": [(0.0, top), (0.6, top), (0.6, top - 0.04)], "color": (40, 40, 40)}
    series = [{"label": NAMES[k], "points": [tuple(p) for p in sec[k] if 0.0 <= p[0] <= 1.0], "color": PALETTE[i % len(PALETTE)]}
              for i, k in enumerate(["t020", "t010", "t005", "calc"])]
    line_chart(os.path.join(OUT, "211_edge.png"), series + [table_line], title="天板の縁のあたり（机の真ん中で切った断面）",
               x_label="机の中心からの距離 x（m）", y_label="高さ（m）", x_range=(0.4, 0.75), y_range=(0.70, 0.79))
    line_chart(os.path.join(OUT, "211_drape.png"), series + [table_line], title="垂れ方の全体（同じ断面）",
               x_label="机の中心からの距離 x（m）", y_label="高さ（m）", x_range=(0.0, 1.0), y_range=(0.35, 0.8))
    table = []
    for k, lab in NAMES.items():
        r = t[k]
        tf = r.get("to_t0025")
        table.append([lab, f"{r['pscale'] * 1000:.2f}", f"{(r['top_min'] - top) * 1000:.1f}", f"{r['gap_mm']:.1f}", str(r["below_top"]),
                      f"{r['lowest']:.3f}", f"{tf['mean'] * 100:.2f}" if tf else "—"])
    g = lambda k: (t[k]["top_min"] - top) * 1000  # noqa: E731
    payload = {
        "title": f"テーブルクロスが机から浮くのは Thickness の分だけ — 既定 0.01 で {g('t010'):.0f} mm 浮く。0.0025 まで薄くしてもめり込まず、Calculate Uniform（辺の長さ × 0.25）なら {g('calc'):.1f} mm",
        "summary":
            "**課題: 実験206 で、天板（上面 0.76 m）に乗った布は平均 0.770 m の高さにあり、1 cm 浮いていた。vellumsolver の Default Thickness の既定 0.01 と同じ値。"
            "厚みを変えると浮きは消えるか。薄くしすぎて机にめり込まないか。垂れ方は変わるか。**\n\n"
            f"実験206 と同じ机と布を {d['grid_rows']}×{d['grid_cols']} に分けて（辺の長さ約 2.3 cm）、{d['last']} フレーム落とした。"
            "vellumsolver の Default Thickness を 0.02・0.01（既定）・0.005・0.0025 にしたものと、vellumconstraints の Thickness を Calculate Uniform（辺の長さ × Edge Length Scale 0.25）にしたものの 5 通り。"
            "天板の範囲にある布の点（約 1500 個）の高さを測り、机の真ん中（z = 0 付近）で切った断面も描いた。\n\n"
            f"**浮きは Thickness そのもの。**天板の上の点のいちばん低い高さは、天板より 0.02 で {g('t020'):.1f} mm、0.01 で {g('t010'):.1f} mm、0.005 で {g('t005'):.1f} mm、0.0025 で {g('t0025'):.1f} mm 上。"
            "布の点の pscale に Thickness の値がそのまま入り、ソルバはそれを半径として天板から離していると考えられる（pscale の値は測った。ソルバの中は見ていない）。\n\n"
            f"**薄くしても、机にめり込まなかった。**天板より下に入った点は、5 通りとも 0 個。Calculate Uniform は、pscale が {t['calc']['pscale'] * 1000:.2f} mm（辺の長さ約 2.3 cm の約 8 分の 1）になり、"
            f"浮きは {g('calc'):.1f} mm。\n\n"
            f"**厚いほど、裾が短く垂れる。**布のいちばん低い点は、0.02 で {t['t020']['lowest']:.3f} m、0.01 で {t['t010']['lowest']:.3f} m、0.005 で {t['t005']['lowest']:.3f} m。"
            f"厚い布は折れ曲がりにくく、角のひだが大きく丸くなる。0.0025 との形の差は、0.02 で平均 {t['t020']['to_t0025']['mean'] * 100:.1f} cm、0.01 で {t['t010']['to_t0025']['mean'] * 100:.1f} cm。\n\n"
            "**決め方: 布の上に物を置く場面や、机との境目が映る場面では、Thickness を下げる。**vellumconstraints の Thickness を Calculate Uniform にすると、布の細かさに合わせて決まる。",
        "graph": "", "graph_image": "",
        "comparisons": [
            {"label": "天板の縁のあたり（断面）",
             "images": [{"path": "211_edge.png", "caption": "黒い線が机。布は天板から Thickness の分だけ浮いて乗る。"},
                        {"path": "211_drape.png", "caption": "厚いほど、縁から外へふくらみ、裾が短い。"}],
             "per_row": 1,
             "columns": ["設定", "pscale（mm）", "天板からいちばん低い所（mm）", "天板からの平均（mm）", "めり込んだ点", "いちばん低い点（m）", "0.0025 との差 平均（cm）"],
             "rows": table},
        ],
        "notes": [
            f"<strong>布が机から浮くのは Thickness の分。</strong>既定の 0.01 では {g('t010'):.0f} mm 浮く。",
            "<strong>0.0025 まで薄くしても、めり込まなかった</strong>（66×84 の布、Substeps 5）。",
            f"<strong>Calculate Uniform にすると、布の細かさに合った厚みになる。</strong>66×84 で {t['calc']['pscale'] * 1000:.1f} mm。",
            "<strong>厚みは垂れ方も変える。</strong>厚いほど裾が短く、角のひだが丸い。",
        ],
        "next": [],
    }
    with open(os.path.join(OUT, "211_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 211_report.json")
    print(payload["title"])


if __name__ == "__main__":
    main()
