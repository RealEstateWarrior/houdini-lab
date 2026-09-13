"""頭打ちの犯人を特定する。

samplesperpixel を 4096 にしても、時間から逆算した実効サンプル数は約567で止まった。
Karma には varianceaa_thresh という「このくらい収束したらもう打ち切る」という
しきい値がある。これが犯人なら、しきい値を下げれば実効サンプル数は伸びるはず。

否定できる形: しきい値を100分の1にしても実効サンプル数が変わらなければ、犯人は別。
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
FIXED, PER = 2.26, 0.00744

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

karma = hou.node("/out").createNode("karma", "thresh_karma")
karma.parm("camera").set(cam.path())
karma.parm("denoiser").set("off")
karma.parm("resolutionx").set(RES[0])
karma.parm("resolutiony").set(RES[1])
karma.parm("samplesperpixel").set(4096)
karma.parm("varianceaa_maxsamples").set(4096)

thresh = karma.parm("varianceaa_thresh")
print("varianceaa_thresh の既定値:", thresh.parmTemplate().defaultValue())

print(f"\n{'しきい値':>10} {'実測(秒)':>9} {'実効サンプル':>12} {'既定比':>8}")
base = None
for value in (0.01, 0.005, 0.001, 0.0002):
    thresh.set(value)
    karma.parm("picture").set(
        os.path.join(OUT, f"018_thresh_{value}.png").replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(30, 30, 1), verbose=False)
    elapsed = time.perf_counter() - start
    effective = max(elapsed - FIXED, 0.0) / PER
    base = base or effective
    print(f"{value:10.4f} {elapsed:9.2f} {effective:12.0f} {effective / base:8.2f}")
