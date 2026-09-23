# -*- coding: utf-8 -*-
"""実験203 — 氷の入ったグラスの水を Karma で撮ると、何が時間を食うのか。どうすれば短くなるか。

制作の問い: 実践「氷の入ったグラスの水」を 1280×720・96 サンプルで撮ろうとしたら、25 分たっても終わらなかった。
透明な物（ガラス・水・氷）を重ねると何倍かかるのか。屈折の回数の上限（Refraction Limit）や、
水とガラスのすき間は時間に効くのか。

  グラス（断面を revolve、厚い底）・水（内側を 0.2 mm すき間をあけて revolve）・氷3つ（角を丸めた箱）を、
  practice_kit と同じ撮り方（暗い幕・キー・リム・ドーム）で、480×270・16 サンプルに下げて1枚ずつ撮り、時間を測る。
    glass      … グラスだけ
    glass_water… グラス＋水
    full       … グラス＋水＋氷
    refr2 / refr8 … full の Refraction Limit を 2 / 8（既定 4）
    opaque_ice … full の氷を透けない白にする
    nogap      … full の水をガラスの内側にぴったり合わせる（すき間 0）

    hython examples/203_karma_glass_cost.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

RES = (480, 270)
SPP = 16
WATER_TOP = 0.07


def build(g):
    import hou
    prof = g.node("attribwrangle", "glass_profile", snippet=(
        "vector pts[] = {{0.0, 0.0, 0}, {0.030, 0.0, 0}, {0.032, 0.002, 0}, {0.036, 0.100, 0}, {0.0355, 0.1012, 0},"
        " {0.0343, 0.1012, 0}, {0.0335, 0.100, 0}, {0.030, 0.010, 0}, {0.028, 0.008, 0}, {0.0, 0.008, 0}};\n"
        "int prim = addprim(0, 'poly');\n"
        "foreach (vector p; pts) addvertex(0, prim, addpoint(0, p));"))
    prof.parm("class").set(0)
    cup = g.node("revolve::2.0", "glass", [prof], divs=96)
    wprof = g.node("attribwrangle", "water_profile", snippet=(
        f"float top = {WATER_TOP};\n"
        "float gap = chf('gap');\n"
        "float r_top = 0.030 + (top - 0.010) / 0.090 * 0.0035 - gap;\n"
        "vector pts[] = {{0.0, 0.0080, 0}, {0.028, 0.0080, 0}, {0.030, 0.010, 0}};\n"
        "pts[0].y += gap; pts[1].y += gap; pts[1].x -= gap; pts[2].x -= gap; pts[2].y += gap;\n"
        "append(pts, set(r_top, top, 0));\n"
        "append(pts, set(0.0, top, 0));\n"
        "int prim = addprim(0, 'poly');\n"
        "foreach (vector p; pts) addvertex(0, prim, addpoint(0, p));"))
    wprof.parm("class").set(0)
    grp = wprof.parmTemplateGroup()
    grp.append(hou.FloatParmTemplate("gap", "gap", 1, default_value=(0.0002,)))
    wprof.setParmTemplateGroup(grp)
    water = g.node("revolve::2.0", "water", [wprof], divs=96)
    cube = g.node("box", "ice_block", size=(0.021, 0.019, 0.02))
    soft = g.node("polybevel::3.0", "melted_edges", [cube], offset=0.003, divisions=3)
    spots = g.node("attribwrangle", "ice_spots", snippet=(
        f"vector places[] = {{{{-0.011, {WATER_TOP - 0.004}, 0.006}}, {{0.012, {WATER_TOP - 0.006}, -0.004}}, {{0.0, {WATER_TOP - 0.021}, -0.012}}}};\n"
        "for (int i = 0; i < 3; i++) {\n"
        "    int p = addpoint(0, places[i]);\n"
        "    setpointattrib(0, 'orient', p, quaternion(radians(set(rand(i) * 40 - 20, rand(i + 5) * 360, rand(i + 9) * 40 - 20)), 0));\n"
        "}"))
    spots.parm("class").set(0)
    ice = g.node("copytopoints::2.0", "ice", [soft, spots])
    glass_m = g.mat("glass_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.5, transparency=1.0)
    water_m = g.mat("water_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=1.33, transparency=1.0,
                    transcolor=(0.8, 0.93, 0.95), transdist=0.2)
    ice_m = g.mat("ice_mat", basecolor=(1, 1, 1), rough=0.08, reflect=1.0, ior=1.31, transparency=1.0)
    a_cup = g.assign(cup, glass_m, "assign_glass")
    a_water = g.assign(water, water_m, "assign_water")
    a_ice = g.assign(ice, ice_m, "assign_ice")
    final = g.node("merge", "drink", [a_cup, a_water, a_ice])
    return final, wprof, ice_m


def shot(g, final, name, light=1.0, spp=SPP, res=RES):
    import hou
    g.id = f"exp203_{name}"
    g.hero(final, "", direction=(1.0, 0.25, 1.2), key=2.5 * light, rim=10.0 * light, dome=0.4 * light, spp=spp, margin=1.15,
           backdrop=(0.35, 0.36, 0.38), bbox=hou.BoundingBox(-0.04, 0, -0.04, 0.04, 0.105, 0.04), res=res)
    return round(g.hero_sec, 2)


def main():
    import hou
    g = kit.Guide("exp203", "実験203", "", tags=[])
    final, wprof, ice_m = build(g)
    karma = None
    rows = []

    def set_inputs(n):
        for i in range(3):
            final.setInput(i, None)
        for i, src in enumerate(["assign_glass", "assign_water", "assign_ice"][:n]):
            final.setInput(i, g.geo.node(src))

    set_inputs(1)
    shot(g, final, "warmup")   # 1 回目は起動の分だけ遅いので捨てる
    for name, n in (("glass", 1), ("glass_water", 2), ("full", 3)):
        set_inputs(n)
        rows.append({"case": name, "sec": shot(g, final, name)})
        print(rows[-1], flush=True)
    karma = hou.node("/out/hero_karma")
    for lim in (2, 8):
        karma.parm("refractionlimit").set(lim)
        rows.append({"case": f"refr{lim}", "sec": shot(g, final, f"refr{lim}")})
        print(rows[-1], flush=True)
    karma.parm("refractionlimit").set(4)
    ice_m.parm("transparency").set(0.0)
    rows.append({"case": "opaque_ice", "sec": shot(g, final, "opaque_ice")})
    print(rows[-1], flush=True)
    ice_m.parm("transparency").set(1.0)
    wprof.parm("gap").set(0.0)
    rows.append({"case": "nogap", "sec": shot(g, final, "nogap")})
    print(rows[-1], flush=True)
    wprof.parm("gap").set(0.0002)
    # 基準：3つとも透けない材質にしたとき
    mats = [hou.node("/mat/" + m) for m in ("glass_mat", "water_mat", "ice_mat")]
    for m in mats:
        m.parm("transparency").set(0.0)
    rows.append({"case": "opaque_all", "sec": shot(g, final, "opaque_all")})
    print(rows[-1], flush=True)
    rows.append({"case": "opaque_dim", "sec": shot(g, final, "opaque_dim", light=0.25)})
    print(rows[-1], flush=True)
    for m in mats:
        m.parm("transparency").set(1.0)
    rows.append({"case": "full_dim", "sec": shot(g, final, "full_dim", light=0.25)})
    print(rows[-1], flush=True)
    karma = hou.node("/out/hero_karma")
    samp = {p.name(): p.eval() for p in karma.parms() if "variance" in p.name() or "convergence" in p.name()}
    print("サンプルの決め方:", samp, flush=True)
    # 1 枚ごとの準備の時間と、サンプルが増えるぶんの時間を分ける（16 と 64 サンプルで撮り比べる）
    for m in mats:
        m.parm("transparency").set(0.0)
    rows.append({"case": "opaque_spp64", "sec": shot(g, final, "opaque_spp64", spp=64)})
    print(rows[-1], flush=True)
    for m in mats:
        m.parm("transparency").set(1.0)
    rows.append({"case": "full_spp64", "sec": shot(g, final, "full_spp64", spp=64)})
    print(rows[-1], flush=True)
    rows.append({"case": "full_960_spp16", "sec": shot(g, final, "full_960_spp16", res=(960, 540))})
    print(rows[-1], flush=True)
    g.save(facts=[], traps=[])
    os.replace(os.path.join(kit.OUT, "pr_exp203_nogap.hipnc"), os.path.join(kit.OUT, "203_scene.hipnc")) \
        if os.path.exists(os.path.join(kit.OUT, "pr_exp203_nogap.hipnc")) else None
    with open(os.path.join(kit.OUT, "203_stats.json"), "w", encoding="utf-8") as fp:
        json.dump({"res": RES, "spp": SPP, "rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた: 203_stats.json")


if __name__ == "__main__":
    main()
