# -*- coding: utf-8 -*-
"""実験091〜094 の図を描く。数字は out/NNN_stats.json から読む（書き写さない）。

    python examples/charts_091_094.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def stats(no):
    with open(os.path.join(OUT, f"{no}_stats.json"), encoding="utf-8") as fp:
        return json.load(fp)


def chart_091():
    rows = stats("091")["rows"]
    line_chart(
        os.path.join(OUT, "091_reduce.png"),
        [
            {"label": "ずれ 平均（元の幅に対する%）",
             "points": [(r["prims"], r["gap_mean_pct"]) for r in rows][::-1],
             "color": PALETTE[0]},
            {"label": "ずれ 最大（元の幅に対する%）",
             "points": [(r["prims"], r["gap_max_pct"]) for r in rows][::-1],
             "color": PALETTE[1], "dash": True},
        ],
        title="面を減らすと、形はどれだけずれるか（元 3,540面）",
        x_label="残った面の数", y_label="元の形からのずれ（幅の%）")
    print("091_reduce.png")


def chart_092():
    rows = stats("092")["rows"]
    # 半分にするたびに何倍になったか。理屈どおりなら4倍（面積あたりの数）
    ratios = [r for r in rows if r.get("prim_ratio")]
    line_chart(
        os.path.join(OUT, "092_remesh.png"),
        [
            {"label": "1段ごとの面の増え方（実測）",
             "points": [(i + 1, r["prim_ratio"]) for i, r in enumerate(ratios)],
             "color": PALETTE[0]},
            {"label": "面積あたりで増えるなら 4倍",
             "points": [(1, 4.0), (len(ratios), 4.0)],
             "color": PALETTE[4], "dash": True},
        ],
        title="辺を半分にすると、面は約4倍になる（実測 4.29 / 3.96 / 4.10）",
        x_label="辺を半分にした回数", y_label="前の段からの倍率",
        y_range=(0, 9))
    line_chart(
        os.path.join(OUT, "092_gap.png"),
        [
            {"label": "ずれ 平均",
             "points": [(r["edge"], r["gap_mean"]) for r in rows][::-1],
             "color": PALETTE[0]},
            {"label": "かかった時間（秒）",
             "points": [(r["edge"], r["seconds"]) for r in rows][::-1],
             "color": PALETTE[1], "dash": True},
        ],
        title="辺を細かくすると、ずれは1/4に、時間は約4倍に",
        x_label="目指す辺の長さ", y_label="ずれ（単位なし）／秒")
    print("092_remesh.png 092_gap.png")


def chart_093():
    data = stats("093")
    rows = data["rows"]
    line_chart(
        os.path.join(OUT, "093_smooth.png"),
        [
            {"label": "体積（元の%）",
             "points": [(r["strength"], r["volume_pct"]) for r in rows],
             "color": PALETTE[0]},
        ],
        title="ならしても、体積はほとんど減らない（強さ160で 99.60%）",
        x_label="Strength", y_label="体積（元の%）")
    line_chart(
        os.path.join(OUT, "093_gap.png"),
        [
            {"label": "元の形からのずれ 平均",
             "points": [(r["strength"], r["gap_mean"]) for r in rows],
             "color": PALETTE[1]},
        ],
        title="形は動いている。強さを上げるほどずれは増える",
        x_label="Strength", y_label="ずれ 平均")
    print("093_smooth.png 093_gap.png")


def chart_094():
    rows = stats("094")["rows"]
    ratios = [r for r in rows if r.get("voxel_ratio")]
    line_chart(
        os.path.join(OUT, "094_voxels.png"),
        [
            {"label": "1段ごとの升目の増え方（実測）",
             "points": [(i + 1, r["voxel_ratio"]) for i, r in enumerate(ratios)],
             "color": PALETTE[0]},
            {"label": "空間ぜんぶを持つなら 8倍",
             "points": [(1, 8.0), (len(ratios), 8.0)],
             "color": PALETTE[4], "dash": True},
            {"label": "表面だけ持つなら 4倍",
             "points": [(1, 4.0), (len(ratios), 4.0)],
             "color": PALETTE[2], "dash": True},
        ],
        title="升目を半分にしても、数は8倍ではなく約4倍（表面の近くだけ持つため）",
        x_label="升目を半分にした回数", y_label="前の段からの倍率",
        y_range=(0, 9))
    line_chart(
        os.path.join(OUT, "094_gap.png"),
        [
            {"label": "元の形からのずれ 平均",
             "points": [(r["voxel"], r["gap_mean"]) for r in rows][::-1],
             "color": PALETTE[0]},
        ],
        title="細かくしてもずれは止まる（元の面の細かさが上限になる）",
        x_label="升目ひとつの大きさ", y_label="ずれ 平均")
    print("094_voxels.png 094_gap.png")


if __name__ == "__main__":
    chart_091()
    chart_092()
    chart_093()
    chart_094()
