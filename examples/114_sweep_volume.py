# -*- coding: utf-8 -*-
"""実験114 — sweep で太さを付けた管の体積は「断面積 × 長さ」になるか。

Round Tube の断面は、円そのものではなく k 角形（Columns = k）。
半径 a の正 k 角形の面積は A = (k/2)·a²·sin(2π/k)。
まっすぐな線に沿わせれば、体積は A × L ちょうどのはず。
曲がった線（実験105 のらせん）に沿わせると、曲がり角で断面が重なったり開いたりするので、
A × （折れ線の長さ）からどれだけずれるかを測る。端は Single Polygon でふさいで閉じる。

    hython examples/114_sweep_volume.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

A = 0.1          # 管の半径


def length_of(parent, node):
    meas = parent.createNode("measure", "len")
    meas.setInput(0, node)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    total = sum(p.attribValue("len") for p in meas.geometry().prims())
    meas.destroy()
    return total


def tube(geo, path, cols, stretch):
    sw = geo.createNode("sweep::2.0", "sw")
    sw.setInput(0, path)
    sw.parm("surfaceshape").set("tube")
    sw.parm("radius").set(A)
    sw.parm("cols").set(cols)
    sw.parm("endcaptype").set("single")
    sw.parm("stretcharoundturns").set(stretch)
    return sw


def main():
    rows = []
    for kind in ("line", "helix_50", "helix_200", "helix_12"):
        for cols in (8, 32):
            for stretch in (False, True):
                geo = sop_bench.fresh()
                if kind == "line":
                    path = geo.createNode("line", "path")
                    path.parm("dist").set(5.0)
                    path.parm("points").set(2)
                else:
                    divs = int(kind.split("_")[1])
                    path = geo.createNode("spiral", "path")
                    path.parm("type").set("poly")
                    path.parm("mode").set("turns")
                    path.parm("turns").set(3)
                    path.parm("height").set(3.0)
                    path.parm("radiusmode").set("endradius")
                    path.parm("startradius").set(1.0)
                    path.parm("endradius").set(1.0)
                    path.parm("divsmode").set("divsperturn")
                    path.parm("divsperturn").set(divs)
                sw = tube(geo, path, cols, stretch)
                t0 = time.perf_counter()
                vol = sop_bench.volume(sw.geometry())
                sec = time.perf_counter() - t0
                L = length_of(geo, path)
                area = cols / 2 * A * A * math.sin(2 * math.pi / cols)
                rows.append({"path": kind, "cols": cols, "stretch": stretch,
                             "length": round(L, 6), "section": round(area, 8),
                             "volume": round(vol, 6), "want": round(area * L, 6),
                             "rel": round(vol / (area * L) - 1, 6), "sec": round(sec, 4)})
                print(rows[-1])
    path = os.path.join(sop_bench.OUT, "114_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"a": A, "rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
