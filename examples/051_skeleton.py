"""実験051 — 骨を作って動かす。子の骨は、親の回転にどう付いてくるか。

実験050で APEX の入口を測った。今回はその手前にある骨組み（KineFX）を触る。

KineFX の骨は<strong>ただの点と線</strong>で持たれている。
点1つが関節1つ、線が親子のつながり。名前（<code>name</code>）を付けて
<code>kinefx::rigdoctor</code> を通すと、行列などの足りない属性が埋まる。

真ん中の関節を回したとき、その先の関節はどこへ行くはずか。
根元を原点、関節が (0,1,0) と (0,2,0) にあるなら、
真ん中を Z 軸まわりに θ 回したとき先端は

    (−sin θ, 1 + cos θ, 0)

に来るはずだ。<strong>先に式を立てて、実測と突き合わせる。</strong>

  A. 手で組んだ骨に何が足りないか。rigdoctor は何を足すか
  B. 真ん中を回したとき、先端は式どおりに動くか
  C. 回した関節そのものは動かないか

    hython examples/051_skeleton.py
    hython examples/051_skeleton.py shot rest
    hython examples/051_skeleton.py shot bent
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

RES = (620, 620)
ANGLES = (0.0, 15.0, 30.0, 45.0, 60.0, 90.0)

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
    // prerotate は「先に回してから動かす」。rotate だと順番が逆になり、
    // 関節そのものが原点のまわりを回ってしまう。
    prerotate(m, radians(ch("angle")), set(0, 0, 1));
    4@localtransform = m;
}
"""

# 比べるための「間違ったほう」
POSE_VEX_WRONG = POSE_VEX.replace("prerotate", "rotate")


def build(angle, wrong=False):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "rig")

    # 1. 骨を手で組む。点3つと、それをつなぐ線1本
    make = geo.createNode("attribwrangle", "make_joints")
    make.parm("class").set(0)
    make.parm("snippet").set(JOINTS_VEX)

    # 2. 足りない属性を埋める
    doc = geo.createNode("kinefx::rigdoctor", "doctor")
    doc.setFirstInput(make)
    doc.parm("transformations").set(1)
    doc.parm("inittransforms").set(1)
    doc.parm("outputparentidx").set(1)

    # 3. 真ん中の関節を回す
    pose = geo.createNode("kinefx::rigattribwrangle", "pose")
    pose.setFirstInput(doc)
    pose.parm("class").set(2)
    pose.parm("snippet").set(POSE_VEX_WRONG if wrong else POSE_VEX)
    ptg = pose.parmTemplateGroup()
    if pose.parm("angle") is None:
        import hou as _hou
        ptg.append(_hou.FloatParmTemplate("angle", "angle", 1,
                                          default_value=(0.0,)))
        pose.setParmTemplateGroup(ptg)
    pose.parm("angle").set(angle)
    pose.setDisplayFlag(True)
    pose.setRenderFlag(True)
    geo.layoutChildren()
    return geo, make, doc, pose


def positions(node):
    out = {}
    for pt in node.geometry().points():
        p = pt.position()
        out[pt.attribValue("name")] = (float(p[0]), float(p[1]), float(p[2]))
    return out


def main():
    stats = {}
    geo, make, doc, pose = build(0.0)

    print("A. 手で組んだ骨と、rigdoctor が足すもの")
    raw = make.geometry()
    fixed = doc.geometry()
    before = sorted(a.name() for a in raw.pointAttribs())
    after = sorted(a.name() for a in fixed.pointAttribs())
    print(f"   手で組んだ直後: {len(raw.points())}点 / "
          f"{len(raw.prims())}線")
    print(f"   属性（前）: {before}")
    print(f"   属性（後）: {after}")
    print(f"   足されたもの: {[a for a in after if a not in before]}")
    stats["attribs_before"] = before
    stats["attribs_after"] = after
    stats["added"] = [a for a in after if a not in before]

    print("\n   足された属性の中身（回す前）")
    print(f"   {'関節':>8} {'位置':>22} {'parent_idx':>11}")
    for pt in fixed.points():
        p = pt.position()
        print(f"   {pt.attribValue('name'):>8} "
              f"({p[0]:6.3f},{p[1]:6.3f},{p[2]:6.3f})   "
              f"{pt.attribValue('parent_idx'):>11}")

    print("\nB. 真ん中の関節を回す")
    print(f"   {'角度':>6} {'先端 実測 x':>12} {'先端 実測 y':>12} "
          f"{'式 x':>10} {'式 y':>10} {'ずれ':>12} "
          f"{'真ん中の関節の移動':>18}")
    rows = []
    for angle in ANGLES:
        geo, make, doc, pose = build(angle)
        pos = positions(pose)
        tip = pos["joint2"]
        mid = pos["joint1"]
        rad = math.radians(angle)
        want = (-math.sin(rad), 1.0 + math.cos(rad), 0.0)
        err = math.dist(tip, want)
        moved = math.dist(mid, (0.0, 1.0, 0.0))
        rows.append({"angle": angle, "tip": list(tip), "want": list(want),
                     "error": err, "mid_moved": moved})
        print(f"   {angle:>6.0f} {tip[0]:>12.6f} {tip[1]:>12.6f} "
              f"{want[0]:>10.6f} {want[1]:>10.6f} {err:>12.9f} "
              f"{moved:>18.9f}")
    worst = max(r["error"] for r in rows)
    worst_mid = max(r["mid_moved"] for r in rows)
    print(f"\n   式とのずれの最大: {worst:.9f}")
    print(f"   式どおりか: {'はい' if worst < 1e-6 else 'いいえ'}")
    print(f"   回した関節そのものの移動の最大: {worst_mid:.9f}")
    print(f"   動かずに済んでいるか: {'はい' if worst_mid < 1e-6 else 'いいえ'}")
    stats["angles"] = rows
    stats["worst"] = worst
    stats["worst_mid"] = worst_mid
    stats["matches"] = bool(worst < 1e-6)

    print("\nC. rotate と prerotate を取り違えるとどうなるか")
    print(f"   {'角度':>6} {'書き方':>10} {'真ん中 x':>10} {'真ん中 y':>10} "
          f"{'先端 x':>10} {'先端 y':>10}")
    wrong_rows = []
    for angle in (30.0, 60.0, 90.0):
        for label, flag in (("prerotate", False), ("rotate", True)):
            geo2, make2, doc2, pose2 = build(angle, wrong=flag)
            pos = positions(pose2)
            mid, tip = pos["joint1"], pos["joint2"]
            wrong_rows.append({"angle": angle, "how": label,
                               "mid": list(mid), "tip": list(tip)})
            print(f"   {angle:>6.0f} {label:>10} {mid[0]:>10.6f} "
                  f"{mid[1]:>10.6f} {tip[0]:>10.6f} {tip[1]:>10.6f}")
    stats["wrong"] = wrong_rows

    with open(os.path.join(OUT, "051_stats.json"), "w",
              encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    import hou_tools
    geo, make, doc, pose = build(45.0)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "051_graph.json"),
                          title="実験051 — 骨を作って動かす")
    hou_tools.save_hip(os.path.join(OUT, "051_skeleton.hipnc"))
    print("\n保存: out/051_stats.json, out/051_graph.json, "
          "out/051_skeleton.hipnc")


def shot(case):
    import hou
    import hou_tools
    angle = 0.0 if case == "rest" else 60.0
    geo, make, doc, pose = build(angle)
    # 骨は線なので、見えるように球を付ける
    show = geo.createNode("copytopoints::2.0", "show")
    ball = geo.createNode("sphere", "ball")
    ball.parm("type").set(2)
    ball.parm("rows").set(16)
    ball.parm("cols").set(16)
    ball.parmTuple("rad").set((0.12, 0.12, 0.12))
    show.setInput(0, ball)
    show.setInput(1, pose)
    # 線のままでは細くて写らないので、骨を筒にする
    wire = geo.createNode("polywire", "bones")
    wire.setFirstInput(pose)
    wire.parm("radius").set(0.05)

    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, wire)
    merged.setInput(1, show)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()

    bbox = hou.BoundingBox(-1.3, -0.3, -0.6, 1.3, 2.3, 0.6)
    png = os.path.join(OUT, f"051_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.0, 0.0, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.05)
    print(f"保存: out/051_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
