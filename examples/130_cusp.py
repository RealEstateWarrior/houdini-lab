# -*- coding: utf-8 -*-
"""実験130 — normal の Cusp Angle は、どの角度から角をくっきりさせるのか。

k 角柱（円柱を k 分割）の側面では、隣り合う面の向きの差が 360/k 度になる。
頂点ごとの法線（Vertex）を作るとき、この差が Cusp Angle より大きければ、
角の点で法線が分かれる（くっきり）。小さければ平均される（なめらか）。
k と Cusp Angle を振って、側面の角の点で法線が分かれたかを数える。
境目ちょうど（差 = Cusp Angle）の扱いも見る。

    hython examples/130_cusp.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def split_ratio(node):
    """側面の点のうち、頂点ごとの法線が2つ以上に分かれている点の割合。"""
    geo = node.geometry()
    split = total = 0
    for pt in geo.points():
        if abs(pt.position()[1]) > 0.4:      # 上下の縁は除く
            continue
        ns = {tuple(round(c, 4) for c in v.attribValue("N")) for v in pt.vertices()}
        total += 1
        split += len(ns) > 1
    return split / total if total else None, total


def main():
    geo = sop_bench.fresh()
    rows = []
    for k in (4, 6, 8, 12, 24):
        tb = geo.createNode("tube", f"tb{k}")
        tb.parm("type").set("poly")
        tb.parm("cols").set(k)
        tb.parm("rows").set(5)
        tb.parm("height").set(1.0)
        for cusp in (10, 20, 30, 45, 60, 90, 360 / k, 360 / k - 0.01, 360 / k + 0.01):
            nm = geo.createNode("normal", f"n_{k}_{int(cusp * 100)}")
            nm.setInput(0, tb)
            nm.parm("type").set("typevertex")
            nm.parm("cuspangle").set(cusp)
            ratio, total = split_ratio(nm)
            rows.append({"k": k, "turn": round(360 / k, 4), "cusp": round(cusp, 4),
                         "split_ratio": ratio, "points": total,
                         "expect_split": 360 / k > cusp})
            print(rows[-1])
    # 境目の近くを細かく: Cusp Angle = 曲がり角 − δ で、分かれ始める δ を探す
    edge = []
    for k in (4, 8, 24):
        tb = geo.node(f"tb{k}")
        for delta in (0.01, 0.03, 0.05, 0.1, 0.2, 0.5, 1.0):
            nm = geo.createNode("normal", f"e_{k}_{int(delta * 1000)}")
            nm.setInput(0, tb)
            nm.parm("type").set("typevertex")
            nm.parm("cuspangle").set(360 / k - delta)
            ratio, _ = split_ratio(nm)
            edge.append({"k": k, "turn": round(360 / k, 4), "delta": delta, "split_ratio": ratio})
            print(edge[-1])
    path = os.path.join(sop_bench.OUT, "130_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "edge": edge}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
