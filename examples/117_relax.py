# -*- coding: utf-8 -*-
"""実験117 — relax は、点どうしをどこまで離すのか。

1×1 の板に点を散らし、pscale を持たせて relax（Point Relax）にかける。
pscale が「半径」なら、重なりが解けたとき点どうしの距離は 2×pscale 以上になるはず。
点の数と pscale の組み合わせで、最も近い点までの距離（最小・平均）を、
relax の前後で比べる。

板の面積を点で割ると、1点あたりの広さ 1/n。六角形に詰めたときの間隔は
√(2/(√3·n))。pscale をこの半分より大きくすると、全部は収まらない。

    hython examples/117_relax.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def nearest(node):
    """点ごとに一番近い点までの距離（最小・平均）。VEX の nearpoints で出す。"""
    parent = node.parent()
    wr = parent.createNode("attribwrangle", "nn")
    wr.setInput(0, node)
    wr.parm("snippet").set('int n[] = nearpoints(0, @P, 1e9, 2);\n'
                           'f@nn = distance(@P, point(0, "P", n[1]));')
    vals = wr.geometry().pointFloatAttribValues("nn")
    xs = wr.geometry().pointFloatAttribValues("P")[0::3]
    zs = wr.geometry().pointFloatAttribValues("P")[2::3]
    wr.destroy()
    return {"min": round(min(vals), 6), "mean": round(sum(vals) / len(vals), 6),
            "out_of_plate": sum(1 for x, z in zip(xs, zs) if abs(x) > 0.5 or abs(z) > 0.5)}


def main():
    geo = sop_bench.fresh()
    plate = geo.createNode("grid", "plate")
    plate.parmTuple("size").set((1.0, 1.0))
    rows = []
    for n in (500, 2000):
        hexgap = math.sqrt(2 / (math.sqrt(3) * n))
        sc = geo.createNode("scatter::2.0", f"sc{n}")
        sc.setInput(0, plate)
        sc.parm("npts").set(n)
        sc.parm("relaxpoints").set(False)
        before = nearest(sc)
        for frac in (0.25, 0.4, 0.5):
            r = hexgap * frac
            ps = geo.createNode("attribwrangle", f"ps{n}_{int(frac * 100)}")
            ps.setInput(0, sc)
            ps.parm("snippet").set(f"f@pscale = {r};")
            for iters in (10, 50):
                rl = geo.createNode("relax", f"rl{n}_{int(frac * 100)}_{iters}")
                rl.setInput(0, ps)
                rl.setInput(1, plate)
                rl.parm("maxiterations").set(iters)
                t0 = time.perf_counter()
                rl.geometry()
                sec = time.perf_counter() - t0
                after = nearest(rl)
                rows.append({"n": n, "hexgap": round(hexgap, 6), "pscale": round(r, 6),
                             "frac": frac, "iters": iters, "before": before, "after": after,
                             "min_over_2r": round(after["min"] / (2 * r), 4),
                             "sec": round(sec, 4)})
                print(rows[-1])
    path = os.path.join(sop_bench.OUT, "117_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
