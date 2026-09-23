# -*- coding: utf-8 -*-
"""実践「レンガ塀を HDA にする」— レンガを段ごとに半分ずらして積み、長さと高さのつまみだけで組み替わる自作ノード（HDA）にまとめる。

本物のレンガ塀は、上下の段で継ぎ目が重ならないよう半枚ずつずらして積む（長手積み）。1枚ずつ色も少しずつ違う。
一度組んだら HDA（Houdini Digital Asset）に包んでおくと、次からは「長さ」「高さ」を変えるだけで何枚でも使い回せる。

    hython examples/pr_brickhda.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("brickhda", "レンガ塀を HDA にする",
                  "レンガを1枚作り、段ごとに半枚ずつずらした位置へ並べて塀にする。組んだノードを1つのサブネットにまとめ、"
                  "「長さ」「高さ」のつまみを外に出して HDA（自作ノード）にする。次からは、つまみを変えるだけで別の塀になる。",
                  tags=["モデリング", "HDA", "VEX", "複製", "Karma"])
    g.shot_dir = (0.6, 0.3, 1.2)
    wall = g.geo.createNode("subnet", "brick_wall")
    group = wall.parmTemplateGroup()
    group.append(hou.FloatParmTemplate("length", "Length", 1, default_value=(3.0,), min=0.5, max=20))
    group.append(hou.FloatParmTemplate("height", "Height", 1, default_value=(1.2,), min=0.2, max=5))
    group.append(hou.IntParmTemplate("seed", "Seed", 1, default_value=(1,)))
    wall.setParmTemplateGroup(group)

    brick = g.node("box", "one_brick", parent=wall, size=(0.21, 0.06, 0.1))
    soft = g.node("polybevel::3.0", "soft_edges", [brick], parent=wall, offset=0.006, divisions=2)
    g.step(soft, "レンガを1枚作る",
           "まずサブネット（<code>subnet</code>）を1つ置き、その中で作業する。あとでこのサブネットごと HDA にする。"
           "<code>box</code> で 21 × 6 × 10 cm（よくあるレンガの大きさ）の箱を作り、<code>polybevel</code> で角を 6 mm 丸める。"
           "角が立ったままだと、光が当たったときに作り物に見える。",
           cap="角を丸めたレンガ1枚。", shading="smoothwire", bbox=hou.BoundingBox(-0.14, -0.05, -0.08, 0.14, 0.05, 0.08))

    spots = g.node("attribwrangle", "bond_pattern", parent=wall, snippet=(
        "// 長手積み。段ごとに半枚ずらし、目地（すき間）10 mm をあけて並べる\n"
        "float L = ch('../length');\n"
        "float H = ch('../height');\n"
        "float bw = 0.21, bh = 0.06, joint = 0.01;\n"
        "int rows = int(H / (bh + joint));\n"
        "int cols = int(L / (bw + joint)) + 1;\n"
        "for (int r = 0; r < rows; r++) {\n"
        "    float shift = (r % 2) * (bw + joint) * 0.5;      // 1段おきに半枚ずらす\n"
        "    for (int c = 0; c < cols; c++) {\n"
        "        float x = c * (bw + joint) + shift - L * 0.5;\n"
        "        if (x < -L * 0.5 - 0.001 || x > L * 0.5 + 0.001) continue;   // 塀の外にはみ出すものは置かない\n"
        "        float s = ch('../seed') + r * 101 + c;\n"
        "        int p = addpoint(0, set(x, r * (bh + joint) + bh * 0.5, (rand(s) - 0.5) * 0.006));\n"
        "        // 1枚ずつ、色と向きを少しだけ変える\n"
        "        vector base = {0.42, 0.16, 0.09};\n"
        "        setpointattrib(0, 'Cd', p, base * fit01(rand(s + 0.5), 0.7, 1.25) + set(0, 0.02, 0.02) * rand(s + 0.7));\n"
        "        setpointattrib(0, 'orient', p, eulertoquaternion(radians(set(0, (rand(s + 0.3) - 0.5) * 1.2, (rand(s + 0.9) - 0.5) * 0.8)), 0));\n"
        "    }\n"
        "}"))
    spots.parm("class").set(0)
    g.step(spots, "レンガを置く場所を決める",
           "何もつながない <code>attribwrangle</code>（Run Over は Detail）で、レンガの中心になる点を並べる。"
           "長さと高さは <strong>ch('../length')・ch('../height')</strong> で、外側のサブネットのつまみから読む。"
           "段の高さはレンガ 6 cm ＋ 目地 1 cm。<strong>1段おきに半枚（11 cm）ずらす</strong>と、上下の継ぎ目が重ならない長手積みになる。"
           "点ごとに色 Cd を 0.7〜1.25 倍に変え、向き orient もごくわずかに（1度以下）傾ける。",
           cap="段ごとに半分ずれた点の並び。", shading="wire", ui_parm="snippet",
           bbox=hou.BoundingBox(-1.6, 0, -0.1, 1.6, 1.25, 0.1))

    bricks = g.node("copytopoints::2.0", "stack", [soft, spots], parent=wall, targetattribs=1)
    bricks.parm("applyto1").set("prims")
    bricks.parm("applyattribs1").set("Cd")   # H21 の copytopoints は、ここに書かないと点の色を移さない
    mortar = g.node("box", "mortar", parent=wall, size=(1, 1, 0.07))
    for axis, expr in (("sizex", 'ch("../length")'), ("sizey", 'ch("../height")'), ("ty", 'ch("../height") / 2')):
        mortar.parm(axis).setExpression(expr)
    whole = g.node("merge", "wall", [bricks, mortar], parent=wall)
    out = g.node("output", "output0", [whole], parent=wall)
    n_bricks = len(spots.geometry().points())
    g.step(whole, "レンガを積み、目地を入れる",
           f"<code>copytopoints</code> でレンガを点に並べる（{n_bricks} 枚）。向き orient は自動で効くが、"
           "<strong>色 Cd は Target Attributes に1行足して「Apply to: Primitives」「Attributes: Cd」と書かないと移らない</strong>。"
           "レンガの後ろに、少し薄い <code>box</code>（厚さ 7 cm）を目地（モルタル）として置く。大きさは Size に "
           "<strong>ch(\"../length\")・ch(\"../height\")</strong> の式を入れ、塀の大きさに合わせて伸び縮みさせる。"
           "最後に <code>output</code> につなぐ（サブネットの出口）。",
           cap=f"{n_bricks} 枚のレンガと目地。", shading="smooth",
           bbox=hou.BoundingBox(-1.6, 0, -0.1, 1.6, 1.25, 0.1))

    wall.layoutChildren()
    hda = wall.createDigitalAsset(name="sp_brick_wall", description="Brick Wall", save_as_embedded=True,
                                  min_num_inputs=0, max_num_inputs=0)
    hda.type().definition().setParmTemplateGroup(hda.parmTemplateGroup())
    g.step(hda, "HDA（自作ノード）にする",
           "サブネットを右クリックして <strong>Create Digital Asset</strong>。名前 <strong>sp_brick_wall</strong>、"
           "保存先は <strong>Embedded</strong>（この hip の中にしまう。別のファイルが要らない）。"
           "サブネットに足しておいた Length・Height・Seed の3つのつまみが、そのまま HDA のつまみになる。"
           "Tab キーのメニューに「Brick Wall」が出て、ほかのノードと同じように置けるようになる。",
           cap="見た目は同じ。中身がまとまり、つまみ3つのノードになった。", shading="smooth", ui_parm="length",
           bbox=hou.BoundingBox(-1.6, 0, -0.1, 1.6, 1.25, 0.1))

    second = g.geo.createNode("sp_brick_wall", "garden_wall")
    second.parm("length").set(1.6)
    second.parm("height").set(0.7)
    second.parm("seed").set(7)
    moved = g.node("xform", "set_front", [second], t=(1.2, 0, 1.1), r=(0, -35, 0))
    n_small = len(second.node("bond_pattern").geometry().points())
    g.step(moved, "つまみを変えて、2つ目の塀を置く",
           "Tab メニューから Brick Wall をもう1つ置き、<strong>Length 1.6・Height 0.7・Seed 7</strong> にする。"
           f"中のノードには触れずに、{n_small} 枚の低い塀ができる。<code>xform</code> で右手前へずらして少し回す。",
           cap=f"つまみだけで作った2つ目の塀（{n_small} 枚）。", shading="smooth",
           bbox=hou.BoundingBox(0.3, 0, 0.5, 2.1, 0.8, 1.7))

    clay = g.mat("brick_mat", basecolor=(1, 1, 1), rough=0.82, reflect=0.25)
    grout = g.mat("mortar_mat", basecolor=(0.55, 0.53, 0.5), rough=0.95)
    paint = g.node("merge", "both_walls", [hda, moved])
    # 材質は HDA の中で、レンガと目地に別々に当てる
    hda.allowEditingOfContents()
    inside_b = hda.node("stack")
    inside_m = hda.node("mortar")
    a1 = hda.createNode("material", "assign_brick")
    a1.setFirstInput(inside_b)
    a1.parm("shop_materialpath1").set(clay.path())
    a2 = hda.createNode("material", "assign_mortar")
    a2.setFirstInput(inside_m)
    a2.parm("shop_materialpath1").set(grout.path())
    hda.node("wall").setInput(0, a1)
    hda.node("wall").setInput(1, a2)
    hda.layoutChildren()
    before_save = second.node("assign_brick") is not None
    hda.type().definition().updateFromNode(hda)
    hda.matchCurrentDefinition()
    after_save = second.node("assign_brick") is not None
    final = paint
    g.step(final, "材質を当てる",
           "HDA の中に入り（右クリック → Allow Editing of Contents）、レンガと目地にそれぞれ <code>material</code> を当てる。"
           "レンガの材質は Base Color を白にして、点の色 Cd をそのまま使う（Roughness 0.82）。目地は明るい灰色。"
           "最後に HDA を保存（Save Node Type）すると、置いてある2つの塀の両方に反映される。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。同じ HDA から、つまみだけ変えた2つの塀。",
           direction=(0.55, 0.28, 1.2), key=3.2, rim=4.0, dome=0.4, spp=64, margin=1.04,
           backdrop=(0.2, 0.19, 0.17), bbox=hou.BoundingBox(-1.6, 0, -0.2, 2.1, 1.25, 1.7))

    # ---- 落とし穴を測る ----
    hda.parm("length").set(6.0)
    n_long = len(hda.node("bond_pattern").geometry().points())
    hda.parm("length").set(3.0)
    traps = [
        {"title": "中のノードは ch('../…') で外のつまみを読む",
         "body": f"中の wrangle と箱は、HDA のつまみを <strong>ch('../length')</strong> のように1つ上を指して読む。"
                 f"Length を 3 から 6 にすると、レンガは {n_bricks} 枚から {n_long} 枚になった（中のノードは触っていない）。"
                 "数字を中に直接書くと、つまみを動かしても塀は変わらない。",
         "img": "", "cap": ""},
        {"title": "中を直したら、定義を保存する",
         "body": "HDA の中身を変えたあとは Save Node Type（台本では definition().updateFromNode()）で定義を保存する。"
                 f"材質のノードを足した直後、2つ目の塀の中には{'もう入っていた' if before_save else 'まだ無かった'}。"
                 f"保存したあとは{'入った' if after_save else 'まだ無い'}。同じ HDA のほかのノードに届くのは、保存したとき。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "HDA の中に8個＋外に4個"], ["レンガ", f"{n_bricks}枚＋{n_small}枚"]], traps=traps)


if __name__ == "__main__":
    main()
