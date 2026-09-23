# -*- coding: utf-8 -*-
"""実践「岩を作る」— 箱から、ごつごつした岩を作って Karma で撮る。

    hython examples/pr_rock.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    g = kit.Guide("rock", "岩を作る",
                  "球を割ったかけらに、うねりと細かいでこぼこを重ねると岩になる。"
                  "割れた平らな面が岩らしさの元。でこぼこを乗せる前に、網を細かく均等にしておく。",
                  tags=["モデリング", "ノイズ", "岩", "Karma"])
    base = g.node("sphere", "base", type="polymesh", rows=24, cols=48, rad=(0.9, 0.6, 0.75))
    g.step(base, "もとの形を置く",
           "<code>sphere</code> を置き、Primitive Type を Polygon Mesh、半径を 0.9 × 0.6 × 0.75 にする。"
           "これを割って、その1かけらを岩にする。",
           cap="少しつぶれた球。", shading="smoothwire")
    pts = g.node("scatter::2.0", "cut_points", [base], npts=9, seed=4)
    g.step(pts, "割る位置を散らす",
           "<code>scatter</code> で表面に9個の点をばらまく。点の1つ1つが、割れたかけらの中心になる。"
           "点を増やすほど、かけらは小さく、面の数は多くなる。",
           cap="9個の点。", ui_parm="npts")
    frac = g.node("voronoifracture::2.0", "split", [base, pts])
    import hou
    names = sorted({p.attribValue("name") for p in frac.geometry().prims()})
    # いちばん大きいかけらを岩にする
    best = max(names, key=lambda nm: sum(pr.intrinsicValue("measuredarea") for pr in frac.geometry().prims()
                                          if pr.attribValue("name") == nm))
    g.step(frac, "球を割る",
           "<code>voronoifracture</code> の左に球、右に点をつなぐ。球が点の数だけのかけらに割れ、"
           "<strong>割れ目は平らな面になる</strong>。この平らな面と角が、岩らしさの元になる。",
           cap=f"{len(names)} 個のかけら。")
    one = g.node("blast", "keep_one", [frac], group=f"@name={best}", negate=1)
    base = g.node("matchsize", "sit_on_floor", [one], justify_y=1)
    g.step(base, "かけらを1つ取り出す",
           f"<code>blast</code> の Group に <code>@name={best}</code> と書き、<strong>Delete Non Selected</strong> を入れると、"
           "そのかけらだけが残る。<code>matchsize</code> で真ん中に寄せ、底を床の高さにそろえる。",
           cap="平らな割れ面と、丸い外側が混ざった形。", shading="smoothwire")
    mesh = g.node("remesh::2.0", "even_mesh", [base], targetsize=0.02)
    g.step(mesh, "網を細かく均等にする",
           "<code>remesh</code> で三角形の網に作り直す。<strong>Target Size を 0.02</strong> にすると、"
           "どこも同じくらいの大きさの三角形で埋まる。このあと乗せるでこぼこは、点を動かして作るので、"
           "点が少ない所は細かく動けない。",
           cap="どこも同じ大きさの三角形になる。", shading="smoothwire", ui_parm="targetsize")
    big = g.node("mountain::2.0", "big_lumps", [mesh], height=0.12, elementsize=0.6, rough=0.45)
    g.step(big, "大きなうねりを乗せる",
           "<code>mountain</code> で面を法線の向きに押し出す。<strong>Height 0.12・Element Size 0.6</strong>。"
           "割れ面の平らさを残したいので、うねりは控えめにする。Height を上げすぎると、割れ面が溶けて芋のようになる。",
           cap="割れ面にゆるいうねりが乗る。", ui_parm="height")
    fine = g.node("mountain::2.0", "fine_detail", [big], height=0.035, elementsize=0.1, rough=0.6, oct=6)
    g.step(fine, "細かいでこぼこを重ねる",
           "もう1つ <code>mountain</code> をつなぎ、<strong>Height 0.035・Element Size 0.1</strong> にする。"
           "大きさの違うノイズを2段に分けると、遠目の形と近くで見た肌理を別々に調整できる。",
           cap="表面に岩肌の肌理が出る。", ui_parm="elementsize")
    color = g.node("attribwrangle", "color_speckle", [fine],
                   snippet="float n = noise(@P * 9.0) * 0.6 + noise(@P * 38.0) * 0.4;\n"
                           "@Cd = fit(n, 0.25, 0.75, 0.35, 1.0);")
    col = g.step(color, "色のむらを付ける",
                 "<code>attribwrangle</code> に2行だけ書き、色（Cd）の明るさを 0.35〜1.0 でばらつかせる。"
                 "大きな模様（×9）と細かい模様（×38）を混ぜると、同じ灰色でも汚れや風化のようなむらになり、作り物っぽさが消える。"
                 "<br><code>float n = noise(@P * 9.0) * 0.6 + noise(@P * 38.0) * 0.4;</code>"
                 "<br><code>@Cd = fit(n, 0.25, 0.75, 0.35, 1.0);</code>",
                 cap="明るいところと暗いところのまだら。", ui_parm="snippet")
    rock_mat = g.mat("rock_mat", basecolor=(0.42, 0.39, 0.35), rough=0.82, reflect=0.3, basecolor_usePointColor=1)
    final = g.assign(col, rock_mat, "assign_rock")
    g.step(final, "岩の材質を当てる",
           "<code>/mat</code> に <code>principledshader</code> を作り、Base Color を少し茶色がかった灰色、"
           "<strong>Roughness 0.82</strong> にする。<strong>Use Point Color を入れる</strong>と、前の段の色のむらが材質に乗る。"
           "<code>material</code> ノードで割り当てる。",
           cap="材質を当てた状態（ビューポート）。", shot=False)
    final.setDisplayFlag(True)
    g.hero(final, "Karma で撮った仕上がり。球を1つ割るところから作れる。", direction=(0.85, 0.42, 1.2),
           key_color=(1.0, 0.93, 0.82))

    # ---- 落とし穴を測る: remesh を省くと、でこぼこが乗らない ----
    import hou
    rows = []
    for ts in (None, 0.08, 0.04, 0.02):
        mesh.parm("targetsize").set(ts or 0.02)
        mesh.bypass(ts is None)
        t0 = time.perf_counter()
        geo = fine.geometry()
        sec = time.perf_counter() - t0
        rows.append((ts, geo.intrinsicValue("pointcount"), sec))
    mesh.bypass(False)
    mesh.parm("targetsize").set(0.02)
    print(rows)
    kit_rows = {r[0]: r for r in rows}
    traps = [
        {"title": "remesh を省くと、でこぼこが乗らない",
         "body": f"かけらのままでは {kit_rows[None][1]:,} 点しかなく、mountain は点を動かすだけなので、細かい肌理が乗らない。"
                 f"remesh の Target Size を 0.08・0.04・0.02 にすると点は {kit_rows[0.08][1]:,}・{kit_rows[0.04][1]:,}・{kit_rows[0.02][1]:,} 個。"
                 "細かいでこぼこ（Element Size 0.1）をはっきり出すには、その 1/5 くらいの 0.02 が目安。",
         "img": "", "cap": ""},
        {"title": "網を細かくすると、そのぶん重くなる",
         "body": f"mountain 2つまで計算し直す時間は、0.08 で {kit_rows[0.08][2]:.2f} 秒、0.02 で {kit_rows[0.02][2]:.2f} 秒。"
                 "岩をたくさん並べるなら、1つを細かく作ってから複製する（手順「地面に物を生やす」）。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "10個"], ["点の数", f"{kit_rows[0.02][1]:,}"]], traps=traps)


if __name__ == "__main__":
    main()
