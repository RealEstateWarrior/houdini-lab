# -*- coding: utf-8 -*-
"""実験244 — 焚き火の煙をどこまで長く立ちのぼらせるか。pyrosolver の Dissipation（煙が薄れて消える速さ）で決まるか。

制作の問い: 焚き火や煙突の煙を、すぐ消える薄い煙にしたい・高くまで残る煙にしたい。pyrosolver の Dissipation（既定 0.1）を変えると、
煙の高さと量はどう変わるのか。

  実践「焚き火」の場面（out/pr_campfire.hipnc）の pyrosolver（burn）の Dissipation を 0・0.05・0.1（既定）・0.2・0.4 にして、96 フレーム（4 秒）回す。
  測るもの（96 フレーム目）: 煙の濃さ（density）が 0.02 を超える升の数と、そのいちばん高い所の高さ、濃さの合計。
  あわせて、実践と同じカメラと明かりで Karma（640×360・16 サンプル＋ノイズ除去）で撮る。条件ごとに別の hython。

    hython examples/244_pyro_smoke_dissipation.py 0.1
    python examples/244_pyro_smoke_dissipation.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
LAST = 96
VALUES = (0.0, 0.05, 0.1, 0.2, 0.4)


def run(d, fd=1, smoke=False):
    import hou
    import numpy as np
    hou.hipFile.load(os.path.join(OUT, "pr_campfire.hipnc"), suppress_save_prompt=True)
    geo = hou.node("/obj/campfire")
    solver = geo.node("burn")
    solver.parm("dissipation").set(d)
    solver.parm("doflamedensity").set(fd)
    if smoke:
        # 火元の点に煙の濃さ density = 1 を足し、升目に移す値にも加える（実践の火元は燃やす値だけで、煙を出していなかった）
        src = geo.node("src")
        rast = geo.node("to_voxels")
        w = geo.createNode("attribwrangle", "add_smoke")
        w.setFirstInput(src)
        w.parm("snippet").set("f@density = 1;")
        rast.setFirstInput(w)
        rast.parm("attributes").set(rast.parm("attributes").eval() + " density")
    final = [c for c in geo.children() if c.isDisplayFlagSet()][0]
    t0 = time.perf_counter()
    for f in range(1, LAST + 1):
        hou.setFrame(f)
        g = solver.geometry()
    sim = time.perf_counter() - t0
    vol = [p for p in g.prims() if p.attribValue("name") == "density"][0]
    rx, ry, rz = vol.resolution()
    a = np.array(vol.allVoxels()).reshape(rz, ry, rx)
    on = a > 0.02
    ys = np.nonzero(on.any(axis=(0, 2)))[0]
    top = float(vol.indexToPos((0, int(ys.max()), 0))[1]) if len(ys) else 0.0
    size = vol.voxelSize()
    tag = f"d{d:g}" + ("_smoke" if smoke else ("" if fd else "_free"))
    row = {"case": tag, "dissipation": d, "set_flame_density": fd, "source_smoke": int(smoke), "sim_sec": round(sim, 2), "res": [rx, ry, rz],
           "smoke_voxels": int(on.sum()), "top": round(top, 3), "density_sum": round(float(a.sum() * size[0] * size[1] * size[2]), 4)}
    final.geometry()
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    for n, v in (("resolutionx", 640), ("resolutiony", 360), ("samplesperpixel", 16), ("varianceaa_maxsamples", 16)):
        karma.parm(n).set(v)
    cam.parm("resx").set(640)
    cam.parm("resy").set(360)
    karma.parm("denoiser").set("oidn")
    karma.parm("picture").set(os.path.join(OUT, f"244_{tag}.png".replace("0.", "0p")).replace("\\", "/"))
    karma.render(frame_range=(LAST, LAST, 1), verbose=False)
    print(row, flush=True)
    with open(os.path.join(OUT, f"244_part_{tag}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)
    if d == 0.1 and smoke:
        import hou_tools
        hou_tools.save_hip(os.path.join(OUT, "244_scene.hipnc"))
        hou_tools.write_graph(geo.path(), os.path.join(OUT, "244_graph.json"), title="実験244")


def combine():
    import sop_bench
    rows = []
    for mode in ("", "_free", "_smoke"):
        for d in VALUES:
            tag = f"d{d:g}" + mode
            with open(os.path.join(OUT, f"244_part_{tag}.json"), encoding="utf-8") as fp:
                rows.append(json.load(fp))
    sop_bench.save(244, rows, {"last": LAST})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(float(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 1, len(sys.argv) > 3 and sys.argv[3] == "smoke")
