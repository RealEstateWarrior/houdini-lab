"""mountain と subdivide の順序を入れ替えると何が変わるか。

実験001で「mountain はポイントを増やさないので、先に分割数を上げる必要がある」と
書いた。それを順序違いの並列比較で確かめ、ディテール量を表面積で定量化する。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

MOUNTAIN = {"height": 0.35, "elementsize": 0.8}


def surface_area(geometry):
    return sum(prim.intrinsicValue("measuredarea") for prim in geometry.prims())


geo = hou.node("/obj").createNode("geo", "order_compare")
box = geo.createNode("box", "box1")

# 利用できる intrinsic を確認する（推測で面積を計算しないため）
probe = geo.createNode("box", "probe")
print("== polygon intrinsics ==")
print(", ".join(sorted(probe.geometry().prims()[0].intrinsicNames())))
probe.destroy()


def mountain_node(name, parent):
    node = geo.createNode("mountain", name)
    node.setFirstInput(parent)
    for parm, value in MOUNTAIN.items():
        node.parm(parm).set(value)
    return node


def subdivide_node(name, parent, iterations):
    node = geo.createNode("subdivide", name)
    node.setFirstInput(parent)
    node.parm("iterations").set(iterations)
    return node


# A: 先にノイズ、あとで分割（実験001と同じ順序）
a_mountain = mountain_node("A_mountain", box)
a_out = subdivide_node("A_subdiv", a_mountain, 2)

# B: 先に分割、あとでノイズ
b_subdiv = subdivide_node("B_subdiv", box, 2)
b_out = mountain_node("B_mountain", b_subdiv)

# C: さらに細かく分割してからノイズ
c_subdiv = subdivide_node("C_subdiv", box, 3)
c_out = mountain_node("C_mountain", c_subdiv)

# D: C と同じ分割数だが、ノイズの特徴サイズを小さくする
d_subdiv = subdivide_node("D_subdiv", box, 3)
d_out = geo.createNode("mountain", "D_mountain")
d_out.setFirstInput(d_subdiv)
d_out.parm("height").set(MOUNTAIN["height"])
d_out.parm("elementsize").set(0.25)

# E: D と同じノイズ設定で、点数だけ増やす（4回分割）
e_subdiv = subdivide_node("E_subdiv", box, 4)
e_out = geo.createNode("mountain", "E_mountain")
e_out.setFirstInput(e_subdiv)
e_out.parm("height").set(MOUNTAIN["height"])
e_out.parm("elementsize").set(0.25)

# 基準: ノイズなしで分割しただけ（A/B は2回、C は3回と対応させる）
base = subdivide_node("base_subdiv", box, 2)
base3 = subdivide_node("base3_subdiv", box, 3)
base4 = subdivide_node("base4_subdiv", box, 4)

b_out.setDisplayFlag(True)
geo.layoutChildren()

variants = [
    ("base", "分割のみ（ノイズなし）", base),
    ("A", "mountain → subdivide(2)", a_out),
    ("B", "subdivide(2) → mountain", b_out),
    ("C", "subdivide(3) → mountain", c_out),
    ("D", "subdivide(3) → mountain\n（elementsize 0.25）", d_out),
    ("E", "subdivide(4) → mountain\n（elementsize 0.25）", e_out),
]

bbox = hou_tools.bbox_union([node.path() for _, _, node in variants])

measurements = []
for key, label, node in variants:
    g = node.geometry()
    area = surface_area(g)
    size = g.boundingBox().sizevec()
    measurements.append({
        "key": key,
        "label": label,
        "points": len(g.points()),
        "prims": len(g.prims()),
        "area": round(area, 5),
        "size": [round(v, 4) for v in size],
        "image": f"003_{key}.png",
    })
    hou_tools.render_preview(node.path(), os.path.join(OUT, f"003_{key}.png"),
                             res=(540, 540), frame_bbox=bbox)

graph = hou_tools.write_graph(
    "/obj/order_compare",
    os.path.join(OUT, "003_graph.json"),
    title="mountain と subdivide の順序比較",
)
with open(os.path.join(OUT, "003_stats.json"), "w", encoding="utf-8") as fp:
    json.dump(measurements, fp, ensure_ascii=False, indent=2)

hou_tools.save_hip(os.path.join(OUT, "003_order.hipnc"))

base_area = measurements[0]["area"]
print("\n== 実測 ==")
print("key   points  prims     表面積   基準比   一辺    面積/一辺^2")
for m in measurements:
    side = m["size"][0]
    print("%-5s %6d  %5d  %9.5f  %7.3f  %.4f  %11.5f"
          % (m["key"], m["points"], m["prims"], m["area"],
             m["area"] / base_area, side, m["area"] / (side * side)))

print("\n== 順序を変えたときのポイント数 ==")
for m in measurements[1:3]:
    print("  %-26s %d点" % (m["label"], m["points"]))
print("nodes: %d  edges: %d" % (len(graph["nodes"]), len(graph["edges"])))

# --- 表面積だけでは「凹凸の量」を測れていないので、基準形からのずれを直接測る。
# 同じ分割回数ならトポロジもポイントの順序も同じなので、点ごとに引き算できる。
def displacement(noisy_node, base_node):
    a = [p.position() for p in noisy_node.geometry().points()]
    b = [p.position() for p in base_node.geometry().points()]
    if len(a) != len(b):
        raise ValueError("ポイント数が違うので点ごとの比較はできない")
    distances = [(pa - pb).length() for pa, pb in zip(a, b)]
    return {
        "mean": sum(distances) / len(distances),
        "max": max(distances),
        "moved": sum(1 for d in distances if d > 1e-6),
        "count": len(distances),
    }


print("\n== 基準形（ノイズなし）からの点ごとのずれ ==")
print("%-26s %8s %8s %14s" % ("", "平均", "最大", "動いた点/全体"))
for label, noisy, reference in (
    ("mountain → subdivide(2)", a_out, base),
    ("subdivide(2) → mountain", b_out, base),
    ("subdivide(3) → mountain", c_out, base3),
    ("同上・elementsize 0.25", d_out, base3),
    ("subdivide(4)・elementsize 0.25", e_out, base4),
):
    d = displacement(noisy, reference)
    print("%-26s %8.5f %8.5f %8d/%-5d"
          % (label, d["mean"], d["max"], d["moved"], d["count"]))

# --- mountain が実際に何点を動かしているかを、分割前の段階で確認する
print("\n== mountain 直後（分割前）に動いた点の数 ==")
for label, noisy, reference in (
    ("box → mountain", a_mountain, box),
    ("subdivide(2) → mountain", b_out, b_subdiv),
    ("subdivide(3) → mountain", c_out, c_subdiv),
):
    d = displacement(noisy, reference)
    print("  %-26s %d/%d 点  平均ずれ %.5f"
          % (label, d["moved"], d["count"], d["mean"]))
