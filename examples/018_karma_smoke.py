"""実験018の第1歩。Karma が本当に動くか、どれくらい時間がかかるかを確かめる。

いきなり本番の比較を組むと、1枚に何分かかるか分からないまま走らせることになる。
まず1枚だけ小さく描いて、時間と出力を確認する。
"""

import os
import time

import hou

sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(sys_path, "out")
SCENE = os.path.join(OUT, "016_pyro.hipnc")

hou.hipFile.load(SCENE, suppress_save_prompt=True, ignore_load_warnings=True)
print("読み込んだ:", SCENE)

for node in hou.node("/obj").children():
    print("  /obj:", node.name(), node.type().name())

# 煙のジオメトリを探す（表示フラグが立っているSOP）
target = None
for obj in hou.node("/obj").children():
    if obj.type().name() != "geo":
        continue
    for sop in obj.children():
        if sop.isDisplayFlagSet():
            target = sop
            print("  表示中のSOP:", sop.path(), sop.type().name())

if target is None:
    raise SystemExit("表示中のSOPが見つからない")

hou.setFrame(30)
geo = target.geometry()
print("フレーム30:", len(geo.points()), "点 /", len(geo.prims()), "プリミティブ")
print("プリミティブの型:", sorted({p.type().name() for p in geo.prims()}))

# カメラ。既存のものがあれば流用する
obj = hou.node("/obj")
cam = obj.node("report_cam")
print("カメラ:", cam.path() if cam else "なし")

karma = hou.node("/out").node("probe_karma") or hou.node("/out").createNode("karma", "probe_karma")
picture = os.path.join(OUT, "018_smoke_test.png").replace("\\", "/")
karma.parm("picture").set(picture)
if cam is not None:
    karma.parm("camera").set(cam.path())
karma.parm("override_camerares").set(True)
karma.parm("res_overridex").set(320)
karma.parm("res_overridey").set(240)
karma.parm("samplesperpixel").set(16)
karma.parm("denoiser").set("none")

print("\n既定値の確認")
for name in ("engine", "samplesperpixel", "varianceaa_minsamples",
             "varianceaa_maxsamples", "denoiser"):
    parm = karma.parm(name)
    print(f"  {name} = {parm.eval()!r}  (既定 {parm.parmTemplate().defaultValue()})")

start = time.perf_counter()
karma.render(frame_range=(30, 30, 1), verbose=False)
elapsed = time.perf_counter() - start

print(f"\n描画にかかった時間: {elapsed:.2f} 秒")
print("出力:", picture, "存在:", os.path.exists(picture),
      os.path.getsize(picture) if os.path.exists(picture) else "")
