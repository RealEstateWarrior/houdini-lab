# -*- coding: utf-8 -*-
"""実験136 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "136_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    near = [r for r in rows if r["fn"] == "nearpoints" and r["max"] == 100]
    same = all(a["count"] == b["count"] and a["dist"] == b["dist"]
               for a, b in zip(rows[0::2], rows[1::2]))
    line_chart(os.path.join(OUT, "136_near.png"),
               [{"label": "見つかった点の数（自分を含む）", "points": [(r["radius"], r["count"]) for r in near],
                 "color": PALETTE[0]}],
               title="間隔1の格子で、半径と見つかる点の数（1・5・9・13 の階段）",
               x_label="半径", y_label="点の数")
    print("136_near.png")
    payload = {
        "title": "nearpoints は自分を先頭に数え、近い順に返す — 半径ちょうど1は入るが、ちょうど√2は入らなかった",
        "summary":
            "間隔1の格子（21×21）の真ん中の点で nearpoints(0, P, 半径, 最大数) を呼び、"
            "返ってきた点の数・順番・距離を調べた。格子なら、答えは数えられる"
            "（半径1で自分＋上下左右の5、√2 で斜めを足して9、2で13）。\n\n"
            "**自分自身も数に入り、いつも先頭に来る。** どの半径でも、1番目は距離0の自分。"
            "ほかの点は、距離の近い順に並んでいた。\n\n"
            "**最大数は自分を含めて数える。** 最大数3なら、自分＋いちばん近い2点。1なら自分だけ。"
            "「近くの別の点を1つ」のつもりで最大数1にすると、自分しか返らない。\n\n"
            "**半径ちょうど 1.0 の点は入った（5点）。** ところが半径を √2 ちょうど（1.414214）にすると、"
            "斜めの点は入らず5点のまま。1.4143 にすると9点になった。√2 は小数で正確に表せないので、"
            "ほんのわずかな丸めで外に出る。境目の点を確実に入れたいなら、半径を少し大きくする。\n\n"
            f"pcfind() は、すべての場合で nearpoints() と{'同じ結果' if same else '違う結果'}だった。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "半径・最大数と、返ってきた点",
             "note": "距離は、返ってきた点までの距離を順に（最初の14個まで）。",
             "images": [{"path": "136_near.png", "caption": "半径が格子の距離（1・√2・2）を越えるたびに、点が増える。"}],
             "per_row": 1,
             "columns": ["関数", "半径", "最大数", "点の数", "自分が先頭", "近い順", "距離"],
             "rows": [[r["fn"], f"{r['radius']:g}", str(r["max"]), str(r["count"]),
                       "はい" if r["self_first"] else "いいえ", "はい" if r["sorted"] else "いいえ",
                       ", ".join(f"{x:g}" for x in r["dist"])] for r in rows]},
        ],
        "notes": [
            "<strong>自分も返る。</strong>ほかの点だけがほしいなら、最大数を1つ多くして先頭を捨てる。",
            "<strong>近い順に並ぶ。</strong>2番目が「いちばん近い別の点」。",
            "<strong>半径の境目は丸めで揺れる。</strong>格子の間隔ちょうどを半径にするなら、少し足しておく。",
        ],
        "next": [
            "同じ距離の点どうしの並び順（点番号の順か）",
            "点が何百万あるときの速さと、最大数の効き目",
        ],
    }
    with open(os.path.join(OUT, "136_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 136_report.json")


if __name__ == "__main__":
    main()
