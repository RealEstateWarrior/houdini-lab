# -*- coding: utf-8 -*-
"""実験221 — 海の映像の 1 枚を速く撮るなら、サンプル数・解像度・ノイズ除去のどれが効くか。

制作の問い: 実験219 で、海の板の点を 1/16 にしても撮る時間は 52% までしか減らなかった。
実践「冬の朝の七里ヶ浜」の映像（960×540・16 サンプル）を、ほかの設定で速くするなら何を下げるか。

  pr_ocean_winter.hipnc のフレーム 30 を、次の 5 通りで撮る（板は 1400×1600 のまま。1 通りずつ、ほかの処理は回さない）。
    s16      … 960×540・16 サンプル（映像の設定。基準）
    s8       … 960×540・8 サンプル
    s4       … 960×540・4 サンプル
    s4_oidn  … 960×540・4 サンプル＋ノイズ除去（OIDN）
    r640     … 640×360・16 サンプル（見比べるときは 960×540 に拡大）
  測るもの: 撮る時間と、基準の画との画素ごとの差の平均（0〜255）。空（上 40%）と水面（縦 57〜80%）に分ける。

    hython examples/221_ocean_render_settings.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
FRAME = 30
CASES = [("s16", (960, 540), 16, "off"), ("s8", (960, 540), 8, "off"), ("s4", (960, 540), 4, "off"),
         ("s4_oidn", (960, 540), 4, "oidn"), ("r640", (640, 360), 16, "off")]


def main():
    import hou
    import numpy as np
    from PIL import Image
    import hou_tools
    import sop_bench
    # 測ったのは、冬の海を作り直す前（2026-09-24 21時）の場面。作り直した後の hip では値が変わるので、前の版を読む（点検 240 で分かった）
    hou.hipFile.load(os.path.join(OUT, "pr_ocean_winter_v1.hipnc"), suppress_save_prompt=True)
    hou.setFrame(FRAME)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    hou.node("/obj/ocean_winter/breaking_waves").geometry()
    # 1 枚目は Karma の立ち上がりの分だけ遅いので、1 枚撮って捨てる
    karma.parm("picture").set(os.path.join(OUT, "_221_warm.png").replace("\\", "/"))
    karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
    rows, imgs = [], {}
    for name, res, spp, dn in CASES:
        for n, v in (("resolutionx", res[0]), ("resolutiony", res[1]), ("samplesperpixel", spp), ("varianceaa_maxsamples", spp)):
            karma.parm(n).set(v)
        cam.parm("resx").set(res[0])
        cam.parm("resy").set(res[1])
        karma.parm("denoiser").set(dn)
        png = os.path.join(OUT, f"221_{name}.png")
        karma.parm("picture").set(png.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        sec = time.perf_counter() - t0
        im = Image.open(png).convert("RGB")
        if im.size != (960, 540):
            im = im.resize((960, 540), Image.BICUBIC)
        imgs[name] = np.asarray(im, dtype=float)
        rows.append({"case": name, "res": list(res), "spp": spp, "denoise": dn, "render_sec": round(sec, 1)})
        print(rows[-1], flush=True)
    ref = imgs["s16"]
    zones = {"sky": (0, 216), "sea": (308, 432)}
    for row in rows:
        row["diff"] = {k: round(float(np.abs(imgs[row["case"]][a:b] - ref[a:b]).mean()), 2) for k, (a, b) in zones.items()}
        print(row)
    hou_tools.save_hip(os.path.join(OUT, "221_scene.hipnc"))
    hou_tools.write_graph("/obj/ocean_winter", os.path.join(OUT, "221_graph.json"), title="実験221")
    sop_bench.save(221, rows, {"frame": FRAME, "zones": zones})


if __name__ == "__main__":
    main()
