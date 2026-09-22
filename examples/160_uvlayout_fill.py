# -*- coding: utf-8 -*-
"""実験160 — uvlayout は 0〜1 の升をどれだけ埋めるか。Padding・Rotation Step・Search Resolution で変わるか。

大きさの違う長方形 12 枚（辺 0.4〜2.0）に、形そのままの UV（uv = P.xz）を付けて uvlayout にかける。
並べたあとの UV の面積の合計（= 0〜1 の升のうち埋まった割合）と、島どうしの大きさの比が保たれているか、
時間を測る。長方形なので、Rotation Step で 90° 回せるようにすると詰まりが良くなるかも見る。

    hython examples/160_uvlayout_fill.py
"""
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def uv_area(prim):
    uvs = [v.attribValue("uv") for v in prim.vertices()]
    s = 0.0
    for i in range(len(uvs)):
        a, b = uvs[i], uvs[(i + 1) % len(uvs)]
        s += a[0] * b[1] - b[0] * a[1]
    return abs(s) / 2


def main():
    geo = sop_bench.fresh()
    rnd = random.Random(7)
    merge = geo.createNode("merge", "all")
    sizes = []
    for i in range(12):
        w, h = rnd.uniform(0.4, 2.0), rnd.uniform(0.4, 2.0)
        sizes.append((round(w, 4), round(h, 4)))
        g = geo.createNode("grid", f"r{i}")
        g.parmTuple("size").set((w, h))
        g.parm("rows").set(2)
        g.parm("cols").set(2)
        g.parmTuple("t").set((i * 3.0, 0, 0))
        merge.setInput(i, g)
    uv = geo.createNode("attribwrangle", "uv")
    uv.setInput(0, merge)
    uv.parm("class").set("vertex")
    uv.parm("snippet").set("v@uv = set(@P.x, @P.z, 0);")
    src = [p.intrinsicValue("measuredarea") for p in uv.geometry().prims()]
    rows = []
    for rot in ("none", "PI2"):
        for pad in (0, 1, 4, 16):
            for res in ("res1", "res2", "res3"):
                lay = geo.createNode("uvlayout::3.0", f"l_{rot}_{pad}_{res}")
                lay.setInput(0, uv)
                lay.parm("rotstep").set(rot)
                lay.parm("padding").set(pad)
                lay.parm("resolution").set(res)
                t0 = time.perf_counter()
                g = lay.geometry()
                sec = time.perf_counter() - t0
                areas = [uv_area(p) for p in g.prims()]
                ratios = [a / s for a, s in zip(areas, src)]
                us = [v.attribValue("uv") for p in g.prims() for v in p.vertices()]
                rows.append({"rotstep": rot, "padding": pad, "resolution": res, "fill": round(sum(areas), 4),
                             "scale_spread": round(max(ratios) / min(ratios), 6),
                             "u_range": [round(min(u[0] for u in us), 4), round(max(u[0] for u in us), 4)],
                             "v_range": [round(min(u[1] for u in us), 4), round(max(u[1] for u in us), 4)],
                             "sec": round(sec, 3)})
                print(rows[-1])
    sop_bench.save(160, rows, {"sizes": sizes, "total_area": round(sum(src), 4)})


if __name__ == "__main__":
    main()
