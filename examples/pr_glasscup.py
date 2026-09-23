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

    turned = g.node("revolve::2.0", "glass_turn", [profile], divs=96)
    cup = g.node("reverse", "glass", [turned])   # 断面をたどった向きのせいで、面が内向きになる。外向きに戻す
    g.step(cup, "回してグラスにする",
           "<code>revolve</code> で断面を y 軸のまわりに1周回す。<strong>Divisions 96</strong>（96 等分）で、縁の丸みがなめらかになる。"
           "閉じた断面を回すので、中まで詰まった（厚みのある）ガラスになる。"
           "この断面のたどり方だと面が内向きになるので、<code>reverse</code> で外向きに戻す。"
           "向きが逆のままだと、Karma は光がガラスに入る所と出る所を取り違え、分厚いかたまりのように写った。",
           cap="厚い底と薄い縁のグラス。", shading="smoothwire")

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
    water_turn = g.node("revolve::2.0", "water_turn", [water_prof], divs=96)
    water = g.node("reverse", "water", [water_turn])   # グラスと同じく、面を外向きに戻す
    liquid_ml = g.node("measure::2.0", "water_volume", [water], measure="volume", attribname="volume")
    vol_ml = (sum(p.attribValue("volume") for p in liquid_ml.geometry().prims())) * 1e6 \
        if liquid_ml.geometry().findPrimAttrib("volume") else 0
    g.step(water, "水を入れる",
           f"内側の壁に沿った断面を、もう1つの Detail の <code>attribwrangle</code> で描き、同じく <code>revolve</code> で回して <code>reverse</code> で面を外向きにする。水面は高さ {WATER_TOP * 100:.0f} cm。"
           "壁とぴったり同じ面にすると、ガラスと水の境目がちらつくので、<strong>0.2 mm だけ内側</strong>にする。"
           f"<code>measure</code>（Volume）で測ると、水は {vol_ml:.0f} ml。",
           cap=f"グラスの中の水（{vol_ml:.0f} ml）。", shading="smooth")

    cube = g.node("box", "ice_block", size=(0.021, 0.018, 0.019))
    soft = g.node("polybevel::3.0", "melted_edges", [cube], offset=0.004, divisions=3)
    dense = g.node("remesh::2.0", "ice_mesh", [soft], targetsize=0.0012)
    lumpy = g.node("mountain::2.0", "ice_lumps", [dense], height=0.0018, elementsize=0.012, rough=0.5, oct=4)
    core = g.node("sphere", "cloudy_core", type="polymesh", rad=(0.006, 0.005, 0.0055), rows=12, cols=18)
    core_shape = g.node("mountain::2.0", "core_lumps", [core], height=0.002, elementsize=0.006)
    spots = g.node("attribwrangle", "ice_spots", snippet=(
        "// 氷5つの置き場所と向き。水面に寄り集まり、頭を少し出して浮く\n"
        f"vector places[] = {{{{-0.012, {WATER_TOP - 0.003}, 0.008}}, {{0.011, {WATER_TOP - 0.004}, 0.007}}, {{0.0, {WATER_TOP - 0.002}, -0.012}},"
        f" {{0.014, {WATER_TOP - 0.008}, -0.009}}, {{-0.013, {WATER_TOP - 0.009}, -0.008}}}};\n"
        "for (int i = 0; i < 5; i++) {\n"
        "    int p = addpoint(0, places[i]);\n"
        "    setpointattrib(0, 'orient', p, quaternion(radians(set(rand(i) * 50 - 25, rand(i + 5) * 360, rand(i + 9) * 50 - 25)), 0));\n"
        "    setpointattrib(0, 'pscale', p, fit01(rand(i + 3), 0.85, 1.1));\n"
        "}"))
    spots.parm("class").set(0)
    ice = g.node("copytopoints::2.0", "ice", [lumpy, spots])
    cores = g.node("copytopoints::2.0", "ice_cores", [core_shape, spots])
    g.step(ice, "氷を浮かべる",
           "本物の氷は、角が丸く、形がいびつで、真ん中が白く濁っている。<code>box</code>（約 2 cm 角）を <code>polybevel</code> で 4 mm 丸め、"
           "<code>remesh</code> で細かい網にしてから <code>mountain</code>（Height 1.8 mm）で面をわずかに波打たせる。"
           "中に、少しゆがんだ小さな <code>sphere</code> を入れて、濁った芯にする。"
           "Detail の <code>attribwrangle</code> で5つの点（水面に寄り集まる位置）と、ばらばらの向き orient・大きさ pscale を作り、"
           "<code>copytopoints</code> で氷と芯を並べる。氷は水より少し軽いので、頭を少し出して浮く。",
           cap="5つの氷。", shading="smooth", bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.11, 0.04))

    glass_m = g.mat("glass_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.5, transparency=1.0)
    water_m = g.mat("water_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.33, transparency=1.0,
                    transcolor=(0.8, 0.93, 0.95), transdist=0.2)
    ice_m = g.mat("ice_mat", basecolor=(1, 1, 1), rough=0.06, reflect=1.0, ior=1.31, transparency=1.0)
    cloudy = g.mat("ice_core_mat", basecolor=(0.92, 0.95, 0.97), rough=0.7, transparency=0.6, ior=1.0)
    final = g.node("merge", "drink", [g.assign(cup, glass_m, "assign_glass"), g.assign(water, water_m, "assign_water"),
                                      g.assign(ice, ice_m, "assign_ice"), g.assign(cores, cloudy, "assign_core")])
    g.step(final, "透明な材質を3つ当てる",
           "どれも <code>principledshader</code> で <strong>Transparency 1・Roughness ほぼ 0</strong>。違いは IOR（屈折率）だけで、"
           "<strong>ガラス 1.5・水 1.33・氷 1.31</strong>。水には Transmission Color をほんの少し青緑にする。"
           "氷の芯は白っぽく、Roughness 0.7・Transparency 0.6 で、光が散ってぼんやり白く見えるようにする。"
           "透明な物は、後ろの明るい所と暗い所の境目が曲がって見えることで形が分かる。撮るときは、背景に明暗の差を作る。",
           cap="材質を当てた状態（ビューポートでは透けない）。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。ガラス・水・氷の屈折の違いで、それぞれの形が見える。",
           direction=(1.0, 0.22, 1.2), key=0.08, rim=0.6, dome=0.03, spp=16, margin=1.2, denoise=True,
           backdrop=(0.2, 0.205, 0.215), backdrop_reflect=0.0, bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.105, 0.04))

    # ---- 落とし穴を測る ----
    def ml(divs):
        water_turn.parm("divs").set(divs)
        return sum(p.attribValue("volume") for p in liquid_ml.geometry().prims()) * 1e6

    water.bypass(True)
    flipped_ml = ml(96)
    water.bypass(False)
    v8 = ml(8)
    v24 = ml(24)
    ml(96)
    traps = [
        {"title": "Divisions が少ないと、水の量まで減る",
         "body": f"水の revolve の Divisions を 8 にすると {v8:.0f} ml、24 で {v24:.0f} ml、96 で {vol_ml:.0f} ml。"
                 "少ない分割では、円が内側の多角形になるので、見た目が角ばるだけでなく体積も小さく出る（実験118）。",
         "img": "", "cap": ""},
        {"title": "面の向きが逆だと、ガラスが分厚いかたまりに写る",
         "body": f"水の reverse を外して measure で体積を測ると {flipped_ml:.0f} ml（負）、入れると {vol_ml:.0f} ml。負の体積は、面が内向きになっている印。"
                 "最初の版はグラスも水も内向きのまま撮っていて、光の入り口と出口が逆になり、グラスが分厚いかたまりのように写った（下の「改訂の記録」）。",
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
