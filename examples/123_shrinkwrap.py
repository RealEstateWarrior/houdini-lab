# -*- coding: utf-8 -*-
"""実験123 — shrinkwrap の外形は、本当に凸包か。

答えが決まる点の置き方で確かめる。
3D: 立方体の8つの角＋中にばらまいた点 → 凸包は立方体そのもの（体積1）
    正八面体の6つの頂点＋中の点 → 体積 4/3
2D: 板の上にばらまいた点 → 凸包の面積を Python で別に計算して比べる（実験108 と同じ計算）

    hython examples/123_shrinkwrap.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "examples"))
hull2d = __import__("108_triangulate").hull


def points_node(geo, name, code):
    wr = geo.createNode("attribwrangle", name)
    wr.parm("class").set(0)
    wr.parm("snippet").set(code)
    return wr


def area_of(parent, node):
    meas = parent.createNode("measure", "a")
    meas.setInput(0, node)
    meas.parm("measure").set("area")
    meas.parm("attribname").set("a")
    total = sum(p.attribValue("a") for p in meas.geometry().prims())
    meas.destroy()
    return total


def main():
    geo = sop_bench.fresh()
    rows = []
    shapes = {
        "cube": ('vector c[] = {{-0.5,-0.5,-0.5},{0.5,-0.5,-0.5},{0.5,0.5,-0.5},{-0.5,0.5,-0.5},'
                 '{-0.5,-0.5,0.5},{0.5,-0.5,0.5},{0.5,0.5,0.5},{-0.5,0.5,0.5}};', 1.0),
        "octahedron": ('vector c[] = {{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};', 4 / 3),
    }
    for name, (corners, want) in shapes.items():
        for inner in (0, 100, 10000):
            code = (corners + '\nforeach (vector q; c) addpoint(0, q);\n'
                    f'for (int i = 0; i < {inner}; i++) {{\n'
                    '  vector r = rand(set(i, 1.3, 7.7)) - 0.5;\n'
                    '  if (abs(r.x) + abs(r.y) + abs(r.z) < 0.49) addpoint(0, r);\n'
                    '}')
            pts = points_node(geo, f"{name}_{inner}", code)
            sw = geo.createNode("shrinkwrap::2.0", f"sw_{name}_{inner}")
            sw.setInput(0, pts)
            sw.parm("type").set("xyz")
            t0 = time.perf_counter()
            out = sw.geometry()
            sec = time.perf_counter() - t0
            vol = sop_bench.volume(out)
            rows.append({"case": name, "inner": inner,
                         "input_points": pts.geometry().intrinsicValue("pointcount"),
                         "out_points": out.intrinsicValue("pointcount"),
                         "out_prims": out.intrinsicValue("primitivecount"),
                         "volume": round(vol, 6), "want": round(want, 6), "sec": round(sec, 4)})
            print(rows[-1])

    plate = geo.createNode("grid", "plate")
    plate.parmTuple("size").set((4.0, 3.0))
    plate.parm("rows").set(2)
    plate.parm("cols").set(2)
    for count in (20, 1000, 100000):
        sc = geo.createNode("scatter::2.0", f"sc{count}")
        sc.setInput(0, plate)
        sc.parm("npts").set(count)
        sc.parm("seed").set(3)
        sw = geo.createNode("shrinkwrap::2.0", f"sw2d_{count}")
        sw.setInput(0, sc)
        sw.parm("type").set("xy")
        sw.parm("planesrc").set("fitplane")
        t0 = time.perf_counter()
        out = sw.geometry()
        sec = time.perf_counter() - t0
        pos = sc.geometry().pointFloatAttribValues("P")
        h, area = hull2d([(pos[3 * i], pos[3 * i + 2]) for i in range(count)])
        rows.append({"case": "plane2d", "inner": count, "input_points": count,
                     "out_points": out.intrinsicValue("pointcount"),
                     "out_prims": out.intrinsicValue("primitivecount"),
                     "area": round(area_of(geo, sw), 6), "want": round(area, 6),
                     "hull_points": h, "sec": round(sec, 4)})
        print(rows[-1])

    path = os.path.join(sop_bench.OUT, "123_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
