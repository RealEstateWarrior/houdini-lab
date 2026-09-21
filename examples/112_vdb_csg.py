# -*- coding: utf-8 -*-
"""実験112 — vdbcombine の和・積・差は、球2つの体積の式に合うか。

半径1の球を2つ、中心の距離 d で重ねる。重なり（レンズ）の体積は
    V_lens = π (4r + d)(2r − d)² / 12
和 = 2·(4/3)π − V_lens、積 = V_lens、差（A − B）= (4/3)π − V_lens。
ボクセルの大きさを変えて、式にどこまで近づくかを見る。
元の球は細かい多角形（実験094と同じ作り方）なので、その分のずれも別に測る。

    hython examples/112_vdb_csg.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

D = 1.0
VOXELS = [0.1, 0.05, 0.025, 0.0125]


def lens(r, d):
    return math.pi * (4 * r + d) * (2 * r - d) ** 2 / 12


def main():
    geo = sop_bench.fresh()
    spheres = []
    for name, x in (("a", 0.0), ("b", D)):
        sp = geo.createNode("sphere", "sp_" + name)
        sp.parm("type").set("polymesh")
        sp.parm("rows").set(200)
        sp.parm("cols").set(200)
        sp.parmTuple("t").set((x, 0.0, 0.0))
        spheres.append(sp)
    poly_volume = sop_bench.volume(spheres[0].geometry())
    ball = 4 / 3 * math.pi
    want = {"sdfunion": 2 * ball - lens(1, D), "sdfintersect": lens(1, D),
            "sdfdifference": ball - lens(1, D)}

    combine_probe = geo.createNode("vdbcombine", "probe")
    menu = list(combine_probe.parm("operation").menuItems())
    print("operation の選択肢:", menu)
    ops = [op for op in ("sdfunion", "sdfintersect", "sdfdifference") if op in menu]

    rows = []
    for voxel in VOXELS:
        vdbs = []
        for sp in spheres:
            v = geo.createNode("vdbfrompolygons", f"v_{sp.name()}_{voxel}".replace(".", "_"))
            v.setInput(0, sp)
            v.parm("voxelsize").set(voxel)
            vdbs.append(v)
        for op in ops:
            comb = geo.createNode("vdbcombine", f"c_{op}_{voxel}".replace(".", "_"))
            comb.setInput(0, vdbs[0])
            comb.setInput(1, vdbs[1])
            comb.parm("operation").set(op)
            back = geo.createNode("convertvdb", f"b_{op}_{voxel}".replace(".", "_"))
            back.setInput(0, comb)
            back.parm("conversion").set("poly")
            t0 = time.perf_counter()
            got = sop_bench.volume(back.geometry())
            sec = time.perf_counter() - t0
            rows.append({"voxel": voxel, "op": op, "volume": round(got, 6),
                         "want": round(want[op], 6),
                         "rel": round(got / want[op] - 1, 6), "sec": round(sec, 3)})
            print(rows[-1])
    path = os.path.join(sop_bench.OUT, "112_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"d": D, "menu": menu, "poly_ball": round(poly_volume, 6),
                   "ball": round(ball, 6), "rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
