# -*- coding: utf-8 -*-
"""実験155 — scatter の密度の属性は、点の割合をそのとおりに分けるか。ばらつきは二項分布の幅か。

2×1 の板（grid 2×1、左右に分かれた2枚の面）を用意し、右の面の density を k、左を 1 にする。
Force Total Count = N で撒くと、右に落ちる点の割合は k/(1+k) のはず。
Global Seed を 20 通り変えて、割合の平均と、ばらつき（標準偏差）を
二項分布の √(N·p·(1−p)) と比べる。Force Total Count を切ったとき（Density Scale だけ）の数も測る。

    hython examples/155_scatter_density.py
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
    grid = geo.createNode("grid", "grid")
    grid.parmTuple("size").set((2.0, 1.0))
    grid.parm("rows").set(2)
    grid.parm("cols").set(3)            # 面が2枚（左 x<0・右 x>0）
    rows = []
    for k in (1.0, 3.0, 9.0):
        w = geo.createNode("attribwrangle", f"dens{int(k)}")
        w.setInput(0, grid)
        w.parm("class").set("primitive")
        w.parm("snippet").set(f"f@density = @P.x > 0 ? {k} : 1.0;")
        for N in (1000, 10000):
            fr, secs = [], []
            for seed in range(20):
                sc = geo.createNode("scatter::2.0", f"s{int(k)}_{N}_{seed}")
                sc.setInput(0, w)
                sc.parm("usedensityattrib").set(1)
                sc.parm("densityattrib").set("density")
                sc.parm("forcetotal").set(1)
                sc.parm("npts").set(N)
                sc.parm("seed").set(seed)
                sc.parm("relaxpoints").set(0)
                t0 = time.perf_counter()
                g = sc.geometry()
                secs.append(time.perf_counter() - t0)
                xs = [p.position()[0] for p in g.points()]
                fr.append(sum(1 for x in xs if x > 0) / len(xs))
                sc.destroy()
            p = k / (1 + k)
            rows.append({"k": k, "N": N, "want": round(p, 6), "mean": round(statistics.mean(fr), 6),
                         "sd_count": round(statistics.pstdev(fr) * N, 3),
                         "binom_sd": round(math.sqrt(N * p * (1 - p)), 3),
                         "min": round(min(fr), 6), "max": round(max(fr), 6), "sec": round(statistics.mean(secs), 4)})
            print(rows[-1])
    # Force Total Count を切る: Density Scale と面積から数が決まるか
    free = []
    for scale in (10.0, 100.0, 1000.0):
        sc = geo.createNode("scatter::2.0", f"free{int(scale)}")
        sc.setInput(0, grid)
        sc.parm("forcetotal").set(0)
        sc.parm("densityscale").set(scale)
        sc.parm("relaxpoints").set(0)
        n = len(sc.geometry().points())
        free.append({"densityscale": scale, "area": 2.0, "points": n, "want": scale * 2.0})
        print(free[-1])
    sop_bench.save(155, rows, {"free": free})


if __name__ == "__main__":
    main()
