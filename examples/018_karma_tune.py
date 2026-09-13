"""解像度の指定がどのパラメータで効くのか、背景と煙のコントラストをどう出すかを確かめる。

1枚目は 320x240 を指定したのに 1280x720 で出てきた。指定の入り口が違う。
ライトも、ドームライトが背景として写り込んで白飛びしている。
"""

import os
import time

import hou
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")

hou.hipFile.load(os.path.join(OUT, "016_pyro.hipnc"),
                 suppress_save_prompt=True, ignore_load_warnings=True)
hou.setFrame(30)

karma = hou.node("/out").createNode("karma", "tune_karma")
cam = hou.node("/obj/report_cam")
karma.parm("camera").set(cam.path())
karma.parm("denoiser").set("off")
karma.parm("samplesperpixel").set(16)

print("カメラ側の解像度:", cam.parm("resx").eval(), "x", cam.parm("resy").eval())
for name in ("override_camerares", "res_fraction", "res_overridex", "res_overridey",
             "resolutionx", "resolutiony", "resolutionMenu"):
    parm = karma.parm(name)
    if parm is not None:
        print(f"  {name} = {parm.eval()!r}")


def shoot(tag, **setup):
    """1枚描いて、時間と画の統計を返す。"""
    for key, value in setup.items():
        karma.parm(key).set(value)
    path = os.path.join(OUT, f"018_tune_{tag}.png").replace("\\", "/")
    karma.parm("picture").set(path)
    start = time.perf_counter()
    karma.render(frame_range=(30, 30, 1), verbose=False)
    elapsed = time.perf_counter() - start
    img = Image.open(path).convert("L")
    pixels = list(img.getdata())
    lo, hi = min(pixels), max(pixels)
    print(f"  {tag:14s} {img.size[0]}x{img.size[1]}  {elapsed:5.1f}秒  "
          f"明るさ {lo}〜{hi}  階調{len(set(pixels))}段")
    return path


print("\n解像度の指定をどこで行うか")
shoot("camres", override_camerares=False)
shoot("override", override_camerares=True, res_overridex=320, res_overridey=240)

print("\nライトを変えて背景と煙のコントラストを見る")
dome = hou.node("/obj/report_dome")
key = hou.node("/obj/report_key")
print("  いまの設定: dome", dome.parm("light_intensity").eval(),
      "/ key", key.parm("light_intensity").eval())

dome.parm("light_intensity").set(0.12)
key.parm("light_intensity").set(4.0)
shoot("darkbg")
