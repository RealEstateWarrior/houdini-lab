# -*- coding: utf-8 -*-
"""実験164 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "164_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    gaps = sorted({r["gap"] for r in rows})
    line_chart(os.path.join(OUT, "164_union.png"),
               [{"label": f"間隔 {s:g}", "points": [(math.log2(1 / r["voxel"]), r["ratio"]) for r in rows if r["gap"] == s], "color": PALETTE[i]}
                for i, s in enumerate(gaps)],
               title="vdbfromparticles（半径 0.5 の粒 2 つ）: 体積 ÷ 2つの球の和の式（横は log2(1/Voxel Size)）",
               x_label="log2（1 / Voxel Size）", y_label="式に対する比")
    ratios = {}
    for s in gaps:
        xs = [r for r in rows if r["gap"] == s]
        d = [1 - r["ratio"] for r in xs]
        ratios[s] = [round(d[i] / d[i + 1], 2) for i in range(len(d) - 1)]
    fine = [r for r in rows if r["voxel"] == 0.0125]
    payload = {
        "title": "vdbfromparticles の粒は pscale を半径にした球 — 2つ重ねると「2つの球の和」の体積に、升目の2乗で近づく",
        "summary":
            "pscale = 0.5 の2点を間隔 s に置き、vdbfromparticles（距離の VDB）→ convertvdb（Polygons）で面にして体積を測った。"
            "比べる式は、半径 r の球2つを間隔 s で重ねた体積 2·(4/3)πr³ − π(4r + s)(2r − s)²/12。\n\n"
            "**粒の半径は pscale そのまま。**間隔 0（1つの球）で、囲む箱の幅は 1 に近づいた（Voxel 0.0125 で 0.9997）。"
            "間隔 1.2（離れた2つ）では横幅がちょうど 2.2。\n\n"
            f"**重なった2つの粒の体積は、2つの球の和の式に合う。**Voxel 0.0125 で、4通りとも式の {min(r['ratio'] for r in fine) * 100:.2f}〜"
            f"{max(r['ratio'] for r in fine) * 100:.2f}%。重なった部分でふくらんだり、なめらかに埋まったりはしない（尖った和のまま）。\n\n"
            "**いつも少し小さく、Voxel を半分にすると不足が約 1/4 になる。**不足の縮み方は "
            + "、".join(f"間隔 {s:g} で {'・'.join(str(x) for x in v)} 倍" for s, v in ratios.items())
            + "。Voxel 0.05 で約 1%、0.025 で 0.3%、0.0125 で 0.07%。\n\n"
            f"**面の数は Voxel を半分にするとほぼ4倍**（間隔 0 で {rows[0]['prims']:,} → {rows[2]['prims']:,}）。時間はどれも 0.01 秒前後（1回目だけ 0.09 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "間隔・Voxel Size と体積",
            "images": [{"path": "164_union.png", "caption": "4本の線がほぼ重なる。重なり方によらず、升目の細かさだけで決まる。"}],
            "per_row": 1,
            "columns": ["間隔 s", "Voxel Size", "体積", "2つの球の和", "比", "横幅", "式の横幅", "縦", "面", "秒"],
            "rows": [[f"{r['gap']:g}", f"{r['voxel']:g}", f"{r['volume']:.6f}", f"{r['want']:.6f}", f"{r['ratio']:.5f}",
                      f"{r['size_x']:g}", f"{r['want_x']:g}", f"{r['size_y']:g}", f"{r['prims']:,}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>粒の大きさは pscale（半径）で決まる。</strong>直径ではない。",
            "<strong>重なりは尖った和。</strong>くっついた所をなめらかにしたいなら、あとで vdbsmoothsdf などをかける（確かめていない）。",
            "<strong>Voxel Size を半分にすると、体積の不足は約 1/4、面は約 4 倍。</strong>",
        ],
        "next": ["Minimum Radius in Voxels より小さい粒の扱い", "たくさんの粒（液体）での体積の合計"],
    }
    with open(os.path.join(OUT, "164_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 164_report.json", ratios)


if __name__ == "__main__":
    main()
