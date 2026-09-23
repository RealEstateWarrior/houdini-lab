# -*- coding: utf-8 -*-
"""実験198 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "198_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, vox = d["rows"], d["voxel"]
    line_chart(os.path.join(OUT, "198_arc.png"),
               [{"label": "当てはめた円の半径 R", "points": [(r["r"], r["R"]) for r in rows], "color": PALETTE[0]},
                {"label": "R = r（Offset × 升）", "points": [(0.05, 0.05), (0.2, 0.2)], "color": PALETTE[4], "dash": True},
                {"label": "R = r + 3 升", "points": [(0.05, 0.08), (0.2, 0.23)], "color": PALETTE[1], "dash": True}],
               title="vdbreshapesdf Open（1×1×1 の箱・Voxel 0.01）: 辺の断面に当てはめた円の半径",
               x_label="r = Offset × Voxel Size", y_label="円の半径 R")
    extra = [(r["R"] - r["r"]) / vox for r in rows]
    payload = {
        "title": "vdbreshapesdf の Open で丸めた辺の断面は円弧 — 半径は Offset × 升より 2.5〜3.2 升大きい",
        "summary":
            f"1 × 1 × 1 の箱を vdbfrompolygons（Voxel Size {vox}・帯は既定）で SDF にし、vdbreshapesdf の Open を Offset 5・10・20 升でかけて面に戻した。"
            "z = 0 の面の中で原点から 0〜90 度に 721 本の光線を撃って当たった点を取り、辺の近くの点に円を当てはめた（最小二乗）。\n\n"
            "**断面は円弧だった。**当てはめの残差は RMS で "
            + "・".join(f"{r['rms']:.1e}" for r in rows)
            + f"（升の {max(r['rms_in_voxels'] for r in rows) * 100:.1f}% 以下）。円の中心は (0.5 − R, 0.5 − R) から "
            + f"{max(abs(r['cx'] - r['center_if_tangent']) for r in rows):.4f} 以内で、両側の平らな面に接している。\n\n"
            "**半径は r（= Offset × 升）より大きかった。**R = "
            + "・".join(f"{r['R']:.4f}" for r in rows)
            + "（r = 0.05・0.1・0.2）。差は "
            + "・".join(f"{e:.1f}" for e in extra)
            + " 升で、r によらずほぼ一定。倍率にすると "
            + "・".join(f"{r['R_over_r']:.2f}" for r in rows)
            + " 倍で、実験196 で「Offset が小さいほど倍率が大きい」と見えたのは、この一定の足し分のためとみられる。"
            "足し分が帯の既定値（3 升）に近いが、帯との関係は確かめていない。\n\n"
            "**実験196 の体積から出した丸みの半径（0.067・0.117・0.223）は、この R より小さい。**体積には三つの面が集まる角の形も入るためとみられる（確かめていない）。"
            "辺の半径は断面で測った。\n\n"
            f"**時間は SDF にするところから面に戻すまで 1 回 {rows[0]['sec']:.2f}〜{rows[-1]['sec']:.2f} 秒**（光線の当たり判定は含まない）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Offset と、辺の断面に当てはめた円",
            "images": [{"path": "198_arc.png", "caption": "測った R（青）は R = r（灰の点線）より 2.5〜3.2 升上をたどる。"}],
            "per_row": 1,
            "columns": ["Offset（升）", "r", "当てはめた点", "R", "R − r（升）", "中心 x", "接するなら 0.5 − R", "残差 RMS", "残差 最大", "対角の点 x", "半径 r の円弧なら", "秒"],
            "rows": [[r["offset"], f"{r['r']:g}", r["points"], f"{r['R']:.5f}", f"{(r['R'] - r['r']) / vox:.2f}", f"{r['cx']:.5f}",
                      f"{r['center_if_tangent']:.5f}", f"{r['rms']:.1e}", f"{r['max_dev']:.1e}", f"{r['diag_x']:.5f}",
                      f"{r['diag_if_arc_r']:.5f}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>Open は辺をきれいな円弧で丸める。</strong>面とのつなぎ目に段差はない。",
            "<strong>半径は Offset × 升 + 約 3 升。</strong>半径 R が欲しいなら Offset ≒ R ÷ 升 − 3（升 0.01・帯既定の箱で）。",
            "<strong>丸みの半径は体積ではなく断面で測る。</strong>",
        ],
        "next": ["帯の幅を変えたときの R − r", "三つの面が集まる角は球か"],
    }
    with open(os.path.join(OUT, "198_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 198_report.json", [round(e, 2) for e in extra])


if __name__ == "__main__":
    main()
