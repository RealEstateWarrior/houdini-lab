# -*- coding: utf-8 -*-
"""実験247 — 映像にノイズ除去を使うと、フレームごとにちらつくか。

制作の問い: 実験241 で、静止画なら 4 サンプル＋ノイズ除去で 32 サンプル（なし）並みになった。映像では、ノイズ除去はフレームごとに
別々にかかるので、動かない所までちらつくことがある。どれだけちらつくのか。サンプルを増やすのと比べてどうか。

  実践「冬の朝の七里ヶ浜」の場面（out/pr_ocean_winter.hipnc）を、フレーム 20〜31 の 12 枚、640×360 で撮る。
    s4_optix   … 4 サンプル＋OptiX
    s4_off     … 4 サンプル・ノイズ除去なし
    s16_off    … 16 サンプル・ノイズ除去なし
    s16_optix  … 16 サンプル＋OptiX
  測るもの: 動かない所（空＝画の上 35%、右下の透かしは除く）の、画素ごとの 12 枚の明るさの標準偏差の平均（ちらつき）。
            と、12 枚を撮る時間。条件ごとに別の hython。

    hython examples/247_karma_denoise_flicker.py s4_optix
    python examples/247_karma_denoise_flicker.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
CASES = {"s4_optix": (4, "optix"), "s4_off": (4, "off"), "s16_off": (16, "off"), "s16_optix": (16, "optix")}
F0, F1 = 20, 31
RES = (640, 360)


def run(tag):
    import hou
    import numpy as np
    import OpenImageIO as oiio
    spp, dn = CASES[tag]
    hou.hipFile.load(os.path.join(OUT, "pr_ocean_winter.hipnc"), suppress_save_prompt=True)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", spp), ("varianceaa_maxsamples", spp)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma.parm("denoiser").set(dn)
    karma.parm("engine").set("cpu")
    hou.setFrame(F0)
    karma.parm("picture").set(os.path.join(OUT, "_247_warm.exr").replace("\\", "/"))
    karma.render(frame_range=(F0, F0, 1), verbose=False)
    d = os.path.join(OUT, f"_247_{tag}")
    os.makedirs(d, exist_ok=True)
    karma.parm("picture").set(os.path.join(d, "f$F4.exr").replace("\\", "/"))
    t0 = time.perf_counter()
    karma.render(frame_range=(F0, F1, 1), verbose=False)
    sec = time.perf_counter() - t0
    frames = []
    for f in range(F0, F1 + 1):
        px = oiio.ImageBuf(os.path.join(d, f"f{f:04d}.exr")).get_pixels(oiio.FLOAT)[:, :, :3]
        frames.append(px @ np.array([0.2126, 0.7152, 0.0722]))
    stack = np.stack(frames)
    sky = stack[:, : int(RES[1] * 0.35), :]
    flick = float(sky.std(axis=0).mean() / sky.mean())
    row = {"case": tag, "spp": spp, "denoiser": dn, "sec12": round(sec, 2), "sky_flicker": round(flick, 5)}
    print(row, flush=True)
    view = np.clip(oiio.ImageBuf(os.path.join(d, f"f{F0 + 6:04d}.exr")).get_pixels(oiio.FLOAT)[:, :, :3], 0, 1) ** (1 / 2.2)
    ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
    ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
    ob.write(os.path.join(OUT, f"247_{tag}.png"))
    with open(os.path.join(OUT, f"247_part_{tag}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)


def combine():
    import sop_bench
    rows = []
    for tag in CASES:
        with open(os.path.join(OUT, f"247_part_{tag}.json"), encoding="utf-8") as fp:
            rows.append(json.load(fp))
    sop_bench.save(247, rows, {"frames": [F0, F1], "res": RES})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1])
