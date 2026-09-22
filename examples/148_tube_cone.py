# -*- coding: utf-8 -*-
"""実験148 — tube で円錐台を作ると、体積と側面の面積は式どおりか。Radius の2つはどちらが上か。

tube（Polygon、End Caps 入り）で Radius = (r1, r2)、Height = 1 にする。
円錐台の体積 πh(r1² + r1r2 + r2²)/3、側面 π(r1 + r2)·√((r1 − r2)² + h²)。
Columns（周の分割）を 12〜384 と増やし、内接多角形の分だけ小さく出るかを見る。

    hython examples/148_tube_cone.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    rows = []
    for r1, r2 in ((1.0, 0.0), (1.0, 0.5), (0.5, 1.0)):
        for cols in (12, 48, 384):
            t = geo.createNode("tube", f"t{int(r1 * 10)}_{int(r2 * 10)}_{cols}")
            t.parm("type").set("poly")
            t.parm("cap").set(1)
            t.parmTuple("rad").set((r1, r2))
            t.parm("height").set(1.0)
            t.parm("cols").set(cols)
            t0 = time.perf_counter()
            g = t.geometry()
            sec = time.perf_counter() - t0
            pts = [p.position() for p in g.points()]
            top = max(p[1] for p in pts)
            r_top = max(math.hypot(p[0], p[2]) for p in pts if abs(p[1] - top) < 1e-6)
            prims = g.prims()
            area = sum(p.intrinsicValue("measuredarea") for p in prims)
            rows.append({"r1": r1, "r2": r2, "cols": cols, "points": len(pts), "prims": len(prims),
                         "top_y": round(top, 6), "r_top": round(r_top, 6),
                         "area": round(area, 6), "volume": round(sop_bench.volume(g), 6),
                         "want_volume": round(math.pi * (r1 * r1 + r1 * r2 + r2 * r2) / 3, 6),
                         "want_side": round(math.pi * (r1 + r2) * math.hypot(r1 - r2, 1.0), 6),
                         "want_caps": round(math.pi * (r1 * r1 + r2 * r2), 6), "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(148, rows)


if __name__ == "__main__":
    main()
