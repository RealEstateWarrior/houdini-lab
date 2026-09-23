# -*- coding: utf-8 -*-
"""実践「夜の街を並べる」— 区画に高さの違うビルを並べ、窓をところどころ光らせて、夜景として撮る。

    hython examples/pr_nightcity.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("nightcity", "夜の街を並べる",
                  "格子の点にビルの箱を1つずつ置き、高さを中心ほど高く、少しずつばらつかせる。"
                  "壁を窓の升目に割って、ところどころを光らせれば夜景になる。街全体を手で作らず、ルールで作る（プロシージャル）入り口。",
                  tags=["モデリング", "複製", "プロシージャル", "街", "Karma", "制作"])
    g.shot_dir = (1.0, 0.9, 1.2)
    lots = g.node("grid", "lots", size=(12, 12), rows=13, cols=13)
    g.step(lots, "区画の点を用意する",
           "<code>grid</code> を 12 × 12、<strong>Rows・Columns を 13</strong> にすると、1 おきに 169 個の点が並ぶ。1つの点に1棟を建てる。",
           cap="169 個の点。", shading="smoothwire")
    plan = g.node("attribwrangle", "zoning", [lots],
                  snippet="// 中心ほど高く、ノイズでばらつかせる\n"
                          "float d = length(set(@P.x, 0, @P.z));\n"
                          "float h = fit(d, 0, 7, 5.0, 0.4) * fit01(rand(@ptnum), 0.4, 1.3);\n"
                          "if (rand(@ptnum + 17) < 0.12) removepoint(0, @ptnum);   // 空き地\n"
                          "float w = fit01(rand(@ptnum + 5), 0.35, 0.6);\n"
                          "v@scale = set(w, h, w);\n"
                          "p@orient = {0, 0, 0, 1};   // 向きを固定（grid の法線 N に合わせて倒れないように）\n"
                          "@P.x += (rand(@ptnum + 1) - 0.5) * 0.12;\n"
                          "@P.z += (rand(@ptnum + 2) - 0.5) * 0.12;")
    g.step(plan, "高さと幅を決める",
           "<code>attribwrangle</code> で、点ごとに建物の大きさ（<code>scale</code>、幅・高さ・奥行き）を決める。"
           "中心からの距離 d が小さいほど高く（5.0 → 0.4）、<code>rand</code> で 0.4〜1.3 倍にばらつかせる。"
           "12% の点は <code>removepoint</code> で消して空き地にする。"
           "<strong><code>p@orient = {0,0,0,1}</code> で向きを固定する</strong>（理由は落とし穴に）。",
           cap="点ごとに高さが決まる（まだ点のまま）。", shading="smoothwire", ui_parm="snippet")
    box = g.node("box", "building", size=(1, 1, 1), t=(0, 0.5, 0))
    g.step(box, "1棟ぶんの箱を作る",
           "<code>box</code> を大きさ 1 のまま、<strong>Center の Y を 0.5</strong> にする。底が地面（y=0）に乗るので、"
           "高さを伸ばしても地面に埋まらない。",
           cap="底が地面にある箱。", shading="smoothwire")
    city = g.node("copytopoints::2.0", "city", [box, plan])
    g.step(city, "点に箱を並べる",
           "<code>copytopoints</code> で、左に箱、右に点。点の <code>scale</code> で箱が伸び縮みして、高さの違うビルが建つ。",
           cap="148 棟の街。", shading="smoothwire")
    wins = g.node("divide", "window_grid", [city], convex=0, brick=1, sizex=0.05, sizey=0.07, sizez=0.05)
    g.step(wins, "壁を窓の升目に割る",
           "<code>divide</code> の <strong>Bricker Polygons</strong> を入れ、Size を 0.05 × 0.07 × 0.05 にする。"
           "壁も屋上も、窓くらいの大きさの升目に切れる。",
           cap="壁が細かい升目になる。", shading="smoothwire", ui_parm="brick")
    lit = g.node("attribwrangle", "lights_on", [wins], **{"class": 1},
                 snippet="// 壁の升目のうち、ところどころを「点いた窓」にする\n"
                         "vector n = prim_normal(0, @primnum, 0.5, 0.5);\n"
                         "i@lit = abs(n.y) < 0.5 && rand(@primnum * 0.37) < 0.16;\n"
                         "v@Cd = i@lit ? (rand(@primnum + 3) < 0.7 ? set(1.0, 0.72, 0.4) : set(0.75, 0.88, 1.0)) * fit01(rand(@primnum), 0.4, 1.2) : {0.1, 0.1, 0.12};")
    g.step(lit, "窓を点ける",
           "<code>attribwrangle</code> の Run Over を <strong>Primitives</strong> にし、壁向き（法線の Y が小さい）の升目のうち "
           "16% を <code>lit</code> = 1 にする。点いた窓には暖かい色（7割）か白っぽい青（3割）を、明るさもばらつかせて入れる。",
           cap="点いた窓が色で分かる（ビューポート）。", ui_parm="snippet")
    ground = g.node("grid", "street", size=(16, 16), rows=2, cols=2)
    facade = g.mat("facade_mat", basecolor=(0.09, 0.095, 0.11), rough=0.35, reflect=0.6)
    window = g.mat("window_mat", basecolor=(0.05, 0.05, 0.05), emitcolor=(1, 1, 1), emitint=3.0,
                   emitcolor_usePointColor=1, rough=0.2)
    road = g.mat("road_mat", basecolor=(0.03, 0.032, 0.036), rough=0.25, reflect=0.8)
    mats = g.node("material", "assign_city", [lit], num_materials=2)
    mats.parm("group1").set("@lit=0")
    mats.parm("shop_materialpath1").set(facade.path())
    mats.parm("group2").set("@lit=1")
    mats.parm("shop_materialpath2").set(window.path())
    road_a = g.assign(ground, road, "assign_road")
    final = g.node("merge", "night_city", [mats, road_a])
    g.step(final, "壁・窓・道の材質を当てる",
           "<code>principledshader</code> を3つ。壁は暗い青みの灰色で少し映り込み、窓は <strong>Emission Intensity 3・Use Point Color</strong>"
           "（前の段の色で光る）、道はほぼ黒で映り込みを強く（濡れた路面）。<code>material</code> の Group に "
           "<code>@lit=0</code> と <code>@lit=1</code> を書き分けて当てる。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った夜景。明かりは窓と、弱い青い空の光だけ。", direction=(1.0, 0.42, 1.3),
           key=0.35, rim=0.8, dome=0.06, dome_color=(0.35, 0.45, 0.8), key_color=(0.6, 0.7, 1.0),
           rim_color=(0.5, 0.6, 1.0), spp=48, margin=0.9, floor=False,
           bbox=hou.BoundingBox(-6.5, 0, -6.5, 6.5, 5.5, 6.5))
    tall_after = city.geometry().boundingBox().sizevec()[1]
    snip = plan.parm("snippet").eval()
    plan.parm("snippet").set(snip.replace("p@orient = {0, 0, 0, 1};", "// orient なし"))
    tall_before = city.geometry().boundingBox().sizevec()[1]
    plan.parm("snippet").set(snip)
    n_bld = city.geometry().intrinsicValue("primitivecount") // 6
    n_poly = wins.geometry().intrinsicValue("primitivecount")
    n_lit = sum(1 for p in lit.geometry().prims() if p.attribValue("lit") == 1)
    t0 = time.perf_counter()
    wins.parm("sizex").set(0.025)
    wins.parm("sizey").set(0.035)
    wins.parm("sizez").set(0.025)
    n_fine = wins.geometry().intrinsicValue("primitivecount")
    sec_fine = time.perf_counter() - t0
    traps = [
        {"title": "Center の Y を 0.5 にしないと、ビルが地面に埋まる",
         "body": "box は中心が原点にあるので、そのまま高さを伸ばすと、上と下に同じだけ伸びて半分が地面の下に入る。"
                 "底を y=0 に置くには Center の Y を 0.5（大きさの半分）にしてから並べる。",
         "img": "", "cap": ""},
        {"title": "grid の点に並べると、ビルが横倒しになる",
         "body": f"grid の点には上向きの法線 N が付いていて、copytopoints は箱の Z（奥行き）を N にそろえる。"
                 f"向きを決めずに並べると、高さが横に倒れ、街全体の高さが {tall_before:.2f} しかなかった"
                 f"（orient を固定すると {tall_after:.2f}）。高さを持つ物を並べるときは orient を入れておく。",
         "img": "", "cap": ""},
        {"title": "窓の升目を細かくすると、面の数が一気に増える",
         "body": f"{n_bld} 棟を 0.05 × 0.07 の升目に割ると {n_poly:,} 面（うち点いた窓 {n_lit:,}）。"
                 f"升目を半分（0.025 × 0.035）にすると {n_fine:,} 面で、割り直すだけで {sec_fine:.1f} 秒かかった。遠景の街なら粗い升目で足りる。",
         "img": "", "cap": ""},
    ]
    wins.parm("sizex").set(0.05)
    wins.parm("sizey").set(0.07)
    wins.parm("sizez").set(0.05)
    g.save(facts=[["足すノード", "11個（材質3つ）"], ["建物", f"{n_bld}棟"], ["面の数", f"{n_poly:,}"]], traps=traps)


if __name__ == "__main__":
    main()
