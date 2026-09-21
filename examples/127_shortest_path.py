# -*- coding: utf-8 -*-
"""実験127 — findshortestpath の道のりは、辺をたどった最短の長さと同じか。

実験119 で、distancealonggeometry の Edge は「辺をたどった道のり」だと分かった。
findshortestpath が出す道の長さ（cost）も同じになるはず。
四角の網（2×2・41×41）で、真ん中から4つの点へ道を引き、
  cost・出てきた道の線の長さ・Edge の距離・|x|+|z|
の4つを比べる。

    hython examples/127_shortest_path.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

TARGETS = [(1.0, 1.0), (1.0, 0.0), (0.5, 0.25), (-0.8, 0.6)]


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "g")
    grid.parmTuple("size").set((2.0, 2.0))
    grid.parm("rows").set(41)
    grid.parm("cols").set(41)
    marks = geo.createNode("attribwrangle", "marks")
    marks.setInput(0, grid)
    marks.parm("snippet").set(
        'if (length(@P) < 1e-5) setpointgroup(0, "start", @ptnum, 1);\n'
        'vector ts[] = {' + ",".join("{%g,0,%g}" % t for t in TARGETS) + '};\n'
        'foreach (int i; vector t; ts) if (distance(@P, t) < 1e-5) i@target = i + 1;\n'
        'if (i@target > 0) setpointgroup(0, "end", @ptnum, 1);')
    edge = geo.createNode("distancealonggeometry", "edge")
    edge.setInput(0, marks)
    edge.parm("startpts").set("start")
    edge.parm("distmetric").set("edge")
    sp = geo.createNode("findshortestpath", "sp")
    sp.setInput(0, marks)
    sp.parm("startpts").set("start")
    sp.parm("endpts").set("end")
    sp.parm("multiplicity").set("anytoeach")
    sp.parm("enableoutputcost").set(True)
    t0 = time.perf_counter()
    out = sp.geometry()
    sec = time.perf_counter() - t0
    meas = geo.createNode("measure", "len")
    meas.setInput(0, sp)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    paths = meas.geometry()
    edge_geo = edge.geometry()
    rows = []
    cost_name = sp.parm("outputcost").evalAsString()
    for prim in paths.prims():
        pts = prim.points()
        last = pts[-1]
        tx, tz = last.position()[0], last.position()[2]
        cost_attr = paths.findPointAttrib(cost_name) or paths.findPrimAttrib(cost_name)
        if cost_attr is None:
            cost = None
        elif cost_attr.type().name() == "Point":
            cost = last.attribValue(cost_name)
        else:
            cost = prim.attribValue(cost_name)
        key = (round(tx, 4), round(tz, 4))
        edge_d = next((p.attribValue("dist") for p in edge_geo.points()
                       if (round(p.position()[0], 4), round(p.position()[2], 4)) == key), None)
        rows.append({"target": [round(tx, 4), round(tz, 4)], "points_on_path": len(pts),
                     "path_length": round(prim.attribValue("len"), 6),
                     "cost": round(cost, 6) if cost is not None else None,
                     "manhattan": round(abs(tx) + abs(tz), 6),
                     "edge_dist": round(edge_d, 6) if edge_d is not None else None})
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "127_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "sec": round(sec, 4), "cost_attr": cost_name,
                   "prims": out.intrinsicValue("primitivecount")}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path, "秒", sec)


if __name__ == "__main__":
    main()
