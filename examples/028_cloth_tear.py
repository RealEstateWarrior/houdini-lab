"""実験028 — 布は破れなかった。Vellum の breaking はどこまで効かないのか。

実験015で布を垂らした。今回はそれを<strong>破る</strong>つもりだった。

<code>vellumconstraints</code> には <code>dobreaking</code>（既定でオフ）と
<code>breakthreshold</code>（既定 0.1）がある。しきい値を下げれば破れやすくなるはずである。

結果を先に書く。<strong>1つも破れなかった。</strong>
しきい値を 1.0 から 0.000001 まで下げても、破れ方の種類を3つとも試しても、
布を100倍重くして応力を1万倍にしても、切れた拘束は<strong>ゼロのまま</strong>だった。

「効かない」を主張するには、効くはずの条件を潰しきる必要がある。順に潰した。

  1. しきい値が高すぎた？      → 0.000001 まで下げた
  2. 破れ方の種類が違う？      → 応力・距離・伸び率の3つとも試した
  3. 力が足りない？            → 重さを100倍にして応力を1万倍にした
  4. 拘束の型が対象外？        → 作られている型を読んで確かめた
  5. ソルバが判定を切っている？→ 中を開いて設定を読んだ

    hython examples/028_cloth_tear.py          … 証拠を集める
    hython examples/028_cloth_tear.py shot off … 画を1枚撮る
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

LAST = 48
SHOT_RES = (520, 520)
BBOX_PATH = os.path.join(OUT, "028_bbox.json")

# breaktypestretch のメニュー索引。0 は none。
BREAK_TYPES = {1: "stretchstress", 2: "stretchdistance", 3: "stretchratio"}

CASES = {
    "off": None,
    "t100": 1.0,
    "t050": 0.5,
    "t020": 0.2,
    "t010": 0.1,      # 既定値
    "t005": 0.05,
    "t002": 0.02,
}


def build(threshold, breaktype=1, stiffness=1.0, mass=None, last=LAST):
    """上の辺だけで吊るしたカーテン。全重量が上端の拘束にかかる。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "tear")

    cloth = geo.createNode("grid", "cloth")
    cloth.parm("orient").set(0)          # XY 平面。縦に立てる
    cloth.parm("sizex").set(4.0)
    cloth.parm("sizey").set(4.0)
    cloth.parm("rows").set(40)
    cloth.parm("cols").set(40)
    cloth.parmTuple("t").set((0, 2.2, 0))

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(cloth)
    # 上の辺の1列だけを留める。ここに布の全重量がかかる。
    snippet = "if (@P.y > 4.1) { @group_pins = 1; }"
    if mass is not None:
        snippet += f"\n@mass = {mass};"
    pins.parm("snippet").set(snippet)

    con = geo.createNode("vellumconstraints", "con")
    con.setFirstInput(pins)
    con.parm("constrainttype").set("cloth")
    con.parm("stretchstiffness").set(stiffness)
    if threshold is not None:
        con.parm("dobreaking").set(True)
        con.parm("breaktypestretch").set(breaktype)
        con.parm("breakthreshold").set(threshold)

    pin = geo.createNode("vellumconstraints", "pin")
    pin.setInput(0, con, 0)
    pin.setInput(1, con, 1)
    pin.parm("constrainttype").set("pin")
    pin.parm("grouptype").set("points")
    pin.parm("group").set("pins")

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, pin, 0)
    solver.setInput(1, pin, 1)
    solver.parm("startframe").set(1)

    # つながった塊の数を数えるため、connectivity で class を振る。
    conn = geo.createNode("connectivity", "conn")
    conn.setFirstInput(solver)
    conn.parm("connecttype").set(1)      # 点でつながっているか

    geo.layoutChildren()
    return geo, cloth, pin, solver, conn


def longest_edge(geometry):
    longest = 0.0
    for prim in geometry.prims():
        points = [v.point().position() for v in prim.vertices()]
        for i in range(len(points)):
            length = (points[i] - points[(i + 1) % len(points)]).length()
            longest = max(longest, length)
    return longest


def pieces(geometry):
    """connectivity が振った class の種類数＝つながった塊の数。"""
    if geometry.findPointAttrib("class") is not None:
        return len({p.attribValue("class") for p in geometry.points()})
    if geometry.findPrimAttrib("class") is not None:
        return len({p.attribValue("class") for p in geometry.prims()})
    raise RuntimeError("class アトリビュートが無い")


def measure(threshold, breaktype=1, stiffness=1.0, mass=None, last=LAST):
    geo, cloth, pin, solver, conn = build(threshold, breaktype, stiffness,
                                          mass, last)
    rest = cloth.geometry()
    rest_points = len(rest.points())
    rest_edge = longest_edge(rest)
    before = len(pin.geometry(1).prims())

    hou.setFrame(last)
    sim = solver.geometry()
    cons = solver.geometry(1)
    group = cons.findPrimGroup("broken")
    stresses = [p.attribValue("stress") for p in cons.prims()
                if p.attribValue("type") == "distance"]

    return {
        "threshold": threshold,
        "breaktype": BREAK_TYPES.get(breaktype) if threshold is not None else None,
        "stiffness": stiffness,
        "mass": mass,
        "frame": last,
        "rest_points": rest_points,
        "rest_longest_edge": rest_edge,
        "constraints_in": before,
        "constraints_out": len(cons.prims()),
        "broken": len(group.prims()) if group else 0,
        "points": len(sim.points()),
        "prims": len(sim.prims()),
        "pieces": pieces(conn.geometry()),
        "longest_edge": longest_edge(sim),
        "max_stress": max(stresses) if stresses else 0.0,
        "lowest": min(p.position()[1] for p in sim.points()),
    }


def environment():
    """「ソルバが判定を切っているのでは」を潰すための事実集め。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "env")
    grid = geo.createNode("grid", "g")
    grid.parm("orient").set(0)
    grid.parm("rows").set(10)
    grid.parm("cols").set(10)

    con = geo.createNode("vellumconstraints", "con")
    con.setFirstInput(grid)
    con.parm("constrainttype").set("cloth")
    con.parm("dobreaking").set(True)

    kinds = {}
    for prim in con.geometry(1).prims():
        key = f"{prim.attribValue('type')} / {prim.attribValue('breaktype')}"
        kinds[key] = kinds.get(key, 0) + 1

    solver = geo.createNode("vellumsolver", "solve")
    facts = {
        "constraint_kinds": kinds,
        "solvermode": solver.parm("solvermode").rawValue(),
        "sop_has_breakfrequency": solver.parm("breakfrequency") is not None,
        "normalizestress": solver.parm("normalizestress").eval(),
    }

    # SOP の中の DOP ソルバが、破れ判定をどの頻度で回しているか
    try:
        solver.allowEditingOfContents()
        for child in solver.allSubChildren():
            if child.type().name() == "vellumsolver":
                parm = child.parm("breakfrequency")
                if parm is not None:
                    facts["dop_breakfrequency"] = parm.rawValue()
                break
    except hou.Error as exc:
        facts["dop_breakfrequency"] = f"読めなかった: {exc}"
    return facts


def main():
    stats = {}

    print("0. 環境の事実")
    facts = environment()
    stats["facts"] = facts
    for key, value in facts.items():
        print(f"   {key}: {value}")

    print("\n1. しきい値を下げていく（破れ方の種類は既定の stretchstress）")
    rows = []
    header = (f"{'しきい値':>10} {'切れた拘束':>10} {'拘束':>8} {'点':>7} "
              f"{'塊':>4} {'一番長い辺':>12} {'最下点':>9}")
    print(header)
    for case, threshold in CASES.items():
        row = measure(threshold)
        row["case"] = case
        rows.append(row)
        label = "なし" if threshold is None else f"{threshold}"
        print(f"{label:>10} {row['broken']:>10} {row['constraints_out']:>8} "
              f"{row['points']:>7} {row['pieces']:>4} "
              f"{row['longest_edge']:>12.5f} {row['lowest']:>9.4f}")
    stats["threshold_sweep"] = rows

    same = all(abs(r["longest_edge"] - rows[0]["longest_edge"]) < 1e-9
               and r["lowest"] == rows[0]["lowest"] for r in rows)
    print(f"\n   全ケースで結果が同一か: {'はい' if same else 'いいえ'}")
    stats["threshold_sweep_identical"] = same

    print("\n2. 破れ方の種類を変える（しきい値 0.000001）")
    kinds = []
    for index, name in BREAK_TYPES.items():
        row = measure(1e-6, breaktype=index)
        kinds.append(row)
        print(f"   {name:16s} 切れた拘束 {row['broken']:5d} / "
              f"{row['constraints_out']} 応力の最大 {row['max_stress']:.3f}")
    stats["breaktype_sweep"] = kinds

    print("\n3. 力を強くする（しきい値 0.000001・stretchdistance）")
    loads = []
    for stiffness, mass in ((1.0, None), (0.01, None), (0.001, None),
                            (0.001, 100.0)):
        row = measure(1e-6, breaktype=2, stiffness=stiffness, mass=mass)
        loads.append(row)
        print(f"   stiffness {stiffness:<6} 重さ {mass or 1}: "
              f"切れた拘束 {row['broken']:5d} 応力の最大 "
              f"{row['max_stress']:10.3f} 一番長い辺 {row['longest_edge']:.5f}")
    stats["load_sweep"] = loads

    broke_anything = any(r["broken"] for r in rows + kinds + loads)
    print(f"\n   どこかで1つでも切れたか: {'はい' if broke_anything else 'いいえ'}")
    stats["broke_anything"] = broke_anything

    with open(os.path.join(OUT, "028_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    # 接続図は最後に1つだけ作る（レンダはしないので固まらない）
    geo, cloth, pin, solver, conn = build(0.1)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "028_graph.json"),
                          title="実験028 — 布は破れなかった")
    hou_tools.save_hip(os.path.join(OUT, "028_tear.hipnc"))
    print("\n保存: out/028_stats.json, out/028_graph.json, out/028_tear.hipnc")


def shot(case):
    """F48 を1枚撮る。レンダはプロセスの最後に1枚だけ（実験027で学んだ癖）。"""
    threshold = CASES[case]
    geo, cloth, pin, solver, conn = build(threshold)
    hou.setFrame(LAST)

    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = hou_tools.bbox_over_frames(solver.path(), [LAST])
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"028_{case}.png")
    hou_tools.render_preview(solver.path(), png, res=SHOT_RES,
                             direction=(0.15, 0.18, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.08)
    print(f"保存: out/028_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
