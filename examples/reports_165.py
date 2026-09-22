# -*- coding: utf-8 -*-
"""実験165 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "165_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, G = d["rows"], d["g"]
    worst_y = worst_v = 0.0
    for r in rows:
        h = 1 / 24 / r["substeps"]
        n = (r["frame"] - 1) * r["substeps"] + 1          # 生まれたフレームでも 1 ステップ進む
        r["n"] = n
        r["model_y"] = -G * h * h * n * (n + 1) / 2
        r["model_vy"] = -G * h * n
        worst_y = max(worst_y, abs(r["y"] - r["model_y"]))
        worst_v = max(worst_v, abs(r["vy"] - r["model_vy"]))
        r["err_pct"] = (r["y"] / r["exact_y"] - 1) * 100
    f25 = [r for r in rows if r["frame"] == 25]
    line_chart(os.path.join(OUT, "165_fall.png"),
               [{"label": "1 秒後の y の誤差（%）", "points": [(r["substeps"], r["err_pct"]) for r in f25], "color": PALETTE[0]}],
               title="POP（24 fps・重力 9.80665）: 1 秒後の落下量の、−½gt² に対する誤差と Substeps",
               x_label="DOP Network の Substeps", y_label="誤差 %")
    s1 = [r for r in f25 if r["substeps"] == 1][0]
    s8 = [r for r in f25 if r["substeps"] == 8][0]
    payload = {
        "title": "POP の粒は、生まれたフレームで 1 ステップ先に進む — 1 秒後の落下は Substeps 1 で 13% 多く、誤差は Substeps に反比例して縮む",
        "summary":
            "原点の 1 点から、最初のフレームにだけ 1 粒を生み（初速 0）、popsolver の後ろに gravity（−9.80665）をつないだ。"
            "24 fps で、フレーム 2・13・25（生まれてから 1/24 秒・0.5 秒・1 秒）の y と v.y を読んだ。\n\n"
            f"**粒は「生まれたフレームのうちに、もう 1 ステップ」進んでいる。**Substeps 1・フレーム 25 の v.y は {s1['vy']:.4f}"
            f"（1 秒ぶんの −9.80665 ではなく、1 + 1/24 秒ぶん）。進んだステップ数を n = (フレーム − 1) × Substeps + 1、1 ステップ h = 1/(24 × Substeps) とすると、"
            f"12 通りすべてで v.y = −g·h·n（差は最大 {worst_v:.0e}）、y = −g·h²·n(n + 1)/2（差は最大 {worst_y:.0e}）と合った。"
            "「速さを先に足し、その速さで位置を進める」やり方（半陰的オイラー）。\n\n"
            f"**そのため、1 秒後の落下量は −½gt² より多い。**Substeps 1 で {s1['y']:.4f}（正しい値 {s1['exact_y']:.4f} より {s1['err_pct']:+.1f}%）。"
            f"Substeps を倍にするたびに誤差はほぼ半分になり、8 で {s8['err_pct']:+.1f}%。誤差のもとは、生まれた瞬間の1ステップと、1ステップごとの足し方の2つ。\n\n"
            "**時間はどれも 25 フレームで 0.3〜0.4 秒。**粒が1つなので、Substeps を増やしても重さはほとんど変わらない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Substeps・フレームと、落ちた量",
            "images": [{"path": "165_fall.png", "caption": "誤差は Substeps に反比例して縮む（1 で +12.8%、8 で +1.6%）。"}],
            "per_row": 1,
            "columns": ["Substeps", "フレーム", "経った時間", "ステップ数 n", "y", "−g·h²·n(n+1)/2", "−½gt²", "誤差", "v.y", "−g·h·n", "25 フレームの秒"],
            "rows": [[r["substeps"], r["frame"], f"{r['t']:.4f}", r["n"], f"{r['y']:.6f}", f"{r['model_y']:.6f}", f"{r['exact_y']:.6f}",
                      f"{r['err_pct']:+.1f}%", f"{r['vy']:.6f}", f"{r['model_vy']:.6f}", f"{r['sec_25f']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>POP の落下は、正しい放物線より少し先を行く。</strong>1 秒で Substeps 1 なら +13%。",
            "<strong>正確に合わせたいなら Substeps を上げる。</strong>誤差はほぼ 1/Substeps。",
            "<strong>生まれたフレームでもう 1 ステップ進む。</strong>生まれた直後の位置が、生みの点からずれている理由。",
        ],
        "next": ["popdrag（空気抵抗）を入れたときの終端速度", "popsolver 側の Substeps との違い"],
    }
    with open(os.path.join(OUT, "165_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 165_report.json", worst_y, worst_v, [round(r["err_pct"], 2) for r in f25])


if __name__ == "__main__":
    main()
