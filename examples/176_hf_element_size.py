# -*- coding: utf-8 -*-
"""実験176 — heightfield_noise の「高さの幅 ÷ Amplitude」は、Element Size で変わるか。

実験168 では 1000 × 1000 の地面・Element Size 500 で、幅が Amplitude の 23%（Fractal なし）だった。
Element Size を 50・100・250・500・1000・2000 と変え（Amplitude 1000、Center Noise 入、Fractal なし と hmfT）、
幅 ÷ Amplitude と、標準偏差 ÷ Amplitude を測る。
地面が模様1つ分より広いほど、ノイズの山の高い所まで入りやすく、幅が広がるはず。

    hython examples/176_hf_element_size.py
"""
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def heights(node):
    for pr in node.geometry().prims():
        if pr.attribValue("name") == "height":
            return list(pr.allVoxels())
    return []


def main():
    geo = sop_bench.fresh()
    hf = geo.createNode("heightfield", "hf")
    hf.parm("gridspacing").set(4.0)
    rows = []
    for fractal in ("none", "hmfT"):
        for es in (50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0):
            n = geo.createNode("heightfield_noise", f"n_{fractal}_{int(es)}")
            n.setInput(0, hf)
            n.parm("combine").set("replace")
            n.parm("fractal").set(fractal)
            n.parm("amp").set(1000.0)
            n.parm("elementsize").set(es)
            t0 = time.perf_counter()
            h = heights(n)
            sec = time.perf_counter() - t0
            rows.append({"fractal": fractal, "element": es, "size_over_element": round(1000 / es, 3),
                         "range_over_amp": round((max(h) - min(h)) / 1000, 4),
                         "sd_over_amp": round(statistics.pstdev(h) / 1000, 4), "mean": round(statistics.fmean(h), 2),
                         "min": round(min(h), 1), "max": round(max(h), 1), "sec": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(176, rows)


if __name__ == "__main__":
    main()
