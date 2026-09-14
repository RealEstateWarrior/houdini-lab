"""実験056 — 長い鎖の IK。関節が増えても式は同じか。

実験055では関節3つ（骨2本）の IK を測り、
<strong>届く距離までは誤差ゼロ、越えたら d − 2</strong>という式にぴたり乗った。

関節が増えたらどうなるか。骨の長さが1のまま n 本つながっているなら、
届く距離は素直に n のはずだ。

    誤差 = max(0, 目標までの距離 − 骨の本数)

使うのは APEX の <code>rig::MultiBoneIKFromArray</code>。
関節の行列の配列を渡すと、解けた配列が返る。

  A. 関節の数を 3 / 5 / 9 / 17 と変えて、式どおりか確かめる
  B. 骨の長さは保たれるか
  C. <code>solver</code> の値を変えると何が変わるか

    hython examples/056_longchain.py
    hython examples/056_longchain.py shot short
    hython examples/056_longchain.py shot long
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

RES = (620, 620)
COUNTS = (3, 5, 9, 17)
FRACTIONS = (0.3, 0.7, 0.95, 1.0, 1.05, 1.5)
DIRECTION = (1.0, 1.0, 0.0)


def target_at(distance):
    length = math.sqrt(sum(v * v for v in DIRECTION))
    return tuple(v / length * distance for v in DIRECTION)


def solve(count, target, solver=None, blend=1.0):
    """関節 count 個の鎖を、目標に向けて解く。"""
    import apex
    import hou

    g = apex.Graph()
    ik = g.addNode("ik", "rig::MultiBoneIKFromArray")
    ports = {g.portName(p): p for p in g.getInputPorts(ik)}

    chain = apex.Matrix4Array(
        [hou.hmath.buildTranslate(0.0, float(i), 0.0)
         for i in range(count)])
    node = g.addNode("v_in", "Value<Matrix4Array>")
    g.setNodeParm(node, "parm", chain)
    g.addWire(g.getOutputPorts(node)[0], ports["in"])

    goal = g.addNode("v_goal", "Value<Matrix4>")
    g.setNodeParm(goal, "parm", hou.hmath.buildTranslate(*target))
    g.addWire(g.getOutputPorts(goal)[0], ports["goal"])

    g.setNodeParm(ik, "blend", blend)
    if solver is not None:
        g.setNodeParm(ik, "solver", solver)
    g.addGraphOutput(ik, "out")
    g.compileProgram()
    g.executeProgram()
    out = g.getNodeOutputData("ik", "out")
    points = [(float(m.at(3, 0)), float(m.at(3, 1)), float(m.at(3, 2)))
              for m in out]
    return points, g


def bone_lengths(points):
    return [math.dist(a, b) for a, b in zip(points, points[1:])]


def main():
    stats = {"counts": list(COUNTS), "fractions": list(FRACTIONS)}

    print("A・B. 関節の数を変えて、式どおりか確かめる")
    print(f"   {'関節':>5} {'骨':>4} {'届く距離':>9} {'目標まで':>10} "
          f"{'誤差 実測':>12} {'誤差 予測':>12} {'差':>14} "
          f"{'骨の長さの幅':>14}")
    rows = []
    for count in COUNTS:
        reach = float(count - 1)
        for frac in FRACTIONS:
            distance = reach * frac
            target = target_at(distance)
            points, _ = solve(count, target)
            tip = points[-1]
            error = math.dist(tip, target)
            want = max(0.0, distance - reach)
            lengths = bone_lengths(points)
            spread = max(lengths) - min(lengths)
            rows.append({"count": count, "bones": count - 1,
                         "reach": reach, "distance": distance,
                         "error": error, "expected": want,
                         "diff": error - want,
                         "length_spread": spread,
                         "length_mean": sum(lengths) / len(lengths)})
            print(f"   {count:>5} {count - 1:>4} {reach:>9.1f} "
                  f"{distance:>10.3f} {error:>12.7f} {want:>12.7f} "
                  f"{error - want:>+14.9f} {spread:>14.9f}")
    worst = max(abs(r["diff"]) for r in rows)
    worst_len = max(r["length_spread"] for r in rows)
    print(f"\n   式とのずれの最大: {worst:.9f}")
    print(f"   式どおりか: {'はい' if worst < 1e-4 else 'いいえ'}")
    print(f"   骨の長さの幅の最大: {worst_len:.9f}")
    print(f"   長さは保たれたか: {'はい' if worst_len < 1e-4 else 'いいえ'}")
    stats["rows"] = rows
    stats["worst"] = worst
    stats["worst_length_spread"] = worst_len

    print("\n   届かないとき、先端はどこで止まるか（関節9個・骨8本）")
    print(f"   {'目標まで':>10} {'先端までの距離':>16} {'骨の本数との差':>16}")
    stop = []
    for distance in (8.0, 9.0, 12.0, 20.0):
        target = target_at(distance)
        points, _ = solve(9, target)
        tip_dist = math.dist(points[0], points[-1])
        stop.append({"distance": distance, "tip_dist": tip_dist,
                     "diff": tip_dist - 8.0})
        print(f"   {distance:>10.1f} {tip_dist:>16.9f} "
              f"{tip_dist - 8.0:>+16.9f}")
    stats["stop"] = stop

    print("\nC. solver の値を変える（関節9個、目標まで 5.0）")
    print(f"   {'solver':>7} {'誤差':>12} {'骨の長さの幅':>14} "
          f"{'鎖の曲がり具合':>16} {'エラー'}")
    srows = []
    target = target_at(5.0)
    for solver in (0, 1, 2, 3):
        try:
            points, g = solve(9, target, solver=solver)
            err = math.dist(points[-1], target)
            lengths = bone_lengths(points)
            # 曲がり具合＝端から端までの直線距離 ÷ 鎖の長さ
            straight = math.dist(points[0], points[-1]) / sum(lengths)
            srows.append({"solver": solver, "error": err,
                          "length_spread": max(lengths) - min(lengths),
                          "straight": straight,
                          "errors": g.errors()[:1]})
            print(f"   {solver:>7} {err:>12.7f} "
                  f"{max(lengths) - min(lengths):>14.9f} "
                  f"{straight:>16.6f} {g.errors()[:1]}")
        except Exception as exc:  # noqa: BLE001
            srows.append({"solver": solver, "error": None,
                          "exception": str(exc)[:80]})
            print(f"   {solver:>7} 例外 {str(exc)[:60]}")
    stats["solvers"] = srows
    good = [r for r in srows if r.get("error") is not None]
    if len(good) > 1:
        same = (max(r["error"] for r in good)
                - min(r["error"] for r in good)) < 1e-6
        print(f"   どの値でも同じ結果か: {'はい' if same else 'いいえ'}")
        stats["solver_same"] = bool(same)

    with open(os.path.join(OUT, "056_stats.json"), "w",
              encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/056_stats.json")


def shot(case):
    import hou
    import hou_tools

    count = 5 if case == "short" else 17
    reach = float(count - 1)
    target = target_at(reach * 0.6)
    points, _ = solve(count, target)

    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "chain")
    build = geo.createNode("attribwrangle", "build")
    build.parm("class").set(0)
    lines = ['int prim = addprim(0, "polyline");']
    for p in points:
        lines.append(f'addvertex(0, prim, addpoint(0, set({p[0]!r}, '
                     f'{p[1]!r}, {p[2]!r})));')
    build.parm("snippet").set("\n".join(lines))

    wire = geo.createNode("polywire", "bones")
    wire.setFirstInput(build)
    wire.parm("radius").set(reach * 0.022)

    ball = geo.createNode("sphere", "jointball")
    ball.parm("type").set(2)
    ball.parm("rows").set(14)
    ball.parm("cols").set(14)
    r = reach * 0.035
    ball.parmTuple("rad").set((r, r, r))
    show = geo.createNode("copytopoints::2.0", "show_joints")
    show.setInput(0, ball)
    show.setInput(1, build)

    goal_pt = geo.createNode("attribwrangle", "goal")
    goal_pt.parm("class").set(0)
    goal_pt.parm("snippet").set(
        f'addpoint(0, set({target[0]!r}, {target[1]!r}, {target[2]!r}));')
    goal_ball = geo.createNode("sphere", "goalball")
    goal_ball.parm("type").set(2)
    goal_ball.parm("rows").set(16)
    goal_ball.parm("cols").set(16)
    gr = reach * 0.05
    goal_ball.parmTuple("rad").set((gr, gr, gr))
    show_g = geo.createNode("copytopoints::2.0", "show_goal")
    show_g.setInput(0, goal_ball)
    show_g.setInput(1, goal_pt)

    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, wire)
    merged.setInput(1, show)
    merged.setInput(2, show_g)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()

    span = reach * 1.15
    bbox = hou.BoundingBox(-span * 0.15, -span * 0.15, -span * 0.3,
                           span, span, span * 0.3)
    png = os.path.join(OUT, f"056_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.0, 0.0, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/056_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
