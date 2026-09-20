# -*- coding: utf-8 -*-
"""実験096 — ばらまく数を指定すると、本当にその数になるのか。

scatter には「Force Total Count」がある。指定した数をそのまま出すという意味だが、
面の形や密度のかかり方で、ぴったりにならないことがあるのではないか。

測るもの
  1. 指定した数と、実際に出た点の数。ぴったり合うか
  2. 点の数と、かかる時間。まっすぐ伸びるか（点の数に比例するか）
  3. 面の大きさが場所によって違う形（球に mountain）でも数は合うか

    hython examples/096_scatter.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

COUNTS = [100, 1000, 10000, 100000, 1000000]


def run(geo, source, count, seed):
    node = geo.createNode("scatter::2.0", f"sc_{count}_{seed}")
    node.setInput(0, source)
    node.parm("forcetotal").set(True)
    node.parm("npts").set(count)
    node.parm("seed").set(seed)
    start = time.perf_counter()
    out = node.geometry()
    elapsed = time.perf_counter() - start
    return out.intrinsicValue("pointcount"), elapsed


def main():
    geo = sop_bench.fresh()

    grid = geo.createNode("grid", "flat")
    grid.parmTuple("size").set((10.0, 10.0))
    grid.parm("rows").set(2)
    grid.parm("cols").set(2)

    sphere = geo.createNode("sphere", "bumpy_sphere")
    sphere.parm("type").set("polymesh")
    sphere.parm("rows").set(60)
    sphere.parm("cols").set(60)
    bumpy = geo.createNode("mountain", "bumpy")
    bumpy.setInput(0, sphere)
    bumpy.parm("height").set(0.4)
    bumpy.parm("elementsize").set(0.5)
    bumpy.parmTuple("offset").set((21.0, 0.0, 0.0))

    rows = []
    for name, source in (("平らな板（1面）", grid), ("凹凸のある球（3,540面）", bumpy)):
        for count in COUNTS:
            got, elapsed = run(geo, source, count, 1)
            per = elapsed / got * 1e6 if got else None
            row = {"shape": name, "asked": count, "got": got,
                   "diff": got - count,
                   "seconds": round(elapsed, 4),
                   "us_per_point": round(per, 3) if per else None}
            rows.append(row)
            print(f"  {name} 指定 {count:>8} -> {got:>8} 点"
                  f"（差 {row['diff']:+d}） {elapsed:.3f}秒"
                  f" 1点あたり {row['us_per_point']}マイクロ秒")

    # 種を変えても数が変わらないかを確かめる（1万点で3回）
    seeds = []
    for seed in (1, 2, 3):
        got, elapsed = run(geo, bumpy, 10000, seed)
        seeds.append({"seed": seed, "got": got, "seconds": round(elapsed, 4)})
        print(f"  種 {seed} -> {got} 点 {elapsed:.3f}秒")

    sop_bench.save("096", rows, {"seeds": seeds})


if __name__ == "__main__":
    main()
