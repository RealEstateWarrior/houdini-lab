"""実験089 — 落ち葉を地面に積もらせる。当たったあとの振る舞いで、積もり方はどう変わるか。

実験086の舞う葉に地面（groundplane）を足し、popsolver の Response を変えて比べる。
「積もる」とは、地面の近くで止まっていること。止まったかどうかは速さで見る。

  A. Response を Unchanged / Stick / Slide の3通りで、3秒後の
     「地面の近くにいる数」「止まっている数」「散らばり」を測る
  B. 地面の Friction を 0 / 0.5 / 1 と変える（Response は Unchanged）

    hython examples/089_fallen_leaves.py a
    hython examples/089_fallen_leaves.py b
    hython examples/089_fallen_leaves.py shot stick
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 144        # 4秒では大半がまだ空中だった。6秒回す
COUNT = 400
NEAR = 0.12         # 地面からこの高さまでを「地面の近く」とみなす
SLOW = 0.05         # この速さより遅ければ「止まっている」


def build(response="none", friction=1.0, bounce=0.1, leaves=False):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "fallen")

    src_geo = geo.createNode("grid", "source_area")
    src_geo.parmTuple("size").set((2.0, 2.0))
    src_geo.parm("orient").set("zx")
    src_geo.parmTuple("t").set((0.0, 2.5, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    source.parm("soppath").set(src_geo.path())
    source.parm("emittype").set("surface")
    source.parm("constantrate").set(COUNT / 2.0)      # 2秒で COUNT 個
    source.parm("constantactivate").setExpression("$FF <= 48")   # 最初の2秒だけ降らせる
    source.parm("impulseactiveate").set(False)
    source.parm("life").set(20.0)
    source.parm("initvel").set("set")
    for axis in "xyz":
        source.parm(f"var{axis}").set(0.2)

    grav = dop.createNode("popforce", "gravity")
    grav.parmTuple("force").set((0.0, -2.0, 0.0))

    wind = dop.createNode("popwind", "wind")
    wind.parmTuple("wind").set((1.0, 0.0, 0.0))
    wind.parm("windspeed").set(1.0)
    wind.parm("airresist").set(2.0)
    wind.parm("amp").set(2.0)
    wind.parm("swirlsize").set(2.0)
    wind.setFirstInput(grav)

    solver.setInput(0, obj)
    solver.setInput(1, wind)
    solver.setInput(2, source)
    solver.parm("collisionresponse").set(response)

    ground = dop.createNode("groundplane", "ground")
    ground.parm("friction").set(friction)
    ground.parm("bounce").set(bounce)
    merge = dop.createNode("merge", "merge")
    merge.setInput(0, ground)
    merge.setInput(1, solver)
    merge.setDisplayFlag(True)        # 地面まで計算させる（実験080）
    dop.layoutChildren()

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("particles")
    out = imp
    if leaves:
        aim = geo.createNode("attribwrangle", "aim")
        aim.setFirstInput(imp)
        aim.parm("class").set(2)
        aim.parm("snippet").set(
            "vector dir = (length(v@v) > 1e-4) ? normalize(v@v) : set(1, 0, 0);\n"
            "@N = dir;\n"
            "v@up = {0, 1, 0};")
        leaf = geo.createNode("grid", "leaf")
        leaf.parmTuple("size").set((0.16, 0.10))
        leaf.parm("orient").set("zx")
        leaf.parm("rows").set(2)
        leaf.parm("cols").set(2)
        copies = geo.createNode("copytopoints::2.0", "leaf_copies")
        copies.setInput(0, leaf)
        copies.setInput(1, aim)
        copies.parm("pack").set(1)
        floor = geo.createNode("grid", "floor_show")
        floor.parmTuple("size").set((14.0, 8.0))          # 風下（+x）まで床を広げる
        floor.parm("tx").set(4.0)
        both = geo.createNode("merge", "show")
        both.setInput(0, floor)
        both.setInput(1, copies)
        out = both
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    geo.layoutChildren()
    return geo, imp, out


def run(response="none", friction=1.0):
    import hou
    import hou_tools
    import numpy
    geo, imp, out = build(response, friction)
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        imp.geometry()
    sec = time.perf_counter() - start
    p = hou_tools.point_array(imp.geometry())
    v = hou_tools.point_array(imp.geometry(), "v")
    speed = numpy.linalg.norm(v, axis=1)
    near = p[:, 1] < NEAR
    still = speed < SLOW
    return {"response": response, "friction": friction, "count": int(len(p)),
            "near_ground": int(near.sum()), "still": int(still.sum()),
            "settled": int((near & still).sum()),
            "y_mean": float(p[:, 1].mean()), "y_min": float(p[:, 1].min()),
            "spread_x": float(p[:, 0].std()), "spread_z": float(p[:, 2].std()),
            "speed_mean": float(speed.mean()), "seconds": sec}


def show(r):
    print(f"   Response {r['response']:<9} 摩擦 {r['friction']:<4} | {r['count']}枚 | "
          f"地面の近く {r['near_ground']:>4} 止まっている {r['still']:>4} 積もった {r['settled']:>4} | "
          f"高さの平均 {r['y_mean']:.4f} | 散らばり 横 {r['spread_x']:.3f} 奥 {r['spread_z']:.3f} | "
          f"速さの平均 {r['speed_mean']:.4f} | {r['seconds']:.2f}秒")


def part_a():
    print("A. 当たったあとの振る舞い（摩擦 1・跳ね 0.1）")
    rows = []
    for response in ("none", "stuck", "slide"):
        r = run(response, 1.0)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "089_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/089_a.json")


def part_b():
    print("B. 地面の摩擦を変える（Response は Unchanged）")
    rows = []
    for friction in (0.0, 0.5, 1.0):
        r = run("none", friction)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "089_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/089_b.json")


def shot(response="stuck"):
    import hou
    import hou_tools
    geo, imp, out = build(response, 1.0, leaves=True)
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        out.geometry()
    if response == "stuck":
        hou_tools.save_hip(os.path.join(OUT, "089_leaves.hipnc"))
    bbox = hou.BoundingBox(-3.0, -0.05, -4.0, 11.0, 2.8, 4.0)
    png = os.path.join(OUT, f"089_fallen_{response}.png")
    hou_tools.render_preview(out.path(), png, res=(720, 400), direction=(0.15, 0.8, 1.0),
                             shading="smooth", frame_bbox=bbox, margin=1.03)
    print(f"保存: {png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "stuck")
    else:
        {"a": part_a, "b": part_b}[arg]()
