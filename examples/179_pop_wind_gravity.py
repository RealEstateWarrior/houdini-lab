# -*- coding: utf-8 -*-
"""実験179 — popwind（風 0）に重力を足すと、終端速度は √(g/k) か。Substeps で変わるか。Wind Speed は掛け算か。

1. 実験175 の粒に重力（gravity、−9.80665）を足し、風は 0（止まった空気）、Air Resistance k = 1・4。
   差の2乗に比例する抵抗なら、終端速度は √(g/k)（k = 1 で 3.1316）。Substeps 1・8 で、2 秒後の v.y を読む。
   実験166 の popdrag は、Substeps 1 で 6% 遅く、Substeps を上げると √(g/k) に近づいた。
2. 重力なし・Wind Velocity (5, 0, 0) のまま Wind Speed を 0.5・1・2 にして、4 秒後の v.x を読む。
   掛け算なら、行き着く速さは 2.5・5・10。

    hython examples/179_pop_wind_gravity.py
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


def build(geo, tag, k, sub, windx, speed, gravity):
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
    wind = dop.createNode("popwind", "wind")
    wind.parm("windx").set(windx)
    wind.parm("windspeed").set(speed)
    wind.parm("airresist").set(k)
    solver.setInput(0, obj)
    solver.setInput(1, src)
    solver.setInput(2, wind)
    last = solver
    if gravity:
        grav = dop.createNode("gravity", "g")
        grav.setInput(0, solver)
        last = grav
    last.setDisplayFlag(True)
    imp = geo.createNode("dopimport", f"imp{tag}")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    return imp


def run(imp, last_frame):
    for F in range(1, last_frame + 1):
        hou.setFrame(F)
        g = imp.geometry()
    return g.points()[0].attribValue("v")


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    fall, speed_rows = [], []
    for k in (1.0, 4.0):
        for sub in (1, 8):
            t0 = time.perf_counter()
            v = run(build(geo, f"g{int(k)}_{sub}", k, sub, 0.0, 1.0, True), 49)
            fall.append({"k": k, "substeps": sub, "vy_2s": round(v[1], 6), "sqrt_g_over_k": round(-math.sqrt(G / k), 6),
                         "sec": round(time.perf_counter() - t0, 3)})
            print(fall[-1])
    for s in (0.5, 1.0, 2.0):
        v = run(build(geo, f"s{int(s * 10)}", 1.0, 1, 5.0, s, False), 97)
        speed_rows.append({"windspeed": s, "vx_4s": round(v[0], 6), "product": 5.0 * s,
                           "quad_4s": round(5.0 * s - 5.0 * s / (1 + 5.0 * s * 1.0 * 4.0), 6)})
        print(speed_rows[-1])
    sop_bench.save(179, fall, {"windspeed": speed_rows, "g": G})


if __name__ == "__main__":
    main()
