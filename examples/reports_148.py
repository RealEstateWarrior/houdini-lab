# -*- coding: utf-8 -*-
"""実験148 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def f(n):
    return n * math.sin(2 * math.pi / n) / (2 * math.pi)


def main():
    with open(os.path.join(OUT, "148_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    for r in rows:
        r["pred"] = r["want_volume"] * f(r["cols"])
        r["want_area"] = r["want_side"] + r["want_caps"]
    line_chart(os.path.join(OUT, "148_cone.png"),
               [{"label": f"Radius ({r1:g}, {r2:g}) の体積",
                 "points": [(math.log2(r["cols"]), r["volume"] / r["want_volume"]) for r in rows
                            if (r["r1"], r["r2"]) == (r1, r2)], "color": PALETTE[i]}
                for i, (r1, r2) in enumerate(((1.0, 0.0), (1.0, 0.5)))]
               + [{"label": "内接多角形の比 n·sin(2π/n)/2π",
                   "points": [(math.log2(n), f(n)) for n in (12, 48, 384)], "color": PALETTE[4], "dash": True}],
               title="tube の円錐・円錐台（高さ1）: 体積 ÷ 式（横は log2 Columns）",
               x_label="log2(Columns)", y_label="体積の比")
    worst = max(abs(r["volume"] - r["pred"]) for r in rows)
    cone12 = rows[0]
    payload = {
        "title": "tube の円錐台は式 × 内接多角形の比 — Radius の1つ目が上、円錐の先は点が重なったまま",
        "summary":
            "tube（Polygon、End Caps 入り、Height 1）で、Radius を (1, 0)・(1, 0.5)・(0.5, 1) にし、"
            "Columns を 12〜384 と変えて体積と面積を測った。\n\n"
            "**Radius の1つ目が上（y = +0.5）、2つ目が下。**(0.5, 1) では上の半径が 0.5 になった。"
            "上下を入れ替えても、体積と面積は同じ値。\n\n"
            "**体積は、円錐台の式 × n·sin(2π/n)/2π に合う**（9通りで差は最大 "
            f"{worst:.0e}）。断面が内接正 n 角形なので、円（実験143）と同じだけ小さくなる。"
            f"Columns 12 の円錐は {cone12['volume']:.5f}（式 {cone12['want_volume']:.6f}）。\n\n"
            "**円錐（Radius の片方 0）でも、先の点は Columns の数だけ重なって残る。**Columns 12 で点は "
            f"{cone12['points']}（上の輪 12 ＋ 先 12）。先を1点にしたいときは fuse が要る。\n\n"
            "**面積も式（側面 + 蓋2枚）に近づく。**Columns 384 で、円錐 "
            f"{rows[2]['area']:.6f}（式 {rows[2]['want_area']:.6f}）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Radius・Columns と体積・面積",
            "note": "予測の体積 = πh(r1² + r1r2 + r2²)/3 × n·sin(2π/n)/2π。式の面積 = 側面 π(r1 + r2)√((r1 − r2)² + h²) + 蓋 π(r1² + r2²)。",
            "images": [{"path": "148_cone.png", "caption": "円錐も円錐台も、点線（内接多角形の比）に重なる。"}],
            "per_row": 1,
            "columns": ["Radius", "Columns", "点", "面", "上の半径", "体積", "予測", "式の体積", "面積", "式の面積", "秒"],
            "rows": [[f"({r['r1']:g}, {r['r2']:g})", r["cols"], r["points"], r["prims"], f"{r['r_top']:g}",
                      f"{r['volume']:.6f}", f"{r['pred']:.6f}", f"{r['want_volume']:.6f}", f"{r['area']:.6f}",
                      f"{r['want_area']:.6f}", f"{r['sec']:.4f}"] for r in rows]}],
        "notes": [
            "<strong>Radius の1つ目 = 上、2つ目 = 下。</strong>",
            "<strong>tube の円錐は先が閉じていない。</strong>点が Columns 個重なっているので、fuse してから使う。",
            "<strong>体積の不足は Columns だけで決まる。</strong>12 で −4.5%、48 で −0.3%、384 で −0.004%。",
        ],
        "next": ["Rows を増やしたときに体積が変わらないこと", "fuse で先を1点にしたあとの法線"],
    }
    with open(os.path.join(OUT, "148_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 148_report.json", worst, [round(r["volume"] / r["want_volume"] - 1, 5) for r in rows[:3]])


if __name__ == "__main__":
    main()
