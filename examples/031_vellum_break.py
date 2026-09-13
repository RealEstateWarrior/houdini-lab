"""実験031 — Vellum の breaking は動く。ただし布の伸びには効かない。

実験028で布を破ろうとして、14通り試して1本も破れなかった。
原因は特定できず、3つの可能性を残した。今回それを潰す。

答えが出た。<strong>breaking は動く。</strong>ただし効く拘束の種類が決まっている。

  glue が作る stitch 拘束 … しきい値どおりに破れる
  cloth が作る distance / bend 拘束 … 同じ場面・同じしきい値でも1本も破れない

同じシーンの中で、cloth 側と glue 側の両方に breaking を入れて確かめた。
消えたのは stitch の12本だけ。distance 770本と bend 682本は1本も消えていない。
<strong>「設定が足りない」のではなく「この種類には効かない」だった。</strong>

もう1つ、028に書いた説明が逆だったことも分かった。
028では「破れた拘束は消えるのではなく broken グループに入る」と書いたが、
実際は<strong>破れた拘束は取り除かれ、broken グループは空のまま</strong>である。
12本が消えても broken は 0 のままだった。

    hython examples/031_vellum_break.py
    hython examples/031_vellum_break.py shot hold
    hython examples/031_vellum_break.py shot tear
"""

import json
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

LAST = 40
SHOT_FRAME = 20
SHOT_RES = (480, 620)
BBOX_PATH = os.path.join(OUT, "031_bbox.json")
TINY = 1e-6


# ---------- 場面1: 吊るした布の下に、もう1枚を glue でくっつける ----------

def build_glue(break_cloth=False, break_glue=False, threshold=TINY,
               last=LAST):
    """上の布を吊るし、下の布を glue で留める。

    下の布の重さは12本の stitch 拘束だけが支える。
    破れれば下の布は落ちるので、最下点を見れば分かる。
    """
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "glue")

    top = geo.createNode("grid", "top")
    top.parm("orient").set(0)          # XY 平面。縦に立てる
    top.parm("sizex").set(2.0)
    top.parm("sizey").set(2.0)
    top.parm("rows").set(12)
    top.parm("cols").set(12)
    top.parmTuple("t").set((0, 4.0, 0))

    bottom = geo.createNode("grid", "bottom")
    bottom.parm("orient").set(0)
    bottom.parm("sizex").set(2.0)
    bottom.parm("sizey").set(2.0)
    bottom.parm("rows").set(12)
    bottom.parm("cols").set(12)
    bottom.parmTuple("t").set((0, 2.02, 0))   # 上の布のすぐ下に置く

    merge = geo.createNode("merge", "merge")
    merge.setInput(0, top)
    merge.setInput(1, bottom)

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(merge)
    pins.parm("snippet").set("if (@P.y > 4.9) { @group_pins = 1; }")

    cloth = geo.createNode("vellumconstraints", "cloth")
    cloth.setFirstInput(pins)
    cloth.parm("constrainttype").set("cloth")
    cloth.parm("stretchstiffness").set(1.0)
    if break_cloth:
        cloth.parm("dobreaking").set(True)
        cloth.parm("breakthreshold").set(threshold)

    glue = geo.createNode("vellumconstraints", "glue")
    glue.setInput(0, cloth, 0)
    glue.setInput(1, cloth, 1)
    glue.parm("constrainttype").set("glue")
    if break_glue:
        glue.parm("dobreaking").set(True)
        glue.parm("breakthreshold").set(threshold)

    pin = geo.createNode("vellumconstraints", "pin")
    pin.setInput(0, glue, 0)
    pin.setInput(1, glue, 1)
    pin.parm("constrainttype").set("pin")
    pin.parm("grouptype").set("points")
    pin.parm("group").set("pins")

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, pin, 0)
    solver.setInput(1, pin, 1)
    solver.parm("startframe").set(1)

    geo.layoutChildren()
    return geo, pin, solver


# ---------- 場面2: 028 と同じ、上端だけで吊るしたカーテン ----------

def build_curtain(kind, threshold, last=LAST):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "curtain")

    cloth = geo.createNode("grid", "cloth")
    cloth.parm("orient").set(0)
    cloth.parm("sizex").set(4.0)
    cloth.parm("sizey").set(4.0)
    cloth.parm("rows").set(20)
    cloth.parm("cols").set(20)
    cloth.parmTuple("t").set((0, 2.2, 0))

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(cloth)
    pins.parm("snippet").set("if (@P.y > 4.1) { @group_pins = 1; }")

    con = geo.createNode("vellumconstraints", "con")
    con.setFirstInput(pins)
    con.parm("constrainttype").set(kind)
    if con.parm("stretchstiffness") is not None:
        con.parm("stretchstiffness").set(1.0)
    if threshold is not None:
        con.parm("dobreaking").set(True)
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
    return geo, pin, solver


# ---------- 場面3: DOP レベル ----------

def build_dop(freq, threshold, last=LAST):
    """SOP 版の中の配線をまねて、DOP を自分で組む。

    こうすると breakfrequency（破れ判定の頻度）を自分で指定できる。
    SOP 版にはこのパラメータが出ていない。
    """
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "dop_tear")

    cloth = geo.createNode("grid", "cloth")
    cloth.parm("orient").set(0)
    cloth.parm("sizex").set(4.0)
    cloth.parm("sizey").set(4.0)
    cloth.parm("rows").set(20)
    cloth.parm("cols").set(20)
    cloth.parmTuple("t").set((0, 2.2, 0))

    pins = geo.createNode("attribwrangle", "make_pins")
    pins.setFirstInput(cloth)
    pins.parm("snippet").set("if (@P.y > 4.1) { @group_pins = 1; }")

    con = geo.createNode("vellumconstraints", "con")
    con.setFirstInput(pins)
    con.parm("constrainttype").set("cloth")
    con.parm("stretchstiffness").set(1.0)
    con.parm("dobreaking").set(True)
    con.parm("breakthreshold").set(threshold)

    pin = geo.createNode("vellumconstraints", "pin")
    pin.setInput(0, con, 0)
    pin.setInput(1, con, 1)
    pin.parm("constrainttype").set("pin")
    pin.parm("grouptype").set("points")
    pin.parm("group").set("pins")

    geom_out = geo.createNode("null", "geo_out")
    geom_out.setInput(0, pin, 0)
    cons_out = geo.createNode("null", "constraints_out")
    cons_out.setInput(0, pin, 1)

    dop = geo.createNode("dopnet", "vellumnet")
    obj = dop.createNode("vellumobject", "cloth_object")
    obj.parm("displaysoppath").set(geom_out.path())
    obj.parm("constraintsoppath").set(cons_out.path())

    solver = dop.createNode("vellumsolver", "solve")
    solver.parm("breakfrequency").set(freq)
    solver.setInput(0, obj)

    # DOP では、力のノードがソルバの下流に並ぶ
    gravity = dop.createNode("gravity", "gravity")
    gravity.setInput(0, solver)
    gravity.setDisplayFlag(True)

    # 拘束ジオメトリは geodatapath に ConstraintGeometry を入れて取り出す
    cons_in = geo.createNode("dopimport", "import_cons")
    cons_in.parm("doppath").set(dop.path())
    cons_in.parm("objpattern").set("*")
    cons_in.parm("geodatapath").set("ConstraintGeometry")

    mesh_in = geo.createNode("dopimport", "import_mesh")
    mesh_in.parm("doppath").set(dop.path())
    mesh_in.parm("objpattern").set("*")
    mesh_in.setDisplayFlag(True)
    return geo, cons_out, cons_in, mesh_in


def breakdown(geometry):
    counts = {}
    for prim in geometry.prims():
        key = prim.attribValue("type")
        counts[key] = counts.get(key, 0) + 1
    return counts


def lowest_of(node):
    geometry = node.geometry()
    return min(p.position()[1] for p in geometry.points())


def main():
    stats = {"threshold": TINY, "last": LAST}

    print("1. 同じ場面で、どの種類の拘束が破れるか（しきい値 0.000001）")
    kinds = []
    for label, bc, bg in (("どちらも breaking なし", False, False),
                          ("glue だけ breaking", False, True),
                          ("cloth だけ breaking", True, False),
                          ("両方に breaking", True, True)):
        geo, pin, solver = build_glue(bc, bg)
        before = breakdown(pin.geometry(1))
        hou.setFrame(LAST)
        after = breakdown(solver.geometry(1))
        group = solver.geometry(1).findPrimGroup("broken")
        row = {
            "label": label, "break_cloth": bc, "break_glue": bg,
            "before": before, "after": after,
            "gone": {k: before.get(k, 0) - after.get(k, 0) for k in before},
            "broken_group": len(group.prims()) if group else None,
            "lowest": lowest_of(solver),
        }
        kinds.append(row)
        print(f"   {label:24s} 消えた {row['gone']} / "
              f"broken グループ {row['broken_group']} / "
              f"最下点 {row['lowest']:8.4f}")
    stats["kinds"] = kinds

    print("\n2. しきい値を変える（glue に breaking）")
    sweep = []
    print(f"   {'しきい値':>12} {'F3':>6} {'F10':>6} {'F40':>6} {'最下点':>10}")
    for threshold in (None, TINY, 1.0, 10.0, 100.0, 1000.0):
        geo, pin, solver = build_glue(False, threshold is not None,
                                      threshold or TINY)
        counts = {}
        for frame in (3, 10, LAST):
            hou.setFrame(frame)
            counts[frame] = len(solver.geometry(1).prims())
        row = {"threshold": threshold, "counts": counts,
               "lowest": lowest_of(solver)}
        sweep.append(row)
        label = "なし" if threshold is None else f"{threshold}"
        print(f"   {label:>12} {counts[3]:>6} {counts[10]:>6} "
              f"{counts[LAST]:>6} {row['lowest']:>10.4f}")
    stats["threshold_sweep"] = sweep

    print("\n3. 028 のカーテンで、cloth と distance を比べる")
    curtains = []
    for kind, threshold in (("cloth", None), ("cloth", TINY),
                            ("distance", None), ("distance", TINY),
                            ("distance", 10.0)):
        geo, pin, solver = build_curtain(kind, threshold)
        before = len(pin.geometry(1).prims())
        hou.setFrame(LAST)
        after = len(solver.geometry(1).prims())
        row = {"kind": kind, "threshold": threshold, "before": before,
               "after": after, "lowest": lowest_of(solver)}
        curtains.append(row)
        label = "なし" if threshold is None else f"{threshold}"
        print(f"   {kind:9s} しきい値 {label:>10} : "
              f"{before} → {after}（{after - before:+d}） "
              f"最下点 {row['lowest']:.4f}")
    stats["curtains"] = curtains

    print("\n4. DOP レベルで breakfrequency を指定しても同じか")
    dops = []
    for freq in ("never", "perframe", "persubstep"):
        geo, cons_out, cons_in, mesh_in = build_dop(freq, TINY)
        before = len(cons_out.geometry().prims())
        hou.setFrame(LAST)
        after = len(cons_in.geometry().prims())
        row = {"breakfrequency": freq, "before": before, "after": after,
               "lowest": lowest_of(mesh_in)}
        dops.append(row)
        print(f"   breakfrequency {freq:11s}: {before} → {after}"
              f"（{after - before:+d}） 最下点 {row['lowest']:.4f}")
    stats["dop"] = dops

    broke = any(any(v for v in r["gone"].values()) for r in kinds)
    print(f"\n   どこかで拘束が消えたか: {'はい' if broke else 'いいえ'}")
    stats["anything_broke"] = broke

    with open(os.path.join(OUT, "031_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, pin, solver = build_glue(False, True)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "031_graph.json"),
                          title="実験031 — Vellum の breaking")
    hou_tools.save_hip(os.path.join(OUT, "031_break.hipnc"))
    print("\n保存: out/031_stats.json, out/031_graph.json, out/031_break.hipnc")


def shot(case):
    """F20 を1枚撮る。レンダはプロセスの最後に1枚だけ（実験027で学んだ癖）。"""
    geo, pin, solver = build_glue(False, case == "tear")
    hou.setFrame(SHOT_FRAME)

    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = solver.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"031_{case}.png")
    hou_tools.render_preview(solver.path(), png, res=SHOT_RES,
                             direction=(0.2, 0.22, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.08)
    print(f"保存: out/031_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
