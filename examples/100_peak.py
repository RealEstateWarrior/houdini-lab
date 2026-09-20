# -*- coding: utf-8 -*-
"""実験100 — 法線の向きに押し出すと、体積は式どおりに増えるか。

peak は点を、その点の法線の向きへ Distance だけ動かす。
球なら、半径 r が r+d になるだけなので、体積は ((r+d)/r)³ 倍になるはず。
球は多角形なので体積そのものは真の球より小さいが、**倍率なら分割の粗さに
関係なく式に合う**。ここを突き合わせる。

同じことを立方体でやると、動く向きが変わる。立方体の点の法線は、隣り合う3面の
平均で (1,1,1)/√3 を向く。だから角は各軸に d/√3 しか動かず、1辺は 1+2d ではなく
1 + 2d/√3 になる。こちらの式に合うかを確かめる。

    hython examples/100_peak.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

RADIUS = 1.0
DISTS = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]
ROWS_COLS = [(20, 20), (60, 60), (120, 120)]


def volume_of(parent, node, tag):
    meas = parent.createNode("measure", f"vol_{tag}")
    meas.setInput(0, node)
    meas.parm("measure").set("volume")
    meas.parm("attribname").set("vol")
    total = sum(prim.attribValue("vol") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def peak_of(geo, source, dist, tag):
    node = geo.createNode("peak", f"peak_{tag}")
    node.setInput(0, source)
    node.parm("dist").set(dist)
    start = time.perf_counter()
    out = node.geometry()
    elapsed = time.perf_counter() - start
    return node, out, elapsed


def main():
    geo = sop_bench.fresh()

    # ---- 球。倍率が式に合うかを見る ----
    sphere_rows = []
    for rows, cols in ROWS_COLS:
        sphere = geo.createNode("sphere", f"sph_{rows}")
        sphere.parm("type").set("polymesh")
        sphere.parm("rows").set(rows)
        sphere.parm("cols").set(cols)
        sphere.parmTuple("rad").set((RADIUS, RADIUS, RADIUS))
        normal = geo.createNode("normal", f"nml_{rows}")
        normal.setInput(0, sphere)
        base_vol = volume_of(geo, normal, f"sb_{rows}")
        true_vol = 4.0 / 3.0 * math.pi * RADIUS ** 3
        print(f"球 {rows}×{cols}: 体積 {base_vol:.6f}"
              f"（真の球 {true_vol:.6f} の {base_vol / true_vol * 100:.3f}%）")
        for dist in DISTS:
            node, out, elapsed = peak_of(geo, normal, dist, f"s{rows}_{dist}")
            vol = volume_of(geo, node, f"s{rows}_{dist}")
            want = ((RADIUS + dist) / RADIUS) ** 3
            got = vol / base_vol
            sphere_rows.append({
                "rows": rows, "dist": dist,
                "volume": round(vol, 6),
                "ratio": round(got, 6),
                "want_ratio": round(want, 6),
                "diff": round(got - want, 6),
                "diff_pct": round((got - want) / want * 100, 4),
                "seconds": round(elapsed, 4),
            })
            print(f"   d={dist:<5} 体積 {vol:>10.6f} 倍率 {got:.6f} / "
                  f"式 {want:.6f}（差 {got - want:+.6f} = "
                  f"{(got - want) / want * 100:+.4f}%）")

    # ---- 立方体。式から外れることを見る ----
    box = geo.createNode("box", "the_box")
    box.parm("type").set("poly")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    box_normal = geo.createNode("normal", "box_nml")
    box_normal.setInput(0, box)
    box_base = volume_of(geo, box_normal, "box_base")
    print(f"立方体: 体積 {box_base:.6f}")

    box_rows = []
    for dist in DISTS:
        node, out, elapsed = peak_of(geo, box_normal, dist, f"b_{dist}")
        vol = volume_of(geo, node, f"b_{dist}")
        # 1辺が 1+2d になった立方体なら、こうなるはず
        want = (1.0 + 2.0 * dist) ** 3
        got = vol / box_base
        # 立方体の点の法線は、隣り合う3面の平均で (1,1,1)/√3 を向く。
        # だから角は各軸に d/√3 だけ動き、1辺は 1 + 2d/√3 になる。
        side = 1.0 + 2.0 * dist / math.sqrt(3.0)
        want_real = side ** 3
        box_rows.append({
            "dist": dist,
            "volume": round(vol, 6),
            "ratio": round(got, 6),
            "want_cube_ratio": round(want, 6),
            "want_real": round(want_real, 6),
            "side": round(side, 6),
            "diff_naive": round(got - want, 6),
            "diff_real": round(got - want_real, 6),
            "seconds": round(elapsed, 4),
        })
        print(f"   d={dist:<5} 体積 {vol:>10.6f} / 1+2d の式 {want:>9.6f}"
              f"（差 {got - want:+.6f}） / 1+2d/√3 の式 {want_real:>9.6f}"
              f"（差 {got - want_real:+.6f}）")

    sop_bench.save("100", sphere_rows,
                   {"true_sphere": round(4.0 / 3.0 * math.pi * RADIUS ** 3, 6),
                    "box_base": round(box_base, 6),
                    "box_rows": box_rows})


if __name__ == "__main__":
    main()
