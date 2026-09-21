# -*- coding: utf-8 -*-
"""実験118 — revolve で回した形の面積と体積は、式どおりか。

線分 (r1, 0) → (r2, h) を y 軸のまわりに k 分割で一周させると、円錐台の側面を
k 角の角錐台で近似した形になる。1枚の面は等脚台形で、
  上下の辺 2·r·sin(π/k)、高さ √(h² + ((r2 − r1)·cos(π/k))²)
面積の合計はこれの k 倍。k を増やすと、円錐台の側面積 π(r1 + r2)·√(h² + (r2 − r1)²) に近づく。

さらに、閉じた断面（正方形）を回すと、ドーナツ型の体積は
パップス・ギュルダンの定理で「断面積 × 断面の重心が回る長さ」になる。
k 角で回した体積は、重心の円を k 角形にした長さ（2k·R·sin(π/k)）ではなく、
断面の各部分ごとに縮むので、式を別に立てて比べる（下の poly_torus_volume）。

    hython examples/118_revolve.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def area_of(parent, node):
    meas = parent.createNode("measure", "area")
    meas.setInput(0, node)
    meas.parm("measure").set("area")
    meas.parm("attribname").set("a")
    total = sum(p.attribValue("a") for p in meas.geometry().prims())
    meas.destroy()
    return total


def frustum_poly_area(r1, r2, h, k):
    s1, s2 = 2 * r1 * math.sin(math.pi / k), 2 * r2 * math.sin(math.pi / k)
    slant = math.sqrt(h * h + ((r2 - r1) * math.cos(math.pi / k)) ** 2)
    return k * (s1 + s2) / 2 * slant


def poly_torus_volume(r_in, r_out, height, k):
    """断面 [r_in, r_out] × [0, height] の長方形を k 角で回した体積。

    半径 r の円を k 角形にすると面積は (k/2)·r²·sin(2π/k)。
    中空の k 角柱 = 外の k 角柱 − 内の k 角柱。
    """
    return (k / 2) * math.sin(2 * math.pi / k) * (r_out ** 2 - r_in ** 2) * height


def main():
    geo = sop_bench.fresh()
    rows = []
    r1, r2, h = 1.0, 0.4, 1.5
    seg = geo.createNode("line", "seg")
    seg.parmTuple("origin").set((r1, 0.0, 0.0))
    seg.parmTuple("dir").set((r2 - r1, h, 0.0))
    seg.parm("dist").set(math.hypot(r2 - r1, h))
    seg.parm("points").set(2)
    for k in (4, 8, 16, 64, 256):
        rv = geo.createNode("revolve::2.0", f"rv{k}")
        rv.setInput(0, seg)
        rv.parm("divs").set(k)
        t0 = time.perf_counter()
        got = area_of(geo, rv)
        sec = time.perf_counter() - t0
        rows.append({"case": "frustum", "k": k, "area": round(got, 6),
                     "want_poly": round(frustum_poly_area(r1, r2, h, k), 6),
                     "want_smooth": round(math.pi * (r1 + r2) * math.hypot(h, r2 - r1), 6),
                     "prims": rv.geometry().intrinsicValue("primitivecount"),
                     "sec": round(sec, 4)})
        print(rows[-1])

    # 閉じた断面（正方形 0.5×0.5、中心が軸から1.25）を回す
    sq = geo.createNode("attribwrangle", "square")
    sq.parm("class").set(0)
    sq.parm("snippet").set(
        'int a = addpoint(0, {1.0, 0, 0}); int b = addpoint(0, {1.5, 0, 0});\n'
        'int c = addpoint(0, {1.5, 0.5, 0}); int d = addpoint(0, {1.0, 0.5, 0});\n'
        'addprim(0, "poly", a, b, c, d);')
    for k in (4, 8, 16, 64, 256):
        rv = geo.createNode("revolve::2.0", f"sq{k}")
        rv.setInput(0, sq)
        rv.parm("divs").set(k)
        vol = sop_bench.volume(rv.geometry())
        area = 0.25
        pappus = area * 2 * math.pi * 1.25
        rows.append({"case": "square_ring", "k": k, "volume": round(vol, 6),
                     "want_poly": round(poly_torus_volume(1.0, 1.5, 0.5, k), 6),
                     "want_smooth": round(pappus, 6),
                     "prims": rv.geometry().intrinsicValue("primitivecount")})
        print(rows[-1])

    path = os.path.join(sop_bench.OUT, "118_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"r1": r1, "r2": r2, "h": h, "rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
