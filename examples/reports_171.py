# -*- coding: utf-8 -*-
"""実験171 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "171_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    kinds = ["curlnoise", "curlxnoise", "noise（ふつう）"]
    line_chart(os.path.join(OUT, "171_div.png"),
               [{"label": k, "points": [(r["freq"], math.log10(r["ratio"])) for r in rows if r["kind"] == k], "color": PALETTE[i]}
                for i, k in enumerate(kinds)],
               title="発散の大きさ ÷ 速さの微分の大きさ（縦は log10。−4 なら 1 万分の 1）",
               x_label="ノイズの周波数（P に掛ける数）", y_label="log10（比）")
    by = {(r["kind"], r["freq"]): r for r in rows}
    c1, c4 = by[("curlnoise", 1.0)], by[("curlnoise", 4.0)]
    n1 = by[("noise（ふつう）", 1.0)]
    x1 = by[("curlxnoise", 1.0)]
    payload = {
        "title": "curlnoise() はほぼ湧き出しのない流れ — 発散は、ふつうのノイズの約 3.5 万分の 1（周波数 1）",
        "summary":
            "1 × 1 × 1 の中の 20³ = 8,000 点で、VEX の curlnoise(P·f)・curlxnoise(P·f)・vector(noise(P·f)) の値を中心差分（h = 0.001）で微分し、"
            "発散（∂vx/∂x + ∂vy/∂y + ∂vz/∂z）を出した。比べやすいように、発散の平均の大きさを、速さの微分の大きさ（|∂vx/∂x| などの平均）で割った。\n\n"
            f"**curlnoise の発散は、ほぼ 0。**周波数 1 で比は {c1['ratio']:.1e}（1 万分の 0.5）、周波数 4 で {c4['ratio']:.1e}。"
            f"ふつうのベクトルノイズは {n1['ratio']:.2f} で、発散が速さの微分と同じくらいの大きさになる。"
            f"周波数 1 で比べると、curlnoise の発散は {n1['ratio'] / c1['ratio']:,.0f} 分の 1。\n\n"
            "**周波数を上げると、少し発散が出てくる。**curlnoise は中でも微分を近似して回転を作っているとみられ、細かい模様ほど"
            "その近似の誤差が表に出る、と考えられるが、確かめていない（こちらの h = 0.001 の差分の誤差も含まれる）。\n\n"
            f"**curlxnoise は平均では小さいが、ところどころ大きく跳ねる。**周波数 1 で平均の比は {x1['ratio']:.1e} なのに、"
            f"いちばん大きい発散は {x1['max_abs_div']:.2f}（curlnoise は {c1['max_abs_div']:.1e}）。模様の中に急に変わる所がある。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "ノイズと発散",
            "images": [{"path": "171_div.png", "caption": "curlnoise（青）はふつうのノイズ（緑）より 3〜4 桁小さい。"}],
            "per_row": 1,
            "columns": ["関数", "周波数", "点", "|発散| の平均", "|発散| の最大", "速さの微分の大きさ", "比", "速さの平均", "秒"],
            "rows": [[r["kind"], f"{r['freq']:g}", f"{r['points']:,}", f"{r['mean_abs_div']:.2e}", f"{r['max_abs_div']:.2e}",
                      f"{r['mean_grad']:.4f}", f"{r['ratio']:.2e}", f"{r['mean_speed']:.4f}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>粒を流して「かたまりのまま渦を巻く」動きにしたいなら curlnoise。</strong>湧き出し・吸い込みがほぼ無いので、粒は1点に集まらない（実験172 で、混み具合がほぼ保たれるのを確かめた）。",
            "<strong>ふつうの noise を速さに使うと、湧き出しと吸い込みができる。</strong>粒が固まったり散ったりする。",
            "<strong>curlxnoise は、ところどころ発散が大きい。</strong>なめらかさが要るなら curlnoise。",
        ],
        "next": ["curlnoise で流した粒の密度が本当に保たれるか", "curlnoise2d（2次元）の発散"],
    }
    with open(os.path.join(OUT, "171_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 171_report.json", round(n1["ratio"] / c1["ratio"]))


if __name__ == "__main__":
    main()
