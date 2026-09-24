# -*- coding: utf-8 -*-
"""実践「桜の花びらが舞い散る」— 花びらを上から少しずつ生み、空気抵抗でゆっくり落とし、くるくる回しながら横へ流す。

本物の花びらは軽くて薄いので、すぐに空気抵抗で遅くなり、ひらひら回りながら、風に流されて斜めに落ちる。
POP（粒のシミュレーション）で粒を落とし、粒ごとに回転（orient）を少しずつ進め、花びらの形をコピーする。

    hython examples/pr_petals.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 120
HERO_F = 110


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("petals", "桜の花びらが舞い散る",
                  "上の広い範囲から花びらの粒を少しずつ生み、重力・空気抵抗・横風で、ゆっくり斜めに落とす。"
                  "popwrangle で粒ごとの向き orient を毎ステップ少しずつ回すと、ひらひら回って見える。最後に花びらの形を粒にコピーする。",
                  tags=["シミュレーション", "POP", "パーティクル", "Karma"])
    g.shot_dir = (0.3, 0.3, 1.0)
    blade = g.node("grid", "petal_blank", orient="zx", size=(1, 1), rows=6, cols=10)
    petal = g.node("attribwrangle", "petal_shape", [blade], snippet=(
        "// 桜の花びら：丸い形で、先に小さな切れ込み。少し反らす\n"
        "float u = @P.x + 0.5;                 // 付け根 0 → 先 1\n"
        "float side = @P.z * 2;                // −1〜1（横方向）\n"
        "float w = sqrt(sin(PI * pow(u, 0.55)));   // 付け根だけ細く、先まで丸くふくらむ\n"
        "@P.z = side * w * chf('width') * 0.5;\n"
        "@P.x = u * chf('length');\n"
        "// 先の真ん中に小さな V 字の切れ込み（桜の花びらの目印）\n"
        "if (u > 0.8) @P.x -= (1 - abs(side)) * (u - 0.8) / 0.2 * chf('length') * 0.14;\n"
        "@P.y = 0.12 * chf('length') * side * side + 0.12 * chf('length') * u * u;   // 横に少し丸まり、先が反る\n"
        "v@Cd = lerp({0.96, 0.68, 0.78}, {1.0, 0.93, 0.95}, smooth(0, 0.6, u));   // 付け根がほんのり桃色、ほとんど白"))
    kit_spare(petal, width=0.016, length=0.022)
    g.step(petal, "花びらを1枚作る",
           "<code>grid</code> を <code>attribwrangle</code> で花びらにする。本物の桜（ソメイヨシノ）の花びらは長さ約 2 cm、丸く、先の真ん中に小さな切れ込みがある。"
           "付け根から先への位置 u で幅を <strong>√sin</strong> の形（付け根だけ細く、先まで丸い）にし、先の真ん中を V 字にへこませ、横に少し丸めて先を反らせる。"
           "長さ 2.2 cm・幅 1.6 cm。色はほとんど白で、付け根だけほんのり桃色（写真の桜の花びらは、思ったよりずっと白い）。",
           cap="桜の花びら1枚（拡大）。", shading="smoothwire",
           bbox=hou.BoundingBox(-0.004, -0.008, -0.022, 0.034, 0.012, 0.022))

    canopy = g.node("grid", "blossom_area", size=(1.4, 0.8), rows=2, cols=2, t=(-0.3, 1.8, 0))
    dop = g.node("dopnet", "fall")
    obj = dop.createNode("popobject", "petals")
    src = dop.createNode("popsource", "from_branches")
    src.parm("soppath").set(canopy.path())
    src.parm("emittype").set("surface")
    src.parm("constantrate").set(420)
    src.parm("life").set(8)
    src.parm("initvel").set("set")
    for axis, v, s in zip("xyz", (0.3, -0.2, 0.0), (0.3, 0.2, 0.3)):
        src.parm(f"vel{axis}").set(v)
        src.parm(f"var{axis}").set(s)
    grav = dop.createNode("popforce", "gravity")
    grav.parmTuple("force").set((0, -9.81, 0))
    drag = dop.createNode("popdrag", "air")
    drag.setFirstInput(grav)
    drag.parm("airresist").set(6.0)
    drag.parmTuple("windvelocity").set((0.5, 0, 0.1))
    spin = dop.createNode("popwrangle", "flutter")
    spin.setFirstInput(drag)
    spin.parm("snippet").set(
        "// 粒ごとに回る軸と速さを決め（はじめの1回だけ）、毎ステップその分だけ向きを回す\n"
        "if (length(v@spin) == 0) v@spin = (set(rand(@id), rand(@id + 1), rand(@id + 2)) - 0.5) * 16;\n"
        "if (length(p@orient) == 0) p@orient = quaternion(radians(set(rand(@id + 3), rand(@id + 4), rand(@id + 5)) * 360), 0);\n"
        "p@orient = qmultiply(p@orient, quaternion(v@spin * @TimeInc));\n"
        "// ひらひら：向きに合わせて、横へ少し揺れる\n"
        "v@v += set(sin(@Time * 5 + @id), 0, cos(@Time * 4 + @id)) * 0.02;")
    solver = dop.createNode("popsolver", "solver")
    solver.setInput(0, obj)
    solver.setInput(1, spin)
    solver.setInput(2, src)
    solver.setDisplayFlag(True)
    dop.layoutChildren()
    parts = g.node("dopimport", "in_air", doppath=dop.path(), objpattern="*")
    t0 = time.perf_counter()
    for f in range(1, LAST + 1):
        hou.setFrame(f)
        parts.geometry()
    sim_sec = time.perf_counter() - t0
    hou.setFrame(HERO_F)
    n_now = len(parts.geometry().points())
    g.step(parts, "粒を生んで、ゆっくり落とす",
           "高さ 1.8 m に板（1.4 × 0.8 m）を置き、<code>dopnet</code> の中の <code>popsource</code> で、その面から "
           "<strong>1 秒に 420 個</strong>の粒を生む（Emission Type は Surface）。はじめの速さは横 0.3・下 0.2 m/秒に、ばらつきを付ける。"
           "<code>popforce</code> で重力、<code>popdrag</code> で <strong>Air Resistance 6</strong>（とても強い空気抵抗＝軽い花びら）と、"
           "風 (0.5, 0, 0.1) m/秒。<code>popwrangle</code> で粒ごとに回る軸と速さ spin を決め、毎ステップ orient を "
           "<code>qmultiply</code> で少しずつ回す。外の <code>dopimport</code> で取り出す。"
           f"フレーム {HERO_F} で {n_now} 枚が舞っている。{LAST} フレームの計算は {sim_sec:.1f} 秒。",
           cap=f"フレーム {HERO_F}。斜めに流れて落ちる粒。", shading="wire", ui_parm="airresist",
           bbox=hou.BoundingBox(-1.6, 0, -1.0, 1.8, 2.5, 0.5))

    copies = g.node("copytopoints::2.0", "petal_copies", [petal, parts])
    sakura = g.mat("petal_mat", basecolor=(1, 1, 1), rough=0.5, sheen=0.4)
    final = g.assign(copies, sakura, "assign_petal")
    g.step(final, "花びらをコピーして、材質を当てる",
           "<code>copytopoints</code> で花びらを粒にコピーする。粒の orient がそのまま花びらの向きになり、1枚ずつ違う向きで回る。"
           "花びらは Base Color を白にして Cd を使い、Sheen 0.4 で薄い花びらのやわらかさを出す。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {HERO_F}）。風に流されて舞い散る桜の花びら。", frame=HERO_F,
           direction=(0.25, 0.15, 1.0), key=1.0, rim=2.0, dome=0.3, dome_color=(0.9, 0.93, 1.0), spp=24, margin=1.0, denoise=True,
           backdrop=(0.1, 0.17, 0.3), backdrop_reflect=0.0, bbox=hou.BoundingBox(-0.25, 0.85, -0.15, 0.35, 1.2, 0.15))
    g.anim(final, (1, LAST), "花びらがひらひら回りながら、斜めに流れて落ちる（120 フレーム＝5 秒）。",
           bbox=hou.BoundingBox(-1.6, 0, -1.0, 1.8, 2.5, 0.5), direction=(0.3, 0.3, 1.0))

    # ---- 落とし穴を測る ----
    def mean_fall_speed():
        vs = [p.attribValue("v")[1] for p in parts.geometry().points()]
        return sum(vs) / len(vs)

    hou.setFrame(HERO_F)
    slow = mean_fall_speed()
    drag.parm("airresist").set(0.5)
    for f in range(1, HERO_F + 1):
        hou.setFrame(f)
        parts.geometry()
    fast = mean_fall_speed()
    drag.parm("airresist").set(6.0)
    for f in range(1, LAST + 1):
        hou.setFrame(f)
        parts.geometry()
    traps = [
        {"title": "空気抵抗が弱いと、石のように落ちる",
         "body": f"Air Resistance 6 では、フレーム {HERO_F} で舞っている粒の落ちる速さは平均 {-slow:.2f} m/秒。"
                 f"0.5 にすると {-fast:.2f} m/秒。花びらのように軽い物は、空気抵抗をとても強くする。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "14個（dopnet の中に6個・材質2つ）"], [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps)


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
