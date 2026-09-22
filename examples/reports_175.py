# -*- coding: utf-8 -*-
"""実験175 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "175_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, tracks, W = d["rows"], d["tracks"], d["wind"]
    worst = 0.0
    for key, tr in tracks.items():
        k = float(key.split("_")[0][1:])
        for i, v in enumerate(tr):
            t = i / 24
            worst = max(worst, abs(v - (W - W / (1 + W * k * t))))
    line_chart(os.path.join(OUT, "175_wind.png"),
               [{"label": f"Air Resistance {k:g}", "points": [(i / 24, v) for i, v in enumerate(tracks[f'k{k:g}_s1'])], "color": PALETTE[i]}
                for i, k in enumerate((0.5, 1.0, 2.0))]
               + [{"label": "風の速さ 5", "points": [(0, W), (3, W)], "color": PALETTE[4], "dash": True}],
               title="popwind（風 5・重力なし）: 粒の速さ v.x の近づき方（Substeps 1）",
               x_label="秒", y_label="v.x")
    same = all(tracks[f"k{k:g}_s1"] == tracks[f"k{k:g}_s8"] for k in (0.5, 1.0, 2.0)) or \
        max(abs(a - b) for k in (0.5, 1.0, 2.0) for a, b in zip(tracks[f"k{k:g}_s1"], tracks[f"k{k:g}_s8"])) < 1e-5
    k1 = [r for r in rows if r["k"] == 1.0 and r["substeps"] == 1][0]
    payload = {
        "title": "popwind の粒は、風との速さの差が 5/(1 + 5·k·t) で縮む — 差の2乗に比例する抵抗を、Substeps によらずぴったり解いている",
        "summary":
            "1 粒（初速 0、重力なし）に popwind（Wind Velocity = (5, 0, 0)、Wind Speed 1）をつなぎ、Air Resistance k と Substeps を変えて v.x を毎フレーム読んだ。\n\n"
            f"**風との差 u は、u = 5 / (1 + 5·k·t) どおりに縮んだ。**3 通りの k・73 フレームのすべてで、この式との差は最大 {worst:.0e}。"
            f"k = 1 なら 1 秒後に v.x = {k1['vx_1s']:.6f}（= 5 − 5/6）。差が半分になるのは t = 1/(5k)（k = 1 で 0.2 秒 = 約 5 フレーム）で、"
            "そこからさらに半分になるには倍の時間がかかる。差に比例する抵抗（指数で縮む）ではなく、差の2乗に比例する抵抗の形。\n\n"
            f"**Substeps 1 と 8 で、速さは同じだった**（{'差は 0.00001 未満' if same else '違いがあった'}）。1 ステップごとに、この式を近似せずに解いているとみられる。"
            "実験166 の popdrag（重力と組み合わせると Substeps で結果が変わった）とは違う。\n\n"
            "**生まれたフレームの余分な 1 ステップも無い。**フレーム 25（1 秒後）の値が t = 1 の式とそのまま合う（実験165 の重力では t + 1/24 になった）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Air Resistance・Substeps と速さ",
            "images": [{"path": "175_wind.png", "caption": "どの k も、点線の 5 にゆっくり近づく（半分になる時間がだんだん延びる）。"}],
            "per_row": 1,
            "columns": ["Air Resistance", "Substeps", "1 秒後の v.x", "差の2乗の式", "差に比例の式", "3 秒後", "差が 1/2 のフレーム", "1/4", "1/8", "秒"],
            "rows": [[f"{r['k']:g}", r["substeps"], f"{r['vx_1s']:.6f}", f"{5 - 5 / (1 + 5 * r['k']):.6f}", f"{5 * (1 - 2.718281828 ** (-r['k'])):.6f}",
                      f"{r['vx_3s']:.6f}", r["half_frames"]["0.5"], r["half_frames"]["0.25"], r["half_frames"]["0.125"], f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>風に乗る速さは、最初は速く、あとはゆっくり。</strong>差が 1/2 → 1/4 → 1/8 になるのに、倍・倍の時間がかかる。",
            "<strong>Air Resistance を倍にすると、同じ所まで近づく時間は半分。</strong>",
            "<strong>popwind は Substeps を上げても変わらない。</strong>風だけなら Substeps で重くする必要はない。",
        ],
        "next": ["popwind と重力を一緒にかけたときの終端速度", "Wind Speed を変えたとき（Wind Velocity との掛け算か）"],
    }
    with open(os.path.join(OUT, "175_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 175_report.json", worst, same)


if __name__ == "__main__":
    main()
