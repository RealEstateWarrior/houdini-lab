# -*- coding: utf-8 -*-
"""実験102 — 押し出した体積は、面積×距離になるか。

polyextrude で平らな板を厚くすると、できる立体の体積は
「元の面積 × 押し出した距離」になるはず。ここを突き合わせる。

さらに Inset（内側に寄せる幅）を入れると、上の面が小さくなる。
1辺 L の正方形を i だけ内側に寄せると、上の面は (L-2i)²。
立体は四角錐台になるので、体積は
    d/3 × (L² + (L-2i)² + L(L-2i))
になるはず。ここも突き合わせる。

    hython examples/102_extrude.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

SIDE = 2.0
DISTS = [0.1, 0.25, 0.5, 1.0, 2.0]
INSETS = [0.0, 0.1, 0.25, 0.5, 0.9]
INSET_DIST = 1.0


def volume_of(parent, node, tag):
    meas = parent.createNode("measure", f"vol_{tag}")
    meas.setInput(0, node)
    meas.parm("measure").set("volume")
    meas.parm("attribname").set("vol")
    total = sum(prim.attribValue("vol") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def frustum(side, inset, dist):
    """四角錐台の体積。上の1辺は side - 2*inset。"""
    top = side - 2.0 * inset
    return dist / 3.0 * (side * side + top * top + side * top)


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "plate")
    grid.parmTuple("size").set((SIDE, SIDE))
    grid.parm("rows").set(2)
    grid.parm("cols").set(2)
    area = SIDE * SIDE
    print(f"板: 1辺 {SIDE} / 面積 {area:.6f}")

    rows = []
    for dist in DISTS:
        node = geo.createNode("polyextrude", f"ex_{dist}")
        node.setInput(0, grid)
        node.parm("dist").set(dist)
        node.parm("outputfront").set(True)
        node.parm("outputback").set(True)
        node.parm("outputside").set(True)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        vol = abs(volume_of(geo, node, f"e{dist}"))
        want = area * dist
        rows.append({
            "dist": dist,
            "prims": out.intrinsicValue("primitivecount"),
            "volume": round(vol, 6),
            "want": round(want, 6),
            "diff": round(vol - want, 6),
            "seconds": round(elapsed, 4),
        })
        print(f"  距離 {dist:<5} -> {rows[-1]['prims']:>3}面 体積 {vol:.6f} / "
              f"面積×距離 {want:.6f}（差 {vol - want:+.6f}）")

    inset_rows = []
    for inset in INSETS:
        node = geo.createNode("polyextrude", f"in_{inset}")
        node.setInput(0, grid)
        node.parm("dist").set(INSET_DIST)
        node.parm("inset").set(inset)
        node.parm("outputfront").set(True)
        node.parm("outputback").set(True)
        node.parm("outputside").set(True)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        vol = abs(volume_of(geo, node, f"i{inset}"))
        want = frustum(SIDE, inset, INSET_DIST)
        prism = area * INSET_DIST
        inset_rows.append({
            "inset": inset,
            "top_side": round(SIDE - 2.0 * inset, 6),
            "prims": out.intrinsicValue("primitivecount"),
            "volume": round(vol, 6),
            "want": round(want, 6),
            "diff": round(vol - want, 6),
            "vs_prism": round(vol - prism, 6),
            "seconds": round(elapsed, 4),
        })
        print(f"  Inset {inset:<4} (上の1辺 {SIDE - 2 * inset:.2f}) -> "
              f"体積 {vol:.6f} / 四角錐台の式 {want:.6f}（差 {vol - want:+.6f}）")

    sop_bench.save("102", rows,
                   {"side": SIDE, "area": round(area, 6),
                    "inset_dist": INSET_DIST, "inset_rows": inset_rows})


if __name__ == "__main__":
    main()
