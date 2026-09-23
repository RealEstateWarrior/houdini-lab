# -*- coding: utf-8 -*-
"""実践「らせん階段を組む」— 段の板を1枚作り、少しずつ回しながら少しずつ高く並べて、らせん階段にする。

本物のらせん階段は、真ん中の柱のまわりに、扇形の段が一定の角度と高さずつずれて並ぶ。
手すりは段の外の端を結んだらせんの線で、細い柱（手すり子）が段ごとに支える。

    hython examples/pr_stairs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

STEPS = 22
TURN = 22.0      # 1段ごとに回す角度（度）
RISE = 0.18      # 1段ごとの高さ（m）


def main():
    import hou
    g = kit.Guide("stairs", "らせん階段を組む",
                  "扇形の段の板を1枚作り、1段ごとに 22度回して 18 cm 上げた位置へ並べる。真ん中に柱を立て、段の外の端を結んだ"
                  "らせんの線に太さを付けて手すりにする。並べ方は VEX の数行で決まる。",
                  tags=["モデリング", "VEX", "複製", "Karma"])
    g.shot_dir = (0.8, 0.45, 1.2)
    tread = g.node("box", "tread", size=(1.0, 0.04, 0.34), t=(0.62, 0, 0))
    taper = g.node("attribwrangle", "fan_shape", [tread], snippet=(
        "// 板を扇形にする。柱に近い側（x が小さい）ほど奥行きを狭くする\n"
        "@P.z *= fit(@P.x, 0.12, 1.12, 0.35, 1.0);"))
    g.step(taper, "段の板を1枚作る",
           "<code>box</code>（長さ 1 m・厚さ 4 cm・奥行き 34 cm）を、柱から外へ向けて置く（中心を x = 0.62 へずらす）。"
           "<code>attribwrangle</code> で、柱に近い側ほど奥行きを狭くし（0.35 倍）、扇形の段にする。",
           cap="扇形の段の板。", shading="smoothwire", bbox=hou.BoundingBox(0, -0.1, -0.3, 1.2, 0.1, 0.3))

    spots = g.node("attribwrangle", "helix_spots", snippet=(
        "// 1段ごとに、角度 turn 度・高さ rise ずつずらした点を置く。点の orient で段の向きを回す\n"
        "int n = chi('steps');\n"
        "for (int i = 0; i < n; i++) {\n"
        "    float a = radians(i * chf('turn'));\n"
        "    int p = addpoint(0, set(0, (i + 1) * chf('rise'), 0));\n"
        "    setpointattrib(0, 'orient', p, quaternion(a, {0, 1, 0}));\n"
        "}"))
    spots.parm("class").set(0)
    kit_spare(spots, ints={"steps": STEPS}, turn=TURN, rise=RISE)
    treads = g.node("copytopoints::2.0", "all_treads", [taper, spots])
    g.step(treads, "少しずつ回して積み上げる",
           f"Detail の <code>attribwrangle</code> で、<strong>{STEPS} 段</strong>ぶんの点を、真ん中の軸の上に高さ <strong>{RISE} m</strong> ずつ置く。"
           f"点ごとの向き orient を、1段ごとに <strong>{TURN:.0f}度</strong>ずつ回す（y 軸まわり）。<code>copytopoints</code> で段を並べると、"
           f"段は軸のまわりを回りながら上がっていく。{STEPS} 段で {STEPS * TURN:.0f}度（1周と少し）、高さ {STEPS * RISE:.2f} m。",
           cap=f"{STEPS} 段のらせん。", shading="smooth", ui_parm="turn")

    pole = g.node("tube", "center_pole", type="poly", rad=(0.1, 0.1), height=STEPS * RISE + 1.0, cols=32, cap=1,
                  t=(0, (STEPS * RISE + 1.0) / 2, 0))
    rail_line = g.node("attribwrangle", "rail_path", snippet=(
        "// 手すり：段の外の端の上 0.9 m を結ぶ、なめらかならせんの線\n"
        "int n = chi('steps');\n"
        "int prim = addprim(0, 'polyline');\n"
        "for (int k = 0; k <= (n - 1) * 8; k++) {\n"
        "    float i = k / 8.0;\n"
        "    float a = radians(i * chf('turn'));\n"
        "    vector p = set(cos(a) * 1.07, (i + 1) * chf('rise') + 0.9, -sin(a) * 1.07);\n"
        "    addvertex(0, prim, addpoint(0, p));\n"
        "}"))
    rail_line.parm("class").set(0)
    kit_spare(rail_line, ints={"steps": STEPS}, turn=TURN, rise=RISE)
    rail = g.node("polywire", "rail", [rail_line], radius=0.025)
    post_pts = g.node("attribwrangle", "post_spots", [spots], snippet=(
        "// 手すり子：各段の外の端に1本。段と同じ角度で、軸から 1.07 m\n"
        "float a = radians(@ptnum * chf('../helix_spots/turn'));\n"
        "@P += set(cos(a) * 1.07, 0.02, -sin(a) * 1.07);"))
    post = g.node("tube", "post", type="poly", rad=(0.012, 0.012), height=0.9, cols=12, t=(0, 0.45, 0))
    posts = g.node("copytopoints::2.0", "posts", [post, post_pts])
    railing = g.node("merge", "railing", [rail, posts])
    g.step(railing, "柱と手すりを付ける",
           "真ん中に <code>tube</code> の柱を立てる。手すりは、Detail の <code>attribwrangle</code> で段の外の端の 90 cm 上を"
           "細かく（1段を8つに分けて）たどるらせんの線を描き、<code>polywire</code>（Radius 2.5 cm）で太さを付ける。"
           "段の点を外の端へずらして、細い <code>tube</code>（手すり子）を <code>copytopoints</code> で並べる。",
           cap="柱・手すり・手すり子。", shading="smooth")

    wood = g.mat("wood_mat", basecolor=(0.45, 0.27, 0.13), rough=0.45, reflect=0.5)
    iron = g.mat("iron_mat", basecolor=(0.08, 0.08, 0.09), metallic=1.0, rough=0.35)
    final = g.node("merge", "staircase", [g.assign(treads, wood, "assign_wood"),
                                          g.assign(g.node("merge", "metal_parts", [pole, railing]), iron, "assign_iron")])
    g.step(final, "材質を当てる",
           "段は明るい木（Roughness 0.45）、柱と手すりは黒い鉄（Metallic 1・Roughness 0.35）。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。木の段と黒い鉄の手すりのらせん階段。", direction=(0.9, 0.35, 1.2),
           key=3.0, rim=5.0, dome=0.5, spp=48, margin=1.05, backdrop=(0.55, 0.53, 0.5))

    # ---- 落とし穴を測る ----
    spots.parm("turn").set(TURN * 2)
    wide = treads.geometry().boundingBox().sizevec()
    spots.parm("turn").set(TURN)
    normal = treads.geometry().boundingBox().sizevec()
    traps = [
        {"title": "回す角度で、階段の広がりと急さが変わる",
         "body": f"1段 {TURN:.0f}度では、階段全体は横 {normal[0]:.2f} × 奥行き {normal[2]:.2f} m。{TURN * 2:.0f}度にすると {wide[0]:.2f} × {wide[2]:.2f} m で、"
                 f"同じ {STEPS} 段が {STEPS * TURN * 2:.0f}度（{STEPS * TURN * 2 / 360:.1f} 周）回る。1周で上がる高さが半分になり、上の段と頭がぶつかりやすくなる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "17個（材質2つ）"], ["段", f"{STEPS}段・高さ {STEPS * RISE:.2f} m"]], traps=traps)


def kit_spare(node, ints=None, **values):
    """wrangle の chf / chi のつまみを作って値を入れる（GUI の「Create spare parameters」ボタンと同じこと）。"""
    import hou
    group = node.parmTemplateGroup()
    for name, value in (ints or {}).items():
        group.append(hou.IntParmTemplate(name, name, 1, default_value=(value,)))
    for name, value in values.items():
        group.append(hou.FloatParmTemplate(name, name, 1, default_value=(value,)))
    node.setParmTemplateGroup(group)
    for name, value in list((ints or {}).items()) + list(values.items()):
        node.parm(name).set(value)


if __name__ == "__main__":
    main()
