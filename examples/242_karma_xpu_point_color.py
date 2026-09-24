# -*- coding: utf-8 -*-
"""実験242 — Karma XPU で色が白くなったのはなぜか。材質の Use Point Color と、点の色（Cd）の有る無しで切り分ける。

制作の問い: 実験232 で、XPU で撮るとドーナツのアイシングと海の空が白くなった。アイシングの材質は「色ピンク・Use Point Color 入り・点の色 Cd なし」、
海の空は「光る色（Emission）を Use Point Color で点の色から取る」だった。どの組み合わせで XPU の色が CPU と変わるのか。

  白い床の上に球を 6 つ並べ、それぞれ別の材質（principledshader）を当てて、CPU と XPU で撮る（別の hython で）。
    A 色ピンク・Use Point Color 切り・Cd なし
    B 色ピンク・Use Point Color 入り・Cd なし          （アイシングと同じ）
    C 色 白・Use Point Color 入り・Cd ピンク             （生地と同じ形）
    D 色ピンク・Use Point Color 入り・Cd 白
    E 光る色 白・Emission の Use Point Color 入り・Cd ピンク（海の空と同じ形）
    F 光る色ピンク・Emission の Use Point Color 切り
  明かりは白いドーム（強さ 1）。640×200・32 サンプル・ノイズ除去なし。球の真ん中（半径の 3 割の円）の色の平均を比べる。

    hython examples/242_karma_xpu_point_color.py cpu
    hython examples/242_karma_xpu_point_color.py xpu
    python examples/242_karma_xpu_point_color.py combine
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
CASES = [("A", dict(basecolor=PINK, basecolor_usePointColor=0), None),
         ("B", dict(basecolor=PINK, basecolor_usePointColor=1), None),
         ("C", dict(basecolor=(1, 1, 1), basecolor_usePointColor=1), PINK),
         ("D", dict(basecolor=PINK, basecolor_usePointColor=1), (1, 1, 1)),
         ("E", dict(basecolor=(0, 0, 0), emitcolor=(1, 1, 1), emitcolor_usePointColor=1, emitint=1.0, reflect=0.0), PINK),
         ("F", dict(basecolor=(0, 0, 0), emitcolor=PINK, emitcolor_usePointColor=0, emitint=1.0, reflect=0.0), None)]


def build():
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "balls")
    floor = geo.createNode("grid", "floor")
    floor.parmTuple("size").set((14, 6))
    fmat = hou.node("/mat").createNode("principledshader::2.0", "floor_white")
    fmat.parm("basecolor_usePointColor").set(0)
    fa = geo.createNode("material", "assign_floor")
    fa.setFirstInput(floor)
    fa.parm("shop_materialpath1").set(fmat.path())
    merge = geo.createNode("merge", "all")
    merge.setInput(0, fa)
    for i, (name, parms, cd) in enumerate(CASES):
        s = geo.createNode("sphere", f"ball_{name}")
        s.parm("type").set("polymesh")
        s.parmTuple("rad").set((0.9, 0.9, 0.9))
        s.parmTuple("t").set((-5.5 + i * 2.2, 0.9, 0))
        src = s
        if cd is not None:
            w = geo.createNode("attribwrangle", f"color_{name}")
            w.setFirstInput(s)
            w.parm("snippet").set(f"v@Cd = {{{cd[0]}, {cd[1]}, {cd[2]}}};")
            src = w
        m = hou.node("/mat").createNode("principledshader::2.0", f"mat_{name}")
        for k, v in parms.items():
            (m.parmTuple(k) if isinstance(v, tuple) else m.parm(k)).set(v)
        a = geo.createNode("material", f"assign_{name}")
        a.setFirstInput(src)
        a.parm("shop_materialpath1").set(m.path())
        merge.setInput(i + 1, a)
    merge.setDisplayFlag(True)
    merge.setRenderFlag(True)
    dome = obj.createNode("envlight", "white_dome")
    dome.parm("light_intensity").set(1)
    cam = obj.createNode("cam", "cam")
    cam.parm("projection").set("ortho")
    cam.parm("orthowidth").set(14)
    cam.parmTuple("t").set((0, 0.9, 10))
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(32)
    karma.parm("varianceaa_maxsamples").set(32)
    karma.parm("denoiser").set("off")
    geo.layoutChildren()
    return karma


def run(engine):
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    karma = build()
    karma.parm("engine").set(engine)
    karma.parm("picture").set(os.path.join(OUT, f"_242_warm_{engine}.exr").replace("\\", "/"))
    karma.render(frame_range=(1, 1, 1), verbose=False)
    exr = os.path.join(OUT, f"_242_{engine}.exr")
    karma.parm("picture").set(exr.replace("\\", "/"))
    t0 = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    sec = time.perf_counter() - t0
    px = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[:, :, :3]
    out = {"engine": engine, "sec": round(sec, 2), "balls": {}}
    ppm = RES[0] / 14.0                     # 1 m あたりの画素
    cy = RES[1] / 2.0                       # カメラは球の中心の高さ
    for i, (name, _, _) in enumerate(CASES):
        cx = (-5.5 + i * 2.2 + 7.0) * ppm
        r = 0.9 * ppm * 0.3
        yy, xx = np.mgrid[0:RES[1], 0:RES[0]]
        m = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
        out["balls"][name] = [round(float(v), 4) for v in px[m].mean(axis=0)]
    print(out, flush=True)
    view = np.clip(px, 0, 1) ** (1 / 2.2)
    ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
    ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
    ob.write(os.path.join(OUT, f"242_{engine}.png"))
    with open(os.path.join(OUT, f"242_part_{engine}.json"), "w", encoding="utf-8") as fp:
        json.dump(out, fp)
    if engine == "cpu":
        hou_tools.save_hip(os.path.join(OUT, "242_scene.hipnc"))
        hou_tools.write_graph("/obj/balls", os.path.join(OUT, "242_graph.json"), title="実験242")


def combine():
    import sop_bench
    parts = {}
    for e in ("cpu", "xpu"):
        with open(os.path.join(OUT, f"242_part_{e}.json"), encoding="utf-8") as fp:
            parts[e] = json.load(fp)
    rows = []
    for name, _, _ in CASES:
        c, x = parts["cpu"]["balls"][name], parts["xpu"]["balls"][name]
        rows.append({"case": name, "cpu": c, "xpu": x, "diff": round(sum(abs(a - b) for a, b in zip(c, x)) / 3, 4)})
        print(rows[-1])
    sop_bench.save(242, rows, {"res": RES, "cpu_sec": parts["cpu"]["sec"], "xpu_sec": parts["xpu"]["sec"]})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1])
