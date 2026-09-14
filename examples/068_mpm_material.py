"""実験068 — 材質ごとに、摩擦の式はどこで外れるか。

<a href="#exp067">実験067</a>で、Ground Friction はクーロン摩擦の μ そのものだと分かった。
ただし摩擦が強いと塊が潰れて、式から外れていった。

<strong>では「潰れる」の中身は材質で決まっているはずで、材質を変えれば外れ方も変わるはずだ。</strong>

  A. 5つの材質で、摩擦 0.25 のときの滑り方を測る
  B. 同じ5つを摩擦 1.0 で測る
  C. 「どれだけ形が崩れたか」と「式からどれだけ外れたか」を並べる

一度に何度も組み直すと hython が止まるので、A と B を別々に走らせる。

    hython examples/068_mpm_material.py a
    hython examples/068_mpm_material.py b
    python  examples/068_mpm_material.py merge
    hython examples/068_mpm_material.py shot elastic
    hython examples/068_mpm_material.py shot sandy
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
V0 = 4.0

MATERIALS = [("elastic", 0), ("chunky", 1), ("liquid", 2),
             ("viscous", 3), ("sandy", 4)]
LABEL = {"elastic": "弾む", "chunky": "塊", "liquid": "液", "viscous": "粘",
         "sandy": "砂"}


def build(material, friction):
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
    container.parm("sizez").set(16.0)
    container.parm("centerx").set(14.0)
    container.parm("centery").set(2.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)
    source.parm("materialtype").set(dict(MATERIALS)[material])
    source.parm("initialvelocityx").set(V0)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)
    solver.parm("groundactive").set(1)
    solver.parm("groundfriction").set(friction)
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
           "y_top": float(pts[:, 1].max()),
           "x_size": float(pts[:, 0].max() - pts[:, 0].min()),
           "z_size": float(pts[:, 2].max() - pts[:, 2].min())}
    if g.findPointAttrib("v"):
        vel = numpy.asarray([p.attribValue("v") for p in g.points()])
        out["vx_mean"] = float(vel[:, 0].mean())
    return out


def run(material, friction):
    import hou
    geo, solver = build(material, friction)
    hou.setFrame(1)
    first = stats_of(solver)
    start = time.perf_counter()
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
    last = stats_of(solver)
    last["material"] = material
    last["friction"] = friction
    last["slid"] = last["x_mean"] - first["x_mean"]
    # 「どれだけ形が崩れたか」。横に広がって縦に潰れるほど大きくなる
    last["squash"] = last["z_size"] / last["y_top"]
    last["seconds"] = time.perf_counter() - start
    return last


def part(name, friction, title):
    print(title)
    print(f"   {'材質':>9} {'滑った距離':>12} {'最後の vx':>12} {'いちばん上':>12} "
          f"{'奥行き':>10} {'潰れ具合':>10} {'秒':>7}")
    rows = []
    for material, _ in MATERIALS:
        info = run(material, friction)
        rows.append(info)
        print(f"   {material:>9} {info['slid']:>12.6f} "
              f"{info.get('vx_mean', 0):>12.6f} {info['y_top']:>12.6f} "
              f"{info['z_size']:>10.6f} {info['squash']:>10.4f} "
              f"{info['seconds']:>6.2f}秒")
    path = os.path.join(OUT, f"068_{name}.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"\n保存: out/068_{name}.json")


def merge():
    rows = {}
    for name in ("a", "b"):
        with open(os.path.join(OUT, f"068_{name}.json"), encoding="utf-8") as fp:
            rows[name] = json.load(fp)

    for name, friction in (("a", 0.25), ("b", 1.0)):
        want = V0 ** 2 / (2 * friction * G)
        print(f"{'A' if name == 'a' else 'B'}. 摩擦 {friction} — "
              f"式が言う距離は {want:.6f}")
        print(f"   {'材質':>9} {'滑った距離':>12} {'実測 ÷ 式':>12} "
              f"{'いちばん上':>12} {'奥行き':>10} {'潰れ具合':>10}")
        for r in rows[name]:
            print(f"   {r['material']:>9} {r['slid']:>12.6f} "
                  f"{r['slid'] / want:>12.6f} {r['y_top']:>12.6f} "
                  f"{r['z_size']:>10.6f} {r['squash']:>10.4f}")
        print()

    print("C. 形の崩れと、式からの外れ")
    print(f"   {'材質':>9} {'潰れ具合 0.25':>14} {'外れ 0.25':>12} "
          f"{'潰れ具合 1.0':>14} {'外れ 1.0':>12} {'距離 0.25 ÷ 1.0':>16}")
    w25 = V0 ** 2 / (2 * 0.25 * G)
    w10 = V0 ** 2 / (2 * 1.0 * G)
    for ra, rb in zip(rows["a"], rows["b"]):
        print(f"   {ra['material']:>9} {ra['squash']:>14.4f} "
              f"{ra['slid'] / w25:>12.6f} {rb['squash']:>14.4f} "
              f"{rb['slid'] / w10:>12.6f} "
              f"{ra['slid'] / rb['slid']:>16.4f}")

    with open(os.path.join(OUT, "068_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/068_stats.json")


def shot(material):
    import hou
    import hou_tools
    geo, solver = build(material, 0.25)
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

    bgeo = os.path.join(OUT, f"068_{material}_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    # 真上から見る。横に広がるほど跡が太くなるので、材質の違いが一目で出る。
    bbox = hou.BoundingBox(-2.4, -0.2, -6.2, 7.0, 0.6, 6.2)
    png = os.path.join(OUT, f"068_{material}.png")
    hou_tools.render_preview(fnode.path(), png, res=(600, 620),
                             direction=(0.0, 1.0, 0.14), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    print(f"保存: out/068_{material}.png")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part("a", 0.25, "A. 5つの材質で、摩擦 0.25 のときの滑り方")
    elif arg == "b":
        part("b", 1.0, "B. 同じ5つを摩擦 1.0 で")
    elif arg == "merge":
        merge()
    elif arg == "shot":
        shot(sys.argv[2])
