# -*- coding: utf-8 -*-
"""実験120 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"slab_polymesh": "板 0.3（Polygon Mesh）",
         "slab_poly_usedivisions": "板 0.3（Polygon + Use Divisions）",
         "shell_0.5": "殻 1−0.5", "shell_0.8": "殻 1−0.8", "shell_0.95": "殻 1−0.95",
         "solid_sphere": "詰まった球（直径2）"}


def main():
    with open(os.path.join(OUT, "120_stats.json"), encoding="utf-8") as fp:
        rows = {r["case"]: r for r in json.load(fp)["rows"]}
    good = [rows[k] for k in ("shell_0.95", "shell_0.8", "slab_polymesh", "shell_0.5", "solid_sphere")]
    line_chart(
        os.path.join(OUT, "120_thickness.png"),
        [{"label": "測った厚み（平均）", "points": [(r["want"], r["mean"]) for r in good],
          "color": PALETTE[0]},
         {"label": "作った厚み", "points": [(r["want"], r["want"]) for r in good],
          "color": PALETTE[2], "dash": True}],
        title="measurethickness は、作った厚みをそのまま返す（殻・板・球）",
        x_label="作った厚み", y_label="測った厚み")
    print("120_thickness.png")

    pm, ud = rows["slab_polymesh"], rows["slab_poly_usedivisions"]
    shells = [rows[k] for k in ("shell_0.5", "shell_0.8", "shell_0.95")]
    worst_shell = max(max(abs(r["min"] - r["want"]), abs(r["max"] - r["want"])) for r in shells)
    payload = {
        "title": "measurethickness は殻の厚みを6桁で返す — 板の縁ではぼかしで細く出る。box の Use Divisions は面にならない",
        "summary":
            "厚みが分かっている形を3つ作って、measurethickness の値と比べた。\n\n"
            "**殻（半径1の球の中に、裏返した半径 r の球）は、ほぼぴったり 1−r。** "
            f"r = 0.5・0.8・0.95 のすべての点で、ずれは最大 {worst_shell:.6f}。"
            f"詰まった球は直径 2 に対して {rows['solid_sphere']['min']:.6f}〜{rows['solid_sphere']['max']:.6f}。\n\n"
            "**板（4×0.3×4）は、既定のままだと少し薄く出る。** 上と下の面の真ん中あたりの点で、平均 "
            f"{pm['mean']:.4f}、最小 {pm['min']:.4f}。"
            "ぼかし（Use Blur）と、まわりの中央値（Median of Neighbors）を切ると、全部 "
            f"{pm['nofilter']['min']:.6f} になった。縁に近い所の短い値が、ぼかしで内側へにじんでいる。\n\n"
            "**つまずいた点: box を Polygon のまま Use Divisions で割ると、面ではなく開いた線の籠になる。** "
            f"{ud['prims']} 本すべてが閉じていない線で、体積は {ud['volume']:g}。"
            f"measurethickness は {ud['mean']:.6f} という意味の無い値を返した。"
            "点を増やした箱がほしいときは、Primitive Type を Polygon Mesh にして Axis Divisions で割る。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "作った厚みと、測った厚み",
             "note": "球は polymesh 96×192。板は上と下の面の、縁から 0.5 以上内側の点だけを数えた。",
             "images": [{"path": "120_thickness.png",
                         "caption": "殻・詰まった球は線の上。板は既定のぼかしで少し下に出る。"}],
             "per_row": 1,
             "columns": ["形", "作った厚み", "平均", "最小", "最大", "点の数"],
             "rows": [[LABEL[k], f"{r['want']:g}", f"{r['mean']:.6f}", f"{r['min']:.6f}",
                       f"{r['max']:.6f}", str(r["n"])] for k, r in rows.items()]},
            {"label": "板で、ぼかしを切ったとき",
             "note": "Use Blur と Median of Neighbors を切った。",
             "images": [],
             "per_row": 1,
             "columns": ["作り方", "既定の平均", "既定の最小", "ぼかし無しの平均", "ぼかし無しの最小"],
             "rows": [[LABEL[k], f"{rows[k]['mean']:.6f}", f"{rows[k]['min']:.6f}",
                       f"{rows[k]['nofilter']['mean']:.6f}", f"{rows[k]['nofilter']['min']:.6f}"]
                      for k in ("slab_polymesh", "slab_poly_usedivisions")]},
        ],
        "notes": [
            "<strong>丸い殻の厚みは正確。</strong>ずれは 0.000001 程度。",
            "<strong>角のある形では、ぼかしで縁の値がにじむ。</strong>正確な値がほしいなら Use Blur と Median of Neighbors を切る。",
            "<strong>box の Use Divisions（Polygon のとき）は開いた線の籠。</strong>measure の体積が0になる。"
            "点を増やすなら Polygon Mesh にする。",
            "<strong>速い。</strong>36,100 点の殻で約0.1秒。",
        ],
        "next": [
            "Max Fitting Sphere と Ray Length で、角の近くの値がどう違うか",
            "Use SDF を入れたときの速さと精度",
            "厚みが場所で変わる形（くさび）で、変化を正しく追えるか",
        ],
    }
    with open(os.path.join(OUT, "120_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 120_report.json")


if __name__ == "__main__":
    main()
