# -*- coding: utf-8 -*-
"""実験154 — polyfill の Fill Mode ごとに、穴は何枚の面で塞がるか。塞いだ面積は正多角形の式どおりか。

蓋のない tube（半径 1、高さ 1、Columns = n）の上下の穴を polyfill で塞ぐ。
穴は正 n 角形なので、塞いだ面積は2つ合わせて n·sin(2π/n)（1つ (n/2)·sin(2π/n)）のはず。
Fill Mode（Single Polygon / Triangles / Triangle Fan / Quadrilateral Fan / Quadrilaterals / Quadrilateral Grid）
ごとに、足された面の数・点の数・何角形か・面積と、閉じた体積を測る。n は 12 と 13。

    hython examples/154_polyfill_modes.py
"""
import collections
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

MODES = ["none", "tris", "trifan", "quadfan", "quads", "gridquads"]


def main():
    geo = sop_bench.fresh()
    labels = None
    rows = []
    for n in (12, 13):
        t = geo.createNode("tube", f"t{n}")
        t.parm("type").set("poly")
        t.parm("cols").set(n)
        t.parm("height").set(1.0)
        base = t.geometry()
        p0, f0 = len(base.points()), len(base.prims())
        side = sum(p.intrinsicValue("measuredarea") for p in base.prims())
        for mode in MODES:
            f = geo.createNode("polyfill", f"f{n}_{mode}")
            f.setInput(0, t)
            f.parm("fillmode").set(mode)
            if labels is None:
                labels = dict(zip(f.parm("fillmode").parmTemplate().menuItems(), f.parm("fillmode").parmTemplate().menuLabels()))
            t0 = time.perf_counter()
            g = f.geometry()
            sec = time.perf_counter() - t0
            new = g.prims()[f0:]
            area = sum(p.intrinsicValue("measuredarea") for p in new)
            warn = " / ".join(f.warnings())
            ys = [pt.position()[1] for pr in new for pt in pr.points()]
            flat = (max(ys) - min(ys) if ys else 0.0)
            rows.append({"n": n, "mode": mode, "label": labels[mode], "added_prims": len(new),
                         "warning": warn, "cap_y_spread": round(flat, 6),
                         "added_points": len(g.points()) - p0,
                         "sides": dict(sorted(collections.Counter(p.numVertices() for p in new).items())),
                         "cap_area": round(area, 6), "want_cap": round(n * math.sin(2 * math.pi / n), 6),
                         "volume": round(sop_bench.volume(g), 6),
                         "want_volume": round(n / 2 * math.sin(2 * math.pi / n), 6),
                         "side_area": round(side, 6), "sec": round(sec, 4)})
            print(rows[-1])
    # Quadrilateral Grid の既定は Smooth（強さ 50）が入っている。切ると面積はどうなるか
    extra = []
    for smooth in (1, 0):
        f = geo.createNode("polyfill", f"gq_s{smooth}")
        f.setInput(0, geo.node("t12"))
        f.parm("fillmode").set("gridquads")
        f.parm("smoothtoggle").set(smooth)
        g = f.geometry()
        new = g.prims()[len(geo.node("t12").geometry().prims()):]
        caps = [pt.position()[1] for pr in new for pt in pr.points()]
        top = [y for y in caps if y > 0]
        extra.append({"smooth": smooth, "strength": f.parm("smoothstrength").eval(),
                      "cap_area": round(sum(p.intrinsicValue("measuredarea") for p in new), 6),
                      "top_y_min": round(min(top), 6), "top_y_max": round(max(top), 6)})
        print(extra[-1])
    sop_bench.save(154, rows, {"labels": labels, "gridquads_smooth": extra})


if __name__ == "__main__":
    main()
