# -*- coding: utf-8 -*-
"""実験196 — vdbreshapesdf の Open は、箱の角を半径 r（= Offset × 升）で丸めるか。体積は実験152 の「角を丸めた箱」の式か。

1 × 1 × 1 の箱を vdbfrompolygons（Voxel Size 0.01）で SDF にし、vdbreshapesdf の Open・Close を Offset 5・10・20 升でかける。
Open（Erode してから Dilate）は、外へ尖った角を半径 r で丸めるはずで、体積は
  (1−2r)³ + 6r(1−2r)² + 3πr²(1−2r) + (4/3)πr³（実験152 と同じ式）
になるはず。Close（Dilate してから Erode）は、へこんだ所が無い箱では何も変えないはず。

    hython examples/196_vdb_open_box.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def rounded(r):
    return (1 - 2 * r) ** 3 + 6 * r * (1 - 2 * r) ** 2 + 3 * math.pi * r * r * (1 - 2 * r) + 4 / 3 * math.pi * r ** 3


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    vox = 0.01
    sdf = geo.createNode("vdbfrompolygons", "sdf")
    sdf.setInput(0, box)
    sdf.parm("voxelsize").set(vox)
    base = geo.createNode("convertvdb", "base")
    base.setInput(0, sdf)
    base.parm("conversion").set("poly")
    v0 = sop_bench.volume(base.geometry())
    rows = [{"operation": "（なし）", "offset": 0, "r": 0.0, "volume": round(v0, 6), "want": 1.0, "sec": 0.0}]
    for op in ("open", "close"):
        for k in (5, 10, 20):
            rs = geo.createNode("vdbreshapesdf", f"{op}{k}")
            rs.setInput(0, sdf)
            rs.parm("operation").set(op)
            rs.parm("voxeloffset").set(k)
            cv = geo.createNode("convertvdb", f"c{op}{k}")
            cv.setInput(0, rs)
            cv.parm("conversion").set("poly")
            t0 = time.perf_counter()
            v = sop_bench.volume(cv.geometry())
            sec = time.perf_counter() - t0
            r = k * vox
            want = rounded(r) if op == "open" else 1.0
            rows.append({"operation": op, "offset": k, "r": r, "volume": round(v, 6), "want": round(want, 6),
                         "ratio_to_base": round(v / v0, 6), "want_ratio": round(want, 6), "sec": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(196, rows, {"voxel": vox, "base_volume": round(v0, 6)})


if __name__ == "__main__":
    main()
