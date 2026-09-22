# -*- coding: utf-8 -*-
"""実験188 — hairgen の毛の本数は Density × 面の面積か。1本の点の数と長さは何で決まるか。

grid（面積 A = 1・4）と球（半径 1、面積 約 4π）を皮にして、hairgen（ガイドなし）を Density 100・1000・5000 で生やす。
毛（線）の本数 ÷ 面積 が Density に合うか、Force Count を入れたときに指定の本数ちょうどか、
1本あたりの点の数が Segments（既定 8）+ 1 か、長さが Length（既定 0.05）か、を測る。

    hython examples/188_hairgen_density.py
"""
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def area(node):
    return sum(p.intrinsicValue("measuredarea") for p in node.geometry().prims())


def main():
    geo = sop_bench.fresh()
    g1 = geo.createNode("grid", "g1")
    g1.parmTuple("size").set((1.0, 1.0))
    g2 = geo.createNode("grid", "g2")
    g2.parmTuple("size").set((2.0, 2.0))
    sp = geo.createNode("sphere", "sp")
    sp.parm("type").set("polymesh")
    sp.parm("rows").set(48)
    sp.parm("cols").set(96)
    rows = []
    for name, skin in (("grid 1×1", g1), ("grid 2×2", g2), ("球 半径1", sp)):
        A = area(skin)
        for dens, force in ((100.0, 0), (1000.0, 0), (5000.0, 0), (1000.0, 1)):
            h = geo.createNode("hairgen::2.0", f"h_{skin.name()}_{int(dens)}_{force}")
            h.setInput(0, skin)
            h.parm("density").set(dens)
            h.parm("forcecount").set(force)
            h.parm("count").set(2500)
            t0 = time.perf_counter()
            g = h.geometry()
            sec = time.perf_counter() - t0
            curves = g.prims()
            npts = [c.numVertices() for c in curves]
            lens = [c.intrinsicValue("measuredperimeter") for c in curves[:500]]
            rows.append({"skin": name, "area": round(A, 4), "density": dens, "force": force, "curves": len(curves),
                         "per_area": round(len(curves) / A, 2), "pts_per_curve": sorted(set(npts))[:3],
                         "length_mean": round(statistics.fmean(lens), 5) if lens else None,
                         "length_spread": round(max(lens) - min(lens), 5) if lens else None, "sec": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(188, rows)


if __name__ == "__main__":
    main()
