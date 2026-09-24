# -*- coding: utf-8 -*-
"""実験238 — 太陽を映す水面のきらめきは、Karma の Color Limit（明るすぎる光を切り詰める上限、既定 10）でどう変わるか。

制作の問い: 水面やガラスに太陽が映る場面では、ぽつぽつと白い点（ファイアフライ）が出やすい。Karma の Color Limit は
明るすぎる光を上限で切り詰めて、それを抑える。上げ下げすると、きらめきの明るさとざらつきはどう変わるか。

  実践「冬の朝の七里ヶ浜」の場面（out/pr_ocean_winter.hipnc、フレーム 30）で、Color Limit を 1・3・10（既定）・30・100・1000 にする
  （Indirect Color Limit は既定どおり Color Limit と同じ値）。640×360・16 サンプル（ノイズ除去なし）で撮る。
  測るもの: 撮る時間、光の道（太陽の下の水面、縦 200〜300・横 230〜330）の明るさの平均と、とても明るい画素（明るさ 5 超）の数、
            同じ Color Limit の 128 サンプルの画との差（光の道の中のざらつき）。

    hython examples/238_karma_color_limit_glitter.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)
FRAME = 30
LIMITS = (1, 3, 10, 30, 100, 1000)
PATH = (slice(200, 300), slice(230, 330))


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.load(os.path.join(OUT, "pr_ocean_winter.hipnc"), suppress_save_prompt=True)
    hou.setFrame(FRAME)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("off")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1])):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    default = karma.parm("colorlimit").eval()
    lum = lambda x: x[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722])  # noqa: E731

    def shoot(limit, spp, path):
        karma.parm("colorlimit").set(limit)
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        return time.perf_counter() - t0, oiio.ImageBuf(path).get_pixels(oiio.FLOAT)

    shoot(10, 1, os.path.join(OUT, "_238_warm.exr"))
    rows = []
    for lim in LIMITS:
        sec, img = shoot(lim, 16, os.path.join(OUT, f"_238_cl{lim}.exr"))
        _, ref = shoot(lim, 128, os.path.join(OUT, f"_238_cl{lim}_ref.exr"))
        a, b = lum(img)[PATH], lum(ref)[PATH]
        rows.append({"case": f"cl{lim}", "color_limit": lim, "sec": round(sec, 2), "path_mean": round(float(b.mean()), 4),
                     "hot_px": int((lum(img) > 5).sum()), "noise": round(float(np.sqrt(np.mean((a - b) ** 2)) / b.mean()), 4)})
        print(rows[-1], flush=True)
        view = np.clip(img[:, :, :3], 0, 1) ** (1 / 2.2)
        ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
        ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
        ob.write(os.path.join(OUT, f"238_cl{lim}.png"))
    for f in os.listdir(OUT):
        if f.startswith("_238_") and f.endswith(".exr"):
            os.remove(os.path.join(OUT, f))
    karma.parm("colorlimit").set(default)
    hou_tools.save_hip(os.path.join(OUT, "238_scene.hipnc"))
    hou_tools.write_graph("/obj/ocean_winter", os.path.join(OUT, "238_graph.json"), title="実験238")
    sop_bench.save(238, rows, {"res": RES, "frame": FRAME, "default_colorlimit": default, "path": [200, 300, 230, 330]})


if __name__ == "__main__":
    main()
