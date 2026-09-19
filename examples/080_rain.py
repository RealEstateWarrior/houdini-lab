"""実験080 — 雨を地面で跳ねさせる。Bounce の数字は、どれだけ跳ね返すか。

<a href="#exp079">実験079</a>で火花を散らした。今度は上から降らせて、地面に当てる。
POP では、地面は groundplane という DOP の物体で、粒とは merge でつなぐ。
地面にも粒（popobject）にも Bounce がある。

Bounce が「跳ね返る速さ ÷ 当たる速さ」（反発係数）なら、跳ね上がる高さは落とした高さの Bounce² 倍。
「高さの比」なら Bounce 倍。どちらかを、高さ 3 から落として決める。

  A. 地面の Bounce を 0.25 / 0.5 / 0.75 / 1.0 と変え、最初に跳ね上がった高さを測る（粒の Bounce は既定の 1）
  B. 地面 0.5 のまま、粒の Bounce を 0.5 にしたらどうなるか（2つは掛け算か）
  C. popsolver の Response を Die にすると、当たった粒は消えるか

    hython examples/080_rain.py a
    hython examples/080_rain.py c
    hython examples/080_rain.py shot
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

FPS = 24.0
DROP = 3.0


def build(ground_bounce=0.5, particle_bounce=1.0, response=None, rain=False, substeps=None):
    """rain が偽なら、高さ 3 の1点から 100粒を一度に落とす。真なら、上の板から降らせ続ける。"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 96)
    geo = hou.node("/obj").createNode("geo", "rain")

    if rain:
        cloud = geo.createNode("grid", "cloud")
        cloud.parmTuple("size").set((8.0, 8.0))
        cloud.parm("ty").set(6.0)
    else:
        cloud = geo.createNode("add", "cloud")
        cloud.parm("points").set(1)
        cloud.parm("usept0").set(1)
        cloud.parmTuple("pt0").set((0.0, DROP, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "drops")
    obj.parm("bounce").set(particle_bounce)
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    source.parm("soppath").set(cloud.path())
    source.parm("initvel").set("set")
    for axis in "xyz":
        source.parm(f"var{axis}").set(0.0)
    if rain:
        source.parm("emittype").set("surface")
        source.parm("constantrate").set(1500)
        source.parm("impulseactiveate").set(False)
        source.parm("vely").set(-6.0)
        source.parm("velx").set(1.0)                   # 少し斜めに降らせる
        source.parm("life").set(3.0)
    else:
        source.parm("emittype").set("point")
        source.parm("constantactivate").set(False)
        source.parm("impulseactiveate").set(True)
        source.parm("impulserate").setExpression("if($FF == 1, 100, 0)")
        source.parm("life").set(100.0)

    grav = dop.createNode("popforce", "gravity")
    grav.parmTuple("force").set((0.0, -9.81, 0.0))
    solver.setInput(0, obj)
    solver.setInput(1, grav)
    solver.setInput(2, source)
    if response:
        solver.parm("collisionresponse").set(response)
    if substeps:
        solver.parm("substep").set(substeps) if solver.parm("substep") else None

    ground = dop.createNode("groundplane", "ground")
    ground.parm("bounce").set(ground_bounce)
    merge = dop.createNode("merge", "merge")
    merge.setInput(0, ground)
    merge.setInput(1, solver)
    merge.setDisplayFlag(True)          # DOP の中は、表示フラグのノードまで計算される（実験079）
    dop.layoutChildren()

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("drops")
    imp.setDisplayFlag(True)
    imp.setRenderFlag(True)
    geo.layoutChildren()
    return geo, dop, imp


def drop_heights(imp, frames=72):
    import hou
    import hou_tools
    ys = []
    for frame in range(1, frames + 1):
        hou.setFrame(frame)
        g = imp.geometry()
        if g is None or not g.points():
            ys.append(None)
            continue
        ys.append(float(hou_tools.point_array(g)[:, 1].mean()))
    return ys


def first_bounce(ys):
    """いちばん下まで落ちたあと、次に上がりきった高さ。"""
    valid = [(i, y) for i, y in enumerate(ys) if y is not None]
    low_i = None
    for (i, y), (j, z) in zip(valid, valid[1:]):
        if z > y + 1e-6:
            low_i = i
            break
    if low_i is None:
        return None, None, None
    peak = max(y for i, y in valid if i >= low_i and i <= low_i + 40)
    return valid[low_i][1], peak, low_i + 1


def part_a():
    rows = []
    print("A. 高さ 3 から落として、最初に跳ね上がった高さ（粒の Bounce 1）")
    for gb, pb in ((0.25, 1.0), (0.5, 1.0), (0.75, 1.0), (1.0, 1.0), (0.5, 0.5), (1.0, 0.5)):
        geo, dop, imp = build(gb, pb)
        start = time.perf_counter()
        ys = drop_heights(imp)
        sec = time.perf_counter() - start
        low, peak, frame = first_bounce(ys)
        ratio = peak / DROP if peak is not None else None
        rows.append({"ground_bounce": gb, "particle_bounce": pb, "low": low, "peak": peak,
                     "low_frame": frame, "ratio": ratio, "ys": ys, "seconds": sec})
        print(f"   地面 {gb:<5} 粒 {pb:<4} | いちばん下 {low:.4f}（F{frame}） 跳ね上がり {peak:.4f} | "
              f"高さの比 {ratio:.4f} | Bounce² {gb * gb:.4f} Bounce {gb:.4f} | {sec:.2f}秒")
    with open(os.path.join(OUT, "080_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/080_a.json")


def part_c():
    import hou
    print("C. popsolver の Response を変えて、100粒を落とす（地面 Bounce 0.5）")
    rows = []
    for resp in ("none", "die", "stuck", "slide"):
        geo, dop, imp = build(0.5, 1.0, response=resp)
        counts = []
        for frame in range(1, 49):
            hou.setFrame(frame)
            g = imp.geometry()
            counts.append(len(g.points()) if g else 0)
        g = imp.geometry()
        ys = [p.position()[1] for p in g.points()] if g and g.points() else []
        hits = None
        if g and g.points() and g.findPointAttrib("hittotal"):
            hits = max(p.attribValue("hittotal") for p in g.points())
        row = {"response": resp, "counts": counts, "last_count": counts[-1],
               "y_last": (sum(ys) / len(ys)) if ys else None, "hittotal_max": hits}
        rows.append(row)
        print(f"   Response {resp:<7} | 粒の数 F12 {counts[11]} F24 {counts[23]} F48 {counts[47]} | "
              f"最後の高さ {row['y_last']} | hittotal の最大 {hits}")
    with open(os.path.join(OUT, "080_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/080_c.json")


def shot():
    """雨の完成形。上の板から斜めに降らせ、地面 Bounce 0.2 で小さく跳ねさせる。"""
    import hou
    import hou_tools
    geo, dop, imp = build(0.2, 1.0, rain=True)
    # 雨粒は、速さの向きに伸びた短い線にする（実験079の火花と同じ作り方）
    drops = geo.createNode("attribwrangle", "streaks")
    drops.setFirstInput(imp)
    drops.parm("class").set(0)
    drops.parm("snippet").set(
        "for (int i = 0; i < npoints(0); i++) {\n"
        "    vector p = point(0, 'P', i);\n"
        "    vector v = point(0, 'v', i);\n"
        "    int a = addpoint(0, p);\n"
        "    int b = addpoint(0, p - v * 0.035);\n"
        "    setpointattrib(0, 'Cd', a, {0.55, 0.7, 0.95});\n"
        "    setpointattrib(0, 'Cd', b, {0.25, 0.35, 0.6});\n"
        "    int prim = addprim(0, 'polyline');\n"
        "    addvertex(0, prim, a);\n"
        "    addvertex(0, prim, b);\n"
        "    removepoint(0, i);\n"
        "}")
    floor = geo.createNode("grid", "floor")
    floor.parmTuple("size").set((10.0, 10.0))
    both = geo.createNode("merge", "show")
    both.setInput(0, floor)
    both.setInput(1, drops)
    both.setDisplayFlag(True)
    both.setRenderFlag(True)
    geo.layoutChildren()
    start = time.perf_counter()
    for frame in range(1, 49):
        hou.setFrame(frame)
        imp.geometry()
    g = imp.geometry()
    low = sum(1 for p in g.points() if p.position()[1] < 0.5)
    print(f"48フレーム: {time.perf_counter() - start:.2f}秒 / {len(g.points())}粒（高さ 0.5 未満 {low}粒）")
    hou_tools.save_hip(os.path.join(OUT, "080_rain.hipnc"))
    bbox = hou.BoundingBox(-5.0, 0.0, -5.0, 5.0, 6.2, 5.0)
    png = os.path.join(OUT, "080_rain.png")
    hou_tools.render_preview(both.path(), png, res=(620, 460), direction=(0.6, 0.35, 1.0),
                             shading="smooth", frame_bbox=bbox, margin=1.02)
    print(f"保存: {png}")


if __name__ == "__main__":
    {"a": part_a, "c": part_c, "shot": shot}[sys.argv[1] if len(sys.argv) > 1 else "a"]()
