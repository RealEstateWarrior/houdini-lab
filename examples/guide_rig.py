"""手順ページ用の画像を作る — 「骨を入れて動かす」（実験051〜054の内容）。

骨を組み、皮を結び付け、曲げる。数字はすべて実験051〜054で実測したもの。

    hython examples/guide_rig.py
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 420)
PREFIX = "guide_rig"
SKIN_ROWS = 60
SKIN_COLS = 24
SKIN_RADIUS = 0.32
ANGLE = 90.0

JOINTS_VEX = """
int prim = addprim(0, "polyline");
for (int i = 0; i < 3; i++) {
    int pt = addpoint(0, set(0.0, float(i), 0.0));
    setpointattrib(0, "name", pt, sprintf("joint%d", i));
    addvertex(0, prim, pt);
}
"""

POSE_VEX = """
if (s@name == "joint1") {
    matrix m = 4@localtransform;
    // prerotate は「先に回してから動かす」。
    // rotate だと関節そのものが原点のまわりを回ってしまう。
    prerotate(m, radians(ch("angle")), set(0, 0, 1));
    4@localtransform = m;
}
"""


def shoot(sop, step, bbox, shading="smoothwire"):
    path = os.path.join(OUT, f"{PREFIX}_{step}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             frame_bbox=bbox, margin=1.05)
    geo = sop.geometry()
    print(f"  {step}: {len(geo.points())}点 / "
          f"{len(geo.prims())}プリミティブ → {path}")


def main():
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "rig")

    # 1. 骨を組む
    make = geo.createNode("attribwrangle", "make_joints")
    make.parm("class").set(0)
    make.parm("snippet").set(JOINTS_VEX)

    # 2. 足りない属性を埋める
    doc = geo.createNode("kinefx::rigdoctor", "doctor")
    doc.setFirstInput(make)
    doc.parm("transformations").set(1)
    doc.parm("inittransforms").set(1)
    doc.parm("outputparentidx").set(1)

    # 3. 関節を回す
    pose = geo.createNode("kinefx::rigattribwrangle", "pose")
    pose.setFirstInput(doc)
    pose.parm("class").set(2)
    pose.parm("snippet").set(POSE_VEX)
    ptg = pose.parmTemplateGroup()
    ptg.append(hou.FloatParmTemplate("angle", "angle", 1,
                                     default_value=(ANGLE,)))
    pose.setParmTemplateGroup(ptg)
    pose.parm("angle").set(ANGLE)

    # 4. 皮を用意する
    skin = geo.createNode("tube", "skin")
    skin.parm("type").set(1)
    skin.parm("rad1").set(SKIN_RADIUS)
    skin.parm("rad2").set(SKIN_RADIUS)
    skin.parm("height").set(2.0)
    skin.parm("rows").set(SKIN_ROWS)
    skin.parm("cols").set(SKIN_COLS)
    skin.parm("ty").set(1.0)
    skin.parm("cap").set(1)

    # 5. 結び付ける
    capture = geo.createNode("kinefx::jointcaptureproximity", "capture")
    capture.setInput(0, skin)
    capture.setInput(1, doc)

    # 6. 皮を動かす（既定の Linear）
    linear = geo.createNode("kinefx::jointdeform", "deform_linear")
    linear.setInput(0, capture)
    linear.setInput(1, doc)
    linear.setInput(2, pose)

    # 7. 痩せないようにする
    dq = geo.createNode("kinefx::jointdeform", "deform_dq")
    dq.setInput(0, capture)
    dq.setInput(1, doc)
    dq.setInput(2, pose)
    dq.parm("method").set("dualquat")
    dq.setDisplayFlag(True)
    dq.setRenderFlag(True)

    # 骨を見せるための飾り
    wire = geo.createNode("polywire", "bones")
    wire.setFirstInput(pose)
    wire.parm("radius").set(0.05)
    rest_wire = geo.createNode("polywire", "bones_rest")
    rest_wire.setFirstInput(doc)
    rest_wire.parm("radius").set(0.05)
    geo.layoutChildren()

    bbox = hou.BoundingBox(-1.5, -0.3, -0.6, 0.8, 2.3, 0.6)
    print("各段を同じカメラで撮る")
    shoot(rest_wire, "1_bones", bbox)
    shoot(wire, "2_posed", bbox)
    shoot(skin, "3_skin", bbox)
    shoot(linear, "4_linear", bbox)
    shoot(dq, "5_dualquat", bbox)

    hou_tools.write_graph(geo.path(),
                          os.path.join(OUT, f"{PREFIX}_graph.json"),
                          title="手順 — 骨を入れて動かす")
    hou_tools.save_hip(os.path.join(OUT, f"{PREFIX}.hipnc"))
    print("保存:", f"out/{PREFIX}.hipnc")


if __name__ == "__main__":
    main()
