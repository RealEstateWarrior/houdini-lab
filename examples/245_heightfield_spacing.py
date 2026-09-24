# -*- coding: utf-8 -*-
"""実験245 — 地形の升目（heightfield の Grid Spacing）を細かくすると、削る（heightfield_erode）時間と見た目はどう変わるか。

制作の問い: 実験227 で、1000 m 四方の地形（升 2 m）を 20 フレーム削るのは 1 秒だった。升を細かくすれば谷筋も細かくなるはずだが、
時間はどれだけ増えるのか。升を倍に細かくすると、刻まれる谷の細かさも倍になるのか。

  heightfield（1000 m 四方）の Grid Spacing を 4・2（実験227）・1 m にし、heightfield_noise（Element Size 300）で山を作って、
  heightfield_erode（::3.0）で 20 フレーム削る。1 通りずつ、ほかの処理は回さない。
  升を細かくしても時間が変わらなかったので、升 1 m で Erosion Feature Size（既定 10 m）を 5・2.5 m にしたものも回す。
  測るもの: 削る時間、升の数、斜面の傾きの平均、谷筋の多さ（高さの 2 階微分＝くぼみの強さが大きい升の割合）。
  陰影図（真ん中の 250 m 四方）は、同じ大きさの画にそろえて並べる。

    hython examples/245_heightfield_spacing.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
SPACINGS = (4.0, 2.0, 1.0)
# 升を細かくしても時間が変わらなかったので、Erosion Feature Size（既定 10 m）も変える（升 1 m で）
FEATURES = (10.0, 5.0, 2.5)
FRAMES = 20


def main():
    import hou
    import numpy as np
    import hou_tools
    import sop_bench
    geo = sop_bench.fresh()
    hf = geo.createNode("heightfield", "ground")
    noise = geo.createNode("heightfield_noise", "mountains")
    noise.setFirstInput(hf)
    noise.parm("elementsize").set(300)
    erode = geo.createNode("heightfield_erode::3.0", "erode")
    erode.setFirstInput(noise)
    erode.parm("freezeframe").set(FRAMES)
    rows = []
    for sp, fs in [(sp, 10.0) for sp in SPACINGS] + [(1.0, fs) for fs in FEATURES[1:]]:
        hf.parm("gridspacing").set(sp)
        erode.parm("erosionscale").set(fs)
        noise.cook(force=True)
        hou.setFrame(FRAMES)
        t0 = time.perf_counter()
        erode.cook(force=True)
        sec = time.perf_counter() - t0
        g = erode.geometry()
        vol = [p for p in g.prims() if p.attribValue("name") == "height"][0]
        rx, ry, _ = vol.resolution()
        h = np.array(vol.allVoxels()).reshape(ry, rx)
        gy, gx = np.gradient(h, sp)
        slope = np.degrees(np.arctan(np.hypot(gx, gy)))
        lap = (np.roll(h, 1, 0) + np.roll(h, -1, 0) + np.roll(h, 1, 1) + np.roll(h, -1, 1) - 4 * h) / (sp * sp)
        gully = float((lap[2:-2, 2:-2] > 0.05).mean())       # くぼみ（谷）の強い升の割合
        np.save(os.path.join(OUT, f"245_h_{sp:g}_{fs:g}.npy"), h)
        rows.append({"case": f"s{sp:g}_f{fs:g}", "spacing": sp, "feature_size": fs, "cells": [rx, ry], "sec": round(sec, 2),
                     "slope_mean": round(float(slope.mean()), 3), "gully_share": round(gully, 4)})
        print(rows[-1], flush=True)
    hf.parm("gridspacing").set(2)
    erode.parm("erosionscale").set(10)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "245_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "245_graph.json"), title="実験245")
    sop_bench.save(245, rows, {"frames": FRAMES})


if __name__ == "__main__":
    main()
