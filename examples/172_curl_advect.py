# -*- coding: utf-8 -*-
"""実験172 — curlnoise で流した粒は、まわりの粒の混み具合を保つか。ふつうのノイズで流すと固まるか。

1 × 1 × 1 の立方体に一様に 20,000 粒を撒き、各粒を v = F(P·2) で 60 ステップ（1 ステップ 0.02）動かす。
F は curlnoise と、vector(noise) − 0.5（ふつうのノイズ。平均が 0 になるよう 0.5 を引く）。
混み具合は「半径 0.05 の中にいる他の粒の数」で測る（撒いた直後なら平均 約 10.5）。
全体の形が変わる影響を避けるため、動かしたあとも他の粒に囲まれている、最初に中心寄り（|x|,|y|,|z| < 0.3）にいた粒だけで比べる。
湧き出しのない流れなら、混み具合の平均も、ばらつきも、撒いた直後と同じくらいのままのはず。

（最初は「升に分けて数える」方法で測ったが、粒の群れ全体の形が変わるだけで空の升が増え、混み具合と区別できなかったのでやめた。）

    hython examples/172_curl_advect.py
"""
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

COUNT = r'''
int near[] = pcfind(0, "P", @P, 0.05, 200);
i@nb = len(near) - 1;
'''


def stats_of(node, inner):
    g = node.geometry()
    nb = g.pointIntAttribValues("nb")
    vals = [nb[i] for i in inner]
    return round(statistics.fmean(vals), 3), round(statistics.pstdev(vals) / statistics.fmean(vals), 4), max(vals), min(vals)


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    fog = geo.createNode("isooffset", "fog")
    fog.setInput(0, box)
    sc = geo.createNode("scatter::2.0", "pts")
    sc.setInput(0, fog)
    sc.parm("forcetotal").set(1)
    sc.parm("npts").set(20000)
    sc.parm("relaxpoints").set(0)
    start = [p.position() for p in sc.geometry().points()]
    inner = [i for i, p in enumerate(start) if max(abs(p[0]), abs(p[1]), abs(p[2])) < 0.3]
    c0 = geo.createNode("attribwrangle", "count0")
    c0.setInput(0, sc)
    c0.parm("snippet").set(COUNT)
    m, cv, mx, mn = stats_of(c0, inner)
    rows = [{"kind": "撒いた直後", "mean_nb": m, "cv": cv, "max": mx, "min": mn, "inner": len(inner),
             "expect": round(20000 * 4 / 3 * math.pi * 0.05 ** 3, 2), "moved": 0.0, "sec": 0.0}]
    print(rows[-1])
    for kind, expr in (("curlnoise", "curlnoise(@P * 2)"), ("noise（ふつう）", "vector(noise(@P * 2)) - 0.5")):
        w = geo.createNode("attribwrangle", "adv_" + ("curl" if kind == "curlnoise" else "noise"))
        w.setInput(0, sc)
        w.parm("snippet").set("for (int i = 0; i < 60; i++) { vector v = %s; @P += v * 0.02; }" % expr)
        c = geo.createNode("attribwrangle", "count_" + w.name())
        c.setInput(0, w)
        c.parm("snippet").set(COUNT)
        t0 = time.perf_counter()
        m, cv, mx, mn = stats_of(c, inner)
        sec = time.perf_counter() - t0
        moved = statistics.fmean((a.position() - b).length() for a, b in zip(w.geometry().points(), start))
        rows.append({"kind": kind, "mean_nb": m, "cv": cv, "max": mx, "min": mn, "inner": len(inner),
                     "expect": rows[0]["expect"], "moved": round(moved, 4), "sec": round(sec, 3)})
        print(rows[-1])
    sop_bench.save(172, rows)


if __name__ == "__main__":
    main()
