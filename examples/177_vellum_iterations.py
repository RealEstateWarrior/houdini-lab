# -*- coding: utf-8 -*-
"""実験177 — Vellum の布の伸びは、Constraint Iterations を増やすと Substeps と同じように減るか。

1 × 1 の grid（21 × 21 点、縦に立てる）の上の辺を Pin Points で留め、重力で 2 秒ぶら下げる。
実験170 と同じ布（上の辺を留めた 1 × 1、21 × 21 点）を、既定の Stretch Stiffness（10^10）でぶら下げ、
vellumsolver の Constraint Iterations（既定 100）を 25・100・400・1600、Substeps を 1 と 5 にして、伸びと時間を測る。
実験170 では Substeps 1 → 5 で、いちばん伸びた辺が 2.3% → 0.1% に減った。

    hython examples/177_vellum_iterations.py
"""
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def edge_stretch(geo_now, rest_len):
    out = []
    for pr in geo_now.prims():
        vs = [v.point() for v in pr.vertices()]
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            out.append((a.position() - b.position()).length())
    return [x / rest_len for x in out]


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "cloth")
    grid.parm("orient").set("xy")
    grid.parmTuple("size").set((1.0, 1.0))
    grid.parm("rows").set(21)
    grid.parm("cols").set(21)
    grp = geo.createNode("groupexpression", "top")
    grp.setInput(0, grid)
    grp.parm("grouptype").set("point")
    grp.parm("groupname1").set("top")
    grp.parm("snippet1").set("@P.y > 0.49")
    rest = 1.0 / 20
    rows = []
    e = 10
    for it in (25, 100, 400, 1600):
        for sub in (1, 5):
            vc = geo.createNode("vellumconstraints", f"vc{it}_{sub}")
            vc.setInput(0, grp)
            vc.parm("constrainttype").set("cloth")
            vc.parm("stretchstiffness").set(1.0)
            vc.parm("stretchstiffnessexp").set(e)
            vc.parm("pingroup").set("top")
            vs = geo.createNode("vellumsolver", f"vs{it}_{sub}")
            vs.setInput(0, vc, 0)
            vs.setInput(1, vc, 1)
            vs.parm("substeps").set(sub)
            vs.parm("niter").set(it)
            t0 = time.perf_counter()
            for F in range(1, 50):
                hou.setFrame(F)
                g = vs.geometry()
            sec = time.perf_counter() - t0
            s = edge_stretch(g, rest)
            # 四角形の辺の長さは rest（対角線は四角形の辺としては出てこない）
            bottom = min(p.position()[1] for p in g.points())
            rows.append({"iterations": it, "substeps": sub, "max_stretch": round(max(s), 5),
                         "mean_stretch": round(statistics.fmean(s), 5), "bottom_y": round(bottom, 5),
                         "sag": round(-0.5 - bottom, 5), "sec_49f": round(sec, 2)})
            print(rows[-1])
    sop_bench.save(177, rows, {"rest_edge": rest})


if __name__ == "__main__":
    main()
