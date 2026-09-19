"""実験071 — 回る台は、上に乗った塊をどう振り回すか。

<a href="#exp070">実験070</a>では板をまっすぐ動かした。今度は<strong>台を回す</strong>。
レコード盤の上に物を置いたようなもの。

回る台の上の物は、摩擦で台に引っぱられて一緒に回る。
一緒に回るには、中心へ向かう力 m ω² r が要る。それを出せるのは摩擦だけで、上限は μ m g。
だから、

    ω² r ＜ μ g   なら、台に乗ったまま回る
    ω² r ＞ μ g   なら、外へ滑り出す

境目は ω = √(μ g ÷ r)。これを否定できる形で確かめる。

  A. 半径 r = 2 に置いて、回す速さ ω を変える（境目は √(9.81 ÷ 2) = 2.215 rad/秒）
  B. ω = 2 に固定して、置く半径 r を変える（境目は 9.81 ÷ 4 = 2.45）
  C. 台に乗って回っているとき、塊の回る速さは台の ω と一致するか

組み込みの地面は切る（実験069）。コライダは Animated (Rigid)（実験070）。

    hython examples/071_mpm_spin.py a
    hython examples/071_mpm_spin.py b
    python  examples/071_mpm_spin.py merge
    hython examples/071_mpm_spin.py shot stay
    hython examples/071_mpm_spin.py shot fling
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 72
FPS = 24.0
SEP = 0.12
G = 9.81
SIZE = 0.6            # 塊の1辺。半径に比べて小さくしておく
FRAMES = (12, 24, 36, 48, 60, 72)


def build(omega, radius=2.0, friction=1.0):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "spin")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((SIZE, SIZE, SIZE))
    box.parmTuple("t").set((radius, SIZE / 2 + 0.02, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(SEP)
    container.parm("sizex").set(16.0)
    container.parm("sizey").set(4.0)
    container.parm("sizez").set(16.0)
    container.parm("centery").set(1.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    # 回る台。上面が y = 0 の円盤を、y 軸まわりに ω rad/秒で回す
    disk = geo.createNode("tube", "disk")
    disk.parm("type").set(1)
    disk.parm("cap").set(True)
    disk.parm("rad1").set(6.0)
    disk.parm("rad2").set(6.0)
    disk.parm("height").set(0.4)
    disk.parm("cols").set(48)
    disk.parm("ty").set(-0.2)
    spin = geo.createNode("xform", "spin")
    spin.setFirstInput(disk)
    spin.parm("ry").setExpression(f"($FF - 1) / $FPS * {omega} * 180 / $PI")

    collider = geo.createNode("mpmcollider", "collider")
    collider.setInput(0, spin)
    collider.setInput(1, container)
    collider.parm("type").set(1)             # Animated (Rigid)
    collider.parm("friction").set(friction)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(1, collider)
    solver.setInput(2, container)
    solver.parm("groundactive").set(0)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver


def stats_of(node):
    import numpy
    g = node.geometry()
    pts = numpy.asarray([p.position() for p in g.points()], dtype=float)
    vel = numpy.asarray([p.attribValue("v") for p in g.points()], dtype=float)
    cx, cz = pts[:, 0].mean(), pts[:, 2].mean()
    r = math.hypot(cx, cz)
    # 各粒の、自分の位置での接線方向の速さ（反時計回りを正、上から見て）
    rr = numpy.hypot(pts[:, 0], pts[:, 2])
    tx, tz = -pts[:, 2] / rr, pts[:, 0] / rr
    tangential = vel[:, 0] * tx + vel[:, 2] * tz
    radial = (vel[:, 0] * pts[:, 0] + vel[:, 2] * pts[:, 2]) / rr
    return {"count": int(len(pts)), "r": r,
            "angle": math.atan2(cz, cx),
            "y_min": float(pts[:, 1].min()),
            "omega_block": float((tangential / rr).mean()),
            "v_tan": float(tangential.mean()),
            "v_rad": float(radial.mean())}


def run(omega, radius=2.0, friction=1.0):
    import hou
    geo, solver = build(omega, radius, friction)
    rows = []
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
        if frame == 1 or frame in FRAMES:
            s = stats_of(solver)
            s["frame"] = frame
            rows.append(s)
    seconds = time.perf_counter() - start
    # 塊が回った角度を、途中の値からつなぐ（±π をまたいでも切れないように）
    total = 0.0
    for a, b in zip(rows, rows[1:]):
        d = b["angle"] - a["angle"]
        d = (d + math.pi) % (2 * math.pi) - math.pi
        total += d
    t = (LAST - 1) / FPS
    last = rows[-1]
    return {"omega": omega, "radius": radius, "friction": friction,
            "r0": rows[0]["r"], "r_last": last["r"], "dr": last["r"] - rows[0]["r"],
            "turned": total, "turned_board": omega * t,
            "omega_block": last["omega_block"], "v_rad": last["v_rad"],
            "count": last["count"], "seconds": seconds, "frames": rows}


def critical_omega(radius, friction=1.0):
    return math.sqrt(friction * G / radius)


def print_row(info):
    wc = critical_omega(info["radius"], info["friction"])
    print(f"   ω {info['omega']:>5} r {info['radius']:>4} | 境目 ω {wc:6.3f} | "
          f"半径 {info['r0']:.4f} → {info['r_last']:.4f}（{info['dr']:+.4f}） | "
          f"塊の ω {info['omega_block']:.4f}（台の {info['omega_block'] / info['omega'] if info['omega'] else 0:.4f}倍） | "
          f"外向きの速さ {info['v_rad']:+.4f} | {info['count']}粒 {info['seconds']:.2f}秒")


def part(name, cases):
    rows = []
    for kw in cases:
        info = run(**kw)
        rows.append(info)
        print_row(info)
    with open(os.path.join(OUT, f"071_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"保存: out/071_{name}.json")


def part_a():
    print("A. 半径 2 に置いて、回す速さを変える（摩擦 1.0。境目 ω = 2.215）")
    part("a", [dict(omega=w) for w in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.4, 3.0)])


def find_edge(radius, friction, lo, hi, steps=6):
    """滑り出す境目の ω を挟み撃ちで探す。3秒で半径が 1.0 以上外へ動いたら「滑り出した」。"""
    tried = []
    for _ in range(steps):
        mid = 0.5 * (lo + hi)
        info = run(mid, radius, friction)
        flung = info["dr"] > 1.0
        tried.append({"omega": mid, "dr": info["dr"], "flung": flung,
                      "omega_ratio": info["omega_block"] / mid,
                      "seconds": info["seconds"]})
        print(f"     ω {mid:.4f} → 半径 {info['dr']:+.4f} {'滑り出した' if flung else '乗ったまま'}"
              f"（{info['seconds']:.2f}秒）")
        if flung:
            hi = mid
        else:
            lo = mid
    edge = 0.5 * (lo + hi)
    return {"radius": radius, "friction": friction, "lo": lo, "hi": hi, "edge": edge,
            "w2r": edge * edge * radius, "mu_eff": edge * edge * radius / G,
            "predicted": critical_omega(radius, friction), "tried": tried}


def edges(name, cases):
    rows = []
    for radius, friction, lo, hi in cases:
        print(f"   半径 {radius}・摩擦 {friction}（式の境目 ω {critical_omega(radius, friction):.4f}）")
        row = find_edge(radius, friction, lo, hi)
        rows.append(row)
        print(f"   → 境目 ω {row['lo']:.4f}〜{row['hi']:.4f}  ω²r = {row['w2r']:.4f}  "
              f"実効の摩擦 {row['mu_eff']:.4f}（式の {row['edge'] / row['predicted']:.4f}倍）")
    with open(os.path.join(OUT, f"071_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"保存: out/071_{name}.json")


def part_b():
    print("B. 置く半径を変えて、境目の ω を探す（摩擦 1.0）。式どおりなら ω²r が一定")
    edges("b", [(r, 1.0, 0.3, 3.5) for r in (1.0, 2.0, 3.0, 4.0)])


def part_c():
    print("C. 摩擦を変えて、境目の ω を探す（半径 2）。式どおりなら ω²r が摩擦に比例")
    edges("c", [(2.0, mu, 0.2, 3.5) for mu in (0.25, 0.5, 2.0)])


def shot(name):
    """72フレームを3フレームおきに重ねて、上から撮る。台の縁も描いておく。"""
    import hou
    import hou_tools
    omega = 1.0 if name == "stay" else 1.5
    geo, solver = build(omega)
    trail = hou.Geometry()
    trail.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    for frame in range(1, LAST + 1, 3):
        hou.setFrame(frame)
        u = (frame - 1) / float(LAST - 1)
        col = (0.15 + 0.75 * u, 0.25 + 0.45 * u, 0.55 + 0.35 * u)
        for p in solver.geometry().points():
            q = trail.createPoint()
            q.setPosition(p.position())
            q.setAttribValue("Cd", col)
    # 基準の円（半径 2 と 6）を点で描く
    for radius, col in ((2.0, (0.75, 0.75, 0.78)), (6.0, (0.55, 0.55, 0.6))):
        for i in range(360):
            a = math.radians(i)
            q = trail.createPoint()
            q.setPosition((radius * math.cos(a), 0.0, radius * math.sin(a)))
            q.setAttribValue("Cd", col)
    bgeo = os.path.join(OUT, f"071_{name}_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    bbox = hou.BoundingBox(-6.3, -0.2, -6.3, 6.3, 0.8, 6.3)
    png = os.path.join(OUT, f"071_{name}.png")
    hou_tools.render_preview(fnode.path(), png, res=(520, 520),
                             direction=(0.0, 1.0, 0.001), shading="smooth",
                             frame_bbox=bbox, margin=1.02)
    print(f"保存: out/071_{name}.png")


def scene():
    import hou_tools
    geo, solver = build(3.0)
    hou_tools.save_hip(os.path.join(OUT, "071_spin.hipnc"))
    print("保存: out/071_spin.hipnc")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part_a()
    elif arg == "b":
        part_b()
    elif arg == "c":
        part_c()
    elif arg == "test":
        print_row(run(float(sys.argv[2]) if len(sys.argv) > 2 else 3.0))
    elif arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "fling")
    elif arg == "scene":
        scene()
