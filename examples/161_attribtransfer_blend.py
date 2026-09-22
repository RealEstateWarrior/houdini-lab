# -*- coding: utf-8 -*-
"""実験161 — attribtransfer の Distance Threshold と Blend Width は、値をどこまで・どんな形で運ぶか。

受け取り側: x = 0〜2 に 0.01 刻みで並んだ 201 点（f@val = 0）。
渡す側: 原点の 1 点（f@val = 1）。
Distance Threshold = d、Blend Width = b を変えて、x ごとの val を読む。
「d までは 1、d から d+b で 0 へ下がる」のか、「d−b から d で下がる」のか、下がり方は直線か、を見る。

    hython examples/161_attribtransfer_blend.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    dst = geo.createNode("attribwrangle", "dst")
    dst.parm("class").set("detail")
    dst.parm("snippet").set("for (int i = 0; i <= 200; i++) { int p = addpoint(0, set(i * 0.01, 0, 0)); setpointattrib(0, 'val', p, 0.0); }")
    src = geo.createNode("attribwrangle", "src")
    src.parm("class").set("detail")
    src.parm("snippet").set("int p = addpoint(0, {0,0,0}); setpointattrib(0, 'val', p, 1.0);")
    rows, profiles = [], {}
    for d in (0.5, 1.0):
        for b in (0.0, 0.25, 0.5):
            at = geo.createNode("attribtransfer", f"at_{int(d * 100)}_{int(b * 100)}")
            at.setInput(0, dst)
            at.setInput(1, src)
            at.parm("primitiveattribs").set(0)
            at.parm("pointattriblist").set("val")
            at.parm("thresholddist").set(d)
            at.parm("blendwidth").set(b)
            t0 = time.perf_counter()
            g = at.geometry()
            sec = time.perf_counter() - t0
            pts = sorted((p.position()[0], p.attribValue("val")) for p in g.points())
            full = [x for x, v in pts if v > 0.9999]
            some = [x for x, v in pts if v > 1e-6]
            mid = [(x, v) for x, v in pts if 1e-6 < v < 0.9999]
            key = f"d{d:g}_b{b:g}"
            profiles[key] = [(round(x, 2), round(v, 4)) for x, v in pts if x <= d + b + 0.1][::5]
            # 下がり方が直線か: 中間の点で 1 − (x − 始まり)/幅 との差
            lin_err = None
            if mid:
                x0, x1 = (full[-1] if full else 0.0), some[-1]
                lin_err = max(abs(v - (1 - (x - x0) / (x1 - x0 + 0.01))) for x, v in mid)
            rows.append({"threshold": d, "blend": b, "full_until": round(full[-1], 2) if full else None,
                         "reach_until": round(some[-1], 2) if some else None, "mid_points": len(mid),
                         "val_at_d": round(dict(pts)[min(dict(pts), key=lambda x: abs(x - d))], 4),
                         "lin_err": round(lin_err, 4) if lin_err is not None else None, "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(161, rows, {"profiles": profiles})


if __name__ == "__main__":
    main()
