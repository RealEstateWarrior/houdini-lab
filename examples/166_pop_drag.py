# -*- coding: utf-8 -*-
"""実験166 — popdrag の Air Resistance k で、落ちる粒の速さは g/k で頭打ちになるか。

実験165 と同じ 1 粒に、popsolver の力の入力へ popdrag（Wind Velocity 0、Ignore Mass 入）をつなぐ。
抵抗が「速さに比例する力 −k·v」なら、終端速度は g/k（k = 1 で 9.80665）。速さの2乗に比例する力なら √(g/k)。
k を 0.5・1・2・5、DOP Network の Substeps を 1 と 4 にして、1・2・4 秒後の v.y を読む。

    hython examples/166_pop_drag.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

G = 9.80665


def build(geo, tag, k, sub):
    pt = geo.createNode("add", f"pt{tag}")
    pt.parm("points").set(1)
    pt.parm("usept0").set(1)
    dop = geo.createNode("dopnet", f"dop{tag}")
    dop.parm("substep").set(sub)
    obj = dop.createNode("popobject", "p")
    solver = dop.createNode("popsolver::2.0", "solver")
    src = dop.createNode("popsource", "src")
    src.parm("emittype").set("allpoint")
    src.parm("soppath").set(pt.path())
    src.parm("constantactivate").set(0)
    src.parm("impulseactiveate").setExpression("$FF == 1")
    src.parm("impulserate").set(1)
    for name in ("velocity1", "velocity2", "velocity3", "varianceamount1", "varianceamount2", "varianceamount3"):
        if src.parm(name) is not None:
            src.parm(name).set(0.0)
    drag = dop.createNode("popdrag", "drag")
    drag.parm("airresist").set(k)
    solver.setInput(0, obj)
    solver.setInput(1, src)
    solver.setInput(2, drag)
    grav = dop.createNode("gravity", "g")
    grav.setInput(0, solver)
    grav.setDisplayFlag(True)
    imp = geo.createNode("dopimport", f"imp{tag}")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    return imp


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    rows = []
    for k in (0.5, 1.0, 2.0, 5.0):
        for sub in (1, 4):
            imp = build(geo, f"{int(k * 10)}_{sub}", k, sub)
            t0 = time.perf_counter()
            vs = {}
            for F in range(1, 98):
                hou.setFrame(F)
                g = imp.geometry()
                if F in (25, 49, 97):
                    vs[F] = g.points()[0].attribValue("v")[1]
            sec = time.perf_counter() - t0
            for F, v in vs.items():
                t = (F - 1) / 24
                rows.append({"k": k, "substeps": sub, "frame": F, "t": round(t, 4), "vy": round(v, 6),
                             "terminal": round(-G / k, 6), "exact_linear": round(-G / k * (1 - math.exp(-k * t)), 6),
                             "sec_97f": round(sec, 3)})
                print(rows[-1])
    # 終端速度が g/k にならなかったので、Substeps を増やして √(g/k) に近づくかを見る（2 秒後）
    conv = []
    for k in (1.0, 4.0):
        for sub in (1, 4, 16, 64):
            imp = build(geo, f"c{int(k)}_{sub}", k, sub)
            for F in range(1, 50):
                hou.setFrame(F)
                g = imp.geometry()
            conv.append({"k": k, "substeps": sub, "vy_2s": round(g.points()[0].attribValue("v")[1], 6),
                         "sqrt_g_over_k": round(-math.sqrt(G / k), 6), "g_over_k": round(-G / k, 6)})
            print(conv[-1])
    sop_bench.save(166, rows, {"g": G, "convergence": conv})


if __name__ == "__main__":
    main()
