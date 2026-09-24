# -*- coding: utf-8 -*-
"""実験233 — Pyro の升目（Voxel Size）を細かくすると、撮る時間と見た目はどう変わるか。

制作の問い: 実験202 で、焚き火の Pyro は Voxel Size 0.04 で計算が 5 倍速くなり、炎の高さの差は 3% だった。
では、Karma で撮る時間と、画の見た目はどう変わるのか。どこまで粗くしてよいのか。

  実践「焚き火」の場面（out/pr_campfire.hipnc、フレーム 60）で、pyrosolver（burn）の Voxel Size を 0.08・0.06・0.04（実践の値）・0.03・0.02 にする。
  補助の明かりはそのまま。640×360・16 サンプル＋ノイズ除去で撮る。条件ごとに別の hython で、はじめに小さく 1 枚撮って捨てる。
  測るもの: 60 フレームの計算時間、炎の升目の数、撮る時間、0.02 の画との差（画素ごとの差の平均 0〜255、右下の透かしは除く）。

    hython examples/233_pyro_voxel_render.py 0.04
    python examples/233_pyro_voxel_render.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
FRAME = 60
RES = (640, 360)
VOXELS = (0.08, 0.06, 0.04, 0.03, 0.02)


def run(vox):
    import hou
    hou.hipFile.load(os.path.join(OUT, "pr_campfire.hipnc"), suppress_save_prompt=True)
    geo = hou.node("/obj/campfire")
    solver = geo.node("burn")
    solver.parm("divsize").set(vox)
    final = [c for c in geo.children() if c.isDisplayFlagSet()][0]
    t0 = time.perf_counter()
    for f in range(1, FRAME + 1):
        hou.setFrame(f)
        g = solver.geometry()
    sim = time.perf_counter() - t0
    vols = [p for p in g.prims() if p.type() == hou.primType.Volume or p.type() == hou.primType.VDB]
    res = max((p.resolution() for p in vols), key=lambda r: r[0] * r[1] * r[2]) if vols else (0, 0, 0)
    final.geometry()
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    karma.parm("denoiser").set("oidn")
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 16), ("varianceaa_maxsamples", 16)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma.parm("picture").set(os.path.join(OUT, "_233_warm.png").replace("\\", "/"))
    karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
    png = os.path.join(OUT, f"233_v{vox:g}.png".replace("0.", "0p"))
    karma.parm("picture").set(png.replace("\\", "/"))
    t0 = time.perf_counter()
    karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
    sec = time.perf_counter() - t0
    row = {"case": f"v{vox:g}", "voxel": vox, "sim_sec": round(sim, 2), "res": list(res), "voxels": int(res[0] * res[1] * res[2]), "render_sec": round(sec, 2)}
    print(row, flush=True)
    with open(os.path.join(OUT, f"233_part_{vox:g}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)
    if vox == 0.04:
        import hou_tools
        hou_tools.save_hip(os.path.join(OUT, "233_scene.hipnc"))
        hou_tools.write_graph(geo.path(), os.path.join(OUT, "233_graph.json"), title="実験233")


def combine():
    import numpy as np
    from PIL import Image
    import sop_bench
    rows = []
    ref = np.asarray(Image.open(os.path.join(OUT, "233_v0p02.png")).convert("RGB"), dtype=float)
    keep = np.ones(ref.shape[:2], bool)
    keep[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False
    for v in VOXELS:
        with open(os.path.join(OUT, f"233_part_{v:g}.json"), encoding="utf-8") as fp:
            r = json.load(fp)
        img = np.asarray(Image.open(os.path.join(OUT, f"233_v{v:g}.png".replace("0.", "0p"))).convert("RGB"), dtype=float)
        r["diff_to_002"] = round(float(np.abs(img - ref)[keep].mean()), 2)
        rows.append(r)
        print(r)
    sop_bench.save(233, rows, {"frame": FRAME, "res": RES, "spp": 16})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(float(sys.argv[1]))
