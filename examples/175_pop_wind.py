# -*- coding: utf-8 -*-
"""実験175 — popwind の風に、粒の速さはどう近づくか。Air Resistance は「速さの差に比例」か「差の2乗」か。

実験165 の 1 粒（初速 0、重力なし）に、popwind（Wind Velocity = (5, 0, 0)）をつなぐ。
風との速さの差 u = 5 − v.x が
  差に比例する抵抗なら  u = 5·e^(−k·t)（半分になる時間が一定）
  差の2乗に比例するなら u = 5 / (1 + 5·k·t)（半分になるまでの時間が、だんだん延びる）
になる。Air Resistance k を 0.5・1・2、Substeps 1 と 8 で、v.x をフレームごとに読む。
実験166 の popdrag（重力に対する終端速度が √(g/k) に近づいた）と見比べる。

    hython examples/175_pop_wind.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

W = 5.0


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
    wind = dop.createNode("popwind", "wind")
    wind.parm("windx").set(W)          # Wind Velocity は windx・windy・windz（Wind Speed は既定の 1）
    if wind.parm("airresist") is not None:
        wind.parm("airresist").set(k)
    solver.setInput(0, obj)
    solver.setInput(1, src)
    solver.setInput(2, wind)
    solver.setDisplayFlag(True)
    imp = geo.createNode("dopimport", f"imp{tag}")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    return imp, wind


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    rows, tracks = [], {}
    for k in (0.5, 1.0, 2.0):
        for sub in (1, 8):
            imp, wind = build(geo, f"{int(k * 10)}_{sub}", k, sub)
            t0 = time.perf_counter()
            tr = []
            for F in range(1, 74):
                hou.setFrame(F)
                g = imp.geometry()
                tr.append(round(g.points()[0].attribValue("v")[0], 6))
            sec = time.perf_counter() - t0
            tracks[f"k{k:g}_s{sub}"] = tr
            # 差が半分・1/4・1/8 になったフレーム
            marks = {}
            for frac in (0.5, 0.25, 0.125):
                hit = next((i + 1 for i, v in enumerate(tr) if W - v <= W * frac), None)
                marks[str(frac)] = hit
            t1 = 24 / 24
            rows.append({"k": k, "substeps": sub, "vx_1s": tr[24], "vx_3s": tr[72],
                         "linear_1s": round(W * (1 - math.exp(-k * (1 + 1 / (24 * sub)))), 6),
                         "quad_1s": round(W - W / (1 + W * k * (1 + 1 / (24 * sub))), 6),
                         "half_frames": marks, "sec": round(sec, 3),
                         "windparm": [wind.parm(c).eval() for c in ("windx", "windy", "windz")] + [wind.parm("windspeed").eval()]})
            print(rows[-1])
    sop_bench.save(175, rows, {"tracks": tracks, "wind": W})


if __name__ == "__main__":
    main()
