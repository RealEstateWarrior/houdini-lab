# -*- coding: utf-8 -*-
"""実践「ゼリーをぷるんと揺らす」— ゼリーの形を中まで詰まった柔らかい体（Vellum の四面体）にして皿に落とし、つぶれた瞬間を撮る。

    hython examples/pr_jelly.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 36


def run(solver, last, probe=None):
    """1 フレームから last まで順に回す。probe があれば、フレームごとの高さを返す。"""
    import hou
    t0 = time.perf_counter()
    heights = {}
    for f in range(1, last + 1):
        hou.setFrame(f)
        geo = solver.geometry()
        if probe:
            box = geo.boundingBox()
            heights[f] = box.sizevec()[1]
    return time.perf_counter() - t0, heights


def main():
    import hou
    g = kit.Guide("jelly", "ゼリーをぷるんと揺らす",
                  "ゼリーは表面だけでなく中まで詰まっているので、形を小さな四面体で埋めてから Vellum で揺らす。"
                  "少し上から皿に落とすと、つぶれて戻る「ぷるん」が出る。撮るときは、四面体ではなく元のきれいな表面を動きに合わせて曲げる。",
                  tags=["シミュレーション", "Vellum", "ソフトボディ", "Karma", "制作"])
    g.shot_dir = (0.9, 0.45, 1.2)
    mold = g.node("tube", "mold", type="poly", rad=(0.22, 0.3), height=0.28, rows=6, cols=40, cap=1, t=(0, 0.34, 0))
    skin = g.node("remesh::2.0", "even_skin", [mold], targetsize=0.03)
    g.step(skin, "ゼリーの形を作る",
           "<code>tube</code> で下が広く上が狭い円柱（半径 0.3 → 0.22、高さ 0.28）を作り、皿の 0.2 m 上に置く。"
           "<code>remesh</code> の <strong>Target Size を 0.03</strong> にして、表面をそろった三角形にする。"
           "細長い面が残っていると、次の四面体づくりがゆがむ。",
           cap="そろった三角形の表面。", shading="smoothwire", ui_parm="targetsize")
    tets = g.node("tetrahedralize::2.0", "fill_inside", [skin])
    g.step(tets, "中を四面体で埋める",
           "<code>tetrahedralize</code> を既定のまま（Mode は Conform to Surface）つなぐ。表面の三角形をそのまま外側に使って、"
           "中を小さな四面体（三角すい）で埋める。ゼリーの「中身」がここでできる。",
           cap="中まで四面体で埋まった形（見た目は外側だけ）。", shading="smoothwire", ui_parm="mode")
    body = g.node("vellumconstraints", "soft_body", [tets], constrainttype="tetstretch",
                  stretchstiffness=1.0, stretchstiffnessexp=4)
    keep = g.node("vellumconstraints", "keep_volume", [body], constrainttype="tetvolume")
    keep.setInput(1, body, 1)
    g.step(keep, "柔らかさと、体積を保つ力を付ける",
           "<code>vellumconstraints</code> を2つ重ねる。1つ目は <strong>Tet Stretch</strong>（四面体の辺が伸び縮みする）で、"
           "<strong>Stiffness を 1 × 10⁴</strong> と柔らかくする。2つ目は <strong>Tet Volume</strong>（四面体ごとの体積を保つ）で既定のまま。"
           "つぶれても体積が減らないので、横にふくらんで戻る。",
           cap="見た目は同じ。中身のつながりが付いた。", shading="smoothwire", ui_parm="stretchstiffnessexp")
    solver = g.node("vellumsolver", "drop", [keep], substeps=5, useground=1)
    solver.setInput(1, keep, 1)
    sim_sec, heights = run(solver, LAST, probe=True)
    rest_h = heights[1]
    squash_f = min((f for f in heights if f > 3), key=lambda f: heights[f])
    squash_h = heights[squash_f]
    hou.setFrame(squash_f)
    g.step(solver, "皿に落として揺らす",
           "<code>vellumsolver</code> に左右の出口をつなぎ、<strong>Ground Plane</strong> を入れて y = 0 に床を作る。Substeps 5。"
           f"再生すると、落ちて床に当たり、ぷるんとつぶれて戻る。高さ {rest_h:.3f} m のゼリーが、"
           f"フレーム {squash_f} でいちばんつぶれて {squash_h:.3f} m になった。",
           cap=f"フレーム {squash_f}。いちばんつぶれた瞬間。", shading="smoothwire", ui_parm="useground")
    bend = g.node("pointdeform", "follow_skin", [skin, tets, solver])
    soft = g.node("subdivide", "smooth_skin", [bend], iterations=1)
    g.step(soft, "きれいな表面を、動きに合わせて曲げる",
           "四面体は中身の計算用で、そのまま撮ると面がでこぼこに見える。<code>pointdeform</code> の左に元の表面（remesh の出力）、"
           "真ん中に <strong>動く前の四面体</strong>（<code>tetrahedralize</code> の出力）、右に計算中の形をつなぐ。"
           "表面が、四面体の動きにそって曲がる。最後に <code>subdivide</code>（1回）で面を細かく割って、角ばりを消す。",
           cap="表面だけが、つぶれた形についてくる。", shading="smooth")
    plate = g.node("tube", "plate", type="poly", rad=(0.5, 0.42), height=0.025, cols=64, cap=1, t=(0, -0.0125, 0))
    jelly = g.mat("jelly_mat", basecolor=(1, 1, 1), rough=0.03, reflect=1.0, ior=1.35, transparency=1.0,
                  transcolor=(0.95, 0.12, 0.2), transdist=0.12)
    dish = g.mat("plate_mat", basecolor=(0.7, 0.7, 0.68), rough=0.12, coat=1.0)
    final = g.node("merge", "dessert", [g.assign(soft, jelly, "assign_jelly"), g.assign(plate, dish, "assign_plate")])
    g.step(final, "ゼリーと皿の材質を当てる",
           "ゼリーは <code>principledshader</code> で <strong>Transparency 1・IOR 1.35</strong>（水に近い）、Roughness 0.03。"
           "<strong>Transmission Color を赤、Transmission Distance を 0.12</strong> にすると、厚い所ほど濃い赤になる。皿は白く、Coat 1 でつやを出す。",
           cap="材質を当てた状態（ビューポートでは透けない）。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム{squash_f}、いちばんつぶれた瞬間）。", direction=(0.8, 0.42, 1.2),
           key=2.2, rim=8.0, dome=0.2, spp=128, margin=1.05, frame=squash_f, backdrop=(0.26, 0.2, 0.2),
           bbox=hou.BoundingBox(-0.5, 0, -0.5, 0.5, 0.45, 0.5))

    # ---- 落とし穴を測る ----
    n_tet = tets.geometry().intrinsicValue("primitivecount")
    skin.parm("targetsize").set(0.015)
    n_fine = tets.geometry().intrinsicValue("primitivecount")
    skin.parm("targetsize").set(0.03)
    body.parm("stretchstiffnessexp").set(10)
    _, hard = run(solver, LAST, probe=True)
    hard_min = min(v for f, v in hard.items() if f > 3)
    body.parm("stretchstiffnessexp").set(4)
    keep.bypass(True)
    _, novol = run(solver, LAST, probe=True)
    novol_min = min(v for f, v in novol.items() if f > 3)
    novol_end = novol[LAST]
    keep.bypass(False)
    run(solver, LAST)
    traps = [
        {"title": "硬すぎると、ぷるんとしない",
         "body": f"Tet Stretch の Stiffness を既定の × 10¹⁰ にすると、いちばんつぶれても高さ {hard_min:.3f} m（はじめ {rest_h:.3f} m）で、"
                 f"ほとんど形が変わらない。× 10⁴ では {squash_h:.3f} m までつぶれた。ゼリーの柔らかさはここで決まる。",
         "img": "", "cap": ""},
        {"title": "Tet Volume がないと、深くつぶれて戻りきらない",
         "body": f"2つ目の Tet Volume を外すと、いちばんつぶれた高さは {novol_min:.3f} m、{LAST} フレーム後も {novol_end:.3f} m。"
                 f"付けたときは {LAST} フレーム後に {heights[LAST]:.3f} m まで戻った。体積を保つ力がないと、深くつぶれ、戻りも足りない。",
         "img": "", "cap": ""},
        {"title": "四面体の数が重さを決める",
         "body": f"remesh 0.03 の表面から、四面体は {n_tet:,} 個できた。{LAST} フレームの計算は {sim_sec:.1f} 秒。"
                 f"Target Size を半分の 0.015 にすると {n_fine:,} 個（{n_fine / n_tet:.1f} 倍）。揺れを決めるまでは粗くする。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "12個（材質2つ）"], ["四面体", f"{n_tet:,}個"],
                  [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps)


if __name__ == "__main__":
    main()
