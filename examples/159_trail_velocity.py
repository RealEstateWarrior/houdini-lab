# -*- coding: utf-8 -*-
"""実験159 — trail の Compute Velocity は、1秒あたりの速さか。3つの差分はどれだけ違うか。

点を x = 0.1·F²（F はフレーム番号）で動かす。速さの正しい値は dx/dt = 0.2·F·(fps)。
フレーム F での差分は
  後ろ（Backward）: (x(F) − x(F−1))·fps = 0.1·(2F − 1)·fps
  中央（Central）  : (x(F+1) − x(F−1))/2·fps = 0.2·F·fps（2次式ではちょうど正しい値）
  前（Forward）    : (x(F+1) − x(F))·fps = 0.1·(2F + 1)·fps
になるはず。fps を 24 と 30 で、Velocity Scale と Compute Acceleration も確かめる。

    hython examples/159_trail_velocity.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

MODES = ["Backward Difference", "Central Difference", "Forward Difference"]


def main():
    geo = sop_bench.fresh()
    add = geo.createNode("add", "pt")
    add.parm("points").set(1)
    add.parm("usept0").set(1)
    add.parm("pt0x").setExpression("0.1 * $F * $F")
    rows = []
    for fps in (24, 30):
        hou.setFps(fps)
        for mi, mode in enumerate(MODES):
            for scale in (1.0, 0.5):
                tr = geo.createNode("trail", f"t{fps}_{mi}_{int(scale * 10)}")
                tr.setInput(0, add)
                tr.parm("result").set("velocity")
                tr.parm("velapproximation").set(mi)
                tr.parm("velscale").set(scale)
                tr.parm("computeaccel").set(1)
                for F in (10, 20):
                    hou.setFrame(F)
                    t0 = time.perf_counter()
                    g = tr.geometry()
                    sec = time.perf_counter() - t0
                    p = g.points()[0]
                    v = p.attribValue("v")[0]
                    a = p.attribValue("accel")[0] if g.findPointAttrib("accel") else None
                    want = {0: 0.1 * (2 * F - 1), 1: 0.2 * F, 2: 0.1 * (2 * F + 1)}[mi] * fps * scale
                    rows.append({"fps": fps, "mode": mode, "scale": scale, "frame": F, "x": round(p.position()[0], 6),
                                 "v": round(v, 6), "want_v": round(want, 6), "exact_v": round(0.2 * F * fps, 6),
                                 "accel": round(a, 6) if a is not None else None, "exact_accel": round(0.2 * fps * fps, 6),
                                 "sec": round(sec, 5)})
                    print(rows[-1])
    hou.setFps(24)
    sop_bench.save(159, rows)


if __name__ == "__main__":
    main()
