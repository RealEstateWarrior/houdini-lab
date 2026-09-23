# -*- coding: utf-8 -*-
"""実践「氷の入ったグラスの水」— 断面を回してグラスと水を作り、氷を浮かべて、ガラス・水・氷の材質で撮る。

本物のグラスは、底が厚く、口に向かって少し広がり、縁は薄い。水は内側いっぱいに入り、氷は水面から少し頭を出して浮く。
ガラス（屈折率 1.5）・水（1.33）・氷（1.31）は、どれも透明で、曲がり方（屈折）の違いで見分けがつく。

    hython examples/pr_glasscup.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

WATER_TOP = 0.07


def main():
    import hou
    g = kit.Guide("glasscup", "氷の入ったグラスの水",
                  "グラスの断面（厚い底・薄い縁）を1枚の多角形で描き、revolve で回して立体にする。水も、内側の断面を回して作る。"
                  "氷は角を丸めた箱。ガラス・水・氷は、屈折率（光の曲がり方）だけを変えた透明な材質で撮る。",
                  tags=["モデリング", "Karma", "材質", "ガラス"])
    g.shot_dir = (1.0, 0.35, 1.2)
    profile = g.node("attribwrangle", "glass_profile", snippet=(
        "// グラスの断面（x が軸からの距離、y が高さ）。外側を下から上へ、縁で折り返して内側を上から下へ\n"
        "vector pts[] = {\n"
        "    {0.0, 0.0, 0}, {0.030, 0.0, 0}, {0.032, 0.002, 0},   // 外の底（角を少し丸める）\n"
        "    {0.036, 0.100, 0}, {0.0355, 0.1012, 0}, {0.0343, 0.1012, 0},   // 縁（薄い）\n"
        "    {0.0335, 0.100, 0}, {0.030, 0.010, 0}, {0.028, 0.008, 0}, {0.0, 0.008, 0}   // 内側と、厚い底\n"
        "};\n"
        "int prim = addprim(0, 'poly');\n"
        "foreach (vector p; pts) addvertex(0, prim, addpoint(0, p));"))
    profile.parm("class").set(0)
    g.step(profile, "グラスの断面を描く",
           "何もつながない <code>attribwrangle</code>（Run Over は Detail）で、グラスを縦に切った断面を1枚の多角形にする。"
           "x は軸からの距離、y は高さ。外側を下から上へ（底は半径 3 cm、口は 3.6 cm）、縁で折り返して内側を上から下へたどる。"
           "底の厚さは 8 mm、縁は 1 mm 弱。本物のグラスも、底が厚くて縁が薄い。",
           cap="グラスの断面（半分）。", shading="wire", bbox=hou.BoundingBox(-0.005, -0.005, -0.01, 0.045, 0.11, 0.01))

    cup = g.node("revolve::2.0", "glass", [profile], divs=96)
    g.step(cup, "回してグラスにする",
           "<code>revolve</code> で断面を y 軸のまわりに1周回す。<strong>Divisions 96</strong>（96 等分）で、縁の丸みがなめらかになる。"
           "閉じた断面を回すので、中まで詰まった（厚みのある）ガラスになる。",
           cap="厚い底と薄い縁のグラス。", shading="smoothwire", ui_parm="divs")

    water_prof = g.node("attribwrangle", "water_profile", snippet=(
        f"// 水の断面。内側の壁に沿って、水面（高さ {WATER_TOP}）まで。壁と重ならないよう 0.2 mm 内側にする\n"
        f"float top = {WATER_TOP};\n"
        "float r_top = 0.030 + (top - 0.010) / 0.090 * 0.0035 - 0.0002;\n"
        "vector pts[] = {{0.0, 0.0082, 0}, {0.0278, 0.0082, 0}, {0.0298, 0.0102, 0}};\n"
        "append(pts, set(r_top, top, 0));   // { } の中には計算した値を書けないので、あとから足す\n"
        "append(pts, set(0.0, top, 0));\n"
        "int prim = addprim(0, 'poly');\n"
        "foreach (vector p; pts) addvertex(0, prim, addpoint(0, p));"))
    water_prof.parm("class").set(0)
    water = g.node("revolve::2.0", "water", [water_prof], divs=96)
    liquid_ml = g.node("measure::2.0", "water_volume", [water], measure="volume", attribname="volume")
    # 断面をたどる向きで面が内向きになり、体積が負で出る。大きさだけ使う
    vol_ml = abs(sum(p.attribValue("volume") for p in liquid_ml.geometry().prims())) * 1e6 \
        if liquid_ml.geometry().findPrimAttrib("volume") else 0
    g.step(water, "水を入れる",
           f"内側の壁に沿った断面を、もう1つの Detail の <code>attribwrangle</code> で描き、同じく <code>revolve</code> で回す。水面は高さ {WATER_TOP * 100:.0f} cm。"
           "壁とぴったり同じ面にすると、ガラスと水の境目がちらつくので、<strong>0.2 mm だけ内側</strong>にする。"
           f"<code>measure</code>（Volume）で測ると、水は {vol_ml:.0f} ml。",
           cap=f"グラスの中の水（{vol_ml:.0f} ml）。", shading="smooth", ui_parm="divs")

    cube = g.node("box", "ice_block", size=(0.021, 0.019, 0.02))
    soft = g.node("polybevel::3.0", "melted_edges", [cube], offset=0.003, divisions=3)
    spots = g.node("attribwrangle", "ice_spots", snippet=(
        "// 氷3つの置き場所と向き。水面あたりに浮かべる\n"
        f"vector places[] = {{{{-0.011, {WATER_TOP - 0.004}, 0.006}}, {{0.012, {WATER_TOP - 0.006}, -0.004}}, {{0.0, {WATER_TOP - 0.021}, -0.012}}}};\n"
        "for (int i = 0; i < 3; i++) {\n"
        "    int p = addpoint(0, places[i]);\n"
        "    setpointattrib(0, 'orient', p, quaternion(radians(set(rand(i) * 40 - 20, rand(i + 5) * 360, rand(i + 9) * 40 - 20)), 0));\n"
        "}"))
    spots.parm("class").set(0)
    ice = g.node("copytopoints::2.0", "ice", [soft, spots])
    g.step(ice, "氷を浮かべる",
           "<code>box</code>（約 2 cm 角）を <code>polybevel</code> で 3 mm 丸め、溶けかけた角にする。"
           "Detail の <code>attribwrangle</code> で3つの点（水面のあたり）と、ばらばらの向き orient を作り、<code>copytopoints</code> で並べる。"
           "氷は水より少し軽いので、頭を少し出して浮く位置に置く。",
           cap="3つの氷。", shading="smooth", bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.11, 0.04))

    glass_m = g.mat("glass_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.5, transparency=1.0)
    water_m = g.mat("water_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.33, transparency=1.0,
                    transcolor=(0.8, 0.93, 0.95), transdist=0.2)
    ice_m = g.mat("ice_mat", basecolor=(1, 1, 1), rough=0.08, reflect=1.0, ior=1.31, transparency=1.0)
    final = g.node("merge", "drink", [g.assign(cup, glass_m, "assign_glass"), g.assign(water, water_m, "assign_water"),
                                      g.assign(ice, ice_m, "assign_ice")])
    g.step(final, "透明な材質を3つ当てる",
           "どれも <code>principledshader</code> で <strong>Transparency 1・Roughness ほぼ 0</strong>。違いは IOR（屈折率）だけで、"
           "<strong>ガラス 1.5・水 1.33・氷 1.31</strong>。水には Transmission Color をほんの少し青緑にする。"
           "透明な物は、後ろの明るい所と暗い所の境目が曲がって見えることで形が分かる。撮るときは、背景に明暗の差を作る。",
           cap="材質を当てた状態（ビューポートでは透けない）。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。ガラス・水・氷の屈折の違いで、それぞれの形が見える。",
           direction=(1.0, 0.25, 1.2), key=0.08, rim=0.5, dome=0.015, spp=16, margin=1.15, denoise=True,
           backdrop=(0.12, 0.125, 0.13), bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.105, 0.04))

    # ---- 落とし穴を測る ----
    def ml(divs):
        water.parm("divs").set(divs)
        return abs(sum(p.attribValue("volume") for p in liquid_ml.geometry().prims())) * 1e6

    v8 = ml(8)
    v24 = ml(24)
    ml(96)
    traps = [
        {"title": "Divisions が少ないと、水の量まで減る",
         "body": f"水の revolve の Divisions を 8 にすると {v8:.0f} ml、24 で {v24:.0f} ml、96 で {vol_ml:.0f} ml。"
                 "少ない分割では、円が内側の多角形になるので、見た目が角ばるだけでなく体積も小さく出る（実験118）。",
         "img": "", "cap": ""},
        {"title": "小さな物は、明かりを弱くする",
         "body": "このグラスは高さ 10 cm。ほかの実践と同じ明かり（キー 2.5・リム 10）で撮ると、画面が真っ白に飛んだ。"
                 "撮影用の明かりは物の大きさに合わせて近くに置かれるので、小さな物ほど強く当たる。キー 0.08・リム 0.5 まで下げて撮った。",
         "img": "", "cap": ""},
        {"title": "透明な物は、サンプル数を上げると時間が大きく延びる",
         "body": "はじめ 96 サンプルで撮ろうとしたら、25 分たっても終わらなかった。測ると、サンプルを 1 増やすごとに延びる時間が、"
                 "不透明な物の 6 倍だった（実験203）。16 サンプルにして、ざらつきはノイズ除去（OIDN）で消す。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "15個（材質3つ）"], ["水の量", f"{vol_ml:.0f} ml"]], traps=traps)


if __name__ == "__main__":
    main()
