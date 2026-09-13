"""pyrosolver のどの出力に、動いている密度が入っているのかを見る。

合計は増えているのに、中身のあるボクセル数と ばらつきが全フレーム同じだった。
煙が昇って広がっているならありえない。読んでいる先が違う。
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

VOXEL = 0.05

hou.hipFile.clear(suppress_save_prompt=True)
geo = hou.node("/obj").createNode("geo", "smoke")

emitter = geo.createNode("sphere", "emitter")
emitter.parm("type").set(2)
emitter.parmTuple("rad").set((0.22, 0.22, 0.22))
emitter.parmTuple("t").set((0.0, -0.9, 0.0))
emitter.parm("rows").set(24)
emitter.parm("cols").set(24)

src = geo.createNode("pyrosource", "src")
src.setFirstInput(emitter)
src.parm("attributes").set(1)
src.parm("attribute1").set("density")

rast = geo.createNode("volumerasterizeattributes", "rasterize")
rast.setFirstInput(src)
rast.parm("attributes").set("density")
rast.parm("voxelsize").set(VOXEL)

solver = geo.createNode("pyrosolver", "solve")
solver.setFirstInput(rast)
solver.setDisplayFlag(True)

print("solver の出力:", solver.outputNames())
for frame in (5, 40):
    hou.setFrame(frame)
    print(f"--- フレーム {frame}")
    for index in range(len(solver.outputNames())):
        try:
            g = solver.geometry(index)
        except hou.Error as exc:
            print(f"  出力{index + 1}: エラー {exc}")
            continue
        if g is None:
            print(f"  出力{index + 1}: なし")
            continue
        vols = [p for p in g.prims() if p.type() == hou.primType.Volume]
        desc = []
        for p in vols[:6]:
            name = p.attribValue("name") if g.findPrimAttrib("name") else "?"
            res = p.resolution()
            desc.append(f"{name}{res}")
        print(f"  出力{index + 1}: プリミティブ{len(g.prims())} / "
              f"ボリューム{len(vols)} / {desc}")
    g = rast.geometry()
    print(f"  rasterize: プリミティブ{len(g.prims())} / "
          f"{[p.resolution() for p in g.prims() if p.type() == hou.primType.Volume]}")
