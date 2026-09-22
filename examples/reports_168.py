# -*- coding: utf-8 -*-
"""実験168 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "168_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "168_amp.png"),
               [{"label": f"Fractal {f}・Center Noise 入", "points": [(r["amp"], r["range"]) for r in rows if r["fractal"] == f and r["center"] == 1],
                 "color": PALETTE[i]} for i, f in enumerate(("none", "hmfT"))]
               + [{"label": "Amplitude そのもの", "points": [(a, a) for a in (100.0, 500.0, 1000.0)], "color": PALETTE[4], "dash": True}],
               title="heightfield_noise（1000×1000・Element Size 500）: 高さの幅（最高 − 最低）と Amplitude",
               x_label="Amplitude", y_label="高さの幅")
    by = {(r["fractal"], r["center"], r["amp"]): r for r in rows}
    shift = [round(by[(f, 0, a)]["mean"] - by[(f, 1, a)]["mean"], 3) for f in ("none", "hmfT") for a in (100.0, 500.0, 1000.0)]
    n1, h1 = by[("none", 1, 1000.0)], by[("hmfT", 1, 1000.0)]
    payload = {
        "title": "heightfield_noise の Amplitude は高さの幅ではない — 幅は Amplitude の 23〜29%、Center Noise を切ると Amplitude の半分だけ上がる",
        "summary":
            "1000 × 1000 の heightfield（Grid Spacing 4、250 × 250 の升）に heightfield_noise（Combine = Replace、Element Size 500、Noise Type は既定）を"
            "かけ、height の升の値から最小・最大・平均・標準偏差を数えた。\n\n"
            f"**高さの幅（最高 − 最低）は Amplitude よりずっと小さい。**Fractal なしで Amplitude の {n1['range_over_amp'] * 100:.1f}%、"
            f"既定の hmfT で {h1['range_over_amp'] * 100:.1f}%。Amplitude 1000 でも、山と谷の差は {n1['range']:.0f}〜{h1['range']:.0f}。"
            "この大きさの地面（Element Size と同じくらいの範囲）では、ノイズの山の高いところまで届かないとみられるが、確かめていない。\n\n"
            "**高さは Amplitude にぴったり比例する。**幅 ÷ Amplitude、標準偏差 ÷ Amplitude は、100・500・1000 のどれでも4桁同じ"
            f"（標準偏差は Amplitude の {n1['sd_over_amp'] * 100:.2f}%・{h1['sd_over_amp'] * 100:.2f}%）。同じ模様を縦に伸ばしているだけ。\n\n"
            f"**Center Noise を切ると、全体がちょうど Amplitude の半分だけ上がる。**平均の差は {', '.join(f'{s:g}' for s in shift)}"
            "（Amplitude 100・500・1000 の順、Fractal なし・hmfT）。入れると平均が 0 のまわりに来る（ぴったり 0 ではない）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Fractal・Center Noise・Amplitude と高さ",
            "images": [{"path": "168_amp.png", "caption": "高さの幅は、点線（Amplitude）の 1/4 ほどの傾きの直線になる。"}],
            "per_row": 1,
            "columns": ["Fractal", "Center Noise", "Amplitude", "最低", "最高", "幅", "幅 ÷ Amplitude", "平均", "標準偏差 ÷ Amplitude", "秒"],
            "rows": [[r["fractal"], "入" if r["center"] else "切", f"{r['amp']:g}", f"{r['min']:g}", f"{r['max']:g}", f"{r['range']:g}",
                      f"{r['range_over_amp']:.4f}", f"{r['mean']:g}", f"{r['sd_over_amp']:.4f}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>欲しい高さの幅から Amplitude を決めるなら、約4倍（hmfT なら約3.4倍）にする。</strong>この大きさ・Element Size のとき。",
            "<strong>Amplitude を倍にすると、地形はそのまま縦に倍。</strong>形は変わらない。",
            "<strong>Center Noise を切ると、地面が Amplitude/2 だけ持ち上がる。</strong>海面の高さを決めるときに効く。",
        ],
        "next": ["Element Size を変えたときの幅 ÷ Amplitude", "heightfield_erode で高さの合計（土の量）が保たれるか"],
    }
    with open(os.path.join(OUT, "168_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 168_report.json", shift)


if __name__ == "__main__":
    main()
