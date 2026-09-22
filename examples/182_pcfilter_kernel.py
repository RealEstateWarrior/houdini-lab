# -*- coding: utf-8 -*-
"""実験182 — pcfilter の重みは、距離に対してどんな形か。

点を2つだけ置く: 探す中心 (0,0,0) から距離 0.5 に val = 0 の点 A、距離 d に val = 1 の点 B。
中心で pcopen(半径 r = 1) → pcfilter('val') をとると、結果 a は w(d) / (w(0.5) + w(d))。
よって w(d)/w(0.5) = a / (1 − a)。d を 0.05 刻みで 0.05〜0.95 まで動かして、重みの形を読む。
（最初は A を中心 d = 0 に置いたが、どの d でも同じ値になり形が読めなかった。中心の点だけ特別に重いとみられる。）
候補: 1 − d/r（直線）、1 − (d/r)²、(1 − (d/r)²)³、など。

    hython examples/182_pcfilter_kernel.py
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    rows = []
    for i in range(1, 20):
        d = i * 0.05
        w = geo.createNode("attribwrangle", f"k{i}")
        w.parm("class").set("detail")
        w.parm("snippet").set(
            f"int a = addpoint(0, set(0, 0.5, 0)); setpointattrib(0, 'val', a, 0.0);"
            f" int b = addpoint(0, set({d}, 0, 0)); setpointattrib(0, 'val', b, 1.0);")
        f = geo.createNode("attribwrangle", f"f{i}")
        f.setInput(0, w)
        f.parm("class").set("detail")
        f.parm("snippet").set("int h = pcopen(0, 'P', {0,0,0}, 1.0, 10); f@a = pcfilter(h, 'val'); i@n = pcnumfound(h); pcclose(h);")
        g = f.geometry()
        a = g.attribValue("a")
        rows.append({"d": round(d, 3), "a": round(a, 7), "found": g.attribValue("n"),
                     "weight_ratio": round(a / (1 - a), 6) if a < 1 else None})
        print(rows[-1])
    # 3〜4 点で、候補の重み（d ÷ いちばん遠い点の距離 で正規化したもの / 半径で正規化したもの）と比べる
    kerns = {"1-t": lambda t: max(0.0, 1 - t), "1-t²": lambda t: max(0.0, 1 - t * t),
             "(1-t²)²": lambda t: max(0.0, 1 - t * t) ** 2, "(1-t²)³": lambda t: max(0.0, 1 - t * t) ** 3}
    multi = []
    for k, pts in enumerate(([(0.2, 1), (0.5, 0), (0.9, 0)], [(0.3, 1), (0.6, 0), (0.8, 0), (0.95, 0)], [(0.1, 0), (0.4, 1), (0.7, 0)])):
        w = geo.createNode("attribwrangle", f"m{k}")
        w.parm("class").set("detail")
        w.parm("snippet").set(" ".join("int p%d = addpoint(0, set(%g, 0, 0)); setpointattrib(0, 'val', p%d, %g);" % (i, d, i, v)
                                       for i, (d, v) in enumerate(pts)))
        f = geo.createNode("attribwrangle", f"mf{k}")
        f.setInput(0, w)
        f.parm("class").set("detail")
        f.parm("snippet").set("int h = pcopen(0, 'P', {0,0,0}, 1.0, 10); f@a = pcfilter(h, 'val'); pcclose(h);")
        a = f.geometry().attribValue("a")
        dmax = max(d for d, v in pts)
        pred = {}
        for name, fn in kerns.items():
            for norm, scale in (("farthest", dmax), ("radius", 1.0)):
                ws = [fn(d / scale) for d, v in pts]
                pred[f"{name}/{norm}"] = round(sum(wt * v for wt, (d, v) in zip(ws, pts)) / sum(ws), 6)
        multi.append({"points": pts, "a": round(a, 6), "pred": pred})
        print(multi[-1])
    sop_bench.save(182, rows, {"multi": multi})


if __name__ == "__main__":
    main()
