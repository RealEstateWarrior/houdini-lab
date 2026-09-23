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
    disc = g.node("tube", "coin", type="poly", rad=(0.013, 0.013), height=0.0018, cols=40, cap=1)
    rim = g.node("polybevel::3.0", "soft_rim", [disc], offset=0.0004, divisions=2)
    g.step(rim, "コインを1枚作る",
           "<code>tube</code> で半径 1.3 cm・厚さ 1.8 mm の円盤を作り（Columns 40 で縁をなめらかに）、"
           "<code>polybevel</code> で縁の角を 0.4 mm 丸める。角が立っていると、光ったときに作り物に見える。",
           cap="縁を丸めたコイン1枚。", shading="smoothwire", bbox=hou.BoundingBox(-0.016, -0.004, -0.016, 0.016, 0.004, 0.016))

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

    metal = g.mat("coin_mat", basecolor=(1, 1, 1), metallic=1.0, rough=0.22)
    wood = g.mat("table_mat", basecolor=(0.12, 0.07, 0.04), rough=0.45, reflect=0.5)
    table = g.node("grid", "table", size=(1.5, 1.5), rows=2, cols=2)
    final = g.node("merge", "coins_on_table", [g.assign(solver, metal, "assign_coin"), g.assign(table, wood, "assign_table")])
    g.step(final, "金属の材質を当てる",
           "コインは <code>principledshader</code> で <strong>Metallic 1・Roughness 0.22</strong>、Base Color を白にして点の色 Cd を使う"
           "（金属は Base Color がそのまま映り込みの色になる）。床は濃い木の色。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {LAST}）。金・銀・銅のコインが散らばる。", frame=LAST,
           direction=(0.7, 0.75, 1.0), key=3.0, rim=6.0, dome=0.6, spp=64, margin=0.95, floor=False,
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
