"""実験022の絵。粒・切り取りなしの面・切り取りありの面を、同じカメラで撮る。"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SEP = 0.07
BOX = 3.0
FRAME = 40
RES = (440, 400)


def build():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "liquid")

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)

    blob = geo.createNode("box", "blob")
    blob.parmTuple("size").set((0.9, 0.9, 0.9))
    blob.parmTuple("t").set((0.0, 1.0, 0.0))

    src = geo.createNode("flipsource", "src")
    src.setFirstInput(blob)
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

    surface = geo.createNode("particlefluidsurface", "surface")
    surface.setFirstInput(solver)
    surface.parm("particlesep").set(SEP)

    convert = geo.createNode("convert", "to_polygons")
    convert.setFirstInput(surface)

    geo.layoutChildren()
    return geo, solver, surface, convert


def main():
    geo, solver, surface, convert = build()
    bbox = hou.BoundingBox(-BOX / 2, -BOX / 2, -BOX / 2, BOX / 2, BOX / 2, BOX / 2)

    hou.setFrame(FRAME)
    hou_tools.render_preview(solver.path(), os.path.join(OUT, "022_particles.png"),
                             res=RES, shading="smooth", frame_bbox=bbox)
    print("粒:", len(solver.geometry(0).points()), "個")

    surface.parm("dobbox").set(False)
    hou.setFrame(FRAME)
    hou_tools.render_preview(convert.path(), os.path.join(OUT, "022_open.png"),
                             res=RES, shading="smooth", frame_bbox=bbox)
    print("切り取りなしの面:", len(convert.geometry().prims()), "面")

    surface.parm("dobbox").set(True)
    for axis in ("x", "y", "z"):
        surface.parm(f"size{axis}").set(BOX)
        surface.parm(f"t{axis}").set(0.0)
    surface.parm("closedends").set(True)
    hou.setFrame(FRAME)
    hou_tools.render_preview(convert.path(), os.path.join(OUT, "022_clipped.png"),
                             res=RES, shading="smooth", frame_bbox=bbox)
    print("切り取りありの面:", len(convert.geometry().prims()), "面")

    hou_tools.write_graph(geo.path(), os.path.join(OUT, "022_graph.json"),
                          title="実験022 — 液体に表面を張る")
    hou_tools.save_hip(os.path.join(OUT, "022_surface.hipnc"))
    print("保存: out/022_graph.json, out/022_surface.hipnc")


if __name__ == "__main__":
    main()
