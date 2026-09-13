"""落ちた水が溜まる絵を撮る。

床を置かないと粒はコンテナの下から抜けて消えるだけで、溜まらない。
ソルバの useground を入れて、コンテナの底に床を置く。
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SEP = 0.07
BOX = 3.0
FRAMES = list(range(1, 73, 3))

hou.hipFile.clear(suppress_save_prompt=True)
geo = hou.node("/obj").createNode("geo", "flip")

container = geo.createNode("flipcontainer", "container")
container.parmTuple("size").set((BOX, BOX, BOX))
container.parm("particlesep").set(SEP)

box = geo.createNode("box", "blob")
box.parmTuple("size").set((0.9, 0.9, 0.9))
box.parmTuple("t").set((0.0, 1.0, 0.0))

src = geo.createNode("flipsource", "src")
src.setInput(0, box)
src.parm("particlesep").set(SEP)
src.parm("volumename").set("source")

merge = geo.createNode("merge", "merge_sources")
merge.setInput(0, container, 0)
merge.setInput(1, src)

solver = geo.createNode("flipsolver", "solver")
solver.parm("particlesep").set(SEP)
solver.parm("donarrowband").set(False)
solver.parm("useground").set(True)
solver.parm("ground_posy").set(-BOX / 2.0)
solver.setInput(0, merge)
solver.setInput(1, container, 1)
solver.setInput(2, container, 2)
solver.setDisplayFlag(True)
solver.setRenderFlag(True)

print("床あり。粒の数を追う")
counts = []
for frame in FRAMES:
    hou.setFrame(frame)
    g = solver.geometry(0)
    counts.append(0 if g is None else len(g.points()))
print("  " + " ".join(f"F{f}:{c}" for f, c in zip(FRAMES, counts)))

bbox = hou.BoundingBox(-BOX / 2, -BOX / 2, -BOX / 2, BOX / 2, BOX / 2, BOX / 2)
paths = hou_tools.render_sequence(solver.path(), OUT, "019_pool", FRAMES,
                                  res=(420, 320), shading="smooth",
                                  frame_bbox=bbox)
print(f"  {len(paths)} 枚")

with open(os.path.join(OUT, "019_pool.json"), "w", encoding="utf-8") as fp:
    json.dump({"frames": FRAMES, "counts": counts, "sep": SEP}, fp,
              ensure_ascii=False, indent=2)

hou_tools.write_graph(geo.path(), os.path.join(OUT, "019_graph.json"),
                      title="実験019 — FLIP 液体")
hou_tools.save_hip(os.path.join(OUT, "019_flip.hipnc"))
print("保存: out/019_pool.json")
