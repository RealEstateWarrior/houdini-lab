# -*- coding: utf-8 -*-
"""実験132 — attribpromote のまとめ方は、それぞれ何を計算しているのか。

格子 4×4 の16点に、決まった値（v = (i × 7) mod 10、i は点番号）を入れ、
点 → 全体（Detail）へ11通りのまとめ方で上げる。Python で同じ計算をして比べる。
点の数が偶数（16）なので、Median が真ん中の2つの平均か、どちらか一方かが分かる。
Mode は同じ値が何度も出るので、同数のときどれを選ぶかも見る。

最後に 点 → 面（Primitive）の Average を、面の4つの角の平均と比べる。

    hython examples/132_promote.py
"""
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

METHODS = ["max", "min", "mean", "mode", "median", "sum", "sumsquare", "rms", "first", "last"]


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "g")
    grid.parm("rows").set(4)
    grid.parm("cols").set(4)
    val = geo.createNode("attribwrangle", "val")
    val.setInput(0, grid)
    val.parm("snippet").set("f@v = (@ptnum * 7) % 10;")
    vals = list(val.geometry().pointFloatAttribValues("v"))
    s = sorted(vals)
    n = len(vals)
    c = Counter(vals)
    top = max(c.values())
    want = {"max": max(vals), "min": min(vals), "mean": sum(vals) / n,
            "sum": sum(vals), "sumsquare": sum(v * v for v in vals),
            "rms": math.sqrt(sum(v * v for v in vals) / n),
            "first": vals[0], "last": vals[-1],
            "median_avg": (s[n // 2 - 1] + s[n // 2]) / 2, "median_low": s[n // 2 - 1],
            "median_high": s[n // 2],
            "mode_candidates": sorted(v for v, k in c.items() if k == top)}
    rows = []
    for m in METHODS:
        pr = geo.createNode("attribpromote", "p_" + m)
        pr.setInput(0, val)
        pr.parm("inname").set("v")
        pr.parm("inclass").set("point")
        pr.parm("outclass").set("detail")
        pr.parm("method").set(m)
        got = pr.geometry().attribValue("v")
        rows.append({"method": m, "got": round(got, 6)})
        print(rows[-1])
    # 点 → 面の平均
    pm = geo.createNode("attribpromote", "p_prim")
    pm.setInput(0, val)
    pm.parm("inname").set("v")
    pm.parm("inclass").set("point")
    pm.parm("outclass").set("primitive")
    pm.parm("method").set("mean")
    prim_err = 0.0
    for prim in pm.geometry().prims():
        corners = [vals[p.number()] for p in prim.points()]
        prim_err = max(prim_err, abs(prim.attribValue("v") - sum(corners) / len(corners)))
    # Mode の同数のとき: 並びを変えて、最初に出る値と最小の値を別にする
    ties = []
    for code in ("f@v = (@ptnum * 7 + 3) % 10;", "f@v = 9 - (@ptnum * 7) % 10;"):
        w2 = geo.createNode("attribwrangle")
        w2.setInput(0, grid)
        w2.parm("snippet").set(code)
        v2 = list(w2.geometry().pointFloatAttribValues("v"))
        c2 = Counter(v2)
        t2 = max(c2.values())
        pr = geo.createNode("attribpromote")
        pr.setInput(0, w2)
        pr.parm("inname").set("v")
        pr.parm("inclass").set("point")
        pr.parm("outclass").set("detail")
        pr.parm("method").set("mode")
        ties.append({"code": code, "first": v2[0], "got": pr.geometry().attribValue("v"),
                     "candidates": sorted(v for v, k in c2.items() if k == t2)})
        print(ties[-1])
    path = os.path.join(sop_bench.OUT, "132_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"values": vals, "want": want, "rows": rows, "prim_mean_err": round(prim_err, 9),
                   "ties": ties}, fp, ensure_ascii=False, indent=1)
    print(want, "prim_err", prim_err)
    print("書いた:", path)


if __name__ == "__main__":
    main()
