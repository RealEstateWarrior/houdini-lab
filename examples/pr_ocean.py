# -*- coding: utf-8 -*-
"""実践「夕暮れの海の波を作る」— 平らな板を、波の設計図（スペクトル）で上下させ、波頭を白くして夕日で撮る。

    hython examples/pr_ocean.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

FRAME = 24


def main():
    import hou
    g = kit.Guide("ocean", "夕暮れの海の波を作る",
                  "海はシミュレーションしなくても作れる。風の強さから波の混ざり方（スペクトル）を決め、平らな板の点をその通りに動かすだけ。"
                  "波のとがった所に白い泡の色を付け、低い夕日を逆光にすると、水面がきらめく。",
                  tags=["エフェクト", "海", "水", "Karma", "制作"])
    g.shot_dir = (0.8, 0.5, 1.2)
    g.shot_bbox = hou.BoundingBox(-10, -1, -10, 10, 1, 10)
    sea = g.node("grid", "sea", size=(60, 60), rows=500, cols=500)
    g.step(sea, "平らな板を敷く",
           "<code>grid</code> を 60 × 60 m、<strong>Rows・Columns 500</strong>（升目 12 cm）にする。"
           "波は点を動かして作るので、升目が粗いと細かい波が出ない。",
           cap="60 m 四方の平らな板（手前の 20 m を表示）。", shading="smoothwire")
    spec = g.node("oceanspectrum", "wind_waves", windspeed=9.0, chopscale=0.9, gridsize=50)
    g.step(spec, "風から波の設計図を作る",
           "<code>oceanspectrum</code> は、風の強さと向きから「どの大きさの波がどれだけ混ざるか」を作る。"
           "<strong>Wind の Speed を 9</strong>（m/秒、やや強い風）、<strong>Chop を 0.9</strong>（波の頭をとがらせる）にする。"
           "Grid Size 50 は、この設計図が何 m ごとにくり返すか。",
           cap="スペクトル（波の設計図）自体は板に見える。", shot=False, ui_parm="windspeed")
    wave = g.node("oceanevaluate::2.0", "move_points", [sea, spec], time="=$T", cusp=1)
    g.step(wave, "設計図どおりに点を動かす",
           "<code>oceanevaluate</code> の左に板、右に <code>oceanspectrum</code> をつなぐ。"
           "<strong>Time に <code>$T</code></strong>（今の秒数）を書くと、再生に合わせて波が進む。"
           "<strong>Cusp Attribute</strong> を入れると、波の頭がとがって折れそうな所に <code>cusp</code> という値が付く。泡の目印に使う。",
           cap=f"フレーム {FRAME}（1 秒）の波。", shading="smooth", ui_parm="time")
    foam = g.node("attribwrangle", "foam_color", [wave],
                  snippet="// 深い海の色から、波の頭（cusp）ほど白い泡の色へ\n"
                          "vector deep = {0.003, 0.012, 0.018};\n"
                          "vector white = {0.85, 0.88, 0.9};\n"
                          "float f = smooth(0.4, 0.7, f@cusp);\n"
                          "v@Cd = lerp(deep, white, f);")
    hou.setFrame(FRAME)
    g.step(foam, "波の頭を白くする",
           "<code>attribwrangle</code> で、<code>cusp</code> が小さい所は深い青緑、大きい所ほど白に近づける。"
           "<code>smooth(0.4, 0.7, …)</code> は、0.4 より下は 0、0.7 より上は 1 に、間をなめらかにつなぐ（しきい値は落とし穴を参照）。",
           cap="とがった波の頭に白が乗る。", shading="smooth", ui_parm="snippet")
    dome = g.node("sphere", "sky", type="polymesh", rows=48, cols=64, rad=(400, 400, 400))
    sky_col = g.node("attribwrangle", "sky_color", [dome],
                     snippet="// 水平線の近くは夕焼けの橙、上へ行くほど夜の青\n"
                             "float h = fit(normalize(@P).y, -0.02, 0.45, 0, 1);\n"
                             "v@Cd = lerp({1.0, 0.42, 0.16}, {0.06, 0.09, 0.25}, pow(h, 0.6));")
    sun_ball = g.node("sphere", "sun_disk", type="polymesh", rad=(9, 9, 9), t=(0, 22, -390))
    g.step(sky_col, "空を置く",
           "海は空を映して色が決まるので、先に空を作る。半径 400 m の <code>sphere</code> で全体を包み、"
           "<code>attribwrangle</code> で高さに合わせて色を付ける。水平線の近くは橙、上ほど夜の青。"
           "奥の低い所に、小さな球を夕日として置く。",
           cap="空の球（内側から見る）。", shot=False)
    water = g.mat("sea_mat", basecolor=(1, 1, 1), basecolor_usePointColor=1, rough=0.02, reflect=1.0, ior=1.33)
    sky_mat = g.mat("sky_mat", basecolor=(0, 0, 0), emitcolor=(1, 1, 1), emitcolor_usePointColor=1, emitint=1.0)
    sun_mat = g.mat("sun_mat", basecolor=(0, 0, 0), emitcolor=(1.0, 0.75, 0.45), emitint=25.0)
    final = g.node("merge", "sea_and_sky", [g.assign(foam, water, "assign_sea"), g.assign(sky_col, sky_mat, "assign_sky"),
                                            g.assign(sun_ball, sun_mat, "assign_sun")])
    g.step(final, "水の材質を当てる",
           "<code>principledshader</code> で <strong>Use Point Color</strong>（前の段の色を使う）、"
           "<strong>Roughness 0.02・Reflectivity 1・IOR 1.33</strong>（水）。水面は空と夕日を映して色が決まるので、材質の色は暗くしておく。"
           "空の球には光る材質（Use Point Color で色を点から取る）、夕日の球には強い光（Emission Intensity 25）。",
           cap="材質を当てた状態。", shot=False)
    # 夕日: 低い角度で奥から差す平行光（distant）。水面に光の道ができる
    sun = hou.node("/obj").createNode("hlight::2.0", "sunset")
    sun.parm("light_type").set("distant")
    sun.parm("light_intensity").set(4.0)
    sun.parmTuple("light_color").set((1.0, 0.55, 0.25))
    look = hou.hmath.buildRotateLookAt(hou.Vector3(0, 22, -390), hou.Vector3(0, 0, 0), hou.Vector3(0, 1, 0))
    sun.parmTuple("r").set(look.extractRotates())
    g.hero(final, f"Karma で撮った仕上がり（フレーム{FRAME}）。夕日を逆光にして、水面のきらめきを出す。",
           direction=(0.1, 0.16, 1.0), floor=False, key=0.0, rim=0.0,
           dome=0.15, dome_color=(0.95, 0.55, 0.4), spp=64, margin=0.9, frame=FRAME,
           bbox=hou.BoundingBox(-12, -0.8, -12, 12, 0.8, 12))

    # ---- 落とし穴を測る ----
    geo = foam.geometry()
    ys = geo.pointFloatAttribValues("P")[1::3]
    wave_h = max(ys) - min(ys)
    cusp = geo.pointFloatAttribValues("cusp")
    foam_share = sum(1 for c in cusp if c > 0.15) / len(cusp)
    foam_real = sum(1 for c in cusp if c > 0.4) / len(cusp)
    # Time を固定すると波が止まる
    wave.parm("time").deleteAllKeyframes()
    wave.parm("time").set(0)
    hou.setFrame(1)
    a = wave.geometry().pointFloatAttribValues("P")
    hou.setFrame(FRAME)
    b = wave.geometry().pointFloatAttribValues("P")
    frozen = max(abs(x - y) for x, y in zip(a, b))
    wave.parm("time").setExpression("$T")
    # 設計図は Grid Size ごとにくり返す: 50 m 離れた2点の高さをくらべる
    probe = hou.node(g.geo.path()).createNode("add", "probe_pts")
    probe.parm("points").set(2)
    probe.parmTuple("pt0").set((3.3, 0, 1.7))
    probe.parmTuple("pt1").set((53.3, 0, 1.7))
    for k in ("usept0", "usept1"):
        if probe.parm(k) is not None:
            probe.parm(k).set(1)
    pev = hou.node(g.geo.path()).createNode("oceanevaluate::2.0", "probe_eval")
    pev.setInput(0, probe)
    pev.setInput(1, spec)
    pev.parm("time").setExpression("$T")
    pp = pev.geometry().points()
    same = abs(pp[0].position()[1] - pp[1].position()[1])
    h0 = pp[0].position()[1]
    probe.destroy()
    pev.destroy()
    # 升目の粗さ
    t0 = time.perf_counter()
    wave.cook(force=True)
    sec500 = time.perf_counter() - t0
    traps = [
        {"title": "Time に $T を書かないと、波が止まる",
         "body": f"Time を 0 のままにすると、フレーム 1 と {FRAME} で点の位置の差は最大 {frozen:.4f} m（まったく同じ）。"
                 "oceanevaluate は「何秒目の波か」を Time で受け取るので、$T を書いて再生とつなぐ。",
         "img": "", "cap": ""},
        {"title": "海は Grid Size ごとに同じ模様をくり返す",
         "body": f"50 m 離れた2点で波の高さをくらべると、差は {same:.6f} m（高さ {h0:.3f} m）で同じだった。"
                 "Grid Size 50 の設計図は 50 m ごとにくり返すので、50 m より広く写すと、同じ波の並びが2回出てくる。"
                 "撮る範囲が Grid Size を超えるときは、Grid Size を大きくしておく。",
         "img": "", "cap": ""},
        {"title": "泡のしきい値を低くすると、海が白っぽくなる",
         "body": f"風 9 m/秒・Chop 0.9 で、いちばん高い所と低い所の差は {wave_h:.2f} m、cusp が 0.15 を超えた点は全体の {foam_share * 100:.1f}% もあった。はじめ smooth(0.15, …) にしたら、海の半分近くに泡の白が混ざった。"
                 f"0.4 を超える点は {foam_real * 100:.1f}% で、泡らしい量になる。"
                 f"25 万点の板を動かすのに {sec500:.2f} 秒。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "10個（材質3つ）"], ["波の高低差", f"{wave_h:.2f} m"]], traps=traps)


if __name__ == "__main__":
    main()
