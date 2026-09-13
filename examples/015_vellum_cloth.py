"""Vellum で布を落とす。布で保存されるべき量は何か。

剛体では体積が保たれた（実験014）。布は面なので体積では測れない。
代わりに「辺の長さの合計」を見る。布は伸びにくい素材なので、
たわんでも落ちても、辺の長さの合計はほぼ変わらないはず。

さらに、伸びにくさ（stretchstiffness）を下げれば、その保存が崩れるはず。
崩れ方を測れば、指標が本当に伸びを捉えているかを確かめられる。
"""

import json
import os
import sys
import time

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
FRAMES = list(range(1, 61, 4))          # 1〜57 を4コマおき、15枚
CHECK_FRAMES = (1, 5, 15, 30, 45, 57)

geo = hou.node("/obj").createNode("geo", "vellum_test")

cloth = geo.createNode("grid", "cloth")
cloth.parm("sizex").set(4.0)
cloth.parm("sizey").set(4.0)
cloth.parm("rows").set(30)
cloth.parm("cols").set(30)
cloth.parmTuple("t").set((0, 3.0, 0))

collider = geo.createNode("sphere", "collider")
collider.parm("type").set(1)
collider.parmTuple("rad").set((1.2, 1.2, 1.2))
collider.parmTuple("t").set((0, 1.0, 0))


def edge_length(geometry):
    """辺の長さの合計。布がどれだけ伸びたかの目安になる。"""
    total = 0.0
    for prim in geometry.prims():
        points = [v.point().position() for v in prim.vertices()]
        for i in range(len(points)):
            total += (points[i] - points[(i + 1) % len(points)]).length()
    return total


def area_of(geometry):
    return sum(p.intrinsicValue("measuredarea") for p in geometry.prims())


rest = cloth.geometry()
rest_edges = edge_length(rest)
rest_area = area_of(rest)
print("== 布の初期状態 ==")
print(f"  {len(rest.points())}点 / {len(rest.prims())}面")
print(f"  辺の長さの合計 {rest_edges:.5f} / 面積 {rest_area:.5f}")


# 両端をピンで留めるためのグループ。布を吊るすと自重で張力がかかる。
pins = geo.createNode("attribwrangle", "make_pins")
pins.setFirstInput(cloth)
pins.parm("snippet").set('if (abs(@P.x) > 1.9) { @group_pins = 1; }')


def build(name, stiffness, pinned):
    source = pins if pinned else cloth
    constraints = geo.createNode("vellumconstraints", f"con_{name}")
    constraints.setFirstInput(source)
    constraints.parm("constrainttype").set("cloth")
    constraints.parm("stretchstiffness").set(stiffness)

    if pinned:
        pinning = geo.createNode("vellumconstraints", f"pin_{name}")
        pinning.setInput(0, constraints, 0)
        pinning.setInput(1, constraints, 1)
        pinning.parm("constrainttype").set("pin")
        # grouptype の既定はプリミティブなので、点のグループを渡すなら
        # 先に points へ切り替える。さらに group を空のままにすると
        # 「全部が対象」と解釈され、布全体がピン留めされて一切動かなくなる。
        pinning.parm("grouptype").set("points")
        pinning.parm("group").set("pins")
        constraints = pinning

    solver = geo.createNode("vellumsolver", f"solve_{name}")
    solver.setInput(0, constraints, 0)
    solver.setInput(1, constraints, 1)
    if not pinned:
        solver.setInput(2, collider, 0)
        solver.parm("useground").set(True)
    solver.parm("startframe").set(1)
    return constraints, solver


CONFIGS = (
    ("たわむ・かたい", 1.0, False, "drape_stiff"),
    ("たわむ・やわらかい", 0.02, False, "drape_soft"),
    ("吊るす・かたい", 1.0, True, "hang_stiff"),
    ("吊るす・やわらかい", 0.02, True, "hang_soft"),
)

runs = []
for label, stiffness, pinned, name in CONFIGS:
    constraints, solver = build(name, stiffness, pinned)

    print(f"\n== {label}（stretchstiffness = {stiffness}）==")
    print("%8s %10s %14s %12s %12s %10s"
          % ("フレーム", "点数", "辺の長さ", "伸び率", "最下点", "計算秒"))
    rows = []
    for frame in CHECK_FRAMES:
        started = time.perf_counter()
        hou.setFrame(frame)
        g = solver.geometry()
        elapsed = time.perf_counter() - started
        if g is None or not len(g.points()):
            print(f"{frame:8d}  ジオメトリが無い")
            continue
        edges = edge_length(g)
        rows.append({"frame": frame, "points": len(g.points()),
                     "edges": round(edges, 5),
                     "ratio": round(edges / rest_edges, 5),
                     "area_ratio": round(area_of(g) / rest_area, 5),
                     "lowest": round(g.boundingBox().minvec()[1], 4),
                     "seconds": round(elapsed, 2)})
        print("%8d %10d %14.5f %12.5f %12.4f %10.2f"
              % (frame, len(g.points()), edges, edges / rest_edges,
                 g.boundingBox().minvec()[1], elapsed))
    runs.append({"label": label, "stiffness": stiffness, "pinned": pinned,
                 "rows": rows, "node": solver})
    hou.setFrame(1)

print("\n== 検証: 伸び率の比較 ==")
print("%-22s %10s %10s" % ("条件", "最大の伸び率", "伸びた割合"))
for run in runs:
    if not run["rows"]:
        continue
    ratios = [r["ratio"] for r in run["rows"]]
    print("%-22s %10.5f %9.3f%%"
          % (run["label"], max(ratios), (max(ratios) - 1.0) * 100))

# --- かたさが効かない。指数側のパラメータを含めて広く振ってみる。
probe_con = geo.createNode("vellumconstraints", "probe_stiff")
print("\n== かたさ関連の既定値 ==")
for name in ("stretchstiffness", "stretchstiffnessexp", "compressstiffness",
             "stretchdampingratio", "bendstiffness"):
    parm = probe_con.parm(name)
    if parm is not None:
        print(f"  {name} = {parm.eval()!r}")
probe_con.destroy()

print("\n== 吊るした布で、かたさを大きく振る ==")
print("%14s %8s %14s %12s" % ("stiffness", "exp", "最後の伸び率", "最下点"))
sweep_rows = []
for stiffness, exponent in ((1.0, 0), (1.0, -6), (1.0, 6),
                            (0.000001, 0), (1000000.0, 0)):
    tag = f"{str(stiffness).replace('.', '_')}_{exponent}"
    constraints = geo.createNode("vellumconstraints", f"sw_con_{tag}")
    constraints.setFirstInput(pins)
    constraints.parm("constrainttype").set("cloth")
    constraints.parm("stretchstiffness").set(stiffness)
    if constraints.parm("stretchstiffnessexp") is not None:
        constraints.parm("stretchstiffnessexp").set(exponent)

    pinning = geo.createNode("vellumconstraints", f"sw_pin_{tag}")
    pinning.setInput(0, constraints, 0)
    pinning.setInput(1, constraints, 1)
    pinning.parm("constrainttype").set("pin")
    pinning.parm("grouptype").set("points")
    pinning.parm("group").set("pins")

    solver = geo.createNode("vellumsolver", f"sw_solve_{tag}")
    solver.setInput(0, pinning, 0)
    solver.setInput(1, pinning, 1)
    solver.parm("startframe").set(1)

    hou.setFrame(57)
    g = solver.geometry()
    ratio = edge_length(g) / rest_edges
    lowest = g.boundingBox().minvec()[1]
    sweep_rows.append({"stiffness": stiffness, "exp": exponent,
                       "ratio": round(ratio, 5), "lowest": round(lowest, 4)})
    print("%14g %8d %14.5f %12.4f" % (stiffness, exponent, ratio, lowest))
    for victim in (solver, pinning, constraints):
        victim.destroy()
hou.setFrame(1)

stiff_node = runs[2]["node"] if len(runs) > 2 else runs[0]["node"]
started = time.perf_counter()
paths = hou_tools.render_sequence(stiff_node.path(), OUT, "015_cloth", FRAMES,
                                  res=(400, 320), direction=(1.0, 0.45, 1.1))
render_seconds = time.perf_counter() - started
print(f"\n  {len(paths)}枚を {render_seconds:.1f}秒で書き出した")

hou.setFrame(1)
geo.layoutChildren()
graph = hou_tools.write_graph("/obj/vellum_test",
                              os.path.join(OUT, "015_graph.json"),
                              title="Vellum クロス")
with open(os.path.join(OUT, "015_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"rest": {"points": len(rest.points()), "prims": len(rest.prims()),
                        "edges": round(rest_edges, 5),
                        "area": round(rest_area, 5)},
               "runs": [{"label": r["label"], "stiffness": r["stiffness"],
                         "rows": r["rows"]} for r in runs],
               "sweep": sweep_rows,
               "render_seconds": round(render_seconds, 1)},
              fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "015_vellum.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
