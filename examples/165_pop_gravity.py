# -*- coding: utf-8 -*-
"""実験165 — POP の粒は、重力で y = −½·g·t² どおりに落ちるか。Substeps で誤差はどう変わるか。

原点の 1 点から、最初のフレームだけ 1 粒を生む（初速 0）。popsolver の後ろに gravity（−9.80665）。
フレーム 1 から 25（24 fps で 1 秒後）まで、粒の y と v.y を読む。
1 ステップ dt ごとに「速さを足してから位置を進める」（前進オイラーの一種）なら、
n ステップ後の y は −g·dt²·n(n+1)/2、「位置を進めてから速さを足す」なら −g·dt²·n(n−1)/2 になる。
DOP Network の Substeps を 1・2・4・8 と変えて、どちらに合うか、正しい値 −½·g·t² にどれだけ近づくかを見る。

    hython examples/165_pop_gravity.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

G = 9.80665


def build(geo, sub):
    pt = geo.createNode("add", f"pt{sub}")
    pt.parm("points").set(1)
    pt.parm("usept0").set(1)
    dop = geo.createNode("dopnet", f"dop{sub}")
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
    solver.setInput(0, obj)
    solver.setInput(1, src)
    grav = dop.createNode("gravity", "g")
    grav.setInput(0, solver)
    grav.setDisplayFlag(True)
    imp = geo.createNode("dopimport", f"imp{sub}")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    return imp


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    dt = 1 / 24
    rows = []
    for sub in (1, 2, 4, 8):
        imp = build(geo, sub)
        t0 = time.perf_counter()
        for F in range(1, 26):
            hou.setFrame(F)
            g = imp.geometry()
        sec = time.perf_counter() - t0
        for F in (2, 13, 25):
            hou.setFrame(F)
            g = imp.geometry()
            p = g.points()[0]
            n = (F - 1) * sub           # 進んだステップの数
            h = dt / sub
            t = (F - 1) * dt
            rows.append({"substeps": sub, "frame": F, "t": round(t, 6), "count": len(g.points()),
                         "y": round(p.position()[1], 6), "vy": round(p.attribValue("v")[1], 6),
                         "exact_y": round(-0.5 * G * t * t, 6), "exact_vy": round(-G * t, 6),
                         "semi_implicit": round(-G * h * h * n * (n + 1) / 2, 6),
                         "explicit": round(-G * h * h * n * (n - 1) / 2, 6), "sec_25f": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(165, rows, {"g": G})


if __name__ == "__main__":
    main()
