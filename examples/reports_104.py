# -*- coding: utf-8 -*-
"""実験104 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "104_stats.json"), encoding="utf-8") as fp:
        data = json.load(fp)
    rows = sorted(data["rows"], key=lambda r: r["seg"])
    carve_rows = data["carve_rows"]
    length = data["length"]
    split = [r for r in rows if r["ceil_points"] != r["round_points"]]
    all_ceil = all(r["matches_ceil"] for r in rows)
    worst_carve = max(abs(r["diff"]) for r in carve_rows)

    line_chart(
        os.path.join(OUT, "104_resample.png"),
        [{"label": "出た点の数（実測）",
          "points": [(r["seg"], r["points"]) for r in rows],
          "color": PALETTE[0]},
         {"label": "切り上げ ceil(L/s)+1",
          "points": [(r["seg"], r["ceil_points"]) for r in rows],
          "color": PALETTE[2], "dash": True},
         {"label": "四捨五入 round(L/s)+1",
          "points": [(r["seg"], r["round_points"]) for r in rows],
          "color": PALETTE[1], "dash": True}],
        title="点の数は切り上げ。四捨五入の線とは2か所で分かれる",
        x_label="Maximum Segment Length", y_label="点の数")
    line_chart(
        os.path.join(OUT, "104_seg.png"),
        [{"label": "指定した刻み",
          "points": [(r["seg"], r["seg"]) for r in rows],
          "color": PALETTE[4], "dash": True},
         {"label": "実際にできた刻み",
          "points": [(r["seg"], r["actual_seg"]) for r in rows],
          "color": PALETTE[0]}],
        title="実際の刻みは、指定より必ず短いか等しい（Maximum は本当に最大）",
        x_label="Maximum Segment Length", y_label="実際の刻み")
    print("104_resample.png 104_seg.png")

    payload = {
        "title": "resample の点の数は切り上げ — 「最大の長さ」は本当に最大だった",
        "summary":
            f"resample の Maximum Segment Length に s を入れると、長さ {length} の線は"
            "何点になるのか。切り上げなら ceil(L/s)+1、四捨五入なら round(L/s)+1。"
            "割り切れない値を混ぜて9通り測った。\n\n"
            f"結果は **9通りすべて切り上げ**。"
            f"2つの式が分かれるのは {len(split)} か所"
            f"（刻み " + " と ".join(f"{r['seg']:g}" for r in split)
            + "）で、そこでも切り上げのほうが合った。\n\n"
            "できた刻みは、指定した値より必ず短いか等しい。"
            f"たとえば刻み 3.0 を指定すると4点になり、実際の刻みは "
            f"{[r for r in rows if r['seg'] == 3.0][0]['actual_seg']}。"
            "刻み 1.5 では 1.4。**「最大の長さ」という名前のとおりで、"
            "指定を超える区間はできない。** 線の全長はどの刻みでも "
            f"{rows[0]['length']} のまま変わらなかった。\n\n"
            f"carve も測った。0〜1 の範囲で線の一部を取り出す箱で、"
            f"長さは「元の長さ × (終わり - 始まり)」になるはず。"
            f"5通りすべてで差は {worst_carve:.6f}。"
            "0.5〜0.5（幅ゼロ）を指定すると、長さ 0・点 0 で何も出てこない。\n\n"
            "つまずいた点: carve の First U / Second U というつまみは"
            "**「使うかどうか」の入切**で、値は domainu1 / domainu2 という"
            "別のつまみに入っている。既定では First U だけが入で domainu1 が 0.25 なので、"
            "何も触らないと 0.25〜1.0 が取り出される（長さ 5.25）。"
            "画面のラベルが同じ名前で2つ並ぶので、スクリプトから触るときに間違えやすい。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": f"resample の刻みと点の数（長さ {length} の線）",
             "note": "元は line（2点）。長さは measure の Perimeter を面ごとに足した値。"
                     "「実際の刻み」は 長さ ÷ (点の数 - 1)。",
             "images": [{"path": "104_resample.png",
                         "caption": "実測は切り上げの線に重なる。"
                                    "四捨五入の線とは2か所で分かれる。"},
                        {"path": "104_seg.png",
                         "caption": "実際の刻みは、指定した値を超えない。"}],
             "per_row": 2,
             "columns": ["刻み", "L/s", "点", "切り上げ", "四捨五入",
                         "実際の刻み", "長さ"],
             "rows": [[f"{r['seg']:g}", f"{r['ratio']:.4f}", str(r["points"]),
                       str(r["ceil_points"]), str(r["round_points"]),
                       f"{r['actual_seg']:.6f}", f"{r['length']:.6f}"]
                      for r in rows]},
            {"label": f"carve で取り出す範囲と長さ（元は {length}）",
             "note": "値は domainu1 / domainu2 に入れる（First U / Second U は入切）。",
             "images": [],
             "per_row": 1,
             "columns": ["始まり", "終わり", "点", "長さ", "式", "差"],
             "rows": [[f"{r['first']:g}", f"{r['second']:g}", str(r["points"]),
                       f"{r['length']:.6f}", f"{r['want']:.6f}",
                       f"{r['diff']:+.6f}"] for r in carve_rows]},
        ],
        "notes": [
            f"<strong>点の数は切り上げ。</strong>9通りすべて ceil(L/s)+1 と一致した"
            f"（{'例外なし' if all_ceil else '例外あり'}）。"
            "四捨五入と分かれる所でも切り上げだった。",
            "<strong>「最大の長さ」は本当に最大。</strong>刻み 3.0 を指定すると"
            f"実際は {[r for r in rows if r['seg'] == 3.0][0]['actual_seg']}、"
            f"1.5 なら {[r for r in rows if r['seg'] == 1.5][0]['actual_seg']}。"
            "指定を超える区間はできない。細かく刻みたいなら、"
            "その数字より短くなることを前提にする。",
            f"<strong>carve は式どおり。</strong>5通りすべてで差は {worst_carve:.6f}。"
            "幅ゼロを指定すると点も出てこない（長さ 0・点 0）。",
            "<strong>つまずいた点。</strong>carve の First U / Second U は"
            "「使うかどうか」の入切で、値は domainu1 / domainu2 にある。"
            "既定は First U だけ入・domainu1 が 0.25 なので、"
            "何も触らないと 0.25〜1.0（長さ 5.25）になる。"
            "画面に同じラベルが2つ並ぶ型のつまみは、スクリプトから触るとき要注意。",
        ],
        "next": [
            "曲がった線でも、切り上げの規則は同じか",
            "Maximum Segment Length ではなく点の数を指定したときの刻み方",
            "carve を時間で動かして線を伸ばすとき、点の数はどう変わるか",
        ],
    }
    with open(os.path.join(OUT, "104_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 104_report.json")


if __name__ == "__main__":
    main()
