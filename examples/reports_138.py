# -*- coding: utf-8 -*-
"""実験138 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "138_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    series = [{"label": "本当の距離 |p| − 1", "points": [(w, w) for w, _ in rows[0]["profile"]],
               "color": PALETTE[4], "dash": True}]
    for i, r in enumerate(rows[:2]):
        series.append({"label": f"SDF（ボクセル {r['voxel']:g}・Band Voxels {r['half']}）",
                       "points": [(w, s) for w, s in r["profile"]], "color": PALETTE[i]})
    line_chart(os.path.join(OUT, "138_sdf.png"), series,
               title="SDF は表面の近くだけ本当の距離。外では ±（Band Voxels × ボクセル）で止まる",
               x_label="本当の符号付き距離", y_label="SDF の値")
    print("138_sdf.png")
    worst = max(r["err_in_band"] for r in rows)
    payload = {
        "title": "vdbfrompolygons の SDF は帯の中だけ本当の距離（ずれ0.0008以下）— 帯の外は ±（Band Voxels×ボクセル）で平ら",
        "summary":
            "半径1の球（polymesh 200×200）から vdbfrompolygons で SDF を作り、中心から斜めに伸ばした線の上で "
            "volumesample した値を、本当の符号付き距離 |p| − 1 と比べた。\n\n"
            f"**表面の近くの帯の中では、SDF は本当の距離と一致した**（4通りでずれ最大 {worst:.4f}）。"
            "ボクセル 0.02 なら 0.0002 まで小さくなる。\n\n"
            "**帯の外では値が一定になる。** 外側は +（Band Voxels × ボクセル）、内側は −（同じ）で平らになった: "
            + "、".join(f"ボクセル {r['voxel']:g}・Band Voxels {r['half']} で ±{r['band']:g}" for r in rows)
            + "。帯の幅は、Exterior / Interior Band Voxels（ボクセルの数）× ボクセルの大きさ。\n\n"
            "つまり、表面から帯の幅より遠い所では「どれだけ遠いか」の情報は無い。"
            "SDF で表面からの距離を使ったマスクを作るときは、帯を必要な距離まで広げておく。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "ボクセル・帯の幅と、SDF のずれ",
             "note": "帯の中 = 表面からの距離が（帯の幅 − 1ボクセル）より近い所。帯の外 = （帯の幅 + 1ボクセル）より遠い所。",
             "images": [{"path": "138_sdf.png",
                         "caption": "SDF（実線）は、表面のまわりだけ本当の距離（破線）に重なり、外では平らになる。"}],
             "per_row": 1,
             "columns": ["ボクセル", "Band Voxels", "帯の幅", "帯の中のずれ（最大）", "帯の外の値", "作る秒"],
             "rows": [[f"{r['voxel']:g}", str(r["half"]), f"{r['band']:g}", f"{r['err_in_band']:.6f}",
                       ", ".join(f"{v:g}" for v in r["outside_values"]), f"{r['sec']:.3f}"] for r in rows]},
        ],
        "notes": [
            "<strong>帯の中は本当の距離。</strong>ずれは 0.001 未満。",
            "<strong>帯の外は ±帯の幅で止まる。</strong>遠くの距離を使いたいなら、Band Voxels を増やす。",
            "<strong>帯の幅 = Band Voxels × ボクセル。</strong>ボクセルを細かくすると、同じ Band Voxels でも帯は細くなる。",
        ],
        "next": ["Fill Interior を入れたとき、中の値がどうなるか", "vdbsmoothsdf の後でも距離の性質が保たれるか"],
    }
    with open(os.path.join(OUT, "138_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 138_report.json")


if __name__ == "__main__":
    main()
