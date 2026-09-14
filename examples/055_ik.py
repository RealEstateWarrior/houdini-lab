"""実験055 — 逆運動学（IK）。届かない場所を指したらどうなるか。

ここまでは関節を1つずつ回して形を作ってきた（順運動学）。
IK はその逆で、<strong>先端を「ここに来い」と指定すると、途中の関節が勝手に決まる</strong>。

APEX の部品 <code>rig::TwoBoneIK</code> を使う。入力は 4×4 の行列で
root / mid / tip / goal、出力は解けた3つの行列。
実験050で組んだグラフの作り方がそのまま使える。

骨は (0,0,0) → (0,1,0) → (0,2,0) の3関節。<strong>長さは 1 と 1 なので、
根元から先端までは最大でも 2 までしか届かない。</strong>

先に式を立てる。目標までの距離を d とすると

    d ≤ 2 なら   誤差 = 0
    d > 2 なら   誤差 = d − 2（まっすぐ伸びきって、そこで止まる）

  A. 目標を近くから遠くまで動かして、誤差を測る
  B. 骨の長さは保たれるか
  C. stretch を入れると何が変わるか

    hython examples/055_ik.py
    hython examples/055_ik.py shot reach
    hython examples/055_ik.py shot far
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

RES = (620, 620)
DISTANCES = (0.5, 1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 3.0, 4.0)
REACH = 2.0
DIRECTION = (1.0, 1.0, 0.0)
JOINTS = {"root": (0.0, 0.0, 0.0), "mid": (0.0, 1.0, 0.0),
          "tip": (0.0, 2.0, 0.0)}


def target_at(distance):
    length = math.sqrt(sum(v * v for v in DIRECTION))
    return tuple(v / length * distance for v in DIRECTION)


def solve(target, stretch=False, blend=1.0):
    """APEX のグラフを1つ組んで、その場で解く。"""
    import apex
    import hou

    g = apex.Graph()
    ik = g.addNode("ik", "rig::TwoBoneIK")
    ports = {g.portName(p): p for p in g.getInputPorts(ik)}

    values = dict(JOINTS)
    values["goal"] = target
    for name, pos in values.items():
        node = g.addNode("v_" + name, "Value<Matrix4>")
        g.setNodeParm(node, "parm", hou.hmath.buildTranslate(*pos))
        g.addWire(g.getOutputPorts(node)[0], ports[name])

    g.setNodeParm(ik, "blend", blend)
    g.setNodeParm(ik, "stretch", bool(stretch))
    for name in ("rootout", "midout", "tipout"):
        g.addGraphOutput(ik, name)
    g.compileProgram()
    g.executeProgram()

    out = {}
    for name in ("rootout", "midout", "tipout"):
        m = g.getNodeOutputData("ik", name)
        out[name] = (float(m.at(3, 0)), float(m.at(3, 1)), float(m.at(3, 2)))
    return out, g


def main():
    stats = {"reach": REACH, "direction": list(DIRECTION),
             "joints": {k: list(v) for k, v in JOINTS.items()}}

    print("A・B. 目標を近くから遠くまで動かす")
    print(f"   {'目標まで':>10} {'先端の位置':>30} {'誤差 実測':>12} "
          f"{'誤差 予測':>12} {'差':>13} {'骨1':>10} {'骨2':>10}")
    rows = []
    for distance in DISTANCES:
        target = target_at(distance)
        out, _ = solve(target)
        tip = out["tipout"]
        error = math.dist(tip, target)
        want = max(0.0, distance - REACH)
        bone1 = math.dist(out["rootout"], out["midout"])
        bone2 = math.dist(out["midout"], out["tipout"])
        rows.append({"distance": distance, "tip": list(tip),
                     "target": list(target), "error": error,
                     "expected": want, "diff": error - want,
                     "bone1": bone1, "bone2": bone2})
        print(f"   {distance:>10.2f} ({tip[0]:8.5f},{tip[1]:8.5f},"
              f"{tip[2]:8.5f}) {error:>12.7f} {want:>12.7f} "
              f"{error - want:>+13.9f} {bone1:>10.6f} {bone2:>10.6f}")
    worst = max(abs(r["diff"]) for r in rows)
    lengths = [r["bone1"] for r in rows] + [r["bone2"] for r in rows]
    spread = max(lengths) - min(lengths)
    print(f"\n   式とのずれの最大: {worst:.9f}")
    print(f"   式どおりか: {'はい' if worst < 1e-5 else 'いいえ'}")
    print(f"   骨の長さ: {min(lengths):.6f} 〜 {max(lengths):.6f}"
          f"（幅 {spread:.9f}）")
    print(f"   長さは保たれたか: {'はい' if spread < 1e-5 else 'いいえ'}")
    stats["rows"] = rows
    stats["worst"] = worst
    stats["length_spread"] = spread

    print("\nC. stretch を入れると何が変わるか")
    print(f"   {'目標まで':>10} {'誤差':>13} {'骨1':>10} {'骨2':>10} "
          f"{'合計 ÷ 2':>12}")
    srows = []
    for distance in (1.0, 2.0, 2.5, 3.0, 4.0):
        target = target_at(distance)
        out, _ = solve(target, stretch=True)
        tip = out["tipout"]
        error = math.dist(tip, target)
        bone1 = math.dist(out["rootout"], out["midout"])
        bone2 = math.dist(out["midout"], out["tipout"])
        srows.append({"distance": distance, "error": error,
                      "bone1": bone1, "bone2": bone2,
                      "ratio": (bone1 + bone2) / REACH})
        print(f"   {distance:>10.2f} {error:>13.9f} {bone1:>10.6f} "
              f"{bone2:>10.6f} {(bone1 + bone2) / REACH:>12.6f}")
    stats["stretch"] = srows
    far = [r for r in srows if r["distance"] > REACH]
    if far:
        worst_far = max(r["error"] for r in far)
        print(f"   届かない距離でも目標に届くか: "
              f"{'はい' if worst_far < 1e-5 else 'いいえ'}"
              f"（誤差の最大 {worst_far:.9f}）")
        print(f"   そのぶん骨が伸びる。いちばん伸びた比: "
              f"{max(r['ratio'] for r in far):.6f}")
        stats["stretch_worst"] = worst_far

    print("\nD. blend を変えると、途中で止まるか")
    print(f"   {'blend':>8} {'先端の位置':>30} {'元からの移動':>14} "
          f"{'目標までの残り':>16}")
    brows = []
    target = target_at(1.5)
    rest_tip = JOINTS["tip"]
    for blend in (0.0, 0.25, 0.5, 0.75, 1.0):
        out, _ = solve(target, blend=blend)
        tip = out["tipout"]
        moved = math.dist(tip, rest_tip)
        left = math.dist(tip, target)
        brows.append({"blend": blend, "tip": list(tip), "moved": moved,
                      "left": left})
        print(f"   {blend:>8.2f} ({tip[0]:8.5f},{tip[1]:8.5f},"
              f"{tip[2]:8.5f}) {moved:>14.6f} {left:>16.6f}")
    stats["blend"] = brows

    with open(os.path.join(OUT, "055_stats.json"), "w",
              encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    # 組んだグラフを図にする
    graph = {
        "title": "実験055 — 二骨IK のグラフ",
        "network": "apex::Graph（rig::TwoBoneIK）",
        "houdini_version": "21.0.700",
        "nodes": [
            {"name": "v_root", "type": "Value<Matrix4>", "pos": [-2.6, 3.0],
             "flags": {"display": False}, "params": {"parm": "(0, 0, 0)"}},
            {"name": "v_mid", "type": "Value<Matrix4>", "pos": [-0.9, 3.0],
             "flags": {"display": False}, "params": {"parm": "(0, 1, 0)"}},
            {"name": "v_tip", "type": "Value<Matrix4>", "pos": [0.9, 3.0],
             "flags": {"display": False}, "params": {"parm": "(0, 2, 0)"}},
            {"name": "v_goal", "type": "Value<Matrix4>", "pos": [2.6, 3.0],
             "flags": {"display": False}, "params": {"parm": "目標の位置"}},
            {"name": "ik", "type": "rig::TwoBoneIK", "pos": [0.0, 1.3],
             "flags": {"display": True},
             "params": {"blend": 1.0, "stretch": False}},
        ],
        "edges": [
            {"from": "v_root", "from_output": 0, "to": "ik", "to_input": 0},
            {"from": "v_mid", "from_output": 0, "to": "ik", "to_input": 1},
            {"from": "v_tip", "from_output": 0, "to": "ik", "to_input": 2},
            {"from": "v_goal", "from_output": 0, "to": "ik", "to_input": 3},
        ],
    }
    with open(os.path.join(OUT, "055_graph.json"), "w",
              encoding="utf-8") as fp:
        json.dump(graph, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/055_stats.json, out/055_graph.json")


def shot(case):
    """解いた結果を、骨の形にして撮る。"""
    import hou
    import hou_tools

    distance = 1.5 if case == "reach" else 4.0
    target = target_at(distance)
    out, _ = solve(target)

    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "ikshot")
    build = geo.createNode("attribwrangle", "build")
    build.parm("class").set(0)
    pts = [out["rootout"], out["midout"], out["tipout"]]
    lines = ['int prim = addprim(0, "polyline");']
    for p in pts:
        lines.append(f'addvertex(0, prim, addpoint(0, set({p[0]!r}, '
                     f'{p[1]!r}, {p[2]!r})));')
    build.parm("snippet").set("\n".join(lines))

    wire = geo.createNode("polywire", "bones")
    wire.setFirstInput(build)
    wire.parm("radius").set(0.06)

    joint_ball = geo.createNode("sphere", "jointball")
    joint_ball.parm("type").set(2)
    joint_ball.parm("rows").set(14)
    joint_ball.parm("cols").set(14)
    joint_ball.parmTuple("rad").set((0.1, 0.1, 0.1))
    show_j = geo.createNode("copytopoints::2.0", "show_joints")
    show_j.setInput(0, joint_ball)
    show_j.setInput(1, build)

    goal_pt = geo.createNode("attribwrangle", "goal")
    goal_pt.parm("class").set(0)
    goal_pt.parm("snippet").set(
        f'addpoint(0, set({target[0]!r}, {target[1]!r}, {target[2]!r}));')
    goal_ball = geo.createNode("sphere", "goalball")
    goal_ball.parm("type").set(2)
    goal_ball.parm("rows").set(16)
    goal_ball.parm("cols").set(16)
    goal_ball.parmTuple("rad").set((0.14, 0.14, 0.14))
    show_g = geo.createNode("copytopoints::2.0", "show_goal")
    show_g.setInput(0, goal_ball)
    show_g.setInput(1, goal_pt)

    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, wire)
    merged.setInput(1, show_j)
    merged.setInput(2, show_g)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()

    bbox = hou.BoundingBox(-0.5, -0.5, -0.5, 3.2, 3.2, 0.5)
    png = os.path.join(OUT, f"055_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.0, 0.0, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/055_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
