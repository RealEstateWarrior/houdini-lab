# -*- coding: utf-8 -*-
"""実験173 — 同じ計算を、VEX（点ごと）・VEX（Detail で1回・ループ）・Python SOP で書くと、どれだけ速さが違うか。

grid の点に「@P.y = sin(@P.x * 10) * cos(@P.z * 10) * 0.1」を入れる。点の数は 1 万・10 万・100 万。
1. attribwrangle（Run Over = Points）
2. attribwrangle（Run Over = Detail）で for ループ（setpointattrib）
3. Python SOP（hou の setPointFloatAttribValues で一度に書く）
4. Python SOP（点を1つずつ setPosition）— 10 万点まで
各 3 回はかって一番速い値を残す（1回目は組み立てで遅くなるため、先に 1 回流しておく）。結果が同じになるかも確かめる。

    hython examples/173_vex_vs_python.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

PY_BULK = '''
import math
node = hou.pwd()
geo = node.geometry()
k = node.evalParm("k")
P = geo.pointFloatAttribValues("P")
out = list(P)
for i in range(0, len(P), 3):
    out[i + 1] = math.sin(P[i] * 10) * math.cos(P[i + 2] * 10) * 0.1 * k
geo.setPointFloatAttribValues("P", out)
'''

PY_EACH = '''
import math
node = hou.pwd()
geo = node.geometry()
k = node.evalParm("k")
for pt in geo.points():
    p = pt.position()
    pt.setPosition((p[0], math.sin(p[0] * 10) * math.cos(p[2] * 10) * 0.1 * k, p[2]))
'''


def timed(node, repeat=3):
    """cook(force=True) だけでは VEX が計算し直さなかった（1e-5 秒）ので、
    コードが読む k を毎回少し変えて、本当に計算し直させる（組み立て直しは起きない）。"""
    if node.parm("k") is None:
        node.addSpareParmTuple(hou.FloatParmTemplate("k", "k", 1, default_value=(1.0,)))
    node.parm("k").set(1.0)
    node.geometry()
    best = 1e9
    for i in range(repeat):
        node.parm("k").set(1.0 + (i + 1) * 1e-7)
        t0 = time.perf_counter()
        node.geometry()
        best = min(best, time.perf_counter() - t0)
    node.parm("k").set(1.0)
    node.geometry()
    return best


def main():
    geo = sop_bench.fresh()
    rows = []
    for side in (100, 316, 1000):
        grid = geo.createNode("grid", f"g{side}")
        grid.parm("rows").set(side)
        grid.parm("cols").set(side)
        n = side * side
        nodes = {}
        w1 = geo.createNode("attribwrangle", f"pts{side}")
        w1.setInput(0, grid)
        w1.parm("snippet").set("@P.y = sin(@P.x * 10) * cos(@P.z * 10) * 0.1 * ch('k');")
        nodes["VEX（点ごと）"] = w1
        w2 = geo.createNode("attribwrangle", f"det{side}")
        w2.setInput(0, grid)
        w2.parm("class").set("detail")
        w2.parm("snippet").set("for (int i = 0; i < npoints(0); i++) { vector p = point(0, 'P', i);"
                               " p.y = sin(p.x * 10) * cos(p.z * 10) * 0.1 * ch('k'); setpointattrib(0, 'P', i, p); }")
        nodes["VEX（Detail でループ）"] = w2
        py = geo.createNode("python", f"py{side}")
        py.setInput(0, grid)
        py.parm("python").set(PY_BULK)
        nodes["Python（まとめて書く）"] = py
        if side <= 316:
            pe = geo.createNode("python", f"pe{side}")
            pe.setInput(0, grid)
            pe.parm("python").set(PY_EACH)
            nodes["Python（1点ずつ）"] = pe
        ref = None
        for name, node in nodes.items():
            sec = timed(node, 3 if side < 1000 else 2)
            ys = node.geometry().pointFloatAttribValues("P")[1::3]
            if ref is None:
                ref = ys
            diff = max(abs(a - b) for a, b in zip(ref, ys))
            rows.append({"points": n, "method": name, "sec": round(sec, 5), "us_per_point": round(sec / n * 1e6, 4),
                         "max_diff": diff})
            print(rows[-1])
    sop_bench.save(173, rows)


if __name__ == "__main__":
    main()
