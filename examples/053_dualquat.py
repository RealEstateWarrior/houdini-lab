"""実験053 — 痩せない曲げ方はあるか。3つのやり方を比べる。

実験052で、骨を曲げると皮が痩せることを測った。
90度で 27.13%、しかも減り方は <strong>27.1284% × (1 − cos θ)</strong> という
きれいな式に乗っていた。

<code>kinefx::jointdeform</code> には混ぜ方が3つある。

    Linear（既定）／ Dual Quaternion ／ その2つの中間

同じ骨・同じ皮・同じ角度で、3つを撮り比べる。

  A. やり方ごとの体積の減り方
  B. Dual Quaternion にも式はあるか
  C. 何と引き換えになっているか（膨らみ・ねじれ）

    hython examples/053_dualquat.py
    hython examples/053_dualquat.py shot linear
    hython examples/053_dualquat.py shot dualquat
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

RES = (620, 620)
ANGLES = (0.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0)
METHODS = (("linear", "Linear（既定）"),
           ("dualquat", "Dual Quaternion"),
           ("blenddualquat", "2つの中間"))
SKIN_ROWS = 60
SKIN_COLS = 24
SKIN_RADIUS = 0.32

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
    prerotate(m, radians(ch("angle")), set(0, 0, 1));
    4@localtransform = m;
}
"""


def build(angle, method="linear"):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "rigskin")

    make = geo.createNode("attribwrangle", "make_joints")
    make.parm("class").set(0)
    make.parm("snippet").set(JOINTS_VEX)

    doc = geo.createNode("kinefx::rigdoctor", "doctor")
    doc.setFirstInput(make)
    doc.parm("transformations").set(1)
    doc.parm("inittransforms").set(1)
    doc.parm("outputparentidx").set(1)

    pose = geo.createNode("kinefx::rigattribwrangle", "pose")
    pose.setFirstInput(doc)
    pose.parm("class").set(2)
    pose.parm("snippet").set(POSE_VEX)
    if pose.parm("angle") is None:
        ptg = pose.parmTemplateGroup()
        ptg.append(hou.FloatParmTemplate("angle", "angle", 1,
                                         default_value=(0.0,)))
        pose.setParmTemplateGroup(ptg)
    pose.parm("angle").set(angle)

    skin = geo.createNode("tube", "skin")
    skin.parm("type").set(1)
    skin.parm("rad1").set(SKIN_RADIUS)
    skin.parm("rad2").set(SKIN_RADIUS)
    skin.parm("height").set(2.0)
    skin.parm("rows").set(SKIN_ROWS)
    skin.parm("cols").set(SKIN_COLS)
    skin.parm("ty").set(1.0)
    skin.parm("cap").set(1)

    # 「2つの中間」は、点ごとの混ぜ具合を表す属性が無いと動かない。
    # 半々（0.5）を全点に入れておく。
    blend = geo.createNode("attribwrangle", "dqblend")
    blend.setFirstInput(skin)
    blend.parm("class").set(2)
    blend.parm("snippet").set("f@dqblend = 0.5;")

    capture = geo.createNode("kinefx::jointcaptureproximity", "capture")
    capture.setInput(0, blend)
    capture.setInput(1, doc)

    deform = geo.createNode("kinefx::jointdeform", "deform")
    deform.setInput(0, capture)
    deform.setInput(1, doc)
    deform.setInput(2, pose)
    deform.parm("method").set(method)
    if method == "blenddualquat":
        deform.parm("dqblendattrib").set("dqblend")
    deform.setDisplayFlag(True)
    deform.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, doc, pose, deform


def measure(node):
    """体積と、断面の太さを測る。"""
    import numpy
    geo = node.geometry()
    total = 0.0
    for prim in geo.prims():
        pts = [v.point().position() for v in prim.vertices()]
        if len(pts) < 3:
            continue
        a = numpy.asarray([pts[0][0], pts[0][1], pts[0][2]])
        for i in range(1, len(pts) - 1):
            b = numpy.asarray([pts[i][0], pts[i][1], pts[i][2]])
            c = numpy.asarray([pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]])
            total += float(numpy.dot(a, numpy.cross(b, c))) / 6.0
    pts = numpy.asarray([[p.position()[0], p.position()[1], p.position()[2]]
                         for p in geo.points()])
    return abs(total), pts


def main():
    import numpy
    stats = {"angles": list(ANGLES)}

    geo, skin, doc, pose, deform = build(0.0)
    base, rest_pos = measure(deform)
    print(f"曲げる前の体積: {base:.6f}")
    stats["volume_rest"] = base

    print("\nA. やり方ごとの体積の減り方")
    print(f"   {'角度':>6}", end="")
    for _, label in METHODS:
        print(f" {label:>18}", end="")
    print()
    table = {key: [] for key, _ in METHODS}
    for angle in ANGLES:
        print(f"   {angle:>6.0f}", end="")
        for key, _ in METHODS:
            geo, skin, doc, pose, deform = build(angle, key)
            vol, _ = measure(deform)
            loss = (1 - vol / base) * 100
            table[key].append({"angle": angle, "volume": vol, "loss": loss})
            print(f" {loss:>17.4f}%", end="")
        print()
    stats["table"] = table

    print("\nB. それぞれ式に乗るか（減った分 ÷ (1 − cos θ)）")
    print(f"   {'角度':>6}", end="")
    for _, label in METHODS:
        print(f" {label:>18}", end="")
    print()
    for i, angle in enumerate(ANGLES):
        if not angle:
            continue
        print(f"   {angle:>6.0f}", end="")
        for key, _ in METHODS:
            loss = table[key][i]["loss"]
            print(f" {loss / (1 - math.cos(math.radians(angle))):>18.4f}",
                  end="")
        print()
    spreads = {}
    for key, label in METHODS:
        vals = [r["loss"] / (1 - math.cos(math.radians(r["angle"])))
                for r in table[key] if r["angle"]]
        spreads[key] = {"min": min(vals), "max": max(vals),
                        "spread": max(vals) - min(vals),
                        "mean": sum(vals) / len(vals)}
        print(f"   {label}: {min(vals):.4f} 〜 {max(vals):.4f}"
              f"（幅 {max(vals) - min(vals):.4f}）")
    stats["per_cos"] = spreads

    print("\nC. 中心からの太さ（90度のとき、高さの帯ごと）")
    print(f"   {'元の高さ':>12}", end="")
    for _, label in METHODS:
        print(f" {label:>18}", end="")
    print()
    radii = {key: [] for key, _ in METHODS}
    posed = {}
    for key, _ in METHODS:
        geo, skin, doc, pose, deform = build(90.0, key)
        _, pts = measure(deform)
        posed[key] = pts
    edges = [0.0, 0.5, 0.75, 1.0, 1.25, 1.5, 2.01]
    for lo, hi in zip(edges, edges[1:]):
        mask = (rest_pos[:, 1] >= lo) & (rest_pos[:, 1] < hi)
        if not mask.any():
            continue
        print(f"   {lo:.2f}〜{hi:.2f}  ", end="")
        for key, _ in METHODS:
            pts = posed[key][mask]
            centre = pts.mean(axis=0)
            r = float(numpy.linalg.norm(pts - centre, axis=1).mean())
            radii[key].append({"lo": lo, "hi": hi, "radius": r})
            print(f" {r:>18.6f}", end="")
        print()
    stats["radii"] = radii

    with open(os.path.join(OUT, "053_stats.json"), "w",
              encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    import hou_tools
    geo, skin, doc, pose, deform = build(90.0, "dualquat")
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "053_graph.json"),
                          title="実験053 — 痩せない曲げ方")
    hou_tools.save_hip(os.path.join(OUT, "053_dualquat.hipnc"))
    print("\n保存: out/053_stats.json, out/053_graph.json, "
          "out/053_dualquat.hipnc")


def shot(case):
    import hou
    import hou_tools
    geo, skin, doc, pose, deform = build(90.0, case)
    bbox = hou.BoundingBox(-1.6, -0.4, -0.6, 0.9, 2.4, 0.6)
    png = os.path.join(OUT, f"053_{case}.png")
    hou_tools.render_preview(deform.path(), png, res=RES,
                             direction=(0.0, 0.0, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.05)
    print(f"保存: out/053_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
