"""実験072 — たわむ板は、上の塊を放り上げられるか。

<a href="#exp070">実験070</a>で、コライダの Type には Static / Animated (Rigid) / Animated (Deforming)
の3つがあり、Deforming では computevelocity が必須だと分かった。ただし070で動かしたのは
「形の変わらない板」だった。今度は<strong>板そのものを曲げる</strong>。

板の真ん中を、決まった速さ v で高さ H まで持ち上げて、そこで止める。
上に乗った塊は、板が止まった瞬間に速さ v で放り出され、そこから

    さらに上がる高さ = v² ÷ (2 g)

だけ上がるはず。v を 2 / 4 / 8 と変えて、この式に乗るかを見る。

  A. Deforming・computevelocity 入り で v を変える（式との比較）
  B. v = 4 で、Type と computevelocity を変える（Static / Rigid / Deforming 入り / Deforming 切り）

組み込みの地面は切る（実験069）。

    hython examples/072_mpm_deform.py a
    hython examples/072_mpm_deform.py b
    hython examples/072_mpm_deform.py shot
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 60
FPS = 24.0
SEP = 0.12
G = 9.81
SIZE = 0.6
LIFT = 1.0            # 板の真ん中を持ち上げる高さ
START = 0.5           # 持ち上げ始める秒（それまでに塊を落ち着かせる）
TYPE_NAME = {0: "Static（既定）", 1: "Animated (Rigid)", 2: "Animated (Deforming)"}


def build(speed, collider_type=2, compute_velocity=True):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "deform")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((SIZE, SIZE, SIZE))
    box.parmTuple("t").set((0.0, SIZE / 2 + 0.02, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(SEP)
    container.parm("sizex").set(10.0)
    container.parm("sizey").set(9.0)
    container.parm("sizez").set(5.0)
    container.parm("centery").set(3.5)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    # 細かく割った板。上面が y = 0
    plank = geo.createNode("box", "plank")
    plank.parm("type").set("polymesh")
    plank.parmTuple("size").set((8.0, 0.4, 4.0))
    plank.parmTuple("divrate").set((33, 2, 9))
    plank.parm("ty").set(-0.2)

    # 真ん中ほど高く持ち上げる。持ち上げる時間 T = LIFT ÷ speed
    bend = geo.createNode("attribwrangle", "bend")
    bend.setFirstInput(plank)
    duration = LIFT / speed
    bend.parm("snippet").set(
        f"float s = clamp((@Time - {START}) / {duration}, 0.0, 1.0);\n"
        f"@P.y += {LIFT} * s * cos(PI * @P.x / 8.0);")

    collider = geo.createNode("mpmcollider", "collider")
    collider.setInput(0, bend)
    collider.setInput(1, container)
    collider.parm("type").set(collider_type)
    collider.parm("computevelocity").set(1 if compute_velocity else 0)
    collider.parm("friction").set(1.0)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(1, collider)
    solver.setInput(2, container)
    solver.parm("groundactive").set(0)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver, bend


def stats_of(node):
    import numpy
    g = node.geometry()
    pts = numpy.asarray([p.position() for p in g.points()], dtype=float)
    vel = numpy.asarray([p.attribValue("v") for p in g.points()], dtype=float)
    return {"count": int(len(pts)), "y_min": float(pts[:, 1].min()),
            "y_mean": float(pts[:, 1].mean()), "vy": float(vel[:, 1].mean())}


def run(speed, collider_type=2, compute_velocity=True):
    import hou
    geo, solver, bend = build(speed, collider_type, compute_velocity)
    stop_time = START + LIFT / speed
    rows = []
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
        s = stats_of(solver)
        s["frame"] = frame
        s["time"] = (frame - 1) / FPS
        rows.append(s)
    seconds = time.perf_counter() - start
    # 板が止まる直前（持ち上げ中）と、そのあとの一番高いところ
    lifting = [r for r in rows if START < r["time"] <= stop_time]
    after = [r for r in rows if r["time"] >= stop_time]
    top = max(after, key=lambda r: r["y_min"]) if after else rows[-1]
    rest = rows[int(START * FPS) - 1]
    return {"speed": speed, "collider_type": collider_type,
            "compute_velocity": compute_velocity,
            "stop_time": stop_time,
            "rest_y_min": rest["y_min"],
            "vy_at_stop": lifting[-1]["vy"] if lifting else 0.0,
            "vy_max": max(r["vy"] for r in rows),
            "peak_y_min": top["y_min"], "peak_time": top["time"],
            "extra": top["y_min"] - (rest["y_min"] + LIFT),
            "predicted": speed * speed / (2 * G),
            "count": rows[-1]["count"], "seconds": seconds, "frames": rows}


def print_row(info):
    print(f"   v {info['speed']:>4} {TYPE_NAME[info['collider_type']]:>22} "
          f"cv {'入' if info['compute_velocity'] else '切'} | 止まる {info['stop_time']:.3f}秒 | "
          f"止まる直前の vy {info['vy_at_stop']:+.4f} 最大 vy {info['vy_max']:+.4f} | "
          f"最高点 {info['peak_y_min']:.4f}（{info['peak_time']:.3f}秒） "
          f"板より上に {info['extra']:+.4f}／式 {info['predicted']:.4f} | "
          f"{info['count']}粒 {info['seconds']:.2f}秒")


def part(name, cases):
    rows = []
    for kw in cases:
        info = run(**kw)
        rows.append(info)
        print_row(info)
    with open(os.path.join(OUT, f"072_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"保存: out/072_{name}.json")


def part_a():
    print("A. Deforming・computevelocity 入り で、持ち上げる速さ v を変える")
    part("a", [dict(speed=v) for v in (1.0, 2.0, 4.0, 8.0)])


def part_b():
    print("B. v = 4 で、Type と computevelocity を変える")
    part("b", [dict(speed=4.0, collider_type=t, compute_velocity=cv)
               for t, cv in ((0, True), (1, True), (1, False), (2, True), (2, False))])


def shot():
    """v = 4 の塊を、止まる前後で重ねて横から撮る。板は最後の形を描く。"""
    import hou
    import hou_tools
    geo, solver, bend = build(4.0)
    trail = hou.Geometry()
    trail.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    for frame in range(1, LAST + 1, 2):
        hou.setFrame(frame)
        u = (frame - 1) / float(LAST - 1)
        col = (0.15 + 0.75 * u, 0.25 + 0.45 * u, 0.55 + 0.35 * u)
        for p in solver.geometry().points():
            q = trail.createPoint()
            q.setPosition(p.position())
            q.setAttribValue("Cd", col)
    hou.setFrame(LAST)
    plank = bend.geometry()
    for p in plank.points():
        if abs(p.position()[2] - 2.0) < 1e-3 and p.position()[1] > 0.0 - 1e-3:
            q = trail.createPoint()
            q.setPosition(p.position())
            q.setAttribValue("Cd", (0.55, 0.55, 0.6))
    bgeo = os.path.join(OUT, "072_launch_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    bbox = hou.BoundingBox(-4.2, -0.3, -0.5, 4.2, 3.2, 0.5)
    png = os.path.join(OUT, "072_launch.png")
    hou_tools.render_preview(fnode.path(), png, res=(700, 330),
                             direction=(0.0, 0.0, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    print("保存: out/072_launch.png")


def scene():
    import hou_tools
    build(4.0)
    hou_tools.save_hip(os.path.join(OUT, "072_deform.hipnc"))
    print("保存: out/072_deform.hipnc")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part_a()
    elif arg == "b":
        part_b()
    elif arg == "test":
        print_row(run(float(sys.argv[2]) if len(sys.argv) > 2 else 4.0))
    elif arg == "shot":
        shot()
    elif arg == "scene":
        scene()
