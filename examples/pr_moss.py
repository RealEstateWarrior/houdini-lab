# -*- coding: utf-8 -*-
"""実践「苔むした石を作る」— 石の上を向いた面にだけ、まだらに苔を生やす。

本物の苔は、雨と光の当たる上の面に厚く、縁ではまだらに薄くなる。近くで見ると短い毛の集まりで、ビロードのように見える。
それを「上を向いた度合い × まだらのノイズ」で生える場所を決め、そこに短い線を密に立てて真似る。

    hython examples/pr_moss.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

STRANDS = 160000


def main():
    import hou
    g = kit.Guide("moss", "苔むした石を作る",
                  "石の上を向いた面にだけ、まだらに苔を生やす。「上を向いている度合い」と「まだらのノイズ」を掛け合わせて"
                  "生える場所を決め、そこに短い毛を密に立てる。色だけで塗るより、毛を立てたほうが苔のふかふかした感じが出る。",
                  tags=["モデリング", "VEX", "散布", "Karma"])
    g.shot_dir = (0.9, 0.55, 1.2)
    base = g.node("sphere", "base", type="polymesh", rows=80, cols=160, rad=(0.55, 0.32, 0.45))
    big = g.node("mountain::2.0", "big_lumps", [base], height=0.16, elementsize=0.45, rough=0.4)
    fine = g.node("mountain::2.0", "fine_detail", [big], height=0.04, elementsize=0.07, rough=0.6, oct=6)
    stone = g.node("normal", "face_dir", [fine])
    g.step(stone, "石の形を作る",
           "<code>sphere</code>（Polygon Mesh、半径 0.55 × 0.32 × 0.45、Rows 80・Columns 160）をつぶれた丸石にする。"
           "<code>mountain</code> を2つ重ね、1つ目（<strong>Height 0.16・Element Size 0.45</strong>）で大きなうねり、"
           "2つ目（<strong>Height 0.04・Element Size 0.07</strong>）で細かいでこぼこを付ける。"
           "最後の <code>normal</code> で面の向き（N）を計算し直す。次の段で「上を向いているか」を見るのに使う。",
           cap="川原にありそうな、平たい丸石。", shading="smooth", ui_parm="height")

    mask = g.node("attribwrangle", "where_moss", [stone], snippet=(
        "// 上を向いている度合い。真上（N.y = 1）で 1、横向き（N.y = 0.2 以下）で 0\n"
        "float up = smooth(chf('side'), chf('top'), v@N.y);\n"
        "// まだらにするノイズ。0.4〜0.6 の間でなめらかに 0 から 1 へ変わる\n"
        "float patch = smooth(0.4, 0.6, noise(@P * chf('patch_size') + 3.7));\n"
        "f@moss = clamp(up * (0.35 + patch), 0, 1);\n"
        "// 苔のない所は灰色の石（ノイズで濃淡を付ける）、苔の所は下地の濃い緑\n"
        "vector rock = {0.11, 0.105, 0.1} * fit(noise(@P * 9.0), 0.3, 0.7, 0.65, 1.25);  // 石にも濃淡のむら\n"
        "// 地衣類（石に付く白っぽい斑点）。写真の苔むした岩には、苔の無い所にこれがまだらに付いている\n"
        "float lichen = smooth(0.6, 0.66, noise(@P * 14 + 7.7));\n"
        "rock = lerp(rock, {0.42, 0.43, 0.38}, lichen * 0.8);\n"
        "v@Cd = lerp(rock, {0.06, 0.1, 0.03}, f@moss);"))
    kit_spare(mask, side=0.2, top=0.75, patch_size=4.0)
    g.step(mask, "苔の生える場所を決める",
           "<code>attribwrangle</code> で、点ごとに <strong>moss</strong>（0〜1）を作る。"
           "まず <strong>N.y</strong>（面が上を向いている度合い）が 0.2 以下なら 0、0.75 以上なら 1 にする。"
           "これにノイズで作ったまだらを掛けると、上の面は厚く、縁はまだらに薄くなる。"
           "色 <strong>Cd</strong> も、moss に合わせて灰色から濃い緑へ変える（毛の根元が見える所の色）。石は濃い灰色にし、別のノイズで濃淡を付け、苔の無い所には白っぽい地衣類の斑点を足す（前の版は石が明るすぎて、白い泡のように見えた）。",
           cap="上の面が緑、縁はまだら。", shading="smooth", ui_parm="patch_size")

    pts = g.node("scatter::2.0", "roots", [mask], npts=STRANDS, usedensityattrib=1, densityattrib="moss")
    g.step(pts, "苔の毛の根元をまく",
           f"<code>scatter</code> で <strong>{STRANDS:,} 個</strong>の点をまく。<strong>Use Density Attribute</strong> を入れて "
           "<strong>Density Attribute を moss</strong> にすると、moss の大きい所ほど点が多く、0 の所には1つも出ない。"
           "点は、面の N などの属性を引き継ぐ。",
           cap="苔の場所にだけ点が集まる。", shading="wire", ui_parm="densityattrib")

    hair = g.node("attribwrangle", "grow_strands", [pts], snippet=(
        "// 点ごとに、面の向き（N）へ短い毛を1本立てる。少しずつ傾きと長さを変えて、揃いすぎないようにする\n"
        "vector tilt = (vector(rand(@ptnum * 3.1 + 1)) - 0.5) * 0.9;\n"
        "vector dir = normalize(normalize(v@N) + tilt);\n"
        "float len = chf('length') * fit01(rand(@ptnum + 7), 0.5, 1.3);\n"
        "float mix = rand(@ptnum + 11);\n"
        "vector tip_col = lerp({0.22, 0.42, 0.04}, {0.42, 0.52, 0.08}, mix);  // 先は明るい黄緑\n"
        "int prim = addprim(0, 'polyline');\n"
        "for (int i = 0; i < 3; i++) {\n"
        "    float t = i / 2.0;\n"
        "    int p = addpoint(0, @P + dir * len * t + {0, -1, 0} * len * 0.15 * t * t);  // 先が少し垂れる\n"
        "    setpointattrib(0, 'Cd', p, lerp({0.05, 0.09, 0.02}, tip_col, t));\n"
        "    setpointattrib(0, 'width', p, lerp(chf('root_width'), chf('root_width') * 0.3, t));\n"
        "    addvertex(0, prim, p);\n"
        "}\n"
        "removepoint(0, @ptnum);"))
    kit_spare(hair, length=0.008, root_width=0.0012)
    g.step(hair, "短い毛を立てる",
           "もう1つの <code>attribwrangle</code> で、点ごとに3つの点をつないだ短い線（毛）を作る。"
           "向きは面の向き N に、ランダムな傾きを少し足したもの。長さは <strong>length = 0.008</strong>（8 mm）を 50〜130% にばらつかせ、"
           "先を少しだけ下へ垂らす。根元は暗い緑、先は明るい黄緑にし、太さ <strong>width</strong> は根元 1.2 mm から先へ細くする。写真の岩の苔は短く密なビロードのようなので、前の版（1.4 cm・9 万本）より短く多くした。"
           "最後に元の点を消す。",
           cap="石の上に、短い毛がびっしり立つ。", shading="smooth", ui_parm="length")

    rock_mat = g.mat("stone_mat", basecolor=(1, 1, 1), rough=0.85, reflect=0.3)
    moss_mat = g.mat("moss_mat", basecolor=(1, 1, 1), rough=0.6, reflect=0.15, sheen=0.6)
    final = g.node("merge", "mossy_stone", [g.assign(mask, rock_mat, "assign_stone"), g.assign(hair, moss_mat, "assign_moss")])
    g.step(final, "材質を当てて合わせる",
           "石と苔に別々の <code>principledshader</code> を当てる。どちらも Base Color を白にしておくと、"
           "点の色 Cd がそのまま色になる（Use Point Color が既定で入っている）。石は Roughness 0.85 でつやを消し、"
           "苔は <strong>Sheen 0.6</strong> で、毛の表面がふわっと明るく光る感じを足す。<code>merge</code> で石と苔を1つにする。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。上の面だけが苔に覆われ、縁はまだらに石がのぞく。", direction=(0.9, 0.5, 1.15),
           key=1.1, rim=2.5, dome=0.25, spp=48, margin=1.12, backdrop=(0.07, 0.055, 0.04), denoise=True,
           key_color=(1.0, 0.95, 0.85))

    # ---- 落とし穴を測る ----
    n_strands = len(hair.geometry().prims())

    def moss_share():
        vals = mask.geometry().pointFloatAttribValues("moss")
        return sum(1 for v in vals if v > 0.5) / len(vals)

    with_n = moss_share()
    stone.bypass(True)
    has_n = mask.inputs()[0].geometry().findPointAttrib("N") is not None
    without_n = moss_share() if has_n else None
    stone.bypass(False)
    if without_n is None:
        n_body = ("<code>normal</code> を外すと、mountain の出力には N が無い（測った）。wrangle の v@N は 0 になり、"
                  "N.y で決める苔の場所が1つも出ない。形を変えたあとは、N を作り直してから向きを読む。")
    else:
        n_body = (f"<code>normal</code> を外すと、moss が 0.5 を超える点は全体の {without_n:.0%}（入れたときは {with_n:.0%}）。"
                  "形を変える前の向きで判定されるので、こぶの上や傾いた面の苔がずれる。")
    traps = [
        {"title": "形を変えたら、N を作り直す",
         "body": n_body, "img": "", "cap": ""},
        {"title": "Force Total Count は「苔のある所にだけ」まかれる",
         "body": f"Density Attribute を使っても、点の総数は Force Total Count のまま（{n_strands:,} 本）。"
                 "苔の場所が狭いと、同じ数が狭い所に詰まって濃くなる。広く生やすなら数も増やす。",
         "img": "", "cap": ""},
        {"title": "毛の数が重さを決める",
         "body": f"{n_strands:,} 本の毛は、点にすると {n_strands * 3:,} 個。Karma で 1280×720 を撮るのにかかった時間は上の表のとおり。"
                 "試すうちは STRANDS を減らして速く回し、最後に戻す。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "12個（材質2つ）"], ["毛の数", f"{n_strands:,}本"]], traps=traps)


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
