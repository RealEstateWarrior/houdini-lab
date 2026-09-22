# -*- coding: utf-8 -*-
"""実験178 — pcfind（近くの点さがし）の時間は、半径と「最大の数」でどう変わるか。

1 × 1 × 1 の中に一様に 10 万点を撒き、全部の点で pcfind(0, "P", @P, r, maxpts) を1回ずつ呼んで、見つかった数の平均を残す。
半径 r（0.01・0.02・0.05・0.1）と maxpts（10・100・1000）を変えて時間をはかる。
見つかる数の期待値は 10万 × (4/3)π r³（端の点では少なくなる）。
時間が「見つかった数」に比例するのか、「半径の中にある点の数」に比例するのかを見る。

    hython examples/178_pcfind_cost.py
"""
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    fog = geo.createNode("isooffset", "fog")
    fog.setInput(0, box)
    sc = geo.createNode("scatter::2.0", "pts")
    sc.setInput(0, fog)
    sc.parm("forcetotal").set(1)
    sc.parm("npts").set(100000)
    sc.parm("relaxpoints").set(0)
    sc.geometry()
    rows = []
    for r in (0.01, 0.02, 0.05, 0.1):
        for mx in (10, 100, 1000):
            w = geo.createNode("attribwrangle", f"pc_{int(r * 1000)}_{mx}")
            w.setInput(0, sc)
            w.addSpareParmTuple(hou.FloatParmTemplate("k", "k", 1, default_value=(1.0,)))
            w.parm("snippet").set(f"int n[] = pcfind(0, 'P', @P, {r} * ch('k'), {mx}); i@found = len(n);")
            w.geometry()
            best = 1e9
            for i in range(2):
                w.parm("k").set(1.0 + (i + 1) * 1e-7)     # 計算し直させる（実験173）
                t0 = time.perf_counter()
                g = w.geometry()
                best = min(best, time.perf_counter() - t0)
            found = g.pointIntAttribValues("found")
            rows.append({"radius": r, "maxpts": mx, "mean_found": round(statistics.fmean(found), 2),
                         "expect_inside": round(100000 * 4 / 3 * math.pi * r ** 3, 2), "sec": round(best, 4),
                         "us_per_point": round(best / 100000 * 1e6, 3)})
            print(rows[-1])
    sop_bench.save(178, rows)


if __name__ == "__main__":
    main()
