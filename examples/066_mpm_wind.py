"""実験066 — MPM に風を当てる。空気抵抗と風速は、どちらが本体か。

mpmsolver には Wind Velocity と Air Drag が並んでいる。
どちらも既定は 0。<strong>では風速だけ上げたら、粒は流れるのか。</strong>

  A. 空気抵抗 0 のまま、風速だけ 0 → 10 に上げる
  B. 風なしで空気抵抗だけ変える。落下速度は v = -g/d (1 - e^(-dt)) に乗るか
  C. 空気抵抗を固定して風速を変える。横速度は風速に比例するか

一度に何度も組み直すと hython が止まるので、A / B / C を別々に走らせて
最後に足し合わせる。

    hython examples/066_mpm_wind.py a
    hython examples/066_mpm_wind.py b
    hython examples/066_mpm_wind.py c
    python  examples/066_mpm_wind.py merge
    hython examples/066_mpm_wind.py shot calm
    hython examples/066_mpm_wind.py shot wind
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

START_Y = 3.0
LAST = 24
FPS = 24.0
SEP = 0.12
G = 9.81


def build(drag, wind):
    """落ちるだけの箱。地面は消す（ぶつかると風の効きが読めなくなる）。"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "mpm")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    box.parmTuple("t").set((0.0, START_Y, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(SEP)
    container.parm("sizex").set(24.0)
    container.parm("sizey").set(16.0)
    container.parm("sizez").set(8.0)
    container.parm("centerx").set(6.0)
    container.parm("centery").set(-3.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)
    # mpmsolver は既定で y=0 に地面を持っている（groundactive=1）。
    # 落ちきってしまうと風の効きが読めないので切る。
    solver.parm("groundactive").set(0)
    solver.parm("airdrag").set(drag)
    solver.parm("windvelocityx").set(wind)
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
           "y_mean": float(pts[:, 1].mean())}
    if g.findPointAttrib("v"):
        vel = numpy.asarray([p.attribValue("v") for p in g.points()])
        out["vx_mean"] = float(vel[:, 0].mean())
        out["vy_mean"] = float(vel[:, 1].mean())
    return out


def run(drag, wind):
    import hou
    geo, solver = build(drag, wind)
    hou.setFrame(1)
    solver.geometry()
    start = time.perf_counter()
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
    info = stats_of(solver)
    info["drag"] = drag
    info["wind"] = wind
    info["seconds"] = time.perf_counter() - start
    return info


def part(name, cases, title):
    print(title)
    print(f"   {'空気抵抗':>9} {'風速':>7} {'粒':>7} {'x の平均':>12} "
          f"{'y の平均':>12} {'vx の平均':>12} {'vy の平均':>12} {'秒':>8}")
    rows = []
    for drag, wind in cases:
        info = run(drag, wind)
        rows.append(info)
        print(f"   {drag:>9} {wind:>7} {info['count']:>7,} "
              f"{info['x_mean']:>12.6f} {info['y_mean']:>12.6f} "
              f"{info.get('vx_mean', 0):>12.6f} {info.get('vy_mean', 0):>12.6f} "
              f"{info['seconds']:>7.2f}秒")
    path = os.path.join(OUT, f"066_{name}.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"\n保存: out/066_{name}.json")


def integrate(drag, wind, t, steps=200000):
    """dv/dt = g + d |w - v| (w - v) を刻んで解く（4次ルンゲクッタ）。

    速さの2乗に比例する抵抗。しかも <strong>3次元の相対速度の大きさ</strong>を
    使うので、横に吹く風が縦の落ち方まで変える。
    """
    gvec = (0.0, -G, 0.0)
    wvec = (wind, 0.0, 0.0)

    def accel(v):
        u = (wvec[0] - v[0], wvec[1] - v[1], wvec[2] - v[2])
        s = math.sqrt(u[0] * u[0] + u[1] * u[1] + u[2] * u[2])
        return (gvec[0] + drag * s * u[0],
                gvec[1] + drag * s * u[1],
                gvec[2] + drag * s * u[2])

    h = t / steps
    v = (0.0, 0.0, 0.0)
    for _ in range(steps):
        k1 = accel(v)
        k2 = accel(tuple(v[i] + h / 2 * k1[i] for i in range(3)))
        k3 = accel(tuple(v[i] + h / 2 * k2[i] for i in range(3)))
        k4 = accel(tuple(v[i] + h * k3[i] for i in range(3)))
        v = tuple(v[i] + h / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
                  for i in range(3))
    return v


def merge():
    rows = {}
    for name in ("a", "b", "c"):
        with open(os.path.join(OUT, f"066_{name}.json"), encoding="utf-8") as fp:
            rows[name] = json.load(fp)

    t = (LAST - 1) / FPS
    print(f"経過時間 t = {LAST - 1} / {FPS} = {t:.6f} 秒")
    print(f"抵抗なしの落下速度 g t = {G * t:.6f}\n")

    print("A. 空気抵抗 0 のまま、風速だけ上げる")
    print(f"   {'風速':>7} {'x の平均':>12} {'vx の平均':>12} {'y の平均':>12} "
          f"{'風速0との差':>14}")
    base = rows["a"][0]
    for r in rows["a"]:
        print(f"   {r['wind']:>7} {r['x_mean']:>12.6f} "
              f"{r.get('vx_mean', 0):>12.6f} {r['y_mean']:>12.6f} "
              f"{abs(r['x_mean'] - base['x_mean']):>14.9f}")

    print("\nB. 風なしで空気抵抗を変える。3つの式のどれに乗るか")
    print(f"   {'空気抵抗':>9} {'vy 実測':>12} {'速さに比例':>12} {'2乗に比例':>12} "
          f"{'終端速度':>12} {'実測 − 2乗':>12}")
    for r in rows["b"]:
        d = r["drag"]
        got = r.get("vy_mean", 0)
        lin = -G / d * (1.0 - math.exp(-d * t))
        quad = integrate(d, 0.0, t)[1]
        term = -math.sqrt(G / d)
        print(f"   {d:>9} {got:>12.6f} {lin:>12.6f} {quad:>12.6f} "
              f"{term:>12.6f} {got - quad:>12.6f}")

    print("\nC. 空気抵抗 1.0 で風速を変える。横速度は風速に比例するか")
    print(f"   {'風速':>7} {'vx 実測':>12} {'vx ÷ 風速':>12} {'2乗に比例':>12} "
          f"{'実測 − 式':>12} {'vy 実測':>12} {'vy 式':>12}")
    for r in rows["c"]:
        w = r["wind"]
        vx = r.get("vx_mean", 0)
        vy = r.get("vy_mean", 0)
        want = integrate(r["drag"], w, t)
        print(f"   {w:>7} {vx:>12.6f} {vx / w:>12.6f} {want[0]:>12.6f} "
              f"{vx - want[0]:>12.6f} {vy:>12.6f} {want[1]:>12.6f}")

    print("\n   「速さに比例」なら vx ÷ 風速 はどの風速でも同じ値になるはず: "
          f"{1.0 - math.exp(-rows['c'][0]['drag'] * t):.6f}")

    with open(os.path.join(OUT, "066_stats.json"), "w", encoding="utf-8") as fp:
        json.dump({"t": t, "rows": rows}, fp, ensure_ascii=False, indent=2)
    print("保存: out/066_stats.json")


def shot(case):
    """通った跡を1枚に重ねる。24フレーム分の粒をぜんぶ置く。"""
    import hou
    import hou_tools
    drag, wind = (1.0, 0.0) if case == "calm" else (1.0, 10.0)
    geo, solver = build(drag, wind)

    trail = hou.Geometry()
    trail.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        src = solver.geometry()
        # 古いほど暗く、新しいほど明るく
        u = (frame - 1) / float(LAST - 1)
        col = (0.15 + 0.75 * u, 0.25 + 0.45 * u, 0.55 + 0.35 * u)
        for p in src.points():
            q = trail.createPoint()
            q.setPosition(p.position())
            q.setAttribValue("Cd", col)

    bgeo = os.path.join(OUT, f"066_{case}_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    bbox = hou.BoundingBox(-1.0, -2.2, -1.0, 9.0, 3.6, 1.0)
    png = os.path.join(OUT, f"066_{case}.png")
    hou_tools.render_preview(fnode.path(), png, res=(760, 420),
                             direction=(0.0, 0.12, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    print(f"保存: out/066_{case}.png")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part("a", [(0.0, 0.0), (0.0, 2.0), (0.0, 5.0), (0.0, 10.0)],
             "A. 空気抵抗 0 のまま、風速だけ上げる")
    elif arg == "b":
        part("b", [(0.25, 0.0), (0.5, 0.0), (1.0, 0.0), (2.0, 0.0),
                   (4.0, 0.0)],
             "B. 風なしで空気抵抗だけ変える")
    elif arg == "c":
        part("c", [(1.0, 2.0), (1.0, 5.0), (1.0, 10.0)],
             "C. 空気抵抗 1.0 で風速を変える")
    elif arg == "merge":
        merge()
    elif arg == "shot":
        shot(sys.argv[2])
