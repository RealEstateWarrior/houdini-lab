# -*- coding: utf-8 -*-
"""実験239 — 画の大きさ（解像度）を上げると、Karma の撮る時間は画素の数に比例して延びるか。映像の見積もりの基準。

制作の問い: 試し撮りは 640×360 で、仕上げは 1920×1080 で撮りたい。画素の数は 9 倍になるが、時間も 9 倍になるのか。
実験221 では、海の映像は解像度を下げてもあまり速くならなかった（場面を Karma に渡す時間が大きい）。場面によって違うのか。

  実践 2 本（ドーナツ＝ふつうの材質、冬の朝の七里ヶ浜＝224 万点の海）の hip を読み、同じ設定（16 サンプル・ノイズ除去なし）で
  640×360・1280×720・1920×1080 に撮る。はじめに小さく 1 枚撮って捨てる。場面ごとに別の hython。
  測るもの: 撮る時間。640×360 の時間を「画の大きさによらない分 a ＋ 画素に比例する分 b」に分けて、a と b を 3 点から求める
  （時間 = a + b × 画素数 に当てはめる）。

    hython examples/239_karma_resolution_time.py donut
    python examples/239_karma_resolution_time.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
SCENES = {"donut": 1, "ocean_winter": 30}
SIZES = ((640, 360), (1280, 720), (1920, 1080))


def run(gid):
    import hou
    hou.hipFile.load(os.path.join(OUT, f"pr_{gid}.hipnc"), suppress_save_prompt=True)
    frame = SCENES[gid]
    hou.setFrame(frame)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("off")
    karma.parm("engine").set("cpu")
    karma.parm("samplesperpixel").set(16)
    karma.parm("varianceaa_maxsamples").set(16)

    def shoot(res, path):
        karma.parm("resolutionx").set(res[0])
        karma.parm("resolutiony").set(res[1])
        cam.parm("resx").set(res[0])
        cam.parm("resy").set(res[1])
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(frame, frame, 1), verbose=False)
        return time.perf_counter() - t0

    shoot((160, 90), os.path.join(OUT, "_239_warm.png"))
    row = {"case": gid, "times": {}}
    for res in SIZES:
        row["times"][f"{res[0]}x{res[1]}"] = round(shoot(res, os.path.join(OUT, f"_239_{gid}_{res[0]}.png")), 2)
    print(row, flush=True)
    with open(os.path.join(OUT, f"239_part_{gid}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)
    if gid == "donut":
        import hou_tools
        hou_tools.save_hip(os.path.join(OUT, "239_scene.hipnc"))
        hou_tools.write_graph("/obj/donut", os.path.join(OUT, "239_graph.json"), title="実験239（ドーナツ）")


def combine():
    import numpy as np
    import sop_bench
    rows = []
    for gid in SCENES:
        with open(os.path.join(OUT, f"239_part_{gid}.json"), encoding="utf-8") as fp:
            r = json.load(fp)
        px = np.array([w * h for w, h in SIZES], dtype=float)
        t = np.array([r["times"][f"{w}x{h}"] for w, h in SIZES])
        b, a = np.polyfit(px, t, 1)
        r["fixed_sec"] = round(float(a), 2)
        r["per_mpx_sec"] = round(float(b * 1e6), 2)
        r["ratio_1080_to_360"] = round(float(t[2] / t[0]), 2)
        rows.append(r)
        print(r)
    sop_bench.save(239, rows, {"sizes": SIZES, "spp": 16})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1])
