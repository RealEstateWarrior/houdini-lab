# -*- coding: utf-8 -*-
"""実践「歯車をかみ合わせて回す」— 歯の数の違う歯車を作り、かみ合う位置に置いて、歯の数の比で回す速さを決める。

本物の歯車は、歯の大きさ（ピッチ）がそろっていれば、歯の数がいくつでもかみ合う。
かみ合った2つは逆向きに回り、回る速さは歯の数に反比例する（歯が2倍なら、回る速さは半分）。

    hython examples/pr_gears.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 96
MODULE = 0.01     # 歯の大きさ（モジュール）。直径 = モジュール × 歯の数


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("gears", "歯車をかみ合わせて回す",
                  "円の縁を歯の数だけ出っぱらせて歯車にする。歯の大きさ（モジュール）をそろえた歯車どうしは、中心の距離を"
                  "「2つの半径の和」にするとかみ合う。回す速さは歯の数の比で決まり、式で回すのでシミュレーションは要らない。",
                  tags=["モデリング", "VEX", "アニメーション", "Karma"])
    g.shot_dir = (0.3, 0.9, 1.0)
    blank = g.node("circle", "blank", type="poly", divs=720, orient=2, radx=1, rady=1)
    teeth = g.node("attribwrangle", "cut_teeth", [blank], snippet=(
        "// 縁の点を、角度に合わせて外へ出し入れして歯にする。歯の数 n、半径 = モジュール × n / 2\n"
        "int n = chi('teeth');\n"
        "float m = chf('module');\n"
        "float r = m * n / 2;\n"
        "float a = atan2(@P.z, @P.x);\n"
        "float wave = cos(a * n);                              // 歯1つで1回、山と谷\n"
        "float tooth = clamp(wave * 2.2, -1, 1);                // 山と谷を平らにして、台形の歯にする\n"
        "@P = normalize(@P) * (r + tooth * m * 1.0);"))
    kit_spare(teeth, ints={"teeth": 24}, module=MODULE)
    body = g.node("polyextrude::2.0", "gear_thickness", [teeth], dist=0.012, outputback=1)
    hole = g.node("tube", "axle", type="poly", rad=(0.012, 0.012), height=0.03, cols=24, cap=1)
    gear = g.node("merge", "gear_with_axle", [body, hole])
    g.step(gear, "歯車を1つ作る",
           "<code>circle</code>（720 分割）の縁の点を、<code>attribwrangle</code> で角度に合わせて外へ出し入れして歯にする。"
           f"<strong>cos(角度 × 歯の数)</strong> は歯1つぶんで1回、山と谷をくり返す。これを 2.2 倍して ±1 で切ると、山と谷が平らな台形の歯になる。"
           f"歯の大きさ <strong>module = {MODULE}</strong>（1 cm）のとき、半径は module × 歯の数 ÷ 2（24 枚なら 12 cm）。"
           "<code>polyextrude</code> で厚さ 1.2 cm にし、真ん中に軸の <code>tube</code> を通す。",
           cap="24 枚歯の歯車。", shading="smooth", ui_parm="teeth",
           bbox=hou.BoundingBox(-0.14, -0.02, -0.14, 0.14, 0.03, 0.14))

    specs = [(24, 0.0, 0.0), (12, None, None), (36, None, None)]
    r = [MODULE * n / 2 for n, _, _ in specs]
    pos = [(0.0, 0.0), (r[0] + r[1], 0.0)]
    ang = math.radians(-120)
    pos.append(((r[0] + r[2]) * math.cos(ang), (r[0] + r[2]) * math.sin(ang)))
    placed = []
    for i, (n, _, _) in enumerate(specs):
        copy = g.node("attribwrangle", f"teeth_{n}", [blank], snippet=teeth.parm("snippet").eval())
        kit_spare(copy, ints={"teeth": n}, module=MODULE)
        solid = g.node("polyextrude::2.0", f"thick_{n}", [copy], dist=0.012, outputback=1)
        axle = g.node("tube", f"axle_{n}", type="poly", rad=(0.012, 0.012), height=0.03, cols=24, cap=1)
        one = g.node("merge", f"gear_{n}", [solid, axle])
        # 回す速さは、歯の数の比。1つ目（24枚）を 1 秒に 45 度回し、かみ合う歯車は逆向きに 24 / n 倍で回す
        speed = 45.0 if i == 0 else -45.0 * 24 / n
        # かみ合わせ：接点で、24 枚の歯の「山」に、相手の歯の「谷」がくるように、はじめの角度を決める
        # （θ は 24 枚の歯車から見た相手の向き。相手の接点での角度は θ+180度）
        theta = math.degrees(math.atan2(pos[i][1], pos[i][0]))
        phase = 0 if i == 0 else -(theta + 180 - (24 * theta + 180) / n)
        spin = g.node("xform", f"spin_{n}", [one], t=(pos[i][0], 0, pos[i][1]))
        spin.parm("ry").setExpression(f"$T * {speed:.4f} + {phase:.4f}")
        placed.append(spin)
    train = g.node("merge", "gear_train", placed)
    g.step(train, "かみ合う位置に置き、歯の数の比で回す",
           "同じ作り方で、歯の数 24・12・36 の歯車を作る（歯の大きさはそろえる）。中心の距離を「2つの半径の和」にすると歯がかみ合う。"
           "<code>xform</code> の Rotate Y に式を入れて回す。24 枚を <strong>$T * 45</strong>（1 秒に 45度）にしたら、"
           "かみ合う歯車は <strong>逆向きに 24 ÷ 歯の数 倍</strong>（12 枚は −90度、36 枚は −30度）で回す。"
           "はじめの角度を半歯ぶんずらしておくと、歯が相手のすき間にはまる。",
           cap="3つの歯車。", shading="smooth", ui_parm="ry",
           bbox=hou.BoundingBox(-0.35, -0.02, -0.35, 0.22, 0.03, 0.14))

    steel = g.mat("gear_mat", basecolor=(0.72, 0.6, 0.38), metallic=1.0, rough=0.3)
    final = g.assign(train, steel, "assign_brass")
    g.step(final, "真ちゅうの材質",
           "<code>principledshader</code> で <strong>Metallic 1・Roughness 0.3</strong>、色を真ちゅうの黄色にする。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。歯の数の違う3つの真ちゅうの歯車。", frame=1,
           direction=(0.25, 0.8, 1.0), key=3.0, rim=6.0, dome=0.6, spp=48, margin=1.05, backdrop=(0.06, 0.07, 0.08),
           bbox=hou.BoundingBox(-0.36, -0.02, -0.36, 0.22, 0.03, 0.14))
    g.anim(final, (1, LAST), "3つの歯車がかみ合って回る（96 フレーム＝4 秒）。",
           bbox=hou.BoundingBox(-0.36, -0.02, -0.36, 0.22, 0.03, 0.14), direction=(0.2, 1.0, 0.6))

    # ---- 落とし穴を測る ----
    size = [2 * max(math.hypot(p.position()[0], p.position()[2]) for p in placed[k].inputs()[0].inputs()[0].inputs()[0].geometry().points())
            for k in range(3)]
    traps = [
        {"title": "直径は、歯の数に比例する",
         "body": f"歯 24・12・36 枚の歯車の、歯先までの直径は {size[0] * 100:.1f}・{size[1] * 100:.1f}・{size[2] * 100:.1f} cm。"
                 "歯の大きさ（module）をそろえると、直径は歯の数に比例する（歯先は module 1 つ分さらに外）。"
                 "だから、中心の距離は module × (歯の数1 + 歯の数2) ÷ 2 で決まる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "18個（材質1つ）"], ["歯の数", "24・12・36"]], traps=traps)


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
