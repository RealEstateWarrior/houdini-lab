# -*- coding: utf-8 -*-
"""実践「雪だるまを作る」— 大小の雪玉を重ね、でこぼこを付けて、枝の腕・炭の目・にんじんの鼻を付ける。

本物の雪だるまは、転がして作った玉なので完全な球ではなく、表面は少しでこぼこで、雪の粒で白くやわらかく光る。
雪は光が中に入って散る（表面の下で光が広がる）ので、影の縁が青白くやわらかい。

    hython examples/pr_snowman.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("snowman", "雪だるまを作る",
                  "大・中・小の3つの雪玉を少しめり込ませて重ね、mountain で手で固めたようなでこぼこを付ける。"
                  "腕は曲がった線に太さを付けた枝、目とボタンは炭、鼻はにんじん。雪の材質は Subsurface（光が中で散る）を入れると雪らしくなる。",
                  tags=["モデリング", "材質", "Karma"])
    g.shot_dir = (0.7, 0.35, 1.2)
    balls = []
    for i, (r, y) in enumerate([(0.34, 0.3), (0.25, 0.8), (0.17, 1.16)]):
        balls.append(g.node("sphere", f"ball{i}", type="polymesh", rad=(r, r * 0.93, r), rows=48, cols=96, t=(0, y, 0)))
    body = g.node("merge", "three_balls", balls)
    lumpy = g.node("mountain::2.0", "hand_packed", [body], height=0.018, elementsize=0.12, rough=0.55, oct=5)
    g.step(lumpy, "雪玉を3つ重ねる",
           "<code>sphere</code> を3つ（半径 34・25・17 cm、少しつぶす）作り、上の玉が下の玉に少しめり込む高さに置く。"
           "<code>merge</code> でまとめ、<code>mountain</code> で <strong>Height 0.018・Element Size 0.12</strong> の浅いでこぼこを付ける。"
           "手で固めた雪玉の、ゆるいでこぼこになる。",
           cap="でこぼこの付いた3つの雪玉。", shading="smooth")

    arms = g.node("attribwrangle", "twig_arms", snippet=(
        "// 左右の腕の枝。付け根から外へ、少し上へ曲がりながら伸ばす。先は2つに分かれる\n"
        "for (int side = -1; side <= 1; side += 2) {\n"
        "    int prim = addprim(0, 'polyline');\n"
        "    vector tip = 0;\n"
        "    for (int i = 0; i <= 8; i++) {\n"
        "        float t = i / 8.0;\n"
        "        vector p = set(side * (0.2 + t * 0.42), 0.86 + t * 0.2 + sin(t * 9 + side) * 0.02, (rand(side + i) - 0.5) * 0.04);\n"
        "        addvertex(0, prim, addpoint(0, p));\n"
        "        tip = p;\n"
        "    }\n"
        "    int twig = addprim(0, 'polyline');\n"
        "    vector fork = tip - set(side * 0.12, 0.03, 0);\n"
        "    addvertex(0, twig, addpoint(0, fork));\n"
        "    addvertex(0, twig, addpoint(0, fork + set(side * 0.08, 0.1, 0.02)));\n"
        "}"))
    arms.parm("class").set(0)
    sticks = g.node("polywire", "twig_thickness", [arms], radius=0.012)
    g.step(sticks, "枝の腕を付ける",
           "Detail の <code>attribwrangle</code> で、左右の腕を折れ線で描く。付け根から外へ伸ばしながら少し上げ、"
           "<code>sin</code> で小さく曲げ、先の手前から小枝を1本分ける。<code>polywire</code>（Radius 0.012）で線に太さを付けると枝になる。",
           cap="左右の枝の腕。", shading="smooth")

    coal_pts = g.node("attribwrangle", "coal_spots", snippet=(
        "// 目2つとボタン3つ。雪玉の表面に置くため、玉の中心から前（+z）へ半径ぶん出す\n"
        "vector c1 = {0, 1.16, 0}; float r1 = 0.165;\n"
        "float xs[] = {-0.055, 0.055};\n"
        "foreach (float x; xs) {\n"
        "    vector d = normalize(set(x, 0.05, 0.16));\n"
        "    addpoint(0, c1 + d * r1);\n"
        "}\n"
        "vector c2 = {0, 0.8, 0}; float r2 = 0.24;\n"
        "float ys[] = {0.1, 0.0, -0.1};\n"
        "foreach (float y; ys) {\n"
        "    vector d = normalize(set(0, y, 0.24));\n"
        "    addpoint(0, c2 + d * r2);\n"
        "}"))
    coal_pts.parm("class").set(0)
    coal = g.node("copytopoints::2.0", "coal", [g.node("sphere", "coal_piece", type="polymesh", rad=(0.02, 0.018, 0.016),
                                                        rows=8, cols=12), coal_pts])
    nose = g.node("tube", "carrot", type="poly", orient="z", rad=(0.018, 0.0), height=0.14, cols=16, t=(0, 1.15, 0.225))
    face = g.node("merge", "face", [coal, nose])
    g.step(face, "炭の目とボタン、にんじんの鼻",
           "Detail の <code>attribwrangle</code> で、目2つとボタン3つの位置を、雪玉の中心から前へ半径ぶん出した所に置く。"
           "小さくつぶした <code>sphere</code> を <code>copytopoints</code> で並べて炭にする。"
           "鼻は <code>tube</code> の片方の半径を 0 にした円すい（長さ 14 cm）を前へ向けて刺す。",
           cap="顔と、胸のボタン。", shading="smooth", bbox=hou.BoundingBox(-0.2, 0.6, -0.1, 0.2, 1.35, 0.35))

    snow = g.mat("snow_mat", basecolor=(0.95, 0.96, 0.98), rough=0.7, sss=0.6, ssscolor=(0.75, 0.85, 1.0), sssdist=0.05)
    bark = g.mat("twig_mat", basecolor=(0.13, 0.08, 0.05), rough=0.8)
    charcoal = g.mat("coal_mat", basecolor=(0.02, 0.02, 0.02), rough=0.5)
    carrot = g.mat("carrot_mat", basecolor=(0.9, 0.35, 0.05), rough=0.5)
    final = g.node("merge", "snowman", [g.assign(lumpy, snow, "assign_snow"), g.assign(sticks, bark, "assign_twig"),
                                        g.assign(coal, charcoal, "assign_coal"), g.assign(nose, carrot, "assign_carrot")])
    g.step(final, "雪の材質（Subsurface）",
           "雪は <code>principledshader</code> で白く、<strong>Subsurface 0.6・Subsurface Color を青白く・Subsurface Distance 0.05</strong>。"
           "光が表面の下へ入って散るので、影の縁がやわらかく青白くなり、石膏のような硬さが消える。枝・炭・にんじんは普通の材質。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。やわらかく光る雪の玉と、枝の腕。", direction=(0.55, 0.22, 1.2),
           key=2.6, rim=6.0, dome=0.7, dome_color=(0.7, 0.8, 1.0), spp=64, margin=1.08,
           backdrop=(0.55, 0.6, 0.68), key_color=(1.0, 0.95, 0.88))

    # ---- 落とし穴を測る ----
    lumpy.parm("height").set(0.08)
    rough_top = lumpy.geometry().boundingBox().maxvec()[1]
    lumpy.parm("height").set(0.018)
    calm_top = lumpy.geometry().boundingBox().maxvec()[1]
    traps = [
        {"title": "でこぼこは浅く",
         "body": f"mountain の Height を 0.018 から 0.08 にすると、いちばん上の高さが {calm_top:.3f} m から {rough_top:.3f} m に変わり、"
                 "0.08 は、いちばん小さな玉（半径 0.17 m）の半分近い深さ。でこぼこの深さは、玉の大きさと比べて決める。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "19個（材質4つ）"], ["高さ", f"{calm_top:.2f} m"]], traps=traps)


if __name__ == "__main__":
    main()
