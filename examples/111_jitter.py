# -*- coding: utf-8 -*-
"""実験111 — pointjitter の Scale は、どれだけ動かす値なのか。

約10万点を jitter して、元の位置からの動きを軸ごとに数える。
Scale が「動く幅」なら、動きは −s/2〜+s/2 の一様で、分散は s²/12 になるはず。
「半径」なら −s〜+s で、分散は s²/3。箱の中に散るのか、球の中に散るのかは、
動いた距離の最大が s/2（軸）と s/2·√3（箱の角）のどちらに届くかで分かる。

    hython examples/111_jitter.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def moves(src, out):
    a = src.geometry().pointFloatAttribValues("P")
    b = out.geometry().pointFloatAttribValues("P")
    d = [y - x for x, y in zip(a, b)]
    return [d[i::3] for i in range(3)]


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "g")
    grid.parm("rows").set(316)
    grid.parm("cols").set(316)
    rows = []
    cases = [("s1", {"scale": 1.0}), ("s0.1", {"scale": 0.1}), ("s2", {"scale": 2.0}),
             ("axis_1_0_0.5", {"scale": 1.0, "axisscale": (1.0, 0.0, 0.5)}),
             ("seed2", {"scale": 1.0, "seed": 2.0})]
    base = None
    for name, setup in cases:
        node = geo.createNode("pointjitter", name.replace(".", "_"))
        node.setInput(0, grid)
        for key, value in setup.items():
            if isinstance(value, tuple):
                node.parmTuple(key).set(value)
            else:
                node.parm(key).set(value)
        t0 = time.perf_counter()
        node.geometry()
        sec = time.perf_counter() - t0
        axes = moves(grid, node)
        n = len(axes[0])
        lengths = [math.sqrt(x * x + y * y + z * z) for x, y, z in zip(*axes)]
        row = {"case": name, "n": n, "sec": round(sec, 4)}
        for k, arr in zip("xyz", axes):
            mean = sum(arr) / n
            row[k] = {"mean": round(mean, 6), "var": round(sum((v - mean) ** 2 for v in arr) / n, 6),
                      "min": round(min(arr), 6), "max": round(max(arr), 6)}
        row["len_max"] = round(max(lengths), 6)
        if name == "s1":
            base = axes
        if name == "seed2":
            row["same_as_seed1"] = round(sum(1 for a, b in zip(base[0], axes[0])
                                             if abs(a - b) < 1e-9) / n, 6)
        rows.append(row)
        print(row)
    path = os.path.join(sop_bench.OUT, "111_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
