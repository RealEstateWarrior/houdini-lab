# -*- coding: utf-8 -*-
"""実践「朝露の蜘蛛の巣」— 放射状の縦糸、らせんの横糸、糸に並ぶ露の粒を作る。

本物の丸い巣（円網）は、中心から放射状に張った縦糸に、外へ向かうらせんの横糸を掛けたもの。
横糸は縦糸の間で少したるみ、朝は細かい露の粒が糸に並んで光る。

    hython examples/pr_web.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("web", "朝露の蜘蛛の巣",
                  "中心から放射状に縦糸を張り、外へ向かうらせんで横糸を掛ける。横糸は縦糸の間で少したるませ、"
                  "最後に糸の上へ小さな水の粒を並べる。後ろから光を当てると、露がきらきら光る。",
                  tags=["モデリング", "VEX", "カーブ", "Karma"])
    g.shot_dir = (0.2, 0.1, 1.0)
    spokes = g.node("attribwrangle", "spokes", snippet=(
        "// 中心から放射状に縦糸を張る。本数・長さは少しずつばらつかせる\n"
        "int n = chi('count');\n"
        "float angs[];\n"
        "float rads[];\n"
        "int center = addpoint(0, {0, 0, 0});\n"
        "int ends[];\n"
        "for (int i = 0; i < n; i++) {\n"
        "    float ang = (i + (rand(i + 1) - 0.5) * 0.35) * 2 * PI / n;\n"
        "    float r = chf('radius') * fit01(rand(i + 17), 0.9, 1.05);\n"
        "    int e = addpoint(0, set(cos(ang) * r, sin(ang) * r, 0));\n"
        "    int prim = addprim(0, 'polyline');\n"
        "    addvertex(0, prim, center);\n"
        "    addvertex(0, prim, e);\n"
        "    append(angs, ang);\n"
        "    append(rads, r);\n"
        "    append(ends, e);\n"
        "}\n"
        "// 外枠の糸（縦糸の先をつなぐ）\n"
        "int frame = addprim(0, 'polyline');\n"
        "foreach (int e; ends) addvertex(0, frame, e);\n"
        "addvertex(0, frame, ends[0]);\n"
        "// 次のノードが使えるように、角度と長さを覚えておく\n"
        "setdetailattrib(0, 'angs', angs);\n"
        "setdetailattrib(0, 'rads', rads);"))
    spokes.parm("class").set(0)
    kit_spare(spokes, ints={"count": 28}, radius=0.25)
    g.step(spokes, "縦糸を放射状に張る",
           "何もつながない <code>attribwrangle</code> を置き、Run Over を <strong>Detail</strong>（全体で1回だけ）にする。"
           "中心に点を1つ置き、<strong>count = 28</strong> 本の縦糸を放射状に伸ばす。角度と長さ（radius = 0.25 m）は1本ごとに少しずつずらす。"
           "縦糸の先どうしをつないだ外枠の糸も作る。最後に、角度と長さを <strong>setdetailattrib</strong> で覚えておく（次のノードで使う）。",
           cap="28 本の縦糸と外枠。", shading="wire", ui_parm="count",
           bbox=hou.BoundingBox(-0.3, -0.3, -0.05, 0.3, 0.3, 0.05))

    spiral = g.node("attribwrangle", "spiral", [spokes], snippet=(
        "// 外へ向かうらせんで横糸を掛ける。縦糸と交わる所に点を置き、その間は中心へ少したるませる\n"
        "float angs[] = detail(0, 'angs');\n"
        "float rads[] = detail(0, 'rads');\n"
        "int n = len(angs);\n"
        "int prim = addprim(0, 'polyline');\n"
        "vector prev = 0;\n"
        "for (int k = 0; k < 2000; k++) {\n"
        "    int i = k % n;\n"
        "    float r = chf('start') + chf('gap') * k / n;\n"
        "    if (r > rads[i] * 0.93) break;             // いちばん短い縦糸の手前で止める\n"
        "    vector p = set(cos(angs[i]) * r, sin(angs[i]) * r, 0);\n"
        "    if (k > 0) {\n"
        "        for (int s = 1; s < 5; s++) {           // 縦糸の間に4点。まん中ほど中心へ寄せる（たるみ）\n"
        "            float t = s / 5.0;\n"
        "            vector q = lerp(prev, p, t);\n"
        "            q -= normalize(q) * chf('sag') * sin(PI * t) * length(p - prev);\n"
        "            addvertex(0, prim, addpoint(0, q));\n"
        "        }\n"
        "    }\n"
        "    addvertex(0, prim, addpoint(0, p));\n"
        "    prev = p;\n"
        "}"))
    spiral.parm("class").set(0)
    kit_spare(spiral, start=0.03, gap=0.011, sag=0.12)
    g.step(spiral, "らせんの横糸を掛ける",
           "もう1つの Detail の <code>attribwrangle</code> で、覚えておいた縦糸の角度を1本ずつ回りながら、半径を少しずつ大きくして点を置く。"
           "1周で <strong>gap = 0.011</strong> m 外へ進む。縦糸と縦糸の間には4点を足し、まん中ほど中心へ寄せる（<strong>sag = 0.12</strong>）。"
           "本物の横糸も、縦糸の間で内側へ少したるむ。いちばん短い縦糸の手前で止める。",
           cap="らせんの横糸。縦糸の間で少したるむ。", shading="wire", ui_parm="gap",
           bbox=hou.BoundingBox(-0.3, -0.3, -0.05, 0.3, 0.3, 0.05))

    silk = g.node("attribwrangle", "silk_width", [spiral], snippet="f@width = chf('width');   // Karma で撮る糸の太さ")
    kit_spare(silk, width=0.0005)
    beads = g.node("resample", "along_silk", [silk], dolength=1, length=0.0025)
    dew = g.node("attribwrangle", "pick_drops", [beads], snippet=(
        "// 糸の上の点から、ところどころを露の粒にする。大きさもばらつかせる\n"
        "if (rand(@ptnum * 1.7 + 3) > chf('keep')) removepoint(0, @ptnum);\n"
        "f@pscale = fit01(pow(rand(@ptnum + 9), 3), chf('small'), chf('big'));\n"
        "@P.y -= f@pscale * 0.6;   // 水は重さで糸の下側に垂れて付く"))
    kit_spare(dew, keep=0.2, small=0.0006, big=0.0022)
    g.step(dew, "露の粒を置く場所を決める",
           "<code>attribwrangle</code> で糸に太さ <strong>width = 0.0005</strong>（0.5 mm）を付ける。"
           "<code>resample</code> で糸を 2.5 mm ごとの点に打ち直し、次の <code>attribwrangle</code> で <strong>2 割</strong>だけ残す（keep = 0.2）。"
           "残った点の大きさ <strong>pscale</strong> は 0.6〜2.2 mm。乱数を3乗して、小さい粒を多く、大きい粒を少しにする。"
           "水は重さで糸の下に付くので、粒の大きさに合わせて少し下げる。",
           cap="糸の上に散らばった露の場所。", shading="wire", ui_parm="keep",
           bbox=hou.BoundingBox(-0.3, -0.3, -0.05, 0.3, 0.3, 0.05))

    drop = g.node("sphere", "drop", type="polymesh", rad=(1, 1, 1), rows=10, cols=16)
    drops = g.node("copytopoints::2.0", "drops", [drop, dew])
    n_drops = len(dew.geometry().points())
    g.step(drops, "粒をコピーする",
           f"<code>sphere</code>（半径 1）を <code>copytopoints</code> で露の点に並べる。点の pscale が大きさになり、{n_drops:,} 粒になる。",
           cap=f"{n_drops:,} 粒の露。", shading="smooth",
           bbox=hou.BoundingBox(-0.3, -0.3, -0.05, 0.3, 0.3, 0.05))

    thread = g.mat("silk_mat", basecolor=(0.9, 0.9, 0.88), rough=0.35, sheen=0.5)
    water = g.mat("dew_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.33, transparency=1.0)
    final = g.node("merge", "web", [g.assign(silk, thread, "assign_silk"), g.assign(drops, water, "assign_dew")])
    g.step(final, "材質を当てる",
           "糸は白く Roughness 0.35、<strong>Sheen 0.5</strong>。露は <code>principledshader</code> で "
           "<strong>Transparency 1・IOR 1.33</strong>（水）、Roughness 0。撮るときは後ろからの光（リム）を強くすると、粒の縁が光る。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。後ろからの光で、露の粒と糸が光る。", direction=(0.25, 0.12, 1.0),
           key=0.8, rim=10.0, dome=0.08, spp=96, margin=1.02, backdrop=(0.012, 0.022, 0.01), backdrop_reflect=0.0,
           rim_color=(1.0, 0.92, 0.8), bbox=hou.BoundingBox(-0.28, -0.28, -0.02, 0.28, 0.28, 0.02))

    # ---- 落とし穴を測る ----
    total = sum(pr.intrinsicValue("measuredperimeter") for pr in silk.geometry().prims())
    spiral.parm("gap").set(0.022)
    turns_wide = len(spiral.geometry().prims()) and len(spiral.geometry().points())
    spiral.parm("gap").set(0.011)
    pts_now = len(spiral.geometry().points())
    traps = [
        {"title": "gap で横糸の本数が決まる",
         "body": f"gap 0.011 で、縦糸と横糸を合わせた点は {pts_now:,} 個。gap を 2 倍の 0.022 にすると {turns_wide:,} 個。"
                 "横糸を細かくするほど、露の粒も増える。",
         "img": "", "cap": ""},
        {"title": "露の数は、糸の長さ × 割合で決まる",
         "body": f"糸の長さは合わせて {total:.1f} m。2.5 mm ごとに点を打ち、2 割を残したので {n_drops:,} 粒になった。"
                 "粒が多すぎると、糸が見えなくなる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "11個（材質2つ）"], ["露の粒", f"{n_drops:,}個"], ["糸の長さ", f"{total:.1f} m"]],
           traps=traps)


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
