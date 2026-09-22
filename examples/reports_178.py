# -*- coding: utf-8 -*-
"""実験178 の図とレポートを、測った値から組み立てる。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "178_stats.json"), encoding="utf-8") as fp:
        rows = json.load(fp)["rows"]
    line_chart(os.path.join(OUT, "178_cost.png"),
               [{"label": "見つかった数と1点あたりの時間", "points": sorted((r["mean_found"], r["us_per_point"]) for r in rows), "color": PALETTE[0]}],
               title="pcfind（10 万点・全点で1回ずつ）: 見つかった点の数の平均と、1点あたりのマイクロ秒",
               x_label="見つかった点の数（平均、自分を含む）", y_label="1点あたり（マイクロ秒）")
    by = {(r["radius"], r["maxpts"]): r for r in rows}
    payload = {
        "title": "pcfind の時間は「見つかった点の数」で決まる — 半径を広げても、最大の数を 10 に絞れば 1 点 0.1 マイクロ秒",
        "summary":
            "1 × 1 × 1 の中に一様に 10 万点を撒き、全部の点で pcfind(0, \"P\", @P, r, maxpts) を1回ずつ呼んだ。"
            "半径 r と最大の数 maxpts を変え、時間（2 回の速い方）と、見つかった数の平均を記録した。\n\n"
            f"**時間は、見つかった点の数にほぼ比例して増えた。**半径 0.1 で maxpts を 10・100・1000 にすると、見つかる数は "
            f"{by[(0.1, 10)]['mean_found']:g}・{by[(0.1, 100)]['mean_found']:g}・{by[(0.1, 1000)]['mean_found']:g}、"
            f"1 点あたり {by[(0.1, 10)]['us_per_point']:.2f}・{by[(0.1, 100)]['us_per_point']:.2f}・{by[(0.1, 1000)]['us_per_point']:.2f} マイクロ秒。"
            "半径の中にもっと多くの点があっても、maxpts で打ち切れば、打ち切った数の分しか時間がかからない。\n\n"
            f"**小さい半径では、ほとんど決まった手間だけ。**半径 0.01（見つかる数 {by[(0.01, 10)]['mean_found']:g}）で 1 点 0.05 マイクロ秒。10 万点で 5 ミリ秒。\n\n"
            "**見つかる数には自分も入る。**半径 0.01 で、期待値（他の点 0.42 個）より多い 1.32 個になったのはそのため。"
            f"半径 0.1 では、立方体の端の点が損をするので、期待値 {by[(0.1, 1000)]['expect_inside']:g} より少ない {by[(0.1, 1000)]['mean_found']:g} 個。",
        "graph": "", "graph_image": "",
        "comparisons": [{
            "label": "半径・maxpts と時間",
            "images": [{"path": "178_cost.png", "caption": "見つかった数（横）が増えるほど、ほぼ一直線に遅くなる。"}],
            "per_row": 1,
            "columns": ["半径", "maxpts", "見つかった数の平均", "半径の中の期待値（他の点）", "秒（10 万点）", "1 点あたり（マイクロ秒）"],
            "rows": [[f"{r['radius']:g}", r["maxpts"], f"{r['mean_found']:g}", f"{r['expect_inside']:g}", f"{r['sec']:.4f}",
                      f"{r['us_per_point']:.3f}"] for r in rows]}],
        "notes": [
            "<strong>pcfind は maxpts で重さが決まる。</strong>要る数だけに絞る。",
            "<strong>見つかる点には自分も入る。</strong>「まわりの数」なら 1 を引く（実験172 でそうした）。",
            "<strong>10 万点・半径 0.05・100 点までで 15 ミリ秒。</strong>毎フレーム回しても軽い。",
        ],
        "next": ["pcopen / pcfilter との速さの違い", "nearpoints() との速さの違い"],
    }
    with open(os.path.join(OUT, "178_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 178_report.json")


if __name__ == "__main__":
    main()
