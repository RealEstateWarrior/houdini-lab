"""OpenGL と Karma を、同じカメラ・同じ露出で撮り直して比べる。

最初の比較はカメラの寄り方が違っていた（OpenGL は margin 1.12、Karma は 0.5）。
煙の写る画素数が違って当たり前で、比較になっていなかった。
実験003以降ずっと守ってきた「全変種を同じカメラで撮る」を、ここで外していた。
"""

import json
import math
import os
import sys
import time

import hou
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 360)
MARGIN = 0.5
FRAME = 30

hou.hipFile.load(os.path.join(OUT, "016_pyro.hipnc"),
                 suppress_save_prompt=True, ignore_load_warnings=True)
hou.setFrame(FRAME)
sop = hou.node("/obj/pyro_test/solve_d0_1")
sop.setDisplayFlag(True)
sop.setRenderFlag(True)
hou.node("/obj/report_dome").parm("light_intensity").set(0.10)
hou.node("/obj/report_key").parm("light_intensity").set(0.25)

bbox = sop.geometry().boundingBox()

gl_path = os.path.join(OUT, "018_opengl.png")
start = time.perf_counter()
hou_tools.render_preview(sop.path(), gl_path, res=RES, shading="smooth",
                         frame_bbox=bbox, margin=MARGIN)
gl_sec = time.perf_counter() - start

cam = hou.node("/obj/report_cam")
karma = hou.node("/out").createNode("karma", "cmp_karma")
karma.parm("camera").set(cam.path())
karma.parm("denoiser").set("off")
karma.parm("resolutionx").set(RES[0])
karma.parm("resolutiony").set(RES[1])
karma.parm("samplesperpixel").set(256)
karma.parm("varianceaa_maxsamples").set(256)
ka_path = os.path.join(OUT, "018_karma.png")
karma.parm("picture").set(ka_path.replace("\\", "/"))
start = time.perf_counter()
karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
ka_sec = time.perf_counter() - start


def load(path):
    img = Image.open(path)
    if img.mode in ("RGBA", "LA"):
        white = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(white, img.convert("RGBA"))
    gray = img.convert("L")
    return gray.size, list(gray.getdata())


def describe(path):
    (width, height), px = load(path)
    inside = [px[i] for i in range(len(px))
              if px[i] < 250
              and not (i % width > width * 0.70 and i // width > height * 0.82)]
    mean = sum(inside) / len(inside)
    sd = math.sqrt(sum((v - mean) ** 2 for v in inside) / len(inside))
    row = height // 2
    profile = [px[row * width + x] for x in range(0, width, width // 32)]
    return {"pixels": len(inside), "levels": len(set(inside)), "mean": mean,
            "sd": sd, "darkest": min(inside), "profile": profile}


gl = describe(gl_path)
ka = describe(ka_path)

print(f"同じカメラ（margin {MARGIN}）・同じ露出で撮り直した結果\n")
print(f"{'':12s}{'時間':>8}{'煙の画素':>10}{'階調':>7}{'平均':>8}"
      f"{'ばらつき':>10}{'最も暗い':>10}")
for name, sec, d in (("OpenGL ROP", gl_sec, gl), ("Karma 256", ka_sec, ka)):
    print(f"{name:12s}{sec:7.2f}秒{d['pixels']:10d}{d['levels']:7d}"
          f"{d['mean']:8.1f}{d['sd']:10.2f}{d['darkest']:10d}")

print("\n中心を横切る線の明るさ（左から右へ32点）")
for name, d in (("OpenGL", gl), ("Karma ", ka)):
    print(f"  {name}: " + " ".join(f"{v:3d}" for v in d["profile"]))

# 煙の「縁のなだらかさ」。255から最も暗い値までの間にある画素の割合。
print("\n縁のなだらかさ（半透明に描かれている画素の割合）")
for name, path in (("OpenGL", gl_path), ("Karma ", ka_path)):
    (width, height), px = load(path)
    inside = [px[i] for i in range(len(px))
              if px[i] < 250
              and not (i % width > width * 0.70 and i // width > height * 0.82)]
    soft = sum(1 for v in inside if v > 150)
    print(f"  {name}: 薄い画素 {soft:6d} / 煙の画素 {len(inside):6d} "
          f"= {100.0 * soft / len(inside):5.1f}%")

with open(os.path.join(OUT, "018_compare.json"), "w", encoding="utf-8") as fp:
    json.dump({"res": list(RES), "margin": MARGIN,
               "opengl": dict(gl, sec=gl_sec), "karma": dict(ka, sec=ka_sec)},
              fp, ensure_ascii=False, indent=2)
print("\n保存: out/018_compare.json")
