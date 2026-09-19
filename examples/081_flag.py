"""実験081 — 旗を風になびかせる。風速を上げると、旗はどこまで持ち上がるか。

左端を竿に留めた布（Vellum の cloth）に、ソルバの Built-in Wind で横から風を当てる。
風が無ければ旗は竿から垂れ下がり、風が強いほど水平に近づくはず。

  A. 風速を 0 / 1 / 2 / 4 / 8 / 16 と変え、3秒後の旗の角度と、はためきの大きさを測る
     角度は、竿の真ん中から見た「旗の先の辺」の向き。0度＝水平、90度＝真下に垂れる
     はためきは、最後の1秒（24フレーム）で旗の先の辺が上下・前後にどれだけ揺れたか（標準偏差）
  B. 風速 4 のまま、布の Normal Drag（面に垂直な向きの抵抗）を 1 / 10（既定） / 100 と変える

    hython examples/081_flag.py a
    hython examples/081_flag.py b
    hython examples/081_flag.py shot
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 144          # 3秒では揺れが収まらなかったので6秒回し、最後の2秒を平均する
WIDTH, HEIGHT = 3.0, 2.0
POLE_Y = 3.0          # 旗の縦の真ん中


def build(wind=4.0, dragnormal=10.0):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "flag")

    cloth = geo.createNode("grid", "cloth")
    cloth.parm("orient").set("xy")
    cloth.parmTuple("size").set((WIDTH, HEIGHT))
    cloth.parm("rows").set(21)
    cloth.parm("cols").set(31)
    cloth.parmTuple("t").set((WIDTH / 2, POLE_Y, 0.0))

    pins = geo.createNode("attribwrangle", "pole_side")
    pins.setFirstInput(cloth)
    pins.parm("snippet").set("if (@P.x < 0.001) i@group_pole = 1;\n"
                             "if (@P.x > %.4f) i@group_tip = 1;" % (WIDTH - 0.001))

    con = geo.createNode("vellumconstraints", "cloth_con")
    con.setFirstInput(pins)
    con.parm("constrainttype").set("cloth")
    con.parm("dragnormal").set(dragnormal)
    pin = geo.createNode("vellumconstraints", "pin")
    pin.setInput(0, con, 0)
    pin.setInput(1, con, 1)
    pin.parm("constrainttype").set("pin")
    pin.parm("grouptype").set("points")
    pin.parm("group").set("pole")

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, pin, 0)
    solver.setInput(1, pin, 1)
    solver.parm("startframe").set(1)
    solver.parm("dowind").set(1)
    solver.parm("windx").set(1.0)
    solver.parm("windspeed").set(wind)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver


def tip_state(node):
    import hou_tools
    g = node.geometry()
    p = hou_tools.point_array(g)
    tip = [pt.number() for pt in g.points() if pt.attribValue("group_tip")] if g.findPointAttrib("group_tip") else None
    return p, tip


def run(wind, dragnormal=10.0):
    import hou
    import numpy
    import hou_tools
    geo, solver = build(wind, dragnormal)
    hou.setFrame(1)
    g0 = solver.geometry()
    tip_idx = numpy.array([pt.number() for pt in g0.points()
                           if pt.position()[0] > WIDTH - 0.001])
    track = []
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        p = hou_tools.point_array(solver.geometry())
        t = p[tip_idx]
        track.append((float(t[:, 0].mean()), float(t[:, 1].mean()), float(t[:, 2].mean())))
    sec = time.perf_counter() - start
    x, y, z = track[-1]
    last = numpy.array(track[-48:])
    angles = numpy.degrees(numpy.arctan2(POLE_Y - last[:, 1], last[:, 0]))
    return {"wind": wind, "dragnormal": dragnormal, "tip_x": x, "tip_y": y, "tip_z": z,
            "angle": float(angles.mean()), "angle_sd": float(angles.std()),
            "angle_min": float(angles.min()), "angle_max": float(angles.max()),
            "flutter_y": float(last[:, 1].std()), "flutter_z": float(last[:, 2].std()),
            "flutter_x": float(last[:, 0].std()), "seconds": sec,
            "track": track, "points": len(solver.geometry().points())}


def show(r):
    print(f"   風速 {r['wind']:<4} Normal Drag {r['dragnormal']:<5} | 旗の先 x {r['tip_x']:.3f} y {r['tip_y']:.3f} "
          f"z {r['tip_z']:+.3f} | 角度 平均 {r['angle']:6.2f}度 ±{r['angle_sd']:5.2f}（{r['angle_min']:.1f}〜{r['angle_max']:.1f}） | はためき 上下 {r['flutter_y']:.4f} "
          f"前後 {r['flutter_z']:.4f} 左右 {r['flutter_x']:.4f} | {r['points']}点 {r['seconds']:.2f}秒")


def part_a():
    print("A. 風速を変える（Normal Drag 10）")
    rows = [run(w) for w in (0.0, 1.0, 2.0, 4.0, 8.0, 16.0)]
    for r in rows:
        show(r)
    with open(os.path.join(OUT, "081_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/081_a.json")


def part_b():
    print("B. 風速 4 で Normal Drag を変える")
    rows = [run(4.0, d) for d in (1.0, 10.0, 100.0)]
    for r in rows:
        show(r)
    with open(os.path.join(OUT, "081_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/081_b.json")


def part_c():
    """効くのは「抵抗 × 風速」か「抵抗 × 風速²」か。積をそろえた組を並べる。"""
    print("C. 抵抗と風速の組み合わせ（(4, 10) と比べる）")
    rows = [run(v, d) for v, d in ((2.0, 40.0), (8.0, 2.5), (2.0, 20.0), (8.0, 5.0))]
    for r in rows:
        show(r)
        print(f"      抵抗×風速 {r['dragnormal'] * r['wind']:.0f} / 抵抗×風速² {r['dragnormal'] * r['wind'] ** 2:.0f}")
    with open(os.path.join(OUT, "081_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/081_c.json")


def shot(wind="4"):
    import hou
    import hou_tools
    geo, solver = build(float(wind))
    pole = geo.createNode("tube", "pole")
    pole.parm("type").set(1)
    pole.parm("cap").set(True)
    pole.parmTuple("rad").set((0.04, 0.04))
    pole.parm("height").set(4.4)
    pole.parmTuple("t").set((-0.04, 2.2, 0.0))
    show_node = geo.createNode("merge", "show")
    show_node.setInput(0, pole)
    show_node.setInput(1, solver)
    show_node.setDisplayFlag(True)
    show_node.setRenderFlag(True)
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
    if wind == "4":
        hou_tools.save_hip(os.path.join(OUT, "081_flag.hipnc"))
    bbox = hou.BoundingBox(-0.3, 0.0, -1.5, 3.3, 4.5, 1.5)
    png = os.path.join(OUT, f"081_flag_{int(float(wind))}.png")
    hou_tools.render_preview(show_node.path(), png, res=(420, 440), direction=(0.35, 0.2, 1.0),
                             shading="smoothwire", frame_bbox=bbox, margin=1.03)
    print(f"保存: {png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "4")
    else:
        {"a": part_a, "b": part_b, "c": part_c}[arg]()
