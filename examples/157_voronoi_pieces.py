# -*- coding: utf-8 -*-
"""実験157 — voronoifracture は、種の点 N 個で N 個のかけらに割るか。かけらの体積を足すと元に戻るか。

1×1×1 の箱の中に scatter で N 個の点を撒き、voronoifracture で割る。
かけらの数（name の種類）・体積の合計・いちばん小さいかけらと大きいかけら・時間を測る。
Create Interior Surfaces を切ると、切り口の面が作られず、体積が測れない（閉じない）はず。

    hython examples/157_voronoi_pieces.py
"""
import collections
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    fill = geo.createNode("isooffset", "fog")
    fill.setInput(0, box)
    rows = []
    for N in (2, 5, 10, 50, 200):
        sc = geo.createNode("scatter::2.0", f"pts{N}")
        sc.setInput(0, fill)
        sc.parm("forcetotal").set(1)
        sc.parm("npts").set(N)
        sc.parm("seed").set(3)
        for interior in (1, 0):
            vf = geo.createNode("voronoifracture::2.0", f"vf{N}_{interior}")
            vf.setInput(0, box)
            vf.setInput(1, sc)
            vf.parm("createinteriorsurfaces").set(interior)
            t0 = time.perf_counter()
            g = vf.geometry()
            sec = time.perf_counter() - t0
            names = g.primStringAttribValues("name") if g.findPrimAttrib("name") else []
            groups = collections.defaultdict(list)
            for pr, nm in zip(g.prims(), names):
                groups[nm].append(pr)
            vols = []
            if interior:
                meas = geo.createNode("measure", f"m{N}")
                meas.setInput(0, vf)
                meas.parm("measure").set("volume")
                meas.parm("attribname").set("vol")
                mg = meas.geometry()
                per = collections.defaultdict(float)
                for pr, nm in zip(mg.prims(), mg.primStringAttribValues("name")):
                    per[nm] += pr.attribValue("vol")
                vols = sorted(per.values())
            rows.append({"N": N, "interior": interior, "seeds": len(sc.geometry().points()), "pieces": len(groups),
                         "prims": len(g.prims()), "points": len(g.points()),
                         "volume": round(sum(vols), 6) if vols else None,
                         "vmin": round(vols[0], 6) if vols else None, "vmax": round(vols[-1], 6) if vols else None,
                         "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(157, rows)


if __name__ == "__main__":
    main()
