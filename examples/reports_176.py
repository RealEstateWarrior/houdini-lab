# -*- coding: utf-8 -*-
"""実験176 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "176_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "176_element.png"),
               [{"label": f"Fractal {f}", "points": [(math.log2(r["size_over_element"]), r["range_over_amp"]) for r in rows if r["fractal"] == f],
                 "color": PALETTE[i]} for i, f in enumerate(("none", "hmfT"))],
               title="heightfield_noise（1000×1000・Amplitude 1000）: 高さの幅 ÷ Amplitude と、地面に入る模様の数（横は log2）",
               x_label="log2（地面の幅 ÷ Element Size）", y_label="幅 ÷ Amplitude")
    by = {(r["fractal"], r["element"]): r for r in rows}
    payload = {
        "title": "heightfield_noise の高さの幅は、地面に入る模様の数で決まる — Element Size を地面の 1/20 にすると Amplitude の 6 割",
        "summary":
            "実験168 の続き。1000 × 1000 の heightfield に heightfield_noise（Amplitude 1000、Center Noise 入）をかけ、Element Size を 50〜2000 と変えて、"
            "高さの幅（最高 − 最低）÷ Amplitude を測った。\n\n"
            "**地面に模様がたくさん入るほど、幅は Amplitude に近づく。**Fractal なしで、地面の幅 ÷ Element Size が "
            f"0.5 なら {by[('none', 2000.0)]['range_over_amp'] * 100:.0f}%、1 なら {by[('none', 1000.0)]['range_over_amp'] * 100:.0f}%、"
            f"2（実験168）なら {by[('none', 500.0)]['range_over_amp'] * 100:.0f}%、4 なら {by[('none', 250.0)]['range_over_amp'] * 100:.0f}%、"
            f"10 なら {by[('none', 100.0)]['range_over_amp'] * 100:.0f}%、20 なら {by[('none', 50.0)]['range_over_amp'] * 100:.0f}%。"
            "模様が少ないと、ノイズの高い山や深い谷に当たる前に地面が終わる。\n\n"
            f"**標準偏差 ÷ Amplitude は、模様が 10 個を超えると約 7% で落ち着く**（10 で {by[('none', 100.0)]['sd_over_amp'] * 100:.1f}%、"
            f"20 で {by[('none', 50.0)]['sd_over_amp'] * 100:.1f}%）。幅は広がり続けるが、ならした高さのばらつきは頭打ちになる。\n\n"
            "**hmfT（既定）も同じ傾向。**模様が多いときは Fractal なしより幅が少し狭い（20 個で "
            f"{by[('hmfT', 50.0)]['range_over_amp'] * 100:.0f}%）、少ないときは広い。\n\n"
            "**20 個入っても、幅は Amplitude の 6 割どまり。**Amplitude は「山と谷の差」ではなく、ノイズの値に掛ける数とみられる。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Element Size と高さ",
            "images": [{"path": "176_element.png", "caption": "模様の数を倍にするたびに幅が広がる。"}],
            "per_row": 1,
            "columns": ["Fractal", "Element Size", "地面 ÷ Element Size", "幅 ÷ Amplitude", "標準偏差 ÷ Amplitude", "最低", "最高", "平均", "秒"],
            "rows": [[r["fractal"], f"{r['element']:g}", f"{r['size_over_element']:g}", f"{r['range_over_amp']:.4f}", f"{r['sd_over_amp']:.4f}",
                      f"{r['min']:g}", f"{r['max']:g}", f"{r['mean']:g}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>欲しい高さの幅から Amplitude を決めるときは、Element Size も一緒に見る。</strong>同じ Amplitude でも幅は 7〜62%。",
            "<strong>Element Size を小さくすると、同じ Amplitude でも山が高くなる。</strong>細かい起伏を足したつもりが、高さも変わる。",
            "<strong>平均も揺れる。</strong>模様が少ないと、Center Noise 入でも平均が 0 から数十ずれる。",
        ],
        "next": ["地面の広さを変えずに、点の細かさ（Grid Spacing）を変えたとき", "heightfield_remap で幅をそろえる"],
    }
    with open(os.path.join(OUT, "176_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 176_report.json")


if __name__ == "__main__":
    main()
