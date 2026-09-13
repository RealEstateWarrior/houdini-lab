"""サンプル数のツマミが本当に効いているかを確かめる。

samplesperpixel を 4 から 128 に増やしても、時間が2倍にしかならなかった。
32倍の仕事をさせたつもりなので、これはおかしい。

Karma には varianceaa_maxsamples という別のパラメータがあり、既定は 9。
名前からして「適応サンプリングの上限」で、これが本当の上限なら
samplesperpixel をいくら上げても 9 で頭打ちになるはず。

仮説: 実際に効いているのは varianceaa_maxsamples のほう。
否定できる形にする。samplesperpixel を固定して varianceaa_maxsamples だけ振り、
時間が変われば仮説どおり、変わらなければ仮説は誤り。
"""

import os
import sys
import time

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

hou.node("/obj/report_dome").parm("light_intensity").set(0.10)
hou.node("/obj/report_key").parm("light_intensity").set(0.25)

karma = hou.node("/out").createNode("karma", "knob_karma")
karma.parm("camera").set(cam.path())
karma.parm("denoiser").set("off")
karma.parm("resolutionx").set(RES[0])
karma.parm("resolutiony").set(RES[1])


def shoot(tag, spp, maxaa):
    karma.parm("samplesperpixel").set(spp)
    karma.parm("varianceaa_maxsamples").set(maxaa)
    path = os.path.join(OUT, f"018_knob_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(30, 30, 1), verbose=False)
    elapsed = time.perf_counter() - start
    pixels = list(Image.open(path).convert("L").getdata())
    mid = [v for v in pixels if 40 <= v <= 200]
    return elapsed, pixels, len(mid)


print("A. varianceaa_maxsamples を既定の9のまま、samplesperpixel を振る")
base = None
for spp in (4, 16, 64, 256):
    elapsed, pixels, mid = shoot(f"a{spp}", spp, 9)
    base = base or elapsed
    print(f"   spp={spp:4d} maxaa=9    {elapsed:6.2f}秒  "
          f"({elapsed / base:4.2f}倍)  中間の画素 {mid}")

print("\nB. samplesperpixel を固定して、varianceaa_maxsamples だけ振る")
base = None
for maxaa in (4, 16, 64, 256):
    elapsed, pixels, mid = shoot(f"b{maxaa}", 256, maxaa)
    base = base or elapsed
    print(f"   spp=256  maxaa={maxaa:4d} {elapsed:6.2f}秒  "
          f"({elapsed / base:4.2f}倍)  中間の画素 {mid}")

print("\nC. 両方そろえて上げる")
base = None
for n in (4, 16, 64, 256):
    elapsed, pixels, mid = shoot(f"c{n}", n, n)
    base = base or elapsed
    print(f"   spp={n:4d} maxaa={n:4d} {elapsed:6.2f}秒  "
          f"({elapsed / base:4.2f}倍)  中間の画素 {mid}")
