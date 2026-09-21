# -*- coding: utf-8 -*-
"""実験138 — vdbfrompolygons の SDF の値は、本当の距離か。

半径1の球（polymesh 200×200）から SDF を作り、中心を通る線の上で volumesample した値を、
本当の符号付き距離 |p| − 1 と比べる。SDF は表面の近く（ナローバンド）しか持たないので、
遠くでは値が一定（背景の値）になるはず。その幅が Half Width（ボクセル何個分か）で決まるかも見る。

    hython examples/138_sdf_values.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    sp = geo.createNode("sphere", "sp")
    sp.parm("type").set("polymesh")
    sp.parm("rows").set(200)
    sp.parm("cols").set(200)
    line = geo.createNode("line", "probe")
    line.parmTuple("origin").set((0.0, 0.0, 0.0))
    line.parmTuple("dir").set((1.0, 0.3, 0.2))
    line.parm("dist").set(2.0)
    line.parm("points").set(401)
    rows = []
    for voxel in (0.05, 0.02):
        for half in (3, 6):
            v = geo.createNode("vdbfrompolygons", f"v_{int(voxel * 1000)}_{half}")
            v.setInput(0, sp)
            v.parm("voxelsize").set(voxel)
            v.parm("exteriorbandvoxels").set(half)
            v.parm("interiorbandvoxels").set(half)
            t0 = time.perf_counter()
            v.geometry()
            sec = time.perf_counter() - t0
            wr = geo.createNode("attribwrangle", f"s_{int(voxel * 1000)}_{half}")
            wr.setInput(0, line)
            wr.setInput(1, v)
            wr.parm("snippet").set("f@sdf = volumesample(1, 0, @P); f@want = length(@P) - 1;")
            g = wr.geometry()
            sdf = g.pointFloatAttribValues("sdf")
            want = g.pointFloatAttribValues("want")
            band = half * voxel
            inside = [(s, w) for s, w in zip(sdf, want) if abs(w) < band - voxel]
            outside = [s for s, w in zip(sdf, want) if abs(w) > band + voxel]
            err = max(abs(s - w) for s, w in inside)
            rows.append({"voxel": voxel, "half": half, "band": round(band, 4),
                         "err_in_band": round(err, 6), "n_in_band": len(inside),
                         "outside_values": sorted({round(s, 5) for s in outside}),
                         "sec": round(sec, 3),
                         "profile": [[round(w, 4), round(s, 5)] for s, w in zip(sdf, want)][::8]})
            print({k: rows[-1][k] for k in rows[-1] if k != "profile"})
    path = os.path.join(sop_bench.OUT, "138_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
