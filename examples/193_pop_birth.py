# -*- coding: utf-8 -*-
"""実験193 — popsource の Constant Birth Rate は「1 秒あたり」か。端数の粒はどう扱われるか。Life Expectancy で消える数は合うか。

grid の面（Emission Type = All Points ではなく Surface）から、Constant Birth Rate R（1 秒あたり）で粒を生み続ける（24 fps、Substeps 1）。
R を 10・100・1000・2400 にして、フレームごとの粒の数を読む。
1 秒あたりなら、1 フレームに R/24 粒（R = 10 なら 0.4167 粒）。端数を持ち越すなら、1 秒後にちょうど R 粒のはず。
Life Expectancy = 0.5 秒（Life Variance 0）にしたものは、0.5 秒以降は数が R × 0.5 あたりで止まるはず。

    hython examples/193_pop_birth.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def build(geo, tag, rate, life):
    grid = geo.createNode("grid", f"g{tag}")
    dop = geo.createNode("dopnet", f"dop{tag}")
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
    for rate, life in ((10.0, 100.0), (100.0, 100.0), (1000.0, 100.0), (2400.0, 100.0), (1000.0, 0.5)):
        imp = build(geo, f"{int(rate)}_{int(life * 10)}", rate, life)
        t0 = time.perf_counter()
        counts = []
        for F in range(1, 50):
            hou.setFrame(F)
            g = imp.geometry()
            counts.append(len(g.points()) if g else 0)
        sec = time.perf_counter() - t0
        per = [counts[0]] + [counts[i] - counts[i - 1] for i in range(1, len(counts))]
        tracks[f"r{int(rate)}_l{life:g}"] = counts
        rows.append({"rate": rate, "life": life, "frame1": counts[0], "frame24": counts[23], "frame25": counts[24], "frame49": counts[48],
                     "per_frame_first": per[:6], "per_frame_set": sorted(set(per[1:24])), "sec_49f": round(sec, 3)})
        print(rows[-1])
    sop_bench.save(193, rows, {"tracks": tracks})


if __name__ == "__main__":
    main()
