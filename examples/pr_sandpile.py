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
    """山の高さと、根元の半径（粒の 95% が入る半径）と、斜面の傾き（度）。
    傾きは、中心からの距離を 2 cm ごとに区切って、区切りごとのいちばん高い粒を取り、
    根元の半径の 20〜80% の範囲で「高さ ÷ 距離」の直線を当てはめて出す（裾の広がりに引っぱられない）。"""
    pts = [p.position() for p in solver.geometry().points()]
    top = max(p[1] for p in pts)
    rs = sorted(math.hypot(p[0], p[2]) for p in pts)
    r95 = rs[int(len(rs) * 0.95)]
    bins = {}
    for p in pts:
        k = int(math.hypot(p[0], p[2]) / 0.02)
        bins[k] = max(bins.get(k, 0.0), p[1])
    xs = [(k + 0.5) * 0.02 for k in bins if 0.2 * r95 <= (k + 0.5) * 0.02 <= 0.8 * r95]
    ys = [bins[int(x / 0.02)] for x in xs]
    if len(xs) < 2:
        return top, r95, 0.0
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return top, r95, math.degrees(math.atan(-slope))


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("sandpile", "砂の柱が崩れて山になる",
                  "MPM の砂で円柱を作り、崩す。支えの無い砂は広がりながら崩れ、低い山になって止まる。"
                  "MPM は「容器（計算する範囲と粒の細かさ）」「湧かせる物」「ぶつかる物」「計算」の4つのノードで組む。",
                  tags=["シミュレーション", "MPM", "砂", "Karma"])
    g.shot_dir = (1.0, 0.45, 1.2)
    column = g.node("tube", "sand_column", type="poly", rad=(0.3, 0.3), height=0.55, cols=40, cap=1, t=(0, 0.275, 0))
    box = g.node("mpmcontainer", "container", particlesep=SEP, sizex=3.0, sizey=1.4, sizez=3.0, centery=0.6)
    src = g.node("mpmsource", "sand", [column, box])
    src.parm("materialpreset").set(PRESET.format("sand"))
    src.parm("materialtype").set("sandy")   # プリセットの名前を入れただけでは Chunky（塊）のままだった
    src.parm("sandfrictionangle").set(36)   # 乾いた砂の安息角に近い値（既定 30）
    g.step(src, "砂の柱を用意する",
           "<code>tube</code> で半径 30 cm・高さ 55 cm の円柱を作る。<code>mpmcontainer</code> は計算する範囲（3 × 1.4 × 3 m）と、"
           f"粒の間隔 <strong>Particle Separation {SEP}</strong>（2 cm）を決める。<code>mpmsource</code> の左に円柱、右に容器をつなぎ、"
           "<strong>Material Preset を Sand</strong>（砂）にし、<strong>Material Type を Sandy</strong> にする。<strong>Friction Angle は 36度</strong>（既定 30度）にする。乾いた砂の山の傾き（安息角）は 30〜35度ほどなので、それに近づける。"
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

    # 本物の砂粒は 0.1〜1 mm で、1 m の山では1粒ずつは見えない。計算の粒（2 cm）をそのまま球で撮ると小石に見えた（前の版）。
    # 粒をつないで1枚の面にし、細かいざらつきと色のむらを付ける
    blob = g.node("vdbfromparticles", "to_surface", [solver], voxelsize=0.005, radiusscale=1.6)
    soft = g.node("vdbsmoothsdf", "smooth_surface", [blob], iterations=8)
    skin = g.node("convertvdb", "to_mesh", [soft], conversion="poly")
    grain = g.node("mountain::2.0", "sand_grain", [skin], height=0.0015, elementsize=0.005, rough=0.7, oct=3)
    grains = g.node("attribwrangle", "sand_color", [grain], snippet=(
        "// 砂の色のむら。乾いた砂は1粒ずつ色が違い、細かい斑点に見える\n"
        "v@Cd = {0.76, 0.62, 0.43} * fit(noise(@P * 400), 0.3, 0.7, 0.8, 1.15) * fit(noise(@P * 20), 0.3, 0.7, 0.92, 1.05);"))
    sand = g.mat("sand_mat", basecolor=(1, 1, 1), rough=0.95, reflect=0.1)
    wood = g.mat("floor_mat", basecolor=(0.35, 0.3, 0.26), rough=0.7)
    final = g.node("merge", "sandbox", [g.assign(grains, sand, "assign_sand"), g.assign(floor, wood, "assign_floor")])
    g.step(final, "粒をつないで、砂の面にする",
           "本物の砂粒は 0.1〜1 mm で、1 m の山では1粒ずつは見えない。計算の粒（2 cm）をそのまま球で撮ると、小石を並べたように見えた（前の版）。"
           "<code>vdbfromparticles</code>（Voxel Size 0.005、Radius Scale 1.6）で粒を1つのボリュームにつなぎ、<code>vdbsmoothsdf</code>（Iterations 8）でならして、"
           "<code>convertvdb</code> で面に戻す。<code>mountain</code>（Height 1.5 mm・Element Size 5 mm）で細かいざらつきを付け、"
           "<code>attribwrangle</code> で細かい色のむら（1粒ずつ色が違う砂の斑点）を付ける。材質は Roughness 0.95 で、つやを消す。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {LAST}）。崩れて止まった砂山。", frame=LAST,
           direction=(1.0, 0.35, 1.2), key=3.2, rim=5.0, dome=0.4, spp=48, margin=1.1, backdrop=(0.3, 0.27, 0.24),
           bbox=hou.BoundingBox(-0.7, 0, -0.7, 0.7, 0.4, 0.7))
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
        {"title": "崩れた山の斜面の傾き",
         "body": f"中心からの距離ごとのいちばん高い粒で斜面の傾きを出すと {ang:.0f}度（Friction Angle は 36度）。"
                 f"柱を一度に崩したので、砂は勢いよく広がり、止まった山は Friction Angle（36度）よりゆるい。前の版の細長い柱（高さ 90 cm・半径 25 cm、Friction Angle 30度）では 17度で、ほぼ平らな円盤になった。",
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
