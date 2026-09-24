# -*- coding: utf-8 -*-
"""実践「夕暮れの海の波を作る」（2026-09-24 作り直し）— 水平線まで続く海面を、3 枚の波の設計図（スペクトル）で動かし、
低い夕日を正面に置いて Karma で撮る。映像も Karma で撮る。

前の版（24 m 四方の板を斜め上から撮った）は、本物の夕暮れの海の写真と並べると、水平線が波の山になって砂丘のように見えた。

    hython examples/pr_ocean.py
"""
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

FRAME = 24
CAM_H = 2.5            # カメラの高さ（m）。船の甲板や防波堤から見る高さ
NEAR, FAR = 3.0, 8000.0
SUN_EL = 3.0           # 夕日の高さ（度）
SKY_R = 20000.0
# 3 枚の設計図: 名前・Grid Size（m）・風（m/秒）・Chop・風向き・Amplitude Scale
SPECTRA = (("swell", 300, 7, 0.6, 20, 0.48), ("wind_chop", 37, 6, 1.1, -25, 0.5), ("ripples", 4.3, 3, 0.8, 0, 0.33))


def main():
    import hou
    g = kit.Guide("ocean", "夕暮れの海の波を作る",
                  "海はシミュレーションしなくても作れる。風の強さから波の混ざり方（設計図）を決め、平らな板の点をその通りに動かすだけ。"
                  "板をカメラから水平線まで広げ、大きなうねり・風の波・さざ波の 3 枚の設計図を重ね、夕日を正面に置くと、"
                  "水面に夕日の光の道ができる。映像も Karma で撮る。",
                  tags=["エフェクト", "海", "水", "Karma", "制作"])
    hou.setFps(24)
    hou.setFrame(FRAME)
    sd = hou.Vector3(0, math.sin(math.radians(SUN_EL)), -math.cos(math.radians(SUN_EL)))
    near_box = hou.BoundingBox(-8, -0.8, -30, 8, 0.8, -3)
    g.shot_dir = (0.0, 0.22, 1.0)

    sea = g.node("grid", "sea", size=(1, 1), rows=1400, cols=1600, t=(0.5, 0, 0.5))
    g.step(sea, "細かい板を敷く",
           "<code>grid</code> を <strong>Size 1 × 1</strong>、<strong>Rows 1400・Columns 1600</strong> にし、<strong>Center を 0.5・0・0.5</strong> にずらす。"
           "板の点は x も z も 0〜1 に並ぶ。この 0〜1 を、次の段で「横の位置」と「カメラからの距離」に読み替える。",
           cap="1 m 四方に 224 万点の板（まだ海の大きさではない）。", shading="smooth",
           bbox=hou.BoundingBox(0, 0, 0, 1, 0, 1), direction=(0.3, 1.0, 0.8))
    fan = g.node("attribwrangle", "spread_to_horizon", [sea],
                 snippet=f"// z（0〜1）をカメラからの距離 {NEAR:g} m〜{FAR:g} m に。近くは細かく、遠くは粗く並べる\n"
                         f"float d = {NEAR:g} * pow({FAR / NEAR:g}, @P.z);\n"
                         "// 横幅は距離に合わせて広げる（カメラに写る幅より少し広く）\n"
                         "float w = d * 0.62 + 2;\n"
                         "// 左右を入れ替えて置く（入れ替えないと面が下を向く。落とし穴を参照）\n"
                         "@P = set((0.5 - @P.x) * 2 * w, 0, -d);")
    g.step(fan, "板をカメラから水平線まで広げる",
           "<code>attribwrangle</code> で、点を「カメラの前の扇形」に並べ直す。カメラは原点の上、−z の向きに置く。"
           f"z の 0〜1 を <strong>距離 {NEAR:g} m〜{FAR / 1000:g} km</strong> に、<code>pow</code> で<strong>近くほど細かく</strong>割り振る。"
           f"となりの行との間は、足もとで約 1.7 cm、水平線の近くで約 45 m。どちらも画面の上ではほぼ同じ細かさになる。"
           f"同じ 224 万点を 8 km 四方に均等に並べると、升目は 5.7 m になり、足もとの波が出ない。",
           cap="上から見た板。カメラ（下の頂点）から 8 km 先まで扇形に広がる。", shading="smoothwire",
           bbox=hou.BoundingBox(-5000, 0, -FAR, 5000, 0, 0), direction=(0.0, 1.0, 0.05))
    specs = []
    for name, gs, ws, chop, wd, amp in SPECTRA:
        specs.append(g.node("oceanspectrum", name, gridsize=gs, res=9 if gs > 10 else 8, windspeed=ws,
                            chopscale=chop, winddir=wd, seed=len(specs) + 1, ampscale=amp))
    mix = g.node("merge", "three_spectra", specs)
    g.step(mix, "波の設計図を 3 枚重ねる",
           "<code>oceanspectrum</code> は、風の強さと向きから「どの大きさの波がどれだけ混ざるか」（設計図）を作る。"
           "本物の沖の海は、遠くから来る大きなうねりの上に、その場の風の波と、さざ波が乗っている。そこで 3 つ作って <code>merge</code> でまとめる。"
           "<br><strong>swell</strong>（うねり）: Grid Size 300・Wind の Speed 7・Chop 0.6・Amplitude の Scale 0.48"
           "<br><strong>wind_chop</strong>（風の波）: Grid Size 37・Speed 6・Chop 1.1・Direction −25°・Scale 0.5"
           "<br><strong>ripples</strong>（さざ波）: Grid Size 4.3・Speed 3・Chop 0.8・Scale 0.33"
           "<br>Grid Size は設計図がくり返す間隔。300・37・4.3 のように割り切れない数にすると、くり返しの継ぎ目が重ならない。"
           "Amplitude の Scale（波の高さの倍率）は既定の 3 から大きく下げる（落とし穴を参照）。",
           cap="", shot=False, ui_parm="ampscale")
    wave = g.node("oceanevaluate::2.0", "move_points", [fan, mix], time="=$T", cusp=1)
    g.step(wave, "設計図どおりに点を動かす",
           "<code>oceanevaluate</code> の左に扇形の板、右に 3 枚の設計図をつなぐ。"
           "<strong>Time に <code>$T</code></strong>（今の秒数）を書くと、再生に合わせて波が進む。"
           "<strong>Cusp Attribute</strong> を入れると、波の頭がとがった所に <code>cusp</code> という値が付く。泡の目印に使う。",
           cap=f"カメラの足もと（3〜30 m）を低い角度から見た波。フレーム {FRAME}（1 秒）。ビューポートでも夕日の光を映してきらめく。", shading="smooth", bbox=near_box, ui_parm="time")
    foam = g.node("attribwrangle", "foam_color", [wave],
                  snippet="// 深い海の色から、波の頭（cusp）が強くとがった所だけ白い泡の色へ\n"
                          "vector deep = {0.004, 0.011, 0.014};\n"
                          "float f = smooth(0.55, 0.85, f@cusp);\n"
                          "v@Cd = lerp(deep, {0.8, 0.82, 0.84}, f);")
    g.step(foam, "水の色と泡を付ける",
           "<code>attribwrangle</code> で、ふだんはほとんど黒に近い深い青緑にする。海の色は、水そのものより空の映り込みで決まるので、水の色は暗くてよい。"
           "<code>cusp</code> が 0.55 を超えた所から白に寄せる。この風の強さ（6〜7 m/秒）では 0.55 を超えた点は無く、白波は立たなかった。夕凪の写真の海にも白波はほとんど無い。風を強めると、この白が出てくる。",
           cap="", shot=False, ui_parm="snippet")
    nrm = g.node("normal", "smooth_normals", [foam])
    dome = g.node("sphere", "sky", type="polymesh", rows=300, cols=600, rad=(SKY_R, SKY_R, SKY_R))
    sky_col = g.node("attribwrangle", "sky_color", [dome],
                     snippet="// 向き d と太陽の向き s から、空の色を決める\n"
                             "vector d = normalize(@P);\n"
                             f"vector s = normalize({{{sd[0]:.4f}, {sd[1]:.4f}, {sd[2]:.4f}}});\n"
                             "float h = max(d.y, 0);          // 水平線からの高さ\n"
                             "float c = max(dot(d, s), 0);    // 太陽に近いほど 1\n"
                             "// 水平線は夕焼けの橙、上ほど夜の青\n"
                             "vector col = lerp({0.95, 0.40, 0.16}, {0.025, 0.045, 0.12}, pow(fit(h, 0, 0.3, 0, 1), 0.4));\n"
                             "// 太陽のまわりの明るみ\n"
                             "col += {1.0, 0.55, 0.25} * pow(c, 80) * 0.8 + {1.0, 0.7, 0.4} * pow(c, 900) * 3;\n"
                             "// 横に長い薄い雲（高さで割って、空の天井に貼ったように見せる）\n"
                             "float n = onoise(set(d.x / max(h, 0.02) * 0.25, 0, d.z / max(h, 0.02) * 2.5), 4, 0.55, 1);\n"
                             "float cl = smooth(-0.05, 0.4, n) * smooth(0.01, 0.06, h) * (1 - smooth(0.15, 0.35, h));\n"
                             "col = lerp(col, lerp({0.12, 0.07, 0.09}, {1.3, 0.62, 0.35}, pow(c, 6)), cl * 0.7);\n"
                             "// 太陽と反対の空は暗く（海の左右が暗く映る）\n"
                             "col *= lerp(0.4, 1.0, pow(c, 6));\n"
                             "if (d.y < 0) col = {0.02, 0.03, 0.05};\n"
                             "v@Cd = col;")
    sun_r = 15000 * math.tan(math.radians(0.27))
    sun_ball = g.node("sphere", "sun_disk", type="polymesh", rad=(sun_r, sun_r, sun_r), t=tuple(sd * 15000))
    g.step(sky_col, "夕焼けの空と夕日を置く",
           "海の色の大半は空の映り込みなので、空を作り込む。半径 20 km の <code>sphere</code> で全体を包み、<code>attribwrangle</code> で点に色を付ける。"
           "水平線は橙、上ほど夜の青。太陽のまわりを明るくし、横に長い薄い雲を <code>onoise</code> で描く。"
           "太陽と反対側の空は暗くする。こうすると、海の左右が暗く、夕日の下だけが光る。"
           f"夕日は、15 km 先・高さ {SUN_EL:g}° に置いた半径 {sun_r:.0f} m の球（見かけの大きさ 0.54°。本物の太陽は 0.53°）。",
           cap="", shot=False, ui_parm="snippet")
    water = g.mat("sea_mat", basecolor=(1, 1, 1), basecolor_usePointColor=1, rough=0.015, reflect=1.0, ior=1.33)
    sky_mat = g.mat("sky_mat", basecolor=(0, 0, 0), emitcolor=(1, 1, 1), emitcolor_usePointColor=1, emitint=1.0)
    sun_mat = g.mat("sun_mat", basecolor=(0, 0, 0), emitcolor=(1.0, 0.8, 0.55), emitint=40.0)
    final = g.node("merge", "sea_and_sky", [g.assign(nrm, water, "assign_sea"), g.assign(sky_col, sky_mat, "assign_sky"),
                                            g.assign(sun_ball, sun_mat, "assign_sun")])
    g.step(final, "水の材質を当てる",
           "<code>normal</code> で面の向きをなめらかにしてから、<code>principledshader</code> を当てる。"
           "<strong>Use Point Color</strong>（前の段の色を使う）、<strong>Roughness 0.015・Reflectivity 1・IOR 1.33</strong>（水）。"
           "Roughness をほぼ 0 にすると、さざ波の 1 つ 1 つが夕日を映して、光の道がきらめく。"
           "空の球は、点の色で光る材質（Emission 1、Use Point Color）。夕日の球は強く光らせる（Emission Intensity 40）。",
           cap="", shot=False)
    # 夕日の光（泡や水面の明るい所を照らす）。夕日の球と同じ向きから差す平行光
    sun = hou.node("/obj").createNode("hlight::2.0", "sunset")
    sun.parm("light_type").set("distant")
    sun.parm("light_intensity").set(6.0)
    sun.parmTuple("light_color").set((1.0, 0.62, 0.32))
    look = hou.hmath.buildRotateLookAt(hou.Vector3(sd * 100), hou.Vector3(0, 0, 0), hou.Vector3(0, 1, 0))
    sun.parmTuple("r").set(look.extractRotates())
    cam = hou.node("/obj").createNode("cam", "sea_cam")
    far_default = cam.parm("far").eval()
    cam.parm("focal").set(35)
    cam.parm("far").set(1e6)
    cam.parmTuple("t").set((0, CAM_H, 0))
    cam.parmTuple("r").set((-3, 0, 0))
    g.hero(final, f"Karma で撮った仕上がり（フレーム{FRAME}）。高さ {CAM_H:g} m から、水平線の夕日に向かって撮る。",
           floor=False, key=0.0, rim=0.0, dome=0.0, spp=32, frame=FRAME, camera=cam)
    cpu_sec = g.hero_sec

    # ---- 落とし穴を測る ----
    geo = wave.geometry()
    P = geo.pointFloatAttribValues("P")
    P0 = fan.geometry().pointFloatAttribValues("P")
    near_y = [P[i + 1] for i in range(0, len(P), 3) if -P0[i + 2] < 40]
    cusp = geo.pointFloatAttribValues("cusp")
    foam_share = sum(1 for c in cusp if c > 0.55) / len(cusp)
    # 波の高さ: 設計図 1 枚ずつ、その Grid Size の板で測る（Amplitude Scale 既定の 3 と、下げた値）
    probe = g.geo.createNode("grid", "probe_grid")
    probe.parm("rows").set(200)
    probe.parm("cols").set(200)
    pev = g.geo.createNode("oceanevaluate::2.0", "probe_eval")
    pev.setInput(0, probe)
    pev.parm("time").set(1)
    heights = {}
    for sp in specs:
        probe.parmTuple("size").set((sp.parm("gridsize").eval(),) * 2)
        pev.setInput(1, sp)
        amp = sp.parm("ampscale").eval()
        sp.parm("ampscale").set(3.0)
        big = statistics.pstdev(pev.geometry().pointFloatAttribValues("P")[1::3])
        sp.parm("ampscale").set(amp)
        small = statistics.pstdev(pev.geometry().pointFloatAttribValues("P")[1::3])
        heights[sp.name()] = (big, small)
    probe.destroy()
    pev.destroy()
    # 3 枚とも既定の 3 に戻して重ねると、どこまで高くなるか
    for sp in specs:
        sp.parm("ampscale").set(3.0)
    yb = wave.geometry().pointFloatAttribValues("P")[1::3]
    big_range = max(yb) - min(yb)
    big_near = max(y for y, p0 in zip(yb, P0[2::3]) if -p0 < 40)
    for sp, spec in zip(specs, SPECTRA):
        sp.parm("ampscale").set(spec[5])
    # 左右を入れ替えずに並べると、面の向き（N）が下を向く
    flip = g.geo.createNode("attribwrangle", "probe_flip")
    flip.setFirstInput(sea)
    flip.parm("snippet").set(fan.parm("snippet").eval().replace("(0.5 - @P.x)", "(@P.x - 0.5)"))
    ny_bad = flip.geometry().prims()[0].normal()[1]
    ny_good = fan.geometry().prims()[0].normal()[1]
    flip.destroy()
    # XPU（GPU）で同じ絵を撮る
    karma = hou.node("/out/hero_karma")
    karma.parm("engine").set("xpu")
    xpu_png = os.path.join(kit.OUT, "_ocean_xpu.png")
    karma.parm("picture").set(xpu_png.replace("\\", "/"))
    t0 = time.perf_counter()
    karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
    xpu_sec = time.perf_counter() - t0
    karma.parm("engine").set("cpu")
    karma.parm("picture").set(os.path.join(kit.OUT, "pr_ocean_hero.png").replace("\\", "/"))
    import OpenImageIO as oiio

    def sky_mean(path):
        buf = oiio.ImageBuf(path)
        roi = oiio.ROI(0, 900, 20, 150, 0, 1, 0, 3)   # 空の左上（太陽と透かしを避ける）
        return sum(oiio.ImageBufAlgo.computePixelStats(buf, roi=roi).avg[:3]) / 3
    sky_cpu, sky_xpu = sky_mean(os.path.join(kit.OUT, "pr_ocean_hero.png")), sky_mean(xpu_png)

    g.karma_anim((1, 120), "Karma で撮った波の動き（5 秒、120 フレーム、960×540）。カメラは止めたまま、波だけが進む。", spp=16)

    sw, ch, rp = heights["swell"], heights["wind_chop"], heights["ripples"]
    traps = [
        {"title": "Amplitude の Scale を既定の 3 のままにすると、カメラが水に沈む",
         "body": f"設計図を 1 枚ずつ測ると、既定の 3 では高さのばらつき（標準偏差）がうねり {sw[0]:.2f} m・風の波 {ch[0]:.2f} m・さざ波 {rp[0]:.3f} m だった。"
                 f"3 枚とも 3 のまま重ねると、いちばん高い所と低い所の差は {big_range:.1f} m、カメラから 40 m 以内でも山の高さが {big_near:.1f} m になり、高さ {CAM_H:g} m のカメラより高い波が手前に立った。"
                 f"下げた値では {sw[1]:.2f} m・{ch[1]:.2f} m・{rp[1]:.3f} m。夕凪の沖の海らしい高さになる。",
         "img": "", "cap": ""},
        {"title": "左右を入れ替えずに並べると、面が下を向く",
         "body": f"<code>(@P.x - 0.5)</code> のまま z を −距離にすると、面の表と裏が入れ替わり、面の向きの上下の成分が {ny_bad:+.1f} になった（入れ替えると {ny_good:+.1f}）。"
                 "裏向きの水面は、光を正しく映さない。",
         "img": "", "cap": ""},
        {"title": "カメラの Far Clipping のままだと、空が写らない",
         "body": f"cam の Far Clipping は既定 {far_default:g} m。半径 {SKY_R / 1000:g} km の空はその外なので、写らずに透明になる。"
                 "1,000,000 にしておく。",
         "img": "", "cap": ""},
        {"title": "GPU の Karma XPU では、空が白く飛んだ",
         "body": f"Karma の Rendering Engine を XPU にして同じ絵を撮ると、{xpu_sec:.1f} 秒（CPU は {cpu_sec:.1f} 秒）。速いが、"
                 f"空の左上の明るさは CPU {sky_cpu:.3f} に対して XPU {sky_xpu:.3f} で、白く飛んだ。空は点の色で光らせる材質（Use Point Color）で、XPU ではこの色が使われていないように見える（原因は確かめていない）。"
                 "この場面は CPU で撮る。",
         "img": "", "cap": ""},
    ]
    facts = [["足すノード", f"{len(g.geo.children())}個（ほかに材質3つ・夕日の光・カメラ）"], ["海の点の数", f"{len(P) // 3:,}"],
             ["足もと（40 m 以内）の波の高さのばらつき", f"{statistics.pstdev(near_y):.2f} m"],
             ["白波が立った点", f"{foam_share * 100:.2f}%"],
             ["映像を撮る時間", f"{g.anim_sec / 60:.1f}分（Karma 960×540、120 枚）"]]
    g.save(facts=facts, traps=traps)


if __name__ == "__main__":
    main()
