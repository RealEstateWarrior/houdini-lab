# -*- coding: utf-8 -*-
"""実験234 — 窓の光で部屋の中を照らすとき、Karma の Diffuse Limit（光が面で跳ね返るのを何回まで追うか）はいくつにすればよいか。

制作の問い: 室内を窓の光だけで照らすと、部屋が暗く写ることがある。Karma の Diffuse Limit は既定 1。
壁から壁へ跳ね返る光をどこまで追えば、部屋の明るさが落ち着くのか。時間とざらつきはどう変わるか。

  6 × 5 m・高さ 3 m の部屋（壁・床・天井は principledshader の色 0.7、Roughness 0.8）。一方の壁に 1.6 × 1.2 m の窓を開け、
  外から太陽（distant、強さ 4、窓から斜めに差し込む）と空（envlight、強さ 1）で照らす。カメラは部屋の中から窓と反対の奥の壁を見る。
  Diffuse Limit を 0・1（既定）・2・4・8・16 にして、640×360・32 サンプル（ノイズ除去なし）で撮る。
  測るもの: 撮る時間、画の明るさの平均（右下の透かしは除く）、Diffuse Limit 16・256 サンプルの画との差（ざらつきと明るさの足りなさ）。

    hython examples/234_karma_diffuse_limit_room.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)
LIMITS = (0, 1, 2, 4, 8, 16)


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "room")
    W, D, H = 6.0, 5.0, 3.0
    panels = []

    def panel(name, size, t, r=(0, 0, 0)):
        g = geo.createNode("grid", name)
        g.parmTuple("size").set(size)
        g.parm("rows").set(2)
        g.parm("cols").set(2)
        g.parmTuple("r").set(r)
        g.parmTuple("t").set(t)
        panels.append(g)

    panel("floor", (W, D), (0, 0, 0))
    panel("ceiling", (W, D), (0, H, 0))
    panel("wall_back", (W, H), (0, H / 2, -D / 2), (90, 0, 0))
    panel("wall_left", (D, H), (-W / 2, H / 2, 0), (90, 90, 0))
    panel("wall_right", (D, H), (W / 2, H / 2, 0), (90, 90, 0))
    # 窓のある壁（手前 z = +D/2）: 1.6 × 1.2 m の穴のまわりを 4 枚で囲む。窓の下端は床から 0.9 m
    wx, wy0, wy1 = 0.8, 0.9, 2.1
    panel("win_left", ((W / 2 - wx), H), (-(W / 2 + wx) / 2, H / 2, D / 2), (90, 0, 0))
    panel("win_right", ((W / 2 - wx), H), ((W / 2 + wx) / 2, H / 2, D / 2), (90, 0, 0))
    panel("win_below", (2 * wx, wy0), (0, wy0 / 2, D / 2), (90, 0, 0))
    panel("win_above", (2 * wx, H - wy1), (0, (wy1 + H) / 2, D / 2), (90, 0, 0))
    room = geo.createNode("merge", "walls")
    for i, p in enumerate(panels):
        room.setInput(i, p)
    mat = hou.node("/mat").createNode("principledshader::2.0", "wall")
    mat.parmTuple("basecolor").set((0.7, 0.7, 0.7))
    mat.parm("rough").set(0.8)
    mat.parm("reflect").set(0.2)
    asg = geo.createNode("material", "assign")
    asg.setFirstInput(room)
    asg.parm("shop_materialpath1").set(mat.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    sun = obj.createNode("hlight::2.0", "sun")
    sun.parm("light_type").set("distant")
    sun.parm("light_intensity").set(4)
    sun.parmTuple("light_color").set((1.0, 0.95, 0.85))
    sun.parmTuple("r").set((-35, 20, 0))       # 窓（+z）の外から、斜め下へ差し込む
    sky = obj.createNode("envlight", "sky")
    sky.parm("light_intensity").set(1)
    sky.parmTuple("light_color").set((0.6, 0.75, 1.0))
    cam = obj.createNode("cam", "cam")
    cam.parmTuple("t").set((0.8, 1.5, 2.2))
    cam.parmTuple("r").set((-5, 12, 0))
    cam.parm("focal").set(18)
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma.parm("denoiser").set("off")

    def shoot(limit, spp, path):
        karma.parm("diffuselimit").set(limit)
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        return time.perf_counter() - t0, oiio.ImageBuf(path).get_pixels(oiio.FLOAT)[:, :, :3]

    keep = np.ones((RES[1], RES[0]), bool)
    keep[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False
    lum = lambda x: x @ np.array([0.2126, 0.7152, 0.0722])  # noqa: E731
    shoot(1, 1, os.path.join(OUT, "_234_warm.exr"))
    sec_ref, ref = shoot(16, 256, os.path.join(OUT, "_234_ref.exr"))
    lref = lum(ref)[keep]
    rows = []
    for lim in LIMITS:
        sec, img = shoot(lim, 32, os.path.join(OUT, f"_234_dl{lim}.exr"))
        li = lum(img)[keep]
        rows.append({"case": f"dl{lim}", "diffuse_limit": lim, "sec": round(sec, 2), "mean": round(float(li.mean()), 4),
                     "mean_ratio": round(float(li.mean() / lref.mean()), 4),
                     "rms_to_ref": round(float(np.sqrt(np.mean((li - lref) ** 2)) / lref.mean()), 4)})
        print(rows[-1], flush=True)
        view = np.clip(img, 0, 1) ** (1 / 2.2)
        ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
        ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
        ob.write(os.path.join(OUT, f"234_dl{lim}.png"))
    for f in os.listdir(OUT):
        if f.startswith("_234_") and f.endswith(".exr"):
            os.remove(os.path.join(OUT, f))
    karma.parm("diffuselimit").set(4)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "234_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "234_graph.json"), title="実験234")
    sop_bench.save(234, rows, {"res": RES, "spp": 32, "ref": {"limit": 16, "spp": 256, "sec": round(sec_ref, 2), "mean": round(float(lref.mean()), 4)}})


if __name__ == "__main__":
    main()
