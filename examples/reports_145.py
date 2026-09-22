# -*- coding: utf-8 -*-
"""実験145 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "145_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    on = [r for r in rows if r["consolidate"] == 1]
    line_chart(os.path.join(OUT, "145_seam.png"),
               [{"label": f"Consolidate Seam = {tol:g}",
                 "points": [(r["gap"] * 2 * 1e4, r["points"]) for r in on if r["tol"] == tol],
                 "color": PALETTE[i]} for i, tol in enumerate((0.0001, 0.001))],
               title="mirror: 元と鏡像の継ぎ目の距離（2g）と点の数（190 ならまとまった）",
               x_label="継ぎ目の距離 2g（×0.0001）", y_label="点の数")
    payload = {
        "title": "mirror の継ぎ目は「元と鏡像の距離」が Consolidate Seam 未満ならまとまる — 境目ちょうどはまとまらない",
        "summary":
            "10×10 点の grid を、縁が面から g だけ離れるように置いて mirror し、点の数を数えた。"
            "全部まとまれば 190、まとまらなければ 200。\n\n"
            "**比べられるのは、面からの距離 g ではなく、元と鏡像の距離 2g。**Consolidate Seam が既定の 0.0001 のとき、"
            "g = 0.00004（距離 0.00008）はまとまり、g = 0.00005（距離 0.0001、ちょうど境目）はまとまらなかった。\n\n"
            "**まとまった点は面の上（x = 0）に寄る。**元の縁が 0.00004 離れていても、出力の継ぎ目は x = 0 の1列だけ。"
            "まとまらないと ±g の2列が残り、見た目はつながっていても面は割れている。\n\n"
            "**Enable Consolidate Seam を切ると、隙間 0 でも 200 点。**同じ位置に点が2つずつ重なる。"
            "面の数はどの場合も 162（81 × 2）で変わらない。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "隙間・Consolidate Seam・点の数",
            "images": [{"path": "145_seam.png", "caption": "距離がつまみの値に届いたところで 200 に跳ねる。"}],
            "per_row": 1,
            "columns": ["面からの隙間 g", "継ぎ目の距離 2g", "Consolidate Seam", "有効", "点", "面", "継ぎ目の x", "秒"],
            "rows": [[f"{r['gap']:g}", f"{r['gap'] * 2:g}", f"{r['tol']:g}", "入" if r["consolidate"] else "切",
                      r["points"], r["prims"], " / ".join(f"{x:g}" for x in r["seam_x"]), f"{r['sec']:.4f}"]
                     for r in rows]}],
        "notes": [
            "<strong>面から g 離れた縁は、g &lt; Consolidate Seam ÷ 2 でまとまる。</strong>比べるのは元と鏡像の距離。",
            "<strong>境目ちょうどはまとまらない</strong>（「未満」の比較）。",
            "<strong>半分だけ作って mirror するなら、縁を面の上に置く。</strong>ずれがあってもまとまった点は面へ寄る。",
        ],
        "next": ["Only Consolidate Unshared Edges を切ったとき", "Distance を入れて面をずらしたとき"],
    }
    with open(os.path.join(OUT, "145_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 145_report.json")


if __name__ == "__main__":
    main()
