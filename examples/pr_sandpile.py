# -*- coding: utf-8 -*-
"""実践「砂の柱が崩れて山になる」— MPM の砂で円柱を作り、支えを外したように崩して、円すいの山にする。

本物の乾いた砂は、筒に詰めて筒を抜くと崩れて広がり、決まった傾き（安息角、乾いた砂でおよそ30〜35度）の山で止まる。
MPM（粒と格子を行き来して計算する方法）の砂の設定で、この崩れ方と止まり方が出る。

    hython examples/pr_sandpile.py
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 72     # 3 秒
SEP = 0.02
PRESET = "sidefx::recipe::sop/mpmsource::material_{}"


def run(solver, last):
    import hou
    t0 = time.perf_counter()
    for f in range(1, last + 1):
        hou.setFrame(f)
        solver.geometry()
    return time.perf_counter() - t0


def pile_shape(solver):
    """山の高さと、根元の半径（粒の 95% が入る半径）と、傾き（度）。"""
    pts = [p.position() for p in solver.geometry().points()]
    top = max(p[1] for p in pts)
    rs = sorted(math.hypot(p[0], p[2]) for p in pts)
    r95 = rs[int(len(rs) * 0.95)]
    return top, r95, math.degrees(math.atan2(top, r95))


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("sandpile", "砂の柱が崩れて山になる",
                  "MPM の砂で円柱を作り、崩す。支えの無い砂は広がりながら崩れ、低い山になって止まる。"
                  "MPM は「容器（計算する範囲と粒の細かさ）」「湧かせる物」「ぶつかる物」「計算」の4つのノードで組む。",
                  tags=["シミュレーション", "MPM", "砂", "Karma"])
    g.shot_dir = (1.0, 0.45, 1.2)
    column = g.node("tube", "sand_column", type="poly", rad=(0.25, 0.25), height=0.9, cols=40, cap=1, t=(0, 0.45, 0))
    box = g.node("mpmcontainer", "container", particlesep=SEP, sizex=3.0, sizey=1.4, sizez=3.0, centery=0.6)
    src = g.node("mpmsource", "sand", [column, box])
    src.parm("materialpreset").set(PRESET.format("sand"))
    src.parm("materialtype").set("sandy")   # プリセットの名前を入れただけでは Chunky（塊）のままだった
    g.step(src, "砂の柱を用意する",
           "<code>tube</code> で半径 25 cm・高さ 90 cm の円柱を作る。<code>mpmcontainer</code> は計算する範囲（3 × 1.4 × 3 m）と、"
           f"粒の間隔 <strong>Particle Separation {SEP}</strong>（2 cm）を決める。<code>mpmsource</code> の左に円柱、右に容器をつなぎ、"
           "<strong>Material Preset を Sand</strong>（砂）にし、<strong>Material Type を Sandy</strong> にする。"
           "円柱の中が、2 cm おきの砂粒で満たされる。",
           cap="砂粒で満たした円柱。", shading="smooth", ui_parm="materialpreset",
           bbox=hou.BoundingBox(-0.9, 0, -0.9, 0.9, 1.0, 0.9))

    floor = g.node("box", "floor", size=(3.0, 0.2, 3.0), t=(0, -0.1, 0))
    hit = g.node("mpmcollider", "floor_collider", [floor, box])
    solver = g.node("mpmsolver", "collapse", [src, hit, box])
    sim_sec = run(solver, LAST)
    n = len(solver.geometry().points())
    top, r95, ang = pile_shape(solver)
    g.step(solver, "床の上で崩す",
           "床の <code>box</code> を <code>mpmcollider</code>（ぶつかる物）にする。左に床、右に容器。"
           "<code>mpmsolver</code> には、左から砂・床・容器の3本をつなぐ。再生すると、支えの無い砂の柱は自分の重さで崩れ、広がって止まる。"
           f"{n:,} 粒・{LAST} フレーム（3 秒）の計算は {sim_sec:.0f} 秒。止まった山は高さ {top:.2f} m、根元の半径 {r95:.2f} m。",
           cap=f"フレーム {LAST}。低く広がった山になって止まった。", shading="smooth", ui_parm="materialpreset",
           bbox=hou.BoundingBox(-0.9, 0, -0.9, 0.9, 1.0, 0.9))

    grains = g.node("attribwrangle", "grain_look", [solver], snippet=(
        "// 粒の大きさと色。砂は1粒ずつ明るさが違う\n"
        "f@pscale = chf('size') * fit01(rand(@ptnum), 0.8, 1.2);\n"
        "v@Cd = {0.78, 0.64, 0.44} * fit01(rand(@ptnum + 3), 0.75, 1.15);"))
    kit_spare(grains, size=SEP * 0.6)
    sand = g.mat("sand_mat", basecolor=(1, 1, 1), rough=0.9, reflect=0.2)
    wood = g.mat("floor_mat", basecolor=(0.35, 0.3, 0.26), rough=0.7)
    final = g.node("merge", "sandbox", [g.assign(grains, sand, "assign_sand"), g.assign(floor, wood, "assign_floor")])
    g.step(final, "粒の見た目を決める",
           "<code>attribwrangle</code> で粒ごとに大きさ <strong>pscale</strong>（間隔の 0.6 倍を 0.8〜1.2 倍にばらつかせる）と、"
           "明るさの違う砂色 Cd を付ける。Karma は、面の無い点を pscale の大きさの小さな球として撮る。材質は Base Color を白にして Cd を使う。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {LAST}）。崩れて止まった砂山。", frame=LAST,
           direction=(1.0, 0.35, 1.2), key=3.2, rim=5.0, dome=0.4, spp=48, margin=1.1, backdrop=(0.3, 0.27, 0.24),
           bbox=hou.BoundingBox(-0.8, 0, -0.8, 0.8, 0.5, 0.8))
    g.anim(final, (1, LAST), "砂の柱が崩れて、山になって止まるまで（72 フレーム＝3 秒）。",
           bbox=hou.BoundingBox(-0.9, 0, -0.9, 0.9, 1.0, 0.9), direction=(1.0, 0.45, 1.2))

    # ---- 落とし穴を測る ----
    src.parm("materialtype").set("chunky")
    run(solver, LAST)
    c_top, c_r95, c_ang = pile_shape(solver)
    src.parm("materialtype").set("sandy")
    run(solver, LAST)
    traps = [
        {"title": "Material Type を Sandy にしないと崩れない",
         "body": f"Material Preset を Sand にしただけだと Material Type は Chunky（塊）のままで、3 秒たっても高さ {c_top:.2f} m・"
                 f"半径 {c_r95:.2f} m と、柱が立ったままだった。Sandy にすると高さ {top:.2f} m・半径 {r95:.2f} m まで崩れた。",
         "img": "", "cap": ""},
        {"title": "崩れた山の傾き",
         "body": f"止まった山の「高さ ÷ 粒の 95% が入る半径」から出した傾きは {ang:.0f}度。裾に広がった粒も半径に入るので、"
                 "斜面そのものの傾きよりゆるく出る測り方。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "9個（材質2つ）"], ["砂粒", f"{n:,}個"], [f"{LAST} フレームの計算", f"{sim_sec:.0f}秒"]],
           traps=traps)


def kit_spare(node, **values):
    """wrangle の chf のつまみを作って値を入れる（GUI の「Create spare parameters」ボタンと同じこと）。"""
    import hou
    group = node.parmTemplateGroup()
    for name, value in values.items():
        group.append(hou.FloatParmTemplate(name, name, 1, default_value=(value,)))
    node.setParmTemplateGroup(group)
    for name, value in values.items():
        node.parm(name).set(value)


if __name__ == "__main__":
    main()
