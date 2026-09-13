"""エラーは消えたが、液体の粒が1つも流れていない。

コンテナの出力1は7点しかなく、タンクの3145点が入っていない。
「どうやって液体を入れるのか」を切り分ける。

試す経路
  A. タンクの粒をコンテナの入力1へ（いまの形）
  B. ソルバの Waterline で水位から作らせる（タンクなし）
  C. flipsource（Create Particles 入り）をコンテナの入力1へ
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

SEP = 0.08


def count(node, index=0):
    try:
        geo = node.geometry(index)
    except hou.Error:
        return -1
    return -1 if geo is None else len(geo.points())


def fresh():
    hou.hipFile.clear(suppress_save_prompt=True)
    return hou.node("/obj").createNode("geo", "flip_test")


def wire(geo, source_node, waterline=False):
    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((3.0, 3.0, 3.0))
    container.parm("particlesep").set(SEP)
    if source_node is not None:
        container.setInput(0, source_node)

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    if waterline and solver.parm("dowaterline") is not None:
        solver.parm("dowaterline").set(True)
    for channel in range(3):
        solver.setInput(channel, container, channel)
    return container, solver


def report(tag, container, solver, source_node=None):
    hou.setFrame(1)
    try:
        solver.cook(force=True)
    except hou.Error:
        pass
    errors = solver.errors()
    line = (f"{tag:34s} 供給元 {count(source_node) if source_node else '—':>7} "
            f"→ コンテナ出力1 {count(container):6d} "
            f"→ ソルバ出力1 {count(solver):6d}")
    print(line + ("  エラー: " + str(errors) if errors else ""))
    if errors:
        return
    counts = []
    for frame in (1, 5, 20, 40):
        hou.setFrame(frame)
        counts.append(f"F{frame}:{count(solver)}")
    print(f"{'':34s} フレームごと: " + "  ".join(counts))


print("A. タンクの粒をコンテナの入力1へ")
geo = fresh()
tank = geo.createNode("particlefluidtank", "tank")
tank.parm("particlesep").set(SEP)
tank.parmTuple("size").set((1.4, 1.4, 1.4))
container, solver = wire(geo, tank)
report("A: tank → container", container, solver, tank)

print("\nB. Waterline で水位から作らせる（タンクなし）")
geo = fresh()
container, solver = wire(geo, None, waterline=True)
report("B: waterline", container, solver)

print("\nC. flipsource（粒を作る設定）をコンテナの入力1へ")
geo = fresh()
box = geo.createNode("box", "box")
box.parmTuple("size").set((1.4, 1.4, 1.4))
src = geo.createNode("flipsource", "src")
src.setInput(0, box)
src.parm("particlesep").set(SEP)
if src.parm("createparticles") is not None:
    src.parm("createparticles").set(True)
container, solver = wire(geo, src)
report("C: flipsource → container", container, solver, src)

print("\n参考: コンテナ単体の出力1が何なのか")
geo = fresh()
container = geo.createNode("flipcontainer", "container")
container.parm("particlesep").set(SEP)
hou.setFrame(1)
g = container.geometry(0)
print("  点数:", len(g.points()), "プリミティブ:", len(g.prims()))
print("  プリミティブの型:", sorted({p.type().name() for p in g.prims()}))
print("  点アトリビュート:", [a.name() for a in g.pointAttribs()])
print("  プリミティブ名:", [p.attribValue("name") if g.findPrimAttrib("name") else "?"
                            for p in g.prims()][:10])
