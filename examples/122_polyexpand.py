# -*- coding: utf-8 -*-
"""実験122 — polyexpand2d でずらした線は、角を丸めるのか、尖らせるのか。

1辺2の正方形を外へ d だけずらすと、
  角を尖らせる（留め継ぎ）なら 周の長さ 4·(2 + 2d)
  角を丸めるなら              周の長さ 8 + 2πd
内へ d ずらすと、どちらでも 4·(2 − 2d)。
周の長さを測れば、どちらの作り方かが分かる。Divisions で何本も作ったときの間隔も見る。

    hython examples/122_polyexpand.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def perimeters(parent, node):
    meas = parent.createNode("measure", "per")
    meas.setInput(0, node)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    geo = meas.geometry()
    out = sorted(round(p.attribValue("len"), 6) for p in geo.prims())
    pts = geo.intrinsicValue("pointcount")
    meas.destroy()
    return out, pts


def main():
    geo = sop_bench.fresh()
    sq = geo.createNode("attribwrangle", "square")
    sq.parm("class").set(0)
    sq.parm("snippet").set(
        'int a = addpoint(0, {-1,0,-1}); int b = addpoint(0, {1,0,-1});\n'
        'int c = addpoint(0, {1,0,1}); int d = addpoint(0, {-1,0,1});\n'
        'addprim(0, "poly", a, b, c, d);')
    rows = []
    for d in (0.1, 0.25, 0.5):
        for side in ("outside", "inside"):
            node = geo.createNode("polyexpand2d", f"pe_{side}_{int(d * 100)}")
            node.setInput(0, sq)
            node.parm("offset").set(d)
            node.parm("divs").set(1)
            node.parm("outputinside").set(side == "inside")
            node.parm("outputoutside").set(side == "outside")
            t0 = time.perf_counter()
            per, pts = perimeters(geo, node)
            sec = time.perf_counter() - t0
            rows.append({"d": d, "side": side, "perimeters": per, "points": pts,
                         "mitre": round(4 * (2 + 2 * d), 6) if side == "outside" else round(4 * (2 - 2 * d), 6),
                         "round": round(8 + 2 * math.pi * d, 6) if side == "outside" else None,
                         "sec": round(sec, 4)})
            print(rows[-1])
    # 何本も作る
    node = geo.createNode("polyexpand2d", "pe_multi")
    node.setInput(0, sq)
    node.parm("offset").set(0.2)
    node.parm("divs").set(4)
    node.parm("outputinside").set(True)
    node.parm("outputoutside").set(True)
    per, pts = perimeters(geo, node)
    multi = {"offset": 0.2, "divs": 4, "perimeters": per, "points": pts}
    print(multi)
    # 鋭い角: 頂角 20° の二等辺三角形。尖らせるなら、外へずらした線は相似な三角形で、
    # 周の長さは (内接円の半径 + d) / 内接円の半径 倍になる
    sharp = []
    for d in (0.05, 0.1, 0.2):
        tri = geo.createNode("attribwrangle", f"tri_{int(d * 100)}")
        tri.parm("class").set(0)
        half = math.radians(10)
        h = 2.0
        tri.parm("snippet").set(
            f'int a = addpoint(0, set(0, 0, {h})); int b = addpoint(0, set({h * math.tan(half)}, 0, 0));\n'
            f'int c = addpoint(0, set({-h * math.tan(half)}, 0, 0));\n'
            'addprim(0, "poly", a, b, c);')
        base = 2 * h * math.tan(half)
        leg = h / math.cos(half)
        per0 = base + 2 * leg
        area = base * h / 2
        r_in = 2 * area / per0
        node = geo.createNode("polyexpand2d", f"pe_tri_{int(d * 100)}")
        node.setInput(0, tri)
        node.parm("offset").set(d)
        node.parm("outputinside").set(False)
        node.parm("outputoutside").set(True)
        per, pts = perimeters(geo, node)
        sharp.append({"d": d, "perimeters": per, "points": pts, "per0": round(per0, 6),
                      "mitre": round(per0 * (r_in + d) / r_in, 6),
                      "round": round(per0 + 2 * math.pi * d, 6)})
        print(sharp[-1])
    path = os.path.join(sop_bench.OUT, "122_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "multi": multi, "sharp": sharp}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
