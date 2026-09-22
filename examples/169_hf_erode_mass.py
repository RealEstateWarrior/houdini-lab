# -*- coding: utf-8 -*-
"""実験169 — heightfield_erode は土の量（高さの合計）を保つか。削れた分はどこへ行くか。

1000 × 1000 の heightfield（Grid Spacing 8、125 × 125 の升）に heightfield_noise（Amplitude 500）で山を作り、
heightfield_erode（既定のまま）をフレーム 1 から順に進める。
フレームごとに、height の合計と、作られる層（debris・sediment・water など）の合計を升の値から数え、
「height + 積もった層」が最初の height の合計と同じか、を見る。

    hython examples/169_hf_erode_mass.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def layers(node):
    out = {}
    for pr in node.geometry().prims():
        name = pr.attribValue("name")
        vals = pr.allVoxels()
        out[name] = (sum(vals), min(vals), max(vals))
    return out


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    hf = geo.createNode("heightfield", "hf")
    hf.parm("gridspacing").set(8.0)
    noise = geo.createNode("heightfield_noise", "noise")
    noise.setInput(0, hf)
    noise.parm("combine").set("replace")
    noise.parm("amp").set(500.0)
    er = geo.createNode("heightfield_erode::3.0", "erode")
    er.setInput(0, noise)
    er.parm("dofreeze").set(0)
    hou.setFrame(1)
    base = layers(noise)["height"]
    rows = []
    t0 = time.perf_counter()
    for F in range(1, 41):
        hou.setFrame(F)
        L = layers(er)
        if F in (1, 2, 5, 10, 20, 40):
            row = {"frame": F, "elapsed": round(time.perf_counter() - t0, 2),
                   "height_sum": round(L["height"][0], 1), "height_min": round(L["height"][1], 2),
                   "height_max": round(L["height"][2], 2)}
            for name in sorted(L):
                if name != "height":
                    row[name + "_sum"] = round(L[name][0], 2)
            rows.append(row)
            print(row)
    sop_bench.save(169, rows, {"base_sum": round(base[0], 1), "base_min": round(base[1], 2), "base_max": round(base[2], 2),
                               "cells": 125 * 125, "cell_area": 64.0})


if __name__ == "__main__":
    main()
