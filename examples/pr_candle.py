# -*- coding: utf-8 -*-
"""実践「ろうそくの炎をともす」— しずく形の炎を、ボリュームに VEX で直接描き、@Time で少しだけ揺らす。

本物のろうそくの炎は、風が無ければほとんど形を変えない、上が細いしずく形。芯のすぐまわりは暗く、
外側ほど明るい黄色で、先は赤っぽくなって消える。流れの計算（Pyro のシミュレーション）を使わなくても、
「しずく形の濃さ」をボリュームに書き込むだけで作れる。

    hython examples/pr_candle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 48


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("candle", "ろうそくの炎をともす",
                  "ろうそくの炎は、風が無ければほとんど形の変わらない、しずく形の光。流れの計算をしなくても、"
                  "箱のボリュームに「しずく形の濃さ」を VEX で書き込み、炎用の材質で光らせれば作れる。@Time を使って、ほんの少し揺らす。",
                  tags=["エフェクト", "VEX", "ボリューム", "炎", "Karma"])
    g.shot_dir = (0.2, 0.2, 1.0)
    wax = g.node("tube", "candle", type="poly", rad=(0.022, 0.022), height=0.12, cols=48, cap=1, t=(0, 0.06, 0))
    wick = g.node("tube", "wick", type="poly", rad=(0.0012, 0.001), height=0.012, cols=8, cap=1, t=(0, 0.126, 0))
    body = g.node("merge", "candle_and_wick", [wax, wick])
    g.step(body, "ろうそくと芯を作る",
           "<code>tube</code> で半径 2.2 cm・高さ 12 cm のろうそくを作り、上に細い <code>tube</code>（高さ 1.2 cm）の芯を立てる。",
           cap="ろうそくと芯。", shading="smooth", bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.2, 0.04))

    box = g.node("volume", "flame_box", sizex=0.03, sizey=0.07, sizez=0.03, tx=0, ty=0.165, tz=0,
                 uniformsamples=4, samplediv=90)
    box.parm("name").set("flame")   # Guide.node の引数 name（ノード名）とぶつかるので別に入れる
    shape = g.node("volumewrangle", "teardrop", [box], snippet=(
        "// しずく形の炎。根元（芯の先）から上へ 0〜1 の高さ y を取り、y ごとの太さ r(y) の中を光らせる\n"
        "vector base = set(0, 0.127, 0);   // 芯の先（0.132）より少し下から始めて、芯を炎で包む\n"
        "float H = chf('height');\n"
        "vector p = @P - base;\n"
        "float y = p.y / H;\n"
        "// 上ほど少しだけ横に揺れる（@Time で動く）\n"
        "float sway = (noise(@Time * 2.5) - 0.5) * chf('flicker') * y * y;\n"
        "p.x -= sway;\n"
        "float r = chf('width') * pow(sin(PI * clamp(y, 0, 1) * 0.92), 1.1) * pow(1 - clamp(y, 0, 1), 0.35);\n"
        "float d = length(set(p.x, p.z)) / max(r, 1e-5);\n"
        "// smooth(小, 大, x) は x が小→大で 0→1。逆向きにしたいときは 1 − smooth(…) と書く\n"
        "float shell = 1 - smooth(0.55, 1.0, d);                              // 内側ほど光り、外でなめらかに消える\n"
        "float dark_core = 1 - 0.6 * (1 - smooth(0.0, 0.5, d)) * (1 - smooth(0.0, 0.45, y));   // 芯のまわりの下だけ暗い\n"
        "f@flame = (y > 0 && y < 1) ? shell * dark_core * (1 - smooth(0.7, 1.0, y)) : 0;"))
    kit_spare(shape, height=0.045, width=0.0075, flicker=0.004)
    hou.setFrame(24)
    g.step(shape, "しずく形の濃さを書き込む",
           "<code>volume</code> で名前 <strong>flame</strong> の小さな箱（3 × 7 × 3 cm）を芯の上に置く（升は約 0.8 mm）。"
           "<code>volumewrangle</code> で、芯の先からの高さを 0〜1 の y にし、y ごとの太さ r を "
           "<strong>sin</strong>（根元から太り、上で細る）で決める。中心からの距離が r より内側の升を光らせ、"
           "芯のまわりの下のほうだけ少し暗くする（本物の炎の暗い芯）。上のほうほど、<strong>@Time</strong> で動くノイズで横に揺らす（flicker = 4 mm）。",
           cap="しずく形の炎（ビューポートでは煙のように見える）。", shading="smooth", ui_parm="width",
           bbox=hou.BoundingBox(-0.03, 0.1, -0.03, 0.03, 0.2, 0.03))

    fire = g.mat("flame_mat", kind="kma_pyroshader")
    fire.parm("enablefire").set(1)
    fire.parm("fireintscale").set(float(os.environ.get("FIRE", "150")))
    fire.parm("densityscale").set(0.0)
    fire.parm("fireint_volumename").set("flame")
    fire.parm("firecolor_volumename").set("flame")
    fire.parm("firecolormode").set("0")
    fire.parm("firecolorramp").set(hou.Ramp((hou.rampBasis.Linear,) * 4, (0.0, 0.25, 0.6, 1.0),
                                            ((0, 0, 0), (0.55, 0.12, 0.02), (1.0, 0.55, 0.12), (1.0, 0.9, 0.6))))
    wax_mat = g.mat("wax_mat", basecolor=(0.92, 0.86, 0.74), rough=0.45, sheen=0.2)
    black = g.mat("wick_mat", basecolor=(0.02, 0.02, 0.02), rough=0.9)
    glow = hou.node("/obj").createNode("hlight::2.0", "candle_light")
    glow.parm("light_type").set("point")
    glow.parmTuple("t").set((0, 0.16, 0))
    glow.parm("light_intensity").set(0.01)
    glow.parmTuple("light_color").set((1.0, 0.62, 0.3))
    final = g.node("merge", "candle_lit", [g.assign(wax, wax_mat, "assign_wax"), g.assign(wick, black, "assign_wick"),
                                           g.assign(shape, fire, "assign_flame")])
    g.step(final, "炎の材質と、ろうそくの明かり",
           "<code>/mat</code> に <code>kma_pyroshader</code>（Karma の炎用の材質）を作り、<strong>Enable Fire</strong> を入れる。"
           "<strong>Intensity Volume と Color Volume を flame</strong> にし、Fire Color Ramp を 黒 → 赤 → 橙 → 黄白 にする。"
           "炎がとても小さく薄いので、<strong>Intensity Scale は 150</strong> まで上げる。"
           "煙は出さないので Density Scale は 0。ボリュームの光だけでは周りがほとんど照らされないので、炎の位置に弱い橙色の "
           "<code>hlight</code>（Point、Intensity 0.01）を置く。強くするとろうそくの頭が白く飛ぶ。ろうは生成りの白、Sheen 0.2。",
           cap="材質と明かりを当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。暗い部屋でともる、しずく形の炎。", direction=(0.15, 0.12, 1.0), frame=24,
           key=0.25, rim=0.25, dome=0.004, spp=96, margin=1.25, backdrop=(0.05, 0.045, 0.04), backdrop_reflect=0.1,
           bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.2, 0.04))
    g.anim(shape, (1, LAST), "炎の先が、ゆっくり左右に揺れる（48 フレーム＝2 秒）。",
           bbox=hou.BoundingBox(-0.03, 0.1, -0.03, 0.03, 0.2, 0.03), direction=(0.2, 0.15, 1.0))

    # ---- 落とし穴を測る ----
    import time
    geo = shape.geometry()
    vol = geo.prims()[0]
    res = vol.resolution()
    lit = sum(1 for v in vol.allVoxels() if v > 0.05)
    traps = [
        {"title": "小さな炎は、Intensity Scale を大きく上げる",
         "body": "kma_pyroshader の Intensity Scale を焚き火と同じくらい（2）にすると、Karma では薄い灰色のもやにしか写らなかった。"
                 "20 でうっすら光り、150 でろうそくの炎らしい明るさになった。数 mm しか厚みのない炎には、焚き火よりずっと大きな値が要った。",
         "img": "", "cap": ""},
        {"title": "箱が小さすぎると、炎の先が切れる",
         "body": f"箱の高さは 7 cm、炎の高さ height は 4.5 cm。升の数は {res[0]}×{res[1]}×{res[2]} で、光っている升は {lit:,} 個。"
                 "炎を長くするときは、箱も同じだけ高くする。箱の外には何も書き込めない。",
         "img": "", "cap": ""},
        {"title": "形の計算だけなので、すぐ出る",
         "body": "流れの計算（Pyro のシミュレーション）を使っていないので、どのフレームでも前のフレームを待たずに形が決まる。"
                 "風で大きくあおられる炎や、煙を出す炎は、Pyro で計算する（実践「焚き火を燃やす」）。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "8個（材質3つ・明かり1つ）"], ["升の数", f"{res[0]}×{res[1]}×{res[2]}"]], traps=traps)


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
