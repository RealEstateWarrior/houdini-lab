# -*- coding: utf-8 -*-
"""実験185 — smooth（smooth::2.0）をかけた円は、どれだけ縮むか。縮み方は Strength と点の数でどう決まるか。

半径 1 の circle（Polygon、閉じた n 角形、n = 12・24・48・96）に smooth（Method = Uniform、Constrained Boundary なし）をかけ、
残った半径 r を測る。となりの点の平均へ寄せる平滑化なら、角 θ = 2π/n として
  1 回 λ だけ寄せる: r = 1 − λ(1 − cos θ)、N 回: r = (1 − λ(1 − cos θ))^N
  熱の広がり（連続）として扱う: r = exp(−t·(1 − cos θ))
のような形になるはず。−ln(r) ÷ (1 − cos θ) が n によらず Strength だけで決まれば、後の形に近い。
Strength（1・10・100）と Filter Quality（1・2・3）を変える。

    hython examples/185_smooth_circle.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    rows = []
    for n in (12, 24, 48, 96):
        c = geo.createNode("circle", f"c{n}")
        c.parm("type").set("poly")
        c.parm("divs").set(n)
        for strength in (1.0, 10.0, 100.0):
            for q in (1, 2, 3):
                s = geo.createNode("smooth::2.0", f"s{n}_{int(strength)}_{q}")
                s.setInput(0, c)
                s.parm("contrainedboundary").set("none")
                s.parm("method").set("uniform")
                s.parm("strength").set(strength)
                s.parm("filterquality").set(q)
                t0 = time.perf_counter()
                g = s.geometry()
                sec = time.perf_counter() - t0
                rs = [p.position().length() for p in g.points()]
                r = sum(rs) / len(rs)
                k = 1 - math.cos(2 * math.pi / n)
                rows.append({"n": n, "strength": strength, "quality": q, "r": round(r, 7), "r_spread": round(max(rs) - min(rs), 7),
                             "neg_ln_r_over_k": round(-math.log(r) / k, 5) if r > 0 else None, "sec": round(sec, 4)})
                print(rows[-1])
    sop_bench.save(185, rows)


if __name__ == "__main__":
    main()
