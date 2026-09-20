# -*- coding: utf-8 -*-
"""実験101 — measure の面積は、どれだけ正しいか。

面積は「測るための道具」としてよく使う。散らす濃さを決めたり、
重さを面積から出したり。その道具そのものの精度を確かめておく。

答えが分かっている形で突き合わせる。
  平らな板 … 1辺 L の正方形なら L²。分割の数に関係なく、ぴったり出るはず
  球      … 半径 r なら 4πr²。多角形なので必ず小さく出る。粗さとの関係を見る

多角形の球の表面積は、真の球より小さくなる。どれだけ足りないかが、
分割の数を増やすとどう減るのかを測る。

    hython examples/101_area.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

SIDE = 2.0
RADIUS = 1.0
GRID_DIVS = [2, 5, 11, 51, 201]
SPHERE_DIVS = [8, 16, 30, 60, 120, 240]


def area_of(parent, node, tag):
    meas = parent.createNode("measure", f"area_{tag}")
    meas.setInput(0, node)
    meas.parm("measure").set("area")
    meas.parm("attribname").set("ar")
    start = time.perf_counter()
    out = meas.geometry()
    total = sum(prim.attribValue("ar") for prim in out.prims())
    elapsed = time.perf_counter() - start
    meas.destroy()
    return total, elapsed


def main():
    geo = sop_bench.fresh()

    exact_grid = SIDE * SIDE
    print(f"板の答え: {exact_grid:.6f}")
    grid_rows = []
    for divs in GRID_DIVS:
        grid = geo.createNode("grid", f"grid_{divs}")
        grid.parmTuple("size").set((SIDE, SIDE))
        grid.parm("rows").set(divs)
        grid.parm("cols").set(divs)
        area, elapsed = area_of(geo, grid, f"g{divs}")
        grid_rows.append({
            "divs": divs,
            "prims": grid.geometry().intrinsicValue("primitivecount"),
            "area": round(area, 6),
            "diff": round(area - exact_grid, 9),
            "seconds": round(elapsed, 4),
        })
        print(f"  分割 {divs:>4} -> {grid_rows[-1]['prims']:>7,}面 "
              f"面積 {area:.6f}（差 {area - exact_grid:+.9f}）")

    exact_sphere = 4.0 * math.pi * RADIUS * RADIUS
    print(f"球の答え: {exact_sphere:.6f}")
    sphere_rows = []
    prev_short = None
    for divs in SPHERE_DIVS:
        sphere = geo.createNode("sphere", f"sph_{divs}")
        sphere.parm("type").set("polymesh")
        sphere.parm("rows").set(divs)
        sphere.parm("cols").set(divs)
        sphere.parmTuple("rad").set((RADIUS, RADIUS, RADIUS))
        area, elapsed = area_of(geo, sphere, f"s{divs}")
        short = exact_sphere - area
        sphere_rows.append({
            "divs": divs,
            "prims": sphere.geometry().intrinsicValue("primitivecount"),
            "area": round(area, 6),
            "short": round(short, 6),
            "short_pct": round(short / exact_sphere * 100, 5),
            "short_ratio": round(prev_short / short, 3) if prev_short else None,
            "seconds": round(elapsed, 4),
        })
        prev_short = short
        print(f"  分割 {divs:>4} -> {sphere_rows[-1]['prims']:>7,}面 "
              f"面積 {area:.6f}（足りない分 {short:.6f} = "
              f"{sphere_rows[-1]['short_pct']:.5f}%）"
              + (f" 前の段の {sphere_rows[-1]['short_ratio']}分の1"
                 if sphere_rows[-1]["short_ratio"] else ""))

    sop_bench.save("101", sphere_rows,
                   {"exact_sphere": round(exact_sphere, 6),
                    "exact_grid": round(exact_grid, 6),
                    "grid_rows": grid_rows})


if __name__ == "__main__":
    main()
