# -*- coding: utf-8 -*-
"""実験172 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "172_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "172_crowd.png"),
               [{"label": "半径 0.05 の中の粒の数（平均）", "points": [(i, r["mean_nb"]) for i, r in enumerate(rows)], "color": PALETTE[0]},
                {"label": "ばらつき（変動係数）× 10", "points": [(i, r["cv"] * 10) for i, r in enumerate(rows)], "color": PALETTE[1]}],
               title="粒の混み具合（0 撒いた直後 / 1 curlnoise で流した後 / 2 ふつうのノイズで流した後）",
               x_label="0 撒いた直後 / 1 curlnoise / 2 noise", y_label="値")
    s0, c, n = rows
    payload = {
        "title": "curlnoise で流した粒は混み具合をほぼ保つ — ふつうのノイズで流すと、平均で2倍以上に固まる",
        "summary":
            "1 × 1 × 1 の立方体に一様に 20,000 粒を撒き、v = curlnoise(P·2) と v = vector(noise(P·2)) − 0.5 で 60 ステップ（1 ステップ 0.02）動かした。"
            "混み具合は「半径 0.05 の中にいる他の粒の数」で測り、最初に中心寄り（|x|, |y|, |z| < 0.3）にいた "
            f"{s0['inner']:,} 粒だけで比べた（実験171 の次の課題）。\n\n"
            f"**curlnoise のあとも、混み具合はほぼ撒いた直後のまま。**平均 {s0['mean_nb']:.2f} → {c['mean_nb']:.2f}（{(c['mean_nb'] / s0['mean_nb'] - 1) * 100:+.0f}%）、"
            f"ばらつき（変動係数）{s0['cv']:.2f} → {c['cv']:.2f}。粒は平均 {c['moved']:.2f} 動いているのに、詰まりも薄まりもほとんどしない。\n\n"
            f"**ふつうのノイズでは、粒が固まった。**平均 {n['mean_nb']:.1f}（{n['mean_nb'] / s0['mean_nb']:.1f} 倍）、変動係数 {n['cv']:.2f}、"
            f"いちばん混んだ粒のまわりには {n['max']} 粒。動いた距離は平均 {n['moved']:.2f} と curlnoise より短いのに、吸い込みのある所へ集まる。\n\n"
            "**最初の測り方はやめた。**立方体を升に分けて1升の粒の数を数える方法では、粒の群れ全体の形が変わるだけで空の升が増え、"
            "混み具合の変化と区別できなかった（curlnoise の方がばらついて見えた）。まわりの粒の数で測ると、この影響が入らない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "流す前と後の混み具合（中心寄りの粒）",
            "images": [{"path": "172_crowd.png", "caption": "curlnoise（1）は撒いた直後（0）とほぼ同じ。ふつうのノイズ（2）で跳ね上がる。"}],
            "per_row": 1,
            "columns": ["", "比べた粒", "まわりの粒の数（平均）", "一様なら", "変動係数", "最大", "最小", "動いた距離の平均", "秒"],
            "rows": [[r["kind"], f"{r['inner']:,}", f"{r['mean_nb']:.2f}", f"{r['expect']:g}", f"{r['cv']:.3f}", r["max"], r["min"],
                      f"{r['moved']:.3f}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>粒を渦で流すなら curlnoise。</strong>60 ステップ動かしても、混み具合の平均は 7% しか変わらなかった。",
            "<strong>ふつうのノイズを速さにすると、粒は吸い込みへ集まる。</strong>平均で 2.3 倍に混む。",
            "<strong>混み具合は「まわりの粒の数」で測る。</strong>升に分けて数えると、群れの形の変化が混ざる。",
        ],
        "next": ["ステップを細かくしたとき、curlnoise の 7% の減りが縮むか", "popcurlnoise（POP の力）で流したとき"],
    }
    with open(os.path.join(OUT, "172_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 172_report.json")


if __name__ == "__main__":
    main()
