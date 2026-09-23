# -*- coding: utf-8 -*-
"""実践「ひび割れから光る溶岩」— 冷えて固まった黒い岩の板のすき間から、中の溶岩が赤く光る地面を作る。

本物の溶岩の表面は、冷えた黒い殻が亀の甲羅のような板に割れ、割れ目から中の熱い溶岩が見えて光る。
割れ目の真ん中ほど熱く（黄色）、殻の縁ほど冷めている（暗い赤）。細胞のような形は VEX の wnoise（ウォーリーノイズ）で作れる。

    hython examples/pr_lava.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("lava", "ひび割れから光る溶岩",
                  "冷えて固まった黒い岩の板と、そのすき間で光る溶岩を作る。VEX の wnoise で「一番近い点までの距離」と"
                  "「二番目に近い点までの距離」を出し、その差が小さい所を割れ目にする。割れ目だけに光る材質を当てる。",
                  tags=["エフェクト", "VEX", "ノイズ", "Karma"])
    g.shot_dir = (0.4, 0.55, 1.1)
    ground = g.node("grid", "ground", size=(4, 3), rows=300, cols=400)
    g.step(ground, "細かい地面を用意する",
           "<code>grid</code>（4 × 3 m）を <strong>Rows 300・Columns 400</strong> に割る（升 1 cm）。割れ目は数 cm の幅なので、"
           "網が粗いと割れ目が描けない。",
           cap="細かく割った地面。", shading="wire", bbox=hou.BoundingBox(-2, -0.2, -1.5, 2, 0.2, 1.5))

    crust = g.node("attribwrangle", "cracked_crust", [ground], snippet=(
        "// wnoise：まわりに散らばった点のうち、一番近い点までの距離 f1 と、二番目に近い点までの距離 f2 を返す\n"
        "float f1, f2;\n"
        "int seed;\n"
        "wnoise(@P * chf('plate_size'), seed, f1, f2);\n"
        "float gap = f2 - f1;                              // 板と板の境目で 0 になる\n"
        "f@heat = 1 - smooth(0.0, chf('crack_width'), gap);   // 割れ目の真ん中で 1、板の上で 0\n"
        "// 板は少し盛り上がり、でこぼこも付く。割れ目は低い\n"
        "float bumps = noise(@P * 6) * 0.03 + noise(@P * 25) * 0.008;\n"
        "@P.y += smooth(0.0, 0.25, gap) * 0.06 + bumps;"))
    kit_spare(crust, plate_size=2.2, crack_width=0.07)
    g.step(crust, "岩の板と割れ目を作る",
           "<code>attribwrangle</code> で <strong>wnoise</strong> を使う。空間に散らばった点のうち、一番近い点までの距離 f1 と、"
           "二番目に近い点までの距離 f2 が返る。<strong>f2 − f1</strong> は、2つの点のちょうど中間（＝板と板の境目）で 0 になる。"
           "これが 0.07 より小さい所を割れ目とし、<strong>heat</strong>（割れ目の真ん中で 1）を付ける。"
           "板の上は 6 cm 持ち上げ、ノイズで細かいでこぼこも付ける。plate_size = 2.2 で、板1枚は数十 cm。",
           cap="亀の甲羅のように割れた地面。", shading="smooth", ui_parm="crack_width",
           bbox=hou.BoundingBox(-2, -0.2, -1.5, 2, 0.2, 1.5))

    tint = g.node("attribwrangle", "hot_colors", [crust], snippet=(
        "// 割れ目の色。熱い所ほど黄色く、冷めた所ほど暗い赤。板は黒い岩\n"
        "vector hot = lerp({0.35, 0.02, 0.0}, {1.0, 0.55, 0.08}, pow(f@heat, 2));\n"
        "vector rock = {0.03, 0.028, 0.026} * fit(noise(@P * 12), 0.3, 0.7, 0.6, 1.4);\n"
        "v@Cd = f@heat > 0.02 ? hot * f@heat : rock;\n"
        "i@group_lava = f@heat > 0.02;"))
    g.step(tint, "熱さで色を分ける",
           "もう1つの <code>attribwrangle</code> で色 Cd を決める。heat が 0.02 より大きい点（割れ目）は、heat が大きいほど "
           "暗い赤 → 黄色に、さらに heat を掛けて縁ほど暗くする。板の点はノイズで濃淡を付けた黒い岩の色。"
           "割れ目の点は <strong>lava</strong> というグループにまとめておく（光る材質を当てる所）。",
           cap="割れ目が赤く、真ん中ほど黄色い。", shading="smooth",
           bbox=hou.BoundingBox(-2, -0.2, -1.5, 2, 0.2, 1.5))

    faces = g.node("attribwrangle", "lava_faces", [tint], snippet=(
        "// 面のグループにする。面の角の点が全部熱い（heat 0.15 より上）ときだけ lava\n"
        "// どれか1つで決めると、板の縁の斜面まで光り、網の升目どおりのギザギザが出た\n"
        "int hot = 1;\n"
        "foreach (int p; primpoints(0, @primnum)) hot &= point(0, 'heat', p) > 0.15;\n"
        "i@group_lava = hot;"))
    faces.parm("class").set(1)
    glow = g.mat("lava_mat", basecolor=(0, 0, 0), rough=0.6, emitint=3.0, emitcolor=(1, 1, 1))
    glow.parm("emitcolor_usePointColor").set(1)
    rock = g.mat("crust_mat", basecolor=(1, 1, 1), rough=0.85, reflect=0.3)
    painted = g.assign(g.assign(faces, rock, "assign_rock"), glow, "assign_lava", group="lava")
    g.step(painted, "割れ目だけを光らせる",
           "材質は面に当てるので、Run Over を Primitives にした <code>attribwrangle</code> で、<strong>角の点が全部熱い</strong>"
           "（heat 0.15 より上）面を <strong>lava</strong> という面のグループにする。そのうえで材質を2つ当てる。まず全体に岩の材質"
           "（Base Color 白＝点の色 Cd を使う、Roughness 0.85）。次の <code>material</code> で Group を <strong>lava</strong> にして、"
           "光る材質（Base Color 黒・<strong>Emission Intensity 3</strong>・Emission Color の <strong>Use Point Color</strong>）を上書きする。"
           "割れ目は Cd の色そのままで光る。",
           cap="材質を当てた状態（ビューポートでは光らない）。", shot=False)
    g.hero(painted, "Karma で撮った仕上がり。黒い殻の割れ目から、熱い溶岩が光る。", direction=(0.3, 0.75, 1.0),
           key=0.4, rim=1.5, dome=0.05, dome_color=(0.4, 0.45, 0.6), spp=64, margin=0.62, floor=False,
           bbox=hou.BoundingBox(-1.6, -0.1, -1.2, 1.6, 0.1, 1.2))

    # ---- 落とし穴を測る ----
    geo = tint.geometry()
    heat = geo.pointFloatAttribValues("heat")
    share = sum(1 for h in heat if h > 0.02) / len(heat)
    crust.parm("crack_width").set(0.24)
    share2 = sum(1 for h in tint.geometry().pointFloatAttribValues("heat") if h > 0.02) / len(heat)
    crust.parm("crack_width").set(0.07)
    ground.parm("rows").set(75)
    ground.parm("cols").set(100)
    share_coarse = sum(1 for h in tint.geometry().pointFloatAttribValues("heat") if h > 0.02) / (76 * 101)
    ground.parm("rows").set(300)
    ground.parm("cols").set(400)
    traps = [
        {"title": "crack_width で割れ目の太さが決まる",
         "body": f"crack_width 0.07 で、光る点は全体の {share:.0%}。0.24 にすると {share2:.0%}。"
                 "割れ目が太いと、黒い殻より溶岩のほうが多くなり、固まりかけた溶岩に見えなくなる。",
         "img": "", "cap": ""},
        {"title": "網の細かさでは、割れ目の量は変わらない",
         "body": f"升 4 cm（Rows 75・Columns 100）にしても、光る点の割合は {share_coarse:.0%}（升 1 cm では {share:.0%}）。"
                 "割れ目の量を決めるのは crack_width と plate_size で、網の細かさは割れ目の縁のなめらかさにだけ効く。"
                 "試すうちは粗い網で速く回し、撮る前に細かくする。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "8個（材質2つ）"], ["光る点の割合", f"{share:.0%}"]], traps=traps)


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
