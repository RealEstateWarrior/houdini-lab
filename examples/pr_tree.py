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
    kit_spare(shape, width=0.16, length=0.3)
    mark = g.node("attribwrangle", "mark_leaf", [shape], snippet="i@isleaf = 1;   // 葉の面に印を付ける（あとで材質を分ける）")
    mark.parm("class").set(1)
    shape = mark
    g.step(shape, "葉を1枚作る",
           "<code>grid</code>（縦長に 4 × 8 に割る）を <code>attribwrangle</code> で葉の形にする。付け根から先への位置 v で幅を "
           "<strong>sin</strong> の形（付け根と先が細い）にし、先を少し垂らす。長さ 30 cm・幅 16 cm。"
           "木の高さが 5 m ほどになるので、本物より少し大きめにしないと遠目に見えない。",
           cap="葉1枚。", shading="smoothwire", bbox=hou.BoundingBox(-0.16, 0, -0.16, 0.16, 0.32, 0.16))

    branches = g.node("lsystem", "grow", type="tube", generations=8, stepinit=0.55, stepscale=0.85,
                      thickinit=0.2, thickscale=0.72, angleinit=30, randscale=0.25, randseed=4, gravity=0.3,
                      premise="FFFA", rule1='A=!"[B]////[B]////B', rule2="B=&FFFA", cols=8)
    g.step(branches, "ルールを書いて、枝を伸ばす",
           "<code>lsystem</code> の Type を <strong>Tube</strong>（太さのある枝）にし、ルールを書く。"
           "Premise（はじまり）は <strong>FFFA</strong>＝3回伸びてから A。Rule 1 <strong>A=!\"[B]////[B]////B</strong> は「細く・短くしてから、"
           "向きを変えつつ枝 B を3本出す」。Rule 2 <strong>B=&FFFA</strong> は「少し倒して3回伸び、先でまた A」。"
           "Generations 8 で、この書き換えを8回繰り返す。Thickness 0.2 で幹を太くする。Random Scale 0.25 で角度と長さをばらつかせ、"
           "Gravity 0.3 で枝先を垂らす。",
           cap="8回の書き換えで育った枝。", shading="smooth", ui_parm="rule1")
    spots = g.node("scatter::2.0", "leaf_spots", [branches], npts=5000, seed=2)
    turn = g.node("attribwrangle", "leaf_turn", [spots], snippet=(
        "// 幹の低い所には葉を付けない。向きと大きさはばらばらにする\n"
        "if (@P.y < chf('lowest')) removepoint(0, @ptnum);\n"
        "p@orient = quaternion(radians(set(rand(@ptnum) * 360, rand(@ptnum + 1) * 360, rand(@ptnum + 2) * 360)), 0);\n"
        "f@pscale = fit01(rand(@ptnum + 3), 0.6, 1.2);"))
    kit_spare(turn, lowest=2.0)
    tree = g.node("merge", "tree", [branches, g.node("copytopoints::2.0", "leaves", [shape, turn])])
    n_leaves = len(turn.geometry().points())
    g.step(tree, "枝に葉をまいて付ける",
           f"<code>scatter</code> で枝の表面に 5000 個の点をまき、<code>attribwrangle</code> で高さ 2 m より下（幹）の点を消す。"
           "残った点に、ばらばらの向き orient と大きさ pscale（0.6〜1.2）を付け、<code>copytopoints</code> で葉を並べる。"
           f"葉は {n_leaves:,} 枚。枝先ほど枝が多いので、点も葉も自然に上のほうへ集まる。",
           cap=f"{n_leaves:,} 枚の葉が付いた木。", shading="smooth", ui_parm="lowest")

    bark = g.mat("bark_mat", basecolor=(0.16, 0.1, 0.06), rough=0.85)
    foliage = g.mat("leaf_mat", basecolor=(1, 1, 1), rough=0.55, sheen=0.3)
    painted = g.assign(g.assign(tree, bark, "assign_bark"), foliage, "assign_leaf", group="@isleaf==1")
    g.step(painted, "幹と葉に材質を当てる",
           "幹は茶色で Roughness 0.85。葉は Base Color を白にして点の色 Cd（緑）を使う。"
           "葉を作ったときに、Primitives の <code>attribwrangle</code> で面に <strong>isleaf = 1</strong> の印を付けておいた。"
           "2つ目の <code>material</code> の Group に <strong>@isleaf==1</strong> と書くと、葉だけに当たる。",
           cap="材質を当てた状態。", shot=False)
    g.hero(painted, "Karma で撮った仕上がり。L-system で育てた木。", direction=(1.0, 0.18, 1.1),
           key=3.0, rim=5.0, dome=0.5, dome_color=(0.85, 0.92, 1.0), spp=64, margin=1.08, backdrop=(0.5, 0.62, 0.72))

    # ---- 落とし穴を測る ----
    counts = {}
    for gen in (6, 7, 8):
        branches.parm("generations").set(gen)
        counts[gen] = len(branches.geometry().prims())
    branches.parm("generations").set(8)
    traps = [
        {"title": "J で付けた葉は、枝先の細さに合わせて縮む",
         "body": "はじめは Rule 2 を B=&FFFAJ にして、J の所に葉（長さ 30 cm）をコピーさせた。撮ると葉は枝先の小さな白い点にしか見えなかった。"
                 "J のコピーは枝先の細さに合わせて小さくなるので、この木では scatter で点をまいて copytopoints で付けるほうが扱いやすい。",
         "img": "", "cap": ""},
        {"title": "Generations は2つずつ効く",
         "body": f"面の数は Generations 6 で {counts[6]:,}、7 で {counts[7]:,}（同じ）、8 で {counts[8]:,}（{counts[8] / counts[6]:.1f} 倍）。"
                 "A は B に、B は A に書き換わるので、2回でやっと1段伸びる。1段伸びると、枝が3本に分かれるので面は約3倍になる。"
                 "奇数に上げても何も変わらないことがある。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "7個（材質2つ）"], ["面の数", f"{counts[8]:,}"]], traps=traps)


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
