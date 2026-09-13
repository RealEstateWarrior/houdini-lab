"""サンプル数はどこまで効くのか。時間が直線から外れる点を探す。

2〜256 の範囲では、時間はサンプル数にほぼ比例していた（固定費2.26秒 + 7.4ミリ秒/本）。
ところが基準画に指定した 2048 本は、その直線なら17.5秒かかるはずのところ
4.9秒で終わっていた。どこかで頭打ちになっている。
"""

import os
import sys
import time

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 360)
hou.hipFile.load(os.path.join(OUT, "016_pyro.hipnc"),
                 suppress_save_prompt=True, ignore_load_warnings=True)
hou.setFrame(30)
sop = hou.node("/obj/pyro_test/solve_d0_1")
sop.setDisplayFlag(True)
sop.setRenderFlag(True)
hou.node("/obj/report_dome").parm("light_intensity").set(0.10)
hou.node("/obj/report_key").parm("light_intensity").set(0.25)

cam = hou.node("/obj/report_cam")
cam.parm("resx").set(RES[0])
cam.parm("resy").set(RES[1])
hou_tools._frame_camera(cam, sop.geometry().boundingBox(), RES, margin=0.5)

karma = hou.node("/out").createNode("karma", "cap_karma")
karma.parm("camera").set(cam.path())
karma.parm("denoiser").set("off")
karma.parm("resolutionx").set(RES[0])
karma.parm("resolutiony").set(RES[1])

FIXED, PER = 2.26, 0.00744   # 2〜256 で当てはめた直線

print(f"{'サンプル':>8} {'実測(秒)':>9} {'直線の予測':>10} {'実測/予測':>10} "
      f"{'実効サンプル':>12}")
for spp in (64, 128, 256, 512, 1024, 2048, 4096):
    karma.parm("samplesperpixel").set(spp)
    karma.parm("varianceaa_maxsamples").set(spp)
    karma.parm("picture").set(
        os.path.join(OUT, f"018_cap_{spp:05d}.png").replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(30, 30, 1), verbose=False)
    elapsed = time.perf_counter() - start
    predicted = FIXED + PER * spp
    effective = max(elapsed - FIXED, 0.0) / PER
    print(f"{spp:8d} {elapsed:9.2f} {predicted:10.2f} {elapsed / predicted:10.2f} "
          f"{effective:12.0f}")
