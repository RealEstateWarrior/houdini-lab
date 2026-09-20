# -*- coding: utf-8 -*-
"""実験098 — 同じ穴を3つの道筋で開けて、答えと突き合わせる。

1辺 1.0 の箱に、半径 0.25 の円柱の穴を1本通す。答えは計算で出せる。

  円で考えた答え   1.0 - π × 0.25² × 1.0 = 0.803650…
  n角形で考えた答え 1.0 - ½ n × 0.25² × sin(2π/n) × 1.0

Houdini の円柱は多角形なので、正しく引けていれば「n角形で考えた答え」に合うはず。
円の答えとの差は、アルゴリズムのせいではなく多角形近似のせいだと分けられる。

道筋は3つ。
  boolean … boolean::2.0 の Subtract
  cookie  … 古いほうの cookie（A minus B）
  vdb     … 両方を VDB にして sdfdifference で引き、面に戻す

あわせて、円柱の辺の数を 12 / 40 / 80 / 200 と変えて、boolean の値が
n角形の答えを追うかどうかも見る。

つまずいた点: 箱と円柱の Primitive Type を poly 以外（mesh / polymesh）にすると、
boolean も cookie も黙って何もしない。エラーも警告も出ず、箱がそのまま出てくる。
最初これに気づかず、体積 1.000000 のまま「差 +24%」という表を作ってしまった。

    hython examples/098_hole.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

RADIUS = 0.25
HEIGHT = 1.0            # 箱の中を通る長さ
CIRCLE = 1.0 - math.pi * RADIUS * RADIUS * HEIGHT
VOXELS = [0.02, 0.01, 0.005]
COLS = [12, 40, 80, 200]
MAIN_COLS = 80


def ngon(n):
    """n角形で開けたときの、残る体積。"""
    area = 0.5 * n * RADIUS * RADIUS * math.sin(2.0 * math.pi / n)
    return 1.0 - area * HEIGHT


def volume_of(parent, node, tag):
    meas = parent.createNode("measure", f"vol_{tag}")
    meas.setInput(0, node)
    meas.parm("measure").set("volume")
    meas.parm("attribname").set("vol")
    total = sum(prim.attribValue("vol") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def make_box(geo):
    box = geo.createNode("box", "the_box")
    box.parm("type").set("poly")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    return box


def make_tube(geo, cols, tag):
    tube = geo.createNode("tube", f"the_tube_{tag}")
    tube.parm("type").set("poly")
    tube.parm("orient").set(2)              # 2 = z 軸方向
    tube.parmTuple("rad").set((RADIUS, RADIUS))
    tube.parm("height").set(2.0)            # 箱を突き抜ける長さ
    tube.parm("cols").set(cols)
    tube.parm("rows").set(2)
    tube.parm("cap").set(True)
    return tube


def row_for(way, detail, node, geo, tag, expect):
    start = time.perf_counter()
    out = node.geometry()
    elapsed = time.perf_counter() - start
    vol = volume_of(geo, node, tag)
    return {
        "way": way, "detail": detail,
        "points": out.intrinsicValue("pointcount"),
        "prims": out.intrinsicValue("primitivecount"),
        "seconds": round(elapsed, 4),
        "volume": round(vol, 6),
        "vs_ngon": round(vol - expect, 6),
        "vs_circle": round(vol - CIRCLE, 6),
        "vs_ngon_pct": round((vol - expect) / expect * 100, 4),
        "vs_circle_pct": round((vol - CIRCLE) / CIRCLE * 100, 4),
    }


def main():
    geo = sop_bench.fresh()
    expect = ngon(MAIN_COLS)
    print(f"円で考えた答え      {CIRCLE:.6f}")
    print(f"{MAIN_COLS}角形で考えた答え {expect:.6f}")

    box = make_box(geo)
    tube = make_tube(geo, MAIN_COLS, "main")
    print(f"箱 {box.geometry().intrinsicValue('primitivecount')}面 / "
          f"円柱 {tube.geometry().intrinsicValue('primitivecount')}面")

    rows = []

    node = geo.createNode("boolean::2.0", "by_boolean")
    node.setInput(0, box)
    node.setInput(1, tube)
    node.parm("booleanop").set("subtract")
    rows.append(row_for("boolean", "Subtract", node, geo, "bool", expect))

    node = geo.createNode("cookie", "by_cookie")
    node.setInput(0, box)
    node.setInput(1, tube)
    node.parm("boolop").set("AminusB")
    rows.append(row_for("cookie", "A minus B", node, geo, "cookie", expect))

    for voxel in VOXELS:
        a = geo.createNode("vdbfrompolygons", f"vdb_a_{voxel}")
        a.setInput(0, box)
        a.parm("voxelsize").set(voxel)
        b = geo.createNode("vdbfrompolygons", f"vdb_b_{voxel}")
        b.setInput(0, tube)
        b.parm("voxelsize").set(voxel)
        combine = geo.createNode("vdbcombine", f"vdb_sub_{voxel}")
        combine.setInput(0, a)
        combine.setInput(1, b)
        combine.parm("operation").set("sdfdifference")
        back = geo.createNode("convertvdb", f"vdb_back_{voxel}")
        back.setInput(0, combine)
        back.parm("conversion").set("poly")
        rows.append(row_for("vdb", f"升目 {voxel}", back, geo,
                            f"vdb{voxel}", expect))

    for row in rows:
        print(f"  {row['way']:<8} {row['detail']:<10} -> "
              f"{row['prims']:>8,}面 {row['seconds']:.3f}秒 "
              f"体積 {row['volume']:.6f}  n角形との差 {row['vs_ngon']:+.6f} "
              f"円との差 {row['vs_circle']:+.6f}")

    # 円柱の辺の数を変えて、boolean が n角形の答えを追うか見る
    cols_rows = []
    for cols in COLS:
        t = make_tube(geo, cols, f"c{cols}")
        node = geo.createNode("boolean::2.0", f"bool_c{cols}")
        node.setInput(0, box)
        node.setInput(1, t)
        node.parm("booleanop").set("subtract")
        want = ngon(cols)
        row = row_for("boolean", f"{cols}角形", node, geo, f"c{cols}", want)
        row["cols"] = cols
        row["expect"] = round(want, 6)
        cols_rows.append(row)
        print(f"  {cols:>4}角形 -> 体積 {row['volume']:.6f} / "
              f"答え {want:.6f}（差 {row['vs_ngon']:+.6f}） "
              f"円との差 {row['vs_circle']:+.6f}")

    sop_bench.save("098", rows,
                   {"circle": round(CIRCLE, 6),
                    "ngon_expect": round(expect, 6),
                    "main_cols": MAIN_COLS,
                    "cols_rows": cols_rows})


if __name__ == "__main__":
    main()
