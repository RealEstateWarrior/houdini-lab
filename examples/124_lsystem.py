# -*- coding: utf-8 -*-
"""実験124 — L-System でコッホ曲線を描くと、長さと幅は式どおりに育つか。

規則: 始まり F、F → F+F--F+F、角度 60°、1歩の長さ 1。
n 世代で、線分は 4^n 本、全長は 4^n、端から端までの距離は 3^n になるはず
（1本が、長さ1の4本に置き換わり、端の間隔は3倍になる）。
Generations に小数（2.5 など）を入れたときの振る舞いも見る。

    hython examples/124_lsystem.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def length_of(parent, node):
    meas = parent.createNode("measure", "len")
    meas.setInput(0, node)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    total = sum(p.attribValue("len") for p in meas.geometry().prims())
    meas.destroy()
    return total


def main():
    geo = sop_bench.fresh()
    rows = []
    for gen in (0, 1, 2, 3, 4, 5, 6, 2.5):
        ls = geo.createNode("lsystem", "koch_" + str(gen).replace(".", "_"))
        ls.parm("premise").set("F")
        ls.parm("rule1").set("F=F+F--F+F")
        ls.parm("rule2").set("")
        ls.parm("angleinit").set(60)
        ls.parm("stepinit").set(1.0)
        ls.parm("generations").set(gen)
        t0 = time.perf_counter()
        out = ls.geometry()
        sec = time.perf_counter() - t0
        pts = out.points()
        first, last = pts[0].position(), pts[-1].position()
        size = out.boundingBox().sizevec()
        rows.append({"gen": gen, "points": len(pts), "prims": out.intrinsicValue("primitivecount"),
                     "length": round(length_of(geo, ls), 6),
                     "end_to_end": round((last - first).length(), 6),
                     "size": [round(v, 6) for v in size],
                     "want_segments": 4 ** gen if gen == int(gen) else None,
                     "want_length": round(4 ** gen, 6), "want_span": round(3 ** gen, 6),
                     "sec": round(sec, 4)})
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "124_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
