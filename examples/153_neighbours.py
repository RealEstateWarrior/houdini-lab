# -*- coding: utf-8 -*-
"""実験153 — VEX の neighbourcount() で数えた隣の点の数から、オイラーの式 V − E + F は出るか。

隣の点の数の合計は、辺の数の2倍になるはず（辺1本が両端の点に1回ずつ数えられる）。
そこで E = Σ neighbourcount / 2 として、V − E + F を形ごとに出す。
答えは 板（grid）1、球と箱 2、トーラス 0。穴が1つ増えるごとに 2 減る。
隣の数の分布（角・縁・内側・極）も残す。

    hython examples/153_neighbours.py
"""
import collections
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    shapes = []
    g1 = geo.createNode("grid", "grid")
    g1.parm("rows").set(6)
    g1.parm("cols").set(9)
    shapes.append(("grid 6×9", g1, 1))
    b = geo.createNode("box", "box")
    b.parm("type").set("polymesh")
    b.parm("dodivs").set(1)
    b.parmTuple("divs").set((4, 4, 4))
    shapes.append(("box 4×4×4", b, 2))
    s = geo.createNode("sphere", "sph")
    s.parm("type").set("polymesh")
    s.parm("rows").set(9)
    s.parm("cols").set(16)
    shapes.append(("sphere 9×16", s, 2))
    t = geo.createNode("torus", "tor")
    t.parm("rows").set(8)
    t.parm("cols").set(12)
    shapes.append(("torus 8×12", t, 0))
    tube = geo.createNode("tube", "tube")
    tube.parm("type").set("poly")
    tube.parm("rows").set(5)
    tube.parm("cols").set(10)
    shapes.append(("tube 5×10（蓋なし）", tube, 0))
    rows = []
    for name, src, want in shapes:
        w = geo.createNode("attribwrangle", "w_" + src.name())
        w.setInput(0, src)
        w.parm("snippet").set("i@nb = neighbourcount(0, @ptnum);")
        t0 = time.perf_counter()
        g = w.geometry()
        sec = time.perf_counter() - t0
        nbs = g.pointIntAttribValues("nb")
        V, F = len(nbs), len(g.prims())
        E2 = sum(nbs)
        # 辺を面から数え直して、neighbourcount の合計と比べる
        edges = set()
        for pr in g.prims():
            vs = [v.point().number() for v in pr.vertices()]
            closed = pr.intrinsicValue("closed")
            n = len(vs)
            for k in range(n if closed else n - 1):
                a, c = vs[k], vs[(k + 1) % n]
                edges.add((min(a, c), max(a, c)))
        rows.append({"shape": name, "V": V, "F": F, "sum_nb": E2, "E_from_nb": E2 / 2, "E_from_prims": len(edges),
                     "euler": V - E2 / 2 + F, "want": want,
                     "hist": dict(sorted(collections.Counter(nbs).items())), "sec": round(sec, 4)})
        print(rows[-1])
    sop_bench.save(153, rows)


if __name__ == "__main__":
    main()
