# -*- coding: utf-8 -*-
"""実験187 — 点の間隔がそろっていない円では、smooth の3つの Method に違いが出るか。どれが丸さを保つか。

半径 1 の円の上に 48 点を、角度が等間隔でないように置く（半分は細かく、半分は粗く: 左半分に 36 点、右半分に 12 点）。
閉じた多角形にして、Method を Uniform・Scale Dominant・Curvature Dominant、Strength を 1・10、Filter Quality 1 で smooth をかけ、
半径の平均・ばらつき（最大 − 最小）・点の角度の動き（左右の点の偏りが直るか）を測る。

    hython examples/187_smooth_uneven.py
"""
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    angs = [math.pi / 2 + math.pi * i / 36 for i in range(36)] + [3 * math.pi / 2 + math.pi * i / 12 for i in range(12)]
    code = "int pts[]; " + " ".join(f"append(pts, addpoint(0, set({math.cos(a):.9f}, {math.sin(a):.9f}, 0)));" for a in angs) + " addprim(0, 'poly', pts);"
    src = geo.createNode("attribwrangle", "uneven")
    src.parm("class").set("detail")
    src.parm("snippet").set(code)
    base = [p.position() for p in src.geometry().points()]
    rows = []
    for method in ("uniform", "scaledominant", "curvaturedominant"):
        for strength in (1.0, 10.0):
            s = geo.createNode("smooth::2.0", f"s_{method}_{int(strength)}")
            s.setInput(0, src)
            s.parm("contrainedboundary").set("none")
            s.parm("method").set(method)
            s.parm("strength").set(strength)
            s.parm("filterquality").set(1)
            pts = [p.position() for p in s.geometry().points()]
            rs = [math.hypot(p[0], p[1]) for p in pts]
            left = [r for r, p in zip(rs, base) if p[0] < -1e-6]
            right = [r for r, p in zip(rs, base) if p[0] > 1e-6]
            cx = statistics.fmean(p[0] for p in pts)
            moved = statistics.fmean(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(pts, base))
            rows.append({"method": method, "strength": strength, "r_mean": round(statistics.fmean(rs), 6),
                         "r_spread": round(max(rs) - min(rs), 6), "r_left": round(statistics.fmean(left), 6),
                         "r_right": round(statistics.fmean(right), 6), "center_x": round(cx, 6), "moved": round(moved, 6)})
            print(rows[-1])
    sop_bench.save(187, rows)


if __name__ == "__main__":
    main()
