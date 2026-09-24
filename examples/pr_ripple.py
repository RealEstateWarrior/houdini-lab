# -*- coding: utf-8 -*-
"""実践「水たまりに雨の波紋」— 雨粒が落ちた所から輪が広がり、弱まって消えるのを、VEX の式だけで動かす。

本物の波紋は、落ちた点から同心円の輪が一定の速さで広がり、外へ行くほど・時間がたつほど弱くなる。
輪がいくつも重なると、水面がちらちら光る。シミュレーションを使わず「輪の式を雨粒の数だけ足す」で作れる。

    hython examples/pr_ripple.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

LAST = 96     # 4 秒
HERO_F = 60


def main():
    import hou
    hou.playbar.setFrameRange(1, LAST)
    g = kit.Guide("ripple", "水たまりに雨の波紋",
                  "雨粒が落ちた所から輪が広がり、弱まって消える。これを「広がる輪の式」を雨粒の数だけ足して作る。"
                  "時間 @Time を使うので、再生すると勝手に動く。シミュレーションは使わない。",
                  tags=["エフェクト", "VEX", "水", "Karma"])
    g.shot_dir = (0.5, 0.45, 1.2)
    water = g.node("grid", "puddle", size=(2.0, 1.4), rows=280, cols=400)
    g.step(water, "水面を細かい網にする",
           "<code>grid</code>（2 × 1.4 m）を <strong>Rows 280・Columns 400</strong> に割る。波紋の山と谷は数 mm しか離れていないので、"
           "網が粗いと輪が描けない（升は約 5 mm）。",
           cap="細かく割った水面。", shading="wire", bbox=hou.BoundingBox(-1, -0.05, -0.7, 1, 0.05, 0.7))

    rings = g.node("attribwrangle", "rain_rings", [water], snippet=(
        "// 雨粒1つ1つについて、落ちた時刻と場所を乱数で決め、そこから広がる輪の高さを足す\n"
        "int drops = chi('drops');\n"
        "float speed = chf('speed');        // 輪が広がる速さ（m/秒）\n"
        "float wave = chf('wavelength');    // 山から山までの長さ\n"
        "float h = 0;\n"
        "for (int i = 0; i < drops; i++) {\n"
        "    float t0 = rand(i * 3.1) * chf('span');                          // 落ちた時刻（秒）\n"
        "    float age = @Time - t0;\n"
        "    if (age < 0 || age > 1.5) continue;                              // まだ落ちていない・もう消えた\n"
        "    vector2 c = set(fit01(rand(i * 7.3), -1, 1), fit01(rand(i * 5.9), -0.7, 0.7));\n"
        "    float d = length(set(@P.x, @P.z) - c);                          // 落ちた点からの距離\n"
        "    float front = speed * age;                                       // いちばん外の輪の位置\n"
        "    if (d > front) continue;                                         // 輪がまだ届いていない\n"
        "    float fade = exp(-age * chf('fade')) * exp(-(front - d) / (wave * 2.5));   // 時間と、輪の後ろほど弱く\n"
        "    h += chf('amp') * fade * sin(2 * PI * (d - front) / wave);\n"
        "}\n"
        "@P.y += h;"))
    kit_spare(rings, ints={"drops": 160}, speed=0.22, wavelength=0.024, fade=2.0, amp=0.003, span=4.0)
    t0 = time.perf_counter()
    hou.setFrame(HERO_F)
    rings.geometry()
    cook_sec = time.perf_counter() - t0
    g.step(rings, "雨粒ごとに、広がる輪を足す",
           "<code>attribwrangle</code> で、点ごとに <strong>drops = 160</strong> 個の雨粒を順に見る。雨粒 i の落ちた時刻と場所は "
           "<code>rand(i …)</code> で決める（同じ i なら毎回同じ値になるので、フレームが進んでも同じ雨粒のまま）。"
           "落ちてからの時間 age が分かれば、いちばん外の輪は <strong>speed × age</strong>（speed = 0.22 m/秒）の所にある。"
           "その内側を <strong>sin</strong> で波打たせ（wavelength = 2.4 cm、高さ amp = 3 mm）、時間がたつほど、輪の後ろほど弱くする。"
           "全部の雨粒の高さを足して、点を上下に動かす。時間は <strong>@Time</strong>（秒）なので、再生すると動く。",
           cap=f"フレーム {HERO_F}。いくつもの輪が重なる。", shading="smooth", ui_parm="drops",
           bbox=hou.BoundingBox(-1, -0.05, -0.7, 1, 0.05, 0.7))

    shape = g.node("attribwrangle", "puddle_shape", [rings], snippet=(
        "// 水たまりの縁を不規則にする。中心からの距離をノイズでゆがめ、外側の面を消す\n"
        "vector c = getbbox_center(0);\n"
        "vector q = (@P - c) * {1.0, 0, 1.4};\n"
        "float edge = 0.78 + (noise(@P * 2.5 + 4.1) - 0.5) * 0.5;\n"
        "if (length(q) > edge) removeprim(0, @primnum, 1);"))
    shape.parm("class").set(1)
    g.step(shape, "水たまりの形に切る",
           "<code>attribwrangle</code> を Primitives で回し、中心からの距離が「ノイズでゆがめた半径」より遠い面を消す。"
           "四角い板が、縁のでこぼこした水たまりの形になる。",
           cap="縁が不規則な水たまり。", shading="smooth", bbox=hou.BoundingBox(-1, -0.05, -0.7, 1, 0.05, 0.7))
    clear = g.mat("water_mat", basecolor=(1, 1, 1), rough=0.02, reflect=1.0, ior=1.33, transparency=1.0,
                  transcolor=(0.55, 0.52, 0.45), transdist=0.02)
    road_grid = g.node("grid", "asphalt", size=(12, 12), rows=400, cols=400, t=(0, -0.004, 0))
    road = g.node("attribwrangle", "asphalt_grain", [road_grid], snippet=(
        "// アスファルトの粒のざらつきと、濡れて濃くなった色のむら\n"
        "@P.y += noise(@P * 60) * 0.002;\n"
        "v@Cd = {0.06, 0.06, 0.065} * fit(noise(@P * 25), 0.3, 0.7, 0.6, 1.4);"))
    tar = g.mat("asphalt_mat", basecolor=(1, 1, 1), rough=0.28, reflect=0.8)
    sky_card = g.node("grid", "overcast_sky", orient="xy", size=(40, 14), rows=2, cols=2, t=(0, 4, -9))
    sky_m = g.mat("sky_mat", basecolor=(0, 0, 0), emitint=1.0, emitcolor=(0.75, 0.8, 0.86))
    final = g.node("merge", "rainy_street", [g.assign(shape, clear, "assign_water"), g.assign(road, tar, "assign_asphalt"),
                                             g.assign(sky_card, sky_m, "assign_sky")])
    g.step(final, "水・濡れた地面・空を置く",
           "水面は <code>principledshader</code> で <strong>Transparency 1・IOR 1.33</strong>（水）・Roughness 0.02。"
           "水たまりの見え方は、ほとんど「空の映り込み」で決まる。写真の雨の水たまりは明るい曇り空を映していて、波紋は映り込みのゆがみとして白い輪に見える。"
           "そこで、奥に大きな板を立てて明るい灰色に光らせ（曇り空）、低い角度から撮って水面に映す。"
           "下には 12 m 四方の <code>grid</code> を置き、<code>attribwrangle</code> で粒のざらつきと濡れた色のむらを付けたアスファルトにする（雨で濡れているので Roughness 0.28 で照り返す）。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム {HERO_F}）。曇り空を映した水たまりに、重なる波紋。",
           direction=(0.05, 0.2, 1.0), key=0.0, rim=0.0, dome=0.15, dome_color=(0.7, 0.75, 0.8), spp=32, margin=0.75,
           frame=HERO_F, floor=False, denoise=True,
           bbox=hou.BoundingBox(-0.9, -0.01, -0.6, 0.9, 0.01, 0.6))
    g.anim(rings, (1, LAST), "雨粒が落ちて、輪が広がって消える（96 フレーム＝4 秒）。",
           bbox=hou.BoundingBox(-1, -0.05, -0.7, 1, 0.05, 0.7), direction=(0.3, 0.9, 0.6), shading="smooth")

    # ---- 落とし穴を測る ----
    rings.parm("drops").set(320)
    t1 = time.perf_counter()
    rings.parm("amp").set(0.00301)   # 同じ設定では計算し直さないので、わずかに変える（実験173）
    rings.geometry()
    cook2 = time.perf_counter() - t1
    rings.parm("drops").set(160)
    rings.parm("amp").set(0.003)
    water.parm("rows").set(70)
    water.parm("cols").set(100)
    coarse_h = max(abs(p.position()[1]) for p in rings.geometry().points())
    water.parm("rows").set(280)
    water.parm("cols").set(400)
    fine_h = max(abs(p.position()[1]) for p in rings.geometry().points())
    traps = [
        {"title": "雨粒の数だけ計算が重くなる",
         "body": f"点 {281 * 401:,} 個 × 雨粒 160 個で、1フレームの計算は {cook_sec:.2f} 秒。雨粒を 320 個にすると {cook2:.2f} 秒。"
                 "どの点も全部の雨粒を見るので、雨粒の数に比例して重くなる。",
         "img": "", "cap": ""},
        {"title": "網が粗いと、輪が描けない",
         "body": f"Rows 70・Columns 100（升 2 cm）にすると、いちばん高い波は {coarse_h * 1000:.2f} mm、細かい網では {fine_h * 1000:.2f} mm。"
                 "波長 2.4 cm に対して升が大きいと、点が山と谷を飛び越えてしまい、輪の形にならない。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "6個（材質2つ）"], ["雨粒", "160個（4秒）"], ["1フレームの計算", f"{cook_sec:.2f}秒"]],
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
