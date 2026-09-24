# -*- coding: utf-8 -*-
"""実験232 — Karma XPU（GPU）で撮れる場面・撮れない場面。実践の場面を CPU と XPU で撮り比べる。

制作の問い: 実践「夕暮れの海」では、XPU は CPU より速かったが、点の色で光らせた空が白く飛んだ。
どの場面なら XPU に任せてよいのか。どれだけ速いのか。絵はどれだけ違うのか。

  実践の hip を読み、仕上がりを撮る Karma（/out/hero_karma）の Rendering Engine だけを CPU・XPU に切り替えて、同じ設定で撮る。
  640×360・32 サンプル・ノイズ除去なし。場面ごとに別の hython で、はじめに小さく 1 枚撮って捨てる（CPU・XPU それぞれ）。
    ocean_winter（冬の海。点の色で光る空・disk の太陽）、campfire（Pyro の炎）、glasscup（透明なガラスと水）、snowman（SSS の雪）、
    donut（ふつうの材質）、neon（光る材質）
  測るもの: 撮る時間（XPU は GPU の準備を含む 1 枚目を捨てたあと）と、CPU の画との差（画素ごとの差の平均 0〜255。右下の透かしは除く）。

    hython examples/232_karma_xpu_scenes.py <実践の id>
    python examples/232_karma_xpu_scenes.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
SCENES = ["ocean_winter", "campfire", "glasscup", "snowman", "donut", "neon"]
FRAMES = {"ocean_winter": 30, "campfire": 60}
RES = (640, 360)


def run(gid):
    import hou
    import numpy as np
    from PIL import Image
    hou.hipFile.load(os.path.join(OUT, f"pr_{gid}.hipnc"), suppress_save_prompt=True)
    frame = FRAMES.get(gid, int(hou.frame()))
    if gid == "campfire":
        geo = hou.node("/obj/campfire")
        final = [c for c in geo.children() if c.isDisplayFlagSet()][0]
        for f in range(1, frame + 1):
            hou.setFrame(f)
            final.geometry()
    hou.setFrame(frame)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("off")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 32), ("varianceaa_maxsamples", 32)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    out = {}
    for engine in ("cpu", "xpu"):
        karma.parm("engine").set(engine)
        karma.parm("picture").set(os.path.join(OUT, f"_232_warm_{engine}.png").replace("\\", "/"))
        karma.render(frame_range=(frame, frame, 1), verbose=False)
        png = os.path.join(OUT, f"232_{gid}_{engine}.png")
        karma.parm("picture").set(png.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(frame, frame, 1), verbose=False)
        out[engine] = time.perf_counter() - t0
    a = np.asarray(Image.open(os.path.join(OUT, f"232_{gid}_cpu.png")).convert("RGB"), dtype=float)
    b = np.asarray(Image.open(os.path.join(OUT, f"232_{gid}_xpu.png")).convert("RGB"), dtype=float)
    keep = np.ones(a.shape[:2], bool)
    keep[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False   # 右下の透かし
    diff = float(np.abs(a - b)[keep].mean())
    row = {"case": gid, "frame": frame, "cpu_sec": round(out["cpu"], 2), "xpu_sec": round(out["xpu"], 2), "diff": round(diff, 2),
           "cpu_mean": round(float(a[keep].mean()), 1), "xpu_mean": round(float(b[keep].mean()), 1)}
    print(row, flush=True)
    with open(os.path.join(OUT, f"232_part_{gid}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)


def combine():
    import sop_bench
    rows = []
    for gid in SCENES:
        with open(os.path.join(OUT, f"232_part_{gid}.json"), encoding="utf-8") as fp:
            rows.append(json.load(fp))
    sop_bench.save(232, rows, {"res": RES, "spp": 32})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1])
