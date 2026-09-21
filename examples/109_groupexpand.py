# -*- coding: utf-8 -*-
"""実験109 — groupexpand は1段でどこまで広がるのか。

格子の真ん中の1つから広げて、段ごとの数を数える。
- 辺でつながった隣へ広がるなら、菱形になる: 2k² + 2k + 1
- 角（点）を共有する隣まで広がるなら、正方形になる: (2k + 1)²
点のグループと面のグループの両方で試し、面では Require Primitives Share Edge の
入切も比べる。負の段数（縮める）も試す。

    hython examples/109_groupexpand.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

STEPS = [0, 1, 2, 3, 4, 6, 8]


def seed_group(geo, grid, cls, code):
    wr = geo.createNode("attribwrangle", "seed_%d" % cls)
    wr.setInput(0, grid)
    wr.parm("class").set(cls)            # 1 = Primitives, 2 = Points
    wr.parm("snippet").set(code)
    return wr


def count(node, kind):
    geo = node.geometry()
    group = (geo.findPointGroup if kind == "points" else geo.findPrimGroup)("grown")
    return len(group.points() if kind == "points" else group.prims()) if group else 0


def main():
    geo = sop_bench.fresh()
    # 点: 21×21 の点、真ん中は 10*21+10
    gpts = geo.createNode("grid", "gp")
    gpts.parm("rows").set(21)
    gpts.parm("cols").set(21)
    spts = seed_group(geo, gpts, 2, 'i@group_start = (@ptnum == 220);')
    # 面: 22×22 の点 = 21×21 の面、真ん中は 10*21+10
    gprm = geo.createNode("grid", "gq")
    gprm.parm("rows").set(22)
    gprm.parm("cols").set(22)
    sprm = seed_group(geo, gprm, 1, 'i@group_start = (@primnum == 220);')

    rows = []
    cases = [("points", spts, "points", None), ("prims_edge", sprm, "prims", True),
             ("prims_point", sprm, "prims", False)]
    for label, src, kind, share in cases:
        for k in STEPS:
            node = geo.createNode("groupexpand", f"{label}_{k}")
            node.setInput(0, src)
            node.parm("group").set("start")
            node.parm("grouptype").set(kind)
            node.parm("outputgroup").set("grown")
            node.parm("numsteps").set(k)
            if share is not None:
                node.parm("primshareedge").set(share)
            t0 = time.perf_counter()
            got = count(node, kind)
            rows.append({"case": label, "steps": k, "count": got,
                         "diamond": 2 * k * k + 2 * k + 1, "square": (2 * k + 1) ** 2,
                         "sec": round(time.perf_counter() - t0, 4)})
            print(rows[-1])

    # 縮める: 真ん中の 9×9 の点から -1, -2 段
    block = seed_group(geo, gpts, 2,
                       'int r = @ptnum / 21, c = @ptnum % 21;'
                       ' i@group_start = abs(r - 10) <= 4 && abs(c - 10) <= 4;')
    shrink = []
    for k in (0, -1, -2, -4):
        node = geo.createNode("groupexpand", f"shrink_{-k}")
        node.setInput(0, block)
        node.parm("group").set("start")
        node.parm("grouptype").set("points")
        node.parm("outputgroup").set("grown")
        node.parm("numsteps").set(k)
        shrink.append({"steps": k, "count": count(node, "points"),
                       "square": max(0, 9 + 2 * k) ** 2})
        print(shrink[-1])

    path = os.path.join(sop_bench.OUT, "109_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "shrink": shrink}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
