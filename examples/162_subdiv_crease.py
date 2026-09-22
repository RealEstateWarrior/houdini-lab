# -*- coding: utf-8 -*-
"""実験162 — subdivide の辺の crease の重み w で、箱はどこまで箱のままか。

1×1×1 の箱の全部の辺に crease SOP で重み w を付け、subdivide（OpenSubdiv Catmull-Clark）で細かくする。
OpenSubdiv の半シャープな crease は「重み w の辺は、w 回目の細分までは尖ったまま、そのあとなめらか」のはず。
それなら Iterations ≤ w のときは元の箱と同じ形（体積 1）になる。w と Iterations を変えて、体積と、
角の点が元の角 (0.5, 0.5, 0.5) からどれだけ離れたかを測る。

    hython examples/162_subdiv_crease.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    rows = []
    for w in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 10.0):
        cr = geo.createNode("crease", f"c{int(w * 10)}")
        cr.setInput(0, box)
        cr.parm("op").set("set")
        cr.parm("crease").set(w)
        for it in (2, 4):
            sd = geo.createNode("subdivide", f"s{int(w * 10)}_{it}")
            sd.setInput(0, cr)
            sd.parm("algorithm").set("osdcc")
            sd.parm("iterations").set(it)
            t0 = time.perf_counter()
            g = sd.geometry()
            sec = time.perf_counter() - t0
            corner = hou.Vector3(0.5, 0.5, 0.5)
            dmin = min((p.position() - corner).length() for p in g.points())
            ext = max(max(abs(c) for c in p.position()) for p in g.points())
            rows.append({"weight": w, "iterations": it, "points": len(g.points()), "prims": len(g.prims()),
                         "volume": round(sop_bench.volume(g), 6), "corner_gap": round(dmin, 6),
                         "max_extent": round(ext, 6), "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(162, rows)


if __name__ == "__main__":
    main()
