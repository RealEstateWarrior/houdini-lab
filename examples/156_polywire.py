# -*- coding: utf-8 -*-
"""実験156 — polywire の管は、Wire Radius の円に内接する正 n 角形か。折れ目では太さがどう変わるか。

1. 長さ 2 のまっすぐな線に polywire（Wire Radius r = 0.1、Divisions n）をかけ、
   点が軸からちょうど r にあるか、側面の面積が 長さ × 2n·r·sin(π/n) になるかを見る（両端には蓋が付く）。
2. 90° に折れた線（(0,0,0)→(1,0,0)→(1,1,0)）で、折れ目の点の輪が軸からどれだけ離れるかを
   Prevent Joint Buckling の入切で比べる。折れ目で太さを保つなら、曲がりの面の中では r / cos(45°) になるはず。

    hython examples/156_polywire.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def line(geo, name, pts):
    n = geo.createNode("add", name)
    n.parm("points").set(len(pts))
    for i, p in enumerate(pts):
        n.parmTuple(f"pt{i}").set(p)
        n.parm(f"usept{i}").set(1)
    n.parm("stdswitcher1").set(1) if n.parm("stdswitcher1") else None
    n.parm("prims").set(1)
    n.parm("prim0").set(" ".join(str(i) for i in range(len(pts))))
    return n


def main():
    geo = sop_bench.fresh()
    r = 0.1
    straight = line(geo, "straight", [(0, 0, 0), (2, 0, 0)])
    rows = []
    for n in (3, 4, 6, 8, 16, 32):
        w = geo.createNode("polywire", f"w{n}")
        w.setInput(0, straight)
        w.parm("radius").set(r)
        w.parm("div").set(n)
        t0 = time.perf_counter()
        g = w.geometry()
        sec = time.perf_counter() - t0
        d = [math.hypot(p.position()[1], p.position()[2]) for p in g.points()]
        xs = sorted({round(p.position()[0], 6) for p in g.points()})
        area = sum(pr.intrinsicValue("measuredarea") for pr in g.prims())
        rows.append({"div": n, "points": len(g.points()), "prims": len(g.prims()), "rmin": round(min(d), 6), "rmax": round(max(d), 6),
                     "x_span": [xs[0], xs[-1]], "area": round(area, 6),
                     "want_side": round(2.0 * 2 * n * r * math.sin(math.pi / n), 6),
                     "want_caps": round(2 * (n / 2) * r * r * math.sin(2 * math.pi / n), 6),
                     "volume": round(sop_bench.volume(g), 6),
                     "want_volume": round(2.0 * (n / 2) * r * r * math.sin(2 * math.pi / n), 6), "sec": round(sec, 4)})
        print(rows[-1])
    bent = line(geo, "bent", [(0, 0, 0), (1, 0, 0), (1, 1, 0)])
    joints = []
    for jc in (1, 0):
        w = geo.createNode("polywire", f"bend{jc}")
        w.setInput(0, bent)
        w.parm("radius").set(r)
        w.parm("div").set(16)
        w.parm("jointcorrect").set(jc)
        g = w.geometry()
        corner = hou.Vector3(1, 0, 0)
        pts = [p.position() for p in g.points()]
        ring = [p for p in pts if (p - corner).length() < 0.3]   # 折れ目の点の輪
        dist = [(p - corner).length() for p in ring]
        miter = hou.Vector3(1, -1, 0).normalized()
        inplane = [abs((p - corner).dot(miter)) for p in ring]
        offplane = max(abs((p - corner).dot(hou.Vector3(1, 1, 0).normalized())) for p in ring)
        joints.append({"jointcorrect": jc, "ring_points": len(ring), "dist_min": round(min(dist), 6), "dist_max": round(max(dist), 6),
                       "inplane_max": round(max(inplane), 6), "off_bisector": round(offplane, 6), "want_inplane": round(r / math.cos(math.pi / 4), 6),
                       "area": round(sum(pr.intrinsicValue("measuredarea") for pr in g.prims()), 6)})
        print(joints[-1])
    sop_bench.save(156, rows, {"radius": r, "joints": joints})


if __name__ == "__main__":
    main()
