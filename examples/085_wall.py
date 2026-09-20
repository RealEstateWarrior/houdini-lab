"""実験085 — 壁を崩す。破片の数は時間にどう効くか。速さで壊れ方はどう変わるか。

3 × 2 × 0.25 の壁を rbdmaterialfracture（Concrete）で割り、
半径 0.25 の球を横からぶつける。

  A. 破片の数（Scatter Points）を 10 / 25 / 50 / 100 と変える。
     実際にできる破片の数、割るのにかかる時間、解くのにかかる時間を測る
  B. 球の速さを 2 / 5 / 8 / 12 と変える。動いた破片の数と、いちばん動いた距離を測る

    hython examples/085_wall.py a
    hython examples/085_wall.py b
    hython examples/085_wall.py shot 8
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 60
STRENGTH = 100.0     # B で決めた「崩れる強さ」。1000 では無傷だった
BALL_R = 0.25


def build(pieces=25, speed=8.0, strength=None):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "wall")

    wall = geo.createNode("box", "wall_box")
    wall.parmTuple("size").set((3.0, 2.0, 0.25))
    wall.parm("ty").set(1.0)

    frac = geo.createNode("rbdmaterialfracture", "fracture")
    frac.setFirstInput(wall)
    frac.parm("materialtype").set("concrete")
    frac.parm("concrete_fracturelevel").set(1)
    frac.parm("concrete_scatterpts1").set(pieces)
    if strength is not None:
        frac.parm("concrete_primarystrength").set(strength)

    ball = geo.createNode("sphere", "ball")
    ball.parm("type").set(2)
    ball.parmTuple("rad").set((BALL_R, BALL_R, BALL_R))
    ball.parm("rows").set(14)
    ball.parm("cols").set(20)
    ball.parmTuple("t").set((-2.0, 1.0, 0.0))

    # 破片は「name で区切られたポリゴン」として解かれるので、球も同じ形に合わせる。
    # packed のまま混ぜると、球だけが動いて壁は無反応だった
    name = geo.createNode("attribwrangle", "name_ball")
    name.setFirstInput(ball)
    name.parm("class").set(1)
    name.parm("snippet").set('s@name = "ball";')

    hit = geo.createNode("attribwrangle", "throw")
    hit.setFirstInput(name)
    hit.parm("class").set(2)                      # 点
    hit.parm("snippet").set(f"v@v = set({speed}, 0, 0);")

    both = geo.createNode("merge", "all")
    both.setInput(0, frac)
    both.setInput(1, hit)

    solver = geo.createNode("rbdbulletsolver", "solve")
    solver.setFirstInput(both)
    solver.setInput(1, frac, 1)        # 破片をつなぐ拘束
    solver.parm("useground").set(True)
    solver.parm("startframe").set(1)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, frac, solver


def centers(node):
    """破片ごとの位置。1つの破片は複数のポリゴンでできているので、name でまとめる。"""
    import numpy
    g = node.geometry()
    names = g.primStringAttribValues("name")
    sums, counts = {}, {}
    for prim, name in zip(g.prims(), names):
        pts = [v.point().position() for v in prim.vertices()]
        c = [sum(p[k] for p in pts) / len(pts) for k in range(3)]
        if name in sums:
            sums[name] = [sums[name][k] + c[k] for k in range(3)]
            counts[name] += 1
        else:
            sums[name], counts[name] = c, 1
    return {n: numpy.array([sums[n][k] / counts[n] for k in range(3)]) for n in sums}


def run(pieces=25, speed=8.0, strength=None):
    import hou
    import numpy
    hou_start = time.perf_counter()
    geo, frac, solver = build(pieces, speed, strength)
    frac.cook(force=True)
    frac_sec = time.perf_counter() - hou_start
    n_pieces = frac.geometry().intrinsicValue("primitivecount")

    hou.setFrame(1)
    first = centers(solver)
    start = time.perf_counter()
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        solver.geometry()
    sim_sec = time.perf_counter() - start
    last = centers(solver)
    moved = {n: float(numpy.linalg.norm(last[n] - first[n])) for n in first if n in last}
    wall = [v for n, v in moved.items() if n != "ball"]
    return {"pieces_asked": pieces, "speed": speed, "strength": strength, "pieces": len(wall),
            "fracture_prims": int(n_pieces), "fracture_sec": frac_sec, "sim_sec": sim_sec,
            "moved_over_01": int(sum(1 for v in wall if v > 0.1)),
            "moved_max": max(wall), "moved_mean": sum(wall) / len(wall),
            "ball_moved": moved.get("ball", 0.0)}


def show(r):
    print(f"   破片 {r['pieces_asked']:>4} 速さ {r['speed']:>5} 強さ {str(r.get('strength')):>8} | 破片 {r['pieces']:>4}個"
          f"（面 {r['fracture_prims']}枚） | 割る {r['fracture_sec']:.2f}秒 解く {r['sim_sec']:.2f}秒 | "
          f"0.1 以上動いた破片 {r['moved_over_01']:>4} | いちばん動いた {r['moved_max']:.3f} "
          f"平均 {r['moved_mean']:.3f} | 球 {r['ball_moved']:.3f}")


def part_a():
    print("A. 破片の数を変える（球の速さ 8・強さ 100）")
    rows = []
    for pieces in (10, 25, 50, 100, 200):
        r = run(pieces, 8.0, STRENGTH)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "085_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/085_a.json")


def part_b():
    print("B. 拘束の強さ（Primary Strength）を変える（破片 25・速さ 8）")
    rows = []
    for strength in (10000.0, 1000.0, 100.0, 10.0, 1.0, 0.0):
        r = run(25, 8.0, strength)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "085_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/085_b.json")


def part_c():
    print("C. 球の速さを変える（破片 25・崩れる強さで）")
    rows = []
    for speed in (2.0, 5.0, 8.0, 12.0):
        r = run(25, speed, STRENGTH)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "085_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/085_c.json")


def shot(speed="8", frame="40"):
    import hou
    import hou_tools
    geo, frac, solver = build(25, float(speed), STRENGTH)
    frame = int(frame)
    for f in range(1, frame + 1):
        hou.setFrame(f)
        solver.geometry()
    if speed == "8":
        hou_tools.save_hip(os.path.join(OUT, "085_wall.hipnc"))
    bbox = hou.BoundingBox(-2.6, -0.1, -1.6, 2.6, 2.4, 1.6)
    png = os.path.join(OUT, f"085_wall_{int(float(speed))}_{frame}.png")
    hou_tools.render_preview(solver.path(), png, res=(680, 400), direction=(0.45, 0.25, 1.0),
                             shading="smoothwire", frame_bbox=bbox, margin=1.03)
    print(f"保存: {png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "shot":
        shot(*(sys.argv[2:4] or ["8"]))
    else:
        {"a": part_a, "b": part_b, "c": part_c}[arg]()
