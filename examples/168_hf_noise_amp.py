# -*- coding: utf-8 -*-
"""実験168 — heightfield_noise の Amplitude は、高さの幅（最高 − 最低）そのものか。Center Noise で平均はどこに来るか。

1000 × 1000 の heightfield（Grid Spacing 4 → 250 × 250 の升）に heightfield_noise（Combine = Replace）をかけ、
height の最小・最大・平均・標準偏差を升の値から数える。
Amplitude（100・500・1000）、Center Noise の入切、Fractal Type（None と既定の hmfT）を変える。
Amplitude が「高さの幅」なら、最高 − 最低 は Amplitude の近くに来るはず。

    hython examples/168_hf_noise_amp.py
"""
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def heights(node):
    g = node.geometry()
    for pr in g.prims():
        if pr.attribValue("name") == "height":
            return list(pr.allVoxels())
    return []


def main():
    geo = sop_bench.fresh()
    hf = geo.createNode("heightfield", "hf")
    hf.parm("gridspacing").set(4.0)
    rows = []
    for fractal in ("none", "hmfT"):
        for center in (1, 0):
            for amp in (100.0, 500.0, 1000.0):
                n = geo.createNode("heightfield_noise", f"n_{fractal}_{center}_{int(amp)}")
                n.setInput(0, hf)
                n.parm("combine").set("replace")
                n.parm("fractal").set(fractal)
                n.parm("centernoise").set(center)
                n.parm("amp").set(amp)
                t0 = time.perf_counter()
                h = heights(n)
                sec = time.perf_counter() - t0
                lo, hi = min(h), max(h)
                rows.append({"fractal": fractal, "center": center, "amp": amp, "cells": len(h),
                             "min": round(lo, 3), "max": round(hi, 3), "range": round(hi - lo, 3),
                             "range_over_amp": round((hi - lo) / amp, 4), "mean": round(statistics.fmean(h), 3),
                             "sd_over_amp": round(statistics.pstdev(h) / amp, 4), "sec": round(sec, 3)})
                print(rows[-1])
    sop_bench.save(168, rows)


if __name__ == "__main__":
    main()
