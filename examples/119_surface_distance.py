# -*- coding: utf-8 -*-
"""実験119 — 面に沿った距離の出し方4通りは、どれが本当の距離に近いか。

実験115 で、attribfill の Arrival Time は四角の網では縦横の道のり |x|+|z| になると分かった。
では distancealonggeometry の3つの測り方（Edge / Surface / Heat Geodesic）と
heatgeodesic はどうか。平らな板の真ん中から測れば、本当の距離は √(x²+z²)。
四角の網・三角の網・remesh した網（向きがばらばら）の3つで比べる。

    hython examples/119_surface_distance.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def compare(node, attrib):
    geo = node.geometry()
    vals = geo.pointFloatAttribValues(attrib)
    pos = geo.pointFloatAttribValues("P")
    diffs = []
    for i, v in enumerate(vals):
        x, z = pos[3 * i], pos[3 * i + 2]
        diffs.append(v - math.sqrt(x * x + z * z))
    n = len(diffs)
    return {"n": n, "mean_abs": round(sum(abs(d) for d in diffs) / n, 6),
            "max_abs": round(max(abs(d) for d in diffs), 6),
            "mean": round(sum(diffs) / n, 6)}


def main():
    geo = sop_bench.fresh()
    meshes = {}
    quad = geo.createNode("grid", "quad")
    quad.parmTuple("size").set((2.0, 2.0))
    quad.parm("rows").set(41)
    quad.parm("cols").set(41)
    meshes["quad"] = quad
    tri = geo.createNode("grid", "tri")
    tri.parmTuple("size").set((2.0, 2.0))
    tri.parm("rows").set(41)
    tri.parm("cols").set(41)
    tri.parm("surftype").set("triangles")
    meshes["tri"] = tri
    rm = geo.createNode("remesh::2.0", "rm")
    rm.setInput(0, quad)
    rm.parm("targetsize").set(0.05)
    # remesh では真ん中に点があるとは限らないので、原点の点を足してからつなぐ
    meshes["remesh"] = rm

    rows = []
    for mesh_name, mesh in meshes.items():
        # 原点に一番近い点を start グループにする
        start = geo.createNode("attribwrangle", f"start_{mesh_name}")
        start.setInput(0, mesh)
        start.parm("class").set(0)
        start.parm("snippet").set(
            'int p = nearpoint(0, {0,0,0});\n'
            'setpointgroup(0, "start", p, 1);\n'
            'vector q = point(0, "P", p); setdetailattrib(0, "offset", length(q));')
        off = start.geometry().attribValue("offset")
        # 原点に点がずれて置かれていたら、その分だけ全体を動かして原点に合わせる
        shift = geo.createNode("attribwrangle", f"shift_{mesh_name}")
        shift.setInput(0, start)
        shift.parm("snippet").set('int p = nearpoint(0, {0,0,0}); @P -= point(0, "P", p);')
        for metric in ("edge", "surface", "heat"):
            node = geo.createNode("distancealonggeometry", f"dag_{mesh_name}_{metric}")
            node.setInput(0, shift)
            node.parm("startpts").set("start")
            node.parm("distmetric").set(metric)
            t0 = time.perf_counter()
            node.geometry()
            sec = time.perf_counter() - t0
            rows.append({"mesh": mesh_name, "method": "distancealonggeometry_" + metric,
                         **compare(node, "dist"), "sec": round(sec, 4), "start_offset": round(off, 6)})
            print(rows[-1])
        hg = geo.createNode("heatgeodesic", f"hg_{mesh_name}")
        hg.setInput(0, shift)
        hg.parm("srcpoints").set("start")
        t0 = time.perf_counter()
        hg.geometry()
        sec = time.perf_counter() - t0
        rows.append({"mesh": mesh_name, "method": "heatgeodesic", **compare(hg, "dist"),
                     "sec": round(sec, 4), "start_offset": round(off, 6)})
        print(rows[-1])
        af = geo.createNode("attribwrangle", f"zero_{mesh_name}")
        af.setInput(0, shift)
        af.parm("snippet").set('f@val = 0;')
        fill = geo.createNode("attribfill", f"af_{mesh_name}")
        fill.setInput(0, af)
        fill.parm("mode").set("eikonal")
        fill.parm("attrib").set("val")
        fill.parm("boundary").set("start")
        t0 = time.perf_counter()
        fill.geometry()
        sec = time.perf_counter() - t0
        rows.append({"mesh": mesh_name, "method": "attribfill_eikonal", **compare(fill, "val"),
                     "sec": round(sec, 4), "start_offset": round(off, 6)})
        print(rows[-1])

    path = os.path.join(sop_bench.OUT, "119_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
