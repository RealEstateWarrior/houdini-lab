# -*- coding: utf-8 -*-
"""実験199 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "199_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, vox = d["rows"], d["voxel"]
    line_chart(os.path.join(OUT, "199_band.png"),
               [{"label": "R − r（升）", "points": [(r["band"], r["extra_in_voxels"]) for r in rows], "color": PALETTE[0]},
                {"label": "帯の幅と同じなら", "points": [(3, 3), (25, 25)], "color": PALETTE[4], "dash": True}],
               title="vdbreshapesdf Open（Offset 10・Voxel 0.01）: 帯の幅と、辺の半径の足し分",
               x_label="Exterior / Interior Band Voxels", y_label="R − r（升）")
    ex = [r["extra_in_voxels"] for r in rows]
    payload = {
        "title": "Open で丸めた辺の半径が約 3 升大きいのは、SDF の帯のせいではない — 帯 3〜25 升で足し分は変わらない",
        "summary":
            "実験198 で、vdbreshapesdf の Open で丸めた辺の半径は Offset × 升より約 3 升大きかった。帯の既定値（3 升）と近いので、"
            "vdbfrompolygons の Exterior / Interior Band Voxels を "
            + "・".join(str(r["band"]) for r in rows)
            + " 升に変え、Open（Offset 10 升・Voxel Size 0.01・1 × 1 × 1 の箱）の辺の断面を実験198 と同じやり方で測った。\n\n"
            f"**足し分 R − r は、帯の幅によらず {min(ex):.2f}〜{max(ex):.2f} 升だった。**R = "
            + "・".join(f"{r['R']:.5f}" for r in rows)
            + "。帯のせいではない。何が 3 升を足しているかは確かめていない。\n\n"
            "**体積は帯 3 升と 6 升で違い、6 升以上は同じだった**（"
            + "・".join(f"{r['volume']:.6f}" for r in rows)
            + "）。辺の半径は変わらないので、実験197 で見た帯による体積の違いは、辺以外（三つの面が集まる角など）から来ているとみられる。確かめていない。\n\n"
            f"**時間は帯が広いほどかかった**（{rows[0]['sec']:.2f} 秒 → {rows[-1]['sec']:.2f} 秒）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "帯の幅と、辺の断面の円",
            "images": [{"path": "199_band.png", "caption": "足し分（青）は帯の幅（点線）と関係なく 3 升で平ら。"}],
            "per_row": 1,
            "columns": ["帯（升）", "Offset（升）", "当てはめた点", "R", "R − r（升）", "中心 x", "接するなら 0.5 − R", "残差 RMS", "体積", "秒"],
            "rows": [[r["band"], r["offset"], r["points"], f"{r['R']:.5f}", f"{r['extra_in_voxels']:.3f}", f"{r['cx']:.5f}",
                      f"{r['center_if_tangent']:.5f}", f"{r['rms']:.1e}", f"{r['volume']:.6f}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>Open の辺の半径は、帯を広げても変わらない。</strong>Offset ≒ R ÷ 升 − 3 は帯によらず使える（升 0.01 の箱で）。",
            "<strong>帯は 6 升あれば体積も変わらなくなった。</strong>それ以上広げると時間だけ増える。",
        ],
        "next": ["升の大きさを変えたときの足し分（3 升か、一定の長さか）", "三つの面が集まる角は球か"],
    }
    with open(os.path.join(OUT, "199_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 199_report.json", ex)


if __name__ == "__main__":
    main()
