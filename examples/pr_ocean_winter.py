# -*- coding: utf-8 -*-
"""実践「夕暮れの海の波を作る」のもう一つの版 — 冬の朝の七里ヶ浜（2026-09-24）。

砂浜に立って、崩れる波の列・波打ち際の泡・濃い青空・高い太陽のきらめきを撮る。
参考は、読者が七里ヶ浜の砂浜から撮った冬の朝の写真 5 枚。夕暮れ版（pr_ocean.py）の作りに、砂浜・崩れる波と泡・太陽の光を足す。

    hython examples/pr_ocean_winter.py
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

FRAME = 30
SH = 7.0             # カメラから波打ち際（静かな水面と砂が交わる所）までの距離（m）
SLOPE = 0.035        # 砂浜の傾き
EYE = 1.5            # 砂の上の目の高さ（m）
NEAR, FAR = 3.0, 8000.0
SUN_EL, SUN_AZ = 15.0, -12.0      # 太陽の高さと向き（度。左がマイナス）
SKY_R = 20000.0
SUN_POWER = 250000.0
SPECTRA = (("swell", 200, 5, 0.5, 10, 0.5), ("wind_chop", 23, 6, 1.3, -30, 0.7), ("ripples", 4.7, 7, 1.5, 20, 2.4),
           ("fine_ripples", 1.9, 5, 1.3, -40, 2.4))

SURF = """// 岸へ寄せて崩れる波の列と、泡（rest は板を広げた直後の位置）
float t = @Time;
float s = -v@rest.z - {SH};                    // 波打ち際から沖へ何 m か
// 遠くのさざ波は画の 1 画素より細かく、残すと規則的な縞になる。カメラから 25〜90 m で消す
@P = v@before_ripples + (@P - v@before_ripples) * (1 - smooth(25, 90, -v@rest.z));
// 沖の波（前の段の上下）は、浅い岸の近くでは半分ほどに弱める
@P = v@rest + (@P - v@rest) * lerp(0.45, 1.0, smooth(0, 70, s));
// 岸へ進む波の列。浅い所ほど波は遅く、間が詰まる（沖で長さ 30 m → 岸で 12 m）。周期は 8 秒
float T = 8;
float bend = 0.8 * noise(set(v@rest.x / 70, 3.1, 0)) - 0.4;
// 位相は「岸からの距離を波の長さで割ったもの」を足し上げる。長さが s で変わるので、式で積分した形にする
float L0 = 12, L1 = 30, S1 = 80;                 // 岸で 12 m、沖 80 m で 30 m
float ss = clamp(s, 0, S1);
float k = (S1 / (L1 - L0)) * log((L0 + (L1 - L0) * ss / S1) / L0) + max(s - S1, 0) / L1;
float ph = 2 * M_PI * (k + t / T) + bend * 6;
float sb = 30 + 12 * (noise(set(v@rest.x / 45, 7.7, 0)) - 0.5);   // 崩れ始める所（沖から 24〜36 m）
float a = fit(s, sb, 160, 0.6, 0.12);            // 沖から寄るほど高く
if (s < sb) a = 0.6 * fit(s, -2, sb, 0.15, 0.5); // 崩れたあとは低く
a *= 0.75 + 0.5 * noise(set(v@rest.x / 30, 1.3, t * 0.05));
float c = 0.5 + 0.5 * cos(ph - 0.9 * sin(ph)); // 岸側が切り立つ形
@P.y += a * (pow(c, 2.2) - 0.25) * smooth(-3, 3, s);
// 泡: 本物の動画では、崩れた波頭から岸まで、岸と平行な細い泡の筋が何本も重なる
float u = ph / (2 * M_PI); u -= floor(u);       // 波頭が通ってからの時間（0〜1）
float zone = (1 - smooth(sb - 4, sb + 3, s)) * smooth(-4, -0.5, s);   // 崩れる所から岸まで
vector q = set(v@rest.x, 0, -s + t * 1.2);      // 泡の模様は岸へ流す
// 岸と平行な筋: 横（x）にはゆっくり、奥行きにはすばやく変わるノイズの「尾根」
float n1 = 1 - abs(noise(set(q.x * 0.12, q.z * 1.6, 0.3)) * 2 - 1);
float n2 = 1 - abs(noise(set(q.x * 0.35, q.z * 4.0, 5.1)) * 2 - 1);
float streak = smooth(0.8, 0.97, n1) + 0.6 * smooth(0.86, 0.98, n2);
float patch = smooth(0.35, 0.65, noise(set(q.x * 0.08, q.z * 0.25, 9.0)));   // 泡の濃い所と薄い所
float brk = 0.6 * noise(set(v@rest.x / 9, t * 0.2, 2.0)) + 0.4 * noise(set(v@rest.x / 2.3, t * 0.3, 4.0));   // 波頭の泡のちぎれ方（2 つの大きさを混ぜて不規則に）
float crest = smooth(0.88, 0.99, c) * zone * smooth(0.3, 0.6, brk);
float trail = exp(-u * 2.2) * zone;              // 波頭が通ったあと、だんだん薄れる
float F = crest + trail * streak * (0.35 + 0.65 * patch) + 0.15 * zone * streak * patch;
f@foam = clamp(F, 0, 1);
// 水の色: 沖は深い青緑。岸近くの薄い水は下の砂が透けて、砂の暗い茶色に寄る
vector deep = lerp({{0.02, 0.028, 0.03}}, {{0.004, 0.016, 0.028}}, smooth(1, 12, s));
v@Cd = lerp(deep, {{0.72, 0.75, 0.77}}, f@foam);"""

SKY = """// 冬の澄んだ青空。水平線だけ白くかすむ
vector d = normalize(@P);
vector s = normalize({SD});
float h = max(d.y, 0);
float c = max(dot(d, s), 0);
vector col = lerp({{0.36, 0.52, 0.78}}, {{0.012, 0.05, 0.28}}, pow(fit(h, 0, 0.5, 0, 1), 0.35));
col += {{0.9, 0.92, 0.95}} * (1 - smooth(0.0, 0.012, h)) * 0.3;
col += {{1.0, 0.98, 0.92}} * (pow(c, 600) * 0.3 + pow(c, 5000) * 3);
// 水平線の少し上に、横に長い薄い雲（向き az はゆっくり、高さ h は速く変わるノイズ）
float az = atan2(d.x, -d.z);
float n = onoise(set(az * 2.5, h * 90, 0.5), 4, 0.55, 1) + 0.3 * onoise(set(az * 12, h * 300, 3.0), 2, 0.5, 1);
float cl = smooth(0.1, 0.5, n) * smooth(0.006, 0.02, h) * (1 - smooth(0.035, 0.06, h));
col = lerp(col, {{0.95, 0.95, 0.93}}, cl * 0.75);
if (d.y < 0) col = {{0.012, 0.02, 0.03}};   // 水平線より下は、暗い海の色（傾いた波の照り返しが下を向いたとき映る）
v@Cd = col;"""


def main():
    import hou
    g = kit.Guide("ocean_winter", "冬の朝の七里ヶ浜",
                  "夕暮れ版と同じ「水平線まで広げた板＋波の設計図」に、砂浜・岸で崩れる波と泡・高い太陽の光を足す。"
                  "崩れる波は、シミュレーションではなく VEX で「岸へ進む波の列」を足し、崩れた所から岸までに泡の色を付ける。"
                  "参考は、七里ヶ浜の砂浜から撮った冬の朝の写真。",
                  tags=["エフェクト", "海", "水", "Karma", "制作"])
    hou.setFps(24)
    hou.setFrame(FRAME)
    el, az = math.radians(SUN_EL), math.radians(SUN_AZ)
    sd = hou.Vector3(math.sin(az) * math.cos(el), math.sin(el), -math.cos(az) * math.cos(el))
    near_box = hou.BoundingBox(-12, -0.8, -60, 12, 1.2, -4)
    g.shot_dir = (0.0, 0.35, 1.0)

    sea = g.node("grid", "sea", size=(1, 1), rows=2200, cols=1000, t=(0.5, 0, 0.5))
    fan = g.node("attribwrangle", "spread_to_horizon", [sea],
                 snippet=f"// 夕暮れ版と同じ。z（0〜1）をカメラからの距離 {NEAR:g} m〜{FAR:g} m に、近くほど細かく\n"
                         f"float d = {NEAR:g} * pow({FAR / NEAR:g}, @P.z);\n"
                         "float w = d * 1.0 + 2;      // 広角のカメラなので、夕暮れ版より横に広く\n"
                         "@P = set((0.5 - @P.x) * 2 * w, 0, -d);\n"
                         "v@rest = @P;                // 動かす前の位置を覚えておく（岸からの距離に使う）")
    g.step(fan, "板を水平線まで広げる",
           "夕暮れ版の 1・2 段目と同じ。<code>grid</code>（Size 1 × 1、<strong>Rows 2200・Columns 1000</strong>、Center 0.5・0・0.5）を、"
           "<code>attribwrangle</code> でカメラの前の扇形に並べ直す。違いは 2 つ。"
           "広角（焦点距離 22 mm）で撮るので横幅を距離と同じにしたことと、動かす前の位置を <code>rest</code> に覚えておくこと。行と列の数も変えた。1400×1600 だと 55 m 先の目が横 7 cm・奥行き 31 cm と細長く、太陽の照り返しが放射状の筋になったので、行を増やして目を正方形に近づけた（点の数は 220 万でほぼ同じ）。"
           "<code>rest</code> から「波打ち際から何 m 沖か」を出して、次の段の崩れる波と泡に使う。",
           cap="上から見た板。カメラ（下の頂点）から 8 km 先まで扇形に広がる。", shading="smoothwire",
           bbox=hou.BoundingBox(-8000, 0, -FAR, 8000, 0, 0), direction=(0.0, 1.0, 0.05))
    specs = [g.node("oceanspectrum", name, gridsize=gs, res=9 if gs > 10 else 10, windspeed=ws, chopscale=chop,
                    winddir=wd, seed=i + 5, ampscale=amp) for i, (name, gs, ws, chop, wd, amp) in enumerate(SPECTRA)]
    big = g.node("merge", "swell_and_chop", specs[:2])
    wave0 = g.node("oceanevaluate::2.0", "move_points", [fan, big], time="=$T")
    keep = g.node("attribwrangle", "before_ripples", [wave0],
                  snippet="// さざ波を足す前の位置を覚えておく（遠くのさざ波を消すのに使う）\nv@before_ripples = @P;")
    small = g.node("merge", "ripples_2", specs[2:])
    wave = g.node("oceanevaluate::2.0", "add_ripples", [keep, small], time="=$T")
    g.step(wave, "沖の波とさざ波を、4 枚の設計図で動かす",
           "夕暮れ版と同じく <code>oceanspectrum</code> を <code>merge</code> して <code>oceanevaluate</code> に渡す（Time に <code>$T</code>）。今回は 2 回に分ける。"
           "<br>・1 回目（move_points）: うねり（Grid Size 200・Speed 5・Scale 0.5）と風の波（23・6・0.7）。"
           "<br>・2 回目（add_ripples）: さざ波 2 枚（<strong>Grid Size 4.7・Speed 7・Scale 2.4</strong> と <strong>1.9・5・2.4</strong>、どちらも Resolution Exponent 10）。"
           "間の <code>attribwrangle</code> で、さざ波を足す前の位置を <code>before_ripples</code> に覚えておき、次の段で遠くのさざ波を消す。"
           "<br>冬の朝の写真は、太陽の前の水面が広くきらめいている。きらめきは細かい波の 1 つ 1 つが太陽を映したもの（実験218）。"
           "本物の海面の傾きは、Cox と Munk が測った式で計算すると、風 5 m/秒で平均約 9°。この場面の水面（カメラから 15〜80 m）を測ると、"
           "さざ波 1 枚では平均 5.9° と平らすぎたので、2 枚にして強め、平均 9.0° にした。"
           "さざ波の Grid Size を 1.3 m にすると、遠くでそのくり返しが縦の縞に見えたので、4.7 m と 1.9 m にした（落とし穴を参照）。",
           cap=f"波打ち際から沖（4〜60 m）の波。フレーム {FRAME}。", shading="smooth", bbox=near_box, ui_parm="ampscale")
    surf = g.node("attribwrangle", "breaking_waves", [wave], snippet=SURF.format(SH=SH))
    g.step(surf, "岸で崩れる波と泡を VEX で足す",
           "<code>attribwrangle</code> で、岸へ進む波の列を足す。本物の砂浜の波は、沖から浅い所へ来ると高く切り立ち、崩れて白い泡になり、低くなって岸を這い上がる。"
           "これを「波打ち際から沖へ何 m か（<code>s</code>）」で書き分ける。"
           "<br>・<strong>遠くのさざ波を消す</strong>: カメラから 25〜90 m で、<code>before_ripples</code> との差を 0 へ近づける。遠くのさざ波は画の 1 画素より細かい。"
           "<br>・<strong>波の列</strong>: 周期 8 秒で岸へ進む。浅い所の波は遅く、間が詰まるので、長さを沖 80 m の 30 m から岸の 12 m へ縮める。"
           "<code>cos(ph - 0.9 * sin(ph))</code> で、岸側が切り立つ形にする。"
           "<br>・<strong>高さ</strong>: 沖 160 m で 0.12 m、崩れる所（沖 24〜36 m、横に揺らす）で 0.6 m。崩れたあとは低くする。"
           "<br>・<strong>泡</strong>: 本物の砂浜の動画では、崩れた波頭から岸まで、岸と平行な細い泡の筋が何本も重なっていた。"
           "そこで、横にはゆっくり・奥行きにはすばやく変わるノイズの「尾根」（<code>1 - abs(noise * 2 - 1)</code>）で筋を描き、波頭が通ったあとに薄れさせる。"
           "波頭の白い線は、2 つの大きさのノイズで不規則にちぎる。"
           "<br>・<strong>水の色</strong>: 深い青緑。波打ち際の薄い水は下の砂が透けるので、暗い茶色に寄せる。点の色 <code>Cd</code> を、水の色から泡の灰白（0.72）へ混ぜる。",
           cap=f"岸と平行な泡の筋と、波頭の白い線（フレーム {FRAME}）。", shading="smooth", bbox=near_box, ui_parm="snippet")
    nrm = g.node("normal", "smooth_normals", [surf])

    def sand(name, z0, z1, rows, width=80, cols=1200):
        s = g.node("grid", name, size=(width, z1 - z0), rows=rows, cols=cols, t=(0, 0, (z0 + z1) / 2))
        return g.node("attribwrangle", name + "_shape", [s],
                      snippet=f"// 岸へ向かって下がる砂浜（傾き {SLOPE}）に、細かい凸凹\n"
                              f"@P.y = {SLOPE} * (@P.z + {SH:g}) + 0.01 * noise(@P * 3) + 0.03 * noise(@P * 0.2) + 0.004 * noise(@P * 9) + 0.002 * noise(@P * 30);\n"
                              "v@Cd = {0.03, 0.029, 0.027} * (0.8 + 0.4 * noise(@P * 8));   // 七里ヶ浜の黒っぽい砂")
    wet = g.node("normal", "wet_sand_n", [sand("wet_sand", -13, -3, 500, width=30, cols=1500)])
    dry = g.node("normal", "dry_sand_n", [sand("dry_sand", -3, 6, 200)])
    g.step(wet, "砂浜を敷く",
           f"<code>grid</code> を 2 枚（濡れた所と乾いた所）置き、<code>attribwrangle</code> で岸へ向かって下げる（傾き {SLOPE}、10 m で 35 cm）。"
           f"カメラから {SH:g} m の所で水面の高さ 0 と交わり、そこが波打ち際になる。その先は水の下に潜る。"
           "七里ヶ浜の砂は黒っぽいので、色は 0.03 前後の暗い灰色。濡れた砂は、あとで材質をつやつやにして空と太陽を映す。",
           cap="", shot=False,  # 暗い砂はビューポートで黒く写るだけなので撮らない
           bbox=hou.BoundingBox(-8, -0.3, -13, 8, 0.3, -3), direction=(0.0, 0.6, 1.0))
    # 空・遠くの陸・富士山は別のオブジェクトにまとめる
    sky_obj = hou.node("/obj").createNode("geo", "sky")
    dome = g.node("sphere", "sky_dome", parent=sky_obj, type="polymesh", rows=300, cols=600, rad=(SKY_R,) * 3)
    sky_col = g.node("attribwrangle", "sky_color", [dome], parent=sky_obj,
                     snippet=SKY.format(SD=f"{{{sd[0]:.4f}, {sd[1]:.4f}, {sd[2]:.4f}}}"))
    land = g.node("grid", "far_land", parent=sky_obj, rows=2, cols=300)
    land_s = g.node("attribwrangle", "land_shape", [land], parent=sky_obj,
                    snippet="// 左の遠くに霞む陸（9 km 先、高さ 0〜430 m）。上の列だけ持ち上げて、横に長い帯にする\n"
                            "int col = @ptnum % 300; int row = @ptnum / 300;\n"
                            "float a = radians(fit(col, 0, 299, -60, -18));\n"
                            "float h = 110 + 160 * noise(set(col / 25.0, 0, 0)) + 60 * noise(set(col / 7.0, 5, 0));\n"
                            "h *= 1 - smooth(-26, -18, degrees(a));\n"
                            "@P = set(sin(a), 0, -cos(a)) * 9000 + set(0, row == 1 ? h * 1.6 : -40, 0);\n"
                            "v@Cd = {0.22, 0.32, 0.50};")
    fuji = g.node("grid", "fuji", parent=sky_obj, rows=2, cols=200)
    fuji_s = g.node("attribwrangle", "fuji_shape", [fuji], parent=sky_obj,
                    snippet="// 右の奥にうっすら富士山（18 km 先に置いた、高さ 330 m の山の影）\n"
                            "int col = @ptnum % 200; int row = @ptnum / 200;\n"
                            "float x = fit(col, 0, 199, -1, 1);\n"
                            "float a = radians(30 + x * 2.2);\n"
                            "float h = 330 * pow(1 - abs(x), 1.6);\n"
                            "@P = set(sin(a), 0, -cos(a)) * 18000 + set(0, row == 1 ? h : -40, 0);\n"
                            "v@Cd = row == 1 && h > 230 ? {0.82, 0.85, 0.92} : {0.50, 0.58, 0.74};")
    sun_r = 15000 * math.tan(math.radians(0.27))
    sun_ball = g.node("sphere", "sun_disk", parent=sky_obj, type="polymesh", rad=(sun_r,) * 3, t=tuple(sd * 15000))
    glow = g.mat("glow_mat", basecolor=(0, 0, 0), reflect=0.0, emitcolor=(1, 1, 1), emitcolor_usePointColor=1, emitint=1.0)
    sun_mat = g.mat("sun_mat", basecolor=(0, 0, 0), reflect=0.0, emitcolor=(1.0, 0.97, 0.9), emitint=600.0)
    far = g.node("merge", "sky_land_fuji", [sky_col, land_s, fuji_s], parent=sky_obj)
    asg_far = g.node("material", "assign_glow", [far], parent=sky_obj)
    asg_far.parm("shop_materialpath1").set(glow.path())
    asg_sun = g.node("material", "assign_sun", [sun_ball], parent=sky_obj)
    asg_sun.parm("shop_materialpath1").set(sun_mat.path())
    sky_out = g.node("merge", "sky_all", [asg_far, asg_sun], parent=sky_obj)
    sky_out.setDisplayFlag(True)
    sky_out.setRenderFlag(True)
    sky_obj.layoutChildren()
    g.step(sky_col, "冬の青空・遠くの陸・富士山を置く",
           "夕暮れ版と同じく、半径 20 km の <code>sphere</code> を <code>attribwrangle</code> で塗って空にする（別のオブジェクト <code>sky</code> にまとめた）。"
           "冬の朝の写真の空は、上ほど濃い青、水平線だけ白くかすむ。雲は水平線の少し上に横に長い筋。"
           "雲は、向き（<code>az</code>）ではゆっくり、高さ（<code>h</code>）では速く変わる <code>onoise</code> で描くと、横に長く伸びる。"
           f"左の遠くに霞む陸（9 km 先）と、右の奥の富士山（18 km 先）は、<code>grid</code> 2 行の上の列だけを持ち上げた帯で作り、空と同じ光る材質にする。"
           f"太陽の円盤は高さ {SUN_EL:g}°・左へ {-SUN_AZ:g}° に置く。",
           cap="", shot=False, ui_parm="snippet")
    water = g.mat("sea_mat", basecolor=(1, 1, 1), basecolor_usePointColor=1, rough=0.07, reflect=1.0, ior=1.33)
    wet_mat = g.mat("wet_sand_mat", basecolor=(0.6, 0.6, 0.6), basecolor_usePointColor=1, rough=0.06, reflect=0.5)
    dry_mat = g.mat("dry_sand_mat", basecolor=(1.4, 1.4, 1.4), basecolor_usePointColor=1, rough=0.85, reflect=0.3)
    final = g.node("merge", "sea_and_beach", [g.assign(nrm, water, "assign_sea"), g.assign(wet, wet_mat, "assign_wet"),
                                              g.assign(dry, dry_mat, "assign_dry")])
    # 太陽の光: 空の球の内側（5 km 先）に、見かけ 0.54° の円い光を置く
    sun = hou.node("/obj").createNode("hlight::2.0", "sun")
    sun.parm("light_type").set("disk")
    rr = 5000 * math.tan(math.radians(0.27))
    sun.parmTuple("areasize").set((2 * rr, 2 * rr))
    sun.parm("normalizearea").set(0)
    sun.parm("light_intensity").set(SUN_POWER)
    sun.parmTuple("light_color").set((1.0, 0.97, 0.92))
    sun.parmTuple("t").set(tuple(sd * 5000))
    sun.parmTuple("r").set(hou.hmath.buildRotateLookAt(hou.Vector3(sd * 5000), hou.Vector3(0, 0, 0),
                                                        hou.Vector3(0, 1, 0)).extractRotates())
    g.step(final, "材質と太陽の光を置く",
           "<code>principledshader</code> を 3 つ。水は Use Point Color・<strong>Roughness 0.07</strong>・IOR 1.33（画素より細かい波のぶんを、つやのぼけで足す。0.08 から光の道が白い帯に見え始める。実験218）。"
           "濡れた砂は Roughness 0.06 でつやを出し、乾いた砂は 0.85。空の材質は <strong>Reflectivity を 0</strong> にする（落とし穴を参照）。"
           "<br>太陽の光は <code>hlight</code> の <strong>disk</strong>（円い光）を、太陽の向きへ 5 km 先に、見かけ 0.54°（半径 23.6 m）で置き、"
           f"<strong>Normalize Light Intensity to Area を切って Intensity {SUN_POWER:,.0f}</strong>。平行光（distant）は空の球にさえぎられて届かない（落とし穴を参照）。",
           cap="", shot=False)
    cam = hou.node("/obj").createNode("cam", "beach_cam")
    cam.parm("focal").set(22)
    cam.parm("far").set(1e6)
    cam.parmTuple("t").set((0, SLOPE * SH + EYE, 0))
    cam.parmTuple("r").set((4, 0, 0))
    g.hero(final, f"Karma で撮った仕上がり（フレーム{FRAME}）。砂浜の目の高さ {EYE:g} m から、太陽の方へ撮る。",
           floor=False, key=0.0, rim=0.0, dome=0.0, spp=32, frame=FRAME, camera=cam)
    cpu_sec = g.hero_sec
    if os.environ.get("QUICK"):     # 見た目を詰めるあいだは、仕上がりを撮ったところで止める（場面だけ保存）
        hou.hipFile.save(os.path.join(kit.OUT, "_ocean_winter_quick.hipnc"))
        return

    # ---- 落とし穴を測る ----
    import OpenImageIO as oiio
    karma = hou.node("/out/hero_karma")
    tmp = os.path.join(kit.OUT, "_winter_probe.png")

    def probe(res=(480, 270)):
        keep = (karma.parm("resolutionx").eval(), karma.parm("resolutiony").eval(), karma.parm("picture").eval())
        karma.parm("resolutionx").set(res[0])
        karma.parm("resolutiony").set(res[1])
        cam.parm("resx").set(res[0])
        cam.parm("resy").set(res[1])
        karma.parm("samplesperpixel").set(8)
        karma.parm("varianceaa_maxsamples").set(8)
        karma.parm("picture").set(tmp.replace("\\", "/"))
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        karma.parm("resolutionx").set(keep[0])
        karma.parm("resolutiony").set(keep[1])
        karma.parm("picture").set(keep[2])
        cam.parm("resx").set(keep[0])
        cam.parm("resy").set(keep[1])
        buf = oiio.ImageBuf(tmp)
        out = {}
        for key, roi in (("sea", oiio.ROI(0, 480, 160, 225, 0, 1, 0, 3)), ("sky", oiio.ROI(250, 470, 10, 60, 0, 1, 0, 3))):
            out[key] = sum(oiio.ImageBufAlgo.computePixelStats(buf, roi=roi).avg[:3]) / 3
        return out

    base = probe()
    # (1) 平行光に替えて、強さを 30 と 1000 にする
    sun.parm("light_type").set("distant")
    dist30 = probe()
    sun.parm("light_intensity").set(1000.0)
    dist1000 = probe()
    sun.parm("light_type").set("disk")
    sun.parm("light_intensity").set(SUN_POWER)
    # (2) 空の材質の Reflectivity を既定に戻す
    reflect_default = hou.node("/mat").createNode("principledshader::2.0", "probe_default").parm("reflect").eval()
    hou.node("/mat/probe_default").destroy()
    glow.parm("reflect").set(reflect_default)
    sun_mat.parm("reflect").set(reflect_default)
    shiny = probe()
    glow.parm("reflect").set(0.0)
    sun_mat.parm("reflect").set(0.0)
    # (3) smooth() の最小と最大を逆に書くと
    pw = g.geo.createNode("add", "probe_pt")
    pw.parm("points").set(1)
    vw = g.geo.createNode("attribwrangle", "probe_smooth")
    vw.setFirstInput(pw)
    vw.parm("snippet").set("f@a = smooth(30, 40, 20); f@b = smooth(30, 40, 35); f@c = smooth(30, 40, 50);\n"
                           "f@ra = smooth(40, 30, 20); f@rb = smooth(40, 30, 35); f@rc = smooth(40, 30, 50);")
    pt = vw.geometry().points()[0]
    sm = {k: pt.attribValue(k) for k in ("a", "b", "c", "ra", "rb", "rc")}
    vw.destroy()
    pw.destroy()
    foam_pts = surf.geometry().pointFloatAttribValues("foam")
    foam_share = sum(1 for f in foam_pts if f > 0.5) / len(foam_pts)

    g.karma_anim((1, 120), "Karma で撮った波の動き（5 秒、120 フレーム、960×540）。沖で崩れた波が泡になって岸へ寄せる。", spp=16)

    traps = [
        {"title": "さざ波の Grid Size が小さいと、遠くでくり返しが縦の縞に見える",
         "body": "さざ波を Grid Size 1.3 m で強めると、カメラから 50 m ほどの水面に、奥へ向かう縦の縞が並んだ。縞の間は画の上で約 1.3 m で、設計図がくり返す間と同じだった。"
                 "遠くでは奥行きの模様は縮んで見えなくなるが、横のくり返しは残るため。Grid Size を 4.7 m・1.9 m に広げ、Resolution Exponent を 10 に上げて細かい波は残すと、縞は消えた。",
         "img": "", "cap": ""},
        {"title": "平行光（distant）の太陽は、空の球にさえぎられて届かない",
         "body": f"太陽の光を <code>hlight</code> の distant にすると、強さを 30 にしても 1000 にしても、海の明るさは {dist30['sea']:.3f} と {dist1000['sea']:.3f} で変わらなかった"
                 f"（disk の太陽では {base['sea']:.3f}）。平行光は無限の遠くから来るので、半径 20 km の空の球が影を落としてしまう。"
                 "空のオブジェクトの Render Visibility を「-shadow」にしても変わらなかった。空の球の内側に、円い光（disk）を置く。",
         "img": "", "cap": ""},
        {"title": "空の材質の Reflectivity が既定のままだと、太陽の光を映して空に大きな光の玉ができる",
         "body": f"光る材質でも、principledshader の Reflectivity は既定 {reflect_default:g} で、つやが残る。強い太陽の光を空の球の内側が映して、"
                 f"太陽のまわりの空の明るさが {base['sky']:.3f} から {shiny['sky']:.3f} になり、濡れた砂にもその照り返しが太い帯で写った。空と太陽の円盤の Reflectivity は 0 にする。",
         "img": "", "cap": ""},
        {"title": "smooth() の最小と最大を逆に書くと、思った向きにならない",
         "body": f"<code>smooth(30, 40, x)</code> は x = 20・35・50 で {sm['a']:.2f}・{sm['b']:.2f}・{sm['c']:.2f}。"
                 f"逆に <code>smooth(40, 30, x)</code> と書くと {sm['ra']:.2f}・{sm['rb']:.2f}・{sm['rc']:.2f} になった。"
                 "「遠いほど 0 にしたい」ときは、<code>1 - smooth(30, 40, x)</code> と書く。試作では、これで泡の範囲と遠くの陸が消えていた。",
         "img": "", "cap": ""},
    ]
    facts = [["足すノード", f"{len(g.geo.children())}個＋空 {len(sky_obj.children())}個（ほかに材質5つ・太陽の光・カメラ）"],
             ["泡の白い点（0.5 以上）", f"{foam_share * 100:.1f}%"],
             ["映像を撮る時間", f"{g.anim_sec / 60:.1f}分（Karma 960×540、120 枚）"]]
    g.save(facts=facts, traps=traps)


if __name__ == "__main__":
    main()
