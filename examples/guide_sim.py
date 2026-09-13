"""手順ページ用の画像（エフェクト編）。1つずつ別プロセスで動かす。

  rbd    … 箱を砕いて落とす（実験014）
  cloth  … 布を垂らす（実験015）
  smoke  … 煙を出す（実験016・021）
  liquid … 水を落とす（実験019）
  pop    … 粒を降らせる（実験020）

各段を同じカメラで撮る。段が進むと何が増えたかがそのまま見える。

    hython examples/guide_sim.py rbd
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (560, 440)


def shoot(sop, name, bbox=None, shading="smoothwire", frame=None):
    if frame is not None:
        hou.setFrame(frame)
    path = os.path.join(OUT, f"{name}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             frame_bbox=bbox)
    geo = sop.geometry()
    print(f"  {name}: {len(geo.points())}点 / {len(geo.prims())}面")
    return path


def rbd():
    """箱を砕いて落とす。箱 → 破片 → 落とす。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "rbd")

    box = geo.createNode("box", "block")
    box.parm("scale").set(2.0)
    box.parmTuple("t").set((0.0, 2.0, 0.0))

    fracture = geo.createNode("rbdmaterialfracture", "fracture")
    fracture.setFirstInput(box)
    fracture.parm("materialtype").set("concrete")

    solver = geo.createNode("rbdbulletsolver", "solver")
    solver.setFirstInput(fracture)
    solver.parm("useground").set(True)
    solver.parm("startframe").set(1)

    unpack = geo.createNode("unpack", "unpack")
    unpack.setFirstInput(solver)

    geo.layoutChildren()
    bbox = hou.BoundingBox(-3.0, -0.4, -3.0, 3.0, 3.4, 3.0)
    shoot(box, "guide_rbd_1_box", bbox, frame=1)
    shoot(fracture, "guide_rbd_2_fracture", bbox, frame=1)
    shoot(unpack, "guide_rbd_3_fall", bbox, frame=14)
    shoot(unpack, "guide_rbd_4_land", bbox, frame=48)
    hou_tools.save_hip(os.path.join(OUT, "guide_rbd.hipnc"))


def cloth():
    """布を垂らす。板 → 留める点 → 拘束 → 解く。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "cloth")

    sheet = geo.createNode("grid", "sheet")
    sheet.parm("sizex").set(4.0)
    sheet.parm("sizey").set(4.0)
    sheet.parm("rows").set(30)
    sheet.parm("cols").set(30)
    sheet.parmTuple("t").set((0.0, 3.0, 0.0))

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(sheet)
    pins.parm("class").set(2)
    pins.parm("snippet").set("if (abs(@P.x) > 1.9) { @group_pins = 1; }")

    constraints = geo.createNode("vellumconstraints", "constraints")
    constraints.setFirstInput(pins)
    constraints.parm("constrainttype").set("cloth")

    pinning = geo.createNode("vellumconstraints", "pinning")
    pinning.setInput(0, constraints, 0)
    pinning.setInput(1, constraints, 1)
    pinning.parm("constrainttype").set("pin")
    pinning.parm("grouptype").set("points")
    pinning.parm("group").set("pins")

    solver = geo.createNode("vellumsolver", "solver")
    solver.setInput(0, pinning, 0)
    solver.setInput(1, pinning, 1)
    solver.parm("startframe").set(1)

    geo.layoutChildren()
    bbox = hou.BoundingBox(-2.4, -1.6, -2.4, 2.4, 3.6, 2.4)
    shoot(sheet, "guide_cloth_1_sheet", bbox, frame=1)
    shoot(pins, "guide_cloth_2_pins", bbox, frame=1)
    shoot(solver, "guide_cloth_3_start", bbox, frame=6)
    shoot(solver, "guide_cloth_4_hang", bbox, frame=60)
    hou_tools.save_hip(os.path.join(OUT, "guide_cloth.hipnc"))


def smoke():
    """煙を出す。発生源 → ボリューム化 → 解く。温度を忘れない。"""
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
    src.parm("attributes").set(2)
    src.parm("attribute1").set("density")
    src.parm("attribute2").set("temperature")

    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    rast.parm("attributes").set("density temperature")
    rast.parm("voxelsize").set(0.05)

    solver = geo.createNode("pyrosolver", "solver")
    solver.setFirstInput(rast)

    geo.layoutChildren()
    bbox = hou.BoundingBox(-2.4, -2.4, -2.4, 2.4, 15.2, 2.4)
    shoot(emitter, "guide_smoke_1_emitter", bbox, shading="smooth", frame=1)
    shoot(rast, "guide_smoke_2_volume", bbox, shading="smooth", frame=1)
    shoot(solver, "guide_smoke_3_rise", bbox, shading="smooth", frame=20)
    shoot(solver, "guide_smoke_4_grown", bbox, shading="smooth", frame=46)
    hou_tools.save_hip(os.path.join(OUT, "guide_smoke.hipnc"))


def liquid():
    """水を落とす。器 → 湧き出し口 → 解く。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "liquid")
    sep = 0.07
    box_size = 3.0

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((box_size, box_size, box_size))
    container.parm("particlesep").set(sep)

    blob = geo.createNode("box", "blob")
    blob.parmTuple("size").set((0.9, 0.9, 0.9))
    blob.parmTuple("t").set((0.0, 1.0, 0.0))

    src = geo.createNode("flipsource", "src")
    src.setFirstInput(blob)
    src.parm("particlesep").set(sep)
    src.parm("volumename").set("source")     # 名前が役割を決める

    merge = geo.createNode("merge", "merge_sources")
    merge.setInput(0, container, 0)
    merge.setInput(1, src)

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(sep)
    solver.parm("donarrowband").set(False)
    solver.parm("useground").set(True)
    solver.parm("ground_posy").set(-box_size / 2.0)
    solver.setInput(0, merge)
    solver.setInput(1, container, 1)
    solver.setInput(2, container, 2)

    geo.layoutChildren()
    bbox = hou.BoundingBox(-box_size / 2, -box_size / 2, -box_size / 2,
                           box_size / 2, box_size / 2, box_size / 2)
    shoot(blob, "guide_liquid_1_blob", bbox, shading="smooth", frame=1)
    shoot(solver, "guide_liquid_2_start", bbox, shading="smooth", frame=6)
    shoot(solver, "guide_liquid_3_fall", bbox, shading="smooth", frame=22)
    shoot(solver, "guide_liquid_4_pool", bbox, shading="smooth", frame=58)
    hou_tools.save_hip(os.path.join(OUT, "guide_liquid.hipnc"))


def pop():
    """粒を降らせる。発生元 → DOPネットワーク → 取り出す。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "pop")

    emitter = geo.createNode("grid", "emitter")
    emitter.parmTuple("size").set((1.0, 1.0))
    emitter.parm("rows").set(10)
    emitter.parm("cols").set(10)
    emitter.parmTuple("t").set((0.0, 3.0, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    force = dop.createNode("popforce", "gravity")
    source.parm("soppath").set(emitter.path())
    source.parm("constantactivate").set(True)
    source.parm("constantrate").set(200)
    source.parm("impulseactiveate").set(False)
    force.parmTuple("force").set((0.0, -9.80665, 0.0))
    solver.setInput(0, obj)
    solver.setInput(1, source)
    solver.setInput(2, force)
    solver.setDisplayFlag(True)

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")          # 空だと1点も読めない

    geo.layoutChildren()
    bbox = hou.BoundingBox(-1.6, -4.5, -1.6, 1.6, 3.4, 1.6)
    shoot(emitter, "guide_pop_1_emitter", bbox, frame=1)
    shoot(imp, "guide_pop_2_birth", bbox, shading="smooth", frame=6)
    shoot(imp, "guide_pop_3_fall", bbox, shading="smooth", frame=26)
    shoot(imp, "guide_pop_4_stream", bbox, shading="smooth", frame=54)
    hou_tools.save_hip(os.path.join(OUT, "guide_pop.hipnc"))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "rbd"
    print(which)
    {"rbd": rbd, "cloth": cloth, "smoke": smoke,
     "liquid": liquid, "pop": pop}[which]()
    print("完了:", which)
