# -*- coding: utf-8 -*-
"""実験207 — 焚き火を Karma で撮るとき、Volume Step Rate と Pyro の Voxel Size で、時間と見た目はどう変わるか。

制作の問い: 焚き火（実践「焚き火を燃やす」）を何百フレームも撮るなら、1 枚を短くしたい。
Karma の Volume Step Rate（ボリュームの中を何歩で進むか。既定 0.25）を粗くすると、どれだけ速く、見た目はどれだけ変わるか。
Pyro を粗い升（Voxel Size）で回した炎は、撮っても見劣りしないか。

  実践のシーン（out/pr_campfire.hipnc。薪・石・炎、Voxel Size 0.03）を開き、フレーム 60 まで燃やして、
  960×540・16 サンプル＋ノイズ除去（実験205 で決めた撮り方）で撮る。
    Volume Step Rate: 1・0.5・0.25（既定）・0.125
    Voxel Size: 0.03（実践の値）と 0.06（升の数が約 8 分の 1）
  見た目の違いは、Voxel Size 0.03・Step Rate 0.125 の画との差（画素の値 0〜255 の差の平均）で、画全体と炎のまわりで測る。
  シーンを作り直すと hython が落ちることがあるので、Voxel Size ごとに 1 プロセスで撮る。

    hython examples/207_karma_fire_steprate.py 0.03
    hython examples/207_karma_fire_steprate.py 0.06
    hython examples/207_karma_fire_steprate.py 0.03 extra   （1920×1080 で Step Rate 1 と 0.125、炎を外した画）
    python examples/207_karma_fire_steprate.py combine
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
RES = (960, 540)
STEPS = [1.0, 0.5, 0.25, 0.125]
FIRE_BOX = (0.3, 0.05, 0.7, 0.75)   # 炎のまわり（画の幅・高さに対する割合）。warmup の画を見て決める


EXTRA = False


def shoot(vox):
    import hou
    hou.hipFile.load(os.path.join(OUT, "pr_campfire.hipnc").replace("\\", "/"), suppress_save_prompt=True, ignore_load_warnings=True)
    solver = [n for n in hou.node("/obj").allSubChildren() if n.type().name() == "pyrosolver"][0]
    rast = [n for n in hou.node("/obj").allSubChildren() if n.type().name() == "volumerasterizeattributes"][0]
    solver.parm("divsize").set(vox)
    rast.parm("voxelsize").set(vox)
    t0 = time.perf_counter()
    for f in range(1, FRAME + 1):
        hou.setFrame(f)
        solver.geometry()
    sim = time.perf_counter() - t0
    fl = [p for p in solver.geometry().prims() if p.type() == hou.primType.Volume and p.attribValue("name") == "flame"][0]
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(16)
    karma.parm("varianceaa_maxsamples").set(16)
    karma.parm("denoiser").set("oidn")
    tag = f"v{int(round(vox * 100)):02d}"
    rows = []

    def render(step, name):
        karma.parm("volumesteprate").set(step)
        path = os.path.join(OUT, f"207_{name}.png")
        karma.parm("picture").set(path.replace("\\", "/"))
        t = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        return round(time.perf_counter() - t, 2)

    render(1.0, f"{tag}_warmup")            # 1 枚目は起動の分だけ遅いので捨てる
    if EXTRA:
        # 1 枚のうち炎が占める時間: 炎を外して撮る。大きな画（1920×1080）で Step Rate が効き始めるか
        for big_step in (1.0, 0.125):
            cam.parm("resx").set(1920)
            cam.parm("resy").set(1080)
            karma.parm("resolutionx").set(1920)
            karma.parm("resolutiony").set(1080)
            rows.append({"vox": vox, "step": big_step, "res": "1920x1080", "tag": f"{tag}_big_s{big_step}",
                         "sec": render(big_step, f"{tag}_big_s{big_step}")})
            print(rows[-1], flush=True)
        cam.parm("resx").set(RES[0])
        cam.parm("resy").set(RES[1])
        karma.parm("resolutionx").set(RES[0])
        karma.parm("resolutiony").set(RES[1])
        merge = [n for n in hou.node("/obj").allSubChildren() if n.type().name() == "merge" and n.name() == "campfire"][0]
        fire_in = [i for i, n in enumerate(merge.inputs()) if n is not None and "fire" in n.name()]
        for i in fire_in:
            merge.setInput(i, None)
        rows.append({"vox": vox, "step": 0.25, "res": "960x540", "tag": f"{tag}_nofire", "sec": render(0.25, f"{tag}_nofire")})
        print(rows[-1], flush=True)
        with open(os.path.join(OUT, "207_part_extra.json"), "w", encoding="utf-8") as fp:
            json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
        print("書いた extra")
        return
    for s in STEPS:
        sec = render(s, f"{tag}_s{s}")
        rows.append({"vox": vox, "step": s, "sec": sec, "tag": f"{tag}_s{s}"})
        print(rows[-1], flush=True)
    info = {"vox": vox, "sim_sec": round(sim, 2), "res": list(fl.resolution()), "rows": rows,
            "defaults": {"volumequality": karma.parm("volumequality").eval(), "volumelimit": karma.parm("volumelimit").eval()}}
    with open(os.path.join(OUT, f"207_part_{tag}.json"), "w", encoding="utf-8") as fp:
        json.dump(info, fp, ensure_ascii=False, indent=1)
    if vox == 0.03:
        import hou_tools
        karma.parm("volumesteprate").set(0.25)
        hou_tools.save_hip(os.path.join(OUT, "207_scene.hipnc"))
        hou_tools.write_graph(solver.parent().path(), os.path.join(OUT, "207_graph.json"), title="実験207")
    print("書いた", tag, info["sim_sec"], info["res"])


def combine():
    import numpy as np
    from PIL import Image
    import sop_bench
    rows, parts = [], []
    for tag in ("v03", "v06"):
        with open(os.path.join(OUT, f"207_part_{tag}.json"), encoding="utf-8") as fp:
            p = json.load(fp)
        parts.append({k: v for k, v in p.items() if k != "rows"})
        rows += p["rows"]
    extra = []
    ep = os.path.join(OUT, "207_part_extra.json")
    if os.path.exists(ep):
        with open(ep, encoding="utf-8") as fp:
            extra = json.load(fp)["rows"]
    ref = np.asarray(Image.open(os.path.join(OUT, "207_v03_s0.125.png")).convert("RGB"), dtype=np.float64)
    h, w = ref.shape[:2]
    x0, y0, x1, y1 = FIRE_BOX
    for r in rows:
        a = np.asarray(Image.open(os.path.join(OUT, f"207_{r['tag']}.png")).convert("RGB"), dtype=np.float64)
        d = np.abs(a - ref)
        r["diff"] = round(float(d.mean()), 3)
        r["diff_fire"] = round(float(d[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].mean()), 3)
        r["bright_fire"] = round(float(a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].mean()), 2)
    if extra:
        a = np.asarray(Image.open(os.path.join(OUT, "207_v03_big_s1.0.png")).convert("RGB"), dtype=np.float64)
        b = np.asarray(Image.open(os.path.join(OUT, "207_v03_big_s0.125.png")).convert("RGB"), dtype=np.float64)
        hh, ww = a.shape[:2]
        dd = np.abs(a - b)
        for r in extra:
            if "big_s1.0" in r["tag"]:
                r["diff_vs_big_s0.125"] = round(float(dd.mean()), 3)
                r["diff_fire_vs_big_s0.125"] = round(float(dd[int(y0 * hh):int(y1 * hh), int(x0 * ww):int(x1 * ww)].mean()), 3)
        rows += extra
    sop_bench.save(207, rows, {"parts": parts, "frame": FRAME, "res": RES, "fire_box": FIRE_BOX})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        EXTRA = len(sys.argv) > 2 and sys.argv[2] == "extra"
        shoot(float(sys.argv[1]))
