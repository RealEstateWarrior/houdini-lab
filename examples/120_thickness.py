# -*- coding: utf-8 -*-
"""実験120 — measurethickness の厚みは、作った厚みと一致するか。

1. 板（box 4×0.3×4）: 大きな面の上では厚み 0.3 になるはず
2. 殻（半径1の球の内側に、半径 r の球を裏返して入れる）: 厚み 1 − r
3. 球（半径1）: 中身が詰まっているので、厚みは直径 2 になるはず
球は細かい多角形なので、多角形のずれも少し乗る。

    hython examples/120_thickness.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def stats(node, attr="thickness", mask=None):
    geo = node.geometry()
    vals = geo.pointFloatAttribValues(attr)
    pos = geo.pointFloatAttribValues("P")
    pick = [v for i, v in enumerate(vals) if mask is None or mask(pos[3 * i:3 * i + 3])]
    n = len(pick)
    return {"n": n, "mean": round(sum(pick) / n, 6), "min": round(min(pick), 6),
            "max": round(max(pick), 6)}


def sphere(geo, name, rad, res=96):
    sp = geo.createNode("sphere", name)
    sp.parm("type").set("polymesh")
    sp.parmTuple("rad").set((rad, rad, rad))
    sp.parm("rows").set(res)
    sp.parm("cols").set(res * 2)
    return sp


def thick(geo, src, name):
    node = geo.createNode("measurethickness", name)
    node.setInput(0, src)
    node.parm("attrname").set("thickness")
    node.parm("maxthickness").set(10.0)
    return node


def main():
    geo = sop_bench.fresh()
    rows = []
    # 1. 板。Polygon Mesh にして点を増やす
    # （最初は Polygon + Use Divisions で作ったが、それは開いた線の籠になり、厚みが測れなかった）
    top_mask = (lambda p: abs(abs(p[1]) - 0.15) < 1e-6 and abs(p[0]) < 1.5 and abs(p[2]) < 1.5)
    for label, setup in (("slab_polymesh", {"type": "polymesh"}),
                         ("slab_poly_usedivisions", {"dodivs": True})):
        box = geo.createNode("box", label)
        box.parmTuple("size").set((4.0, 0.3, 4.0))
        for key, value in setup.items():
            box.parm(key).set(value)
        box.parmTuple("divrate").set((21, 2, 21))
        box.parmTuple("divs").set((21, 2, 21))
        g = box.geometry()
        t0 = time.perf_counter()
        th = thick(geo, box, "t_" + label)
        th.geometry()
        sec = time.perf_counter() - t0
        open_prims = sum(1 for p in g.prims() if not p.isClosed())
        filt = thick(geo, box, "t_nofilter_" + label)
        filt.parm("useblur").set(False)
        filt.parm("medianofneighbors").set(False)
        rows.append({"case": label, "want": 0.3, "sec": round(sec, 4),
                     "prims": g.intrinsicValue("primitivecount"), "open_prims": open_prims,
                     "volume": round(sop_bench.volume(g), 6),
                     **stats(th, mask=top_mask),
                     "nofilter": stats(filt, mask=top_mask)})
        print(rows[-1])
    # 2. 殻
    for r in (0.5, 0.8, 0.95):
        outer = sphere(geo, f"outer_{r}", 1.0)
        inner = sphere(geo, f"inner_{r}", r)
        rev = geo.createNode("reverse", f"rev_{r}")
        rev.setInput(0, inner)
        mg = geo.createNode("merge", f"shell_{r}")
        mg.setInput(0, outer)
        mg.setInput(1, rev)
        t0 = time.perf_counter()
        th = thick(geo, mg, f"t_shell_{r}")
        th.geometry()
        sec = time.perf_counter() - t0
        rows.append({"case": f"shell_{r}", "want": round(1 - r, 6), "sec": round(sec, 4),
                     **stats(th)})
        print(rows[-1])
    # 3. 詰まった球
    solid = sphere(geo, "solid", 1.0)
    th = thick(geo, solid, "t_solid")
    rows.append({"case": "solid_sphere", "want": 2.0, **stats(th)})
    print(rows[-1])

    path = os.path.join(sop_bench.OUT, "120_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
