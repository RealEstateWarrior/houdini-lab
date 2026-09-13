"""「Sources チャンネルは名前付きのVDBを運んでいる」を確かめる。

コンテナの出力1は7つのVDBで、名前は
    source / sink / velsurface / guidingsurface / pressuresurface / vel / pressure

ヘルプには「Sources: 液体の粒を期待する」と書いてあるが、実際に流れているのは
粒ではなくVDBだった。だからタンクの3145点を入れても何も起きなかった。

仮説: このチャンネルでは<名前>が役割を決めている。
     source という名前のVDBを混ぜれば、そこから液体が湧くはず。

否定できる形: 名前を source 以外にしたら湧かないはず。両方試す。
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


def run(volume_name, label):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "flip_test")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.2, 1.2, 1.2))
    box.parmTuple("t").set((0.0, 0.8, 0.0))

    src = geo.createNode("flipsource", "src")
    src.setInput(0, box)
    src.parm("particlesep").set(SEP)
    if src.parm("volumename") is not None:
        src.parm("volumename").set(volume_name)

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((3.0, 3.0, 3.0))
    container.parm("particlesep").set(SEP)

    merge = geo.createNode("merge", "merge_sources")
    merge.setInput(0, container, 0)     # コンテナの Sources チャンネル
    merge.setInput(1, src)              # そこに VDB を1つ足す

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    solver.setInput(0, merge)
    solver.setInput(1, container, 1)
    solver.setInput(2, container, 2)

    hou.setFrame(1)
    try:
        solver.cook(force=True)
    except hou.Error:
        pass
    if solver.errors():
        print(f"{label:28s} エラー: {solver.errors()}")
        return

    names = sorted(p.attribValue("name") for p in merge.geometry().prims())
    counts = []
    for frame in (1, 5, 10, 20, 40):
        hou.setFrame(frame)
        counts.append(count(solver))
    print(f"{label:28s} " + "  ".join(f"F{f}:{c}" for f, c in
                                      zip((1, 5, 10, 20, 40), counts)))
    print(f"{'':28s} merge に流れたVDB: {names}")
    return solver, geo


print("flipsource の既定の Volume Name を確認")
hou.hipFile.clear(suppress_save_prompt=True)
probe = hou.node("/obj").createNode("geo", "probe").createNode("flipsource", "p")
print("  volumename =", probe.parm("volumename").eval() if probe.parm("volumename") else "なし")
print("  createparticles =",
      probe.parm("createparticles").eval() if probe.parm("createparticles") else "なし")

print("\n名前を変えて、液体が湧くかどうかを見る")
run("source", "A: 名前 = source")
run("surface", "B: 名前 = surface（既定）")
run("notasource", "C: 名前 = notasource")
