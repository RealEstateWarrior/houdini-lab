"""実験060 — 031〜059 の振り返り点検。別の条件で測り直す。

30件ごとの点検。実験030では 001〜029 を点検した。今回は 031〜059。

<strong>同じ条件で走らせ直しても意味がない。</strong>同じ結果が出るだけで、
それは「再現した」だけであって「正しい」とは言えない。
だから<strong>条件を変えて測る</strong>。式として書いたものは、
数字を変えても同じ式に乗るはずだ。乗らなければ、それは式ではなく偶然だった。

  1. 球の面積（042・043 の土台）を、別のやり方で出す
  2. density は「面積あたりの本数」か — 土台の大きさを変えて確かめる
  3. 毛の太さは直径か — 別の解像度・別の距離で
  4. 体積の減り = 係数 × (1 − cos θ) — 骨の長さと皮の太さを変えて
  5. IK の届く距離 = 骨の長さの合計 — 長さを 1 以外にして
  6. APEX のノード数＝点数 — 枝分かれのある形で

    hython examples/060_audit.py
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "060_stats.json")

RESULTS = []


def record(no, claim, original, retested, ok, note=""):
    RESULTS.append({"exp": no, "claim": claim, "original": original,
                    "retested": retested, "ok": ok, "note": note})
    mark = "一致" if ok else "食い違い"
    print(f"   → {mark}")


# ---------------------------------------------------------------- 1
def check_area():
    """球の面積を、面から直接足す方法で出す。"""
    import hou
    print("\n1. 球の面積（実験042・043 の土台は 12.53039 としていた）")
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "area")
    sphere = geo.createNode("sphere", "s")
    sphere.parm("type").set(2)
    sphere.parm("rows").set(40)
    sphere.parm("cols").set(40)
    total = 0.0
    for prim in sphere.geometry().prims():
        pts = [v.point().position() for v in prim.vertices()]
        for i in range(1, len(pts) - 1):
            a = pts[i] - pts[0]
            b = pts[i + 1] - pts[0]
            total += a.cross(b).length() / 2.0
    ideal = 4.0 * math.pi
    print(f"   三角形を足して出した面積: {total:.6f}")
    print(f"   真球なら: {ideal:.6f}（{total / ideal * 100:.2f}%）")
    print(f"   もとの記録: 12.53039")
    ok = abs(total - 12.53039) < 0.0005
    record("042", "球（40×40）の表面積は 12.53039", "12.53039",
           f"{total:.6f}", ok,
           f"真球 {ideal:.5f} の {total / ideal * 100:.2f}%")


# ---------------------------------------------------------------- 2
def check_density():
    """土台の大きさを変えて、density が「面積あたりの本数」か確かめる。"""
    import hou
    print("\n2. density は「面積あたりの本数」か（実験042）")
    print(f"   {'半径':>6} {'面積':>10} {'density':>9} {'出た本数':>10} "
          f"{'本数 ÷ 面積':>14}")
    rows = []
    for radius in (0.5, 1.0, 2.0):
        hou.hipFile.clear(suppress_save_prompt=True)
        geo = hou.node("/obj").createNode("geo", "fur")
        sphere = geo.createNode("sphere", "s")
        sphere.parm("type").set(2)
        sphere.parm("rows").set(40)
        sphere.parm("cols").set(40)
        sphere.parmTuple("rad").set((radius, radius, radius))
        normal = geo.createNode("normal", "n")
        normal.setFirstInput(sphere)
        fur = geo.createNode("fur", "fur")
        fur.setFirstInput(normal)
        fur.parm("density").set(100)
        area = 0.0
        for prim in sphere.geometry().prims():
            pts = [v.point().position() for v in prim.vertices()]
            for i in range(1, len(pts) - 1):
                a = pts[i] - pts[0]
                b = pts[i + 1] - pts[0]
                area += a.cross(b).length() / 2.0
        hairs = len(fur.geometry().prims())
        rows.append({"radius": radius, "area": area, "hairs": hairs,
                     "per_area": hairs / area})
        print(f"   {radius:>6.1f} {area:>10.5f} {100:>9} {hairs:>10,} "
              f"{hairs / area:>14.3f}")
    spread = (max(r["per_area"] for r in rows)
              - min(r["per_area"] for r in rows))
    print(f"   「本数 ÷ 面積」の幅: {spread:.3f}")
    ok = spread < 5.0
    record("042", "density は面積1あたりの本数", "99.678（半径1で確認）",
           " / ".join(f"{r['per_area']:.3f}" for r in rows), ok,
           f"半径を 0.5 / 1.0 / 2.0 と変えた。幅 {spread:.3f}")


# ---------------------------------------------------------------- 3
def check_width():
    """別の解像度・別の距離で、width が直径か確かめる。"""
    import hou
    import hou_tools
    from PIL import Image
    import numpy

    print("\n3. 毛の太さ width は直径か（実験045）")
    res = (480, 480)
    thickness = 0.03
    length = 1.0
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "one")
    line = geo.createNode("line", "hair")
    line.parm("originx").set(-length / 2)
    line.parm("dirx").set(1.0)
    line.parm("diry").set(0.0)
    line.parm("dist").set(length)
    line.parm("points").set(2)
    wide = geo.createNode("attribwrangle", "w")
    wide.setFirstInput(line)
    wide.parm("class").set(2)
    wide.parm("snippet").set(f"f@width = {thickness!r};")
    wide.setDisplayFlag(True)
    wide.setRenderFlag(True)

    hou_tools._ensure_lights()
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(res[0])
    cam.parm("resy").set(res[1])
    pad = 0.10
    bbox = hou.BoundingBox(-length / 2 - pad, -pad, -pad,
                           length / 2 + pad, pad, pad)
    hou_tools._frame_camera(cam, bbox, res, (0.0, 0.0, 1.0), margin=1.0)
    focal = cam.parm("focal").eval()
    aperture = cam.parm("aperture").eval()
    distance = hou.Vector3(cam.worldTransform().extractTranslates()).length()
    scale = res[0] / (aperture * distance / focal)

    karma = hou.node("/out").createNode("karma", "audit_width")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(res[0])
    karma.parm("resolutiony").set(res[1])
    karma.parm("samplesperpixel").set(9)
    karma.parm("varianceaa_maxsamples").set(9)
    path = os.path.join(OUT, "060_width.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    karma.render(frame_range=(1, 1, 1), verbose=False)

    alpha = numpy.asarray(Image.open(path).convert("RGBA"),
                          dtype=numpy.float64)[:, :, 3] / 255.0
    # ロゴの箱を外す（480×480 なので比で当てる）
    h, w = alpha.shape
    alpha = alpha.copy()
    alpha[int(h * 0.85):, int(w * 0.55):] = 0.0
    cols = alpha.sum(axis=0)
    used = numpy.nonzero(cols > 0.01)[0]
    x0, x1 = used[0], used[-1]
    span = x1 - x0 + 1
    mid = cols[x0 + int(span * 0.2):x1 - int(span * 0.2) + 1]
    measured = float(numpy.median(mid))
    predicted = thickness * scale
    ratio = measured / predicted
    print(f"   解像度 {res[0]}×{res[1]} / 太さ {thickness} / 長さ {length}")
    print(f"   1世界単位 = {scale:.3f}px")
    print(f"   予測 {predicted:.4f}px / 実測 {measured:.4f}px / "
          f"比 {ratio:.4f}")
    print(f"   もとの記録: 0.9969〜1.0019（600×600、太さ 0.005〜0.04）")
    ok = abs(ratio - 1.0) < 0.02
    record("045", "width は直径（比 ≒ 1.0）", "0.9969〜1.0019",
           f"{ratio:.4f}", ok,
           f"解像度と太さを変えた（{res[0]}px / 太さ {thickness}）")


# ---------------------------------------------------------------- 4
def check_volume_law():
    """骨の長さと皮の太さを変えて、(1 − cos θ) の式が保たれるか。"""
    import hou
    print("\n4. 体積の減り = 係数 × (1 − cos θ)（実験052）")
    joints_vex = """
int prim = addprim(0, "polyline");
for (int i = 0; i < 3; i++) {
    int pt = addpoint(0, set(0.0, float(i) * 1.5, 0.0));
    setpointattrib(0, "name", pt, sprintf("joint%d", i));
    addvertex(0, prim, pt);
}
"""
    pose_vex = """
if (s@name == "joint1") {
    matrix m = 4@localtransform;
    prerotate(m, radians(ch("angle")), set(0, 0, 1));
    4@localtransform = m;
}
"""

    def volume(node):
        import numpy
        total = 0.0
        for prim in node.geometry().prims():
            pts = [v.point().position() for v in prim.vertices()]
            if len(pts) < 3:
                continue
            a = numpy.asarray([pts[0][0], pts[0][1], pts[0][2]])
            for i in range(1, len(pts) - 1):
                b = numpy.asarray([pts[i][0], pts[i][1], pts[i][2]])
                c = numpy.asarray([pts[i + 1][0], pts[i + 1][1],
                                   pts[i + 1][2]])
                total += float(numpy.dot(a, numpy.cross(b, c))) / 6.0
        return abs(total)

    def make(angle):
        hou.hipFile.clear(suppress_save_prompt=True)
        hou.playbar.setFrameRange(1, 1)
        geo = hou.node("/obj").createNode("geo", "rigskin")
        mk = geo.createNode("attribwrangle", "mk")
        mk.parm("class").set(0)
        mk.parm("snippet").set(joints_vex)
        doc = geo.createNode("kinefx::rigdoctor", "doc")
        doc.setFirstInput(mk)
        doc.parm("transformations").set(1)
        doc.parm("inittransforms").set(1)
        doc.parm("outputparentidx").set(1)
        pose = geo.createNode("kinefx::rigattribwrangle", "pose")
        pose.setFirstInput(doc)
        pose.parm("class").set(2)
        pose.parm("snippet").set(pose_vex)
        if pose.parm("angle") is None:
            ptg = pose.parmTemplateGroup()
            ptg.append(hou.FloatParmTemplate("angle", "angle", 1,
                                             default_value=(0.0,)))
            pose.setParmTemplateGroup(ptg)
        pose.parm("angle").set(angle)
        skin = geo.createNode("tube", "skin")
        skin.parm("type").set(1)
        skin.parm("rad1").set(0.5)      # 052 は 0.32
        skin.parm("rad2").set(0.5)
        skin.parm("height").set(3.0)    # 052 は 2.0
        skin.parm("rows").set(60)
        skin.parm("cols").set(24)
        skin.parm("ty").set(1.5)
        skin.parm("cap").set(1)
        cap = geo.createNode("kinefx::jointcaptureproximity", "cap")
        cap.setInput(0, skin)
        cap.setInput(1, doc)
        dfm = geo.createNode("kinefx::jointdeform", "dfm")
        dfm.setInput(0, cap)
        dfm.setInput(1, doc)
        dfm.setInput(2, pose)
        return geo, dfm

    geo, dfm = make(0.0)
    base = volume(dfm)
    print(f"   骨の長さ 1.5（052 は 1.0）、皮の半径 0.5（052 は 0.32）")
    print(f"   {'角度':>6} {'体積':>12} {'減った分':>11} "
          f"{'÷ (1 − cos θ)':>16}")
    vals = []
    for angle in (15.0, 30.0, 45.0, 60.0, 90.0, 120.0):
        geo, dfm = make(angle)
        vol = volume(dfm)
        loss = (1 - vol / base) * 100
        k = loss / (1 - math.cos(math.radians(angle)))
        vals.append(k)
        print(f"   {angle:>6.0f} {vol:>12.6f} {loss:>10.4f}% {k:>16.4f}")
    spread = max(vals) - min(vals)
    print(f"   係数の幅: {spread:.4f}（052 では 0.0002）")
    ok = spread < 0.05
    record("052", "体積の減り = 係数 × (1 − cos θ)",
           "係数 27.1284、幅 0.0002",
           f"係数 {sum(vals) / len(vals):.4f}、幅 {spread:.4f}", ok,
           "骨の長さと皮の太さを変えても、同じ形の式に乗るか")


# ---------------------------------------------------------------- 5
def check_reach():
    """骨の長さを 1 以外にして、届く距離が合計長になるか。"""
    import apex
    import hou
    print("\n5. IK の届く距離 = 骨の長さの合計（実験055・056）")
    bone = 0.7
    counts = (3, 5, 9)
    print(f"   骨1本の長さ {bone}（055・056 は 1.0）")
    print(f"   {'関節':>5} {'骨':>4} {'合計長':>8} {'目標まで':>10} "
          f"{'先端までの距離':>16} {'合計長との差':>14}")
    diffs = []
    for count in counts:
        reach = bone * (count - 1)
        g = apex.Graph()
        ik = g.addNode("ik", "rig::MultiBoneIKFromArray")
        ports = {g.portName(p): p for p in g.getInputPorts(ik)}
        chain = apex.Matrix4Array(
            [hou.hmath.buildTranslate(0.0, bone * i, 0.0)
             for i in range(count)])
        node = g.addNode("v_in", "Value<Matrix4Array>")
        g.setNodeParm(node, "parm", chain)
        g.addWire(g.getOutputPorts(node)[0], ports["in"])
        far = reach * 3.0
        target = (far / math.sqrt(2), far / math.sqrt(2), 0.0)
        goal = g.addNode("v_goal", "Value<Matrix4>")
        g.setNodeParm(goal, "parm", hou.hmath.buildTranslate(*target))
        g.addWire(g.getOutputPorts(goal)[0], ports["goal"])
        g.setNodeParm(ik, "blend", 1.0)
        g.addGraphOutput(ik, "out")
        g.compileProgram()
        g.executeProgram()
        out = g.getNodeOutputData("ik", "out")
        pts = [(float(m.at(3, 0)), float(m.at(3, 1)), float(m.at(3, 2)))
               for m in out]
        tip = math.dist(pts[0], pts[-1])
        diffs.append(abs(tip - reach))
        print(f"   {count:>5} {count - 1:>4} {reach:>8.2f} {far:>10.2f} "
              f"{tip:>16.9f} {tip - reach:>+14.9f}")
    worst = max(diffs)
    print(f"   合計長との差の最大: {worst:.9f}")
    ok = worst < 1e-5
    record("056", "届く距離 = 骨の長さの合計", "骨の本数（長さ1のとき）",
           f"差の最大 {worst:.9f}", ok, f"骨1本を {bone} にして確かめた")


# ---------------------------------------------------------------- 6
def check_graph_geo():
    """枝分かれのあるグラフで、ノード数＝点数か確かめる。"""
    import apex
    import hou
    print("\n6. APEX のノード数＝点数、配線数＝プリミティブ数（実験057）")
    g = apex.Graph()
    # 実験057は一直線の足し算だった。今回は枝分かれさせる
    a = g.addNode("a", "Value<Float>")
    b = g.addNode("b", "Value<Float>")
    g.setNodeParm(a, "parm", 2.0)
    g.setNodeParm(b, "parm", 5.0)
    add1 = g.addNode("add1", "Add<Float>")
    add2 = g.addNode("add2", "Add<Float>")
    mul = g.addNode("mul", "Multiply<Float>")
    wires = 0
    for node, src in ((add1, a), (add2, b)):
        pa, pb = g.getInputPorts(node)
        g.addWire(g.getOutputPorts(src)[0], pa)
        wires += 1
        sub = g.addSubPort(pb, "b1")
        g.addWire(g.getOutputPorts(src)[0], sub)
        wires += 1
    mports = g.getInputPorts(mul)
    g.addWire(g.getOutputPorts(add1)[0], mports[0])
    wires += 1
    if len(mports) > 1:
        try:
            sub = g.addSubPort(mports[1], "m1")
            g.addWire(g.getOutputPorts(add2)[0], sub)
        except Exception:  # noqa: BLE001
            g.addWire(g.getOutputPorts(add2)[0], mports[1])
        wires += 1
    g.addGraphOutput(mul, g.portName(g.getOutputPorts(mul)[0]))
    nodes = len(list(g.allNodes()))

    geo = hou.Geometry()
    g.saveToGeometry(geo)
    print(f"   枝分かれのあるグラフ: ノード {nodes}個 / 配線 {wires}本")
    print(f"   ジオメトリ: {len(geo.points())}点 / "
          f"{len(geo.prims())}プリミティブ")
    ok = len(geo.points()) == nodes and len(geo.prims()) == wires
    record("057", "ノード数＝点数、配線数＝プリミティブ数",
           "一直線の足し算で確認",
           f"点 {len(geo.points())} / プリミティブ {len(geo.prims())}", ok,
           "枝分かれのある形で確かめた")


def main():
    check_area()
    check_density()
    check_width()
    check_volume_law()
    check_reach()
    check_graph_geo()

    print("\n" + "=" * 60)
    print("点検のまとめ")
    print(f"   {'実験':>5} {'調べたこと':<34} {'結果':>8}")
    for r in RESULTS:
        print(f"   {r['exp']:>5} {r['claim'][:32]:<34} "
              f"{('一致' if r['ok'] else '食い違い'):>8}")
    agreed = sum(1 for r in RESULTS if r["ok"])
    print(f"\n   {agreed} / {len(RESULTS)} 件が一致")

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump({"results": RESULTS, "agreed": agreed,
                   "total": len(RESULTS)}, fp,
                  ensure_ascii=False, indent=2)
    print("保存: out/060_stats.json")


if __name__ == "__main__":
    main()
