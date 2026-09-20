# -*- coding: utf-8 -*-
"""実験092 — 辺の長さを揃えると、面はどれだけ増えるか。

remesh は「目指す辺の長さ」を決めると、そこに近い三角形で張り直す。
長さを半分にすると面は4倍になるはず（面積あたりの三角形の数が4倍）。
本当にそうなるか、そのとき形はどれだけずれるかを測る。

    hython examples/092_remesh.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

EDGE = [0.2, 0.1, 0.05, 0.025]


def main():
    geo = sop_bench.fresh()
    sphere = geo.createNode("sphere", "src_sphere")
    sphere.parm("type").set("polymesh")
    sphere.parm("rows").set(40)
    sphere.parm("cols").set(40)
    base = sphere.geometry()
    base_prims = base.intrinsicValue("primitivecount")
    print(f"元: {base_prims} 面")

    rows = []
    prev = None
    for edge in EDGE:
        node = geo.createNode("remesh", f"rem_{edge}")
        node.setInput(0, sphere)
        node.parm("targetsize").set(edge)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        gap = sop_bench.spread(out, base)
        prims = out.intrinsicValue("primitivecount")
        row = {
            "edge": edge,
            "prims": prims,
            "points": out.intrinsicValue("pointcount"),
            "seconds": round(elapsed, 4),
            "gap_mean": round(gap["mean"], 6),
            "gap_max": round(gap["max"], 6),
            "prim_ratio": round(prims / prev, 3) if prev else None,
        }
        prev = prims
        rows.append(row)
        print(f"  辺 {edge:<6} -> {prims:>7} 面 {elapsed:.3f}秒 "
              f"ずれ 平均 {row['gap_mean']:.6f} 最大 {row['gap_max']:.6f}"
              + (f" 面の倍率 {row['prim_ratio']}" if row["prim_ratio"] else ""))

    sop_bench.save("092", rows, {"base_prims": base_prims})


if __name__ == "__main__":
    main()
