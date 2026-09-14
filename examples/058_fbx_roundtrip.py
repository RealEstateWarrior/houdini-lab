"""実験058 — 骨を FBX で書き出して読み直す。往復で何が残るか。

Houdini で組んだリグは、最後は別のソフト（Unreal Engine など）へ渡すことになる。
その橋渡しに使われるのが FBX。

<strong>往復させて、何が保たれて何が失われるかを測る。</strong>
これは「思ったとおりに動くか」ではなく「思ったとおりに<strong>残るか</strong>」の実験。

  A. 関節の位置は保たれるか
  B. 名前と親子関係は保たれるか
  C. 曲げた姿勢も保たれるか
  D. 関節の数を増やすと、ファイルはどう重くなるか

    hython examples/058_fbx_roundtrip.py
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "058_stats.json")
FBX_DIR = os.path.join(OUT, "058_fbx")

COUNTS = (3, 5, 9, 17, 33)
ANGLE = 60.0


def joints_vex(count):
    return f"""
int prim = addprim(0, "polyline");
for (int i = 0; i < {count}; i++) {{
    int pt = addpoint(0, set(0.0, float(i), 0.0));
    setpointattrib(0, "name", pt, sprintf("joint%d", i));
    addvertex(0, prim, pt);
}}
"""


POSE_VEX = """
if (s@name == "joint1") {
    matrix m = 4@localtransform;
    prerotate(m, radians(ch("angle")), set(0, 0, 1));
    4@localtransform = m;
}
"""


def build(count, angle=0.0):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "rig")

    make = geo.createNode("attribwrangle", "make_joints")
    make.parm("class").set(0)
    make.parm("snippet").set(joints_vex(count))

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
    pose.setDisplayFlag(True)
    pose.setRenderFlag(True)
    geo.layoutChildren()
    return geo, doc, pose


def export(geo, doc, pose, path):
    rop = geo.createNode("kinefx::rop_fbxcharacteroutput", "out_fbx")
    rop.setInput(0, pose)        # Rest Geometry
    rop.setInput(1, doc)         # Capture Pose
    rop.setInput(2, pose)        # Animated Pose
    rop.parm("outputfilepath").set(path.replace("\\", "/"))
    rop.parm("mkpath").set(1)
    rop.parm("execute").pressButton()
    return rop


def reimport(path):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "back")
    imp = geo.createNode("kinefx::fbxcharacterimport", "import")
    imp.parm("fbxfile").set(path.replace("\\", "/"))
    return geo, imp


def joints(node):
    out = {}
    g = node.geometry()
    if g is None:
        return out
    for pt in g.points():
        name = (pt.attribValue("name")
                if g.findPointAttrib("name") else str(pt.number()))
        p = pt.position()
        parent = (pt.attribValue("parent_idx")
                  if g.findPointAttrib("parent_idx") else None)
        out[name] = {"pos": (float(p[0]), float(p[1]), float(p[2])),
                     "parent": parent, "index": pt.number()}
    return out


def main():
    os.makedirs(FBX_DIR, exist_ok=True)
    stats = {"counts": list(COUNTS), "angle": ANGLE}

    print("A・B. まっすぐな骨を往復させる")
    print(f"   {'関節':>5} {'書き出し前':>10} {'読み直し後':>10} "
          f"{'位置のずれ 最大':>16} {'名前が残ったか':>16} "
          f"{'親子が残ったか':>16} {'バイト':>10}")
    rows = []
    for count in COUNTS:
        path = os.path.join(FBX_DIR, f"rig{count}.fbx")
        geo, doc, pose = build(count)
        before = joints(pose)
        export(geo, doc, pose, path)
        size = os.path.getsize(path) if os.path.exists(path) else 0

        geo2, imp = reimport(path)
        after = joints(imp)

        shared = [k for k in before if k in after]
        worst = 0.0
        for key in shared:
            worst = max(worst, math.dist(before[key]["pos"],
                                         after[key]["pos"]))
        names_ok = len(shared) == len(before)
        parent_ok = all(before[k]["parent"] == after[k]["parent"]
                        for k in shared) if shared else False
        rows.append({"count": count, "before": len(before),
                     "after": len(after), "shared": len(shared),
                     "worst": worst, "names_ok": names_ok,
                     "parent_ok": parent_ok, "bytes": size})
        print(f"   {count:>5} {len(before):>10} {len(after):>10} "
              f"{worst:>16.9f} "
              f"{('はい' if names_ok else 'いいえ'):>16} "
              f"{('はい' if parent_ok else 'いいえ'):>16} {size:>10,}")
    stats["straight"] = rows

    print("\nC. 曲げた姿勢も残るか（関節9個、真ん中を60度）")
    path = os.path.join(FBX_DIR, "rig_posed.fbx")
    geo, doc, pose = build(9, ANGLE)
    before = joints(pose)
    export(geo, doc, pose, path)
    geo2, imp = reimport(path)
    after = joints(imp)
    print(f"   {'関節':>8} {'書き出し前':>28} {'読み直し後':>28} "
          f"{'ずれ':>14}")
    posed = []
    worst = 0.0
    for key in sorted(before, key=lambda k: before[k]["index"]):
        if key not in after:
            print(f"   {key:>8} （読み直し後に無い）")
            continue
        b, a = before[key]["pos"], after[key]["pos"]
        d = math.dist(b, a)
        worst = max(worst, d)
        posed.append({"name": key, "before": list(b), "after": list(a),
                      "diff": d})
        print(f"   {key:>8} ({b[0]:8.5f},{b[1]:8.5f},{b[2]:8.5f}) "
              f"({a[0]:8.5f},{a[1]:8.5f},{a[2]:8.5f}) {d:>14.9f}")
    print(f"   いちばん大きいずれ: {worst:.9f}")
    print(f"   姿勢は残ったか: {'はい' if worst < 1e-4 else 'いいえ'}")
    stats["posed"] = {"rows": posed, "worst": worst}

    print("\nD. 関節の数とファイルの重さ")
    print(f"   {'関節':>5} {'バイト':>10} {'1関節あたり':>14}")
    for r in rows:
        print(f"   {r['count']:>5} {r['bytes']:>10,} "
              f"{r['bytes'] / r['count']:>13.1f}B")
    if len(rows) >= 2:
        first, last = rows[0], rows[-1]
        per = ((last["bytes"] - first["bytes"])
               / (last["count"] - first["count"]))
        base = first["bytes"] - per * first["count"]
        print(f"   関節1つの実費: 約 {per:.1f} バイト")
        print(f"   大きさによらない土台: 約 {base:.0f} バイト")
        stats["per_joint_bytes"] = per
        stats["base_bytes"] = base

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/058_stats.json")


if __name__ == "__main__":
    main()
