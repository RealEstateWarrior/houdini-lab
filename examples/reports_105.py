# -*- coding: utf-8 -*-
"""実験105 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "105_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    conv = [r for r in rows if r["radius"] == 1.0 and r["turns"] == 3]
    worst = max(abs(r["diff_poly"]) for r in rows)
    pts_ok = all(r["points"] == r["want_points"] for r in rows)
    by_div = {r["divs"]: r for r in conv}

    line_chart(
        os.path.join(OUT, "105_spiral.png"),
        [{"label": "測った長さ ÷ なめらかならせんの長さ",
          "points": [(math.log10(r["divs"]), r["ratio_smooth"]) for r in conv],
          "color": PALETTE[0]},
         {"label": "折れ線の式 ÷ なめらかならせんの長さ",
          "points": [(math.log10(r["divs"]), r["want_poly"] / r["want_smooth"])
                     for r in conv],
          "color": PALETTE[2], "dash": True}],
        title="1巻きの分割を増やすと、らせんの長さは式の値に近づく（半径1・3巻き・高さ3）",
        x_label="1巻きの分割数（log10。0.6=4、1.7=50、3=1000）",
        y_label="長さの比")
    print("105_spiral.png")

    payload = {
        "title": "spiral の長さは折れ線の式に6桁一致 — 1巻き50分割で 0.06% 短い",
        "summary":
            "spiral を多角形で出して、長さを式と突き合わせた。半径を一定にすると、"
            "1巻きを N 分割した折れ線の1区間は、横に 2r·sin(π/N)、縦に p/N 進む"
            "（p は1巻きで上がる高さ）。これを 巻き数×N 本足せば全長になる。"
            "分割を細かくしていくと、なめらかならせんの長さ "
            "巻き数×√((2πr)²+p²) に近づくはず。\n\n"
            f"結果は **10通りすべて折れ線の式と一致**（差は最大 {worst:.6f}）。"
            f"点の数も 巻き数×N+1 で{'すべて一致' if pts_ok else '一致しないものがあった'}。\n\n"
            "なめらかならせんと比べると、既定の Divisions per Turn = 50 で "
            f"{by_div[50]['ratio_smooth']:.6f}（{(1 - by_div[50]['ratio_smooth']) * 100:.2f}% 短い）。"
            f"4分割なら {by_div[4]['ratio_smooth']:.6f}、"
            f"1000分割なら {by_div[1000]['ratio_smooth']:.6f}。"
            "分割を2倍にすると、足りない分はおよそ1/4になる"
            f"（8分割で {(1 - by_div[8]['ratio_smooth']) * 100:.3f}%、"
            f"16分割で {(1 - by_div[16]['ratio_smooth']) * 100:.3f}%）。\n\n"
            "高さ 0 にすると、同じ円を巻き数の回数だけなぞった線になる"
            "（4巻きで長さ 25.116 ≒ 円周の4倍）。平らな渦巻きにはならない。"
            "渦巻きにしたいときは、半径を変える（Start と End を変える）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "らせんの長さ（折れ線の式・なめらかな式と比べる）",
             "note": "type=Polygon、mode=Turns、半径は Start = End。長さは measure の "
                     "Perimeter を面ごとに足した値。折れ線の式は "
                     "巻き数×N×√((2r·sin(π/N))²+(p/N)²)。",
             "images": [{"path": "105_spiral.png",
                         "caption": "分割を増やすと比は1に近づく。"
                                    "実測（実線）と折れ線の式（破線）は重なる。"}],
             "per_row": 1,
             "columns": ["半径", "巻き数", "高さ", "1巻きの分割", "点",
                         "長さ", "折れ線の式", "差", "なめらかな式との比"],
             "rows": [[f"{r['radius']:g}", str(r["turns"]), f"{r['height']:g}",
                       str(r["divs"]), str(r["points"]), f"{r['length']:.6f}",
                       f"{r['want_poly']:.6f}", f"{r['diff_poly']:+.6f}",
                       f"{r['ratio_smooth']:.6f}"] for r in rows]},
        ],
        "notes": [
            f"<strong>折れ線の式に一致。</strong>10通りすべてで差は {worst:.6f} 以下。"
            "点の数は 巻き数×分割数+1。",
            f"<strong>既定の50分割で 0.06% 短い。</strong>比は {by_div[50]['ratio_smooth']:.6f}。"
            "ばねや電線の長さを正確に出したいときは、分割を増やすか、式で補正する。",
            "<strong>分割2倍で、足りない分は約1/4。</strong>弦と弧の差は分割の2乗に反比例して減る。"
            "精度を1桁上げるには、分割を約3.2倍にすればよい。",
            "<strong>高さ0は渦巻きにならない。</strong>半径が一定のままだと、"
            "同じ円を何周もなぞるだけ（点も重なる）。",
        ],
        "next": [
            "半径を変えた渦巻き（Archimedean / Logarithmic）の長さと式",
            "NURBS で出したときの長さ（多角形より長くなるはず。確かめていない）",
            "sweep で太さを付けたときの体積と、らせんの長さ×断面積",
        ],
    }
    with open(os.path.join(OUT, "105_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 105_report.json")


if __name__ == "__main__":
    main()
