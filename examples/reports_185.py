# -*- coding: utf-8 -*-
"""実験185 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def model(n, S, q):
    L = 2 * (1 - math.cos(2 * math.pi / n))          # となりの平均との差の大きさ（ラプラシアンの固有値）
    return 1 / (1 + S * L ** q / math.comb(2 * q, q))


def main():
    with open(os.path.join(OUT, "185_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    worst = 0.0
    for r in rows:
        r["model"] = model(r["n"], r["strength"], r["quality"])
        worst = max(worst, abs(r["r"] - r["model"]))
    line_chart(os.path.join(OUT, "185_smooth.png"),
               [{"label": f"Filter Quality {q}（Strength 10）", "points": [(math.log2(r["n"]), r["r"]) for r in rows if r["quality"] == q and r["strength"] == 10.0],
                 "color": PALETTE[q - 1]} for q in (1, 2, 3)],
               title="smooth（Uniform・Strength 10）: 半径 1 の n 角形に残った半径（横は log2 n）",
               x_label="log2（点の数 n）", y_label="残った半径")
    by = {(r["n"], r["strength"], r["quality"]): r for r in rows}
    a = by[(12, 10.0, 1)]
    payload = {
        "title": "smooth の縮み方は r = 1/(1 + Strength·L^q/C(2q, q)) — 36 通りで6桁一致。Filter Quality を上げるほど形を保つ",
        "summary":
            "半径 1 の circle（Polygon、n 角形）に smooth（smooth::2.0、Method = Uniform、Constrained Boundary なし）をかけ、残った半径 r を測った。"
            "点の数 n・Strength S・Filter Quality q を変えた（36 通り）。\n\n"
            "**Filter Quality 1 では r = 1/(1 + S·(1 − cos θ))（θ = 2π/n）。**n = 12・S = 10 で "
            f"{a['r']:.7f}（式 {a['model']:.7f}）。となりの平均へ近づける計算を、1 回で「行き先から逆算して」解く形（陰的な1ステップ）になっている。"
            "S をいくら大きくしても、半径は 0 にはならない。\n\n"
            "**Filter Quality q を上げると、r = 1/(1 + S·L^q/C(2q, q))。**L = 2(1 − cos θ)（となりとの差の強さ）、C(2q, q) は二項係数（q = 1・2・3 で 2・6・20）。"
            f"36 通りすべてで、この式との差は最大 {worst:.0e}。ここで使った円では L は 1 より小さいので、q を上げるほど縮みにくくなる。"
            "細かいでこぼこ（L が大きい）は消し、なだらかな形（L が小さい）は残すフィルタになっている。\n\n"
            "**点の数が多いほど縮まない。**同じ Strength 10・Quality 1 で、n = 12 は "
            f"{by[(12, 10.0, 1)]['r']:.3f}、n = 96 は {by[(96, 10.0, 1)]['r']:.3f}。細かい網ほど、となりとの差が小さいため。\n\n"
            "**どの点も同じだけ縮む**（半径のばらつきは最大 1.3e-6）。形は円のまま小さくなる。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "点の数・Strength・Filter Quality と、残った半径",
            "images": [{"path": "185_smooth.png", "caption": "Quality 3（緑）は n = 24 でもほぼ縮まない。"}],
            "per_row": 1,
            "columns": ["n", "Strength", "Filter Quality", "残った半径", "式", "−ln r ÷ (1 − cos θ)", "点ごとの差", "秒"],
            "rows": [[r["n"], f"{r['strength']:g}", r["quality"], f"{r['r']:.7f}", f"{r['model']:.7f}",
                      f"{r['neg_ln_r_over_k']:g}" if r["neg_ln_r_over_k"] is not None else "—", f"{r['r_spread']:.1e}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>smooth は Strength をいくら上げても、ゼロまでは縮まない。</strong>1/(1 + S·…) の形。",
            "<strong>形を保ったまま細かいでこぼこだけ消したいなら Filter Quality を上げる。</strong>3 なら 96 角形の円はまったく縮まない。",
            "<strong>粗い網ほど縮む。</strong>同じ Strength でも、点が少ない所は形が大きく変わる。",
        ],
        "next": ["Scale Dominant・Curvature Dominant の縮み方", "開いた線（端が固定されない）での縮み方"],
    }
    with open(os.path.join(OUT, "185_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 185_report.json", worst)


if __name__ == "__main__":
    main()
