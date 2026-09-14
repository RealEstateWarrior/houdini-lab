"""手順ページ用の画像を作る — 「塊をぶつけて潰す（MPM）」（実験061〜067の内容）。

数字はすべて実験061〜067で実測したもの。
1プロセスで何度もシーンを組み直すと hython が止まるので、1枚ずつ別々に撮る。

    hython examples/guide_mpm.py box
    hython examples/guide_mpm.py particles
    hython examples/guide_mpm.py hit
    hython examples/guide_mpm.py sandy
    hython examples/guide_mpm.py surface
    hython examples/guide_mpm.py coarse
    hython examples/guide_mpm.py fine
    hython examples/guide_mpm.py all      （全部を子プロセスで順に）
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

RES = (640, 420)
PREFIX = "guide_mpm"
START_Y = 3.0
LAST = 30
SEP = 0.12

# 落ちる前（高いところ）、ぶつかったあと（地面のあたり）、
# 跳ね返りまで入れた縦長、の3通りで枠を分ける。
BOX_BBOX = (-0.9, 2.3, -0.9, 0.9, 3.7, 0.9)
HIT_BBOX = (-0.95, -0.10, -0.95, 0.95, 0.95, 0.95)
TALL_BBOX = (-1.1, -0.15, -1.1, 1.1, 3.05, 1.1)

# 既定は 1（Chunky）。materialpreset ではなくこちらが本体（実験062）
MATERIALS = {"elastic": 0, "chunky": 1, "liquid": 2, "viscous": 3, "sandy": 4}


def build(material="chunky", sep=SEP, friction=1.0):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "mpm")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    box.parmTuple("t").set((0.0, START_Y, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(sep)
    container.parm("sizex").set(8.0)
    container.parm("sizey").set(8.0)
    container.parm("sizez").set(8.0)
    container.parm("centery").set(2.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)
    # materialpreset ではなく materialtype が本体（実験062）
    source.parm("materialtype").set(MATERIALS[material])

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)
    # 地面は既定で y = 0 にある（実験066）。ここでは摩擦だけ決める
    solver.parm("groundactive").set(1)
    solver.parm("groundfriction").set(friction)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, box, source, solver


def shoot(sop, step, bbox, shading="smooth", margin=1.04):
    import hou
    import hou_tools
    path = os.path.join(OUT, f"{PREFIX}_{step}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             direction=(0.32, 0.26, 1.0),
                             frame_bbox=hou.BoundingBox(*bbox) if bbox else None,
                             margin=margin)
    g = sop.geometry()
    b = g.boundingBox()
    print(f"  {step}: {len(g.points())}点 / {len(g.prims())}プリミティブ "
          f"/ 広がり {b.sizevec()[0]:.4f} × {b.sizevec()[1]:.4f} "
          f"× {b.sizevec()[2]:.4f} → {path}")


def advance(solver, last=LAST):
    import hou
    for frame in range(1, last + 1):
        hou.setFrame(frame)
        solver.geometry()


def shot(which):
    import hou
    if which == "box":
        geo, box, source, solver = build()
        box.setDisplayFlag(True)
        box.setRenderFlag(True)
        hou.setFrame(1)
        shoot(box, "1_box", BOX_BBOX, shading="smoothwire")

    elif which == "particles":
        geo, box, source, solver = build()
        hou.setFrame(1)
        shoot(solver, "2_particles", BOX_BBOX)

    elif which == "hit":
        geo, box, source, solver = build()
        advance(solver)
        shoot(solver, "3_hit", HIT_BBOX)

    elif which == "sandy":
        # 砂は他より大きく広がるので、この1枚だけ枠を合わせ直す。
        # 同じ枠に収めると点が潰れて何も見えない。
        geo, box, source, solver = build(material="sandy")
        advance(solver)
        shoot(solver, "4_sandy", None, margin=1.06)

    elif which == "surface":
        geo, box, source, solver = build()
        advance(solver)
        surf = geo.createNode("mpmsurface", "surface")
        surf.setInput(0, solver)
        # 既定は Surface VDB。面が欲しいなら polygonmesh（実験063）
        surf.parm("outputtype").set("polygonmesh")
        conv = geo.createNode("convert", "to_poly")
        conv.setInput(0, surf)
        conv.parm("totype").set("poly")
        conv.setDisplayFlag(True)
        conv.setRenderFlag(True)
        shoot(conv, "5_surface", HIT_BBOX, shading="smoothwire")

    elif which in ("bounce_elastic", "bounce_chunky"):
        material = which.split("_")[1]
        step = "8_elastic" if material == "elastic" else "9_chunky"
        geo, box, source, solver = build(material=material)
        advance(solver)
        shoot(solver, step, TALL_BBOX)

    elif which in ("coarse", "fine"):
        sep = 0.20 if which == "coarse" else 0.07
        step = "6_coarse" if which == "coarse" else "7_fine"
        geo, box, source, solver = build(sep=sep)
        advance(solver)
        shoot(solver, step, HIT_BBOX)

    elif which == "hip":
        geo, box, source, solver = build()
        surf = geo.createNode("mpmsurface", "surface")
        surf.setInput(0, solver)
        surf.parm("outputtype").set("polygonmesh")
        conv = geo.createNode("convert", "to_poly")
        conv.setInput(0, surf)
        conv.parm("totype").set("poly")
        conv.setDisplayFlag(True)
        conv.setRenderFlag(True)
        geo.layoutChildren()
        path = os.path.join(OUT, "guide_mpm.hipnc")
        hou.hipFile.save(path)
        print(f"保存: {path}")

    else:
        raise SystemExit(f"知らない指定: {which}")


def all_of():
    hython = sys.executable
    here = os.path.abspath(__file__)
    for which in ("box", "particles", "hit", "sandy", "surface",
                  "coarse", "fine", "bounce_elastic", "bounce_chunky"):
        print(f"--- {which}")
        subprocess.run([hython, here, which], check=True)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "all":
        all_of()
    else:
        shot(arg)
