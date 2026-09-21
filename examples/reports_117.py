# -*- coding: utf-8 -*-
"""実験117 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "117_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    series = []
    i = 0
    for n in (500, 2000):
        for iters in (10, 50):
            sub = [r for r in rows if r["n"] == n and r["iters"] == iters]
            series.append({"label": f"{n}点・{iters}回",
                           "points": [(r["frac"], r["min_over_2r"]) for r in sub],
                           "color": PALETTE[i], "dash": iters == 10})
            i += 1
    line_chart(os.path.join(OUT, "117_relax.png"), series,
               title="最も近い点までの距離 ÷ 2×pscale。詰め込みに近いほど 1 に届かない",
               x_label="pscale ÷ 六角形に詰めたときの間隔",
               y_label="最小距離 ÷ (2×pscale)")
    print("117_relax.png")

    small = [r for r in rows if r["frac"] == 0.25 and r["iters"] == 50]
    tight = [r for r in rows if r["frac"] == 0.5 and r["iters"] == 50]
    b500 = rows[0]["before"]
    out_max = max(r["after"]["out_of_plate"] for r in rows)
    payload = {
        "title": "relax は点を 2×pscale 近くまで離す — 余裕があれば97%、詰め込みに近いと73〜77%",
        "summary":
            "1×1 の板に点を散らして pscale を持たせ、relax（Point Relax）にかけた。"
            "pscale が半径なら、重なりが解けたとき点どうしは 2×pscale 以上離れるはず。"
            "板に六角形で詰めたときの間隔 √(2/(√3·n)) を基準にして、pscale をその 0.25・0.4・0.5 倍にした"
            "（0.5 倍だと、ちょうど六角形に詰めたときに触れ合う大きさ）。\n\n"
            f"relax の前は、500 点で最も近い2点の距離が {b500['min']:.4f}（ほぼ重なっている）。\n\n"
            "**余裕があるとき（0.25 倍）は、最小距離が 2×pscale の "
            f"{min(r['min_over_2r'] for r in small) * 100:.0f}〜{max(r['min_over_2r'] for r in small) * 100:.0f}% まで届いた**"
            "（50回）。pscale は半径として働いている。ぴったり 2×pscale にはならず、少し食い込む。\n\n"
            "**詰め込みに近い（0.5 倍）と、届かない。** 50回で "
            f"{min(r['min_over_2r'] for r in tight) * 100:.0f}〜{max(r['min_over_2r'] for r in tight) * 100:.0f}%。"
            "回数を10→50に増やすと少し伸びる（500点で 60%→77%）が、1には届かなかった。\n\n"
            f"板の外にはみ出した点は、どの場合も最大 {out_max} 個（2000点中）。"
            "2つめの入力に板を渡して、面の上に留めた。\n\n"
            "速さ: 2000点・50回で約0.1秒。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "点の数・pscale・回数と、最も近い点までの距離",
             "note": "最小距離は、点ごとに nearpoints で一番近い点を探して、その距離の最小。"
                     "scatter の Relax Iterations は切った。",
             "images": [{"path": "117_relax.png",
                         "caption": "pscale が小さいほど 2×pscale に近づく。破線は10回、実線は50回。"}],
             "per_row": 1,
             "columns": ["点", "pscale", "基準比", "回数", "最小距離", "平均距離",
                         "最小 ÷ 2pscale", "はみ出し", "秒"],
             "rows": [[str(r["n"]), f"{r['pscale']:.5f}", f"{r['frac']:g}", str(r["iters"]),
                       f"{r['after']['min']:.5f}", f"{r['after']['mean']:.5f}",
                       f"{r['min_over_2r']:.3f}", str(r["after"]["out_of_plate"]),
                       f"{r['sec']:.3f}"] for r in rows]},
        ],
        "notes": [
            "<strong>pscale は半径。</strong>余裕があれば、点どうしは 2×pscale の約97%まで離れる。",
            "<strong>詰め込みに近いと届かない。</strong>板に入る限界の半分の pscale（六角形で触れ合う大きさ）では"
            " 73〜77%。回数を増やしても大きくは変わらない。",
            "<strong>面の上に留めるなら、2つめの入力に面を渡す。</strong>はみ出しは 2000点中 最大4点。",
        ],
        "next": [
            "Relax in 3D Space を入れたとき、面から浮くか",
            "scatter の Relax Iterations と、relax を別に通すのとの違い",
            "曲がった面（球）の上で、同じ距離が保てるか",
        ],
    }
    with open(os.path.join(OUT, "117_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 117_report.json")


if __name__ == "__main__":
    main()
