# -*- coding: utf-8 -*-
"""実験106 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402

LABEL = {"uniform_0_1": "一様 0〜1", "uniform_2_5": "一様 2〜5",
         "normal_s1": "正規 中央0・Scale 1", "normal_s2": "正規 中央0・Scale 2",
         "normal_m3_s05": "正規 中央3・Scale 0.5"}


def main():
    with open(os.path.join(OUT, "106_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    n = d["points"]
    rows = d["rows"]
    share = d["discrete"]["share"]
    ball, orient, bern, seed = d["vec"]["ball"], d["vec"]["orient"], d["bern"], d["seed"]
    # 平均のぶれの目安（標準誤差）: 標準偏差 / √n
    for r in rows:
        r["se"] = math.sqrt(r["want_var"] / n)
        r["z"] = (r["mean"] - r["want_mean"]) / r["se"]
    worst_z = max(abs(r["z"]) for r in rows)
    worst_var = max(abs(r["var"] / r["want_var"] - 1) for r in rows)

    keys = sorted(share, key=float)
    line_chart(
        os.path.join(OUT, "106_discrete.png"),
        [{"label": "出た割合（実測）",
          "points": [(float(k), share[k]) for k in keys], "color": PALETTE[0]},
         {"label": "式 1/10",
          "points": [(float(k), 0.1) for k in keys], "color": PALETTE[2], "dash": True}],
        title="整数の一様（0〜9・刻み1）: 端の9も出る。どれも約10%",
        x_label="出た値", y_label="割合")
    print("106_discrete.png")

    payload = {
        "title": "attribrandomize の分布は式どおり — Scale Around Middle は標準偏差だった",
        "summary":
            f"attribrandomize で {n:,} 点に乱数を1つずつ入れ、平均・分散・割合を数えて、"
            "分布の式から出る値と比べた。10万点あると、平均のぶれは標準偏差の約 1/316 に収まるはず"
            "（標準誤差 σ/√n）。\n\n"
            f"**一様・正規の5通りすべてで、平均のずれは標準誤差の {worst_z:.2f} 倍以内、"
            f"分散のずれは {worst_var * 100:.2f}% 以内。** 式どおりの分布が出ている。\n\n"
            "正規分布の **Scale Around Middle は標準偏差**だった。Scale 2 で標準偏差 "
            f"{rows[3]['sd']:.4f}、0.5 で {rows[4]['sd']:.4f}。"
            "画面の名前からは分散なのか幅なのか分からないが、標準偏差として読めばよい。\n\n"
            "整数の一様（0〜9・刻み1）では、**上端の 9 も出る**。10通りの値がそれぞれ "
            f"{min(share.values()) * 100:.2f}〜{max(share.values()) * 100:.2f}%。"
            f"2つの値（B の確率 0.3）では B が {bern['share_b'] * 100:.2f}%。\n\n"
            f"3成分の「球の中」は、長さの平均 {ball['len_mean']:.4f}（式は 3/4）、最大 "
            f"{ball['len_max']:.6f}。「向き」は長さが全部 {orient['len_min']:.6f}〜"
            f"{orient['len_max']:.6f} で、平均の向きはほぼ0。\n\n"
            "同じ種なら値は1つ残らず同じ。種を 0→1 に変えると、同じ値になった点は "
            f"{seed['diff_seed_equal_share'] * 100:.4f}%。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": f"一様・正規の平均と分散（{n:,} 点）",
             "note": "z は（平均 − 式）÷ 標準誤差。±2 の中なら、偶然のぶれの範囲。",
             "images": [],
             "per_row": 1,
             "columns": ["分布", "平均", "式", "z", "分散", "式", "最小", "最大"],
             "rows": [[LABEL[r["case"]], f"{r['mean']:.6f}", f"{r['want_mean']:g}",
                       f"{r['z']:+.2f}", f"{r['var']:.6f}", f"{r['want_var']:.6f}",
                       f"{r['min']:.4f}", f"{r['max']:.4f}"] for r in rows]},
            {"label": "整数の一様（0〜9・刻み1）の割合",
             "note": "Min 0・Max 9・Step Size 1。",
             "images": [{"path": "106_discrete.png",
                         "caption": "10通りの値がどれも約10%。上端の9も出る。"}],
             "per_row": 1,
             "columns": ["値"] + [f"{float(k):g}" for k in keys],
             "rows": [["割合"] + [f"{share[k] * 100:.2f}%" for k in keys]]},
            {"label": "3成分の分布",
             "note": "長さ = √(x²+y²+z²)。球の中が一様なら、長さの平均は 3/4。",
             "images": [],
             "per_row": 1,
             "columns": ["分布", "長さの平均", "最小", "最大", "平均の向き"],
             "rows": [["球の中", f"{ball['len_mean']:.6f}", f"{ball['len_min']:.6f}",
                       f"{ball['len_max']:.6f}", str(ball["avg"])],
                      ["向き", f"{orient['len_mean']:.6f}", f"{orient['len_min']:.6f}",
                       f"{orient['len_max']:.6f}", str(orient["avg"])]]},
        ],
        "notes": [
            "<strong>分布は式どおり。</strong>一様・正規の5通りで、平均は標準誤差の"
            f" {worst_z:.2f} 倍以内、分散は {worst_var * 100:.2f}% 以内。",
            "<strong>Scale Around Middle は標準偏差。</strong>Scale 2 で標準偏差 "
            f"{rows[3]['sd']:.4f}。分散ではない。",
            "<strong>整数の一様は上端を含む。</strong>0〜9 なら10通り、どれも約10%。",
            f"<strong>球の中は、中まで均一。</strong>長さの平均 {ball['len_mean']:.4f}（式 0.75）。"
            "表面だけに散る「向き」とは別物。",
            "<strong>同じ種なら、同じ値。</strong>種を変えれば全部の点が変わる。",
            f"<strong>速い。</strong>{n:,} 点で 0.01〜0.13 秒"
            "（最初の1回は読み込みを含むので遅い）。",
        ],
        "next": [
            "Exponential・Log-Normal の Middle Value と Spread Around Middle の意味",
            "Use Seed Attribute で id を種にしたとき、点を消しても値が変わらないか",
            "Cone Angle を付けた向きの分布が、角度どおりに収まるか",
        ],
    }
    with open(os.path.join(OUT, "106_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 106_report.json")


if __name__ == "__main__":
    main()
