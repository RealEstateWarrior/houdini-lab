# -*- coding: utf-8 -*-
"""実践「L-system で木を育てる」— 文字の書き換えルールで枝分かれを繰り返し、枝先に葉を付ける。

本物の木は「伸びる → 枝分かれする → 先がまた伸びる」を繰り返し、上の枝ほど細く短い。
L-system は、この繰り返しを文字の書き換え（A を「枝3本と A」に置き換える、を何回もやる）で表す。

    hython examples/pr_tree.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("tree", "L-system で木を育てる",
                  "lsystem ノードは、文字の書き換えルールを何回も繰り返して枝を伸ばす。F は「前へ伸びる」、[ ] は「枝分かれ」、"
                  "& や / は「向きを変える」。葉は、できた枝の表面に点をまいてコピーする。",
                  tags=["モデリング", "L-system", "Karma"])
    g.shot_dir = (1.0, 0.25, 1.1)
    leaf = g.node("grid", "leaf_blank", orient="xy", size=(1, 1), rows=8, cols=4, t=(0, 0.5, 0))
    shape = g.node("attribwrangle", "leaf_shape", [leaf], snippet=(
        "// 板を葉の形にする。v = 付け根 0 → 先 1\n"
        "float v = clamp(@P.y, 0, 1);\n"
        "@P.x *= chf('width') * sin(PI * pow(v, 0.8));      // 付け根と先が細い\n"
        "@P.y = v * chf('length');\n"
        "@P.z = -0.3 * chf('length') * v * v;                // 先が少し垂れる\n"
        "v@Cd = lerp({0.1, 0.24, 0.04}, {0.26, 0.42, 0.07}, v);   // 付け根は濃く、先は明るい緑"))
    kit_spare(shape, width=0.06, length=0.11)
    mark = g.node("attribwrangle", "mark_leaf", [shape], snippet="i@isleaf = 1;   // 葉の面に印を付ける（あとで材質を分ける）")
    mark.parm("class").set(1)
    shape = mark
    g.step(shape, "葉を1枚作る",
           "<code>grid</code>（縦長に 4 × 8 に割る）を <code>attribwrangle</code> で葉の形にする。付け根から先への位置 v で幅を "
           "<strong>sin</strong> の形（付け根と先が細い）にし、先を少し垂らす。長さ 11 cm・幅 6 cm（広葉樹の葉の大きさ）。",
           cap="葉1枚。", shading="smoothwire", bbox=hou.BoundingBox(-0.06, 0, -0.06, 0.06, 0.12, 0.06))

    branches = g.node("lsystem", "grow", type="tube", generations=12, stepinit=0.5, stepscale=0.82,
                      thickinit=0.34, thickscale=0.68, angleinit=38, randscale=0.3, randseed=4, gravity=0.15,
                      premise="FFA", rule1='A=!"[B]////[B]////B', rule2="B=&FFA", cols=10)
    g.step(branches, "ルールを書いて、枝を伸ばす",
           "<code>lsystem</code> の Type を <strong>Tube</strong>（太さのある枝）にし、ルールを書く。"
           "Premise（はじまり）は <strong>FFA</strong>＝2回伸びてから A。Rule 1 <strong>A=!\"[B]////[B]////B</strong> は「細く・短くしてから、"
           "向きを変えつつ枝 B を3本出す」。Rule 2 <strong>B=&FFA</strong> は「少し倒して2回伸び、先でまた A」。"
           "Generations 12 で、この書き換えを12回繰り返す。本物の広葉樹は、太い幹が低い所で分かれ、枝が横へ広がって丸い樹冠になる。"
           "そこで Thickness 0.34（太い幹）・Angle 38（枝を大きく開く）にし、幹を短くする。Random Scale 0.3 で角度と長さをばらつかせ、"
           "Gravity 0.15 で枝先を少し垂らす。",
           cap="12回の書き換えで育った枝。", shading="smooth", ui_parm="rule1")
    # 面の大きさで割った「細さ」を密度にして、細い枝（枝先）ほど多く葉をまく。そのままだと太い枝に葉が固まる
    thin = g.node("measure::2.0", "segment_area", [branches], measure="area", attribname="area")
    weight = g.node("attribwrangle", "twig_weight", [thin], snippet=(
        "// 細い枝（面が小さい）ほど大きな値。幹や太い枝はほぼ 0\n"
        "f@leafdensity = pow(1e-4 / max(f@area, 1e-6), 1.5);"))
    weight.parm("class").set(1)
    spots = g.node("scatter::2.0", "leaf_spots", [weight], npts=45000, seed=2, usedensityattrib=1,
                   densityattrib="leafdensity")
    turn = g.node("attribwrangle", "leaf_turn", [spots], snippet=(
        "// 葉は細い枝（先のほう）にだけ付ける。太い枝や幹には付かない。向き・大きさ・色は1枚ずつばらばらにする\n"
        "if (@P.y < chf('lowest')) removepoint(0, @ptnum);\n"
        "p@orient = quaternion(radians(set(rand(@ptnum) * 360, rand(@ptnum + 1) * 360, rand(@ptnum + 2) * 360)), 0);\n"
        "f@pscale = fit01(rand(@ptnum + 3), 0.7, 1.2);\n"
        "@P += (vector(rand(@ptnum + 7)) - 0.5) * 0.12;   // 枝から少し離して、ふんわりした房にする\n"
        "// 外側の日の当たる葉は明るい黄緑、内側は濃い緑\n"
        "vector c = getbbox_center(0);\n"
        "float out = clamp(length(@P - c) / 2.2, 0, 1);\n"
        "v@Cd = lerp({0.07, 0.17, 0.03}, {0.24, 0.38, 0.07}, out) * fit01(rand(@ptnum + 5), 0.75, 1.2);"))
    kit_spare(turn, lowest=0.5)
    leaves = g.node("copytopoints::2.0", "leaves", [shape, turn], targetattribs=1)
    leaves.parm("applyto1").set("points")
    leaves.parm("applyattribs1").set("Cd")
    tree = g.node("merge", "tree", [branches, leaves])
    n_leaves = len(turn.geometry().points())
    g.step(tree, "枝に葉をまいて付ける",
           "葉は枝先に付くので、<code>measure</code> で枝の面ごとの面積を測り、<code>attribwrangle</code>（Primitives）で「細さ」<strong>leafdensity</strong>（面積が小さいほど大きい）を作る。"
           "<code>scatter</code> の Density Attribute にこれを使って 45,000 個の点をまくと、細い枝に集まる。面積のまままくと、太い枝に葉が固まった（前の版）。"
           "<code>attribwrangle</code> で高さ 0.5 m より下の点を消し、枝から少し離してふんわりさせる。"
           "残った点に、ばらばらの向き orient と大きさ pscale（0.7〜1.2）を付け、<code>copytopoints</code> で葉を並べる。"
           "色も1枚ずつ変え、樹冠の外側（日の当たる所）ほど明るい黄緑、内側ほど濃い緑にする。"
           f"葉は {n_leaves:,} 枚。枝先ほど枝が多いので、葉も自然に外側へ集まり、丸い樹冠になる。",
           cap=f"{n_leaves:,} 枚の葉が付いた木。", shading="smooth", ui_parm="lowest")

    bark = g.mat("bark_mat", basecolor=(0.16, 0.1, 0.06), rough=0.85)
    foliage = g.mat("leaf_mat", basecolor=(1, 1, 1), rough=0.55, sheen=0.3)
    painted = g.assign(g.assign(tree, bark, "assign_bark"), foliage, "assign_leaf", group="@isleaf==1")
    g.step(painted, "幹と葉に材質を当てる",
           "幹は茶色で Roughness 0.85。葉は Base Color を白にして点の色 Cd（緑）を使う。"
           "葉を作ったときに、Primitives の <code>attribwrangle</code> で面に <strong>isleaf = 1</strong> の印を付けておいた。"
           "2つ目の <code>material</code> の Group に <strong>@isleaf==1</strong> と書くと、葉だけに当たる。",
           cap="材質を当てた状態。", shot=False)
    ground = g.node("grid", "meadow", size=(14, 14), rows=2, cols=2, t=(0, 0.002, 0))
    grass = g.mat("meadow_mat", basecolor=(0.16, 0.24, 0.07), rough=0.9)
    scene = g.node("merge", "field", [painted, g.assign(ground, grass, "assign_meadow")])
    g.hero(scene, "Karma で撮った仕上がり。L-system で育てた広葉樹。", direction=(1.0, 0.12, 1.1),
           key=3.0, rim=3.0, dome=0.6, dome_color=(0.85, 0.92, 1.0), spp=32, margin=1.15, denoise=True, backdrop=(0.5, 0.62, 0.8), backdrop_reflect=0.0,
           key_color=(1.0, 0.95, 0.85), bbox=painted.geometry().boundingBox())

    # ---- 落とし穴を測る ----
    counts = {}
    for gen in (10, 11, 12):
        branches.parm("generations").set(gen)
        counts[gen] = len(branches.geometry().prims())
    branches.parm("generations").set(12)
    traps = [
        {"title": "J で付けた葉は、枝先の細さに合わせて縮む",
         "body": "はじめは Rule 2 を B=&FFFAJ にして、J の所に葉（長さ 30 cm）をコピーさせた。撮ると葉は枝先の小さな白い点にしか見えなかった。"
                 "J のコピーは枝先の細さに合わせて小さくなるので、この木では scatter で点をまいて copytopoints で付けるほうが扱いやすい。",
         "img": "", "cap": ""},
        {"title": "Generations は2つずつ効く",
         "body": f"面の数は Generations 10 で {counts[10]:,}、11 で {counts[11]:,}、12 で {counts[12]:,}（10 の {counts[12] / counts[10]:.1f} 倍）。"
                 "A は B に、B は A に書き換わるので、2回でやっと1段伸びる。1段伸びると、枝が3本に分かれるので面は約3倍になる。"
                 "奇数に上げても、ほとんど変わらないことがある。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "13個（材質3つ）"], ["枝の面の数", f"{counts[12]:,}"], ["葉", f"{n_leaves:,}枚"]], traps=traps)


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
