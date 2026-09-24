# -*- coding: utf-8 -*-
"""実験241 — Karma のノイズ除去は OIDN と OptiX のどちらがよいか。何サンプルから使えるか。

制作の問い: 試し撮りや映像は、サンプルを減らしてノイズ除去で仕上げたい。Karma の Denoiser には Intel OIDN と NVIDIA OptiX がある。
どちらが速く、どちらが本物（たくさんサンプルを取った画）に近いか。何サンプルまで減らしてよいか。

  実践 2 本（ドーナツ＝細かい模様、雪だるま＝SSS のなめらかな面）の hip を読み、640×360 で撮る。
    サンプル 4・8・16・32 × ノイズ除去なし・OIDN・OptiX
  基準は 512 サンプル・ノイズ除去なし。はじめに小さく 1 枚撮って捨てる（OIDN・OptiX もそれぞれ 1 回ずつ先に動かす）。場面ごとに別の hython。
  測るもの: 撮る時間、基準との差（画素ごとの差の平均 0〜255、右下の透かしは除く）、細かさ（となりの画素との差の平均。基準に近いほど模様が残っている）。

    hython examples/241_karma_denoiser.py donut
    python examples/241_karma_denoiser.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)
SCENES = ("donut", "snowman")
SPPS = (4, 8, 16, 32)
DENOISERS = ("off", "oidn", "optix")


def run(gid):
    import hou
    import numpy as np
    from PIL import Image
    hou.hipFile.load(os.path.join(OUT, f"pr_{gid}.hipnc"), suppress_save_prompt=True)
    hou.setFrame(1)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("engine").set("cpu")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1])):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])

    def shoot(spp, dn, path):
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        karma.parm("denoiser").set(dn)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        return time.perf_counter() - t0, np.asarray(Image.open(path).convert("RGB"), dtype=float)

    for dn in DENOISERS:
        shoot(1, dn, os.path.join(OUT, f"_241_warm_{dn}.png"))
    _, ref = shoot(512, "off", os.path.join(OUT, f"241_{gid}_ref.png"))
    keep = np.ones(ref.shape[:2], bool)
    keep[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False
    detail = lambda a: float(np.abs(np.diff(a.mean(axis=2), axis=1)).mean())  # noqa: E731
    rows = [{"case": f"{gid}_ref", "scene": gid, "spp": 512, "denoiser": "off", "detail": round(detail(ref), 3)}]
    for spp in SPPS:
        for dn in DENOISERS:
            sec, img = shoot(spp, dn, os.path.join(OUT, f"241_{gid}_{spp}_{dn}.png"))
            rows.append({"case": f"{gid}_{spp}_{dn}", "scene": gid, "spp": spp, "denoiser": dn, "sec": round(sec, 2),
                         "diff": round(float(np.abs(img - ref)[keep].mean()), 3), "detail": round(detail(img), 3)})
            print(rows[-1], flush=True)
    with open(os.path.join(OUT, f"241_part_{gid}.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp)
    if gid == "donut":
        import hou_tools
        karma.parm("denoiser").set("optix")
        karma.parm("samplesperpixel").set(16)
        hou_tools.save_hip(os.path.join(OUT, "241_scene.hipnc"))
        hou_tools.write_graph("/obj/donut", os.path.join(OUT, "241_graph.json"), title="実験241（ドーナツ）")


def combine():
    import sop_bench
    rows = []
    for gid in SCENES:
        with open(os.path.join(OUT, f"241_part_{gid}.json"), encoding="utf-8") as fp:
            rows += json.load(fp)
    sop_bench.save(241, rows, {"res": RES, "ref_spp": 512})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1])
