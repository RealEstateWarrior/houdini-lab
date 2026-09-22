# -*- coding: utf-8 -*-
"""実験173 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

METHODS = ["VEX（点ごと）", "VEX（Detail でループ）", "Python（まとめて書く）", "Python（1点ずつ）"]


def main():
    with open(os.path.join(OUT, "173_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "173_speed.png"),
               [{"label": m, "points": [(math.log10(r["points"]), math.log10(r["sec"] * 1000)) for r in rows if r["method"] == m],
                 "color": PALETTE[i]} for i, m in enumerate(METHODS)],
               title="同じ計算（@P.y = sin·cos）の時間。縦は log10（ミリ秒）、横は log10（点の数）",
               x_label="log10（点の数）", y_label="log10（ミリ秒）")
    by = {(r["points"], r["method"]): r for r in rows}
    big = 1000000
    v, dl, pb = by[(big, METHODS[0])], by[(big, METHODS[1])], by[(big, METHODS[2])]
    pe = by[(99856, METHODS[3])]
    diff = max(r["max_diff"] for r in rows)
    payload = {
        "title": "同じ計算でも VEX（点ごと）は Detail のループの約170倍、Python の約260倍速い — 100 万点で 1.3 ミリ秒",
        "summary":
            "grid の点に @P.y = sin(@P.x·10)·cos(@P.z·10)·0.1 を入れる計算を4通りで書き、1 万・10 万・100 万点で時間をはかった"
            "（2〜3 回の一番速い値。1 回目の組み立ては先に済ませた）。\n\n"
            f"**VEX を点ごと（Run Over = Points）に流すのが圧倒的に速い。**100 万点で {v['sec'] * 1000:.2f} ミリ秒（1 点あたり {v['us_per_point'] * 1000:.1f} ナノ秒）。"
            "点ごとに分けて、いくつもの計算を同時に進めているとみられる（確かめていない）。\n\n"
            f"**同じ VEX でも、Detail で1回だけ走らせて for ループで回すと、100 万点で {dl['sec'] * 1000:.0f} ミリ秒（{dl['sec'] / v['sec']:.0f} 倍）。**"
            "ループが1本の流れで順に回り、同時に進められないためとみられる。\n\n"
            f"**Python は、値をまとめて読み書きしても 100 万点で {pb['sec'] * 1000:.0f} ミリ秒（VEX の {pb['sec'] / v['sec']:.0f} 倍）。**"
            f"点を1つずつ setPosition すると、さらに約 {pe['us_per_point'] / by[(99856, METHODS[2])]['us_per_point']:.1f} 倍遅い（10 万点で {pe['sec'] * 1000:.0f} ミリ秒）。\n\n"
            f"**結果はどれも同じ**（y の差は最大 {diff:.1e}。Python は倍精度で計算して単精度に書くための差）。\n\n"
            "**はかり方の注意:** cook(force=True) だけでは VEX のノードが計算し直さず、どれも 0.00001 秒と出た。"
            "コードが読むつまみ（ch('k')）を毎回わずかに変えて、計算し直させてからはかった。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "書き方・点の数と時間",
            "images": [{"path": "173_speed.png", "caption": "VEX（点ごと・青）だけが桁違いに下。Detail のループ（橙）は Python（緑）と同じくらい。"}],
            "per_row": 1,
            "columns": ["点の数", "書き方", "秒", "1 点あたり（マイクロ秒）", "結果の差"],
            "rows": [[f"{r['points']:,}", r["method"], f"{r['sec']:.5f}", f"{r['us_per_point']:.4f}", f"{r['max_diff']:.1e}"] for r in rows]}],
        "notes": [
            "<strong>点ごとの計算は、Run Over = Points の wrangle で書く。</strong>Detail でループすると同時に進められず、約170倍遅い。",
            "<strong>Python で書くなら、値をまとめて読み書きする。</strong>1点ずつより約6倍速い。",
            "<strong>時間をはかるときは、本当に計算し直しているか確かめる。</strong>cook(force=True) だけでは VEX は計算し直さなかった。",
        ],
        "next": ["Run Over = Primitives と Points の違い", "point() で他の点を読むときの遅さ"],
    }
    with open(os.path.join(OUT, "173_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 173_report.json", round(dl["sec"] / v["sec"]), round(pb["sec"] / v["sec"]))


if __name__ == "__main__":
    main()
