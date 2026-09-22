# -*- coding: utf-8 -*-
"""実験144 — torus の面積 4π²Rr・体積 2π²Rr² に、Rows と Columns はどう効くか。

Radius = (1, 0.25) の torus（Polygon）で、Rows と Columns を別々に増やす。
どちらが大きな輪を、どちらが管の断面を刻むのかを点の位置から確かめ、
面積と体積の式からのずれが、それぞれの分割にどう依存するかを見る。

    hython examples/144_torus.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

R, r = 1.0, 0.25


def main():
    geo = sop_bench.fresh()
    rows = []
    cases = [(rw, 96) for rw in (6, 12, 24, 48, 96)] + [(96, cl) for cl in (6, 12, 24, 48)]
    for rw, cl in cases:
        t = geo.createNode("torus", f"t{rw}_{cl}")
        t.parm("type").set("poly")
        t.parmTuple("rad").set((R, r))
        t.parm("rows").set(rw)
        t.parm("cols").set(cl)
        t0 = time.perf_counter()
        g = t.geometry()
        sec = time.perf_counter() - t0
        area = sum(p.intrinsicValue("measuredarea") for p in g.prims())
        vol = sop_bench.volume(g)
        # 軸（y）からの距離と高さの種類の数: 断面の刻みの手がかり
        heights = sorted({round(p.position()[1], 5) for p in g.points()})
        rows.append({"rows": rw, "cols": cl, "points": len(g.points()), "prims": len(g.prims()),
                     "heights": len(heights), "area": round(area, 6), "volume": round(vol, 6),
                     "sec": round(sec, 4)})
        print(rows[-1])
    sop_bench.save(144, rows, {"R": R, "r": r, "want_area": 4 * math.pi ** 2 * R * r,
                               "want_volume": 2 * math.pi ** 2 * R * r * r})


if __name__ == "__main__":
    main()
