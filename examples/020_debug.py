"""粒が0のまま。どこで止まっているのかを1段ずつ見る。

見るところ
  1. DOPネットワークの中にオブジェクトが出来ているか
  2. そのオブジェクトが粒を持っているか
  3. dopimport が読めているか
"""

import hou

hou.hipFile.clear(suppress_save_prompt=True)
geo = hou.node("/obj").createNode("geo", "pop_test")

src_geo = geo.createNode("grid", "emitter")
src_geo.parmTuple("size").set((1.0, 1.0))
src_geo.parm("rows").set(10)
src_geo.parm("cols").set(10)
src_geo.parmTuple("t").set((0.0, 3.0, 0.0))

dop = geo.createNode("dopnet", "popnet")
obj = dop.createNode("popobject", "particles")
solver = dop.createNode("popsolver", "solver")
source = dop.createNode("popsource", "source")
force = dop.createNode("popforce", "gravity")

source.parm("soppath").set(src_geo.path())
source.parm("constantactivate").set(True)
source.parm("constantrate").set(200)
force.parmTuple("force").set((0.0, -9.80665, 0.0))

solver.setInput(0, obj)
solver.setInput(1, source)
solver.setInput(2, force)
solver.setDisplayFlag(True)

print("popsource の主なパラメータ")
for name in ("emittype", "soppath", "constantactivate", "constantrate",
             "impulseactiveate", "impulserate", "sourcegrouptype"):
    parm = source.parm(name)
    if parm is not None:
        print(f"  {name} = {parm.eval()!r}  disabled={parm.isDisabled()}")

print("\npopobject の主なパラメータ")
names = [p.name() for p in obj.parms()]
print("  sop/geo に関係するもの:",
      [n for n in names if any(k in n.lower() for k in ("sop", "geo", "path"))][:12])

for frame in (1, 2, 5, 10, 20):
    hou.setFrame(frame)
    sim = dop.simulation()
    objects = sim.objects()
    line = f"F{frame:3d}: DOPオブジェクト {len(objects)}"
    for o in objects:
        geo_data = o.geometry()
        pts = len(geo_data.points()) if geo_data else -1
        line += f" [{o.name()}: {pts}点]"
    print(line)

print("\ndopimport のパラメータ")
imp = geo.createNode("dopimport", "import")
imp.parm("doppath").set(dop.path())
for name in ("importstyle", "doppath", "objectpattern", "datapath"):
    parm = imp.parm(name)
    if parm is not None:
        print(f"  {name} = {parm.eval()!r}")
print("  全パラメータ:", [p.name() for p in imp.parms()][:20])
