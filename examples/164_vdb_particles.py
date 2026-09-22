# -*- coding: utf-8 -*-
"""実験164 — vdbfromparticles で2つの粒をつなぐと、体積は「2つの球の和」の式どおりか。

pscale = 0.5 の2点を間隔 s に置き、vdbfromparticles（距離の VDB）→ convertvdb（ポリゴン）で面にして体積を測る。
半径 r の球2つが間隔 s で重なったときの体積は 2·(4/3)πr³ − π(4r + s)(2r − s)²/12（s < 2r）。
Voxel Size を 0.05・0.025・0.0125 と変え、Point Radius Scale が半径をそのまま使うか（r = pscale）も確かめる。

    hython examples/164_vdb_particles.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def union(r, s):
    one = 4 / 3 * math.pi * r ** 3
    if s >= 2 * r:
        return 2 * one
    return 2 * one - math.pi * (4 * r + s) * (2 * r - s) ** 2 / 12


def main():
    geo = sop_bench.fresh()
    rows = []
    r = 0.5
    for s in (0.0, 0.5, 0.8, 1.2):
        pts = geo.createNode("attribwrangle", f"p{int(s * 10)}")
        pts.parm("class").set("detail")
        pts.parm("snippet").set(f"int a = addpoint(0, set({-s / 2}, 0, 0)); int b = addpoint(0, set({s / 2}, 0, 0));"
                                f" setpointattrib(0, 'pscale', a, {r}); setpointattrib(0, 'pscale', b, {r});")
        for vox in (0.05, 0.025, 0.0125):
            vp = geo.createNode("vdbfromparticles", f"v{int(s * 10)}_{int(vox * 10000)}")
            vp.setInput(0, pts)
            vp.parm("voxelsize").set(vox)
            cv = geo.createNode("convertvdb", f"c{int(s * 10)}_{int(vox * 10000)}")
            cv.setInput(0, vp)
            cv.parm("conversion").set("poly")
            t0 = time.perf_counter()
            g = cv.geometry()
            sec = time.perf_counter() - t0
            bb = g.boundingBox()
            want = union(r, s)
            vol = sop_bench.volume(g)
            rows.append({"gap": s, "voxel": vox, "volume": round(vol, 6), "want": round(want, 6),
                         "ratio": round(vol / want, 5), "size_x": round(bb.sizevec()[0], 4), "want_x": round(s + 2 * r, 4),
                         "size_y": round(bb.sizevec()[1], 4), "prims": len(g.prims()), "sec": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(164, rows, {"radius": r})


if __name__ == "__main__":
    main()
