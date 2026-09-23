# -*- coding: utf-8 -*-
"""実験197 — SDF の帯（Band Voxels）を広げると、vdbreshapesdf の Close は凸な箱を削らなくなるか。Open の丸みは r に近づくか。

実験196 では、帯が既定（外 3・内 3 升）のまま Offset 5〜20 升で Close をかけると、凸な箱が最大 1.2% 削れ、
Open の丸みも r より 1〜3 割大きかった。帯を Offset より広く（外・内とも 25 升）して同じことをする。

    hython examples/197_vdb_band.py
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
    sdf.parm("exteriorbandvoxels").set(25)
    sdf.parm("interiorbandvoxels").set(25)
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
    sop_bench.save(197, rows, {"voxel": vox, "base_volume": round(v0, 6), "band": 25})


if __name__ == "__main__":
    main()
