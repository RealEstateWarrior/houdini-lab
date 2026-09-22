# -*- coding: utf-8 -*-
"""実験170 — Vellum の布は、Stretch Stiffness を下げるとどれだけ伸びるか。Substeps で硬さは変わるか。

1 × 1 の grid（21 × 21 点、縦に立てる）の上の辺を Pin Points で留め、重力で 2 秒ぶら下げる。
vellumconstraints（Cloth）の Stretch Stiffness を 1 × 10^e（e = 10 が既定）で変え、
いちばん伸びた辺の伸び率・辺の平均の伸び率・下の辺がどれだけ下がったかを測る。
vellumsolver の Substeps を 1 と 5 にして、同じ硬さでも伸び方が変わるかも見る。

    hython examples/170_vellum_stretch.py
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
    for e in (10, 4, 3, 2):
        for sub in (1, 5):
            vc = geo.createNode("vellumconstraints", f"vc{e}_{sub}")
            vc.setInput(0, grp)
            vc.parm("constrainttype").set("cloth")
            vc.parm("stretchstiffness").set(1.0)
            vc.parm("stretchstiffnessexp").set(e)
            vc.parm("pingroup").set("top")
            vs = geo.createNode("vellumsolver", f"vs{e}_{sub}")
            vs.setInput(0, vc, 0)
            vs.setInput(1, vc, 1)
            vs.parm("substeps").set(sub)
            t0 = time.perf_counter()
            for F in range(1, 50):
                hou.setFrame(F)
                g = vs.geometry()
            sec = time.perf_counter() - t0
            s = edge_stretch(g, rest)
            # 四角形の辺の長さは rest（対角線は四角形の辺としては出てこない）
            bottom = min(p.position()[1] for p in g.points())
            rows.append({"exp": e, "stiffness": 10.0 ** e, "substeps": sub, "max_stretch": round(max(s), 5),
                         "mean_stretch": round(statistics.fmean(s), 5), "bottom_y": round(bottom, 5),
                         "sag": round(-0.5 - bottom, 5), "sec_49f": round(sec, 2)})
            print(rows[-1])
    sop_bench.save(170, rows, {"rest_edge": rest})


if __name__ == "__main__":
    main()
