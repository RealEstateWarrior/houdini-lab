# -*- coding: utf-8 -*-
"""実験235 — 雲が灰色で重たく見えるのは、Karma の Volume Limit（雲の中で光が散らばるのを何回まで追うか）のせいか。

制作の問い: 本物の積雲は、日陰の側や底でも明るい灰白色で、中から光っているように見える。CG の雲は底が暗く重たくなりやすい。
Karma の Volume Limit（既定 0）を上げると、雲はどう明るくなるのか。時間はどれだけ延びるのか。

  実践「もくもくの雲を浮かべる」の場面（out/pr_cloud.hipnc。太陽 distant 強さ 4・空のドーム 0.5）を使う。
  Volume Limit を 0（既定）・1・2・4・8・16 にして、640×360・32 サンプル（ノイズ除去なし）で撮る。
  雲の範囲（雲の濃さが写っている画素）を、上半分（日の当たる側）と下半分（底）に分け、明るさの平均を比べる。
  Volume Limit 16 の画を基準に、明るさが何 % 出ているかを見る。はじめに小さく 1 枚撮って捨てる。

    hython examples/235_karma_cloud_volume_limit.py
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
    hou.hipFile.load(os.path.join(OUT, "pr_cloud.hipnc"), suppress_save_prompt=True)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("off")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 32), ("varianceaa_maxsamples", 32)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    default = karma.parm("volumelimit").eval()

    def shoot(limit, path):
        karma.parm("volumelimit").set(limit)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        buf = oiio.ImageBuf(path)
        return time.perf_counter() - t0, buf.get_pixels(oiio.FLOAT)

    shoot(0, os.path.join(OUT, "_235_warm.exr"))
    imgs, secs = {}, {}
    for lim in LIMITS:
        secs[lim], imgs[lim] = shoot(lim, os.path.join(OUT, f"_235_vl{lim}.exr"))
        print(lim, round(secs[lim], 2), flush=True)
    # 雲の範囲: 基準の画で、アルファ（雲や幕が写っている）ではなく、背景の幕より明るい所。幕は暗い青なので、明るさ 0.15 を超える所を雲とする
    lum = lambda x: x[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722])  # noqa: E731
    ref = lum(imgs[16])
    cloud = ref > 0.15
    cloud[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False     # 右下の透かし
    ys = np.nonzero(cloud)[0]
    mid = int(np.median(ys))
    top = cloud.copy()
    top[mid:] = False
    bottom = cloud.copy()
    bottom[:mid] = False
    rows = []
    for lim in LIMITS:
        L = lum(imgs[lim])
        rows.append({"case": f"vl{lim}", "volume_limit": lim, "sec": round(secs[lim], 2),
                     "top": round(float(L[top].mean()), 4), "bottom": round(float(L[bottom].mean()), 4),
                     "top_ratio": round(float(L[top].mean() / ref[top].mean()), 4),
                     "bottom_ratio": round(float(L[bottom].mean() / ref[bottom].mean()), 4)})
        print(rows[-1], flush=True)
        view = np.clip(imgs[lim][:, :, :3], 0, 1) ** (1 / 2.2)
        ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
        ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
        ob.write(os.path.join(OUT, f"235_vl{lim}.png"))
    for f in os.listdir(OUT):
        if f.startswith("_235_") and f.endswith(".exr"):
            os.remove(os.path.join(OUT, f))
    karma.parm("volumelimit").set(4)
    hou_tools.save_hip(os.path.join(OUT, "235_scene.hipnc"))
    geo = hou.node("/obj/cloud")
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "235_graph.json"), title="実験235")
    sop_bench.save(235, rows, {"res": RES, "spp": 32, "default_volumelimit": default, "cloud_pixels": int(cloud.sum()), "mid_row": mid})


if __name__ == "__main__":
    main()
