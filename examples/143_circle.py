# -*- coding: utf-8 -*-
"""実験143 — circle（Polygon）の周と面積は、正 n 角形の式どおりか。弧の Divisions は何を数えるか。

半径 1 の円を Divisions = n の Polygon で作ると、頂点が円周に乗る正 n 角形なら
周 2n·sin(π/n)、面積 (n/2)·sin(2π/n) になる。Arc Type を Open Arc にして 0〜90° を切ると、
点の数が n か n+1 か（Divisions が点を数えるか辺を数えるか）を見る。

    hython examples/143_circle.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    rows, arcs = [], []
    for n in (3, 4, 6, 12, 48, 192, 768):
        c = geo.createNode("circle", f"c{n}")
        c.parm("type").set("poly")
        c.parm("divs").set(n)
        t0 = time.perf_counter()
        g = c.geometry()
        sec = time.perf_counter() - t0
        pr = g.prims()[0]
        rs = [p.position().length() for p in g.points()]
        rows.append({"divs": n, "points": len(g.points()), "rmin": round(min(rs), 6), "rmax": round(max(rs), 6),
                     "perimeter": round(pr.intrinsicValue("measuredperimeter"), 6),
                     "area": round(pr.intrinsicValue("measuredarea"), 6),
                     "want_perimeter": round(2 * n * math.sin(math.pi / n), 6),
                     "want_area": round(n / 2 * math.sin(2 * math.pi / n), 6), "sec": round(sec, 4)})
        print(rows[-1])
    for arc in ("openarc", "closedarc", "slicedarc"):
        for n in (4, 12):
            c = geo.createNode("circle", f"a_{arc}_{n}")
            c.parm("type").set("poly")
            c.parm("arc").set(arc)
            c.parmTuple("angle").set((0.0, 90.0))
            c.parm("divs").set(n)
            g = c.geometry()
            pr = g.prims()[0]
            arcs.append({"arc": arc, "divs": n, "points": len(g.points()), "prims": len(g.prims()),
                         "closed": bool(pr.intrinsicValue("closed")),
                         "perimeter": round(pr.intrinsicValue("measuredperimeter"), 6),
                         "area": round(pr.intrinsicValue("measuredarea"), 6)})
            print(arcs[-1])
    sop_bench.save(143, rows, {"arcs": arcs})


if __name__ == "__main__":
    main()
