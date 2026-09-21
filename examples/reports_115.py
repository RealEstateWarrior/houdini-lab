# -*- coding: utf-8 -*-
"""実験115 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"poisson_edges": "Interpolate：左0・右1 → 直線",
         "eikonal_edge": "Arrival Time：左端から → x",
         "eikonal_point": "Arrival Time：1点から（四角の網）→ 直線距離",
         "eikonal_point_vs_manhattan": "同じ値を 縦横の道のり |x|+|z| と比べる",
         "eikonal_point_tris": "Arrival Time：1点から（三角の網）→ 直線距離",
         "eikonal_sphere": "Arrival Time：球の北極から → 弧の長さ"}


def main():
    with open(os.path.join(OUT, "115_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]

    def pick(case):
        return [r for r in rows if r["case"] == case]

    series = []
    for i, case in enumerate(("eikonal_point", "eikonal_point_tris", "eikonal_point_vs_manhattan")):
        series.append({"label": LABEL[case], "points": [(r["res"], r["mean_abs"]) for r in pick(case)],
                       "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "115_eikonal.png"), series,
               title="1点からの到着時間は、網を細かくしても直線距離に近づかない",
               x_label="横の点の数（網の細かさ）", y_label="ずれの平均（絶対値）")
    print("115_eikonal.png")

    sph = pick("eikonal_sphere")
    quad = pick("eikonal_point")
    tri = pick("eikonal_point_tris")
    payload = {
        "title": "attribfill の到着時間は「網の辺をたどる道のり」 — 四角の網ではマンハッタン距離そのもの",
        "callout": "実験119 で、この値が distancealonggeometry の Edge（辺をたどった道のり）と"
                   "3つの網すべてで同じになると確かめた。面に沿った本当の距離がほしいときは、"
                   "distancealonggeometry の Surface を使う。",
        "summary":
            "attribfill で値を埋め、式で出る答えと比べた。\n\n"
            "**Interpolate (Poisson) は式どおり。** 4×2 の板の左端を0・右端を1に固定すると、"
            "中は x に比例する直線で埋まった（3通りの細かさで、ずれ 0.000000）。\n\n"
            "**Arrival Time (Eikonal) も、網の辺と同じ向きに進むなら式どおり。** 左端から出発すると、"
            "到着時間は x+2 にぴったり。球の北極から出発すると、弧の長さ r·θ に対して "
            f"ずれ {sph[0]['max_abs']:.4f}（24段）→ {sph[-1]['max_abs']:.5f}（96段）で、"
            "細かくすると約1/4ずつ減った（経線がそのまま辺になっている）。\n\n"
            "**ところが1点から出発すると、直線距離にならない。** 四角の網では、到着時間は "
            "**縦横の道のり |x|+|z| と1点残らず一致**した（ずれ 0.000000）。"
            f"直線距離とは、角で最大 {quad[0]['max_abs']:.4f}（= 3 − √5）ずれる。"
            "網を 21→81 と細かくしても、ずれの平均は "
            f"{quad[0]['mean_abs']:.3f} → {quad[-1]['mean_abs']:.3f} でほとんど変わらない。"
            "網の辺をたどる最短の道のりを数えているからと考えられる。\n\n"
            "三角の網（斜めの辺がある）にすると、ずれの平均は "
            f"{tri[-1]['mean_abs']:.3f} に下がるが、最大は {tri[-1]['max_abs']:.4f} のまま"
            "（斜めの辺が向いていない側の角）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "埋め方と、式とのずれ",
             "note": "板は 4×2（横の点 21・41・81）。球は半径1の polymesh（段 24・48・96）。"
                     "固定する点は Boundary Group に入れた。",
             "images": [{"path": "115_eikonal.png",
                         "caption": "1点から出発すると、網を細かくしてもずれが減らない。"
                                    "縦横の道のり（緑）とは0。"}],
             "per_row": 1,
             "columns": ["埋め方と答え", "細かさ", "ずれの平均", "ずれの最大"],
             "rows": [[LABEL[r["case"]], str(r["res"]), f"{r['mean_abs']:.6f}",
                       f"{r['max_abs']:.6f}"] for r in rows]},
        ],
        "notes": [
            "<strong>Interpolate は、まわりの平均で埋める。</strong>両端を固定した板なら直線になる。",
            "<strong>Arrival Time は「辺をたどる道のり」。</strong>四角の網では |x|+|z|。"
            "丸く広がる波にはならない。",
            "<strong>細かくしても直らない。</strong>ずれは網の向きで決まるので、点を増やしても同じ。"
            "直線距離がほしいなら、点どうしの距離を VEX で直接測る（distance や xyzdist）。",
            "<strong>網の向きに沿った広がりなら正確。</strong>端からの距離、球の経線に沿った距離は式どおり。",
        ],
        "next": [
            "Blur (Diffusion) の Diffusion Time と、ぼけ幅（ガウスの広がり）の関係",
            "remesh で向きのばらけた三角の網にすると、1点からの到着時間は丸くなるか",
            "Speed Attribute を場所で変えたとき、屈折のように曲がるか",
        ],
    }
    with open(os.path.join(OUT, "115_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 115_report.json")


if __name__ == "__main__":
    main()
