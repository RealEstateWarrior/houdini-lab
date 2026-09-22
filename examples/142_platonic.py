# -*- coding: utf-8 -*-
"""実験142 — platonic の Radius は「中心から頂点まで」か。面積と体積を式と突き合わせる。

正多面体は、外接球の半径 R を決めれば、辺の長さも面積も体積も式で決まる。
Radius = 1 で作った5種類について、中心から頂点までの距離・辺の長さ・面積・体積を測り、
外接半径 1 の式の値と比べる。

    hython examples/142_platonic.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

PHI = (1 + 5 ** 0.5) / 2
# 外接半径 R=1 のときの辺の長さ a と、a から面積・体積を出す式
SOLIDS = {
    "tetrahedron": (4, 4 / 6 ** 0.5, lambda a: 3 ** 0.5 * a * a, lambda a: a ** 3 / (6 * 2 ** 0.5)),
    "cube": (6, 2 / 3 ** 0.5, lambda a: 6 * a * a, lambda a: a ** 3),
    "octahedron": (8, 2 ** 0.5, lambda a: 2 * 3 ** 0.5 * a * a, lambda a: 2 ** 0.5 / 3 * a ** 3),
    "icosahedron": (20, 1 / math.sin(2 * math.pi / 5), lambda a: 5 * 3 ** 0.5 * a * a,
                    lambda a: 5 * (3 + 5 ** 0.5) / 12 * a ** 3),
    "dodecahedron": (12, 4 / (3 ** 0.5 * (1 + 5 ** 0.5)), lambda a: 3 * (25 + 10 * 5 ** 0.5) ** 0.5 * a * a,
                     lambda a: (15 + 7 * 5 ** 0.5) / 4 * a ** 3),
}


def main():
    geo = sop_bench.fresh()
    labels = None
    rows = []
    for i in range(5):
        n = geo.createNode("platonic", f"p{i}")
        n.parm("type").set(i)
        n.parm("radius").set(1.0)
        if labels is None:
            labels = list(n.parm("type").parmTemplate().menuLabels())
        t0 = time.perf_counter()
        g = n.geometry()
        sec = time.perf_counter() - t0
        pts = [p.position() for p in g.points()]
        c = sum(pts, pts[0] * 0) / len(pts)
        dist = [(p - c).length() for p in pts]
        edges = []
        for prim in g.prims():
            vs = [v.point().position() for v in prim.vertices()]
            edges += [(vs[k] - vs[k - 1]).length() for k in range(len(vs))]
        area = sum(pr.intrinsicValue("measuredarea") for pr in g.prims())
        vol = sop_bench.volume(g)
        rows.append({"type": i, "label": labels[i], "points": len(pts), "prims": len(g.prims()),
                     "rmin": round(min(dist), 6), "rmax": round(max(dist), 6),
                     "edge_min": round(min(edges), 6), "edge_max": round(max(edges), 6),
                     "area": round(area, 6), "volume": round(vol, 6), "sec": round(sec, 4)})
        print(rows[-1])
    sop_bench.save(142, rows, {"labels": labels,
                               "formula": {k: {"faces": v[0], "edge": v[1], "area": v[2](v[1]), "volume": v[3](v[1])}
                                           for k, v in SOLIDS.items()}})


if __name__ == "__main__":
    main()
