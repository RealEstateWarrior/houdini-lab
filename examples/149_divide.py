# -*- coding: utf-8 -*-
"""実験149 — divide の Bricker は何枚に切るか。Convex の Maximum Edges で n 角形は何枚になるか。

1×1 の正方形1枚（grid 2×2 点、中心が原点）を、Bricker Polygons の Size = s で切る。
升目が原点から並ぶなら、枚数は (1/s)²（割り切れないときは端数の分だけ増える）。Offset でずらすと増えるかを見る。
正 n 角形（circle の Polygon）を Convex Polygons・Maximum Edges = 3 / 4 で割り、枚数と面積を数える。

    hython examples/149_divide.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def area(g):
    return sum(p.intrinsicValue("measuredarea") for p in g.prims())


def main():
    geo = sop_bench.fresh()
    sq = geo.createNode("grid", "sq")
    sq.parmTuple("size").set((1.0, 1.0))
    sq.parm("rows").set(2)
    sq.parm("cols").set(2)
    bricks = []
    for s in (0.5, 0.25, 0.3, 0.1):
        for off in (0.0, 0.05):
            d = geo.createNode("divide", f"b{int(s * 100)}_{int(off * 100)}")
            d.setInput(0, sq)
            d.parm("convex").set(0)
            d.parm("brick").set(1)
            for ax in "xyz":
                d.parm("size" + ax).set(s)
                d.parm("offset" + ax).set(off)
            t0 = time.perf_counter()
            g = d.geometry()
            sec = time.perf_counter() - t0
            sides = sorted({p.numVertices() for p in g.prims()})
            bricks.append({"size": s, "offset": off, "prims": len(g.prims()), "points": len(g.points()),
                           "sides": sides, "area": round(area(g), 6), "sec": round(sec, 4)})
            print(bricks[-1])
    convex = []
    for n in (5, 8, 12, 13):
        c = geo.createNode("circle", f"c{n}")
        c.parm("type").set("poly")
        c.parm("divs").set(n)
        a0 = area(c.geometry())
        for k in (3, 4):
            d = geo.createNode("divide", f"cv{n}_{k}")
            d.setInput(0, c)
            d.parm("numsides").set(k)
            g = d.geometry()
            convex.append({"n": n, "max_edges": k, "prims": len(g.prims()),
                           "sides": sorted(p.numVertices() for p in g.prims()),
                           "area": round(area(g), 6), "area0": round(a0, 6)})
            print(convex[-1])
    sop_bench.save(149, bricks, {"convex": convex})


if __name__ == "__main__":
    main()
