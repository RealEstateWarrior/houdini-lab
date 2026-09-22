# -*- coding: utf-8 -*-
"""実験187 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LAB = {"uniform": "Uniform", "scaledominant": "Scale Dominant", "curvaturedominant": "Curvature Dominant"}


def main():
    with open(os.path.join(OUT, "187_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "187_uneven.png"),
               [{"label": f"{LAB[m]}（細かい側 → 粗い側）", "points": [(0, r["r_left"]), (1, r["r_right"])], "color": PALETTE[i]}
                for i, m in enumerate(LAB) for r in rows if r["method"] == m and r["strength"] == 10.0],
               title="smooth（Strength 10）: 点の細かい左半分（0）と粗い右半分（1）に残った半径",
               x_label="0 = 細かい側（36 点）、1 = 粗い側（12 点）", y_label="残った半径の平均")
    by = {(r["method"], r["strength"]): r for r in rows}
    u, s, c = by[("uniform", 10.0)], by[("scaledominant", 10.0)], by[("curvaturedominant", 10.0)]
    payload = {
        "title": "点の間隔がそろわない円では、smooth は粗い側を大きく縮める — 3つの Method の差は小さく、どれも丸さを保たない",
        "summary":
            "実験186 の続き。半径 1 の円の上に、左半分に 36 点・右半分に 12 点と偏らせて 48 点を置いた多角形に、"
            "Method を変えて smooth（Filter Quality 1）をかけた。\n\n"
            f"**粗い側ほど縮む。**Strength 10・Uniform で、細かい左半分の半径は {u['r_left']:.3f}、粗い右半分は {u['r_right']:.3f}。"
            f"丸かった形が、半径の差 {u['r_spread']:.3f} のゆがんだ形になった。点の間が広い所ほど、となりとの差（L）が大きいため"
            "（実験185・186 の式と同じ理由）。\n\n"
            f"**Scale Dominant と Curvature Dominant は、ほぼ同じ結果**（半径の平均 {s['r_mean']:.6f} と {c['r_mean']:.6f}）。"
            f"Uniform より点の動きが少し小さい（平均 {u['moved']:.4f} → {s['moved']:.4f}）が、左右の差はむしろ少し大きい（{u['r_spread']:.3f} → {s['r_spread']:.3f}）。\n\n"
            f"**Strength 1 なら、どれも差はわずか**（半径の差 {by[('uniform', 1.0)]['r_spread']:.3f}〜{by[('scaledominant', 1.0)]['r_spread']:.3f}）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Method・Strength と形",
            "images": [{"path": "187_uneven.png", "caption": "どの Method も右（粗い側）で大きく下がる。"}],
            "per_row": 1,
            "columns": ["Method", "Strength", "半径の平均", "細かい側", "粗い側", "半径の差（最大 − 最小）", "点の動きの平均"],
            "rows": [[LAB[r["method"]], f"{r['strength']:g}", f"{r['r_mean']:.5f}", f"{r['r_left']:.5f}", f"{r['r_right']:.5f}",
                      f"{r['r_spread']:.5f}", f"{r['moved']:.5f}"] for r in rows]}],
        "notes": [
            "<strong>smooth の前に、点の間隔をそろえる。</strong>resample や remesh で細かさをそろえないと、粗い所だけ形が崩れる。",
            "<strong>Method を変えても、この偏りはほとんど直らない。</strong>",
            "<strong>弱い Strength（1）なら、偏りはほぼ目立たない。</strong>",
        ],
        "next": ["resample でそろえてから smooth したときの形", "面（2次元の網）での Method の違い"],
    }
    with open(os.path.join(OUT, "187_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 187_report.json")


if __name__ == "__main__":
    main()
