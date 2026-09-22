# -*- coding: utf-8 -*-
"""実験145 — mirror の継ぎ目は、どこまで離れていても1点にまとまるか。

10×10 点の grid（1×1）を、左の縁が x = g になるように置き、x = 0 の面で mirror する。
継ぎ目の点が全部まとまれば 200 − 10 = 190 点、まとまらなければ 200 点。
隙間 g を 0〜0.001 と振り、Consolidate Seam（既定 0.0001）の前後で数が変わるかを見る。
隙間は両側で 2g になる点に注意（元と鏡像の距離）。

    hython examples/145_mirror_seam.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "grid")
    grid.parmTuple("size").set((1.0, 1.0))
    grid.parm("rows").set(10)
    grid.parm("cols").set(10)
    grid.parm("orient").set("xy")
    rows = []
    for gap in (0.0, 0.00002, 0.00004, 0.00005, 0.00006, 0.0001, 0.001):
        for tol in (0.0001, 0.001):
            for on in (1, 0):
                xf = geo.createNode("xform", f"x_{gap}_{tol}_{on}")
                xf.setInput(0, grid)
                xf.parm("tx").set(0.5 + gap)
                m = geo.createNode("mirror", f"m_{gap}_{tol}_{on}")
                m.setInput(0, xf)
                m.parm("consolidatepts").set(on)
                m.parm("consolidatetol").set(tol)
                t0 = time.perf_counter()
                g = m.geometry()
                sec = time.perf_counter() - t0
                xs = sorted(p.position()[0] for p in g.points())
                inner = [x for x in xs if abs(x) < 0.01]
                rows.append({"gap": gap, "tol": tol, "consolidate": on, "points": len(g.points()),
                             "prims": len(g.prims()), "seam_x": sorted({round(x, 6) for x in inner}),
                             "sec": round(sec, 4)})
                print(rows[-1])
    sop_bench.save(145, rows)


if __name__ == "__main__":
    main()
