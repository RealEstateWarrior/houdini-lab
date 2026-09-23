# -*- coding: utf-8 -*-
"""実践「窓ガラスを割る」— 球をぶつけて、当たった所から放射状にひびが走ったガラスを割る。

本物の割れたガラスは、当たった点から放射状のひびが伸び、その間を同心円のひびがつないで、
中心近くは細かく砕けて飛び、外側の大きな破片は枠に残る。rbdmaterialfracture の Glass がこの割れ方を作る。

    hython examples/pr_glass.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 48      # 2 秒
HERO_F = 9
HIT = (0.12, 0.9, 0.0)


def run(solver, last):
    import hou
    t0 = time.perf_counter()
    for f in range(1, last + 1):
        hou.setFrame(f)
        solver.geometry()
    return time.perf_counter() - t0


def centers(node):
    """破片ごとの位置（packed の点の位置）。"""
    geo = node.geometry()
    return {pr.attribValue("name"): pr.vertices()[0].point().position() for pr in geo.prims()}


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("glass", "窓ガラスを割る",
                  "板ガラスに球をぶつけて割る。rbdmaterialfracture を Glass にして当たる点を渡すと、そこから放射状と同心円のひびが入る。"
                  "枠に触れている破片だけ動かないようにしておくと、真ん中が砕けて飛び、外側の破片が枠に残る。",
                  tags=["シミュレーション", "RBD", "破壊", "Karma"])
    g.shot_dir = (0.7, 0.25, 1.2)
    pane = g.node("box", "pane", size=(1.0, 1.4, 0.008), t=(0, 0.75, 0))
    hit = g.node("add", "hit_point", points=1, usept0=1, pt0=HIT)
    g.step(g.node("merge", "preview_pane", [pane, hit]), "ガラス板と、当たる点を置く",
           "<code>box</code> で 1 × 1.4 m、厚さ 8 mm の板を立てる（窓1枚ぶん）。"
           f"<code>add</code> で点を1つだけ作り、球が当たる所（{HIT[0]}, {HIT[1]}, 0）に置く。ひびはこの点から広がる。",
           cap="立てたガラス板と、当たる点。", shading="smoothwire", ui_parm="pt0",
           bbox=hou.BoundingBox(-0.6, 0, -0.1, 0.6, 1.5, 0.1))
    frac = g.node("rbdmaterialfracture", "crack", [pane], materialtype="glass", glass_useinput=1)
    frac.setInput(3, hit)
    pieces0 = len(set(frac.geometry().primStringAttribValues("name")))
    g.step(frac, "ガラスの割れ方で割る",
           "<code>rbdmaterialfracture</code> の Material Type を <strong>Glass</strong> にし、4番目の入口（Impact Points）に当たる点をつなぐ。"
           "<strong>Use Input Points</strong> を入れると、その点を中心に <strong>放射状のひび</strong>（既定 20 本）と、それをつなぐ同心円のひびが入る。"
           f"破片は {pieces0} 個になった。右の出口には、破片どうしをくっつけておく「つながり」が出る。",
           cap=f"{pieces0} 個の破片。中心ほど細かい。", shading="wire", ui_parm="glass_radialcracknum",
           bbox=hou.BoundingBox(-0.6, 0, -0.1, 0.6, 1.5, 0.1))

    ball = g.node("sphere", "ball", type="polymesh", rad=(0.06, 0.06, 0.06), rows=16, cols=24, t=(HIT[0], HIT[1], 0.7))
    throw = g.node("attribwrangle", "throw", [ball], snippet=(
        "// 球に名前と速さを付ける。-z 向き（ガラスへ）に 14 m/秒\n"
        "s@name = 'ball';\n"
        "v@v = {0, 0, -14};"))
    both = g.node("merge", "glass_and_ball", [frac, throw])
    pack = g.node("pack", "one_per_piece", [both], packbyname=1, transfer_attributes="name v")
    held = g.node("attribwrangle", "hold_edges", [pack], snippet=(
        "// 破片ごとの外枠（bounds = xmin, xmax, ymin, ymax, zmin, zmax）。枠（板の縁から 3 cm）に触れる破片は動かさない\n"
        "float b[] = primintrinsic(0, 'bounds', @ptnum);\n"
        "int on_frame = b[0] < -0.47 || b[1] > 0.47 || b[2] < 0.08 || b[3] > 1.42;\n"
        "string piece = prim(0, 'name', @ptnum);   // 塊1つにつき点が1つ。名前は面（塊）のほうに付いている\n"
        "i@active = piece == 'ball' ? 1 : !on_frame;"))
    n_held = sum(1 for p in held.geometry().points() if p.attribValue("active") == 0)
    g.step(held, "球を用意し、枠に触れる破片を止める",
           "<code>sphere</code>（半径 6 cm）を当たる点の 70 cm 手前に置き、<code>attribwrangle</code> で名前 <strong>ball</strong> と速さ "
           "<strong>v = (0, 0, −14)</strong>（ガラスへ向かって秒速 14 m）を付ける。<code>merge</code> でガラスとまとめ、"
           "<code>pack</code> の <strong>Pack By Name</strong> を入れて、同じ name の面を1つの塊（破片1つ）にまとめる。"
           f"最後の <code>attribwrangle</code> で、塊の外枠が板の縁から 3 cm 以内に入るものを <strong>active = 0</strong>（動かない）にする。{n_held} 個が止まった。",
           cap="見た目は同じ。縁の破片が「動かない」印を持った。", shading="wire", ui_parm="snippet",
           bbox=hou.BoundingBox(-0.6, 0, -0.1, 0.6, 1.5, 0.8))

    glue = g.node("attribwrangle", "weak_glue", [frac], snippet=(
        "// 破片どうしをくっつける力。既定のままだと強すぎて、球が跳ね返るだけで割れない\n"
        "f@strength = chf('strength');"))
    glue.setInput(0, frac, 1)
    glue.parm("class").set(1)
    kit_spare(glue, strength=float(os.environ.get("GLUE", "0.8")))
    solver = g.node("rbdbulletsolver", "shatter", [held], useground=1, startframe=1)
    solver.setInput(1, glue)
    sim_sec = run(solver, LAST)
    if os.environ.get("TEST"):
        hou.setFrame(1)
        a = centers(solver)
        hou.setFrame(LAST)
        b = centers(solver)
        print("GLUE", glue.parm("strength").eval(), "moved", sum(1 for k in a if k != "ball" and (a[k] - b[k]).length() > 0.05),
              "of", len(a) - 1, "ball z", b["ball"][2])
        return
    hou.setFrame(1)
    c1 = centers(solver)
    hou.setFrame(LAST)
    c2 = centers(solver)
    flew = sum(1 for k in c1 if k != "ball" and (c1[k] - c2[k]).length() > 0.05)
    g.step(solver, "ぶつけて割る",
           "rbdmaterialfracture の右の出口（つながり）に <code>attribwrangle</code> をつなぎ、Run Over を Primitives にして "
           "<strong>strength を 0.8</strong> に下げる。既定のままだと強すぎて、球が跳ね返るだけで1枚も割れなかった。"
           "<code>rbdbulletsolver</code> の左に塊、<strong>真ん中に弱めたつながり</strong>をつなぎ、Ground Plane を入れる。"
           "球が当たると、そのまわりのつながりが切れて破片が飛び、遠くの破片はつながったまま枠に残る。"
           f"{LAST} フレームで、{len(c1) - 1} 個のうち {flew} 個が動いた。",
           cap=f"フレーム {HERO_F}。当たった所から砕けて飛び散る。", shading="smoothwire", ui_parm="useground",
           bbox=hou.BoundingBox(-0.6, 0, -0.9, 0.6, 1.5, 0.8))

    frame = []
    for i, (size, t) in enumerate([((1.12, 0.06, 0.06), (0, 0.02, 0)), ((1.12, 0.06, 0.06), (0, 1.48, 0)),
                                   ((0.06, 1.52, 0.06), (-0.53, 0.75, 0)), ((0.06, 1.52, 0.06), (0.53, 0.75, 0))]):
        frame.append(g.node("box", f"frame{i}", size=size, t=t))
    wood = g.node("merge", "window_frame", frame)
    glass_mat = g.mat("glass_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.52, transparency=1.0,
                      transcolor=(0.85, 0.95, 0.92), transdist=0.3)
    wood_mat = g.mat("frame_mat", basecolor=(0.25, 0.14, 0.07), rough=0.5)
    unpack = g.node("unpack", "shards", [solver])
    steel = g.mat("steel_mat", basecolor=(0.6, 0.6, 0.62), metallic=1.0, rough=0.25)
    shards = g.assign(g.assign(unpack, glass_mat, "assign_glass"), steel, "assign_ball", group="@name=ball")
    final = g.node("merge", "window", [shards, g.assign(wood, wood_mat, "assign_frame")])
    g.step(final, "枠を付けて、ガラスの材質を当てる",
           "細い <code>box</code> 4本で木の窓枠を作る。ガラスは <code>principledshader</code> で <strong>Transparency 1・IOR 1.52</strong>（板ガラス）、"
           "Roughness 0。Transmission Color を少し青緑に、Transmission Distance 0.3 にすると、破片の厚い縁がうっすら緑に見える（本物の板ガラスの色）。"
           "<code>unpack</code> で塊を元の面に戻してから材質を当て、もう1つの <code>material</code> で Group を <strong>@name=ball</strong> にして、球だけ鉄にする。",
           cap="材質を当てた状態（ビューポートでは透けない）。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {HERO_F}）。当たった所から放射状に砕けた破片が飛ぶ。",
           direction=(0.55, 0.2, 1.2), key=3.0, rim=9.0, dome=0.5, spp=96, margin=1.02, frame=HERO_F,
           backdrop=(0.05, 0.055, 0.065), bbox=hou.BoundingBox(-0.62, 0, -0.5, 0.62, 1.52, 0.4))
    g.anim(final, (1, LAST), "球が当たって、破片が飛び散り、床に落ちるまで（48 フレーム＝2 秒）。",
           bbox=hou.BoundingBox(-0.7, 0, -1.2, 0.7, 1.52, 0.8), direction=(0.9, 0.35, 1.0))

    # ---- 落とし穴を測る ----
    held.bypass(True)
    run(solver, LAST)
    hou.setFrame(1)
    a1 = centers(solver)
    hou.setFrame(LAST)
    a2 = centers(solver)
    all_moved = sum(1 for k in a1 if k != "ball" and (a1[k] - a2[k]).length() > 0.05)
    held.bypass(False)
    frac.parm("glass_radialcracknum").set(8)
    pieces8 = len(set(frac.geometry().primStringAttribValues("name")))
    frac.parm("glass_radialcracknum").set(20)
    run(solver, LAST)
    traps = [
        {"title": "枠で止めないと、板ごと倒れる",
         "body": f"hold_edges を外すと、{LAST} フレームで {len(a1) - 1} 個のうち {all_moved} 個が動いた。"
                 "ガラス板はただ床に立っているだけなので、つながったまま倒れる。縁の破片を active = 0 にして、枠にはまっている状態を作る。",
         "img": "", "cap": ""},
        {"title": "つなぐ力（strength）で、割れる広さが決まる",
         "body": f"strength 0.8 で {flew} 個が動いた。同じ場面で測ると、1.5 で 7 個、2.5 で 1 個、5 以上では 0 個（球が跳ね返るだけ）。"
                 "小さいほど広く割れる。",
         "img": "", "cap": ""},
        {"title": "放射状のひびの数で、破片の数が決まる",
         "body": f"Radial Crack Number 20（既定）で {pieces0} 個、8 にすると {pieces8} 個。放射状のひびの間を同心円のひびが切るので、"
                 "本数を減らすと大きな三角の破片になる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "18個（材質2つ）"], ["破片", f"{pieces0}個"],
                  [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps)


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
