# -*- coding: utf-8 -*-
"""実験191 — 多角形の球は、本当の球からどれだけ内側にへこんでいるか。xyzdist で測ると式どおりか。

半径 1 の本当の球の上に一様に 2 万点を撒き（点の位置は計算で作る）、xyzdist で多角形の球（Polygon Mesh・Rows × Columns）までの距離を測る。
多角形は内側に入るので、いちばん大きい距離は「面の真ん中が球面からへこむ量」。
細い帯の四角形なら、へこみは大ざっぱに 1 − cos(Δ/2)（Δ は隣の点どうしの角度）に比例して小さくなるはず。
Columns = 2 × (Rows − 1) の球で、Rows を 7〜97 と変える。

    hython examples/191_sphere_gap.py
"""
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    pts = geo.createNode("attribwrangle", "pts")
    pts.parm("class").set("detail")
    pts.parm("snippet").set("for (int i = 0; i < 20000; i++) { float u = rand(i * 1.37 + 0.1) * 2 - 1; float t = rand(i * 2.71 + 0.3) * 2 * PI;"
                            " float s = sqrt(1 - u * u); addpoint(0, set(s * cos(t), u, s * sin(t))); }")
    rows = []
    for R in (7, 13, 25, 49, 97):
        sp = geo.createNode("sphere", f"sp{R}")
        sp.parm("type").set("polymesh")
        sp.parm("rows").set(R)
        sp.parm("cols").set(2 * (R - 1))
        w = geo.createNode("attribwrangle", f"d{R}")
        w.setInput(0, pts)
        w.setInput(1, sp)
        w.parm("snippet").set("f@d = xyzdist(1, @P);")
        t0 = time.perf_counter()
        d = w.geometry().pointFloatAttribValues("d")
        sec = time.perf_counter() - t0
        delta = math.pi / (R - 1)                        # 縦の隣どうしの角度（横も 2π / (2(R−1)) で同じ）
        chord = 1 - math.cos(delta / 2)                  # 辺の真ん中のへこみ
        corner = 1 - math.cos(delta / 2) ** 2            # 四角形の真ん中（2 方向ぶん）の目安
        rows.append({"rows": R, "cols": 2 * (R - 1), "max_gap": round(max(d), 7), "mean_gap": round(statistics.fmean(d), 7),
                     "edge_formula": round(chord, 7), "face_formula": round(corner, 7), "sec": round(sec, 4)})
        print(rows[-1])
    sop_bench.save(191, rows)


if __name__ == "__main__":
    main()
