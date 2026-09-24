# -*- coding: utf-8 -*-
"""実験228 — 火花・雪・雨のような粒を、Karma で何百万個まで撮れるか。点のまま渡すのと、小さな球を並べるのとでどう違うか。

制作の問い: 粒のエフェクト（火花・雪・雨・砂ぼこり）は、粒の数が何十万〜何百万になる。/obj の Karma に点のまま渡すと、
Karma は点を小さな球として描く（半径は pscale）。実験222 では、パックした形を /obj の Karma に何万個も渡すと、場面を渡すだけで何分もかかった。
粒ならどうか。

  4 m 四方・高さ 4 m の箱の中に、N 個の点を乱数で散らす（pointgenerate＋VEX。pscale 0.005 = 半径 5 mm。色は白）。
    points  … 点のまま（N = 1 万・10 万・100 万・1000 万）
    spheres … 半径 5 mm の球（面 48 枚）を copytopoints でパックして並べる（N = 1 万・3 万）
  はじめに小さく 1 枚撮って捨てる。1 通りずつ、ほかの重い処理は回さない。
  測るもの: 640×360・8 サンプル＋ノイズ除去の撮る時間。同じ画を 2 回続けて撮り、1 回目（場面を Karma に渡す分を含む）と 2 回目を比べる。

    hython examples/228_karma_points_count.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
CASES = [("points", 10000), ("points", 100000), ("points", 1000000), ("points", 10000000), ("spheres", 10000), ("spheres", 30000)]


def main():
    import hou
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "particles")
    # 点を N 個作って、4 m 四方・高さ 4 m の箱の中に乱数で散らす
    # （はじめは scatter でまいたが、scatter は 100 万個が上限で、1000 万を指定しても 100 万個だった）
    pts = geo.createNode("pointgenerate", "spots")
    look = geo.createNode("attribwrangle", "size_and_color")
    look.setFirstInput(pts)
    look.parm("snippet").set("@P = set(rand(@ptnum * 3 + 0.1) * 4 - 2, rand(@ptnum * 3 + 1.1) * 4, rand(@ptnum * 3 + 2.1) * 4 - 2);\n"
                             "f@pscale = 0.005;\nv@Cd = {0.9, 0.9, 0.9};")
    ball = geo.createNode("sphere", "ball")
    ball.parm("type").set("polymesh")
    ball.parm("rows").set(6)
    ball.parm("cols").set(8)
    ball.parmTuple("rad").set((1, 1, 1))
    cp = geo.createNode("copytopoints::2.0", "balls")
    cp.setInput(0, ball)
    cp.setInput(1, look)
    cp.parm("pack").set(1)
    pick = geo.createNode("switch", "points_or_spheres")
    pick.setInput(0, look)
    pick.setInput(1, cp)
    mat = hou.node("/mat").createNode("principledshader::2.0", "white")
    mat.parm("basecolor_usePointColor").set(1)
    asg = geo.createNode("material", "assign")
    asg.setFirstInput(pick)
    asg.parm("shop_materialpath1").set(mat.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    key = obj.createNode("hlight::2.0", "key")
    key.parm("light_type").set("distant")
    key.parm("light_intensity").set(3)
    key.parmTuple("r").set((-45, 30, 0))
    cam = obj.createNode("cam", "cam")
    cam.parmTuple("t").set((0, 2, 9))
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("oidn")

    def render(path, res, spp):
        for n, v in (("resolutionx", res[0]), ("resolutiony", res[1]), ("samplesperpixel", spp), ("varianceaa_maxsamples", spp)):
            karma.parm(n).set(v)
        cam.parm("resx").set(res[0])
        cam.parm("resy").set(res[1])
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        return time.perf_counter() - t0

    pts.parm("npts").set(1000)
    render(os.path.join(OUT, "_228_warm.png"), (64, 36), 1)
    rows = []
    for kind, n in CASES:
        pts.parm("npts").set(n)
        pick.parm("input").set(0 if kind == "points" else 1)
        t0 = time.perf_counter()
        pick.geometry()
        cook = time.perf_counter() - t0
        tag = f"{kind}_{n // 1000}k"
        # 同じ画を 2 回続けて撮る。1 回目は場面を Karma に渡す分を含み、2 回目は変わっていない場面をそのまま使う
        first = render(os.path.join(OUT, f"228_{tag}.png"), (640, 360), 8)
        again = render(os.path.join(OUT, f"_228_{tag}_again.png"), (640, 360), 8)
        n_real = len(look.geometry().points())
        rows.append({"case": tag, "kind": kind, "count": n, "points_real": n_real, "cook_sec": round(cook, 2),
                     "sec_first": round(first, 2), "sec_again": round(again, 2)})
        print(rows[-1], flush=True)
    pts.parm("npts").set(100000)
    pick.parm("input").set(0)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "228_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "228_graph.json"), title="実験228")
    sop_bench.save(228, rows, {"pscale": 0.005})


if __name__ == "__main__":
    main()
