# -*- coding: utf-8 -*-
"""実験152 — polybevel で箱の辺を丸めると、体積は「角を丸めた箱」の式に近づくか。

1×1×1 の箱の全部の辺を polybevel（Offset = d）で面取りし、Fillet Shape を
Round にして Divisions を 1〜16 と増やす。Offset が丸みの半径 d そのものなら、
体積は (1−2d)³ + 6d(1−2d)² + 3πd²(1−2d) + (4/3)πd³
（芯の箱 + 面の板6枚 + 1/4 円柱12本 + 1/8 球8個）に近づくはず。
Solid（平らな面取り）の体積と、点の数・時間も残す。

    hython examples/152_bevel_volume.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def rounded(d):
    return (1 - 2 * d) ** 3 + 6 * d * (1 - 2 * d) ** 2 + 3 * math.pi * d * d * (1 - 2 * d) + 4 / 3 * math.pi * d ** 3


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    rows = []
    for d in (0.05, 0.1, 0.2):
        for shape, divs in (("solid", 1), ("round", 1), ("round", 2), ("round", 4), ("round", 8), ("round", 16)):
            b = geo.createNode("polybevel::3.0", f"b_{int(d * 100)}_{shape}_{divs}")
            b.setInput(0, box)
            b.parm("grouptype").set("edges")
            b.parm("offset").set(d)
            b.parm("filletshape").set(shape)
            b.parm("divisions").set(divs)
            t0 = time.perf_counter()
            g = b.geometry()
            sec = time.perf_counter() - t0
            bb = g.boundingBox()
            rows.append({"offset": d, "shape": shape, "divisions": divs, "points": len(g.points()),
                         "prims": len(g.prims()), "size": [round(x, 6) for x in bb.sizevec()],
                         "volume": round(sop_bench.volume(g), 6), "want_round": round(rounded(d), 6),
                         "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(152, rows)


if __name__ == "__main__":
    main()
