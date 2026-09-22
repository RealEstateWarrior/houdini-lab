# -*- coding: utf-8 -*-
"""実験161 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def falloff(x, d, b):
    if x <= d:
        return 1.0
    if b <= 0 or x >= d + b:
        return 0.0
    t = (x - d) / b
    return (1 - t * t) ** 2


def main():
    with open(os.path.join(OUT, "161_stats.json"), encoding="utf-8") as fp:
        dd = json.load(fp)
    rows, prof = dd["rows"], dd["profiles"]
    worst = 0.0
    for key, pts in prof.items():
        d = float(key.split("_")[0][1:])
        b = float(key.split("_")[1][1:])
        for x, v in pts:
            worst = max(worst, abs(v - falloff(x, d, b)))
    series = []
    for i, key in enumerate(("d0.5_b0", "d0.5_b0.25", "d0.5_b0.5", "d1_b0.5")):
        series.append({"label": key.replace("d", "Threshold ").replace("_b", "・Blend "), "points": prof[key], "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "161_blend.png"), series,
               title="attribtransfer: 原点の 1 点から運ばれた val と距離",
               x_label="渡す点からの距離", y_label="受け取った val")
    payload = {
        "title": "attribtransfer は Distance Threshold までそのまま運び、Blend Width の外側で (1 − t²)² に落とす",
        "summary":
            "x = 0〜2 に 0.01 刻みで並べた 201 点へ、原点の 1 点から val = 1 を attribtransfer で運んだ。"
            "Distance Threshold（d）と Blend Width（b）を変え、距離ごとに受け取った値を読んだ。\n\n"
            "**d までは 1 のまま、d から d + b で 0 まで下がる。**弱まる区間は Threshold の内側ではなく外側に付く"
            "（d = 0.5・b = 0.25 で、0.5 まで 1、0.74 まで何か届き、0.75 から 0）。Blend Width = 0 なら d でぷつりと切れる。\n\n"
            f"**下がり方は直線ではなく (1 − t²)²（t = (距離 − d)/b）。**記録した点すべてで、この式との差は最大 {worst:.4f}。"
            "始まりはゆっくり、真ん中で急に、終わりはまたゆっくり 0 へ着く。t = 0.5 で 0.5625。\n\n"
            "**時間はほとんどかからない。**1回目だけ 0.09 秒（最初の組み立て）、あとは 0.0001 秒。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Threshold・Blend と、値の届き方",
            "images": [{"path": "161_blend.png", "caption": "どの線も Threshold までは 1。Blend の分だけ外へなだらかに伸びる。"}],
            "per_row": 1,
            "columns": ["Distance Threshold", "Blend Width", "1 のままの所まで", "届く所まで", "中間の点", "直線との差（最大）", "秒"],
            "rows": [[f"{r['threshold']:g}", f"{r['blend']:g}", f"{r['full_until']:g}", f"{r['reach_until']:g}", r["mid_points"],
                      f"{r['lin_err']:.4f}" if r["lin_err"] is not None else "—", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>Blend Width は Threshold の外に足される。</strong>届く距離は d + b。",
            "<strong>弱まり方は (1 − t²)²。</strong>直線より、端がなめらか。",
            "<strong>ここまでの結果は、渡す点が 1 つのとき。</strong>Max Sample Count を上げて複数の点を混ぜるときは別の話。",
        ],
        "next": ["Max Sample Count を上げたときの混ざり方（Kernel Function）", "面（primitive）から運ぶときの距離の測り方"],
    }
    with open(os.path.join(OUT, "161_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 161_report.json", worst)


if __name__ == "__main__":
    main()
