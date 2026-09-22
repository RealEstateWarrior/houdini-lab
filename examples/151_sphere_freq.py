# -*- coding: utf-8 -*-
"""実験151 — sphere の Polygon（Frequency）は、点 10f²+2・面 20f² の測地球か。同じ点の数なら Polygon Mesh より丸いか。

半径 1 の sphere を Primitive Type = Polygon にし、Frequency f を 1〜12 と変えて、
点と面の数、頂点が球面に乗っているか、面積と体積を測る。
同じくらいの点の数の Polygon Mesh（Rows × Columns、Rows = Columns / 2）と、
面積と体積の足りなさ（4π・4π/3 との差）を比べる。

    hython examples/151_sphere_freq.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def measure(node):
    t0 = time.perf_counter()
    g = node.geometry()
    sec = time.perf_counter() - t0
    rs = [p.position().length() for p in g.points()]
    area = sum(pr.intrinsicValue("measuredarea") for pr in g.prims())
    sides = sorted({pr.numVertices() for pr in g.prims()})
    return {"points": len(rs), "prims": len(g.prims()), "sides": sides,
            "rmin": round(min(rs), 6), "rmax": round(max(rs), 6),
            "area": round(area, 6), "volume": round(sop_bench.volume(g), 6), "sec": round(sec, 4)}


def main():
    geo = sop_bench.fresh()
    poly = []
    for f in (1, 2, 3, 4, 6, 8, 12):
        s = geo.createNode("sphere", f"p{f}")
        s.parm("type").set("poly")
        s.parm("freq").set(f)
        r = measure(s)
        r.update({"freq": f, "want_points": 10 * f * f + 2, "want_prims": 20 * f * f})
        poly.append(r)
        print(r)
    mesh = []
    for cols in (8, 12, 16, 24, 32, 48, 64):
        s = geo.createNode("sphere", f"m{cols}")
        s.parm("type").set("polymesh")
        s.parm("rows").set(cols // 2 + 1)
        s.parm("cols").set(cols)
        r = measure(s)
        r.update({"rows": cols // 2 + 1, "cols": cols})
        mesh.append(r)
        print(r)
    sop_bench.save(151, poly, {"mesh": mesh, "area": 4 * math.pi, "volume": 4 / 3 * math.pi})


if __name__ == "__main__":
    main()
