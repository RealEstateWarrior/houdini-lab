# -*- coding: utf-8 -*-
"""実験112 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

OP = {"sdfunion": "和（SDF Union）", "sdfintersect": "積（SDF Intersect）",
      "sdfdifference": "差（SDF Difference）"}


def main():
    with open(os.path.join(OUT, "112_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = data["rows"]
    poly_err = data["poly_ball"] / data["ball"] - 1
    voxels = sorted({r["voxel"] for r in rows}, reverse=True)

    def rel(op, v):
        return next(r["rel"] for r in rows if r["op"] == op and r["voxel"] == v)

    series = []
    for i, op in enumerate(OP):
        series.append({"label": OP[op],
                       "points": [(math.log2(0.1 / v), abs(rel(op, v)) * 100) for v in voxels],
                       "color": PALETTE[i]})
    series.append({"label": "元の多角形の球そのもののずれ",
                   "points": [(math.log2(0.1 / v), abs(poly_err) * 100) for v in voxels],
                   "color": PALETTE[4], "dash": True})
    line_chart(os.path.join(OUT, "112_csg.png"), series,
               title="ボクセルを半分にするたびに、式とのずれが減る（どれも体積は少なめに出る）",
               x_label="ボクセルを半分にした回数（0=0.1、3=0.0125）",
               y_label="式とのずれ（%、絶対値）")
    print("112_csg.png")

    fine = voxels[-1]
    all_under = all(r["rel"] < 0 for r in rows)
    payload = {
        "title": "vdbcombine の和・積・差は球2つの式に収束 — ボクセル 0.0125 で 0.08% 以内、どれも少なめ",
        "summary":
            f"半径1の球を2つ、中心の距離 {data['d']:g} で重ね、vdbcombine の SDF Union / "
            "Intersect / Difference で合わせてから多角形に戻し、体積を式と比べた。"
            "重なり（レンズ）の体積は π(4r+d)(2r−d)²/12 で出せるので、"
            "和・積・差の答えはすべて式で分かる。\n\n"
            f"**3つとも、ボクセルを細かくするほど式に近づいた。** ボクセル {fine:g} で、"
            f"和 {rel('sdfunion', fine) * 100:+.3f}%・積 {rel('sdfintersect', fine) * 100:+.3f}%・"
            f"差 {rel('sdfdifference', fine) * 100:+.3f}%。"
            f"ボクセル 0.1 では 和 {rel('sdfunion', 0.1) * 100:+.2f}%・積 "
            f"{rel('sdfintersect', 0.1) * 100:+.2f}%。\n\n"
            f"**ずれは{'すべて' if all_under else 'ほとんど'}マイナス（体積が少なめ）。** "
            "実験094（VDB は形をやせさせる）と同じ向き。ずれの割合は積（レンズ）が一番大きい。"
            "レンズは縁が鋭く尖っていて、その先をボクセルが丸めるからだと考えられる"
            "（尖りの影響だけを分けては確かめていない）。\n\n"
            "ボクセルを半分にしたときの減り方は、最初は約1/4（0.1→0.05 で和が "
            f"{rel('sdfunion', 0.1) / rel('sdfunion', 0.05):.1f}分の1）、細かくなるほど鈍る。"
            "元の球（200×200 の多角形）自体が "
            f"{poly_err * 100:+.3f}% 小さいので、そこが底になる。\n\n"
            "速さ: ボクセル 0.0125 で和が "
            f"{next(r['sec'] for r in rows if r['op'] == 'sdfunion' and r['voxel'] == fine):.1f} 秒"
            "（VDB 化・合成・多角形化・体積の合計）。半分にすると約3〜4倍。\n\n"
            "つまずいた点: 素性の控え（node_dump.py）では Operation の選択肢が12個で切れていて、"
            "SDF Intersect / Difference が載っていなかった。本物は18個ある。"
            "控えを直した（選択肢は全部残す）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "ボクセルの大きさと体積（式との比）",
             "note": "球は polymesh 200×200。vdbfrompolygons → vdbcombine → convertvdb（Polygons）→"
                     " measure の Volume を面ごとに足した値。",
             "images": [{"path": "112_csg.png",
                         "caption": "どの合わせ方も、ボクセルを細かくすると式に近づく。"
                                    "灰色の破線は、元の多角形の球が持っているずれ。"}],
             "per_row": 1,
             "columns": ["ボクセル", "合わせ方", "体積", "式", "ずれ", "秒"],
             "rows": [[f"{r['voxel']:g}", OP[r["op"]], f"{r['volume']:.6f}",
                       f"{r['want']:.6f}", f"{r['rel'] * 100:+.3f}%", f"{r['sec']:.3f}"]
                      for r in rows]},
        ],
        "notes": [
            "<strong>和・積・差は式どおりに収束する。</strong>ボクセル 0.0125 で3つとも 0.08% 以内。",
            "<strong>体積は少なめに出る。</strong>12通りすべてマイナス。"
            "ぴったり合わせたいときは、細かくするか、少し太らせて戻す。",
            "<strong>尖った所を含む形ほどずれる。</strong>同じボクセルでも、積（レンズ）は和の約2倍ずれた。",
            "<strong>Operation の選択肢は18個。</strong>SDF Intersect・SDF Difference・Topology 系は後ろのほうにある。",
        ],
        "next": [
            "Topology Union / Intersect（形ではなく、ボクセルの有無で合わせる）の結果",
            "polygon の boolean（実験098）と、同じ球2つで速さと精度を比べる",
            "Half Width を広げると、細い所のやせ方が変わるか",
        ],
    }
    with open(os.path.join(OUT, "112_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 112_report.json")


if __name__ == "__main__":
    main()
