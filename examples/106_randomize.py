# -*- coding: utf-8 -*-
"""実験106 — attribrandomize の乱数は、名前どおりの分布になっているか。

約10万点に1つずつ値を入れ、平均・分散・最小・最大・割合を数えて、
分布の式から出る値と突き合わせる。

- 一様（0〜1）: 平均 0.5、分散 1/12
- 一様（2〜5）: 平均 3.5、分散 0.75
- 正規（中央0、Scale 1 と 2）: Scale が標準偏差なのかを確かめる
- 一様の整数（0〜9、刻み1）: 端の9が入るか。1つあたり10%か
- 2つの値（確率0.3）: B の割合が0.3か
- 球の中（3成分）: 長さの平均は 3/4、最大は1以下
- 向き（3成分）: 長さは全部1、平均の向きは0

    hython examples/106_randomize.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

SIDE = 316          # 316×316 = 99,856 点


def stats(values):
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    return {"n": n, "mean": mean, "var": var, "sd": math.sqrt(var),
            "min": min(values), "max": max(values)}


def run(geo, grid, name, dims, setup):
    node = geo.createNode("attribrandomize", name)
    node.setInput(0, grid)
    node.parm("name").set("val")
    node.parm("dimensions").set(dims)
    for key, value in setup.items():
        parm = node.parmTuple(key)
        if isinstance(value, (list, tuple)):
            parm.set(value)
        else:
            node.parm(key).set(value) if node.parm(key) else parm.set((value,) * len(parm))
    t0 = time.perf_counter()
    out = node.geometry()
    raw = out.pointFloatAttribValues("val")
    sec = time.perf_counter() - t0
    return raw, sec


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "g")
    grid.parm("rows").set(SIDE)
    grid.parm("cols").set(SIDE)
    rows = []

    scalar_cases = [
        ("uniform_0_1", {"distribution": "uniform", "min": 0.0, "max": 1.0},
         {"mean": 0.5, "var": 1 / 12}),
        ("uniform_2_5", {"distribution": "uniform", "min": 2.0, "max": 5.0},
         {"mean": 3.5, "var": 0.75}),
        ("normal_s1", {"distribution": "normal", "median": 0.0, "stddev": 1.0},
         {"mean": 0.0, "var": 1.0}),
        ("normal_s2", {"distribution": "normal", "median": 0.0, "stddev": 2.0},
         {"mean": 0.0, "var": 4.0}),
        ("normal_m3_s05", {"distribution": "normal", "median": 3.0, "stddev": 0.5},
         {"mean": 3.0, "var": 0.25}),
    ]
    for name, setup, want in scalar_cases:
        raw, sec = run(geo, grid, name, 1, setup)
        st = stats(raw)
        rows.append({"case": name, **{k: round(v, 6) if isinstance(v, float) else v
                                      for k, v in st.items()},
                     "want_mean": round(want["mean"], 6), "want_var": round(want["var"], 6),
                     "sec": round(sec, 4)})
        print(rows[-1])

    # 整数の一様: 0〜9 刻み1。端の9が入るか
    raw, sec = run(geo, grid, "discrete", 1, {"distribution": "uniformdiscrete",
                                               "mindiscrete": 0.0, "maxdiscrete": 9.0,
                                               "stepsize": 1.0})
    hist = {}
    for v in raw:
        hist[round(v, 6)] = hist.get(round(v, 6), 0) + 1
    n = len(raw)
    discrete = {"values": sorted(hist), "share": {str(k): round(hist[k] / n, 4)
                                                  for k in sorted(hist)},
                "sec": round(sec, 4)}
    print("discrete", discrete)

    # 2つの値
    raw, sec = run(geo, grid, "bern", 1, {"distribution": "bernoulli",
                                           "valuea": 0.0, "valueb": 1.0,
                                           "probvalueb": 0.3})
    bern = {"share_b": round(sum(1 for v in raw if v > 0.5) / len(raw), 5),
            "other": sorted({round(v, 6) for v in raw}), "sec": round(sec, 4)}
    print("bern", bern)

    # 3成分: 球の中と向き
    vec = {}
    for name, dist in (("ball", "uniformball"), ("orient", "uniformorient")):
        raw, sec = run(geo, grid, name, 3, {"distribution": dist})
        lens = [math.sqrt(raw[i] ** 2 + raw[i + 1] ** 2 + raw[i + 2] ** 2)
                for i in range(0, len(raw), 3)]
        m = len(lens)
        avg = [sum(raw[i::3]) / m for i in range(3)]
        vec[name] = {"len_mean": round(sum(lens) / m, 6), "len_min": round(min(lens), 6),
                     "len_max": round(max(lens), 6),
                     "avg": [round(a, 6) for a in avg], "sec": round(sec, 4)}
        print(name, vec[name])

    # 種を変えると違う値になるか。同じ種なら同じか
    a, _ = run(geo, grid, "seed_a", 1, {"distribution": "uniform", "seed": 0.0})
    b, _ = run(geo, grid, "seed_b", 1, {"distribution": "uniform", "seed": 0.0})
    c, _ = run(geo, grid, "seed_c", 1, {"distribution": "uniform", "seed": 1.0})
    seed = {"same_seed_equal": a == b,
            "diff_seed_equal_share": round(sum(1 for x, y in zip(a, c) if x == y) / len(a), 6)}
    print("seed", seed)

    path = os.path.join(sop_bench.OUT, "106_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"points": SIDE * SIDE, "rows": rows, "discrete": discrete,
                   "bern": bern, "vec": vec, "seed": seed},
                  fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
