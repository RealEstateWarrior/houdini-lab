# -*- coding: utf-8 -*-
"""実践「テーブルクロスを掛ける」— 平らな布を机の上から落とし、角が垂れてひだができるまで待つ。

本物のテーブルクロスは、天板の上は平らで、縁から下へまっすぐ垂れ、四隅だけが円すい形にふくらんで大きなひだになる。
Vellum の布を天板に「ぶつかる物」として当てるだけで、この形が自然に出る。

    hython examples/pr_tablecloth.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 72     # 3 秒


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
    g = kit.Guide("tablecloth", "テーブルクロスを掛ける",
                  "平らな布（Vellum の cloth）を机の少し上に置いて落とす。机を「ぶつかる物」として渡すだけで、"
                  "天板の上は平らに、縁からはまっすぐ垂れ、四隅には大きなひだができる。布を細かく割るほど、ひだは細かくなる。",
                  tags=["シミュレーション", "Vellum", "布", "Karma"])
    g.shot_dir = (1.0, 0.7, 1.25)
    top = g.node("box", "table_top", size=(1.2, 0.04, 0.8), t=(0, 0.74, 0))
    legs = []
    for i, (x, z) in enumerate([(-0.54, -0.34), (0.54, -0.34), (-0.54, 0.34), (0.54, 0.34)]):
        legs.append(g.node("box", f"leg{i}", size=(0.05, 0.72, 0.05), t=(x, 0.36, z)))
    table = g.node("merge", "table", [top] + legs)
    g.step(table, "机を作る",
           "<code>box</code> で天板（1.2 × 0.04 × 0.8 m、高さ 0.74 m）と、細い脚を4本作り、<code>merge</code> でまとめる。"
           "この机は、あとで布が「ぶつかる物」になる。",
           cap="天板と4本の脚。", shading="smoothwire")

    cloth = g.node("grid", "cloth", size=(1.9, 1.45), rows=110, cols=140, t=(0, 0.86, 0), r=(0, 4, 0))
    g.step(cloth, "布を机の上に置く",
           "<code>grid</code>（1.9 × 1.45 m）を天板より 12 cm 上に置く。天板より縁ごとに 33〜35 cm 大きいので、そのぶんが垂れる。"
           "<strong>Rows 110・Columns 140</strong> と細かく割る。布は網の線でしか曲がれないので、粗いとひだが角ばる。"
           "Rotate Y を 4 度だけ回して、机とぴったり揃えない（揃いすぎると作り物に見える）。",
           cap="机の上に浮かせた平らな布。", shading="smoothwire", ui_parm="rows",
           bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))

    vc = g.node("vellumconstraints", "cloth_setup", [cloth], constrainttype="cloth")
    solver = g.node("vellumsolver", "drop", [vc], substeps=5, useground=1)
    solver.setInput(1, vc, 1)
    solver.setInput(2, table)
    sim_sec = run(solver, LAST)
    geo = solver.geometry()
    hang = 0.76 - geo.boundingBox().minvec()[1]
    g.step(solver, "机にぶつけて落とす",
           "<code>vellumconstraints</code> の Constraint Type を <strong>Cloth</strong> にする（布として引っぱり合うつながりが付く）。"
           "<code>vellumsolver</code> には3本つなぐ。左に布、真ん中に vellumconstraints の右の出口（つながり）、"
           "<strong>右に机</strong>。右の入口は「ぶつかる物」で、布は机を通り抜けずに乗る。Ground Plane も入れ、Substeps 5。"
           f"{LAST} フレーム（3 秒）で落ち着き、布の角は天板から {hang:.2f} m 下まで垂れた。",
           cap=f"フレーム {LAST}。天板の上は平ら、四隅に大きなひだ。", shading="smoothwire", ui_parm="substeps",
           bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))

    smooth = g.node("subdivide", "soft_folds", [solver], iterations=1)
    thick = g.node("polyextrude::2.0", "thickness", [smooth], dist=0.002, outputback=1)
    g.step(thick, "なめらかにして、厚みを付ける",
           "<code>subdivide</code>（1回）で網をさらに細かく割り、ひだの折れ目の角を消す。"
           "<code>polyextrude</code> で <strong>Distance 0.002</strong>（2 mm）押し出し、<strong>Output Back</strong> を入れて裏面も残す。"
           "厚みのない布は、縁が紙のように薄く見える。",
           cap="なめらかで、少し厚みのある布。", shading="smooth", bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))

    linen = g.mat("linen_mat", basecolor=(0.86, 0.84, 0.79), rough=0.8, reflect=0.2, sheen=0.5)
    wood = g.mat("wood_mat", basecolor=(0.3, 0.17, 0.09), rough=0.45, reflect=0.5)
    final = g.node("merge", "dining", [g.assign(thick, linen, "assign_linen"), g.assign(table, wood, "assign_wood")])
    g.step(final, "材質を当てる",
           "布は <code>principledshader</code> で生成りの白（0.86, 0.84, 0.79）、Roughness 0.8、<strong>Sheen 0.5</strong>"
           "（布の毛羽が光をふわっと返す）。机は濃い茶色で Roughness 0.45。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {LAST}）。四隅のひだと、縁からまっすぐ垂れる布。",
           direction=(0.95, 0.62, 1.2), key=3.4, rim=4.0, dome=0.45, spp=64, margin=1.05, frame=LAST,
           backdrop=(0.16, 0.15, 0.14), bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))
    g.anim(final, (1, LAST), "机の上に落ちて、角が垂れて落ち着くまで（72 フレーム＝3 秒）。",
           bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8), direction=(1.0, 0.7, 1.25))

    # ---- 落とし穴を測る ----
    solver.setInput(2, None)
    run(solver, LAST)
    fall_top = solver.geometry().boundingBox().maxvec()[1]
    solver.setInput(2, table)
    cloth.parm("rows").set(44)
    cloth.parm("cols").set(56)
    coarse_sec = run(solver, LAST)
    cloth.parm("rows").set(110)
    cloth.parm("cols").set(140)
    run(solver, LAST)
    traps = [
        {"title": "机を右の入口につながないと、布は床まで落ちる",
         "body": f"vellumsolver の右の入口を空にすると、{LAST} フレームで布のいちばん高い所は {fall_top:.2f} m（床の上に重なった）。"
                 "机は見えているだけでは布に当たらない。ぶつかる物は、必ず右の入口に渡す。",
         "img": "", "cap": ""},
        {"title": "細かさと重さ",
         "body": f"Rows 110・Columns 140（点 {111 * 141:,} 個）で {LAST} フレームの計算は {sim_sec:.1f} 秒。"
                 f"Rows 44・Columns 56（点 {45 * 57:,} 個）では {coarse_sec:.1f} 秒。粗いうちに落ち方を決めて、最後に細かくする。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "13個（材質2つ）"], ["布の点", f"{111 * 141:,}個"],
                  [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps)


if __name__ == "__main__":
    main()
