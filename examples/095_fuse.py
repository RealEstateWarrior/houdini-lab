# -*- coding: utf-8 -*-
"""実験095 — どこまで近ければ「同じ点」になるのか。

fuse は Snap Distance より近い点をひとつにまとめる。
では、その距離を変えると点はどう減るのか。狙った継ぎ目だけが閉じるのか、
それとも細かい所まで潰れてしまうのか。

場面を2つ作る。
  gap  … 板を2枚、隙間 d だけ離して並べる。d を固定し、Snap Distance を振る
         → 継ぎ目が閉じる境目はどこか
  mesh … 球を細かく割った形に、そのまま fuse をかける
         → 距離を上げると、どこから形そのものが潰れ始めるか

    hython examples/095_fuse.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

GAP = 0.01          # 板2枚のあいだの隙間
DISTS = [0.0, 0.001, 0.005, 0.009, 0.0095, 0.01, 0.011, 0.02, 0.05]
MESH_DISTS = [0.0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.16]


def two_plates(geo):
    """板を2枚、x 方向に GAP だけ離して並べる。継ぎ目の点は 2×11 個。"""
    left = geo.createNode("grid", "plate_left")
    left.parm("orient").set(0)                 # 0 = XY 平面
    left.parmTuple("size").set((1.0, 1.0))
    left.parm("rows").set(11)
    left.parm("cols").set(11)
    left.parmTuple("t").set((-0.5 - GAP / 2, 0.0, 0.0))

    right = geo.createNode("grid", "plate_right")
    right.parm("orient").set(0)
    right.parmTuple("size").set((1.0, 1.0))
    right.parm("rows").set(11)
    right.parm("cols").set(11)
    right.parmTuple("t").set((0.5 + GAP / 2, 0.0, 0.0))

    merge = geo.createNode("merge", "plates")
    merge.setInput(0, left)
    merge.setInput(1, right)
    return merge


def main():
    geo = sop_bench.fresh()

    plates = two_plates(geo)
    base = plates.geometry()
    base_points = base.intrinsicValue("pointcount")
    print(f"板2枚: {base_points} 点（隙間 {GAP}）")

    gap_rows = []
    for dist in DISTS:
        node = geo.createNode("fuse", f"gap_{dist}")
        node.setInput(0, plates)
        node.parm("usetol3d").set(True)
        node.parm("tol3d").set(dist)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        points = out.intrinsicValue("pointcount")
        row = {"dist": dist, "points": points,
               "merged": base_points - points,
               "seconds": round(elapsed, 4)}
        gap_rows.append(row)
        print(f"  距離 {dist:<7} -> {points:>4} 点（{row['merged']:>3} 個が合わさった）"
              f" {elapsed:.3f}秒")

    sphere = geo.createNode("sphere", "mesh_sphere")
    sphere.parm("type").set("polymesh")
    sphere.parm("rows").set(50)
    sphere.parm("cols").set(50)
    mesh_base = sphere.geometry()
    mesh_points = mesh_base.intrinsicValue("pointcount")
    print(f"球: {mesh_points} 点")

    mesh_rows = []
    for dist in MESH_DISTS:
        node = geo.createNode("fuse", f"mesh_{dist}")
        node.setInput(0, sphere)
        node.parm("usetol3d").set(True)
        node.parm("tol3d").set(dist)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        points = out.intrinsicValue("pointcount")
        gap = sop_bench.spread(out, mesh_base)
        row = {"dist": dist, "points": points,
               "kept_pct": round(points / mesh_points * 100, 3),
               "prims": out.intrinsicValue("primitivecount"),
               "seconds": round(elapsed, 4),
               "gap_mean": round(gap["mean"], 6) if gap["mean"] is not None else None}
        mesh_rows.append(row)
        print(f"  距離 {dist:<6} -> {points:>5} 点（元の {row['kept_pct']:.1f}%）"
              f" {row['prims']:>5} 面 {elapsed:.3f}秒 ずれ {row['gap_mean']}")

    sop_bench.save("095", gap_rows,
                   {"gap": GAP, "base_points": base_points,
                    "mesh_base_points": mesh_points, "mesh_rows": mesh_rows})


if __name__ == "__main__":
    main()
