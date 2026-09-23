# -*- coding: utf-8 -*-
"""実践「霧の森に光の筋を差す」— 幹を並べ、霧（ボリューム）で満たし、葉の層のすき間から日を差し込ませる。

本物の「光の筋」（薄明光線）は、霧や細かい水滴で満ちた空気に、木の葉のすき間から日が差すと見える。
霧が無ければ光は見えず、すき間が無ければ筋にならない。つまり「霧」「穴のあいた覆い」「強い一方向の光」の3つがそろえば出る。

    hython examples/pr_fog.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("fog", "霧の森に光の筋を差す",
                  "森の中を霧（ボリューム）で満たし、上に穴だらけの葉の層を置いて、斜め上から強い日を当てる。"
                  "霧が光を散らすので、葉のすき間を通った光だけが筋になって見える。幹は円柱を並べるだけで足りる。",
                  tags=["レンダリング", "ボリューム", "Karma", "散布"])
    g.shot_dir = (0.3, 0.18, 1.0)
    ground = g.node("grid", "ground", size=(30, 30), rows=2, cols=2)
    spots = g.node("scatter::2.0", "tree_spots", [ground], npts=240, relaxpoints=1, relaxiterations=20, seed=3)
    sizes = g.node("attribwrangle", "tree_sizes", [spots], snippet=(
        "// カメラの前（手前の細長い帯）には木を立てない。目の前に幹があると何も見えない\n"
        "if (@P.z > -4 && abs(@P.x - 0.25 * (@P.z + 4)) < 1.3) removepoint(0, @ptnum);\n"
        "// 幹の太さを木ごとに変える（pscale）。向きも少し傾ける\n"
        "f@pscale = fit01(rand(@ptnum + 5), 0.6, 1.4);\n"
        "vector tilt = set(rand(@ptnum + 1) - 0.5, 0, rand(@ptnum + 2) - 0.5) * 0.06;\n"
        "p@orient = dihedral({0, 1, 0}, normalize(set(0, 1, 0) + tilt));"))
    trunk = g.node("tube", "trunk", type="poly", rad=(0.11, 0.15), height=16, cols=20, t=(0, 8, 0))
    trees = g.node("copytopoints::2.0", "trees", [trunk, sizes])
    g.step(trees, "幹を並べる",
           "30 m 四方の <code>grid</code> に、<code>scatter</code> で <strong>240 本</strong>ぶんの点をまく（Relax を入れて、木どうしが重ならないようにする）。"
           "カメラは森の中に置くので、森は画面より広く作る（端が写ると作り物に見える）。"
           "<code>attribwrangle</code> で、カメラの前の細長い帯にある点を消して空き地をつくり、木ごとに太さ <strong>pscale</strong> を 0.6〜1.4 倍に変え、<strong>orient</strong> で少しだけ傾ける。"
           "<code>tube</code>（高さ 16 m、根元が少し太い）を <code>copytopoints</code> で並べる。葉は画面の外（上）にあるので、幹だけで森に見える。",
           cap="240 本の幹。", shading="smooth", bbox=hou.BoundingBox(-15, 0, -15, 15, 16, 15))

    leaves = g.node("grid", "canopy", size=(44, 44), rows=200, cols=200, t=(0, 11, 0))
    holes = g.node("attribwrangle", "leaf_gaps", [leaves], snippet=(
        "// 葉の層にすき間をあける。ノイズが大きい所の面を消す（ここを光が通る）\n"
        "if (noise(@P * chf('gap_size') + 1.3) > chf('open')) removeprim(0, @primnum, 1);"))
    holes.parm("class").set(1)
    kit_spare(holes, gap_size=0.9, open=0.62)
    g.step(holes, "穴だらけの葉の層を置く",
           "44 m 四方の <code>grid</code>（200 × 200 に割る）を高さ 11 m に置く。<code>attribwrangle</code> を Primitives で回し、"
           "<strong>ノイズが 0.62 より大きい所の面を消す</strong>。消えた所が葉のすき間になり、ここを通った光だけが筋になる。"
           "この層は画面の上の外にあるので、カメラには写らない。",
           cap="ところどころに穴のあいた葉の層。", shading="smooth", ui_parm="open",
           bbox=hou.BoundingBox(-22, 10, -22, 22, 12, 22))

    fog = g.node("volume", "fog", sizex=30, sizey=11, sizez=30, ty=5.5, uniformsamples=4, samplediv=110)
    fog.parm("name").set("density")   # Guide.node の引数 name（ノード名）とぶつかるので別に入れる
    thick = g.node("volumewrangle", "fog_density", [fog], snippet=(
        "// 霧の濃さ。下ほど濃く、ノイズでむらを付ける\n"
        "float low = exp(-@P.y / chf('height'));\n"
        "float lumps = fit(noise(@P * 0.35), 0.3, 0.7, 0.5, 1.3);\n"
        "f@density = chf('amount') * low * lumps;"))
    kit_spare(thick, amount=0.025, height=5.0)
    g.step(thick, "霧で満たす",
           "<code>volume</code> で、名前 <strong>density</strong> の箱（30 × 11 × 30 m、森と同じ広さ）を作る。Uniform Sampling Divs 110 で、升は約 0.27 m。"
           "霧のむらはゆるやかなので、升は粗くてよい。"
           "<code>volumewrangle</code> で濃さを決める。<strong>amount = 0.025</strong> を基準に、高さで弱める（height 5 m で 1/e になる）、"
           "ノイズで 0.5〜1.3 倍のむらを付ける。霧はうすいほうが筋がはっきりする。",
           cap="下ほど濃い霧（ビューポートでは箱の影で見える）。", shading="smooth", ui_parm="amount",
           bbox=hou.BoundingBox(-15, 0, -15, 15, 11, 15))

    bark = g.mat("bark_mat", basecolor=(0.09, 0.075, 0.06), rough=0.9)
    moss_floor = g.mat("floor_mat", basecolor=(0.06, 0.07, 0.035), rough=0.95)
    canopy_mat = g.mat("canopy_mat", basecolor=(0.02, 0.04, 0.01), rough=0.9)
    final = g.node("merge", "forest", [g.assign(trees, bark, "assign_bark"), g.assign(ground, moss_floor, "assign_floor"),
                                       g.assign(holes, canopy_mat, "assign_canopy"), thick])
    sun = hou.node("/obj").createNode("hlight::2.0", "sun")
    sun.parm("light_type").set("distant")
    sun.parm("light_intensity").set(2.0)
    sun.parmTuple("light_color").set((1.0, 0.9, 0.72))
    sun.parmTuple("r").set((-58, 150, 0))
    g.step(final, "日を斜め上から当てる",
           "幹・地面・葉の層に暗い材質を当て、霧とまとめる。<code>hlight</code> を <strong>Distant</strong>（太陽のように平行な光）にし、"
           "Intensity 2・少し黄色、Rotate (−58, 150, 0) で <strong>カメラの向こう側の斜め上</strong>から差す向きにする。"
           "光は向こうからこちらへ来るので、霧の中の筋が明るく見える（逆光）。ほかの明かりはごく弱くする。",
           cap="材質と光を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。葉のすき間を通った日が、霧の中で筋になる。",
           direction=(0.25, 0.1, 1.0), key=0.0, rim=0.0, dome=0.06, dome_color=(0.5, 0.6, 0.7), floor=False,
           spp=64, margin=1.0, bbox=hou.BoundingBox(-3.5, 0, -10, 3.5, 5, 2), denoise=True)

    # ---- 落とし穴を測る ----
    n_faces = len(leaves.geometry().prims())
    n_left = len(holes.geometry().prims())
    holes.parm("open").set(0.5)
    n_left_05 = len(holes.geometry().prims())
    holes.parm("open").set(0.62)
    # 霧を 0 にした絵を、同じカメラで撮る（落とし穴の図）
    thick.parm("amount").set(0.0)
    karma = hou.node("/out/hero_karma")
    karma.parm("picture").set(os.path.join(kit.OUT, "pr_fog_nofog.png").replace("\\", "/"))
    karma.parm("samplesperpixel").set(24)
    karma.render(verbose=False)
    thick.parm("amount").set(0.025)
    karma.parm("picture").set(os.path.join(kit.OUT, "pr_fog_hero.png").replace("\\", "/"))
    traps = [
        {"title": "霧が無いと、光の筋は見えない",
         "body": "fog_density の amount を 0 にして同じカメラで撮ると、光は地面と幹に当たった所だけが明るくなり、空中の筋は消えた。"
                 "光の筋は、空気中の霧が光を横へ散らして見えるもの。",
         "img": "pr_fog_nofog.png", "cap": "霧を 0 にしたとき。空中に光が見えない。"},
        {"title": "すき間の量",
         "body": f"葉の層は {n_faces:,} 面のうち、open 0.62 で {n_left:,} 面が残った（{1 - n_left / n_faces:.0%} が穴）。"
                 f"open を 0.5 にすると {n_left_05:,} 面（{1 - n_left_05 / n_faces:.0%} が穴）。open で光の入る量を決める。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "17個（材質3つ・光1つ）"], ["木", "240本"]], traps=traps)


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
