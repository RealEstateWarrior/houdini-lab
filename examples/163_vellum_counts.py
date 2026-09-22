# -*- coding: utf-8 -*-
"""実験163 — vellumconstraints（Cloth）は、網の辺ごとに何本の拘束を作るか。

rows × cols の grid（四角形）と、それを三角形にしたもの（divide）に vellumconstraints（Constraint Type = Cloth）をかけ、
出てくる拘束（2つ目の出力の線）を種類（type 属性）ごとに数える。
四角形の網の辺の数 E、三角形にしたときの辺の数、内側の辺（2枚の面にはさまれた辺）の数と比べる。

    hython examples/163_vellum_counts.py
"""
import collections
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def edges_of(g):
    count = collections.Counter()
    for pr in g.prims():
        vs = [v.point().number() for v in pr.vertices()]
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            count[(min(a, b), max(a, b))] += 1
    inner = sum(1 for c in count.values() if c == 2)
    return len(count), inner


def main():
    geo = sop_bench.fresh()
    rows = []
    for r, c in ((3, 3), (5, 8), (10, 10)):
        grid = geo.createNode("grid", f"g{r}_{c}")
        grid.parm("rows").set(r)
        grid.parm("cols").set(c)
        tri = geo.createNode("divide", f"t{r}_{c}")
        tri.setInput(0, grid)
        for name, src in (("quads", grid), ("triangles", tri)):
            vc = geo.createNode("vellumconstraints", f"vc_{name}_{r}_{c}")
            vc.setInput(0, src)
            vc.parm("constrainttype").set("cloth")
            t0 = time.perf_counter()
            cons = vc.geometry(1)
            sec = time.perf_counter() - t0
            types = collections.Counter(cons.primStringAttribValues("type")) if cons.findPrimAttrib("type") else {}
            E, inner = edges_of(src.geometry())
            rows.append({"grid": f"{r}×{c}", "mesh": name, "points": len(src.geometry().points()), "faces": len(src.geometry().prims()),
                         "edges": E, "inner_edges": inner, "constraints": dict(types), "total": len(cons.prims()),
                         "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(163, rows)


if __name__ == "__main__":
    main()
