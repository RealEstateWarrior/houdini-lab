# -*- coding: utf-8 -*-
"""実験236 — 氷の入ったグラスの水が黒ずむのは、Karma の Refraction Limit（光が透けて曲がるのを何回まで追うか）のせいか。

制作の問い: ガラスのコップに水と氷を入れて撮ると、氷や水の奥が黒く抜けることがある。光はガラスの外側・内側・水・氷と、
何度も境目を通り抜けるので、途中で追うのをやめると、そこが黒くなる。Refraction Limit（既定 4）はいくつにすればよいか。

  実践「氷の入ったグラスの水」の場面（out/pr_glasscup.hipnc）で、Refraction Limit を 1・2・4（既定）・8・16 にして、
  640×360・32 サンプル（ノイズ除去なし）で撮る。はじめに小さく 1 枚撮って捨てる。
  測るもの: 撮る時間、グラスの中（画の真ん中の縦長の窓）の明るさの平均と、暗い画素（明るさ 0.03 未満）の割合。

    hython examples/236_karma_glass_refraction_limit.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)
LIMITS = (1, 2, 4, 8, 16)
WIN = (slice(60, 330), slice(250, 390))     # グラスの中（縦 60〜330・横 250〜390）


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.load(os.path.join(OUT, "pr_glasscup.hipnc"), suppress_save_prompt=True)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("off")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 32), ("varianceaa_maxsamples", 32)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    default = karma.parm("refractionlimit").eval()
    lum = lambda x: x[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722])  # noqa: E731

    def shoot(limit, path):
        karma.parm("refractionlimit").set(limit)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        return time.perf_counter() - t0, oiio.ImageBuf(path).get_pixels(oiio.FLOAT)

    karma.parm("samplesperpixel").set(1)
    karma.parm("varianceaa_maxsamples").set(1)
    shoot(4, os.path.join(OUT, "_236_warm.exr"))
    karma.parm("samplesperpixel").set(32)
    karma.parm("varianceaa_maxsamples").set(32)
    rows = []
    for lim in LIMITS:
        sec, img = shoot(lim, os.path.join(OUT, f"_236_rl{lim}.exr"))
        L = lum(img)[WIN]
        rows.append({"case": f"rl{lim}", "refraction_limit": lim, "sec": round(sec, 2), "glass_mean": round(float(L.mean()), 4),
                     "dark_share": round(float((L < 0.03).mean()), 4)})
        print(rows[-1], flush=True)
        view = np.clip(img[:, :, :3], 0, 1) ** (1 / 2.2)
        ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
        ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
        ob.write(os.path.join(OUT, f"236_rl{lim}.png"))
    for f in os.listdir(OUT):
        if f.startswith("_236_") and f.endswith(".exr"):
            os.remove(os.path.join(OUT, f))
    karma.parm("refractionlimit").set(default)
    hou_tools.save_hip(os.path.join(OUT, "236_scene.hipnc"))
    hou_tools.write_graph("/obj/glasscup", os.path.join(OUT, "236_graph.json"), title="実験236")
    sop_bench.save(236, rows, {"res": RES, "spp": 32, "default_refractionlimit": default, "window": [60, 330, 250, 390]})


if __name__ == "__main__":
    main()
