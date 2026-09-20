# -*- coding: utf-8 -*-
"""実験091 — 面を減らすと、形はどれだけずれるか。

polyreduce は「残す割合」を決めると、そこまで面を間引く。
間引けば軽くなるが、形は元から離れる。どれだけ離れるのかを測る。

ずれの測り方は、減らしたあとの各点から、元の面までの最短距離。
その平均と最大を取る。元の大きさに対する割合で見る。

    hython examples/091_polyreduce.py
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

KEEP = [80, 50, 25, 10, 5, 2]


def make_source(parent):
    """元の形。球を細かく割って、なだらかな凹凸を付ける。"""
    sphere = parent.createNode("sphere", "src_sphere")
    sphere.parm("type").set("polymesh")
    sphere.parmTuple("rad").set((1.0, 1.0, 1.0))
    sphere.parm("rows").set(60)
    sphere.parm("cols").set(60)
    mountain = parent.createNode("mountain", "src_mountain")
    mountain.setInput(0, sphere)
    mountain.parm("height").set(0.18)
    mountain.parm("elementsize").set(0.9)
    mountain.parmTuple("offset").set((3.0, 0.0, 0.0))
    return mountain


def main():
    geo = sop_bench.fresh()
    parent = geo
    source = make_source(parent)
    base = source.geometry()
    base_prims = base.intrinsicValue("primitivecount")
    base_size = base.boundingBox().sizevec()[0]
    print(f"元: {base_prims} 面 / 幅 {base_size:.4f}")

    rows = []
    for keep in KEEP:
        node = parent.createNode("polyreduce::2.0", f"red_{keep}")
        node.setInput(0, source)
        node.parm("percentage").set(keep)
        import time
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        gap = sop_bench.spread(out, base)
        row = {
            "keep": keep,
            "prims": out.intrinsicValue("primitivecount"),
            "points": out.intrinsicValue("pointcount"),
            "seconds": round(elapsed, 4),
            "gap_mean": round(gap["mean"], 6),
            "gap_max": round(gap["max"], 6),
            "gap_mean_pct": round(gap["mean"] / base_size * 100, 4),
            "gap_max_pct": round(gap["max"] / base_size * 100, 4),
        }
        rows.append(row)
        print(f"  残す {keep:>3}% -> {row['prims']:>6} 面 "
              f"{row['seconds']:.3f}秒 ずれ 平均 {row['gap_mean']:.6f}"
              f"（幅の {row['gap_mean_pct']:.3f}%） 最大 {row['gap_max']:.6f}")

    sop_bench.save("091", rows,
                   {"base_prims": base_prims, "base_size": round(base_size, 6)})


if __name__ == "__main__":
    main()
