# -*- coding: utf-8 -*-
"""実践「文字を落として割る」— 厚みのある文字をコンクリートのように割り、高い所から床へ落として砕く。

本物のもろい物（石膏・コンクリート）は、床に当たった所から割れ、角のかけらが飛び、大きな塊は形を残して転がる。
rbdmaterialfracture で先に割っておき、かけらどうしを弱い「つながり」でくっつけて落とすと、当たった勢いでつながりが切れて砕ける。

    hython examples/pr_letters.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 60
WORD = "HOUDINI"


def run(solver, last):
    import hou
    t0 = time.perf_counter()
    for f in range(1, last + 1):
        hou.setFrame(f)
        solver.geometry()
    return time.perf_counter() - t0


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("letters", "文字を落として割る",
                  "font で文字を作って押し出し、厚みのある文字にする。rbdmaterialfracture で割っておき、"
                  "かけらどうしを弱くくっつけて床へ落とすと、当たった所から砕ける。文字ごとに色を変えておくと、どのかけらがどの文字か分かる。",
                  tags=["シミュレーション", "RBD", "破壊", "Karma"])
    g.shot_dir = (0.4, 0.45, 1.2)
    text = g.node("font", "word", text=WORD, fontsize=0.5, halign=1, valign=0)
    solid = g.node("polyextrude::2.0", "thick", [text], dist=0.12, outputback=1)
    paint = g.node("attribwrangle", "letter_colors", [solid], snippet=(
        "// 文字ごとに色を変える。左から右へ、色相を少しずつ回す\n"
        "vector c = getbbox_center(0);\n"
        "vector s = getbbox_size(0);\n"
        "float u = (@P.x - (c.x - s.x / 2)) / s.x;\n"
        "v@Cd = hsvtorgb(set(floor(u * 7) / 7.0, 0.55, 0.85));"))
    paint.parm("class").set(1)
    g.step(paint, "文字を作って、厚みを付ける",
           f"<code>font</code> で「{WORD}」と書き、Font Size 0.5、中央そろえにする。<code>polyextrude</code> で "
           "<strong>Distance 0.12</strong> 押し出し、<strong>Output Back</strong> を入れて裏も閉じる（中の詰まった文字になる）。"
           "<code>attribwrangle</code>（Primitives）で、左から右へ色相を回して、文字ごとに色を変える。",
           cap="厚みのある7文字。", shading="smooth")

    frac = g.node("rbdmaterialfracture", "crack", [paint], materialtype="concrete")
    pieces = len(set(frac.geometry().primStringAttribValues("name")))
    glue = g.node("attribwrangle", "weak_glue", snippet="f@strength = chf('strength');   // かけらどうしのつながりの強さ")
    glue.setInput(0, frac, 1)
    glue.parm("class").set(1)
    kit_spare(glue, strength=float(os.environ.get("GLUE", "4")))
    g.step(frac, "コンクリートのように割っておく",
           "<code>rbdmaterialfracture</code> の Material Type を <strong>Concrete</strong> にする。文字の中に点が散らばり、"
           f"ごつごつした {pieces} 個のかけらに割れる。右の出口のつながり（Glue）には <code>attribwrangle</code>（Primitives）をつなぎ、"
           "<strong>strength</strong> を 4 に弱めておく。強いままだと、落ちても割れずに文字の形のまま転がる。",
           cap=f"{pieces} 個のかけら（見た目はまだ1つ）。", shading="wire", ui_parm="materialtype")

    lift = g.node("xform", "hold_up", [frac], t=(0, 1.3, 0), r=(-25, 0, 8))
    solver = g.node("rbdbulletsolver", "drop", [lift], useground=1, startframe=1)
    solver.setInput(1, glue)
    solver.parm("margin").set(0.002)
    sim_sec = run(solver, LAST)
    geo = solver.geometry()
    names = geo.primStringAttribValues("name")
    moved_apart = len(set(names))
    g.step(solver, "床へ落とす",
           "<code>xform</code> で文字を 1.3 m 持ち上げ、少し傾ける。<code>rbdbulletsolver</code> の左にかけら、真ん中に弱めたつながりをつなぎ、"
           "Ground Plane を入れる。<strong>Collision Margin は 0.002</strong>（小さなかけらが浮かないように）。"
           f"再生すると、斜めに落ちた文字の、先に当たった角から砕ける。{LAST} フレームの計算は {sim_sec:.1f} 秒。",
           cap=f"フレーム {LAST}。砕けて散らばった文字。", shading="smooth", ui_parm="margin",
           bbox=hou.BoundingBox(-1.8, 0, -1.0, 1.8, 1.0, 1.0))

    stone = g.mat("letter_mat", basecolor=(1, 1, 1), rough=0.55, reflect=0.4)
    final = g.assign(solver, stone, "assign_letters")
    g.step(final, "材質を当てる",
           "<code>principledshader</code> の Base Color を白にして、面の色 Cd（文字ごとの色）を使う。割れた断面も同じ色になる。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {LAST}）。床に落ちて砕けた文字。", frame=LAST,
           direction=(0.35, 0.5, 1.2), key=3.0, rim=5.0, dome=0.4, spp=64, margin=1.05, backdrop=(0.2, 0.2, 0.21),
           bbox=hou.BoundingBox(-1.6, 0, -0.8, 1.6, 0.4, 0.8))
    g.anim(final, (1, LAST), "文字が落ちて、床に当たって砕けるまで（60 フレーム）。",
           bbox=hou.BoundingBox(-1.8, 0, -1.0, 1.8, 1.7, 1.0), direction=(0.4, 0.4, 1.2))

    # ---- 落とし穴を測る ----
    def spread():
        pts = {}
        for pr in solver.geometry().prims():
            pts.setdefault(pr.attribValue("name"), pr.vertices()[0].point().position())
        xs = [p[0] for p in pts.values()]
        zs = [p[2] for p in pts.values()]
        return max(xs) - min(xs), max(zs) - min(zs)

    w_weak = spread()
    glue.parm("strength").set(1000)
    run(solver, LAST)
    w_strong = spread()
    glue.parm("strength").set(4)
    run(solver, LAST)
    traps = [
        {"title": "つながりが強いと、割れずに転がる",
         "body": f"strength 4 では、止まったかけらの散らばりは 横 {w_weak[0]:.2f} m・奥行き {w_weak[1]:.2f} m。"
                 f"1000 にすると 横 {w_strong[0]:.2f} m・奥行き {w_strong[1]:.2f} m。つながりが強いと、文字は形を保ったまま倒れるだけになる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "9個（材質1つ）"], ["かけら", f"{pieces}個"], [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]],
           traps=traps)


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
