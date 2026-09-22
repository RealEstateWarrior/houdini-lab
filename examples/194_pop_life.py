# -*- coding: utf-8 -*-
"""実験194 — Life Expectancy の粒は何フレーム生きるか。Substeps と Life の値でどう変わるか。

実験193 と同じく、Constant Birth Rate 2400（24 fps で 1 フレームちょうど 100 粒）で粒を生み続け、
Life Expectancy（ばらつき 0）を 0.5・0.52・0.54 秒、DOP Network の Substeps を 1・2・4 にして、止まったときの粒の数を読む。
粒が k フレーム生きるなら、数は 100 × k で止まる。実験193 では 0.5 秒（12 フレーム）の粒が 11 フレームで消えた。

    hython examples/194_pop_life.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def build(geo, tag, rate, life, sub=1):
    grid = geo.createNode("grid", f"g{tag}")
    dop = geo.createNode("dopnet", f"dop{tag}")
    dop.parm("substep").set(sub)
    obj = dop.createNode("popobject", "p")
    solver = dop.createNode("popsolver::2.0", "solver")
    src = dop.createNode("popsource", "src")
    src.parm("emittype").set("surface")
    src.parm("soppath").set(grid.path())
    src.parm("constantactivate").set(1)
    src.parm("constantrate").set(rate)
    src.parm("impulseactiveate").set(0)
    src.parm("life").set(life)
    src.parm("lifevar").set(0.0)
    solver.setInput(0, obj)
    solver.setInput(1, src)
    solver.setDisplayFlag(True)
    imp = geo.createNode("dopimport", f"imp{tag}")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    return imp


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    rows, tracks = [], {}
    for life in (0.5, 0.52, 0.54):
      for sub in (1, 2, 4):
        rate = 2400.0
        imp = build(geo, f"{int(life * 100)}_{sub}", rate, life, sub)
        t0 = time.perf_counter()
        counts = []
        for F in range(1, 50):
            hou.setFrame(F)
            g = imp.geometry()
            counts.append(len(g.points()) if g else 0)
        sec = time.perf_counter() - t0
        per = [counts[0]] + [counts[i] - counts[i - 1] for i in range(1, len(counts))]
        tracks[f"l{life:g}_s{sub}"] = counts
        rows.append({"rate": rate, "life": life, "substeps": sub, "settled": counts[-1], "frames_alive": counts[-1] / 100,
                     "frame1": counts[0], "frame24": counts[23], "frame25": counts[24], "frame49": counts[48],
                     "per_frame_first": per[:6], "per_frame_set": sorted(set(per[1:24])), "sec_49f": round(sec, 3)})
        print(rows[-1])
    sop_bench.save(194, rows, {"tracks": tracks})


if __name__ == "__main__":
    main()
