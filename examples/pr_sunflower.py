# -*- coding: utf-8 -*-
"""実践「ひまわりを咲かせる」— 種は黄金角（137.5度）で渦巻きに並べ、花びらは曲げた板を外向きにコピーする。

本物のひまわりの中心は、種が左右2方向の渦を巻いてすき間なく詰まっている。1粒ごとに 137.5度（黄金角）回して、
中心からの距離を √(番号) に比例させると、この並び（葉序）になる。花びらは舌のような形で、先が少し反る。

    hython examples/pr_sunflower.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("sunflower", "ひまわりを咲かせる",
                  "中心の種は、1粒ごとに 137.5度（黄金角）回して、中心からの距離を √番号 に比例させて並べる。"
                  "これだけで本物と同じ渦巻きになる。花びらは板を舌の形に曲げ、2重の輪に外向きにコピーする。",
                  tags=["モデリング", "VEX", "複製", "Karma"])
    g.shot_dir = (0.25, 0.55, 1.0)
    seeds = g.node("attribwrangle", "golden_spiral", snippet=(
        "// 黄金角の渦巻き。i 番目の種は、角度 i × 137.5度、中心からの距離 c × √i\n"
        "int n = chi('count');\n"
        "float golden = radians(137.508);\n"
        "for (int i = 0; i < n; i++) {\n"
        "    float r = chf('spacing') * sqrt(i);\n"
        "    float a = i * golden;\n"
        "    float y = 0.03 - r * r * 1.2;                                   // 中心が少し盛り上がった円盤\n"
        "    int p = addpoint(0, set(cos(a) * r, y, sin(a) * r));\n"
        "    // となりの花までの距離は間隔の約 1.7 倍（測った値 5.8 mm ÷ 3.4 mm）。半径をその半分にすると、すき間なく接する\n"
        "    setpointattrib(0, 'pscale', p, chf('spacing') * 0.85 * fit(r, 0, 0.12, 0.85, 1.05));\n"
        "    // 本物の中心は、色の輪になっている：真ん中は黄緑のつぼみ、その外は咲いた黄金色の小花（花粉）、いちばん外はこげ茶\n"
        "    float u = r / (chf('spacing') * sqrt(n));\n"
        "    vector bud = {0.42, 0.48, 0.1}, bloom = {0.95, 0.62, 0.08}, ripe = {0.13, 0.06, 0.02};\n"
        "    vector c = lerp(bud, bloom, smooth(0.2, 0.35, u));\n"
        "    c = lerp(c, ripe, smooth(0.55, 0.7, u));\n"
        "    setpointattrib(0, 'Cd', p, c * fit01(rand(i + 0.3), 0.8, 1.15));\n"
        "    // 盛り上がった面に垂直に立てる（面の傾きは高さの式を r で微分した −2.4r）\n"
        "    vector nrm = normalize(set(2.4 * cos(a) * r, 1, 2.4 * sin(a) * r));\n"
        "    vector4 q = dihedral({0, 1, 0}, nrm);\n"
        "    setpointattrib(0, 'orient', p, q);\n"
        "}"))
    seeds.parm("class").set(0)
    kit_spare(seeds, ints={"count": 1400}, spacing=0.0034)
    g.step(seeds, "種を黄金角で並べる",
           "何もつながない <code>attribwrangle</code>（Run Over は Detail）で、<strong>count = 1400</strong> 粒の種の点を作る。"
           "i 番目の粒は、角度 <strong>i × 137.508度</strong>（黄金角）、中心からの距離 <strong>spacing × √i</strong>。"
           "こうすると粒どうしがすき間なく詰まり、右回りと左回りの渦が浮かび上がる。本物のひまわりと同じ並び方。"
           "中心を少し盛り上げ、粒の大きさ pscale と色 Cd を付ける。色は本物と同じく3つの輪にする。"
           "真ん中は黄緑のつぼみ、その外は咲いた黄金色の小花、いちばん外はこげ茶。粒の向き orient は、盛り上がった面に垂直にする。",
           cap="1400 粒の渦巻き。", shading="wire", ui_parm="count",
           bbox=hou.BoundingBox(-0.14, -0.03, -0.14, 0.14, 0.04, 0.14))

    bump = g.node("tube", "floret", type="poly", rad=(1, 0.35), height=1.8, cols=6, cap=1, t=(0, 0.9, 0))
    disk = g.node("copytopoints::2.0", "seed_disk", [bump, seeds], targetattribs=1)
    disk.parm("applyto1").set("points")
    disk.parm("applyattribs1").set("Cd")
    g.step(disk, "小さな花を並べる",
           "ひまわりの中心は種ではなく、小さな筒の形の花（管状花）がびっしり詰まったもの。前の版は丸い粒を並べていたが、写真と比べると形が違った。"
           "先の細い六角の <code>tube</code>（下の半径 1・上 0.35・高さ 1.8）を <code>copytopoints</code> で点に並べる（大きさは pscale で決まる）。"
           "色を移すため、Target Attributes に「<strong>Apply to: Points</strong>」「Attributes: Cd」を足す（H21 は書かないと色が移らない）。",
           cap="渦巻きに詰まった種。", shading="smooth",
           bbox=hou.BoundingBox(-0.14, -0.03, -0.14, 0.14, 0.04, 0.14))

    blade = g.node("grid", "petal_blank", orient="zx", size=(1, 1), rows=6, cols=16, t=(0.5, 0, 0))
    shape = g.node("attribwrangle", "petal_shape", [blade], snippet=(
        "// 板を花びらの形にする。u = 根元 0 → 先 1。本物の花びらは先がとがり、縦に筋があり、少し波打つ\n"
        "float u = clamp(@P.x, 0, 1);\n"
        "float w = chf('width') * pow(sin(PI * fit(u, 0, 1, 0.1, 0.85)), 0.7) * pow(1 - u, 0.35);   // 先に向かってとがる\n"
        "float side = @P.z;                                                 // −0.5〜0.5（板の横方向）\n"
        "@P.z = side * w * 2;\n"
        "@P.x = u * chf('length');\n"
        "@P.y = chf('curl') * u * u - abs(@P.z) * 0.3 + sin(u * PI * 3) * 0.002;   // 先が反り、縦に溝、小さく波打つ\n"
        "float vein = 0.88 + 0.12 * cos(side * PI * 14);                   // 縦の筋\n"
        "v@Cd = lerp({0.95, 0.55, 0.02}, {1.0, 0.8, 0.06}, smooth(0, 0.35, u)) * vein;"))
    blade.parm("rows").set(12)
    blade.parm("cols").set(24)
    kit_spare(shape, width=0.03, length=0.12, curl=0.012)
    g.step(shape, "花びらを1枚作る",
           "<code>grid</code>（12 × 24 に割る）を細長い板にし、<code>attribwrangle</code> で形を作る。"
           "根元から先への位置 u を使い、幅を <strong>sin</strong> と <strong>(1 − u)</strong> の掛け算にして、先がとがった形にする（本物の花びらは先がとがる）。"
           "高さを <strong>curl × u²</strong> で先ほど少し反らせ、<code>sin</code> で小さく波打たせる。長さ 12 cm・幅 3 cm。"
           "色は根元が濃い黄色、先が明るい黄色で、横方向の <code>cos</code> で細い縦の筋を付ける。",
           cap="先のとがった、筋のある花びら。", shading="smoothwire",
           bbox=hou.BoundingBox(0, -0.03, -0.05, 0.14, 0.03, 0.05))

    ring = g.node("attribwrangle", "petal_ring", snippet=(
        "// 花びらの付け根を2重の輪に並べる。外の輪は、内の輪の間にくるよう半分ずらす\n"
        "int n = chi('count');\n"
        "for (int layer = 0; layer < 2; layer++) {\n"
        "    for (int i = 0; i < n; i++) {\n"
        "        float a = (i + layer * 0.5) * 2 * PI / n + (rand(i + layer * 50) - 0.5) * 0.08;\n"
        "        float r = chf('radius') - layer * 0.006;\n"
        "        int p = addpoint(0, set(cos(a) * r, -0.02 - layer * 0.006, sin(a) * r));\n"
        "        // 外向き（花びらの x）を半径の向きに合わせ、少し上へ傾ける。外の輪ほど下がる\n"
        "        float lift = radians(fit01(rand(i * 3 + layer), 4, 18) - layer * 10);\n"
        "        vector out = set(cos(a), 0, sin(a));\n"
        "        matrix3 m = maketransform(cross(out, {0, 1, 0}), {0, 1, 0});\n"
        "        rotate(m, lift, cross({0, 1, 0}, out));\n"
        "        setpointattrib(0, 'orient', p, quaternion(m));\n"
        "        setpointattrib(0, 'pscale', p, fit01(rand(i * 7 + layer), 0.85, 1.1));\n"
        "    }\n"
        "}"))
    ring.parm("class").set(0)
    kit_spare(ring, ints={"count": 30}, radius=0.125)
    petals = g.node("copytopoints::2.0", "petals", [shape, ring])
    g.step(petals, "花びらを2重の輪に並べる",
           "もう1つの Detail の <code>attribwrangle</code> で、種の円盤のまわり（半径 12.5 cm）に <strong>30 個 × 2 段</strong>の点を置く。"
           "外の段は内の段の間にくるよう半分ずらす。点ごとの向き <strong>orient</strong> は、花びらの長い向きを外へ向け、"
           "4〜18度上へ傾ける（外の段は 10度下げる）。大きさ pscale もばらつかせる。<code>copytopoints</code> で花びらを並べる。",
           cap="60 枚の花びら。", shading="smooth", bbox=hou.BoundingBox(-0.28, -0.08, -0.28, 0.28, 0.08, 0.28))

    bract_shape = g.node("attribwrangle", "bract_shape", [blade], snippet=(
        "// 萼（がく）：花びらの後ろに見える、緑の短い葉。先が細くとがる\n"
        "float u = clamp(@P.x, 0, 1);\n"
        "@P.z *= 0.022 * 2 * pow(1 - u, 0.8) * pow(sin(PI * fit(u, 0, 1, 0.15, 1)), 0.5);\n"
        "@P.x = u * 0.05;\n"
        "@P.y = -0.01 * u * u;\n"
        "v@Cd = {0.16, 0.3, 0.06};"))
    bract_pts = g.node("attribwrangle", "bract_ring", snippet=(
        "// 花びらより少し内側・下に、萼の輪を置く。少し下へ向ける\n"
        "int n = 26;\n"
        "for (int i = 0; i < n; i++) {\n"
        "    float a = (i + 0.25) * 2 * PI / n;\n"
        "    int p = addpoint(0, set(cos(a) * 0.115, -0.04, sin(a) * 0.115));\n"
        "    vector out = set(cos(a), 0, sin(a));\n"
        "    matrix3 m = maketransform(cross(out, {0, 1, 0}), {0, 1, 0});\n"
        "    rotate(m, radians(-15), cross({0, 1, 0}, out));\n"
        "    setpointattrib(0, 'orient', p, quaternion(m));\n"
        "}"))
    bract_pts.parm("class").set(0)
    bracts = g.node("copytopoints::2.0", "bracts", [bract_shape, bract_pts])
    back = g.node("sphere", "flower_back", type="polymesh", rad=(0.13, 0.04, 0.13), rows=12, cols=36, t=(0, -0.052, 0))
    stem = g.node("tube", "stem", type="poly", rad=(0.012, 0.015), height=0.9, cols=16, t=(0, -0.49, 0))
    seed_mat = g.mat("seed_mat", basecolor=(1, 1, 1), rough=0.95, reflect=0.1)   # つやがあると、小さな粒が空を映して白く光る
    petal_mat = g.mat("petal_mat", basecolor=(1, 1, 1), rough=0.5, sheen=0.3)
    green = g.mat("stem_mat", basecolor=(0.12, 0.25, 0.05), rough=0.6)
    leafy = g.mat("bract_mat", basecolor=(1, 1, 1), rough=0.6, sheen=0.2)
    bloom = g.node("merge", "sunflower", [g.assign(disk, seed_mat, "assign_seed"), g.assign(petals, petal_mat, "assign_petal"),
                                          g.assign(bracts, leafy, "assign_bract"),
                                          g.assign(back, green, "assign_back"), g.assign(stem, green, "assign_green")])
    final = g.node("xform", "face_camera", [bloom], r=(62, 0, 0))
    g.step(final, "茎と裏を付けて、こちらへ向ける",
           "花びらの後ろに、緑の萼（がく）を同じ作り方で 26 枚、少し下へ向けて並べる。"
           "花の裏に平たい <code>sphere</code>、下に細い <code>tube</code> の茎を付け、どちらも緑にする（本物の裏は緑）。種と花びらは Base Color を白にして"
           "点の色 Cd をそのまま使う。種は <strong>Roughness 0.95</strong> でつやを消す（つやがあると、小さな粒1つ1つが空を映して白く光る）。花びらは Sheen 0.3。最後に <code>xform</code> で 62度起こして、花をカメラのほうへ向ける。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。種の渦巻きと、2重の花びら。", direction=(0.15, 0.1, 1.0),
           key=2.2, rim=3.0, dome=0.18, dome_color=(0.8, 0.9, 1.0), spp=64, margin=1.02, key_color=(1.0, 0.93, 0.8),
           backdrop=(0.1, 0.22, 0.38), bbox=hou.BoundingBox(-0.3, -0.28, -0.12, 0.3, 0.3, 0.3))

    # ---- 落とし穴を測る ----
    import math

    def min_gap(angle_deg):
        seeds.parm("snippet").set(seeds.parm("snippet").eval().replace("137.508", str(angle_deg)))
        pts = [p.position() for p in seeds.geometry().points()][200:600]
        seeds.parm("snippet").set(seeds.parm("snippet").eval().replace(str(angle_deg), "137.508"))
        best = []
        for i, a in enumerate(pts):
            best.append(min((a - b).length() for j, b in enumerate(pts) if j != i))
        return sum(best) / len(best)

    gap_golden = min_gap("137.508")
    gap_140 = min_gap("140.0")
    gap_120 = min_gap("120.0")
    traps = [
        {"title": "角度が少し違うだけで、すき間ができる",
         "body": f"となりの粒までの距離の平均（200〜600 番の粒）は、137.508度で {gap_golden * 1000:.2f} mm、140度で {gap_140 * 1000:.2f} mm、"
                 f"120度で {gap_120 * 1000:.2f} mm。黄金角からずれると、粒が何本かの線の上に固まり、線と線の間がすき間になる。"
                 "距離が縮むのは、固まった粒どうしが近づくため。",
         "img": "", "cap": ""},
        {"title": "種の色は Points に移す",
         "body": "copytopoints の Target Attributes を「Apply to: Primitives」にすると、面には Cd が付いている（ビューポートでは茶色）のに、"
                 "Karma では種が白く写った。「Apply to: Points」にすると茶色に写った。Karma で撮るものは、色を点に移しておく。",
         "img": "", "cap": ""},
        {"title": "距離は √番号 に比例させる",
         "body": "中心からの距離を番号そのものに比例させると、外へ行くほど粒の間が広がってしまう。√番号 にすると、"
                 "円の面積（半径の2乗）が番号に比例して増えるので、どこでも同じ込み具合になる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "15個（材質3つ）"], ["種", "1400粒"], ["花びら", "60枚"]], traps=traps)


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
