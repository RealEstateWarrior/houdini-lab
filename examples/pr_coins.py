# -*- coding: utf-8 -*-
"""実践「コインをばらまく」— 金・銀・銅のコインを空中にばらばらの向きで置き、RBD（Bullet）で床へ落として散らばらせる。

本物のコインは、落ちると跳ねて転がり、最後は平らに寝て止まる。縁で立つものはまれ。
1枚ずつを「まとめた塊」（packed）にしてから Bullet に渡すと、何百枚でも軽く計算できる。

    hython examples/pr_coins.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 72
COUNT = 240


def run(solver, last):
    import hou
    t0 = time.perf_counter()
    for f in range(1, last + 1):
        hou.setFrame(f)
        solver.geometry()
    return time.perf_counter() - t0


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("coins", "コインをばらまく",
                  "コインを1枚作り、空中にばらばらの向きで何百枚も並べて、RBD（Bullet）で床へ落とす。"
                  "1枚ずつを packed（まとめた塊）にしておくと、計算がとても軽い。色は金・銀・銅の3つから選ぶ。",
                  tags=["シミュレーション", "RBD", "複製", "Karma"])
    g.shot_dir = (0.8, 0.8, 1.0)
    profile = g.node("attribwrangle", "coin_profile", snippet=(
        "// 硬貨の断面（半分）。面は少し低く、縁（リム）が一段高い。x が中心からの距離、y が高さ\n"
        "vector pts[] = {{0.0, 0.0006, 0}, {0.0108, 0.0006, 0}, {0.0113, 0.0009, 0}, {0.0128, 0.0009, 0}, {0.013, 0.0007, 0},\n"
        "                {0.013, -0.0007, 0}, {0.0128, -0.0009, 0}, {0.0113, -0.0009, 0}, {0.0108, -0.0006, 0}, {0.0, -0.0006, 0}};\n"
        "int prim = addprim(0, 'poly');\n"
        "foreach (vector p; pts) addvertex(0, prim, addpoint(0, p));"))
    profile.parm("class").set(0)
    turned = g.node("revolve::2.0", "coin_turn", [profile], divs=72)
    body = g.node("reverse", "coin_body", [turned])
    dense = g.node("remesh::2.0", "coin_mesh", [body], targetsize=0.0004)
    rim = g.node("attribwrangle", "relief", [dense], snippet=(
        "// 面の浮き彫り。縁より内側の平らな面だけを、模様の形にわずかに持ち上げる\n"
        "float r = length(set(@P.x, @P.z));\n"
        "if (r < 0.0102 && abs(@P.y) > 0.0005) {\n"
        "    float a = atan2(@P.z, @P.x);\n"
        "    float pattern = smooth(0.52, 0.56, noise(set(@P.x, @P.z, @P.y > 0) * 900));   // 中の絵柄\n"
        "    float ring = smooth(0.0088, 0.0090, r) * (1 - smooth(0.0098, 0.0100, r)) * (frac(a * 30 / (2 * PI)) > 0.5);   // 縁に沿った点々\n"
        "    @P.y += sign(@P.y) * 0.00015 * max(pattern * (r < 0.008), ring);\n"
        "}"))
    g.step(rim, "コインを1枚作る",
           "本物の硬貨は、面が少し低く、縁（リム）が一段高くなっていて、面には浮き彫りの絵柄がある。前の版は、ただの円盤で豆粒のように見えた。"
           "何もつながない Detail の <code>attribwrangle</code> で、断面の半分（半径 1.3 cm・厚さ 1.8 mm、縁だけ 0.3 mm 高い）を多角形で描き、"
           "<code>revolve</code>（72 分割）で回して <code>reverse</code> で面を外向きにする。<code>remesh</code> で 0.4 mm の細かい網にし、"
           "もう1つの <code>attribwrangle</code> で、縁の内側の面をノイズの形に 0.15 mm 持ち上げて絵柄に、縁に沿って点々の飾りを付ける。",
           cap="縁が高く、浮き彫りのあるコイン。", shading="smooth", bbox=hou.BoundingBox(-0.016, -0.004, -0.016, 0.016, 0.004, 0.016))

    cloud = g.node("box", "drop_zone", size=(0.25, 0.3, 0.25), t=(0, 0.3, 0))
    spots = g.node("scatter::2.0", "coin_spots", [cloud], npts=COUNT, seed=3)
    spin = g.node("attribwrangle", "random_coins", [spots], snippet=(
        "// 1枚ずつ向きをばらばらにし、金・銀・銅のどれかの色を付ける\n"
        "p@orient = quaternion(radians(set(rand(@ptnum) * 360, rand(@ptnum + 1) * 360, rand(@ptnum + 2) * 360)), 0);\n"
        "float pick = rand(@ptnum + 5);\n"
        "v@Cd = pick < 0.4 ? {1.0, 0.76, 0.34} : (pick < 0.75 ? {0.9, 0.9, 0.92} : {0.95, 0.55, 0.38});\n"
        "v@v = set(rand(@ptnum + 7) - 0.5, 0, rand(@ptnum + 8) - 0.5) * 0.6;   // 少し横にも飛ばす"))
    coins = g.node("copytopoints::2.0", "coins", [rim, spin], pack=1, targetattribs=1)
    coins.parm("applyto1").set("points")
    coins.parm("applyattribs1").set("Cd v")
    g.step(coins, "空中にばらまいて並べる",
           f"<code>box</code>（25 × 30 × 25 cm）の表面に、<code>scatter</code> で <strong>{COUNT} 個</strong>の点をまく。"
           "<code>attribwrangle</code> で点ごとに、ばらばらの向き <strong>orient</strong>、金・銀・銅のどれかの色 Cd、横向きの小さな速さ v を付ける。"
           "<code>copytopoints</code> でコインを並べ、<strong>Pack and Instance</strong> を入れて1枚ずつを packed の塊にする。"
           "Target Attributes に「Apply to: Points」「Attributes: Cd v」を足して、色と速さも移す。",
           cap=f"空中に並んだ {COUNT} 枚。", shading="smooth", ui_parm="pack",
           bbox=hou.BoundingBox(-0.2, 0.1, -0.2, 0.2, 0.5, 0.2))

    solver = g.node("rbdbulletsolver", "drop", [coins], useground=1, startframe=1)
    # 既定の Collision Margin 0.02 のままだと、厚さ 1.8 mm のコインが床から 2 cm 浮いて止まった
    run(solver, LAST)
    hover = sorted(p.position()[1] for p in solver.geometry().points())[COUNT // 2]
    solver.parm("margin").set(0.0005)
    solver.parm("collision_margin").set(0.0005)
    sim_sec = run(solver, LAST)
    rest = sorted(p.position()[1] for p in solver.geometry().points())[COUNT // 2]
    flat = 0
    for p in solver.geometry().prims():
        up = hou.Vector3(0, 1, 0) * p.fullTransform()
        if abs(up.normalized()[1]) > 0.9:
            flat += 1
    g.step(solver, "床へ落とす",
           "<code>rbdbulletsolver</code> に packed のコインをつなぎ、<strong>Ground Plane</strong> を入れる。"
           "コインは薄いので、<strong>Collision Margin を 0.0005</strong>（0.5 mm）に下げる（床の側の Collision Margin も同じ）。"
           f"再生すると、コインは落ちて跳ね、転がって止まる。{LAST} フレーム（3 秒）の計算は {sim_sec:.1f} 秒。"
           f"止まった {COUNT} 枚のうち {flat} 枚が平らに寝ていた（面の向きが真上・真下から約25度以内）。",
           cap=f"フレーム {LAST}。床に散らばったコイン。", shading="smooth", ui_parm="useground",
           bbox=hou.BoundingBox(-0.3, 0, -0.3, 0.3, 0.1, 0.3))

    metal = g.mat("coin_mat", basecolor=(1, 1, 1), metallic=1.0, rough=0.3)
    wood = g.mat("table_mat", basecolor=(1, 1, 1), rough=0.45, reflect=0.5)
    table_grid = g.node("grid", "table", size=(1.5, 1.5), rows=300, cols=300)
    table = g.node("attribwrangle", "wood_grain", [table_grid], snippet=(
        "// 木目：x 方向にゆらいだ縞。濃い茶と明るい茶を行き来する\n"
        "float s = sin((@P.z + noise(@P * 4) * 0.03) * 260);\n"
        "v@Cd = lerp({0.09, 0.05, 0.025}, {0.2, 0.12, 0.06}, s * 0.5 + 0.5) * fit(noise(@P * 30), 0.3, 0.7, 0.85, 1.1);"))
    final = g.node("merge", "coins_on_table", [g.assign(solver, metal, "assign_coin"), g.assign(table, wood, "assign_table")])
    g.step(final, "金属の材質を当てる",
           "コインは <code>principledshader</code> で <strong>Metallic 1・Roughness 0.3</strong>、Base Color を白にして点の色 Cd を使う"
           "（金属は Base Color がそのまま映り込みの色になる）。床は <code>grid</code> に <code>attribwrangle</code> でゆらいだ縞の木目を付ける。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {LAST}）。金・銀・銅のコインが散らばる。", frame=LAST,
           direction=(0.7, 0.75, 1.0), key=0.3, rim=0.6, dome=0.35, spp=48, margin=0.6, floor=False, denoise=True,
           bbox=hou.BoundingBox(-0.25, 0, -0.25, 0.25, 0.03, 0.25))
    g.anim(final, (1, LAST), "コインが落ちて跳ね、散らばって止まるまで（72 フレーム＝3 秒）。",
           bbox=hou.BoundingBox(-0.3, 0, -0.3, 0.3, 0.45, 0.3), direction=(0.8, 0.6, 1.0))

    # ---- 落とし穴を測る ----
    coins.parm("pack").set(0)
    unpacked_sec = None
    try:
        unpacked_sec = run(solver, LAST)
        unpacked_n = len(solver.geometry().prims())
    finally:
        coins.parm("pack").set(1)
    run(solver, LAST)
    traps = [
        {"title": "薄い物は、Collision Margin で浮く",
         "body": f"Collision Margin が既定の 0.02 のままだと、止まったコインの中心の高さ（真ん中の値）は {hover * 1000:.1f} mm。"
                 f"厚さ 1.8 mm のコインが、床から 2 cm 近く浮いて止まった。0.0005 にすると {rest * 1000:.1f} mm で、床に寝た。"
                 "Bullet は形のまわりに余白を付けて当たりを取るので、余白が形より大きいと浮く（大きな箱では目立たない。実験167）。",
         "img": "", "cap": ""},
        {"title": "Pack and Instance を切ると",
         "body": f"切ると、出てくる面は {unpacked_n:,} 枚になり、{LAST} フレームの計算は {unpacked_sec:.1f} 秒だった（packed では {sim_sec:.1f} 秒）。"
                 f"packed なら 1 枚のコインが 1 つの塊で、形の数は {COUNT} のまま扱える。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "10個（材質2つ）"], ["コイン", f"{COUNT}枚"], [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]],
           traps=traps)


if __name__ == "__main__":
    main()
