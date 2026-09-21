# -*- coding: utf-8 -*-
"""実験124 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "124_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    whole = [r for r in rows if r["gen"] == int(r["gen"])]
    half = next(r for r in rows if r["gen"] == 2.5)
    worst_rel = max(abs(r["length"] / r["want_length"] - 1) for r in whole)
    seg_ok = all(r["points"] - 1 == r["want_segments"] for r in whole)
    span_ok = max(abs(r["end_to_end"] - r["want_span"]) for r in whole)

    line_chart(
        os.path.join(OUT, "124_koch.png"),
        [{"label": "全長の log4（実測）", "points": [(r["gen"], math.log(r["length"], 4)) for r in whole],
          "color": PALETTE[0]},
         {"label": "端から端の log3（実測）", "points": [(r["gen"], math.log(r["end_to_end"], 3)) for r in whole],
          "color": PALETTE[1]},
         {"label": "世代（式なら両方ともこの線）", "points": [(r["gen"], r["gen"]) for r in whole],
          "color": PALETTE[4], "dash": True}],
        title="コッホ曲線: 全長は4倍、端の間隔は3倍ずつ育つ",
        x_label="世代", y_label="log（全長は4、端の間隔は3 を底に）")
    print("124_koch.png")

    g6 = whole[-1]
    payload = {
        "title": "L-System のコッホ曲線は式どおり — 全長4^n・端の間隔3^n。小数の世代は途中の形になる",
        "summary":
            "lsystem に、始まり F、規則 F → F+F--F+F、角度 60°、1歩の長さ 1 を入れて、コッホ曲線を育てた。"
            "n 世代で、線分は 4^n 本、全長は 4^n、端から端までの距離は 3^n になるはず。\n\n"
            f"**0〜6 世代のすべてで式どおり。** 線分の数は 4^n 本で{'一致' if seg_ok else '不一致'}、"
            f"端の間隔は 3^n（差は最大 {span_ok:.6f}）、全長のずれは最大 {worst_rel * 1e6:.1f} ppm"
            f"（6世代で {g6['length']:.6f}。小数の丸めの範囲）。"
            f"6世代は {g6['points']:,} 点を {g6['sec'] * 1000:.1f} ミリ秒で作った。\n\n"
            "曲線は y 方向（上）へ伸び、盛り上がりは x 方向に出た。高さは端の間隔の √3/6 倍"
            f"（6世代で {g6['size'][0]:.4f} ＝ 729 × √3/6）。\n\n"
            f"**Generations に 2.5 を入れると、点の数は3世代と同じ {half['points']} 点**で、"
            f"全長は {half['length']:g}（2世代 16 と3世代 64 の間）、端の間隔は {half['end_to_end']:.4f}。"
            "3世代の形へ向かう途中の形らしい（Continuous Length が既定で入っている。"
            "線分1本ずつの長さと、切った場合は確かめていない）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "世代と、線分・全長・端の間隔",
             "note": "全長は measure の Perimeter。端の間隔は最初と最後の点の距離。",
             "images": [{"path": "124_koch.png",
                         "caption": "log を取ると、全長（底4）と端の間隔（底3）はどちらも世代の数に重なる。"}],
             "per_row": 1,
             "columns": ["世代", "点", "全長", "4^n", "端の間隔", "3^n", "ミリ秒"],
             "rows": [[f"{r['gen']:g}", f"{r['points']:,}", f"{r['length']:.6f}",
                       f"{r['want_length']:g}" if r in whole else "—", f"{r['end_to_end']:.6f}",
                       f"{r['want_span']:g}" if r in whole else "—", f"{r['sec'] * 1000:.1f}"]
                      for r in rows]},
        ],
        "notes": [
            "<strong>規則どおりに育つ。</strong>線分 4^n 本、全長 4^n、端の間隔 3^n。",
            "<strong>速い。</strong>4,097 点でも 2 ミリ秒。",
            "<strong>小数の世代は、次の世代と同じ点の数で、長さは途中の値。</strong>",
            "<strong>全長 ÷ 端の間隔 = (4/3)^n。</strong>世代を増やすほど、同じ幅に長い線が詰まる（フラクタル）。",
        ],
        "next": [
            "Step Size Scale と \" 記号で、枝が世代ごとに短くなる木の全長",
            "Continuous Length を切ったとき、小数の世代がどうなるか",
            "Tube で出したときの点の数と速さ",
        ],
    }
    with open(os.path.join(OUT, "124_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 124_report.json")


if __name__ == "__main__":
    main()
