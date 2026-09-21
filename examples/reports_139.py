# -*- coding: utf-8 -*-
"""実験139 の図とレポートを、測った値から組み立てる。"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def main():
    with open(os.path.join(OUT, "139_stats.json"), encoding="utf-8") as fp:
        d = json.load(fp)
    rows, s = d["rows"], d["step"]
    line_chart(os.path.join(OUT, "139_blur.png"),
               [{"label": "ぼけ幅（実測、点の数）", "points": [(math.log10(r["iters"]), r["width_pts"]) for r in rows],
                 "color": PALETTE[0]},
                {"label": "√(2·s·N)", "points": [(math.log10(r["iters"]), math.sqrt(2 * s * r["iters"])) for r in rows],
                 "color": PALETTE[2], "dash": True},
                {"label": "√(s·N)（1回1度のとき）", "points": [(math.log10(r["iters"]), r["sqrt_rule"]) for r in rows],
                 "color": PALETTE[1], "dash": True}],
               title="段差のぼけ幅は回数の平方根で広がる。1回の中で2度ぼかしている",
               x_label="回数（log10。0=1、3=1000）", y_label="ぼけ幅（点の数）")
    print("139_blur.png")
    worst2 = max(r["max_err_vs_2pass"] for r in rows)
    payload = {
        "title": "attribblur の1回は「となりの平均へ半分近づく」を2度 — ぼけ幅は √回数。線では Pin Border で全く動かない",
        "summary":
            "401点の線（点の間隔 0.01）に段差の値（左 0・右 1）を入れて attribblur にかけ、"
            "Python で同じ計算をくり返したものと1点ずつ比べた。\n\n"
            f"**既定のままだと、1点も変わらなかった**（100回かけて、変わった点 {d['pinned_changed']} 個）。"
            "Pin Border（縁を止める）が入っていて、開いた線では全部の点が縁とみなされるため。"
            "線をぼかすときは Pin Border を切る。\n\n"
            "**切ると、1回のぼかしは「v ← v + s·((左 + 右)/2 − v)」を2度くり返したものと一致した**"
            f"（Step Size s = {s:g}、1〜1000回でずれ最大 {worst2:.7f}）。1度だけの計算とは最大 0.08 ずれる。"
            "Odd / Even Step Size という2つのつまみがあることとも合う（奇数・偶数の段で1度ずつ）。\n\n"
            "**段差のぼけ幅（標準偏差）は、回数の平方根で広がった。** 1・10・100・1000 回で "
            + "・".join(f"{r['width_pts']:g}" for r in rows) + " 点ぶん（= √(2·s·N)）。"
            "ぼけ幅を2倍にしたいなら、回数を4倍にする。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "回数と、ぼけ方",
             "note": "ぼけ幅 = となりとの差を分布とみなしたときの標準偏差（点の数で）。端の点は、となり1点に近づく。",
             "images": [{"path": "139_blur.png", "caption": "実測（青）は √(2·s·N) の線に重なる。"}],
             "per_row": 1,
             "columns": ["回数", "2度ずつの計算とのずれ", "1度ずつの計算とのずれ", "ぼけ幅", "√(2·s·N)", "秒"],
             "rows": [[str(r["iters"]), f"{r['max_err_vs_2pass']:.7f}", f"{r['max_err_vs_rule']:.4f}",
                       f"{r['width_pts']:.4f}", f"{math.sqrt(2 * s * r['iters']):.4f}", f"{r['sec']:.4f}"]
                      for r in rows]},
        ],
        "notes": [
            "<strong>開いた線では Pin Border を切る。</strong>入れたままだと何も起きない（エラーも出ない）。",
            "<strong>1回 = 2度のぼかし。</strong>Step Size 0.5 なら、となりの平均との差の半分だけ近づく計算を2度。",
            "<strong>ぼけ幅は √回数。</strong>4倍の回数で2倍の幅。",
        ],
        "next": ["面（格子）の上で、ぼけ幅が同じ式になるか", "Volume Preserving モードで、段差の高さがどう変わるか"],
    }
    with open(os.path.join(OUT, "139_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた: 139_report.json")


if __name__ == "__main__":
    main()
