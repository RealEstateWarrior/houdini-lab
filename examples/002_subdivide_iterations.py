"""subdivide の回数を 0〜3 で比較する。

ポイント数・プリミティブ数・バウンディングボックスの変化を実測し、
同一カメラでレンダして並べる。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
ITERATIONS = (0, 1, 2, 3)

geo = hou.node("/obj").createNode("geo", "subdiv_compare")

# subdivide SOP が実際に何を提供しているかを確認する（推測で書かないため）
probe = geo.createNode("subdivide", "probe")
print("== subdivide SOP parms ==")
print(", ".join(p.name() for p in probe.parms()))
for name in ("algorithm", "iterations", "surroundpoly", "closeholes"):
    parm = probe.parm(name)
    if parm is None:
        print(f"  {name}: (なし)")
        continue
    try:
        labels = parm.menuLabels()
    except hou.OperationFailed:
        labels = None
    print(f"  {name}: default={parm.eval()!r} menu={labels}")
probe.destroy()

box = geo.createNode("box", "box1")

variants = []
for n in ITERATIONS:
    node = geo.createNode("subdivide", f"subdiv_{n}")
    node.setFirstInput(box)
    node.parm("iterations").set(n)
    variants.append((n, node))

variants[-1][1].setDisplayFlag(True)
geo.layoutChildren()

bbox = hou_tools.bbox_union([node.path() for _, node in variants])

measurements = []
for n, node in variants:
    geometry = node.geometry()
    size = geometry.boundingBox().sizevec()
    measurements.append({
        "iterations": n,
        "points": len(geometry.points()),
        "prims": len(geometry.prims()),
        "size": [round(v, 4) for v in size],
        "image": f"002_subdiv_{n}.png",
    })
    hou_tools.render_preview(node.path(), os.path.join(OUT, f"002_subdiv_{n}.png"),
                             res=(540, 540), frame_bbox=bbox)

graph = hou_tools.write_graph(
    "/obj/subdiv_compare",
    os.path.join(OUT, "002_graph.json"),
    title="subdivide の回数比較（box を4通りに分岐）",
)
with open(os.path.join(OUT, "002_stats.json"), "w", encoding="utf-8") as fp:
    json.dump(measurements, fp, ensure_ascii=False, indent=2)

hou_tools.save_hip(os.path.join(OUT, "002_subdivide.hipnc"))

print("\n== 実測 ==")
print("iter  points  prims   bbox size")
for m in measurements:
    print("%4d  %6d  %6d   %s" % (m["iterations"], m["points"], m["prims"], m["size"]))

print("\n== プリミティブ数の倍率 ==")
for prev, cur in zip(measurements, measurements[1:]):
    ratio = cur["prims"] / prev["prims"] if prev["prims"] else float("nan")
    print("  %d回 -> %d回 : %.2f倍" % (prev["iterations"], cur["iterations"], ratio))

print("\n== 一辺の長さの変化（元の box は 1.0） ==")
for m in measurements:
    print("  %d回: %.4f" % (m["iterations"], m["size"][0]))
print("nodes: %d  edges: %d" % (len(graph["nodes"]), len(graph["edges"])))

# --- 追加検証1: 1回目だけ辺の長さが 1.0 のまま縮まないのはなぜか
# 仮説: Catmull-Clark は各面の中心に新しい点を作る。立方体の面中心は ±0.5 に
# あるため、1回目はその新点がバウンディングボックスの端を保持している。
probe1 = geo.createNode("subdivide", "verify_iter1")
probe1.setFirstInput(box)
probe1.parm("iterations").set(1)
positions = [p.position() for p in probe1.geometry().points()]
max_x = max(pos[0] for pos in positions)
holders = [pos for pos in positions if abs(pos[0] - max_x) < 1e-6]
print("\n== 追加検証1: 1回目の +X 端を保持している点 ==")
print("  max x = %.6f" % max_x)
print("  その位置にある点の数 = %d" % len(holders))
for pos in holders:
    print("    (%.4f, %.4f, %.4f)" % (pos[0], pos[1], pos[2]))

# --- 追加検証2: 回数を増やすとどこまで縮むのか（レンダなしで数値だけ）
print("\n== 追加検証2: 収束の様子 ==")
print("iter  points   prims   一辺")
for n in range(0, 7):
    node = geo.createNode("subdivide", f"converge_{n}")
    node.setFirstInput(box)
    node.parm("iterations").set(n)
    g = node.geometry()
    print("%4d  %6d  %6d   %.5f"
          % (n, len(g.points()), len(g.prims()), g.boundingBox().sizevec()[0]))
    node.destroy()

# --- 追加検証3: 縮みの原因は「分割」ではなく「平滑化」なのかを確かめる
# OpenSubdiv Bilinear は平滑化せずに分割するだけの方式。これで縮まなければ、
# 縮みの原因は分割そのものではなく Catmull-Clark の平滑化だと確定できる。
print("\n== 追加検証3: アルゴリズム別（iterations=3 で固定） ==")
algorithms = probe1.parm("algorithm").menuLabels()
for index, label in enumerate(algorithms):
    node = geo.createNode("subdivide", f"alg_{index}")
    node.setFirstInput(box)
    node.parm("algorithm").set(index)
    node.parm("iterations").set(3)
    try:
        g = node.geometry()
        print("  %-34s points=%6d prims=%6d 一辺=%.5f"
              % (label, len(g.points()), len(g.prims()), g.boundingBox().sizevec()[0]))
    except hou.Error as exc:
        print("  %-34s エラー: %s" % (label, exc))
    node.destroy()

# --- 追加検証4: Mantra-Compatible は極限曲面を直接評価しているのか
# 検証3で Mantra-Compatible の一辺 0.83951 が、検証2の収束列から外挿した極限値と
# 一致した。もし極限曲面を直接評価しているなら、回数を変えても一辺は変わらないはず。
print("\n== 追加検証4: 回数を変えたときの一辺の比較 ==")
print("iter   OpenSubdiv CC   Mantra-Compatible")
for n in range(1, 6):
    sizes = []
    for algorithm in (2, 1):
        node = geo.createNode("subdivide", f"cmp_{algorithm}_{n}")
        node.setFirstInput(box)
        node.parm("algorithm").set(algorithm)
        node.parm("iterations").set(n)
        sizes.append(node.geometry().boundingBox().sizevec()[0])
        node.destroy()
    print("%4d   %13.5f   %17.5f" % (n, sizes[0], sizes[1]))
