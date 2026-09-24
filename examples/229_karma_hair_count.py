# -*- coding: utf-8 -*-
"""実験229 — 毛（ヘア・ファー）を何本まで Karma で撮れるか。曲線のまま渡すのと、細い筒の面にするのとでどう違うか。

制作の問い: 動物の毛並みや芝生を作ると、毛が何十万本にもなる。/obj の Karma は曲線を、太さ（width）のある毛として描ける。
曲線のまま渡すのと、polywire で細い筒の面（ポリゴン）にして渡すのとで、時間はどう違うか。何本まで撮れるか。

  半径 0.5 m の球の表面に N 本の毛を生やす（VEX で 1 本 8 点の曲線。長さ 8 cm、少し外へ曲げる。根元の太さ 1 mm → 先 0.2 mm）。
    curves  … 曲線のまま（N = 1 万・10 万・100 万）
    polywire … polywire で太さ 1 mm の筒の面にする（N = 1 万・3 万）
  はじめに小さく 1 枚撮って捨てる。1 通りずつ、ほかの重い処理は回さない。
  測るもの: 640×360・8 サンプル＋ノイズ除去の撮る時間。同じ画を 2 回続けて撮り、1 回目（場面を Karma に渡す分を含む）と 2 回目を比べる。

    hython examples/229_karma_hair_count.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
CASES = [("curves", 10000), ("curves", 100000), ("curves", 1000000), ("polywire", 10000), ("polywire", 30000)]


def main():
    import hou
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "fur")
    ball = geo.createNode("sphere", "skin")
    ball.parm("type").set("polymesh")
    ball.parmTuple("rad").set((0.5, 0.5, 0.5))
    ball.parm("rows").set(48)
    ball.parm("cols").set(64)
    roots = geo.createNode("pointgenerate", "roots")
    grow = geo.createNode("attribwrangle", "grow_hair")
    grow.setInput(0, roots)
    grow.setInput(1, ball)
    grow.parm("snippet").set(
        "// 根元: 球の表面の乱数の位置。そこから外へ 8 cm、先ほど少し横へ曲げた 8 点の曲線を作る\n"
        "vector d = normalize(set(rand(@ptnum * 3 + 0.1), rand(@ptnum * 3 + 1.1), rand(@ptnum * 3 + 2.1)) - 0.5);\n"
        "vector root = d * 0.5;\n"
        "vector side = normalize(cross(d, {0, 1, 0.01}));\n"
        "int prim = addprim(0, 'polyline');\n"
        "for (int i = 0; i < 8; i++) {\n"
        "    float t = i / 7.0;\n"
        "    int p = addpoint(0, root + d * 0.08 * t + side * 0.02 * t * t);\n"
        "    setpointattrib(0, 'width', p, lerp(0.001, 0.0002, t));\n"
        "    setpointattrib(0, 'Cd', p, lerp({0.25, 0.16, 0.08}, {0.8, 0.65, 0.45}, t));\n"
        "    addvertex(0, prim, p);\n"
        "}\n"
        "removepoint(0, @ptnum);")
    wire = geo.createNode("polywire", "tubes")
    wire.setFirstInput(grow)
    wire.parm("radius").set(0.0005)   # 半径 0.5 mm（太さ 1 mm）
    if wire.parm("div") is not None:
        wire.parm("div").set(4)
    pick = geo.createNode("switch", "curves_or_tubes")
    pick.setInput(0, grow)
    pick.setInput(1, wire)
    skin_and_hair = geo.createNode("merge", "skin_and_hair")
    skin_and_hair.setInput(0, ball)
    skin_and_hair.setInput(1, pick)
    mat = hou.node("/mat").createNode("principledshader::2.0", "hair_mat")
    mat.parm("basecolor_usePointColor").set(1)
    mat.parm("rough").set(0.5)
    asg = geo.createNode("material", "assign")
    asg.setFirstInput(skin_and_hair)
    asg.parm("shop_materialpath1").set(mat.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    key = obj.createNode("hlight::2.0", "key")
    key.parm("light_type").set("distant")
    key.parm("light_intensity").set(3)
    key.parmTuple("r").set((-35, 40, 0))
    dome = obj.createNode("envlight", "sky")
    dome.parm("light_intensity").set(0.4)
    cam = obj.createNode("cam", "cam")
    cam.parmTuple("t").set((0, 0, 2.2))
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("oidn")

    def render(path):
        for n, v in (("resolutionx", 640), ("resolutiony", 360), ("samplesperpixel", 8), ("varianceaa_maxsamples", 8)):
            karma.parm(n).set(v)
        cam.parm("resx").set(640)
        cam.parm("resy").set(360)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        return time.perf_counter() - t0

    roots.parm("npts").set(1000)
    render(os.path.join(OUT, "_229_warm.png"))
    rows = []
    for kind, n in CASES:
        roots.parm("npts").set(n)
        pick.parm("input").set(0 if kind == "curves" else 1)
        g = pick.geometry()
        tag = f"{kind}_{n // 1000}k"
        first = render(os.path.join(OUT, f"229_{tag}.png"))
        again = render(os.path.join(OUT, f"_229_{tag}_again.png"))
        rows.append({"case": tag, "kind": kind, "count": n, "prims": len(g.prims()), "points": len(g.points()),
                     "sec_first": round(first, 2), "sec_again": round(again, 2)})
        print(rows[-1], flush=True)
    roots.parm("npts").set(100000)
    pick.parm("input").set(0)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "229_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "229_graph.json"), title="実験229")
    sop_bench.save(229, rows, {})


if __name__ == "__main__":
    main()
