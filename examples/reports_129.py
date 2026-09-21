# -*- coding: utf-8 -*-
"""実験129 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

KIND = {"gaussian": "ガウス曲率", "mean": "平均曲率", "curvedness": "curvedness"}


def main():
    with open(os.path.join(OUT, "129_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    per, dflt = data["per_area"], data["default"]

    def rel(r, k):
        w = r["want"][k]
        return (r[k]["mean"] - w) / w if w else None

    worst = {res: max(abs(rel(r, k)) for r in per if r["res"] == res for k in KIND if r["want"][k])
             for res in (24, 96)}
    series = []
    for i, k in enumerate(KIND):
        pts = [(r["res"], abs(rel(r, k)) * 100) for r in per if r["shape"] == "sphere" and r["r"] == 1.0]
        series.append({"label": f"球 r=1 の{KIND[k]}", "points": pts, "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "129_curvature.png"), series,
               title="Divide Element Area を入れれば、曲率は式どおり。網を4倍細かくするとずれは約1/16",
               x_label="球の段数（24 と 96）", y_label="式とのずれ（%）")
    print("129_curvature.png")

    s1 = next(r for r in dflt if r["shape"] == "sphere" and r["r"] == 1.0 and r["res"] == 96)
    s2 = next(r for r in dflt if r["shape"] == "sphere" and r["r"] == 2.0 and r["res"] == 96)
    payload = {
        "title": "measure の曲率は既定のままだと式と合わない — Divide Element Area を入れると球・円柱とも0.03%以内",
        "summary":
            "半径 r の球（ガウス曲率 1/r²・平均曲率 1/r）と円柱（ガウス曲率 0・平均曲率 1/(2r)）で、"
            "measure の Curvature を式と比べた。極や縁の近くは除いた。\n\n"
            "**既定のままだと、式の値は出てこない。** 半径1の球で、ガウス曲率が "
            f"{s1['gaussian']['mean']:.6f}（式は 1）、平均曲率が {s1['mean']['mean']:.6f}。"
            f"しかも半径2の球でも同じ値（{s2['gaussian']['mean']:.6f}）で、大きさに左右されない。"
            "網を細かくすると値が小さくなることから、既定では「点のまわりの面積の分を足し込んだ量」を"
            "大きさで正規化して出していると考えられる（Divide Element Area が切、Scale Normalize が入。"
            "中の計算そのものは確かめていない）。\n\n"
            "**Divide Element Area を入れ、Scale Normalize を切ると、式どおりの曲率になった。** "
            f"段数24 で最大 {worst[24] * 100:.2f}%、段数96 で最大 {worst[96] * 100:.3f}% のずれ。"
            "網を4倍細かくすると、ずれは約1/16（細かさの2乗で減る）。円柱のガウス曲率は、どちらでも 0。\n\n"
            "平均曲率の符号は、外向きの法線の球でプラスだった。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "Divide Element Area 入・Scale Normalize 切のときの曲率（点の平均）",
             "note": "球は polymesh（段数 × 2倍の列）。|y| < 0.8r の点だけ。円柱は高さ4、縁から 0.5 以上離れた点だけ。",
             "images": [{"path": "129_curvature.png",
                         "caption": "どの曲率も、網を細かくすると式に近づく。"}],
             "per_row": 1,
             "columns": ["形", "r", "段数", "ガウス", "式", "平均", "式", "curvedness", "式"],
             "rows": [[("球" if r["shape"] == "sphere" else "円柱"), f"{r['r']:g}", str(r["res"]),
                       f"{r['gaussian']['mean']:.6f}", f"{r['want']['gaussian']:.4f}",
                       f"{r['mean']['mean']:.6f}", f"{r['want']['mean']:.4f}",
                       f"{r['curvedness']['mean']:.6f}", f"{r['want']['curvedness']:.4f}"] for r in per]},
            {"label": "既定のまま（Divide Element Area 切・Scale Normalize 入）",
             "note": "大きさを変えても同じ値。網を細かくすると小さくなる。",
             "images": [],
             "per_row": 1,
             "columns": ["形", "r", "段数", "ガウス", "平均", "curvedness"],
             "rows": [[("球" if r["shape"] == "sphere" else "円柱"), f"{r['r']:g}", str(r["res"]),
                       f"{r['gaussian']['mean']:.6f}", f"{r['mean']['mean']:.6f}",
                       f"{r['curvedness']['mean']:.6f}"] for r in dflt]},
        ],
        "notes": [
            "<strong>曲率の値そのものがほしいなら、Divide Element Area を入れて Scale Normalize を切る。</strong>",
            "<strong>既定の値は、網の細かさで変わる。</strong>マスクに使うなら、同じ網どうしで比べる。",
            "<strong>ずれは網の細かさの2乗で減る。</strong>段数96の球で 0.03% 以内。",
        ],
        "next": [
            "Principal（最小・最大の主曲率）とその向きが、円柱で軸方向と周方向に出るか",
            "Scale Normalize だけを切ったとき、何で割っているのか",
            "トーラスの外側（ガウス曲率がプラス）と内側（マイナス）の符号",
        ],
    }
    with open(os.path.join(OUT, "129_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 129_report.json")


if __name__ == "__main__":
    main()
