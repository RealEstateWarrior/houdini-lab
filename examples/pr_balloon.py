# -*- coding: utf-8 -*-
"""実践「風船をふくらませる」— 布の袋に内側から圧力をかけてふくらませ、色違いを束ねて撮る。

    hython examples/pr_balloon.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

FRAME = 24


def run(solver, last):
    import hou
    t0 = time.perf_counter()
    for f in range(1, last + 1):
        hou.setFrame(f)
        solver.geometry()
    return time.perf_counter() - t0


def volume(geo):
    """閉じた面の体積（三角形ごとの符号付き体積を足す）。"""
    v = 0.0
    for p in geo.prims():
        ps = [x.point().position() for x in p.vertices()]
        for i in range(1, len(ps) - 1):
            v += ps[0].dot(ps[i].cross(ps[i + 1])) / 6.0
    return abs(v)


def main():
    import hou
    g = kit.Guide("balloon", "風船をふくらませる",
                  "しぼんだ風船を布（Vellum の cloth）で作り、内側から圧力（pressure）をかけてふくらませる。"
                  "どこまでふくらむかは、圧力と、ゴムの伸びにくさの綱引きで決まる。色違いを束ねて、パーティーの風船にする。",
                  tags=["シミュレーション", "Vellum", "複製", "Karma", "制作"])
    g.shot_dir = (0.9, 0.3, 1.2)
    ball = g.node("sphere", "rubber", type="polymesh", rows=24, cols=32, rad=(0.11, 0.13, 0.11))
    shape = g.node("attribwrangle", "teardrop", [ball],
                   snippet="// 下半分を細くして、風船のしずく形にする\n"
                           "if (@P.y < 0) {\n"
                           "    float k = fit(@P.y, -0.13, 0, 0.3, 1);\n"
                           "    @P.x *= k;  @P.z *= k;\n"
                           "}\n"
                           "// いちばん下の点を「knot」（結び目）にする\n"
                           "i@group_knot = @P.y < -0.125;")
    g.step(shape, "しぼんだ風船の形を作る",
           "<code>sphere</code> を Polygon Mesh・Rows 24・Columns 32 で置き、<code>attribwrangle</code> で下半分を細くしてしずく形にする。"
           "大きさはふくらんだ後の6割ほど（しぼんだ状態）。いちばん下の点は <strong>knot</strong>（結び目）というグループにする。",
           cap="しぼんだ小さい風船。", shading="smoothwire", ui_parm="snippet")
    skin = g.node("vellumconstraints", "rubber_skin", [shape], constrainttype="cloth", pingroup="knot",
                  stretchstiffness=1.0, stretchstiffnessexp=3)
    g.step(skin, "ゴムの膜にする",
           "<code>vellumconstraints</code> を <strong>Cloth</strong> にして、表面を伸び縮みする膜にする。"
           "<strong>Stretch の Stiffness を 1 × 10³</strong>（既定は 1 × 10¹⁰ でほとんど伸びない布）に下げて、ゴムのように伸びるようにする。"
           "Pin Points に knot と書いて、結び目を留める。",
           cap="見た目は同じ。膜のつながりが付いた。", shading="smoothwire", ui_parm="stretchstiffnessexp")
    air = g.node("vellumconstraints", "air_pressure", [skin], constrainttype="pressure", stretchrestscale=3.0)
    air.setInput(1, skin, 1)
    g.step(air, "中に空気を入れる",
           "もう1つ <code>vellumconstraints</code> をつなぎ（<strong>左右の出口を両方</strong>）、Type を <strong>Pressure</strong> にする。"
           "閉じた袋の体積を保とうとする拘束で、<strong>Rest Length Scale を 3</strong> にすると「今の3倍の体積が本来の大きさ」と思って、ふくらもうとする。",
           cap="見た目は同じ。圧力のつながりが足された。", shading="smoothwire", ui_parm="stretchrestscale")
    solver = g.node("vellumsolver", "inflate", [air], substeps=5, gravity=(0, 0, 0))
    solver.setInput(1, air, 1)
    v0 = volume(shape.geometry())
    sim_sec = run(solver, FRAME)
    v1 = volume(solver.geometry())
    g.step(solver, "ふくらませる",
           "<code>vellumsolver</code> に左右の出口をつなぎ、<strong>Gravity を 0</strong>（ヘリウム風船なので下に落とさない）、Substeps 5。"
           f"再生すると、数フレームでふくらむ。体積は {v0 * 1000:.1f} L から {v1 * 1000:.1f} L（{v1 / v0:.1f} 倍）になった。",
           cap=f"フレーム {FRAME}。ふくらんだ風船。", shading="smoothwire", ui_parm="gravity")
    spots = g.node("circle", "bunch", type="poly", orient="zx", radx=0.32, rady=0.32, divs=5)
    vary = g.node("attribwrangle", "place_balloons", [spots],
                  snippet="// 高さ・大きさ・傾き・色を1つずつ変える\n"
                          "@P.y = 1.1 + rand(@ptnum + 2) * 0.4;\n"
                          "@P *= set(1.3, 1, 1.3);  @P.y /= 1.3;\n"
                          "f@pscale = fit01(rand(@ptnum + 4), 1.5, 1.9);\n"
                          "vector out = normalize(set(@P.x, 3, @P.z));\n"
                          "p@orient = dihedral({0, 1, 0}, out);   // 束の外へ少し傾ける\n"
                          "vector palette[] = array({0.85, 0.08, 0.1}, {1.0, 0.72, 0.05}, {0.1, 0.4, 0.95},\n"
                          "                         {0.95, 0.35, 0.6}, {0.2, 0.7, 0.4});\n"
                          "v@Cd = palette[@ptnum % 5];")
    copies = g.node("copytopoints::2.0", "five_balloons", [solver, vary], targetattribs=1)
    copies.parm("applyto1").set("points")
    copies.parm("applyattribs1").set("Cd")
    g.step(copies, "色違いを5つ束ねる",
           "<code>circle</code> の5点に、<code>attribwrangle</code> で高さ・大きさ・傾き・色を付け、"
           "<code>copytopoints</code> でふくらんだ風船を並べる。色は Target Attributes で <strong>Points に Cd</strong> を移す（宝石の実践と同じく、既定では色は移らない）。",
           cap="高さと傾きの違う5つ。", shading="smoothwire", ui_parm="targetattribs")
    strings = g.node("attribwrangle", "strings", [vary], **{"class": 2},
                     snippet="// 風船の結び目から、下の重りまで糸を1本ずつ引く\n"
                             "vector knot = @P + qrotate(p@orient, {0, -0.13, 0}) * f@pscale;\n"
                             "int a = addpoint(0, knot);\n"
                             "int b = addpoint(0, {0, 0.12, 0});\n"
                             "int line = addprim(0, \"polyline\", a, b);\n"
                             "setpointattrib(0, \"width\", a, 0.006);\n"
                             "setpointattrib(0, \"width\", b, 0.006);\n"
                             "removepoint(0, @ptnum);\n"
                             "if (@ptnum == 0) removeprim(0, 0, 0);   // 並べるのに使った円の面は消す")
    weight = g.node("box", "weight", size=(0.14, 0.12, 0.14), t=(0, 0.06, 0))
    latex = g.mat("latex_mat", basecolor=(1, 1, 1), basecolor_usePointColor=1, rough=0.3, reflect=0.6, coat=1.0, coatrough=0.05)
    thread = g.mat("string_mat", basecolor=(0.9, 0.9, 0.88), rough=0.6)
    gold = g.mat("weight_mat", basecolor=(0.95, 0.7, 0.3), metallic=1.0, rough=0.25)
    final = g.node("merge", "party", [g.assign(copies, latex, "assign_latex"), g.assign(strings, thread, "assign_string"),
                                      g.assign(weight, gold, "assign_weight")])
    g.step(final, "糸と重りを足して、材質を当てる",
           "<code>attribwrangle</code> で、各風船の結び目から下の重りまで <code>addprim</code> で線を1本ずつ引く。"
           "並べるのに使った円の面は要らないので <code>removeprim</code> で消す。線の点に <strong>width</strong>（太さ 0.006）を付けると、Karma は線を糸として描く。"
           "風船の材質は <strong>Use Point Color</strong> で色を点から取り、Coat 1（表面のつや）でゴムらしい光り方にする。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム{FRAME}）。", direction=(0.7, 0.28, 1.2),
           key=3.2, rim=5.0, dome=0.45, spp=96, margin=0.95, frame=FRAME, backdrop=(0.8, 0.66, 0.58),
           bbox=hou.BoundingBox(-0.7, 0, -0.7, 0.7, 1.95, 0.7))

    # ---- 落とし穴を測る ----
    air.parm("stretchrestscale").set(1.0)
    run(solver, FRAME)
    v_rest1 = volume(solver.geometry())
    air.parm("stretchrestscale").set(3.0)
    skin.parm("stretchstiffnessexp").set(10)
    run(solver, FRAME)
    v_stiff = volume(solver.geometry())
    skin.parm("stretchstiffnessexp").set(3)
    knots = [pt.number() for pt in shape.geometry().points() if pt.position()[1] < -0.125]
    run(solver, FRAME)
    knot_pin = solver.geometry().point(knots[0]).position()[1]
    skin.parm("pingroup").set("")
    run(solver, FRAME)
    knot_free = solver.geometry().point(knots[0]).position()[1]
    skin.parm("pingroup").set("knot")
    run(solver, FRAME)
    traps = [
        {"title": "Rest Length Scale が 1 のままだと、ふくらまない",
         "body": f"Pressure の Rest Length Scale を 1 にすると、{FRAME} フレーム後の体積は {v_rest1 * 1000:.1f} L で、"
                 f"はじめ（{v0 * 1000:.1f} L）のまま。圧力は「今の体積を保つ」力なので、ふくらませたいときは 1 より大きくする。",
         "img": "", "cap": ""},
        {"title": "既定の布は、3倍にしても3倍にならない",
         "body": f"Rest Length Scale 3 でも、膜の Stiffness が既定（× 10¹⁰）だと体積は {v_stiff / v0:.2f} 倍にとどまった。"
                 f"× 10³ に下げると {v1 / v0:.2f} 倍。ふくらむ大きさは、圧力と膜の伸びにくさの綱引きで決まる。",
         "img": "", "cap": ""},
        {"title": "結び目を留めないと、束ねる位置がずれる",
         "body": f"結び目を留めると、ふくらんだあとも結び目は y = {knot_pin:.3f} m のまま。留めないと {knot_free:.3f} m に動いた"
                 f"（細いしずくの下側が丸くふくらむので、結び目が {(knot_free - knot_pin) * 100:.0f} cm 上へ引き込まれる）。糸をつなぐ点は先に留めておくと、あとで糸を引く位置が合う。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "13個（材質3つ）"], [f"{FRAME} フレームの計算", f"{sim_sec:.1f}秒"],
                  ["ふくらみ", f"{v1 / v0:.1f}倍"]], traps=traps)


if __name__ == "__main__":
    main()
