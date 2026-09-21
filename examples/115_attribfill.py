# -*- coding: utf-8 -*-
"""実験115 — attribfill の埋め方は、式で出る答えと合うか。

1. Interpolate (Poisson): 板の左端を0、右端を1に固定して中を埋める。
   まわりの平均になるように埋めるなら、答えは x に比例する直線になるはず。
2. Arrival Time (Eikonal): 左端から出発した「到着時間」。速さ1なら左端からの距離 = x。
3. 同じく1点から: 距離 √(x²+z²) と比べる（網の目に沿って進むぶん、ずれるはず）。
4. 球の北極から: 表面に沿った距離（大円の弧）r·θ と比べる。

    hython examples/115_attribfill.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def wrangle(geo, src, code, name):
    wr = geo.createNode("attribwrangle", name)
    wr.setInput(0, src)
    wr.parm("snippet").set(code)
    return wr


def fill(geo, src, mode, name):
    node = geo.createNode("attribfill", name)
    node.setInput(0, src)
    node.parm("mode").set(mode)
    node.parm("attrib").set("val")
    node.parm("boundary").set("fixed")
    return node


def errors(node, want):
    geo = node.geometry()
    vals = geo.pointFloatAttribValues("val")
    pos = geo.pointFloatAttribValues("P")
    diffs = [v - want(pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]) for i, v in enumerate(vals)]
    return {"mean_abs": round(sum(abs(d) for d in diffs) / len(diffs), 6),
            "max_abs": round(max(abs(d) for d in diffs), 6),
            "mean": round(sum(diffs) / len(diffs), 6), "n": len(diffs)}


def main():
    rows = []
    geo = sop_bench.fresh()
    for res in (21, 41, 81):
        grid = geo.createNode("grid", f"g{res}")
        grid.parmTuple("size").set((4.0, 2.0))
        grid.parm("rows").set(res // 2 + 1)
        grid.parm("cols").set(res)
        # 左端 x=-2 を0、右端 x=2 を1に固定
        edges = wrangle(geo, grid, 'f@val = @P.x > 0 ? 1 : 0;\n'
                        'i@group_fixed = abs(abs(@P.x) - 2) < 1e-5;', f"edges{res}")
        t0 = time.perf_counter()
        pois = fill(geo, edges, "poisson", f"pois{res}")
        rows.append({"case": "poisson_edges", "res": res,
                     **errors(pois, lambda x, y, z: (x + 2) / 4),
                     "sec": round(time.perf_counter() - t0, 4)})
        print(rows[-1])
        # 左端から出発（Eikonal）。答えは x+2
        left = wrangle(geo, grid, 'f@val = 0;\ni@group_fixed = abs(@P.x + 2) < 1e-5;', f"left{res}")
        t0 = time.perf_counter()
        eik = fill(geo, left, "eikonal", f"eik{res}")
        rows.append({"case": "eikonal_edge", "res": res,
                     **errors(eik, lambda x, y, z: x + 2),
                     "sec": round(time.perf_counter() - t0, 4)})
        print(rows[-1])
        # 真ん中の1点から。答えは √(x²+z²)
        center = wrangle(geo, grid, 'f@val = 0;\ni@group_fixed = length(@P) < 1e-5;', f"c{res}")
        t0 = time.perf_counter()
        eik1 = fill(geo, center, "eikonal", f"eik1_{res}")
        rows.append({"case": "eikonal_point", "res": res,
                     **errors(eik1, lambda x, y, z: math.sqrt(x * x + z * z)),
                     "sec": round(time.perf_counter() - t0, 4)})
        print(rows[-1])
        rows.append({"case": "eikonal_point_vs_manhattan", "res": res,
                     **errors(eik1, lambda x, y, z: abs(x) + abs(z))})
        print(rows[-1])
        # 同じ格子を三角形にすると（斜めの辺ができる）
        tri = geo.createNode("grid", f"t{res}")
        tri.parmTuple("size").set((4.0, 2.0))
        tri.parm("rows").set(res // 2 + 1)
        tri.parm("cols").set(res)
        tri.parm("surftype").set("triangles")
        ctri = wrangle(geo, tri, 'f@val = 0; i@group_fixed = length(@P) < 1e-5;', f"ct{res}")
        eik3 = fill(geo, ctri, "eikonal", f"eik3_{res}")
        rows.append({"case": "eikonal_point_tris", "res": res,
                     **errors(eik3, lambda x, y, z: math.sqrt(x * x + z * z))})
        print(rows[-1])

    # 球の北極から。答えは r·θ（r=1）
    for res in (24, 48, 96):
        sp = geo.createNode("sphere", f"sp{res}")
        sp.parm("type").set("polymesh")
        sp.parm("rows").set(res)
        sp.parm("cols").set(res * 2)
        pole = wrangle(geo, sp, 'f@val = 0;\ni@group_fixed = @P.y > 0.99999;', f"pole{res}")
        t0 = time.perf_counter()
        eik = fill(geo, pole, "eikonal", f"eiks{res}")
        rows.append({"case": "eikonal_sphere", "res": res,
                     **errors(eik, lambda x, y, z: math.acos(max(-1.0, min(1.0, y /
                              math.sqrt(x * x + y * y + z * z))))),
                     "sec": round(time.perf_counter() - t0, 4)})
        print(rows[-1])

    path = os.path.join(sop_bench.OUT, "115_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
