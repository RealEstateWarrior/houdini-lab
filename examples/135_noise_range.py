# -*- coding: utf-8 -*-
"""実験135 — VEX のノイズは、どんな範囲の値を出すのか。

noise()・snoise()・onoise()・anoise()・xnoise()・flownoise()・curlnoise() を、
約100万点（100×100×100 の格子、間隔 0.37）で呼び、最小・最大・平均・標準偏差を数える。
「0〜1 に収まる」「−1〜1」などの思い込みを、実測で置き換える。
ベクトルを返すものは x 成分を数える。

    hython examples/135_noise_range.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

FUNCS = {
    "noise(P)": "f@n = noise(p);",
    "snoise(P)": "f@n = snoise(p);",
    "onoise(P)": "f@n = onoise(p);",
    "anoise(P)": "f@n = anoise(p);",
    "xnoise(P)": "f@n = xnoise(p);",
    "flownoise(P, 0)": "f@n = flownoise(p, 0);",
    "curlnoise(P).x": "f@n = curlnoise(p).x;",
    "vector noise(P).x": "vector v = noise(p); f@n = v.x;",
    "rand(P)": "f@n = rand(p);",
}


def main():
    geo = sop_bench.fresh()
    pts = geo.createNode("attribwrangle", "pts")
    pts.parm("class").set(0)
    pts.parm("snippet").set(
        "for (int i = 0; i < 100; i++) for (int j = 0; j < 100; j++) for (int k = 0; k < 100; k++)\n"
        "  addpoint(0, set(i, j, k) * 0.37 + {0.123, 0.456, 0.789});")
    rows = []
    for name, body in FUNCS.items():
        wr = geo.createNode("attribwrangle", "w")
        wr.setInput(0, pts)
        wr.parm("snippet").set("vector p = @P;\n" + body)
        t0 = time.perf_counter()
        vals = wr.geometry().pointFloatAttribValues("n")
        sec = time.perf_counter() - t0
        n = len(vals)
        mean = sum(vals) / n
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
        inside01 = sum(1 for v in vals if 0 <= v <= 1) / n
        rows.append({"func": name, "n": n, "min": round(min(vals), 5), "max": round(max(vals), 5),
                     "mean": round(mean, 5), "sd": round(sd, 5), "inside01": round(inside01, 5),
                     "sec": round(sec, 3)})
        print(rows[-1])
        wr.destroy()
    path = os.path.join(sop_bench.OUT, "135_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
