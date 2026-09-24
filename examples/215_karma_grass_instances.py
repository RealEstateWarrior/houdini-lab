# -*- coding: utf-8 -*-
"""実験215 — 草を何本まで Karma で撮れるか。パックしたまま（インスタンス）と、パックを解いた場合で、時間はどれだけ違うか。

制作の問い: 草原や森を作ると、同じ草や木を何万本も並べる。copytopoints の Pack and Instance を入れたまま撮るのと、
入れずに（ふつうの面として）撮るのとで、Karma の時間はどれだけ違うのか。本数を 10 倍にすると、時間は何倍になるのか。

  草 1 本 = 細い三角の葉を 3 枚（面 15 枚）。10 × 10 m の地面に scatter で点をまき、copytopoints で並べる
  （点ごとに向きと大きさを VEX でばらつかせる）。本数と並べ方を switch で切り替えて、同じカメラ（地面を斜め上から）で
  960×540・16 サンプル＋ノイズ除去で撮り、時間を測る。
    packed_1e4 / packed_1e5 / packed_1e6 … Pack and Instance を入れる（1 万・10 万・100 万本）
    flat_1e4 / flat_1e5                 … 入れない（面をそのまま複製。10 万本で面 150 万枚）
  1 枚目は起動の分だけ遅いので、小さく撮って捨てる。シーンは作り直さず、switch の番号だけ変える（作り直すと hython が落ちることがある）。

    hython examples/215_karma_grass_instances.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (960, 540)
CASES = [("packed_1e4", 10000, True), ("packed_1e5", 100000, True), ("packed_1e6", 1000000, True),
         ("flat_1e4", 10000, False), ("flat_1e5", 100000, False)]


def main():
    import hou
    import practice_kit as kit
    import sop_bench
    g = kit.Guide("exp215", "実験215", "", tags=[])
    blade = g.node("attribwrangle", "grass_blade", snippet=(
        "// 細い三角の葉を 3 枚、根元で 120° ずつ回して立てる。1 枚は 5 段の帯（面 5 枚）\n"
        "for (int k = 0; k < 3; k++) {\n"
        "    float a = radians(k * 120.0 + 15.0);\n"
        "    vector side = set(cos(a), 0, sin(a)) * 0.012;\n"
        "    vector lean = set(-sin(a), 0, cos(a)) * 0.05;\n"
        "    int prev_l = -1, prev_r = -1;\n"
        "    for (int i = 0; i <= 5; i++) {\n"
        "        float t = i / 5.0;\n"
        "        vector c = lean * t * t + set(0, t * 0.3, 0);\n"
        "        int l = addpoint(0, c - side * (1 - t));\n"
        "        int r = addpoint(0, c + side * (1 - t));\n"
        "        if (i > 0) addprim(0, 'poly', prev_l, prev_r, r, l);\n"
        "        prev_l = l; prev_r = r;\n"
        "    }\n"
        "}"))
    blade.parm("class").set(0)
    ground = g.node("grid", "ground", size=(10, 10), rows=2, cols=2)
    pts = g.node("scatter::2.0", "spots", [ground])
    pts.parm("npts").set(10000)
    vary = g.node("attribwrangle", "vary", [pts], snippet=(
        "// 草ごとに向き・大きさ・色をばらつかせる\n"
        "@orient = quaternion(radians(rand(@ptnum) * 360), {0, 1, 0});\n"
        "@pscale = fit01(rand(@ptnum + 3), 0.6, 1.4);\n"
        "// rand() は小数もベクトルも返せるので、lerp() の中では float() で小数だと決める（書かないと Ambiguous call のエラー）\n"
        "@Cd = lerp({0.10, 0.28, 0.05}, {0.35, 0.45, 0.12}, float(rand(@ptnum + 7)));"))
    packed = g.node("copytopoints::2.0", "grass_packed", [blade, vary], pack=1, targetattribs=1)
    packed.parm("applyattribs1").set("Cd")
    packed.parm("applyto1").set("points")
    flat = g.node("copytopoints::2.0", "grass_flat", [blade, vary], pack=0, targetattribs=1)
    flat.parm("applyattribs1").set("Cd")
    flat.parm("applyto1").set("prims")
    pick = g.node("switch", "packed_or_flat", [packed, flat])
    grass_m = g.mat("grass_mat", basecolor=(1, 1, 1), rough=0.6)
    grass_m.parm("basecolor_usePointColor").set(1)
    soil_m = g.mat("soil_mat", basecolor=(0.12, 0.09, 0.06), rough=0.9)
    final = g.node("merge", "field", [g.assign(ground, soil_m, "assign_soil"), g.assign(pick, grass_m, "assign_grass")])
    bbox = hou.BoundingBox(-5, 0, -5, 5, 0.4, 5)
    if os.environ.get("DRY"):
        for tag, n, is_packed in CASES[:1] + CASES[3:4]:
            pts.parm("npts").set(n)
            pick.parm("input").set(0 if is_packed else 1)
            geo = pick.geometry()
            for nd in g.geo.children():
                if nd.errors():
                    print("ERR", nd.name(), nd.errors()[:1])
            if geo is None:
                continue
            print(tag, geo.intrinsicValue("primitivecount"), geo.intrinsicValue("pointcount"), len(blade.geometry().prims()))
        return
    g.hero(final, "", direction=(0.0, 0.55, 1.0), res=(240, 135), spp=4, bbox=bbox, margin=0.9, floor=False)   # 温め（捨てる）
    karma = hou.node("/out/hero_karma")
    cam = hou.node("/obj/hero_cam")
    for p, v in (("resx", RES[0]), ("resy", RES[1])):
        cam.parm(p).set(v)
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(16)
    karma.parm("varianceaa_maxsamples").set(16)
    karma.parm("denoiser").set("oidn")
    rows = []
    for tag, n, is_packed in CASES:
        pts.parm("npts").set(n)
        pick.parm("input").set(0 if is_packed else 1)
        t0 = time.perf_counter()
        geo = pick.geometry()
        cook = time.perf_counter() - t0
        info = {"case": tag, "count": n, "packed": is_packed, "cook_sec": round(cook, 2),
                "prims": geo.intrinsicValue("primitivecount"), "points": geo.intrinsicValue("pointcount")}
        path = os.path.join(OUT, f"215_{tag}.png")
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(hou.frame(), hou.frame(), 1), verbose=False)
        info["sec"] = round(time.perf_counter() - t0, 2)
        rows.append(info)
        print(info, flush=True)
    import hou_tools
    pts.parm("npts").set(10000)
    pick.parm("input").set(0)
    g.geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "215_scene.hipnc"))
    hou_tools.write_graph(g.geo.path(), os.path.join(OUT, "215_graph.json"), title="実験215")
    sop_bench.save(215, rows, {"res": RES, "spp": 16, "blade_prims": len(blade.geometry().prims())})


if __name__ == "__main__":
    main()
