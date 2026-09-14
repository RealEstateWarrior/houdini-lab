"""実験069 — コライダの摩擦は、組み込みの地面と同じ式に乗るか。

<a href="#exp067">実験067</a>で測ったのは <code>mpmsolver</code> が最初から持っている地面。
<code>mpmcollider</code> にも <code>friction</code> と <code>sticky</code> があり、こちらは自分で置く物。

  A. 組み込みの地面を切り、代わりに箱のコライダを敷いて摩擦を振る
  B. 実験067の「組み込みの地面」の数字と、同じ摩擦どうしで突き合わせる
  C. 両方を同時に置いて、摩擦が食い違ったらどちらが勝つか

一度に何度も組み直すと hython が止まるので、A と C を別々に走らせる。

    hython examples/069_mpm_collider.py a
    hython examples/069_mpm_collider.py c
    python  examples/069_mpm_collider.py merge
    hython examples/069_mpm_collider.py shot
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

# 実験067で測った「組み込みの地面」の距離。同じ条件で並べて比べる
GROUND_067 = {0.0: 6.499988, 0.1: 5.204091, 0.25: 3.260808,
              0.5: 1.751774, 1.0: 1.194665}


def build(ground_friction=None, collider_friction=None,
          collider_sticky=0.0, ground_y=0.0):
    """ground_friction が None なら組み込みの地面を切る。
    collider_friction が None なら箱のコライダを置かない。"""
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
    source.parm("initialvelocityx").set(V0)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)

    if collider_friction is not None:
        # 上面がちょうど y = 0 になる板。滑る範囲は全部覆う
        floor = geo.createNode("box", "floor")
        floor.parmTuple("size").set((14.0, 0.4, 6.0))
        floor.parmTuple("t").set((5.0, -0.2, 0.0))
        collider = geo.createNode("mpmcollider", "collider")
        collider.setInput(0, floor)
        collider.setInput(1, container)
        collider.parm("friction").set(collider_friction)
        collider.parm("sticky").set(collider_sticky)
        solver.setInput(1, collider)

    if ground_friction is None:
        solver.parm("groundactive").set(0)
    else:
        solver.parm("groundactive").set(1)
        solver.parm("groundfriction").set(ground_friction)
        solver.parm("groundposy").set(ground_y)

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
    last.update(kw)
    last["slid"] = last["x_mean"] - first["x_mean"]
    last["seconds"] = time.perf_counter() - start
    return last


def part_a():
    print("A. 組み込みの地面を切り、箱のコライダだけで滑らせる")
    print(f"   {'コライダの摩擦':>14} {'滑った距離':>12} {'最後の vx':>12} "
          f"{'高さ':>10} {'奥行き':>10} {'秒':>7}")
    rows = []
    for mu in (0.0, 0.1, 0.25, 0.5, 1.0):
        info = run(ground_friction=None, collider_friction=mu)
        rows.append(info)
        print(f"   {mu:>14} {info['slid']:>12.6f} "
              f"{info.get('vx_mean', 0):>12.6f} {info['y_mean']:>10.6f} "
              f"{info['z_size']:>10.6f} {info['seconds']:>6.2f}秒")
    with open(os.path.join(OUT, "069_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/069_a.json")


def part_c():
    print("C. 両方を置いて、摩擦が食い違ったらどちらが勝つか")
    cases = [
        {"ground_friction": 0.25, "collider_friction": 0.25},
        {"ground_friction": 1.0, "collider_friction": 0.0},
        {"ground_friction": 0.0, "collider_friction": 1.0},
        {"ground_friction": 0.25, "collider_friction": None},
    ]
    print(f"   {'地面の摩擦':>12} {'コライダの摩擦':>14} {'滑った距離':>12} "
          f"{'最後の vx':>12} {'高さ':>10} {'秒':>7}")
    rows = []
    for kw in cases:
        info = run(**kw)
        rows.append(info)
        cf = ("なし" if kw["collider_friction"] is None
              else f"{kw['collider_friction']}")
        print(f"   {kw['ground_friction']:>12} {cf:>14} "
              f"{info['slid']:>12.6f} {info.get('vx_mean', 0):>12.6f} "
              f"{info['y_mean']:>10.6f} {info['seconds']:>6.2f}秒")
    with open(os.path.join(OUT, "069_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/069_c.json")


def merge():
    rows = {}
    for name in ("a", "c"):
        with open(os.path.join(OUT, f"069_{name}.json"), encoding="utf-8") as fp:
            rows[name] = json.load(fp)

    print("A・B. コライダと組み込みの地面を、同じ摩擦どうしで並べる")
    print(f"   {'摩擦 μ':>8} {'コライダ':>12} {'組み込みの地面':>14} "
          f"{'差':>12} {'コライダ ÷ 地面':>16} {'式の距離':>12} "
          f"{'コライダ ÷ 式':>14}")
    for r in rows["a"]:
        mu = r["collider_friction"]
        ground = GROUND_067[mu]
        want = V0 ** 2 / (2 * mu * G) if mu else float("inf")
        ratio = r["slid"] / want if mu else float("nan")
        print(f"   {mu:>8} {r['slid']:>12.6f} {ground:>14.6f} "
              f"{r['slid'] - ground:>12.6f} {r['slid'] / ground:>16.6f} "
              f"{want:>12.6f} {ratio:>14.6f}")

    print("\nC. 両方を置いたとき")
    print(f"   {'地面の摩擦':>12} {'コライダの摩擦':>14} {'滑った距離':>12} "
          f"{'最後の vx':>12}")
    for r in rows["c"]:
        cf = ("なし" if r["collider_friction"] is None
              else f"{r['collider_friction']}")
        print(f"   {r['ground_friction']:>12} {cf:>14} {r['slid']:>12.6f} "
              f"{r.get('vx_mean', 0):>12.6f}")

    with open(os.path.join(OUT, "069_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/069_stats.json")


def shot():
    import hou
    import hou_tools
    geo, solver = build(ground_friction=None, collider_friction=0.25)
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

    bgeo = os.path.join(OUT, "069_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    bbox = hou.BoundingBox(-0.8, -0.15, -1.0, 4.6, 1.15, 1.0)
    png = os.path.join(OUT, "069_collider.png")
    hou_tools.render_preview(fnode.path(), png, res=(760, 260),
                             direction=(0.0, 0.10, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    print(f"保存: out/069_collider.png")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part_a()
    elif arg == "c":
        part_c()
    elif arg == "d":
        print("D. 地面を下げて、先に触るのをコライダにする")
        print(f"   {'地面の高さ':>12} {'地面の摩擦':>12} {'コライダの摩擦':>14} "
              f"{'滑った距離':>12} {'最後の vx':>12}")
        rows = []
        for kw in ({"ground_y": -0.5, "ground_friction": 1.0,
                    "collider_friction": 0.0},
                   {"ground_y": -0.5, "ground_friction": 0.0,
                    "collider_friction": 1.0},
                   {"ground_y": -0.5, "ground_friction": 1.0,
                    "collider_friction": None}):
            info = run(**kw)
            rows.append(info)
            cf = ("なし" if kw["collider_friction"] is None
                  else f"{kw['collider_friction']}")
            print(f"   {kw['ground_y']:>12} {kw['ground_friction']:>12} "
                  f"{cf:>14} {info['slid']:>12.6f} "
                  f"{info.get('vx_mean', 0):>12.6f}")
        with open(os.path.join(OUT, "069_d.json"), "w",
                  encoding="utf-8") as fp:
            json.dump(rows, fp, ensure_ascii=False, indent=2)
        print("\n保存: out/069_d.json")
    elif arg == "e":
        # 実験062〜065と同じ組み方（落とすだけ）で、床の箱があってもなくても
        # 同じ結果になるかを確かめる。推測で済ませないための一手間。
        import hou
        import numpy

        def drop(with_floor):
            hou.hipFile.clear(suppress_save_prompt=True)
            hou.playbar.setFrameRange(1, 30)
            geo = hou.node("/obj").createNode("geo", "mpm")
            box = geo.createNode("box", "box")
            box.parmTuple("size").set((1.0, 1.0, 1.0))
            box.parmTuple("t").set((0.0, 3.0, 0.0))
            container = geo.createNode("mpmcontainer", "container")
            container.parm("particlesep").set(0.12)
            container.parm("sizex").set(8.0)
            container.parm("sizey").set(6.0)
            container.parm("sizez").set(8.0)
            container.parm("centery").set(2.0)
            source = geo.createNode("mpmsource", "source")
            source.setInput(0, box)
            source.setInput(1, container)
            solver = geo.createNode("mpmsolver", "solve")
            solver.setInput(0, source)
            solver.setInput(2, container)
            if with_floor:
                # 実験062〜065で置いていたのと同じ板（上面がちょうど y = 0）
                ground = geo.createNode("box", "ground")
                ground.parmTuple("size").set((6.0, 0.4, 6.0))
                ground.parmTuple("t").set((0.0, -0.2, 0.0))
                collider = geo.createNode("mpmcollider", "collider")
                collider.setInput(0, ground)
                collider.setInput(1, container)
                solver.setInput(1, collider)
            solver.setDisplayFlag(True)
            for frame in range(1, 31):
                hou.setFrame(frame)
                solver.geometry()
            g = solver.geometry()
            pts = numpy.asarray([[p.position()[0], p.position()[1],
                                  p.position()[2]] for p in g.points()])
            je = numpy.asarray([p.attribValue("Je") for p in g.points()])
            jp = numpy.asarray([p.attribValue("Jp") for p in g.points()])
            return {"floor": with_floor, "count": int(len(pts)),
                    "y_mean": float(pts[:, 1].mean()),
                    "y_top": float(pts[:, 1].max()),
                    "spread": float(max(pts[:, 0].max() - pts[:, 0].min(),
                                        pts[:, 2].max() - pts[:, 2].min())),
                    "J": float((je * jp).mean())}

        print("E. 実験062〜065と同じ組み方で、床の箱があってもなくても同じか")
        print(f"   {'床の箱':>8} {'粒':>7} {'高さの平均':>12} {'いちばん上':>12} "
              f"{'広がり':>10} {'Je × Jp':>12}")
        rows = []
        for with_floor in (True, False):
            r = drop(with_floor)
            rows.append(r)
            print(f"   {'あり' if with_floor else 'なし':>8} {r['count']:>7,} "
                  f"{r['y_mean']:>12.6f} {r['y_top']:>12.6f} "
                  f"{r['spread']:>10.6f} {r['J']:>12.6f}")
        a, b = rows
        print(f"\n   高さの差: {abs(a['y_mean'] - b['y_mean']):.9f}")
        print(f"   広がりの差: {abs(a['spread'] - b['spread']):.9f}")
        print(f"   Je × Jp の差: {abs(a['J'] - b['J']):.9f}")
        with open(os.path.join(OUT, "069_e.json"), "w",
                  encoding="utf-8") as fp:
            json.dump(rows, fp, ensure_ascii=False, indent=2)
        print("\n保存: out/069_e.json")
    elif arg == "merge":
        merge()
    elif arg == "shot":
        shot()
