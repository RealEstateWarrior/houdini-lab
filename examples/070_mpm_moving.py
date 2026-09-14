"""実験070 — 動く板は、上に乗った塊をどれだけ運ぶか。

<a href="#exp069">実験069</a>で、コライダの摩擦は組み込みの地面と同じものだと分かった。
今度は<strong>板のほうを動かす</strong>。ベルトコンベアの上に物を置いたようなもの。

  A. 板の速さを 0 / 1 / 2 / 4 / 8 と変えて、塊がどれだけ運ばれるか
  B. 式「運ばれる距離 = 板の速さ × 時間 − 板の速さ² ÷ (2 μ g)」に乗るか
  C. computevelocity を切ると何が起きるか
  D. 摩擦を変えると、追いつくまでの時間はどう動くか

組み込みの地面は切る（実験069。切らないとコライダの摩擦が効かない）。

    hython examples/070_mpm_moving.py a
    hython examples/070_mpm_moving.py c
    hython examples/070_mpm_moving.py d
    python  examples/070_mpm_moving.py merge
    hython examples/070_mpm_moving.py shot
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

START_Y = 0.52
LAST = 40
FPS = 24.0
SEP = 0.12
G = 9.81


def build(speed, friction=1.0, compute_velocity=True, collider_type=1):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "mpm")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    box.parmTuple("t").set((0.0, START_Y, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(SEP)
    container.parm("sizex").set(40.0)
    container.parm("sizey").set(8.0)
    container.parm("sizez").set(8.0)
    container.parm("centerx").set(14.0)
    container.parm("centery").set(2.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    # 上面がちょうど y = 0 の長い板。1フレーム目を 0 秒として横へ流す
    floor = geo.createNode("box", "floor")
    floor.parmTuple("size").set((60.0, 0.4, 6.0))
    floor.parm("ty").set(-0.2)
    floor.parm("tx").setExpression(f"10.0 + ($FF - 1) / $FPS * {speed}")

    collider = geo.createNode("mpmcollider", "collider")
    collider.setInput(0, floor)
    collider.setInput(1, container)
    # type の既定は 0（Static）。動かすなら 1（Animated Rigid）にしないと、
    # 板がいくら動いても粒は何も感じない。エラーは出ない。
    collider.parm("type").set(collider_type)
    collider.parm("friction").set(friction)
    collider.parm("computevelocity").set(1 if compute_velocity else 0)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(1, collider)
    solver.setInput(2, container)
    # 実験069。組み込みの地面を切らないとコライダの摩擦が効かない
    solver.parm("groundactive").set(0)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver


def stats_of(node):
    import numpy
    g = node.geometry()
    pts = numpy.asarray([[p.position()[0], p.position()[1], p.position()[2]]
                         for p in g.points()])
    out = {"count": int(len(pts)),
           "x_mean": float(pts[:, 0].mean()),
           "y_mean": float(pts[:, 1].mean()),
           "z_size": float(pts[:, 2].max() - pts[:, 2].min())}
    if g.findPointAttrib("v"):
        vel = numpy.asarray([p.attribValue("v") for p in g.points()])
        out["vx_mean"] = float(vel[:, 0].mean())
    return out


def run(**kw):
    import hou
    geo, solver = build(**kw)
    hou.setFrame(1)
    first = stats_of(solver)
    start = time.perf_counter()
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
    last = stats_of(solver)
    last.update({k: v for k, v in kw.items()})
    last["carried"] = last["x_mean"] - first["x_mean"]
    last["seconds"] = time.perf_counter() - start
    return last


def table(rows, head, cols):
    print(head)
    for r in rows:
        print(cols(r))


def part_a():
    print("A. 板の速さを変えて、塊がどれだけ運ばれるか（摩擦 1.0）")
    print(f"   {'板の速さ':>10} {'運ばれた距離':>14} {'最後の vx':>12} "
          f"{'高さ':>10} {'奥行き':>10} {'秒':>7}")
    rows = []
    for speed in (0.0, 1.0, 2.0, 4.0, 8.0):
        info = run(speed=speed)
        rows.append(info)
        print(f"   {speed:>10} {info['carried']:>14.6f} "
              f"{info.get('vx_mean', 0):>12.6f} {info['y_mean']:>10.6f} "
              f"{info['z_size']:>10.6f} {info['seconds']:>6.2f}秒")
    with open(os.path.join(OUT, "070_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/070_a.json")


TYPE_NAME = {0: "Static（既定）", 1: "Animated Rigid", 2: "Animated Deforming"}


def part_c():
    print("C. type と computevelocity を変える（板の速さ 4.0・摩擦 1.0）")
    print(f"   {'type':>20} {'computevelocity':>16} {'運ばれた距離':>14} "
          f"{'最後の vx':>12} {'高さ':>10}")
    rows = []
    for ct, cv in ((0, True), (1, True), (1, False), (2, True), (2, False)):
        info = run(speed=4.0, collider_type=ct, compute_velocity=cv)
        rows.append(info)
        print(f"   {TYPE_NAME[ct]:>20} {'入り' if cv else '切り':>16} "
              f"{info['carried']:>14.6f} {info.get('vx_mean', 0):>12.6f} "
              f"{info['y_mean']:>10.6f}")
    with open(os.path.join(OUT, "070_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/070_c.json")


def part_d():
    print("D. 摩擦を変える（板の速さ 4.0）")
    print(f"   {'摩擦':>8} {'運ばれた距離':>14} {'最後の vx':>12} "
          f"{'式の距離':>12} {'追いつく秒':>12}")
    rows = []
    t = (LAST - 1) / FPS
    for mu in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0):
        info = run(speed=4.0, friction=mu)
        rows.append(info)
        if mu:
            catch = 4.0 / (mu * G)
            want = (4.0 * t - 4.0 ** 2 / (2 * mu * G) if catch <= t
                    else 0.5 * mu * G * t * t)
        else:
            catch, want = float("inf"), 0.0
        print(f"   {mu:>8} {info['carried']:>14.6f} "
              f"{info.get('vx_mean', 0):>12.6f} {want:>12.6f} "
              f"{catch:>12.4f}")
    with open(os.path.join(OUT, "070_d.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/070_d.json")


def merge():
    rows = {}
    for name in ("a", "c", "d"):
        with open(os.path.join(OUT, f"070_{name}.json"), encoding="utf-8") as fp:
            rows[name] = json.load(fp)
    t = (LAST - 1) / FPS
    print(f"経過時間 t = {LAST - 1} / {FPS} = {t:.6f} 秒\n")

    print("A・B. 板の速さと、運ばれた距離（摩擦 1.0）")
    print(f"   {'板の速さ':>10} {'運ばれた距離':>14} {'式の距離':>12} "
          f"{'実測 ÷ 式':>12} {'最後の vx':>12} {'vx ÷ 板の速さ':>14} "
          f"{'追いつく秒':>12}")
    for r in rows["a"]:
        v = r["speed"]
        if v == 0:
            print(f"   {v:>10} {r['carried']:>14.6f} {0.0:>12.6f} "
                  f"{'—':>12} {r.get('vx_mean', 0):>12.6f} {'—':>14} "
                  f"{'—':>12}")
            continue
        catch = v / (1.0 * G)
        want = v * t - v * v / (2 * 1.0 * G)
        vx = r.get("vx_mean", 0)
        print(f"   {v:>10} {r['carried']:>14.6f} {want:>12.6f} "
              f"{r['carried'] / want:>12.6f} {vx:>12.6f} "
              f"{vx / v:>14.6f} {catch:>12.4f}")

    print("\nC. computevelocity")
    for r in rows["c"]:
        print(f"   {'入り' if r['compute_velocity'] else '切り':>6} "
              f"運ばれた距離 {r['carried']:>12.6f} / "
              f"最後の vx {r.get('vx_mean', 0):>10.6f}")

    print("\nD. 摩擦を変える（板の速さ 4.0）")
    print(f"   {'摩擦':>8} {'運ばれた距離':>14} {'式の距離':>12} {'実測 ÷ 式':>12} "
          f"{'最後の vx':>12} {'追いつく秒':>12}")
    for r in rows["d"]:
        mu = r["friction"]
        if mu == 0:
            print(f"   {mu:>8} {r['carried']:>14.6f} {0.0:>12.6f} "
                  f"{'—':>12} {r.get('vx_mean', 0):>12.6f} {'∞':>12}")
            continue
        catch = 4.0 / (mu * G)
        want = (4.0 * t - 16.0 / (2 * mu * G) if catch <= t
                else 0.5 * mu * G * t * t)
        print(f"   {mu:>8} {r['carried']:>14.6f} {want:>12.6f} "
              f"{r['carried'] / want:>12.6f} {r.get('vx_mean', 0):>12.6f} "
              f"{catch:>12.4f}")

    with open(os.path.join(OUT, "070_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/070_stats.json")


def shot(name="carried"):
    import hou
    import hou_tools
    speed = 4.0 if name == "carried" else 0.0
    geo, solver = build(speed)
    trail = hou.Geometry()
    trail.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    for frame in range(1, LAST + 1, 2):
        hou.setFrame(frame)
        src = solver.geometry()
        u = (frame - 1) / float(LAST - 1)
        col = (0.15 + 0.75 * u, 0.25 + 0.45 * u, 0.55 + 0.35 * u)
        for p in src.points():
            q = trail.createPoint()
            q.setPosition(p.position())
            q.setAttribValue("Cd", col)

    bgeo = os.path.join(OUT, f"070_{name}_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    bbox = hou.BoundingBox(-0.8, -0.15, -1.0, 6.6, 1.15, 1.0)
    png = os.path.join(OUT, f"070_{name}.png")
    hou_tools.render_preview(fnode.path(), png, res=(760, 260),
                             direction=(0.0, 0.10, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    print(f"保存: out/070_{name}.png")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part_a()
    elif arg == "c":
        part_c()
    elif arg == "d":
        part_d()
    elif arg == "merge":
        merge()
    elif arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "carried")
