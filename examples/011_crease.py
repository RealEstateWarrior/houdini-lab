"""crease（折り目）で、分割しても角を残せるか。

実験002で「subdivide を重ねると立方体が球になる」と測った。3回分割で一辺が
0.84918 まで縮む。crease を付ければ角が保たれるはずだが、どれだけの重みが
必要なのかは分からない。

理屈の上では「重み N なら N 回分の分割まで角が保たれる」はず。3回分割するなら
重み3で完全に立方体のままになる、という予測を立てて確かめる。
"""

import json
import math
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

ITERATIONS = 3
WEIGHTS = (0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 10.0)

geo = hou.node("/obj").createNode("geo", "crease_test")
box = geo.createNode("box", "box1")

probe = geo.createNode("crease", "probe")
print("== crease SOP の既定値 ==")
for name in ("group", "op", "crease", "creaseattrib", "addcolor"):
    parm = probe.parm(name)
    print(f"  {name} = {parm.eval()!r}" if parm else f"  {name}: (なし)")
probe.destroy()


def sharpness(node):
    """隣り合う面のなす角の最大値。角が残っていれば大きく、丸まれば小さい。"""
    geometry = node.geometry()
    normals = {}
    for prim in geometry.prims():
        normals[prim.number()] = prim.normal()

    # 辺を共有する面の組を、点の組から探す
    by_edge = {}
    for prim in geometry.prims():
        points = [v.point().number() for v in prim.vertices()]
        for i in range(len(points)):
            a, b = points[i], points[(i + 1) % len(points)]
            by_edge.setdefault((min(a, b), max(a, b)), []).append(prim.number())

    angles = []
    for prims in by_edge.values():
        if len(prims) != 2:
            continue
        first, second = normals[prims[0]], normals[prims[1]]
        dot = max(-1.0, min(1.0, first.dot(second)))
        angles.append(math.degrees(math.acos(dot)))
    return max(angles) if angles else 0.0


rows = []
nodes = []
print(f"\n== 重みを変えて {ITERATIONS} 回分割する ==")
print("%8s %10s %10s %14s %14s"
      % ("重み", "点数", "面数", "一辺の長さ", "最大の折れ角"))
for weight in WEIGHTS:
    tag = str(weight).replace(".", "_")
    crease = geo.createNode("crease", f"crease_{tag}")
    crease.setFirstInput(box)
    crease.parm("op").set("set")
    crease.parm("crease").set(weight)

    sub = geo.createNode("subdivide", f"sub_{tag}")
    sub.setFirstInput(crease)
    sub.parm("iterations").set(ITERATIONS)

    g = sub.geometry()
    side = g.boundingBox().sizevec()[0]
    angle = sharpness(sub)
    rows.append({"weight": weight, "points": len(g.points()),
                 "prims": len(g.prims()), "side": round(side, 5),
                 "angle": round(angle, 2), "image": f"011_w{tag}.png"})
    nodes.append(sub)
    print("%8.1f %10d %10d %14.5f %13.2f度"
          % (weight, len(g.points()), len(g.prims()), side, angle))

bbox = hou_tools.bbox_union([n.path() for n in nodes])
for row, node in zip(rows, nodes):
    hou_tools.render_preview(node.path(), os.path.join(OUT, row["image"]),
                             res=(420, 420), frame_bbox=bbox)

# 比較用: 分割していない素の box
raw_side = box.geometry().boundingBox().sizevec()[0]
raw_angle = sharpness(box)
print(f"\n  参考: 分割前の box は 一辺 {raw_side:.5f} / 折れ角 {raw_angle:.2f}度")
hou_tools.render_preview(box.path(), os.path.join(OUT, "011_raw.png"),
                         res=(420, 420), frame_bbox=bbox)

nodes[0].setDisplayFlag(True)
geo.layoutChildren()
graph = hou_tools.write_graph("/obj/crease_test",
                              os.path.join(OUT, "011_graph.json"),
                              title="crease の重みと角の残り方")
with open(os.path.join(OUT, "011_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"iterations": ITERATIONS, "raw_side": round(raw_side, 5),
               "raw_angle": round(raw_angle, 2), "rows": rows}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "011_crease.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
