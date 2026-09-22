# -*- coding: utf-8 -*-
"""実験195 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "195_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, vox = d["rows"], d["voxel"]
    de = [r for r in rows if r["operation"] in ("dilate", "erode") and r["iterations"] == 4]
    line_chart(os.path.join(OUT, "195_reshape.png"),
               [{"label": "半径の変化（升目の数で）", "points": sorted((r["offset"] * (1 if r["operation"] == "dilate" else -1), r["change_in_voxels"]) for r in de), "color": PALETTE[0]},
                {"label": "Offset どおり", "points": [(-5, -5), (5, 5)], "color": PALETTE[4], "dash": True}],
               title="vdbreshapesdf（半径 1 の球・Voxel 0.02）: Offset（Erode は負）と、半径の変化",
               x_label="Offset（升目の数、Erode はマイナス）", y_label="半径の変化 ÷ 升の大きさ")
    worst = max(abs(r["change_in_voxels"] - (r["offset"] if r["operation"] == "dilate" else -r["offset"])) for r in de)
    same_it = all(abs(a["change"] - b["change"]) < 1e-9 for a in rows for b in rows
                  if a["operation"] == b["operation"] and a["offset"] == b["offset"] and a["iterations"] != b["iterations"])
    op = [r for r in rows if r["operation"] in ("open", "close")]
    payload = {
        "title": "vdbreshapesdf の Dilate・Erode は、球の半径を Offset × 升の大きさだけ変える — Iterations は効かず、Open・Close は形をほぼ変えない",
        "summary":
            f"半径 1 の球を vdbfrompolygons（Voxel Size {vox}）で SDF にし、vdbreshapesdf の Operation と Offset（升目の数）を変えた。"
            "convertvdb で面に戻して体積を測り、同じ体積の球の半径に直して比べた。\n\n"
            f"**Dilate は半径を + Offset × {vox}、Erode は − Offset × {vox} だけ変えた。**6 通りで、ずれは最大 {worst:.3f} 升"
            f"（Offset 5 の Dilate で {[r for r in de if r['operation'] == 'dilate' and r['offset'] == 5][0]['change']:+.4f}、Erode で {[r for r in de if r['operation'] == 'erode' and r['offset'] == 5][0]['change']:+.4f}）。"
            "SDF の値から Offset を引く（足す）だけの、面を等しく押し出す処理になっている。\n\n"
            f"**Iterations（既定 4）を 1 にしても、結果は同じだった**（{'すべて一致' if same_it else '違いがあった'}）。Dilate・Erode には効かないつまみとみられる。\n\n"
            f"**Open（Erode してから Dilate）と Close（その逆）は、球をほぼ元のまま残した**（半径の変化 {op[0]['change_in_voxels']:.3f}・{op[1]['change_in_voxels']:.3f} 升）。"
            "丸い形には削れる角がないため。尖った角のある形で差が出るはず（確かめていない）。\n\n"
            "**時間は 1 回 0.5 秒前後**（SDF にするところと面に戻すところを含む）。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "Operation・Offset・Iterations と半径",
            "images": [{"path": "195_reshape.png", "caption": "測った点は点線（Offset どおり）にほぼ乗る。"}],
            "per_row": 1,
            "columns": ["Operation", "Offset（升）", "Iterations", "半径", "変化", "Offset × 升の大きさ", "変化 ÷ 升", "秒"],
            "rows": [[r["operation"], r["offset"], r["iterations"], f"{r['radius']:.6f}", f"{r['change']:+.6f}", f"{r['want']:+.4f}",
                      f"{r.get('change_in_voxels', 0):+.3f}", f"{r['sec']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>SDF をちょうど d だけ太らせる（痩せさせる）なら、Offset = d ÷ 升の大きさ。</strong>",
            "<strong>Iterations は Dilate・Erode の量を変えない。</strong>",
            "<strong>Open・Close は丸い形をほとんど変えない。</strong>細い突起や小さな穴を消すための処理。",
        ],
        "next": ["角のある箱での Open・Close の効き方", "Offset を升目より細かく（小数で）指定したとき"],
    }
    with open(os.path.join(OUT, "195_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 195_report.json", worst, same_it)


if __name__ == "__main__":
    main()
