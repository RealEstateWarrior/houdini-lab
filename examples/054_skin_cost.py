"""実験054 — なぜ Linear が既定なのか。速さと、ねじれ。

実験053で、Dual Quaternion のほうが 154倍も痩せないと分かった。
ではなぜ Linear が既定のままなのか。考えられるのは2つ。

  1. Dual Quaternion のほうが遅い
  2. ねじれ（骨の軸まわりの回転）で挙動が違う

どちらも測る。

速さの測り方には実験009の教訓を使う。<strong>同じノードを焼き直すとキャッシュが効いて
時間が出ない</strong>ので、毎回新しいノードを作って初回のクックを測る。

  A. 点の数を変えて、2つのやり方の時間を比べる
  B. 骨の軸まわりにひねったとき、体積はどうなるか
  C. ひねりの限界（180度）で何が起きるか

    hython examples/054_skin_cost.py speed
    hython examples/054_skin_cost.py twist
    hython examples/054_skin_cost.py shot linear
    hython examples/054_skin_cost.py shot dualquat
    python  examples/054_skin_cost.py report
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "054_stats.json")

RES = (620, 620)
SKIN_COLS = 24
SKIN_RADIUS = 0.32
METHODS = (("linear", "Linear（既定）"), ("dualquat", "Dual Quaternion"))
TWISTS = (0.0, 45.0, 90.0, 135.0, 170.0, 179.0)
SIZES = ((120, 24), (240, 48), (480, 96), (960, 192), (1440, 288))

JOINTS_VEX = """
int prim = addprim(0, "polyline");
for (int i = 0; i < 3; i++) {
    int pt = addpoint(0, set(0.0, float(i), 0.0));
    setpointattrib(0, "name", pt, sprintf("joint%d", i));
    addvertex(0, prim, pt);
}
"""


def pose_vex(axis):
    """axis が (0,0,1) なら曲げ、(0,1,0) なら骨の軸まわりのひねり。"""
    return (
        'if (s@name == "joint1") {\n'
        "    matrix m = 4@localtransform;\n"
        f"    prerotate(m, radians(ch(\"angle\")), set({axis[0]}, "
        f"{axis[1]}, {axis[2]}));\n"
        "    4@localtransform = m;\n"
        "}\n")


def build(angle, method="linear", rows=60, axis=(0, 0, 1), cols=SKIN_COLS):
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
    pose.parm("snippet").set(pose_vex(axis))
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
    skin.parm("rows").set(rows)
    skin.parm("cols").set(cols)
    skin.parm("ty").set(1.0)
    skin.parm("cap").set(1)

    capture = geo.createNode("kinefx::jointcaptureproximity", "capture")
    capture.setInput(0, skin)
    capture.setInput(1, doc)
    # 結び付けまでは両方に共通なので、先に計算を済ませておく
    capture.geometry()

    deform = geo.createNode("kinefx::jointdeform", "deform")
    deform.setInput(0, capture)
    deform.setInput(1, doc)
    deform.setInput(2, pose)
    deform.parm("method").set(method)
    deform.setDisplayFlag(True)
    deform.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, capture, doc, pose, deform


def volume_of(node):
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
    return abs(total)


def load():
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as fp:
            return json.load(fp)
    return {}


def save(stats):
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)


def speed():
    """A. 点の数を変えて、時間を比べる。"""
    print("A. 点の数を変えて、2つのやり方の時間を比べる")
    print(f"   {'点の数':>9} {'面の数':>9} {'Linear':>12} "
          f"{'Dual Quaternion':>18} {'倍率':>8} {'1点あたりの差':>16}")
    # 1回目は準備の分が乗るので、捨てる
    build(90.0, "linear", rows=120, cols=24)[5].geometry()

    rows = []
    for row_count, col_count in SIZES:
        times = {}
        points = prims = 0
        for key, _ in METHODS:
            geo, skin, capture, doc, pose, deform = build(
                90.0, key, rows=row_count, cols=col_count)
            start = time.perf_counter()
            g = deform.geometry()        # ここで初めて計算が走る
            times[key] = time.perf_counter() - start
            points, prims = len(g.points()), len(g.prims())
        ratio = times["dualquat"] / times["linear"]
        per_point = (times["dualquat"] - times["linear"]) / points * 1e9
        rows.append({"rows": row_count, "cols": col_count,
                     "points": points, "prims": prims,
                     "linear": times["linear"],
                     "dualquat": times["dualquat"],
                     "ratio": ratio, "per_point_ns": per_point})
        print(f"   {points:>9,} {prims:>9,} {times['linear'] * 1000:>10.2f}ms "
              f"{times['dualquat'] * 1000:>16.2f}ms {ratio:>8.2f} "
              f"{per_point:>14.2f}ns")
    stats = load()
    stats["speed"] = rows
    ratios = [r["ratio"] for r in rows]
    stats["ratio_range"] = [min(ratios), max(ratios)]
    print(f"   倍率の幅: {min(ratios):.2f} 〜 {max(ratios):.2f}")
    big = [r for r in rows if r["points"] > 20000]
    if big:
        per = sum(r["per_point_ns"] for r in big) / len(big)
        print(f"   点が2万を超える行の「1点あたりの差」の平均: {per:.2f}ns")
        stats["per_point_ns"] = per
    save(stats)


def twist():
    """B・C. 骨の軸まわりにひねる。"""
    print("B. 骨の軸まわりにひねったとき、体積はどうなるか")
    geo, skin, capture, doc, pose, deform = build(0.0, "linear")
    base = volume_of(deform)
    print(f"   ひねる前の体積: {base:.6f}")
    print(f"   {'ひねり':>8} {'Linear':>14} {'減った分':>12} "
          f"{'Dual Quaternion':>18} {'減った分':>12}")
    rows = []
    for angle in TWISTS:
        vals = {}
        for key, _ in METHODS:
            geo, skin, capture, doc, pose, deform = build(
                angle, key, axis=(0, 1, 0))
            vals[key] = volume_of(deform)
        row = {"angle": angle,
               "linear": vals["linear"],
               "linear_loss": (1 - vals["linear"] / base) * 100,
               "dualquat": vals["dualquat"],
               "dualquat_loss": (1 - vals["dualquat"] / base) * 100}
        rows.append(row)
        print(f"   {angle:>8.0f} {row['linear']:>14.6f} "
              f"{row['linear_loss']:>11.4f}% {row['dualquat']:>18.6f} "
              f"{row['dualquat_loss']:>11.4f}%")
    stats = load()
    stats["twist"] = rows
    stats["twist_base"] = base
    last = rows[-1]
    print(f"\n   179度のとき: Linear {last['linear_loss']:.4f}% / "
          f"Dual Quaternion {last['dualquat_loss']:.4f}%")

    print("\nC. 高さごとに、実際は何度ねじれたか")
    import numpy
    geo, skin, capture, doc, pose, deform = build(0.0, "linear")
    rest = numpy.asarray([[p.position()[0], p.position()[1],
                           p.position()[2]]
                          for p in deform.geometry().points()])
    rest_ang = numpy.arctan2(rest[:, 2], rest[:, 0])
    edges = [0.0, 0.5, 0.9, 1.1, 1.5, 2.01]
    profile = []
    for want in (170.0, 181.0):
        print(f"   指定 {want:.0f}度")
        print(f"   {'元の高さ':>12} {'Linear':>12} {'Dual Quaternion':>18}")
        for lo, hi in zip(edges, edges[1:]):
            mask = (rest[:, 1] >= lo) & (rest[:, 1] < hi)
            # 軸の近くは角度が不安定なので、外側だけ使う
            radius = numpy.sqrt(rest[:, 0] ** 2 + rest[:, 2] ** 2)
            mask = mask & (radius > SKIN_RADIUS * 0.8)
            if not mask.any():
                continue
            row = {"deg": want, "lo": lo, "hi": hi}
            line = f"   {lo:.2f}〜{hi:.2f}  "
            for key, _ in METHODS:
                geo, skin, capture, doc, pose, deform = build(
                    want, key, axis=(0, 1, 0))
                pts = numpy.asarray([[p.position()[0], p.position()[1],
                                      p.position()[2]]
                                     for p in deform.geometry().points()])
                ang = numpy.arctan2(pts[:, 2], pts[:, 0])
                turn = numpy.degrees(numpy.angle(
                    numpy.exp(1j * (ang[mask] - rest_ang[mask]))))
                value = float(numpy.median(turn))
                row[key] = value
                line += f" {value:>18.3f}"
            profile.append(row)
            print(line)
    stats["twist_profile"] = profile
    save(stats)


def shot(case):
    import hou
    import hou_tools
    geo, skin, capture, doc, pose, deform = build(170.0, case,
                                                  axis=(0, 1, 0))
    bbox = hou.BoundingBox(-0.55, -0.1, -0.55, 0.55, 2.1, 0.55)
    png = os.path.join(OUT, f"054_{case}.png")
    hou_tools.render_preview(deform.path(), png, res=RES,
                             direction=(0.55, 0.25, 1.0),
                             shading="smoothwire",
                             frame_bbox=bbox, margin=1.05)
    print(f"保存: out/054_{case}.png")


def scene():
    import hou_tools
    geo, skin, capture, doc, pose, deform = build(170.0, "dualquat",
                                                  axis=(0, 1, 0))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "054_graph.json"),
                          title="実験054 — 速さとねじれ")
    hou_tools.save_hip(os.path.join(OUT, "054_skin_cost.hipnc"))
    print("保存: out/054_graph.json, out/054_skin_cost.hipnc")


def report():
    stats = load()
    print("A. 速さ")
    print(f"   {'点の数':>9} {'Linear':>12} {'Dual Quaternion':>18} "
          f"{'倍率':>8}")
    for r in stats.get("speed", []):
        print(f"   {r['points']:>9,} {r['linear'] * 1000:>10.2f}ms "
              f"{r['dualquat'] * 1000:>16.2f}ms {r['ratio']:>8.2f}")
    print("\nB. ねじれ")
    print(f"   {'ひねり':>8} {'Linear 減った分':>16} "
          f"{'Dual Quaternion 減った分':>24}")
    for r in stats.get("twist", []):
        print(f"   {r['angle']:>8.0f} {r['linear_loss']:>15.4f}% "
              f"{r['dualquat_loss']:>23.4f}%")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "speed":
        speed()
    elif cmd == "twist":
        twist()
    elif cmd == "shot":
        shot(sys.argv[2])
    elif cmd == "scene":
        scene()
    else:
        report()
