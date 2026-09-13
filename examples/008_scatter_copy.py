"""scatter で点をばらまき、copy to points でジオメトリを複製する。

プロシージャルモデリングの中核パターン。点の数、複製後の点数、そして
「複製したものが地面の傾きに沿うかどうか」を測る。
"""

import json
import math
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

geo = hou.node("/obj").createNode("geo", "scatter_copy")


def create(type_names, name):
    """ノードのタイプ名はバージョンで変わることがあるので、順に試す。"""
    for type_name in type_names:
        try:
            return geo.createNode(type_name, name)
        except hou.OperationFailed:
            continue
    raise SystemExit(f"作れるノードがなかった: {type_names}")


# --- 地面を作る
grid = geo.createNode("grid", "ground")
grid.parm("sizex").set(10.0)
grid.parm("sizey").set(10.0)
grid.parm("rows").set(60)
grid.parm("cols").set(60)

terrain = geo.createNode("mountain", "terrain")
terrain.setFirstInput(grid)
terrain.parm("height").set(1.2)
terrain.parm("elementsize").set(3.0)

normals = geo.createNode("normal", "ground_normals")
normals.setFirstInput(terrain)

# --- scatter のパラメータを確認する
probe = geo.createNode("scatter", "probe")
print("== scatter SOP の主なパラメータ ==")
for name in ("npts", "randseed", "relaxiterations", "usedensity", "densityattrib",
             "outputnormal", "emergencylimit"):
    parm = probe.parm(name)
    print(f"  {name}: " + ("(なし)" if parm is None else repr(parm.eval())))
print("  全パラメータ:", ", ".join(p.name() for p in probe.parms()))
probe.destroy()

COUNTS = (50, 200, 800)
print("\n== scatter の npts と実際の点数 ==")
print("%10s %10s %10s" % ("指定した数", "実際の点数", "一致"))
scatter_rows = []
for count in COUNTS:
    node = geo.createNode("scatter", f"scatter_{count}")
    node.setFirstInput(normals)
    node.parm("npts").set(count)
    actual = len(node.geometry().points())
    scatter_rows.append({"requested": count, "actual": actual})
    print("%10d %10d %10s" % (count, actual, "はい" if actual == count else "いいえ"))
    if count != 200:
        node.destroy()

scatter = geo.node("scatter_200")
print("\n  scatter が持つポイントアトリビュート:",
      ", ".join(a.name() for a in scatter.geometry().pointAttribs()))

# --- 複製するもの
template = geo.createNode("tube", "template")
template.parm("type").set(1)        # 既定は Primitive で1点1面になるので Polygon にする
template.parm("cap").set(1)
template.parm("rad1").set(0.0)      # 先細りの円錐にして向きを見やすくする
template.parm("rad2").set(0.18)
template.parm("height").set(0.9)
template.parm("cols").set(10)
template.parm("rows").set(2)
tpl_points = len(template.geometry().points())
tpl_prims = len(template.geometry().prims())
print(f"\n== 複製するジオメトリ ==\n  {tpl_points}点 / {tpl_prims}面")


def copy_node(name, points_node):
    node = create(("copytopoints::2.0", "copytopoints"), name)
    node.setInput(0, template)
    node.setInput(1, points_node)
    return node


# --- A: 法線なしの点に複製する
strip = geo.createNode("attribdelete", "strip_normals")
strip.setFirstInput(scatter)
strip.parm("ptdel").set("N")

copy_plain = copy_node("copy_plain", strip)

# --- B: 法線ありの点に複製する
copy_oriented = copy_node("copy_oriented", scatter)

# --- C: 法線あり＋大きさをばらつかせる
vary = geo.createNode("attribwrangle", "vary_scale")
vary.setFirstInput(scatter)
vary.parm("snippet").set("@pscale = fit01(rand(@ptnum * 7.3), 0.35, 1.4);")
copy_varied = copy_node("copy_varied", vary)


def copy_stats(node, source_points):
    geometry = node.geometry()
    positions = [p.position() for p in geometry.points()]
    copies = len(positions) // tpl_points

    # 各複製について「重心から最も遠い点」への向きを取る。テンプレートは同じなので、
    # 複製が回転していなければこの向きは全部そろう。ばらつけば回転しているということ。
    directions = []
    sizes = []
    for i in range(copies):
        block = positions[i * tpl_points:(i + 1) * tpl_points]
        centroid = hou.Vector3(0, 0, 0)
        for p in block:
            centroid += p
        centroid /= len(block)
        # テンプレートの頂点の並び順は複製間で同じなので、固定の番号の点を使う。
        # 「最も遠い点」を選ぶ方式は、円錐の底面リングのように等距離の点が並ぶと
        # 選ばれる点が複製ごとにばらついて意味をなさなかった。
        axis = block[0] - centroid
        if axis.length() > 1e-9:
            directions.append(axis.normalized())
            sizes.append(axis.length())

    mean_dir = hou.Vector3(0, 0, 0)
    for d in directions:
        mean_dir += d
    mean_dir = mean_dir.normalized()
    angles = [math.degrees(math.acos(max(-1.0, min(1.0, d.dot(mean_dir)))))
              for d in directions]

    return {
        "points": len(positions),
        "prims": len(geometry.prims()),
        "copies": copies,
        "expected_points": source_points * tpl_points,
        "angle_mean": sum(angles) / len(angles),
        "angle_max": max(angles),
        "size_min": min(sizes),
        "size_max": max(sizes),
    }


scatter_points = len(scatter.geometry().points())
variants = [
    ("plain", "法線なし", copy_plain),
    ("oriented", "法線あり", copy_oriented),
    ("varied", "法線あり＋pscale", copy_varied),
]

copy_oriented.setDisplayFlag(True)
geo.layoutChildren()

bbox = hou_tools.bbox_union([node.path() for _, _, node in variants])
hou_tools.render_preview(terrain.path(), os.path.join(OUT, "008_ground.png"),
                         res=(460, 330), direction=(0.9, 0.5, 1.0))

print("\n== copy to points の結果（散布点 %d、テンプレート %d点）=="
      % (scatter_points, tpl_points))
print("%-18s %8s %8s %10s %12s %12s"
      % ("条件", "点数", "複製数", "予想点数", "向きのばらつき", "大きさの幅"))
copy_rows = []
for key, label, node in variants:
    stats = copy_stats(node, scatter_points)
    copy_rows.append({"key": key, "label": label, **stats,
                      "image": f"008_{key}.png"})
    hou_tools.render_preview(node.path(), os.path.join(OUT, f"008_{key}.png"),
                             res=(460, 330), direction=(0.9, 0.5, 1.0),
                             frame_bbox=bbox)
    print("%-18s %8d %8d %10d %7.2f度/%5.2f %5.2f〜%5.2f"
          % (label, stats["points"], stats["copies"], stats["expected_points"],
             stats["angle_mean"], stats["angle_max"],
             stats["size_min"], stats["size_max"]))


# --- 追加検証: N はテンプレートのどの軸に対応するのか
# 複製が地面の傾きに沿って回ってはいるが、円錐が横倒しに見える。
# N がテンプレートの Y 軸ではなく Z 軸に割り当てられている疑いがある。
def tip_index(node, axis):
    """テンプレートの先端の点番号。並び順は複製後も保たれる。"""
    positions = [p.position() for p in node.geometry().points()]
    return max(range(len(positions)), key=lambda i: positions[i][axis])


def angle_against_normals(copy_node, template_node, template_axis, points_node):
    tip = tip_index(template_node, template_axis)
    per_copy = len(template_node.geometry().points())
    pos = [p.position() for p in copy_node.geometry().points()]
    normals = [hou.Vector3(p.attribValue("N"))
               for p in points_node.geometry().points()]

    angles = []
    for i, normal in enumerate(normals):
        block = pos[i * per_copy:(i + 1) * per_copy]
        centroid = hou.Vector3(0, 0, 0)
        for p in block:
            centroid += p
        centroid /= len(block)
        direction = (block[tip] - centroid).normalized()
        dot = max(-1.0, min(1.0, direction.dot(normal.normalized())))
        angles.append(math.degrees(math.acos(dot)))
    return sum(angles) / len(angles), min(angles), max(angles)


template_z = geo.createNode("tube", "template_z")
for parm_name, value in (("type", 1), ("cap", 1), ("rad1", 0.0), ("rad2", 0.18),
                         ("height", 0.9), ("cols", 10), ("rows", 2),
                         ("orient", 2)):
    template_z.parm(parm_name).set(value)

copy_z = create(("copytopoints::2.0", "copytopoints"), "copy_z")
copy_z.setInput(0, template_z)
copy_z.setInput(1, scatter)
hou_tools.render_preview(copy_z.path(), os.path.join(OUT, "008_z_axis.png"),
                         res=(460, 330), direction=(0.9, 0.5, 1.0),
                         frame_bbox=bbox)

print("\n== 複製の向きと、散布点の N との角度 ==")
print("%-28s %10s %10s %10s" % ("テンプレートの向き", "平均", "最小", "最大"))
axis_rows = []
for label, node, template_node, axis in (
    ("Y軸（tube の既定）", copy_oriented, template, 1),
    ("Z軸", copy_z, template_z, 2),
):
    mean_a, min_a, max_a = angle_against_normals(node, template_node, axis, scatter)
    axis_rows.append({"label": label, "mean": round(mean_a, 3),
                      "min": round(min_a, 3), "max": round(max_a, 3)})
    print("%-28s %9.2f度 %9.2f度 %9.2f度" % (label, mean_a, min_a, max_a))

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/scatter_copy",
                              os.path.join(OUT, "008_graph.json"),
                              title="scatter と copy to points")
with open(os.path.join(OUT, "008_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"scatter": scatter_rows, "template": {"points": tpl_points,
                                                     "prims": tpl_prims},
               "copies": copy_rows, "axis": axis_rows}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "008_scatter_copy.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
