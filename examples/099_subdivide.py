# -*- coding: utf-8 -*-
"""実験099 — 立方体を細分化すると、どこまで縮んで、どこで止まるか。

subdivide（Catmull-Clark）は、割るたびに形を滑らかにする。
立方体を割り続けると、行き着く先は決まった形（極限曲面）で、その体積も決まっている。
どこまで縮むのか、どの深さで止まるのかを測る。

答えが分かっている所と突き合わせる:
  1辺 1.0 の立方体の体積は 1.0。割れば必ず小さくなる。
  深さを増やすほど体積は単調に減り、ある値に収束するはず。

あわせて Algorithm を5通り（houdini / mantra / osdcc / osdloop / osdbilinear）
比べる。bilinear は割るだけで滑らかにしないので、体積は変わらないはず。
これが変わらなければ、測り方が正しいことの裏付けにもなる。

    hython examples/099_subdivide.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

DEPTHS = [0, 1, 2, 3, 4, 5, 6]
ALGOS = [(0, "houdini"), (1, "mantra"), (2, "osdcc"),
         (3, "osdloop"), (4, "osdbilinear")]


def volume_of(parent, node, tag):
    meas = parent.createNode("measure", f"vol_{tag}")
    meas.setInput(0, node)
    meas.parm("measure").set("volume")
    meas.parm("attribname").set("vol")
    total = sum(prim.attribValue("vol") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "the_box")
    box.parm("type").set("poly")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    base_vol = volume_of(geo, box, "base")
    print(f"元の立方体: {box.geometry().intrinsicValue('primitivecount')}面 "
          f"体積 {base_vol:.6f}")

    rows = []
    prev = base_vol
    for depth in DEPTHS:
        node = geo.createNode("subdivide", f"sd_{depth}")
        node.setInput(0, box)
        node.parm("iterations").set(depth)
        node.parm("algorithm").set(2)          # 2 = osdcc（Catmull-Clark）
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        vol = volume_of(geo, node, f"d{depth}")
        row = {
            "depth": depth,
            "prims": out.intrinsicValue("primitivecount"),
            "points": out.intrinsicValue("pointcount"),
            "seconds": round(elapsed, 4),
            "volume": round(vol, 6),
            "volume_pct": round(vol / base_vol * 100, 4),
            "step": round(vol - prev, 6),
        }
        prev = vol
        rows.append(row)
        print(f"  深さ {depth} -> {row['prims']:>7,}面 {elapsed:.3f}秒 "
              f"体積 {vol:.6f}（元の {row['volume_pct']:.2f}%、"
              f"前の段から {row['step']:+.6f}）")

    # 割り方（Algorithm）を5通り。深さは3で揃える
    algos = []
    for index, name in ALGOS:
        node = geo.createNode("subdivide", f"al_{index}")
        node.setInput(0, box)
        node.parm("iterations").set(3)
        node.parm("algorithm").set(index)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        vol = volume_of(geo, node, f"a{index}")
        algos.append({
            "algorithm": name,
            "prims": out.intrinsicValue("primitivecount"),
            "points": out.intrinsicValue("pointcount"),
            "seconds": round(elapsed, 4),
            "volume": round(vol, 6),
            "volume_pct": round(vol / base_vol * 100, 4),
        })
        print(f"  深さ3 / {name:<12} -> {out.intrinsicValue('primitivecount'):>7,}面 "
              f"体積 {vol:.6f}（元の {algos[-1]['volume_pct']:.2f}%）")

    sop_bench.save("099", rows,
                   {"base_volume": round(base_vol, 6), "algorithms": algos})


if __name__ == "__main__":
    main()
