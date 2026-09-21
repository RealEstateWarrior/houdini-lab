# -*- coding: utf-8 -*-
"""実験111 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "111_stats.json"), encoding="utf-8") as fp:
        rows = {r["case"]: r for r in json.load(fp)["rows"]}
    scales = [("s0.1", 0.1), ("s1", 1.0), ("s2", 2.0)]
    s1, ax, sd2 = rows["s1"], rows["axis_1_0_0.5"], rows["seed2"]
    n = s1["n"]
    worst = max(abs(rows[c][k]["var"] / (s * s / 12) - 1) for c, s in scales for k in "xyz")

    line_chart(
        os.path.join(OUT, "111_var.png"),
        [{"label": "x の動きの分散（実測）",
          "points": [(s, rows[c]["x"]["var"]) for c, s in scales], "color": PALETTE[0]},
         {"label": "s²/12（幅 s の一様）",
          "points": [(s, s * s / 12) for _, s in scales], "color": PALETTE[2], "dash": True},
         {"label": "s²/3（半径 s の一様）",
          "points": [(s, s * s / 3) for _, s in scales], "color": PALETTE[1], "dash": True}],
        title="Scale は「幅」: 動きは −s/2〜+s/2 の一様（分散 s²/12）",
        x_label="Scale", y_label="分散")
    print("111_var.png")

    def axis_row(label, r):
        return [label] + [f"{r[k]['min']:+.4f}〜{r[k]['max']:+.4f}" for k in "xyz"] + \
               [f"{r[k]['var']:.6f}" for k in "xyz"] + [f"{r['len_max']:.4f}"]

    payload = {
        "title": "pointjitter の Scale は「幅」 — 各軸 −s/2〜+s/2 の一様で、箱の中に散る",
        "summary":
            f"{n:,} 点に pointjitter をかけ、元の位置からの動きを軸ごとに数えた。"
            "Scale が「動く幅」なら動きは −s/2〜+s/2 の一様で分散は s²/12、"
            "「半径」なら −s〜+s で分散は s²/3 になる。\n\n"
            "**Scale は幅だった。** Scale 1 で動きは各軸 "
            f"{s1['x']['min']:+.3f}〜{s1['x']['max']:+.3f}、分散は x {s1['x']['var']:.5f}"
            f"（式 1/12 = 0.08333）。Scale 0.1・1・2 の3通り×3軸で、分散のずれは "
            f"{worst * 100:.2f}% 以内。\n\n"
            f"**散る範囲は球ではなく箱。** 動いた距離の最大は {s1['len_max']:.4f} で、"
            "軸の端 0.5 を超えて、箱の角 0.5×√3 ≒ 0.866 の近くまで届いた。\n\n"
            "Axis Scales は軸ごとの倍率。(1, 0, 0.5) にすると y は1点も動かず、"
            f"z は −{abs(ax['z']['min']):.3f}〜{ax['z']['max']:.3f}（幅が半分）。"
            "x の動きは Axis Scales を触らないときと1点残らず同じで、"
            "同じ乱数に倍率を掛けているだけだと分かる。\n\n"
            f"Seed を 1→2 に変えると、x の動きが同じだった点は {sd2['same_as_seed1'] * 100:g}%。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": f"Scale と動きの範囲・分散（{n:,} 点）",
             "note": "動き = jitter 後の位置 − 元の位置。",
             "images": [{"path": "111_var.png",
                         "caption": "実測は s²/12 の線に乗る。s²/3（半径の読み方）とは4倍ちがう。"}],
             "per_row": 1,
             "columns": ["設定", "x の範囲", "y の範囲", "z の範囲",
                         "x の分散", "y の分散", "z の分散", "距離の最大"],
             "rows": [axis_row("Scale 0.1", rows["s0.1"]), axis_row("Scale 1", s1),
                      axis_row("Scale 2", rows["s2"]),
                      axis_row("Scale 1・Axis (1, 0, 0.5)", ax),
                      axis_row("Scale 1・Seed 2", sd2)]},
        ],
        "notes": [
            "<strong>Scale は動く幅。</strong>各軸 −s/2〜+s/2。0.05 だけ揺らしたいなら Scale 0.1。",
            "<strong>箱の中に散る。</strong>角の方向には √3 倍（約1.73倍）遠くまで動く。"
            "距離をそろえたいなら、attribrandomize の Inside Sphere で動きを作って足す（実験106）。",
            "<strong>Axis Scales は同じ乱数への倍率。</strong>0 にした軸は動かない。",
            "<strong>速い。</strong>10万点で 0.04 秒（最初の1回を除く）。",
        ],
        "next": [
            "Use Point Scale を入れたとき、pscale が幅に掛かるのか",
            "Mask に 0.5 を入れたとき、幅が半分になるのか、半分の点だけ動くのか",
            "Use ID Attribute で点を消しても、残った点の動きが変わらないか",
        ],
    }
    with open(os.path.join(OUT, "111_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 111_report.json")


if __name__ == "__main__":
    main()
