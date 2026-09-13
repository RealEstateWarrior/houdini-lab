"""polyextrude で押し出し、boolean で削る。硬い形を作る2つの道具。

押し出しは点数がどう増えるのか、距離は指定どおりになるのか。
boolean は3つの演算で何が変わるのか、点の数はどうなるのか。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

geo = hou.node("/obj").createNode("geo", "extrude_boolean")


def probe(type_name, names):
    node = geo.createNode(type_name, f"probe_{type_name}")
    print(f"== {type_name} ==")
    print("  parms:", ", ".join(p.name() for p in node.parms()))
    for name in names:
        parm = node.parm(name)
        if parm is None:
            print(f"    {name}: (なし)")
            continue
        try:
            menu = dict(zip(parm.menuItems(), parm.menuLabels()))
        except hou.OperationFailed:
            menu = None
        print(f"    {name} = {parm.eval()!r}" + (f"  menu={menu}" if menu else ""))
    node.destroy()


probe("polyextrude", ("dist", "inset", "divisions", "outputfront", "outputback",
                      "outputside", "splitType", "limitinset"))
probe("boolean", ("booleanop", "surfacetype", "detriangulate", "asubtract",
                  "bsubtract", "resolvetype"))

# --- 押し出し
grid = geo.createNode("grid", "grid")
grid.parm("sizex").set(10.0)
grid.parm("sizey").set(10.0)
grid.parm("rows").set(5)
grid.parm("cols").set(5)
base_points = len(grid.geometry().points())
base_prims = len(grid.geometry().prims())
print(f"\n== 押し出しの元 ==\n  {base_points}点 / {base_prims}面")

print("\n== polyextrude の距離と結果 ==")
print("%8s %8s %8s %14s %14s" % ("距離", "点数", "面数", "高さ", "指定との差"))
extrude_rows = []
extrude_nodes = []
for distance in (0.0, 0.5, 1.0, 2.0):
    node = geo.createNode("polyextrude", f"ext_{str(distance).replace('.', '_')}")
    node.setFirstInput(grid)
    node.parm("dist").set(distance)
    g = node.geometry()
    height = g.boundingBox().sizevec()[1]
    extrude_rows.append({"dist": distance, "points": len(g.points()),
                         "prims": len(g.prims()), "height": round(height, 5),
                         "image": f"012_ext_{str(distance).replace('.', '_')}.png"})
    extrude_nodes.append(node)
    print("%8.1f %8d %8d %14.5f %14.5f"
          % (distance, len(g.points()), len(g.prims()), height,
             height - distance))

# --- inset を足すと何が変わるか
print("\n== inset（内側への縮み）を変える（距離 1.0 固定）==")
print("%8s %8s %8s %14s" % ("inset", "点数", "面数", "上面の一辺"))
inset_rows = []
for inset in (0.0, 0.3, 0.8):
    node = geo.createNode("polyextrude", f"ins_{str(inset).replace('.', '_')}")
    node.setFirstInput(grid)
    node.parm("dist").set(1.0)
    node.parm("inset").set(inset)
    g = node.geometry()
    # 上面だけの広がりを見るため、最も高い点の水平方向の広がりを測る
    top = [p.position() for p in g.points()
           if abs(p.position()[1] - g.boundingBox().maxvec()[1]) < 1e-5]
    spread = (max(p[0] for p in top) - min(p[0] for p in top)) if top else 0.0
    inset_rows.append({"inset": inset, "points": len(g.points()),
                       "prims": len(g.prims()), "top_spread": round(spread, 5)})
    print("%8.1f %8d %8d %14.5f"
          % (inset, len(g.points()), len(g.prims()), spread))
    node.destroy()

bbox = hou_tools.bbox_union([n.path() for n in extrude_nodes])
for row, node in zip(extrude_rows, extrude_nodes):
    hou_tools.render_preview(node.path(), os.path.join(OUT, row["image"]),
                             res=(420, 320), frame_bbox=bbox,
                             direction=(0.9, 0.5, 1.0))

# --- boolean
box = geo.createNode("box", "bool_box")
box.parm("scale").set(2.0)
sphere = geo.createNode("sphere", "bool_sphere")
sphere.parm("type").set(1)              # ポリゴンにしないと boolean が扱えない
sphere.parm("rows").set(30)
sphere.parm("cols").set(30)
sphere.parmTuple("rad").set((1.35, 1.35, 1.35))

def volume_of(node):
    return sum(p.intrinsicValue("measuredvolume") for p in node.geometry().prims())


box_volume = volume_of(box)
sphere_volume = volume_of(sphere)
print(f"\n== boolean の材料 ==")
print(f"  box: {len(box.geometry().points())}点 /"
      f" {len(box.geometry().prims())}面 / 体積 {box_volume:.5f}")
print(f"  sphere: {len(sphere.geometry().points())}点 /"
      f" {len(sphere.geometry().prims())}面 / 体積 {sphere_volume:.5f}")
print(f"  （sphere の rows/cols を 30 にしても面数が変わらない＝"
      f"ポリゴン球は別の分割方法を使っている）")

print("\n== boolean の演算ごとの結果 ==")
print("%-14s %10s %10s %14s" % ("演算", "点数", "面数", "体積"))
bool_rows = []
bool_nodes = []
probe_bool = geo.createNode("boolean", "probe_op")
op_menu = list(zip(probe_bool.parm("booleanop").menuItems(),
                   probe_bool.parm("booleanop").menuLabels()))
probe_bool.destroy()

for item, label in op_menu:
    if item.startswith("_"):              # メニューの区切り線
        continue
    node = geo.createNode("boolean", f"bool_{item}")
    node.setInput(0, box)
    node.setInput(1, sphere)
    node.parm("booleanop").set(item)
    try:
        g = node.geometry()
    except hou.Error as exc:
        print(f"{label:14s} エラー: {exc}")
        node.destroy()
        continue
    volume = sum(p.intrinsicValue("measuredvolume") for p in g.prims())
    bool_rows.append({"op": item, "label": label, "points": len(g.points()),
                      "prims": len(g.prims()), "volume": round(volume, 5),
                      "image": f"012_bool_{item}.png"})
    bool_nodes.append(node)
    print("%-14s %10d %10d %14.5f"
          % (label, len(g.points()), len(g.prims()), volume))

bool_bbox = hou_tools.bbox_union([n.path() for n in bool_nodes])
for row, node in zip(bool_rows, bool_nodes):
    hou_tools.render_preview(node.path(), os.path.join(OUT, row["image"]),
                             res=(420, 420), frame_bbox=bool_bbox)

# --- 体積の関係が成り立つか
found = {row["op"]: row["volume"] for row in bool_rows}
print("\n== 体積の関係を確かめる ==")
if {"union", "intersect"} <= found.keys():
    total = found["union"] + found["intersect"]
    print(f"  和集合 + 積集合 = {total:.5f}")
    print(f"  box + sphere   = {box_volume + sphere_volume:.5f}")
    print(f"  差             = {abs(total - box_volume - sphere_volume):.7f}")
if {"subtract", "intersect"} <= found.keys():
    expected = box_volume - found["intersect"]
    print(f"  box - 積集合 = {expected:.5f} / 実測の差集合 = {found['subtract']:.5f}")
    print(f"  差           = {abs(expected - found['subtract']):.7f}")

if bool_nodes:
    bool_nodes[0].setDisplayFlag(True)
geo.layoutChildren()
graph = hou_tools.write_graph("/obj/extrude_boolean",
                              os.path.join(OUT, "012_graph.json"),
                              title="polyextrude と boolean")
with open(os.path.join(OUT, "012_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"source": {"points": base_points, "prims": base_prims},
               "extrude": extrude_rows, "inset": inset_rows,
               "boolean": bool_rows,
               "volumes": {"box": round(box_volume, 5),
                           "sphere": round(sphere_volume, 5)}},
              fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "012_extrude_boolean.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
