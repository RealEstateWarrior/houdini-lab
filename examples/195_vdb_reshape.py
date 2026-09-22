# -*- coding: utf-8 -*-
"""実験195 — vdbreshapesdf の Dilate / Erode は、球の半径を Offset（升目の数）× 升の大きさだけ変えるか。

半径 1 の球（polymesh 96×192）を vdbfrompolygons（Voxel Size 0.02）で SDF にし、vdbreshapesdf の Operation と Offset（升目の数）を変える。
convertvdb で面に戻して体積を測り、同じ体積の球の半径を出す（r = (3V/4π)^(1/3)）。
Dilate なら半径が + Offset × 0.02、Erode なら − になるはず。Iterations（既定 4）を 1 にしたときも比べる。Open・Close も見る。

    hython examples/195_vdb_reshape.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def radius_of(node):
    v = sop_bench.volume(node.geometry())
    return (3 * v / (4 * math.pi)) ** (1 / 3), v


def main():
    geo = sop_bench.fresh()
    sp = geo.createNode("sphere", "sp")
    sp.parm("type").set("polymesh")
    sp.parm("rows").set(96)
    sp.parm("cols").set(192)
    vox = 0.02
    sdf = geo.createNode("vdbfrompolygons", "sdf")
    sdf.setInput(0, sp)
    sdf.parm("voxelsize").set(vox)
    base = geo.createNode("convertvdb", "base")
    base.setInput(0, sdf)
    base.parm("conversion").set("poly")
    r0, v0 = radius_of(base)
    rows = [{"operation": "（なし）", "offset": 0, "iterations": 0, "radius": round(r0, 6), "change": 0.0, "want": 0.0, "sec": 0.0}]
    cases = [(op, k, it) for op in ("dilate", "erode") for k in (1, 2, 5) for it in (4, 1)] + [("open", 2, 4), ("close", 2, 4)]
    for op, k, it in cases:
        rs = geo.createNode("vdbreshapesdf", f"r_{op}_{k}_{it}")
        rs.setInput(0, sdf)
        rs.parm("operation").set(op)
        rs.parm("voxeloffset").set(k)
        rs.parm("iterations").set(it)
        cv = geo.createNode("convertvdb", f"c_{op}_{k}_{it}")
        cv.setInput(0, rs)
        cv.parm("conversion").set("poly")
        t0 = time.perf_counter()
        r, v = radius_of(cv)
        sec = time.perf_counter() - t0
        want = {"dilate": k * vox, "erode": -k * vox}.get(op, 0.0)
        rows.append({"operation": op, "offset": k, "iterations": it, "radius": round(r, 6), "change": round(r - r0, 6),
                     "want": round(want, 6), "change_in_voxels": round((r - r0) / vox, 3), "sec": round(sec, 3)})
        print(rows[-1])
    sop_bench.save(195, rows, {"voxel": vox, "base_volume": round(v0, 6)})


if __name__ == "__main__":
    main()
