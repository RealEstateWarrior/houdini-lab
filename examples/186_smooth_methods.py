# -*- coding: utf-8 -*-
"""実験186 — smooth の Method（Uniform・Scale Dominant・Curvature Dominant）で、円の縮み方は変わるか。開いた線の端はどうなるか。

1. 半径 1 の 24 角形（Polygon）に、Method を変えて smooth（Strength 10・Filter Quality 1・2）をかけ、残った半径を読む。
   Uniform は実験185 の式 r = 1/(1 + S·L^q/C(2q,q)) に合う。ほかの2つがそれより縮むか縮まないかを見る。
2. 開いた線（x = 0〜1 を 41 点、y = 0.1·sin(4πx) の波）に smooth（Uniform・Strength 10）をかけ、
   Constrained Boundary を None・Unshared Edges（既定）で比べて、端の点が動くか、波の高さがどれだけ残るかを見る。

    hython examples/186_smooth_methods.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    c = geo.createNode("circle", "c24")
    c.parm("type").set("poly")
    c.parm("divs").set(24)
    circle = []
    for method in ("uniform", "scaledominant", "curvaturedominant"):
        for q in (1, 2):
            s = geo.createNode("smooth::2.0", f"s_{method}_{q}")
            s.setInput(0, c)
            s.parm("contrainedboundary").set("none")
            s.parm("method").set(method)
            s.parm("strength").set(10.0)
            s.parm("filterquality").set(q)
            rs = [p.position().length() for p in s.geometry().points()]
            circle.append({"method": method, "quality": q, "r": round(sum(rs) / len(rs), 7),
                           "spread": round(max(rs) - min(rs), 7)})
            print(circle[-1])
    wave = geo.createNode("attribwrangle", "wave")
    wave.parm("class").set("detail")
    wave.parm("snippet").set("int pts[]; for (int i = 0; i <= 40; i++) { float x = i / 40.0;"
                             " append(pts, addpoint(0, set(x, 0.1 * sin(4 * PI * x), 0))); } addprim(0, 'polyline', pts);")
    line = []
    for bnd in ("none", "unsharededges"):
        s = geo.createNode("smooth::2.0", f"w_{bnd}")
        s.setInput(0, wave)
        s.parm("contrainedboundary").set(bnd)
        s.parm("method").set("uniform")
        s.parm("strength").set(10.0)
        s.parm("filterquality").set(1)
        pts = [p.position() for p in s.geometry().points()]
        amp = max(abs(p[1]) for p in pts)
        line.append({"boundary": bnd, "end0": [round(pts[0][0], 5), round(pts[0][1], 5)],
                     "end1": [round(pts[-1][0], 5), round(pts[-1][1], 5)], "amp": round(amp, 6),
                     "amp_ratio": round(amp / 0.1, 4), "x_span": round(pts[-1][0] - pts[0][0], 5)})
        print(line[-1])
    L = 2 * (1 - math.cos(2 * math.pi / 40 * 2))      # 波の周期は 20 点（1 周期 = 0.5）
    sop_bench.save(186, circle, {"line": line, "wave_L": L})


if __name__ == "__main__":
    main()
