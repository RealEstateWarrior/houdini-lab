# -*- coding: utf-8 -*-
"""実験158 — 種の点を relax すると、voronoifracture のかけらの大きさはそろうか。

実験157 と同じ 1×1×1 の箱に、scatter で 50 個の種を撒く。Relax Iterations を 0〜100 と変え、
かけらの体積のばらつき（標準偏差 ÷ 平均 = 変動係数）と、最大 ÷ 最小を測る。
種の点どうしの最短距離と、壁（箱の面）までの距離も測る（relax は点を離す処理なので、最短距離が伸びるはず）。

    hython examples/158_voronoi_relax.py
"""
import collections
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
    box = geo.createNode("box", "box")
    fill = geo.createNode("isooffset", "fog")
    fill.setInput(0, box)
    rows = []
    N = 50
    for it in (0, 5, 20, 50, 100):
        for seed in (3, 7, 11):
            sc = geo.createNode("scatter::2.0", f"pts{it}_{seed}")
            sc.setInput(0, fill)
            sc.parm("forcetotal").set(1)
            sc.parm("npts").set(N)
            sc.parm("seed").set(seed)
            sc.parm("relaxpoints").set(1 if it else 0)
            sc.parm("relaxiterations").set(max(it, 1))
            pts = [p.position() for p in sc.geometry().points()]
            dmin = min((pts[i] - pts[j]).length() for i in range(N) for j in range(i + 1, N))
            wall = [0.5 - max(abs(c) for c in p) for p in pts]      # いちばん近い壁までの距離
            near = sum(1 for w in wall if w < 0.02) / N
            vf = geo.createNode("voronoifracture::2.0", f"vf{it}_{seed}")
            vf.setInput(0, box)
            vf.setInput(1, sc)
            meas = geo.createNode("measure", f"m{it}_{seed}")
            meas.setInput(0, vf)
            meas.parm("measure").set("volume")
            meas.parm("attribname").set("vol")
            t0 = time.perf_counter()
            mg = meas.geometry()
            sec = time.perf_counter() - t0
            per = collections.defaultdict(float)
            for pr, nm in zip(mg.prims(), mg.primStringAttribValues("name")):
                per[nm] += pr.attribValue("vol")
            v = list(per.values())
            rows.append({"iterations": it, "seed": seed, "pieces": len(v), "total": round(sum(v), 6),
                         "cv": round(statistics.pstdev(v) / statistics.mean(v), 4),
                         "max_over_min": round(max(v) / min(v), 2), "seed_dmin": round(dmin, 4), "near_wall": round(near, 3),
                         "wall_mean": round(statistics.mean(wall), 4), "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(158, rows)


if __name__ == "__main__":
    main()
