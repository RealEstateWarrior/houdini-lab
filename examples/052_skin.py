"""実験052 — 骨に肉を付ける。曲げると痩せるのか。

実験051で骨を曲げた。今回はその骨に皮（メッシュ）を結び付けて、
骨と一緒に動かす。

キャラクターの腕を曲げると、肘のあたりが痩せる——というのは
この仕組みでよく言われる話だが、<strong>どれくらい痩せるのかは聞いたことがない</strong>。
測る。

  A. 結び付けると、皮に何が付くか
  B. 曲げたとき、根元側の点は動かずに済むか
  C. 曲げる角度と、体積の減り方

    hython examples/052_skin.py
    hython examples/052_skin.py shot rest
    hython examples/052_skin.py shot bent
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


def build(angle, influences=None):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "rigskin")

    # 骨（実験051と同じ）
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

    # 皮。骨を包む筒
    skin = geo.createNode("tube", "skin")
    skin.parm("type").set(1)
    skin.parm("rad1").set(SKIN_RADIUS)
    skin.parm("rad2").set(SKIN_RADIUS)
    skin.parm("height").set(2.0)
    skin.parm("rows").set(SKIN_ROWS)
    skin.parm("cols").set(SKIN_COLS)
    skin.parm("ty").set(1.0)
    skin.parm("cap").set(1)

    # 骨に結び付ける
    capture = geo.createNode("kinefx::jointcaptureproximity", "capture")
    capture.setInput(0, skin)
    capture.setInput(1, doc)
    if influences is not None:
        # 1つの点が、いくつの骨の影響を受けるか。既定は2
        capture.parm("maxinfluences").set(influences)

    # 骨の動きに合わせて皮を動かす
    deform = geo.createNode("kinefx::jointdeform", "deform")
    deform.setInput(0, capture)
    deform.setInput(1, doc)
    deform.setInput(2, pose)
    deform.setDisplayFlag(True)
    deform.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, capture, doc, pose, deform


def volume(node):
    import hou
    geo = node.geometry()
    verb = hou.sopNodeTypeCategory().nodeVerb("measure")
    verb.setParms({"type": 2})       # volume
    return geo, verb


def measure_volume(node):
    """体積を測る。measure SOP を使わず、面から直接求める。"""
    import numpy
    geo = node.geometry()
    total = 0.0
    for prim in geo.prims():
        pts = [v.point().position() for v in prim.vertices()]
        if len(pts) < 3:
            continue
        # 三角形に割って、原点との四面体の符号付き体積を足す
        a = numpy.asarray([pts[0][0], pts[0][1], pts[0][2]])
        for i in range(1, len(pts) - 1):
            b = numpy.asarray([pts[i][0], pts[i][1], pts[i][2]])
            c = numpy.asarray([pts[i + 1][0], pts[i + 1][1],
                               pts[i + 1][2]])
            total += float(numpy.dot(a, numpy.cross(b, c))) / 6.0
    return abs(total)


def main():
    import numpy
    stats = {}
    geo, skin, capture, doc, pose, deform = build(0.0)

    print("A. 結び付けると、皮に何が付くか")
    before = sorted(a.name() for a in skin.geometry().pointAttribs())
    after = sorted(a.name() for a in capture.geometry().pointAttribs())
    print(f"   皮: {len(skin.geometry().points())}点 / "
          f"{len(skin.geometry().prims())}面")
    print(f"   属性（前）: {before}")
    print(f"   属性（後）: {after}")
    print(f"   足されたもの: {[a for a in after if a not in before]}")
    stats["skin_points"] = len(skin.geometry().points())
    stats["skin_prims"] = len(skin.geometry().prims())
    stats["added"] = [a for a in after if a not in before]

    base_volume = measure_volume(deform)
    print(f"\n   曲げる前の体積: {base_volume:.6f}")
    # 筒の体積の理屈の値（半径 0.32、高さ 2.0、24角形なので真円より小さい）
    ideal = math.pi * SKIN_RADIUS ** 2 * 2.0
    poly = (0.5 * SKIN_COLS * SKIN_RADIUS ** 2
            * math.sin(2 * math.pi / SKIN_COLS)) * 2.0
    print(f"   真円の筒なら: {ideal:.6f}")
    print(f"   24角形の筒なら: {poly:.6f}（実測との差 "
          f"{abs(poly - base_volume) / poly * 100:.4f}%）")
    stats["volume_rest"] = base_volume
    stats["volume_ideal"] = ideal
    stats["volume_poly"] = poly

    print("\nB・C. 曲げる角度と、体積の減り方")
    print(f"   {'角度':>6} {'体積':>12} {'最初との比':>12} {'減った分':>12} "
          f"{'根元側の点の移動':>18} {'先端の移動':>12}")
    rows = []
    rest_pos = None
    for angle in ANGLES:
        geo, skin, capture, doc, pose, deform = build(angle)
        vol = measure_volume(deform)
        pts = numpy.asarray([[p.position()[0], p.position()[1],
                              p.position()[2]]
                             for p in deform.geometry().points()])
        if rest_pos is None:
            rest_pos = pts.copy()
            low_mask = rest_pos[:, 1] < 0.5      # 根元側（動かないはず）
            high_mask = rest_pos[:, 1] > 1.5     # 先端側
        moved = numpy.linalg.norm(pts - rest_pos, axis=1)
        row = {"angle": angle, "volume": vol,
               "ratio": vol / base_volume,
               "root_move": float(moved[low_mask].max()),
               "tip_move": float(moved[high_mask].max())}
        rows.append(row)
        print(f"   {angle:>6.0f} {vol:>12.6f} {row['ratio']:>12.6f} "
              f"{(1 - row['ratio']) * 100:>11.4f}% "
              f"{row['root_move']:>18.9f} {row['tip_move']:>12.6f}")
    # 減り方に式があるか。角度そのもの・二乗・(1 − cos θ) の3通りで割ってみる
    print(f"\n   {'角度':>6} {'減った分':>11} {'÷ θ':>10} {'÷ θ²':>12} "
          f"{'÷ (1 − cos θ)':>16}")
    for row in rows:
        angle = row["angle"]
        loss_pct = (1 - row["ratio"]) * 100
        rad = math.radians(angle)
        row["loss"] = loss_pct
        row["per_deg"] = loss_pct / angle if angle else float("nan")
        row["per_sq"] = loss_pct / angle ** 2 if angle else float("nan")
        row["per_cos"] = (loss_pct / (1 - math.cos(rad))
                          if angle else float("nan"))
        if not angle:
            print(f"   {angle:>6.0f} {loss_pct:>10.4f}% {'—':>10} "
                  f"{'—':>12} {'—':>16}")
        else:
            print(f"   {angle:>6.0f} {loss_pct:>10.4f}% "
                  f"{row['per_deg']:>10.5f} {row['per_sq']:>12.7f} "
                  f"{row['per_cos']:>16.4f}")
    cos_vals = [r["per_cos"] for r in rows if r["angle"]]
    spread = max(cos_vals) - min(cos_vals)
    print(f"   (1 − cos θ) で割った値の幅: {spread:.6f}")
    print(f"   一定と言えるか: {'はい' if spread < 0.01 else 'いいえ'}")
    stats["per_cos_spread"] = spread
    stats["per_cos_mean"] = sum(cos_vals) / len(cos_vals)

    stats["angles"] = rows
    worst_root = max(r["root_move"] for r in rows)
    loss = (1 - rows[-1]["ratio"]) * 100
    print(f"\n   根元側の点の移動の最大: {worst_root:.9f}")
    print(f"   根元は動かずに済んでいるか: "
          f"{'はい' if worst_root < 1e-6 else 'いいえ'}")
    print(f"   120度で減った体積: {loss:.4f}%")
    stats["worst_root"] = worst_root
    stats["loss_at_max"] = loss

    print("\n   どの高さの点が、どれだけ動いたか（90度のとき）")
    geo, skin, capture, doc, pose, deform = build(90.0)
    pts = numpy.asarray([[p.position()[0], p.position()[1],
                          p.position()[2]]
                         for p in deform.geometry().points()])
    moved = numpy.linalg.norm(pts - rest_pos, axis=1)
    print(f"   {'元の高さ':>12} {'点の数':>8} {'移動の平均':>12} "
          f"{'移動の最大':>12}")
    bands = []
    edges = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.01]
    for lo, hi in zip(edges, edges[1:]):
        mask = (rest_pos[:, 1] >= lo) & (rest_pos[:, 1] < hi)
        if not mask.any():
            continue
        band = {"lo": lo, "hi": hi, "count": int(mask.sum()),
                "mean": float(moved[mask].mean()),
                "max": float(moved[mask].max())}
        bands.append(band)
        print(f"   {lo:.2f}〜{hi:.2f}   {int(mask.sum()):>8} "
              f"{band['mean']:>12.6f} {band['max']:>12.6f}")
    stats["bands"] = bands
    still = ["{:.2f}〜{:.2f}".format(b["lo"], b["hi"])
             for b in bands if b["max"] < 1e-6]
    print("   まったく動かなかった帯: " + ("なし" if not still
                                           else ", ".join(still)))

    print("\nD. 1つの点が影響を受ける骨の数（maxinfluences）を変える")
    print(f"   {'骨の数':>8} {'体積':>12} {'減った分':>12} "
          f"{'根元の帯の移動 最大':>20} {'先端の移動 最大':>16}")
    inf_rows = []
    for count in (1, 2, 3):
        geo, skin, capture, doc, pose, deform = build(90.0,
                                                      influences=count)
        vol = measure_volume(deform)
        pts = numpy.asarray([[p.position()[0], p.position()[1],
                              p.position()[2]]
                             for p in deform.geometry().points()])
        moved = numpy.linalg.norm(pts - rest_pos, axis=1)
        low = (rest_pos[:, 1] < 0.25)
        high = (rest_pos[:, 1] > 1.75)
        row = {"influences": count, "volume": vol,
               "loss": (1 - vol / base_volume) * 100,
               "root_move": float(moved[low].max()),
               "tip_move": float(moved[high].max())}
        inf_rows.append(row)
        print(f"   {count:>8} {vol:>12.6f} {row['loss']:>11.4f}% "
              f"{row['root_move']:>20.9f} {row['tip_move']:>16.6f}")
    stats["influences"] = inf_rows

    with open(os.path.join(OUT, "052_stats.json"), "w",
              encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    import hou_tools
    geo, skin, capture, doc, pose, deform = build(90.0)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "052_graph.json"),
                          title="実験052 — 骨に肉を付ける")
    hou_tools.save_hip(os.path.join(OUT, "052_skin.hipnc"))
    print("\n保存: out/052_stats.json, out/052_graph.json, "
          "out/052_skin.hipnc")


def shot(case):
    import hou
    import hou_tools
    angle = 0.0 if case == "rest" else 90.0
    influences = 1 if case == "sharp" else None
    geo, skin, capture, doc, pose, deform = build(angle,
                                                  influences=influences)
    bbox = hou.BoundingBox(-1.6, -0.4, -0.6, 0.9, 2.4, 0.6)
    png = os.path.join(OUT, f"052_{case}.png")
    hou_tools.render_preview(deform.path(), png, res=RES,
                             direction=(0.0, 0.0, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.05)
    print(f"保存: out/052_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
