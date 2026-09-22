# -*- coding: utf-8 -*-
"""実験147 — twist SOP の6つの Operation は、体積を保つか。Strength は何を表すか。

1×1×1 の箱（各辺 24 分割）を x 方向に1〜3の長さに伸ばし、Primary Axis = X で
Twist / Bend / Shear / Taper / Linear Taper / Squash をかける。
体積が変わらないはずのもの（ねじり・曲げ・せん断）と、変わるもの（細め・つぶし）を分け、
x の端での断面の大きさから、Strength の意味を読み取る。

    hython examples/147_twist_ops.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

OPS = ["twist", "bend", "shear", "taper", "ltaper", "squash"]


def section(g, x, tol=1e-4):
    ps = [p.position() for p in g.points()]
    xs = [p[0] for p in ps]
    target = min(xs) if x == "min" else max(xs)
    sl = [p for p in ps if abs(p[0] - target) < tol]
    ys = [p[1] for p in sl] or [0]
    zs = [p[2] for p in sl] or [0]
    return round(max(ys) - min(ys), 6), round(max(zs) - min(zs), 6), round(target, 6)


def main():
    geo = sop_bench.fresh()
    rows = []
    for length in (1.0, 2.0):
        box = geo.createNode("box", f"box{int(length)}")
        box.parm("type").set("polymesh")
        box.parmTuple("size").set((length, 1.0, 1.0))
        box.parmTuple("t").set((length / 2, 0.0, 0.0))  # x は 0〜length
        box.parm("dodivs").set(1)
        box.parmTuple("divs").set((24, 24, 24))
        v0 = sop_bench.volume(box.geometry())
        for op in OPS:
            for s in (0.5, 1.0):
                tw = geo.createNode("twist", f"tw_{op}_{s}_{int(length)}")
                tw.setInput(0, box)
                tw.parm("op").set(op)
                tw.parm("strength").set(s)
                t0 = time.perf_counter()
                g = tw.geometry()
                sec = time.perf_counter() - t0
                bb = g.boundingBox()
                v = sop_bench.volume(g)
                rows.append({"length": length, "op": op, "strength": s, "v0": round(v0, 6), "volume": round(v, 6),
                             "ratio": round(v / v0, 6), "end0": section(g, "min"), "end1": section(g, "max"),
                             "bbox": [round(x, 4) for x in bb.sizevec()], "sec": round(sec, 4)})
                print(rows[-1])
    # x = 1 の端、z = 0.5 の辺で、y ごとにどこへ動いたか（Strength の意味を読む）
    box = geo.node("box1")
    prof = []
    for op in OPS:
        for s in (0.5, 2.0):
            tw = geo.createNode("twist", f"pf_{op}_{s}")
            tw.setInput(0, box)
            tw.parm("op").set(op)
            tw.parm("strength").set(s)
            for a, c in zip(box.geometry().points(), tw.geometry().points()):
                pa, pc = a.position(), c.position()
                if abs(pa[0] - 1) < 1e-6 and abs(pa[2] - 0.5) < 1e-6 and round(pa[1] * 24) % 6 == 0:
                    prof.append({"op": op, "strength": s, "y": round(pa[1], 4),
                                 "to": [round(v, 4) for v in pc]})
    sop_bench.save(147, rows, {"profile": prof})


if __name__ == "__main__":
    main()
