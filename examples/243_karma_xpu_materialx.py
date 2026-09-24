# -*- coding: utf-8 -*-
"""実験243 — Karma XPU で材質の色を効かせるには。MaterialX の材質（mtlxstandard_surface）なら色は出るか。

制作の問い: 実験242 で、XPU では principledshader の色（Base Color）が効かず白くなった。点の色（Cd）で塗るほかに、
MaterialX の材質（/mat の mtlxstandard_surface）を当てれば、XPU でも材質の色が出るのか。CPU と同じ色になるのか。

  実験242 と同じ並べ方で球を 4 つ置き、CPU と XPU で撮る（別の hython）。
    P  principledshader・Base Color ピンク（実験242 の A と同じ）
    M  mtlxstandard_surface・Base Color ピンク
    MR mtlxstandard_surface・Base Color 赤（1, 0.1, 0.1）
    ME mtlxstandard_surface・Emission ピンク（Emission 1、Base 0）
  明かりは白いドーム（強さ 1）。640×200・32 サンプル・ノイズ除去なし。球の真ん中の色の平均を比べる。

    hython examples/243_karma_xpu_materialx.py cpu
    hython examples/243_karma_xpu_materialx.py xpu
    python examples/243_karma_xpu_materialx.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 200)
PINK = (0.95, 0.45, 0.66)
CASES = ["P", "Pw", "Pk", "M", "Mw", "MR", "ME"]
# Pw・Mw は点の色 Cd を白、Pk は Cd を黒にした球（材質の Use Point Color は切り）。実験242 では、Cd を持つ球と merge した球の色が XPU で白くなった


def material(name):
    import hou
    m = hou.node("/mat")
    if name in ("P", "Pw", "Pk"):
        n = m.createNode("principledshader::2.0", "mat_P")
        n.parmTuple("basecolor").set(PINK)
        n.parm("basecolor_usePointColor").set(0)
        return n
    n = m.createNode("mtlxstandard_surface", f"mat_{name}")
    col = PINK if name in ("M", "ME", "Mw") else (1.0, 0.1, 0.1)
    if name == "ME":
        n.parm("base").set(0)
        n.parm("emission").set(1)
        n.parmTuple("emission_color").set(col)
    else:
        n.parmTuple("base_color").set(col)
    return n


def run(engine):
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "balls")
    merge = geo.createNode("merge", "all")
    for i, name in enumerate(CASES):
        s = geo.createNode("sphere", f"ball_{name}")
        s.parm("type").set("polymesh")
        s.parmTuple("rad").set((0.9, 0.9, 0.9))
        s.parmTuple("t").set((-6.6 + i * 2.2, 0.9, 0))
        src = s
        if name in ("Pw", "Pk", "Mw"):
            w = geo.createNode("attribwrangle", f"color_{name}")
            w.setFirstInput(s)
            w.parm("snippet").set("v@Cd = {0, 0, 0};" if name == "Pk" else "v@Cd = {1, 1, 1};")
            src = w
        a = geo.createNode("material", f"assign_{name}")
        a.setFirstInput(src)
        a.parm("shop_materialpath1").set(material(name).path())
        merge.setInput(i, a)
    merge.setDisplayFlag(True)
    merge.setRenderFlag(True)
    dome = obj.createNode("envlight", "white_dome")
    dome.parm("light_intensity").set(1)
    cam = obj.createNode("cam", "cam")
    cam.parm("projection").set("ortho")
    cam.parm("orthowidth").set(16)
    cam.parmTuple("t").set((0, 0.9, 10))
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 32), ("varianceaa_maxsamples", 32)):
        karma.parm(n).set(v)
    karma.parm("denoiser").set("off")
    karma.parm("engine").set(engine)
    karma.parm("picture").set(os.path.join(OUT, f"_243_warm_{engine}.exr").replace("\\", "/"))
    karma.render(frame_range=(1, 1, 1), verbose=False)
    exr = os.path.join(OUT, f"_243_{engine}.exr")
    karma.parm("picture").set(exr.replace("\\", "/"))
    t0 = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    sec = time.perf_counter() - t0
    px = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[:, :, :3]
    out = {"engine": engine, "sec": round(sec, 2), "balls": {}}
    ppm = RES[0] / 16.0
    yy, xx = np.mgrid[0:RES[1], 0:RES[0]]
    for i, name in enumerate(CASES):
        cx = (-6.6 + i * 2.2 + 8.0) * ppm
        r = 0.9 * ppm * 0.3
        m = (xx - cx) ** 2 + (yy - RES[1] / 2.0) ** 2 < r * r
        out["balls"][name] = [round(float(v), 4) for v in px[m].mean(axis=0)]
    print(out, flush=True)
    view = np.clip(px, 0, 1) ** (1 / 2.2)
    ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
    ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
    ob.write(os.path.join(OUT, f"243_{engine}.png"))
    with open(os.path.join(OUT, f"243_part_{engine}.json"), "w", encoding="utf-8") as fp:
        json.dump(out, fp)
    if engine == "cpu":
        geo.layoutChildren()
        hou_tools.save_hip(os.path.join(OUT, "243_scene.hipnc"))
        hou_tools.write_graph("/obj/balls", os.path.join(OUT, "243_graph.json"), title="実験243")


def combine():
    import sop_bench
    parts = {}
    for e in ("cpu", "xpu"):
        with open(os.path.join(OUT, f"243_part_{e}.json"), encoding="utf-8") as fp:
            parts[e] = json.load(fp)
    rows = []
    for name in CASES:
        c, x = parts["cpu"]["balls"][name], parts["xpu"]["balls"][name]
        rows.append({"case": name, "cpu": c, "xpu": x, "diff": round(sum(abs(a - b) for a, b in zip(c, x)) / 3, 4)})
        print(rows[-1])
    sop_bench.save(243, rows, {"res": RES, "cpu_sec": parts["cpu"]["sec"], "xpu_sec": parts["xpu"]["sec"]})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1])
