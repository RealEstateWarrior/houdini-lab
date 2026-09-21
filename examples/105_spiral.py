# -*- coding: utf-8 -*-
"""実験105 — らせんの長さは式どおりか。

spiral を多角形（Polygon）で出し、半径を一定（Start = End）にする。
1巻きを N 分割した折れ線の長さは、1区間の弦
    c = sqrt((2 r sin(pi/N))^2 + (p/N)^2)      p は1巻きで上がる高さ
を turns×N 本足したものになるはず。分割を細かくすると、なめらかならせんの長さ
    turns × sqrt((2 pi r)^2 + p^2)
に近づく。この2つと突き合わせる。

長さは measure（Perimeter）を面ごとに足す。

    hython examples/105_spiral.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

# (半径, 巻き数, 高さ, 1巻きの分割数)
CASES = [
    (1.0, 3, 3.0, 4), (1.0, 3, 3.0, 8), (1.0, 3, 3.0, 16), (1.0, 3, 3.0, 50),
    (1.0, 3, 3.0, 200), (1.0, 3, 3.0, 1000),
    (0.5, 5, 1.0, 50), (2.0, 2, 8.0, 50), (1.0, 4, 0.0, 50), (0.25, 10, 5.0, 50),
]


def length_of(parent, node):
    meas = parent.createNode("measure", "len")
    meas.setInput(0, node)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    total = sum(prim.attribValue("len") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def main():
    rows = []
    for radius, turns, height, divs in CASES:
        geo = sop_bench.fresh()
        node = geo.createNode("spiral", "sp")
        node.parm("type").set("poly")
        node.parm("mode").set("turns")
        node.parm("turns").set(turns)
        node.parm("height").set(height)
        node.parm("radiusmode").set("endradius")
        node.parm("startradius").set(radius)
        node.parm("endradius").set(radius)
        node.parm("divsmode").set("divsperturn")
        node.parm("divsperturn").set(divs)
        t0 = time.perf_counter()
        out = node.geometry()
        points = out.intrinsicValue("pointcount")
        got = length_of(geo, node)
        sec = time.perf_counter() - t0
        size = out.boundingBox().sizevec()
        pitch = height / turns
        chord = math.sqrt((2 * radius * math.sin(math.pi / divs)) ** 2
                          + (pitch / divs) ** 2)
        want_poly = turns * divs * chord
        want_smooth = turns * math.sqrt((2 * math.pi * radius) ** 2 + pitch ** 2)
        rows.append({
            "radius": radius, "turns": turns, "height": height, "divs": divs,
            "points": points, "want_points": turns * divs + 1,
            "length": round(got, 6),
            "want_poly": round(want_poly, 6),
            "diff_poly": round(got - want_poly, 6),
            "want_smooth": round(want_smooth, 6),
            "ratio_smooth": round(got / want_smooth, 6),
            "size": [round(v, 6) for v in size],
            "sec": round(sec, 4),
        })
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "105_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
