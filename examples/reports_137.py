# -*- coding: utf-8 -*-
"""実験137 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "137_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    xs = d["x"]
    sm = d["smooth(0.0, 1.0, x)"]
    inner = [(x, v) for x, v in zip(xs, sm) if 0 <= x <= 1]
    sm_err = max(abs(v - (3 * x * x - 2 * x ** 3)) for x, v in inner)
    line_chart(os.path.join(OUT, "137_fit.png"),
               [{"label": "fit(x, 0, 1, 0, 10)", "points": list(zip(xs, d["fit(x, 0, 1, 0, 10)"])), "color": PALETTE[0]},
                {"label": "efit / lerp（同じ値）", "points": list(zip(xs, d["efit(x, 0, 1, 0, 10)"])),
                 "color": PALETTE[1], "dash": True},
                {"label": "smooth(0, 1, x) × 10", "points": [(x, v * 10) for x, v in zip(xs, sm)], "color": PALETTE[2]}],
               title="fit と smooth は 0〜1 の外で止まる。efit と lerp は伸び続ける",
               x_label="x", y_label="値")
    print("137_fit.png")

    def at(f, x):
        return d[f][xs.index(x)]

    same = d["efit(x, 0, 1, 0, 10)"] == d["lerp(0.0, 10.0, x)"]
    payload = {
        "title": "VEX の fit は範囲の外で止まり、efit と lerp は伸び続ける — smooth は 3x²−2x³",
        "summary":
            "x を −0.5〜1.5 まで振って、範囲を直す VEX の関数が、範囲の外でどうなるかを見た。\n\n"
            f"**fit() と fit01() は、範囲の外で止まる（クランプする）。** fit(x, 0, 1, 0, 10) は "
            f"x = −0.5 で {at('fit(x, 0, 1, 0, 10)', -0.5):g}、x = 1.5 で {at('fit(x, 0, 1, 0, 10)', 1.5):g}。\n\n"
            f"**efit() と lerp() は、止まらずに伸びる。** 同じ x で {at('efit(x, 0, 1, 0, 10)', -0.5):g} と "
            f"{at('efit(x, 0, 1, 0, 10)', 1.5):g}。この2つは全部の x で{'同じ値' if same else '違う値'}だった。"
            "範囲の外も比例で伸ばしたい（外挿したい）ときは efit を使う。\n\n"
            "**smooth(0, 1, x) は、0〜1 の中では 3x² − 2x³（スムーズステップ）と一致**"
            f"（ずれ最大 {sm_err:.6f}）し、外では 0 と 1 で止まる。両端でなめらかに止まる曲線。\n\n"
            "clamp(x, 0, 1) は、もちろん 0 と 1 で止まる。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "関数ごとの値（x = −0.5, 0, 0.5, 1, 1.5）",
             "note": "",
             "images": [{"path": "137_fit.png",
                         "caption": "fit（青）は 0 と 10 で止まり、efit・lerp（橙の破線）はまっすぐ伸びる。"}],
             "per_row": 1,
             "columns": ["関数", "x=−0.5", "x=0", "x=0.5", "x=1", "x=1.5", "範囲の外"],
             "rows": [[f] + [f"{at(f, x):g}" for x in (-0.5, 0.0, 0.5, 1.0, 1.5)] +
                      ["止まる" if at(f, -0.5) == at(f, 0.0) else "伸びる"]
                      for f in d if f != "x"]},
        ],
        "notes": [
            "<strong>fit はクランプする。</strong>範囲の外の値を残したいなら efit。",
            "<strong>efit と lerp は同じ直線。</strong>書きやすい方を使えばよい。",
            "<strong>smooth は 3x²−2x³。</strong>端でなめらかに止めたいマスクに向く。",
        ],
        "next": ["fit の元の範囲を逆（1, 0）にしたときの振る舞い", "chramp（ランプ）の範囲の外"],
    }
    with open(os.path.join(OUT, "137_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 137_report.json")


if __name__ == "__main__":
    main()
