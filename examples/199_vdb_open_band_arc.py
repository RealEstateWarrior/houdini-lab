# -*- coding: utf-8 -*-
"""実験199 — vdbreshapesdf の Open で丸めた辺の半径が Offset × 升より約 3 升大きい（実験198）のは、SDF の帯の幅のせいか。

実験198 と同じ箱・同じ測り方（z = 0 の断面に光線を撃ち、辺の近くの点に円を当てはめる）で、
vdbfrompolygons の Exterior / Interior Band Voxels を 3・6・12・25 升に変え、Open を Offset 10 升でかける。
足し分 R − r が帯の幅と一緒に変われば帯のせい、変わらなければ別の理由。

    hython examples/199_vdb_open_band_arc.py
"""
import importlib.util
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

_spec = importlib.util.spec_from_file_location("e198", os.path.join(HERE, "examples", "198_vdb_open_arc.py"))
e198 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e198)


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    vox, k = 0.01, 10
    r = k * vox
    rows = []
    for band in (3, 6, 12, 25):
        sdf = geo.createNode("vdbfrompolygons", f"sdf{band}")
        sdf.setInput(0, box)
        sdf.parm("voxelsize").set(vox)
        sdf.parm("exteriorbandvoxels").set(band)
        sdf.parm("interiorbandvoxels").set(band)
        rs = geo.createNode("vdbreshapesdf", f"open{band}")
        rs.setInput(0, sdf)
        rs.parm("operation").set("open")
        rs.parm("voxeloffset").set(k)
        cv = geo.createNode("convertvdb", f"c{band}")
        cv.setInput(0, rs)
        cv.parm("conversion").set("poly")
        t0 = time.perf_counter()
        g = cv.geometry()
        sec = time.perf_counter() - t0
        allp = e198.hits(g)
        lo = 0.5 - 3 * r
        arc = [p for p in allp if lo < p[0] < 0.499 and lo < p[1] < 0.499]
        cx, cy, R, rms, mx = e198.fit_circle(arc)
        vol = sop_bench.volume(g)
        rows.append({"band": band, "offset": k, "r": r, "points": len(arc), "R": round(R, 5),
                     "extra_in_voxels": round((R - r) / vox, 3), "cx": round(cx, 5), "center_if_tangent": round(0.5 - R, 5),
                     "rms": round(rms, 6), "max_dev": round(mx, 6), "volume": round(vol, 6), "sec": round(sec, 3)})
        print(rows[-1])
    sop_bench.save(199, rows, {"voxel": vox})


if __name__ == "__main__":
    main()
