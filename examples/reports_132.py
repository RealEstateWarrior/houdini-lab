# -*- coding: utf-8 -*-
"""実験132 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"max": "Maximum", "min": "Minimum", "mean": "Average", "mode": "Mode", "median": "Median",
         "sum": "Sum", "sumsquare": "Sum of Squares", "rms": "Root Mean Square",
         "first": "First Match", "last": "Last Match"}


def main():
    with open(os.path.join(OUT, "132_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    w, rows, ties = d["want"], d["rows"], d["ties"]
    got = {r["method"]: r["got"] for r in rows}
    plain = ["max", "min", "mean", "sum", "sumsquare", "rms", "first", "last"]
    ok = all(abs(got[m] - w[m]) < 1e-5 for m in plain)
    vals = sorted(d["values"])
    line_chart(os.path.join(OUT, "132_promote.png"),
               [{"label": "16個の値を小さい順に", "points": [(i, v) for i, v in enumerate(vals)],
                 "color": PALETTE[0]},
                {"label": f"Median の出力 {got['median']:g}", "points": [(0, got["median"]), (15, got["median"])],
                 "color": PALETTE[1], "dash": True},
                {"label": f"真ん中2つの平均 {w['median_avg']:g}", "points": [(0, w["median_avg"]), (15, w["median_avg"])],
                 "color": PALETTE[4], "dash": True}],
               title="値が偶数個のとき、Median は真ん中の2つの「大きい方」を返した",
               x_label="小さい順の番号", y_label="値")
    print("132_promote.png")

    table = [[LABEL[m], f"{got[m]:g}", f"{w[m]:g}" if m in w else "—"] for m in plain]
    table.append(["Median", f"{got['median']:g}",
                  f"平均なら {w['median_avg']:g}／下 {w['median_low']:g}／上 {w['median_high']:g}"])
    table.append(["Mode", f"{got['mode']:g}", "同数の候補 " + ", ".join(f"{v:g}" for v in w["mode_candidates"])])
    payload = {
        "title": "attribpromote の11通りのまとめ方 — Median は偶数個なら上の方、Mode は同数なら最小の値",
        "summary":
            "格子 4×4 の16点に、v = (点番号 × 7) mod 10 という決まった値を入れ、attribpromote で"
            "点 → 全体（Detail）に上げた。Python で同じ計算をして、まとめ方ごとに比べた。\n\n"
            f"**最大・最小・平均・合計・2乗の合計・RMS・最初・最後の8通りは、式と{'すべて一致' if ok else '一致しないものがあった'}。**"
            f"平均 {got['mean']:g}、RMS {got['rms']:.6f} など。\n\n"
            f"**Median は、値が偶数個のとき真ん中の2つの平均ではなく、大きい方を返した**"
            f"（小さい順に並べた 8番目 {w['median_low']:g} と 9番目 {w['median_high']:g} のうち {got['median']:g}。"
            f"平均なら {w['median_avg']:g}）。\n\n"
            "**Mode は、いちばん多く出た値が同数で並ぶとき、その中の最小の値を返した。** 元の並べ方（候補 0, 1, 4, 5, 7, 8 → 0）に加え、"
            "最初に出る値が最小にならない並べ方2通りでも確かめた（最初に出てきた値ではない）: "
            + "、".join(f"候補 {', '.join(f'{v:g}' for v in t['candidates'])} → {t['got']:g}"
                       f"（最初の値は {t['first']:g}）" for t in ties) + "。\n\n"
            f"点 → 面の Average は、面の4つの角の値の平均と一致した（ずれ {d['prim_mean_err']:g}）。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "点 → 全体へのまとめ方（16点）",
             "note": "値は 0, 7, 4, 1, 8, 5, 2, 9, 6, 3, 0, 7, 4, 1, 8, 5（点番号の順）。",
             "images": [{"path": "132_promote.png",
                         "caption": "偶数個の Median は、真ん中の2つの上の方（5）。平均の 4.5 ではない。"}],
             "per_row": 1,
             "columns": ["まとめ方", "出た値", "式"],
             "rows": table},
        ],
        "notes": [
            "<strong>Median は偶数個で上の方。</strong>中央値として平均がほしいなら、自分で計算する。",
            "<strong>Mode の同数は最小の値。</strong>ばらつきが大きいデータの Mode は当てにしにくい。",
            "<strong>点 → 面の Average は、角の平均そのもの。</strong>",
        ],
        "next": [
            "Piece Attribute を使って、塊ごとにまとめたときの結果",
            "頂点 → 点（Vertex → Point）で、共有された点の値がどうまとまるか",
        ],
    }
    with open(os.path.join(OUT, "132_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 132_report.json")


if __name__ == "__main__":
    main()
