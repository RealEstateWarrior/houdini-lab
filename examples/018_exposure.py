"""露出合わせ。煙が白飛びしていると、ノイズを測っても意味がない。

255 に張り付いた画素は、本当の値がいくつだったのか分からなくなっている。
サンプル数を増やすと張り付く画素が増えていたので、明るさを下げて
中間の階調に収める必要がある。
"""

import os
import sys

import hou
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

hou.hipFile.load(os.path.join(OUT, "016_pyro.hipnc"),
                 suppress_save_prompt=True, ignore_load_warnings=True)
hou.setFrame(30)

sop = hou.node("/obj/pyro_test/solve_d0_1")
sop.setDisplayFlag(True)
sop.setRenderFlag(True)

RES = (400, 300)
cam = hou.node("/obj/report_cam")
cam.parm("resx").set(RES[0])
cam.parm("resy").set(RES[1])
hou_tools._frame_camera(cam, sop.geometry().boundingBox(), RES, margin=0.5)

dome = hou.node("/obj/report_dome")
key = hou.node("/obj/report_key")

karma = hou.node("/out").createNode("karma", "exposure_karma")
karma.parm("camera").set(cam.path())
karma.parm("denoiser").set("off")
karma.parm("resolutionx").set(RES[0])
karma.parm("resolutiony").set(RES[1])
karma.parm("samplesperpixel").set(64)

print(f"{'dome':>6} {'key':>6} {'黒(0)':>8} {'白飛び(255)':>11} "
      f"{'中間の画素':>10} {'中間の平均':>10}")

for dome_i, key_i in ((0.55, 1.6), (0.20, 0.5), (0.10, 0.25), (0.05, 0.12)):
    dome.parm("light_intensity").set(dome_i)
    key.parm("light_intensity").set(key_i)
    path = os.path.join(OUT, f"018_exp_{dome_i}_{key_i}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    karma.render(frame_range=(30, 30, 1), verbose=False)

    pixels = list(Image.open(path).convert("L").getdata())
    black = sum(1 for v in pixels if v == 0)
    white = sum(1 for v in pixels if v == 255)
    mid = [v for v in pixels if 0 < v < 255]
    print(f"{dome_i:6.2f} {key_i:6.2f} {black:8d} {white:11d} "
          f"{len(mid):10d} {sum(mid) / max(len(mid), 1):10.1f}")
