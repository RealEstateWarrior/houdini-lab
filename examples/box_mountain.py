"""Box を山にして細分割し、高さで色を付ける。

hython で実行すると out/ に接続図用JSON・プレビュー画像・統計JSONを書き出す。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

geo = hou.node("/obj").createNode("geo", "box_mountain")

box = geo.createNode("box", "box1")
box.parm("scale").set(1.0)

mountain = geo.createNode("mountain", "mountain1")
mountain.setFirstInput(box)
mountain.parm("height").set(0.35)
mountain.parm("elementsize").set(0.8)

subdivide = geo.createNode("subdivide", "subdivide1")
subdivide.setFirstInput(mountain)
subdivide.parm("iterations").set(1)

color = geo.createNode("color", "color1")
color.setFirstInput(subdivide)
color.parm("colortype").set(1)  # Bounding Box: 位置をそのままRGBに割り当てる

out_null = geo.createNode("null", "OUT")
out_null.setFirstInput(color)
out_null.setDisplayFlag(True)

geo.layoutChildren()

graph = hou_tools.write_graph(
    "/obj/box_mountain",
    os.path.join(OUT, "box_mountain_graph.json"),
    title="Box を山にして細分割し、位置で色付け",
)
stats = hou_tools.geometry_stats("/obj/box_mountain/OUT")
with open(os.path.join(OUT, "box_mountain_stats.json"), "w", encoding="utf-8") as fp:
    json.dump(stats, fp, ensure_ascii=False, indent=2)

hou_tools.render_preview("/obj/box_mountain/OUT", os.path.join(OUT, "box_mountain.png"))
hou_tools.save_hip(os.path.join(OUT, "box_mountain.hipnc"))

print("nodes: %d  edges: %d" % (len(graph["nodes"]), len(graph["edges"])))
print("points: %s  prims: %s" % (stats["points"], stats["prims"]))
print("bbox: %s .. %s" % (stats["bbox_min"], stats["bbox_max"]))
print("point attribs: %s" % ", ".join(stats["point_attribs"]))
