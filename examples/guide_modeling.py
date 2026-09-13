"""手順ページ用の画像をまとめて作る（モデリング編）。

4つの手順ぶんを1回のhythonで撮る。起動のたびに10秒ほどかかるので、まとめたほうが速い。

  terrain … 地形を作る（実験003〜007の内容）
  hard    … 硬い形を作る（実験012）
  smooth  … 丸くする・角を残す（実験002・011）
  vex     … VEX で点を動かす（実験009）

どの手順も、段が進むと何が増えたかがそのまま見えるように、同じカメラで撮る。

    hython examples/guide_modeling.py
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (620, 420)


def shoot(sop, name, bbox=None, shading="smoothwire"):
    path = os.path.join(OUT, f"{name}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             frame_bbox=bbox)
    geo = sop.geometry()
    print(f"  {name}: {len(geo.points())}点 / {len(geo.prims())}面")
    return path


def terrain():
    """地形を作る。平面 → 分割 → ノイズ → 種類を選ぶ。"""
    print("terrain")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "terrain")

    grid = geo.createNode("grid", "ground")
    grid.parmTuple("size").set((10.0, 10.0))
    grid.parm("rows").set(20)
    grid.parm("cols").set(20)

    dense = geo.createNode("grid", "ground_dense")
    dense.parmTuple("size").set((10.0, 10.0))
    dense.parm("rows").set(160)
    dense.parm("cols").set(160)

    rough_noise = geo.createNode("mountain::2.0", "rough_terrain")
    rough_noise.setFirstInput(grid)
    rough_noise.parm("height").set(1.2)
    rough_noise.parm("elementsize").set(4.0)

    fine = geo.createNode("mountain::2.0", "fine_terrain")
    fine.setFirstInput(dense)
    fine.parm("height").set(1.2)
    fine.parm("elementsize").set(4.0)

    detail = geo.createNode("mountain::2.0", "detail_terrain")
    detail.setFirstInput(dense)
    detail.parm("height").set(1.2)
    detail.parm("elementsize").set(1.2)
    detail.parm("rough").set(0.75)

    cells = geo.createNode("mountain::2.0", "cell_terrain")
    cells.setFirstInput(dense)
    cells.parm("height").set(1.2)
    cells.parm("elementsize").set(2.0)
    cells.parm("basis").set("worleyFA")   # Worley 系。岩っぽくなる

    geo.layoutChildren()
    bbox = hou_tools.bbox_union([fine.path(), detail.path(), cells.path()])
    shoot(grid, "guide_terrain_1_grid", bbox)
    shoot(rough_noise, "guide_terrain_2_coarse", bbox)
    shoot(fine, "guide_terrain_3_dense", bbox)
    shoot(detail, "guide_terrain_4_detail", bbox)
    shoot(cells, "guide_terrain_5_basis", bbox)
    hou_tools.save_hip(os.path.join(OUT, "guide_terrain.hipnc"))


def hard():
    """硬い形を作る。箱 → 穴を開ける → 面を一段くぼませる。"""
    print("hard")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "hard_surface")

    box = geo.createNode("box", "base")
    box.parmTuple("size").set((2.0, 1.0, 1.4))

    # 縦に貫く円柱。tube は既定で Y 軸に立つので、回さなくてよい
    cutter = geo.createNode("tube", "cutter")
    cutter.parm("type").set(1)
    cutter.parm("rad1").set(0.32)
    cutter.parm("rad2").set(0.32)
    cutter.parm("height").set(3.0)
    cutter.parm("cap").set(True)
    cutter.parm("cols").set(24)

    drill = geo.createNode("boolean::2.0", "drill")
    drill.setInput(0, box)
    drill.setInput(1, cutter)
    drill.parm("booleanop").set(2)          # 差（subtract）

    panel = geo.createNode("polyextrude::2.0", "panel")
    panel.setFirstInput(drill)
    panel.parm("dist").set(-0.08)           # 内側へ。面が一段くぼむ
    panel.parm("inset").set(0.12)

    geo.layoutChildren()
    bbox = hou_tools.bbox_union([box.path(), cutter.path()])
    shoot(box, "guide_hard_1_box", bbox)
    shoot(cutter, "guide_hard_2_cutter", bbox)
    shoot(drill, "guide_hard_3_boolean", bbox)
    shoot(panel, "guide_hard_4_panel", bbox)
    hou_tools.save_hip(os.path.join(OUT, "guide_hard.hipnc"))


def smooth():
    """丸くする、角を残す。箱 → 分割 → crease。"""
    print("smooth")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "smooth_shape")

    box = geo.createNode("box", "base")

    sub1 = geo.createNode("subdivide", "divide1")
    sub1.setFirstInput(box)
    sub1.parm("iterations").set(1)

    sub3 = geo.createNode("subdivide", "divide3")
    sub3.setFirstInput(box)
    sub3.parm("iterations").set(3)

    crease = geo.createNode("crease", "keep_edges")
    crease.setFirstInput(box)
    crease.parm("group").set("0-3")
    crease.parm("crease").set(3)

    sub_crease = geo.createNode("subdivide", "divide3_crease")
    sub_crease.setFirstInput(crease)
    sub_crease.parm("iterations").set(3)

    geo.layoutChildren()
    bbox = hou_tools.bbox_union([box.path(), sub3.path()])
    shoot(box, "guide_smooth_1_box", bbox)
    shoot(sub1, "guide_smooth_2_once", bbox)
    shoot(sub3, "guide_smooth_3_thrice", bbox)
    shoot(sub_crease, "guide_smooth_4_crease", bbox)
    hou_tools.save_hip(os.path.join(OUT, "guide_smooth.hipnc"))


def vex():
    """VEX で点を動かす。平面 → 波 → 色。"""
    print("vex")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "vex_wave")

    grid = geo.createNode("grid", "sheet")
    grid.parmTuple("size").set((10.0, 10.0))
    grid.parm("rows").set(120)
    grid.parm("cols").set(120)

    wave = geo.createNode("attribwrangle", "make_wave")
    wave.setFirstInput(grid)
    wave.parm("class").set(2)          # 点ごと
    wave.parm("snippet").set(
        "float d = length(@P);\n"
        "@P.y = sin(d * 2.0) * 0.6 / (1.0 + d * 0.25);")

    color = geo.createNode("attribwrangle", "make_color")
    color.setFirstInput(wave)
    color.parm("class").set(2)
    color.parm("snippet").set(
        "@Cd = set(0.25 + @P.y, 0.55, 0.95 - @P.y);")

    geo.layoutChildren()
    bbox = hou_tools.bbox_union([color.path()])
    shoot(grid, "guide_vex_1_grid", bbox)
    shoot(wave, "guide_vex_2_wave", bbox)
    shoot(color, "guide_vex_3_color", bbox)
    hou_tools.save_hip(os.path.join(OUT, "guide_vex.hipnc"))


if __name__ == "__main__":
    # 1プロセスで複数のシーンを作ると止まることがあるので、1つずつ動かす
    which = sys.argv[1] if len(sys.argv) > 1 else "terrain"
    {"terrain": terrain, "hard": hard, "smooth": smooth,
     "vex": vex}[which]()
    print("完了:", which)
