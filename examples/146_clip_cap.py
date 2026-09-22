# -*- coding: utf-8 -*-
"""実験146 — clip で切った球の面積は、アルキメデスの 2πRh になるか。

半径 1 の球を y = c の面で切り、上側（above か below か、どちらが残るかも確かめる）の面積を測る。
球帯の面積は高さ h だけで決まる（2πRh）。分割 48×96 と 192×384 で比べ、
切り口の点がちょうど面の上に乗るか、Keep = Both で面が2つに分かれるかも見る。

    hython examples/146_clip_cap.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def area(g):
    return sum(p.intrinsicValue("measuredarea") for p in g.prims())


def main():
    geo = sop_bench.fresh()
    rows = []
    for res in (48, 192):
        sp = geo.createNode("sphere", f"sp{res}")
        sp.parm("type").set("polymesh")
        sp.parm("rows").set(res)
        sp.parm("cols").set(res * 2)
        full = area(sp.geometry())
        for c in (-0.5, 0.0, 0.3, 0.7):
            for op in ("above", "below", "both"):
                cl = geo.createNode("clip", f"c{res}_{int(c * 10)}_{op}")
                cl.setInput(0, sp)
                cl.parm("clipop").set(op)
                cl.parmTuple("dir").set((0.0, 1.0, 0.0))
                cl.parm("dist").set(c)
                t0 = time.perf_counter()
                g = cl.geometry()
                sec = time.perf_counter() - t0
                ys = [p.position()[1] for p in g.points()]
                on_plane = sum(1 for y in ys if abs(y - c) < 1e-6)
                a = area(g)
                rows.append({"res": res, "c": c, "op": op, "points": len(ys), "prims": len(g.prims()),
                             "ymin": round(min(ys), 6), "ymax": round(max(ys), 6), "on_plane": on_plane,
                             "area": round(a, 6), "full": round(full, 6),
                             "want_above": round(2 * math.pi * (1 - c), 6),
                             "want_below": round(2 * math.pi * (1 + c), 6), "sec": round(sec, 4)})
                print(rows[-1])
    sop_bench.save(146, rows)


if __name__ == "__main__":
    main()
