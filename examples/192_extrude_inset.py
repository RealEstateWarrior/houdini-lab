# -*- coding: utf-8 -*-
"""実験192 — polyextrude の Inset は、上の面を内側へ i だけ寄せるか。押し出した形は角錐台の体積になるか。

1 × 1 の正方形1枚（grid 2 × 2 点）を polyextrude（Distance d・Inset i・Output Back 入）で押し出す。
上の面が (1 − 2i)² の正方形になり、体積が角錐台の式 d/3 · (A₁ + A₂ + √(A₁A₂))（A₁ = 1、A₂ = (1 − 2i)²）になるかを見る。
Inset を大きくして上の面が消える（i = 0.5）と、四角錐（体積 d/3）になるはず。i > 0.5 ではどうなるかも見る。

    hython examples/192_extrude_inset.py
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
    sq = geo.createNode("grid", "sq")
    sq.parmTuple("size").set((1.0, 1.0))
    sq.parm("rows").set(2)
    sq.parm("cols").set(2)
    rows = []
    for d in (0.5, 1.0):
        for i in (0.0, 0.1, 0.25, 0.4, 0.5, 0.6):
            ex = geo.createNode("polyextrude::2.0", f"e{int(d * 10)}_{int(i * 100)}")
            ex.setInput(0, sq)
            ex.parm("dist").set(d)
            ex.parm("inset").set(i)
            ex.parm("outputback").set(1)
            t0 = time.perf_counter()
            g = ex.geometry()
            sec = time.perf_counter() - t0
            top_y = max(p.position()[1] for p in g.points())
            top = [p.position() for p in g.points() if abs(p.position()[1] - top_y) < 1e-6]
            side = max(abs(p[0]) for p in top) * 2 if top else 0.0
            A1, A2 = 1.0, max(0.0, 1 - 2 * i) ** 2
            rows.append({"dist": d, "inset": i, "points": len(g.points()), "prims": len(g.prims()), "top_y": round(top_y, 6),
                         "top_side": round(side, 6), "want_side": round(max(0.0, 1 - 2 * i), 6),
                         "volume": round(sop_bench.volume(g), 6),
                         "want_volume": round(d / 3 * (A1 + A2 + math.sqrt(A1 * A2)), 6), "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(192, rows)


if __name__ == "__main__":
    main()
