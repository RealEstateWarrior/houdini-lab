# -*- coding: utf-8 -*-
"""実験129 — measure の曲率は、球と円柱の式に合うか。

半径 r の球: ガウス曲率 1/r²、平均曲率 1/r、曲がり具合（curvedness）1/r
半径 r の円柱の側面: ガウス曲率 0、平均曲率 1/(2r)、curvedness 1/(r√2)
（平均曲率 = 2つの主曲率の平均、curvedness = √((k1² + k2²)/2)）

球は極のまわりの網がゆがむので、|y| < 0.8r の点だけを数える。円柱は上下の縁を除く。
網の細かさを変えて、式に近づくかも見る。

    hython examples/129_curvature.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


PER_AREA = True     # False にすると既定のまま（面積で割らない・大きさで正規化する）


def curv(parent, src, kind, mask):
    m = parent.createNode("measure::2.0", "k_" + kind)
    m.setInput(0, src)
    m.parm("grouptype").set("points")
    m.parm("measure").set("curvature")
    m.parm("curvaturetype").set(kind)
    m.parm("attribname").set("k")
    if PER_AREA:
        m.parm("divideelementarea").set(True)
        m.parm("scalenormalize").set(False)
    g = m.geometry()
    vals = g.pointFloatAttribValues("k")
    pos = g.pointFloatAttribValues("P")
    pick = [v for i, v in enumerate(vals) if mask(pos[3 * i:3 * i + 3])]
    m.destroy()
    n = len(pick)
    mean = sum(pick) / n
    return {"n": n, "mean": round(mean, 6), "min": round(min(pick), 6), "max": round(max(pick), 6)}


def main():
    global PER_AREA
    out = {}
    for per_area in (False, True):
        PER_AREA = per_area
        out["per_area" if per_area else "default"] = run()
    path = os.path.join(sop_bench.OUT, "129_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


def run():
    geo = sop_bench.fresh()
    rows = []
    for r in (0.5, 1.0, 2.0):
        for res in (24, 96):
            sp = geo.createNode("sphere", f"sp_{r}_{res}".replace(".", "_"))
            sp.parm("type").set("polymesh")
            sp.parmTuple("rad").set((r, r, r))
            sp.parm("rows").set(res)
            sp.parm("cols").set(res * 2)
            mask = (lambda p, r=r: abs(p[1]) < 0.8 * r)
            t0 = time.perf_counter()
            row = {"shape": "sphere", "r": r, "res": res,
                   "gaussian": curv(geo, sp, "gaussian", mask),
                   "mean": curv(geo, sp, "mean", mask),
                   "curvedness": curv(geo, sp, "curvedness", mask),
                   "want": {"gaussian": 1 / r ** 2, "mean": 1 / r, "curvedness": 1 / r},
                   "sec": round(time.perf_counter() - t0, 4)}
            rows.append(row)
            print(row)
    for r in (0.5, 1.0):
        for res in (24, 96):
            tb = geo.createNode("tube", f"tb_{r}_{res}".replace(".", "_"))
            tb.parm("type").set("poly")
            tb.parmTuple("rad").set((r, r))
            tb.parm("height").set(4.0)
            tb.parm("rows").set(17)
            tb.parm("cols").set(res)
            mask = (lambda p: abs(p[1]) < 1.5)
            row = {"shape": "tube", "r": r, "res": res,
                   "gaussian": curv(geo, tb, "gaussian", mask),
                   "mean": curv(geo, tb, "mean", mask),
                   "curvedness": curv(geo, tb, "curvedness", mask),
                   "want": {"gaussian": 0.0, "mean": 1 / (2 * r), "curvedness": 1 / (r * math.sqrt(2))}}
            rows.append(row)
            print(row)
    return rows


if __name__ == "__main__":
    main()
