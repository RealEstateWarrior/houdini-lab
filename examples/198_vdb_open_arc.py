# -*- coding: utf-8 -*-
"""実験198 — vdbreshapesdf の Open で丸めた箱の辺は、断面が円弧になっているか。半径はいくつか。

1 × 1 × 1 の箱を vdbfrompolygons（Voxel Size 0.01・帯は既定）で SDF にし、Open を Offset 5・10・20 升でかけて面に戻す。
z = 0 の面の中で、原点から 0〜90 度の向きに 721 本の光線を撃ち（hou.Geometry.intersect）、当たった点のうち
辺の近く（x・y とも 0.499 未満、0.5 − 3r より外）の点に円を当てはめる（最小二乗、Kasa 法）。
円弧なら当てはめの残差は升の大きさより十分小さく、中心は (0.5 − R, 0.5 − R) に来るはず。

    hython examples/198_vdb_open_arc.py
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def hits(geo):
    pts = []
    for i in range(721):
        a = math.radians(90 * i / 720)
        p, n, uvw = hou.Vector3(), hou.Vector3(), hou.Vector3()
        if geo.intersect(hou.Vector3(0, 0, 0), hou.Vector3(math.cos(a), math.sin(a), 0), p, n, uvw) >= 0:
            pts.append((p[0], p[1]))
    return pts


def fit_circle(pts):
    x, y = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
    A = np.column_stack([x, y, np.ones_like(x)])
    b = x * x + y * y
    cx2, cy2, c = np.linalg.lstsq(A, b, rcond=None)[0]
    cx, cy = cx2 / 2, cy2 / 2
    R = math.sqrt(c + cx * cx + cy * cy)
    res = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - R
    return cx, cy, R, float(np.sqrt(np.mean(res ** 2))), float(np.max(np.abs(res)))


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    vox = 0.01
    sdf = geo.createNode("vdbfrompolygons", "sdf")
    sdf.setInput(0, box)
    sdf.parm("voxelsize").set(vox)
    rows = []
    for k in (5, 10, 20):
        r = k * vox
        rs = geo.createNode("vdbreshapesdf", f"open{k}")
        rs.setInput(0, sdf)
        rs.parm("operation").set("open")
        rs.parm("voxeloffset").set(k)
        cv = geo.createNode("convertvdb", f"c{k}")
        cv.setInput(0, rs)
        cv.parm("conversion").set("poly")
        t0 = time.perf_counter()
        g = cv.geometry()
        sec = time.perf_counter() - t0
        allp = hits(g)
        lo = 0.5 - 3 * r
        arc = [p for p in allp if lo < p[0] < 0.499 and lo < p[1] < 0.499]
        cx, cy, R, rms, mx = fit_circle(arc)
        diag = [p for p in allp if abs(p[0] - p[1]) < 1e-3][0]
        rows.append({"offset": k, "r": r, "points": len(arc), "cx": round(cx, 5), "cy": round(cy, 5), "R": round(R, 5),
                     "R_over_r": round(R / r, 3), "center_if_tangent": round(0.5 - R, 5),
                     "rms": round(rms, 6), "max_dev": round(mx, 6), "rms_in_voxels": round(rms / vox, 3),
                     "diag_x": round(diag[0], 5), "diag_if_arc_r": round(0.5 - r + r / math.sqrt(2), 5),
                     "sec": round(sec, 3)})
        print(rows[-1])
    sop_bench.save(198, rows, {"voxel": vox})


if __name__ == "__main__":
    main()
