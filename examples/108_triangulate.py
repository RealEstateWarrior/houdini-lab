# -*- coding: utf-8 -*-
"""実験108 — triangulate2d の三角形の数は、式で先に分かるか。

平面の点 n 個を三角形で埋めると、外周（凸包）に乗る点が h 個なら
三角形は 2n − 2 − h 枚になる（オイラーの多面体定理から出る）。
面積の合計は凸包の面積に一致するはず。

ばらまいた点（scatter）と、きっちり並んだ点（格子。4点が同じ円に乗る
ので、どちらの対角線で割っても「正しい」分け方になる）の両方で確かめる。
凸包と面積は Python 側で計算する。

    hython examples/108_triangulate.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def hull(points):
    """凸包（Andrew の方法）。一直線上の点は外周に数える。"""
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) < -1e-12:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) < -1e-12:
            upper.pop()
        upper.append(p)
    ring = lower[:-1] + upper[:-1]
    area = 0.0
    corners = [p for i, p in enumerate(ring)
               if abs(cross(ring[i - 1], p, ring[(i + 1) % len(ring)])) > 1e-12]
    for i, p in enumerate(corners):
        q = corners[(i + 1) % len(corners)]
        area += p[0] * q[1] - q[0] * p[1]
    return len(ring), abs(area) / 2


def area_of(parent, node):
    meas = parent.createNode("measure", "area")
    meas.setInput(0, node)
    meas.parm("measure").set("area")
    meas.parm("attribname").set("a")
    total = sum(prim.attribValue("a") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def run(geo, source, label):
    node = geo.createNode("triangulate2d::3.0", "tri_" + label)
    node.setInput(0, source)
    t0 = time.perf_counter()
    out = node.geometry()
    sec = time.perf_counter() - t0
    src = source.geometry()
    xy = [(round(p[0], 9), round(p[2], 9)) for p in
          (pt.position() for pt in src.points())]
    n = len(set(xy))
    h, hull_area = hull(xy)
    tris = out.intrinsicValue("primitivecount")
    not_tri = sum(1 for prim in out.prims() if len(prim.vertices()) != 3)
    return {"case": label, "n": n, "h": h, "tris": tris, "want": 2 * n - 2 - h,
            "not_tri": not_tri, "area": round(area_of(geo, node), 6),
            "hull_area": round(hull_area, 6), "sec": round(sec, 4)}


def main():
    rows = []
    geo = sop_bench.fresh()
    plane = geo.createNode("grid", "plane")
    plane.parmTuple("size").set((4, 3))
    plane.parm("rows").set(2)
    plane.parm("cols").set(2)
    for count, seed in ((10, 1), (100, 2), (1000, 3), (10000, 4), (100000, 5)):
        sc = geo.createNode("scatter::2.0", f"sc{count}")
        sc.setInput(0, plane)
        sc.parm("npts").set(count)
        sc.parm("seed").set(seed)
        rows.append(run(geo, sc, f"scatter_{count}"))
        print(rows[-1])
    for k in (3, 5, 11, 51):
        grid = geo.createNode("grid", f"g{k}")
        grid.parm("rows").set(k)
        grid.parm("cols").set(k)
        only_pts = geo.createNode("add", f"pts{k}")
        only_pts.setInput(0, grid)
        only_pts.parm("remove").set(True)       # 面を消して点だけにする
        row = run(geo, only_pts, f"grid_{k}x{k}")
        row["grid_want"] = 2 * (k - 1) ** 2
        rows.append(row)
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "108_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
