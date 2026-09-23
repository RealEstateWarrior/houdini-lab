# -*- coding: utf-8 -*-
"""実践「花火を打ち上げる」— 菊（尾を引く星が丸く開く花火）を POP で1発作り、時間と場所をずらして3発にする。

本物の菊は、玉の中に並んだ星（火薬の粒）が一斉に外へ飛び、火の粉の尾を引きながら重力で垂れていく。
それを「球の表面に点を並べる → 外向きの速さを付ける → 重力と空気抵抗で飛ばす → 通った跡を線にする」で真似る。

    hython examples/pr_fireworks.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 60          # 2.5 秒
HERO_F = 22
TRAIL = 18         # 尾の長さ（フレーム数）


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("fireworks", "花火を打ち上げる",
                  "夜空で丸く開く「菊」の花火を作る。球の表面に並べた点を一斉に外へ飛ばし、重力と空気抵抗で垂れさせ、"
                  "通った跡を線にすると尾ができる。1発できたら、時間と場所をずらして3発に増やす。",
                  tags=["シミュレーション", "エフェクト", "POP", "パーティクル", "Karma"])
    g.shot_dir = (0.25, 0.08, 1.0)
    ball = g.node("sphere", "shell", type="poly", rad=(1, 1, 1), freq=6)
    stars = g.node("scatter::2.0", "stars", [ball], npts=320, relaxpoints=1)
    g.step(stars, "玉の中の「星」を並べる",
           "<code>sphere</code>（半径 1 m）の表面に、<code>scatter</code> で <strong>320 個</strong>の点をまく。"
           "1つ1つが、花火の玉に詰まった「星」（燃えながら飛ぶ火薬の粒）になる。"
           "<strong>Relax Iterations</strong> を入れておくと、点どうしが離れて、開いたときに穴や固まりができにくい。",
           cap="球の表面に並んだ 320 個の星。", shading="wire", ui_parm="npts",
           bbox=hou.BoundingBox(-1.3, -1.3, -1.3, 1.3, 1.3, 1.3))
    push = g.node("attribwrangle", "push_out", [stars], snippet=(
        "// 中心から外向きに飛ばす。速さは星ごとに少しだけ変える（全部同じだと、きれいすぎる球になる）\n"
        "float speed = chf('speed') * fit01(rand(@ptnum + 3), 0.88, 1.0);\n"
        "v@v = normalize(@P) * speed;\n"
        "@P *= 0.5;\n"
        "v@Cd = chv('color');"))
    kit_spare(push, speed=34.0, color=(1.0, 0.72, 0.32))
    g.step(push, "外向きの速さと色を付ける",
           "<code>attribwrangle</code> で、点ごとに <strong>v</strong>（速さと向き）を付ける。向きは球の中心から外、"
           "速さは <strong>speed = 34</strong>（m/秒）を星ごとに 88〜100% の範囲でばらつかせる。"
           "全部同じ速さだと、コンパスで描いたような不自然な球になる。色 <strong>Cd</strong> は金色（1, 0.72, 0.32）。",
           cap="見た目は同じ。点ごとに「外向きの速さ」が入った。", shading="wire", ui_parm="speed",
           bbox=hou.BoundingBox(-1.3, -1.3, -1.3, 1.3, 1.3, 1.3))

    dop = g.node("dopnet", "burst")
    obj = dop.createNode("popobject", "stars")
    src = dop.createNode("popsource", "all_at_once")
    src.parm("soppath").set(push.path())
    src.parm("emittype").set("allpoint")
    src.parm("constantactivate").set(False)
    # All Points では Impulse Count は使われず、Impulse Activation が 1 のフレームごとに全点が生まれる。
    # だから「1 フレーム目だけ 1」は Activation のほうに入れる
    src.parm("impulseactiveate").setExpression("$FF == 1")
    src.parm("initvel").set("use")
    src.parm("life").set(2.2)
    src.parm("lifevar").set(0.5)
    grav = dop.createNode("popforce", "gravity")
    grav.parmTuple("force").set((0.0, -9.81, 0.0))
    drag = dop.createNode("popdrag", "air")
    drag.setFirstInput(grav)
    drag.parm("airresist").set(0.45)
    solver = dop.createNode("popsolver", "solver")
    solver.setInput(0, obj)
    solver.setInput(1, drag)
    solver.setInput(2, src)
    solver.setDisplayFlag(True)
    dop.layoutChildren()
    imp = g.node("dopimport", "fly", doppath=dop.path(), objpattern="*")
    t0 = time.perf_counter()
    for f in range(1, LAST + 1):
        hou.setFrame(f)
        imp.geometry()
    sim_sec = time.perf_counter() - t0
    hou.setFrame(HERO_F)
    spread = imp.geometry().boundingBox().sizevec()
    print("星の数", len(imp.geometry().points()), "広がり", spread)
    g.step(imp, "重力と空気抵抗で飛ばす",
           "<code>dopnet</code> の中に POP を組む。<code>popsource</code> は Emission Type を <strong>All Points</strong>、"
           "<strong>Impulse Activation</strong> に式 <strong>$FF == 1</strong> を入れて、1 フレーム目だけ 320 個を一度に生む。"
           "Initial Velocity は <strong>Use Inherited Velocity</strong>（前の段で付けた v をそのまま使う）。"
           "寿命 <strong>Life Expectancy 2.2 秒・Life Variance 0.5</strong> で、消える時間をばらけさせる。"
           "<code>popforce</code> で下向き 9.81 の重力、<code>popdrag</code> の <strong>Air Resistance 0.45</strong> で空気抵抗を入れる。"
           f"空気抵抗があると最初だけ速く広がり、すぐ減速して垂れる。花火らしさはここで出る。0.9 秒後の広がりは約 {spread[0]:.0f} m。"
           "外の <code>dopimport</code> で結果を取り出す。",
           cap=f"フレーム {HERO_F}。開いて、垂れはじめた星。", shading="wire", ui_parm="airresist")

    tail = g.node("trail", "tail", [imp], result="poly", length=TRAIL, close=0)
    glow = g.node("attribwrangle", "hot_head", [tail], snippet=(
        "// 尾の先頭（いちばん新しい位置）ほど白く熱く、うしろほど赤く暗くする。\n"
        "// trail の線は、同じ星の数フレーム前の位置をつないだもの。age が小さいほど古い位置\n"
        "int prim = @primnum;\n"
        "int pts[] = primpoints(0, prim);\n"
        "float head = point(0, 'age', pts[-1]);\n"
        "foreach (int p; pts) head = max(head, point(0, 'age', p));\n"
        "float lag = clamp((head - f@age) / chf('trail_sec'), 0, 1);     // 0 = 先頭、1 = 尾の端\n"
        "float fade = pow(1 - clamp(f@age / f@life, 0, 1), 1.5);         // 寿命の終わりへ向けて暗く\n"
        "vector hot = {1.0, 0.95, 0.8};\n"
        "v@Cd = lerp(hot, v@Cd * {1, 0.55, 0.3}, smooth(0, 0.6, lag)) * fade * (1 - lag * 0.85);\n"
        "f@width = lerp(chf('w_head'), chf('w_tail'), lag);\n"
        "f@pscale = f@width;   // POP が付けた pscale（粒の大きさ）も線の太さとして読まれるので、同じ値にそろえる"))
    glow.parm("class").set(2)
    R = spread[0] / 2   # 開いた花火の半径（測った値）。太さ・間隔・カメラはこれで決める
    kit_spare(glow, trail_sec=TRAIL / 24.0, w_head=round(R * 0.0022, 3), w_tail=round(R * 0.0006, 3))
    g.step(glow, "通った跡を線にして、尾を付ける",
           f"<code>trail</code> の Result Type を <strong>Connect as Polygons</strong>、Trail Length を <strong>{TRAIL}</strong> にすると、"
           f"星ごとに「今までの {TRAIL} フレーム分の位置」をつないだ線ができる。これが火の粉の尾になる。"
           f"次の <code>attribwrangle</code> で、線の先頭ほど白く太く、うしろほど赤く細くする（width {R * 0.0022:.2f} → {R * 0.0006:.2f} m）。"
           "さらに寿命の終わりに向けて全体を暗くすると、燃え尽きて消えていく。",
           cap="尾を引いて垂れる金色の菊。", shading="wire", ui_parm="length")

    shells = []
    plan = [((0, 0, 0), 0, None), (( -R * 1.7, -R * 0.5, -R * 1.2), 7, (1.0, 0.25, 0.35)),
            ((R * 1.6, -R * 0.25, -R * 1.6), 13, (0.45, 0.85, 1.0))]
    for i, (pos, delay, tint) in enumerate(plan):
        src_node = glow
        if tint:
            recolor = g.node("attribwrangle", f"tint{i}", [glow], snippet=(
                "// 金色（元の色）を、この玉の色に置き換える。明るさは元のまま\n"
                "float lum = max(v@Cd.r, max(v@Cd.g, v@Cd.b));\n"
                "vector c = chv('tint');\n"
                "v@Cd = lerp(c * lum, v@Cd, clamp(lum - 0.85, 0, 1) * 4);"))
            recolor.parm("class").set(2)
            kit_spare(recolor, tint=tint)
            src_node = recolor
        late = g.node("timeshift", f"later{i}", [src_node])
        late.parm("frame").deleteAllKeyframes()
        late.parm("frame").setExpression(f"max($F - {delay}, 1)")
        move = g.node("xform", f"place{i}", [late], t=pos)
        shells.append(move)
    sky = g.node("merge", "three_shells", shells)
    g.step(sky, "時間と場所をずらして3発にする",
           "<code>timeshift</code> の Frame に <strong>$F - 7</strong> のような式を入れると、同じ花火を 7 フレーム遅れて再生できる。"
           "<code>xform</code> で場所をずらし、もう1本の <code>attribwrangle</code> で色を赤・水色に置き換える。"
           "計算（POP）は1回だけで、3発とも同じ結果を使い回すので軽い。最後に <code>merge</code> でまとめる。",
           cap=f"フレーム {HERO_F}。3発が少しずつ遅れて開いている。", shading="wire", ui_parm="frame",
           bbox=hou.BoundingBox(-R * 2.8, -R * 2.2, -R * 2.8, R * 2.7, R * 1.2, R))

    fire = g.mat("fireworks_mat", basecolor=(0, 0, 0), rough=1.0, reflect=0.0, emitint=0.9, emitcolor=(1, 1, 1))
    fire.parm("emitcolor_usePointColor").set(1)
    final = g.assign(sky, fire, "assign_fire")
    g.step(final, "光る材質を当てる",
           "<code>principledshader</code> の <strong>Emission Intensity を 0.9</strong>、<strong>Emission Color の Use Point Color</strong> を入れる。"
           "線の色（Cd）がそのまま光の色になる。Base Color は黒にして、光以外の見え方を消す。",
           cap="材質を当てた状態（ビューポートでは光らない）。", shot=False)

    box = hou.BoundingBox(-R * 2.6, -R * 1.5, -R * 2.8, R * 2.5, R * 1.1, R)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {HERO_F}）。3発の菊が、時間差で開いている。", direction=(0.18, 0.1, 1.0),
           floor=False, key=0.0, rim=0.0, dome=0.035, dome_color=(0.18, 0.24, 0.5), spp=64, margin=1.02, frame=HERO_F,
           bbox=box)
    g.anim(final, (1, LAST), "打ち上がって開き、垂れて消えるまで（60 フレーム＝2.5 秒）。", bbox=box, direction=(0.18, 0.1, 1.0),
           shading="wire")

    # ---- 落とし穴を測る ----
    hou.setFrame(HERO_F)
    drag.parm("airresist").set(0.0)
    free = imp.geometry().boundingBox().sizevec()[0]
    drag.parm("airresist").set(0.45)
    push.parm("speed").set(34.0)
    n_pts = sum(len(s.geometry().points()) for s in [glow])
    src.parm("lifevar").set(0.0)
    hou.setFrame(40)
    alive_same = len(imp.geometry().points())
    hou.setFrame(60)
    alive_same_60 = len(imp.geometry().points())
    src.parm("lifevar").set(0.5)
    hou.setFrame(40)
    alive_var = len(imp.geometry().points())
    hou.setFrame(60)
    alive_var_60 = len(imp.geometry().points())
    hou.setFrame(HERO_F)
    traps = [
        {"title": "空気抵抗を入れないと、花火に見えない",
         "body": f"Air Resistance を 0 にすると、フレーム {HERO_F} の広がりは約 {free:.0f} m（0.45 のときは約 {spread[0]:.0f} m）。"
                 "減速しないので星がまっすぐ飛び続け、ただ大きくなる球になる。本物は最初に勢いよく開き、すぐ止まって垂れる。",
         "img": "", "cap": ""},
        {"title": "寿命をばらけさせないと、一斉に消える",
         "body": f"Life Variance 0 では、フレーム 40 に {alive_same} 個あった星が、フレーム 60 には {alive_same_60} 個。"
                 f"0.5 では 40 で {alive_var} 個、60 で {alive_var_60} 個。ばらつきがあると、少しずつ消えていく。",
         "img": "", "cap": ""},
        {"title": "尾の点数は、星の数 × Trail Length",
         "body": f"320 個の星に Trail Length {TRAIL} で、尾の線の点はフレーム {HERO_F} で {n_pts:,} 個。"
                 "尾を長くすると点が同じ割合で増える。3発にしても計算は1回で済むのは、timeshift で使い回しているから。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "15個（dopnet の中に5個）"], ["星の数", "320個 × 3発"],
                  [f"{LAST} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps)


def kit_spare(node, **values):
    """wrangle の chf / chv のつまみを作って値を入れる（GUI の「Create spare parameters」ボタンと同じこと）。"""
    import hou
    group = node.parmTemplateGroup()
    for name, value in values.items():
        if isinstance(value, (tuple, list)):
            tmpl = hou.FloatParmTemplate(name, name, 3, default_value=value, naming_scheme=hou.parmNamingScheme.RGBA
                                         if "color" in name or "tint" in name else hou.parmNamingScheme.XYZW)
        else:
            tmpl = hou.FloatParmTemplate(name, name, 1, default_value=(value,))
        group.append(tmpl)
    node.setParmTemplateGroup(group)
    for name, value in values.items():
        if isinstance(value, (tuple, list)):
            node.parmTuple(name).set(value)
        else:
            node.parm(name).set(value)


if __name__ == "__main__":
    main()
