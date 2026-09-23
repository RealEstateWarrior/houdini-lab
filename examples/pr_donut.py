# -*- coding: utf-8 -*-
"""実践「ドーナツを飾る」— トーラスの生地に、上側だけアイシングをかけ、カラースプレー（スプリンクル）を散らす。

本物のアイシングは、ドーナツの上半分を覆い、縁は垂れて波打つ。表面はつやがあり、少し厚みがある。
スプリンクルは細長い粒で、表面に寝た向きでばらばらに散らばる。

    hython examples/pr_donut.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

SPRINKLES = 420


def main():
    import hou
    g = kit.Guide("donut", "ドーナツを飾る",
                  "トーラス（ドーナツ形）の生地を作り、上を向いた面だけを取り出してアイシングにする。縁はノイズで波打たせる。"
                  "アイシングの上に点をまき、細長い粒を表面に寝かせて並べるとカラースプレーになる。",
                  tags=["モデリング", "VEX", "複製", "Karma"])
    g.shot_dir = (0.5, 0.9, 1.0)
    # 本物のリングドーナツは、直径 9〜10 cm、穴 2〜3 cm、高さ 3 cm ほど（写真と比べて決めた）
    dough = g.node("torus", "dough", type="poly", rad=(0.03, 0.0175), rows=64, cols=128)
    dough = g.node("normal", "dough_dir", [dough])   # 次の wrangle で面の向き N を使うので、先に作る
    puffy = g.node("attribwrangle", "puffy", [dough], snippet=(
        "// 少しつぶして、ふっくらむらを付ける。\n"
        "@P.y *= 0.85;\n"
        "@P += @N * (noise(@P * 70) - 0.5) * 0.0018;\n"
        "// 揚げ色：上下は濃いきつね色、側面の真ん中は油に浸からず白っぽい帯になる\n"
        "float band = 1 - smooth(0.0, 0.35, abs(v@N.y));\n"
        "v@Cd = lerp({0.55, 0.3, 0.1}, {0.92, 0.8, 0.58}, band) * fit01(noise(@P * 120), 0.85, 1.1);"))
    puffy = g.node("normal", "puffy_dir", [puffy])   # 形を変えたので、向きを作り直す
    g.step(puffy, "生地を作る",
           "本物のリングドーナツは、直径 9〜10 cm で穴は 2〜3 cm と小さい。<code>torus</code> を <strong>半径 3 cm・太さ 1.75 cm</strong>"
           "（直径 9.5 cm、穴 2.5 cm）にして 64 × 128 に割り、<code>attribwrangle</code> で高さを 0.85 倍につぶす。"
           "面の向き N にそってノイズでわずかに出し入れし、揚げた生地のふっくらしたむらにする。"
           "色は、上下を濃いきつね色、側面の真ん中を白っぽい帯にする（揚げるときに油に浸からない所）。"
           "torus の出力には N が無いので、前後に <code>normal</code> を入れて向きを作る（形を変えたあとは作り直す）。",
           cap="ふっくらした生地と、側面の白い帯。", shading="smooth")

    cover = g.node("attribwrangle", "icing_area", [puffy], snippet=(
        "// 上を向いた面だけ残す。縁はノイズで上下させて、垂れたように波打たせる\n"
        "vector n = prim_normal(0, @primnum, 0.5, 0.5);\n"
        "vector c = prim(0, 'P', @primnum);\n"
        "float edge = chf('edge') + (noise(c * 90) - 0.5) * chf('wobble');\n"
        "if (n.y < edge) removeprim(0, @primnum, 1);"))
    cover.parm("class").set(1)
    kit_spare(cover, edge=0.15, wobble=0.7)
    extruded = g.node("polyextrude::2.0", "icing_thickness", [cover], dist=0.0025, outputback=1)
    # 生地から受け継いだ点の色（揚げ色）を消す。残っていると、材質のピンクに揚げ色が掛かってオレンジに写った
    icing = g.node("attribdelete", "drop_dough_color", [extruded], ptdel="Cd")
    g.step(icing, "アイシングをかける",
           "生地のコピーを <code>attribwrangle</code>（Primitives）で削る。面の向きの上下成分 N.y が <strong>edge = 0.15</strong> より小さい面を消すと、"
           "上の面だけが残る（本物のアイシングも、側面の真ん中までは届かない）。edge をノイズで上下させる（wobble 0.7）と、縁が垂れたように波打つ。"
           "<code>polyextrude</code> で <strong>2.5 mm</strong> 押し出して厚みを付ける（Output Back で裏も閉じる）。"
           "アイシングは生地から点の色 Cd（揚げ色）を受け継いでいるので、<code>attribdelete</code> で消しておく。"
           "残したままだと、材質のピンクに揚げ色が掛け合わされて、オレンジに写った。",
           cap="上の面を覆う、縁の波打ったアイシング。", shading="smooth", ui_parm="edge")

    spots = g.node("scatter::2.0", "sprinkle_spots", [cover], npts=SPRINKLES, seed=4, relaxpoints=1)
    lay = g.node("attribwrangle", "lay_flat", [spots], snippet=(
        "// 粒を表面に寝かせる。長い向き（z）を表面にそったばらばらの向きに、上（y）を面の向き N に合わせる\n"
        "vector n = normalize(v@N);\n"
        "vector t = normalize(cross(n, set(rand(@ptnum), rand(@ptnum + 1), rand(@ptnum + 2)) - 0.5));\n"
        "p@orient = quaternion(maketransform(t, n));\n"
        "@P += n * 0.0031;   // アイシングの厚み（2.5 mm）の上に乗せる\n"
        "vector cols[] = {{0.95, 0.2, 0.25}, {1.0, 0.8, 0.1}, {0.2, 0.6, 0.95}, {0.3, 0.8, 0.35}, {0.97, 0.95, 0.92}, {0.75, 0.35, 0.85}};\n"
        "v@Cd = cols[int(rand(@ptnum + 9) * len(cols))];"))
    grain = g.node("tube", "sprinkle", type="poly", orient="z", rad=(0.00055, 0.00055), height=0.0055, cols=10, cap=1)
    sprinkles = g.node("copytopoints::2.0", "sprinkles", [grain, lay], targetattribs=1)
    sprinkles.parm("applyto1").set("points")
    sprinkles.parm("applyattribs1").set("Cd")
    g.step(sprinkles, "カラースプレーを散らす",
           f"アイシングの面に <code>scatter</code> で {SPRINKLES} 個の点をまく（Relax で間をそろえる）。"
           "<code>attribwrangle</code> で、粒の長い向きを「面にそったばらばらの向き」、上を面の向き N に合わせた <strong>orient</strong> を作り、"
           "アイシングの厚みぶん持ち上げる。色は6色から選ぶ。細い円柱の <code>tube</code>（長さ 5.5 mm・太さ 1.1 mm、端を閉じる）を <code>copytopoints</code> で並べ、"
           "色は Target Attributes の「Apply to: Points」「Cd」で移す。",
           cap=f"{SPRINKLES} 粒のカラースプレー。", shading="smooth", ui_parm="npts")

    # Subsurface（SSS）を入れると、Karma が 20 分たっても撮り終わらなかった（2026-09-24）。ここでは入れない
    bread = g.mat("dough_mat", basecolor=(1, 1, 1), rough=0.65, sheen=0.4)   # 色は点の Cd（揚げ色と白い帯）
    glaze = g.mat("icing_mat", basecolor=(0.95, 0.45, 0.66), rough=0.2, coat=0.5, sheen=0.0)
    candy = g.mat("sprinkle_mat", basecolor=(1, 1, 1), rough=0.3, coat=0.4)
    final = g.node("merge", "donut", [g.assign(puffy, bread, "assign_dough"), g.assign(icing, glaze, "assign_icing"),
                                      g.assign(sprinkles, candy, "assign_sprinkles")])
    g.step(final, "材質を当てる",
           "生地は Base Color を白にして点の色 Cd（揚げ色と白い帯）を使い、Roughness 0.65・Sheen 0.4。アイシングはピンクで <strong>Roughness 0.15・Coat 0.6</strong>（つや）。"
           "スプリンクルは Base Color を白にして点の色 Cd を使う。"
           "Subsurface（光が中へ入って散る）も試したが、このドーナツでは Karma が 20 分たっても撮り終わらなかったので入れていない。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。ピンクのアイシングとカラースプレーのドーナツ。", direction=(0.45, 0.75, 1.0),
           key=0.05, rim=0.05, dome=0.22, dome_color=(1.0, 1.0, 1.0), spp=32, margin=0.8, backdrop=(0.32, 0.32, 0.33),
           key_color=(1.0, 1.0, 1.0))

    # ---- 落とし穴を測る ----
    faces_all = len(puffy.geometry().prims())
    kept = len(cover.geometry().prims())
    cover.parm("wobble").set(0.0)
    kept_flat = len(cover.geometry().prims())
    cover.parm("wobble").set(0.7)
    traps = [
        {"title": "アイシングの広さは edge で決まる",
         "body": f"生地の {faces_all:,} 面のうち、edge 0.15 で {kept:,} 面（{kept / faces_all:.0%}）がアイシングになった。"
                 f"wobble を 0 にすると {kept_flat:,} 面で、縁がまっすぐな線になる。本物らしい垂れは wobble で出す。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "12個（材質3つ）"], ["スプリンクル", f"{SPRINKLES}粒"]], traps=traps)


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
