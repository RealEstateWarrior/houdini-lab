# -*- coding: utf-8 -*-
"""実験141 — pointsfromvolume の点の数は、体積 ÷ 間隔³ になるか。

形の中を、間隔 s の格子（Grid）か四面体の並び（Tetrahedral）で点を埋める。
格子なら1点あたりの体積は s³、四面体の並び（面心立方の詰め方なら）は s³/√2 のはず。
箱（2×1×1、体積2）と球（半径1、体積 4π/3）で、点の数 × 1点あたりの体積 が
形の体積にどれだけ近いかを見る。

    hython examples/141_points_from_volume.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    box.parmTuple("size").set((2.0, 1.0, 1.0))
    sp = geo.createNode("sphere", "sp")
    sp.parm("type").set("polymesh")
    sp.parm("rows").set(96)
    sp.parm("cols").set(192)
    shapes = {"box": (box, 2.0), "sphere": (sp, 4 / 3 * math.pi)}
    rows = []
    for name, (src, vol) in shapes.items():
        for init in ("grid", "tetrahedral"):
            for sep in (0.1, 0.05, 0.025):
                pv = geo.createNode("pointsfromvolume", f"pv_{name}_{init}_{int(sep * 1000)}")
                pv.setInput(0, src)
                pv.parm("inittype").set(init)
                pv.parm("particlesep").set(sep)
                t0 = time.perf_counter()
                n = pv.geometry().intrinsicValue("pointcount")
                sec = time.perf_counter() - t0
                rows.append({"shape": name, "init": init, "sep": sep, "points": n,
                             "grid_est": round(n * sep ** 3, 6),
                             "fcc_est": round(n * sep ** 3 / math.sqrt(2), 6),
                             "volume": round(vol, 6), "sec": round(sec, 3)})
                print(rows[-1])
    path = os.path.join(sop_bench.OUT, "141_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
