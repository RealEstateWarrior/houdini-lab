"""実験024 — 動く煙で Karma を撮り直す。

実験018で2つのレンダラーを比べたとき、題材にしていた煙は<strong>動いていなかった</strong>。
それが分かったのは実験021。一様な球が濃くなるだけの絵で、
「どちらのレンダラーでも似たような塊にしかならない」という結論を出していた。

題材を入れ替えて確かめ直す。021で温度を供給して立ち上るようにした煙を使う。

018で出した結論は2つ。
  (a) OpenGL も輪郭と厚みによる濃淡は描ける
  (b) 描けていないのは、光が中を通ることによる陰影

形のある煙なら差がもっと出るはず。同じ指標で測って、018の数字と並べる。

    hython examples/024_karma_smoke.py
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

FRAME = 40
RES = (460, 760)
MARGIN = 1.04
DOME, KEY = 0.10, 0.25
VOXEL = 0.05
SAMPLES = 256


def build():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "smoke")

    emitter = geo.createNode("sphere", "emitter")
    emitter.parm("type").set(2)
    emitter.parmTuple("rad").set((0.22, 0.22, 0.22))
    emitter.parmTuple("t").set((0.0, -0.9, 0.0))
    emitter.parm("rows").set(24)
    emitter.parm("cols").set(24)

    src = geo.createNode("pyrosource", "src")
    src.setFirstInput(emitter)
    src.parm("attributes").set(2)
    src.parm("attribute1").set("density")
    src.parm("attribute2").set("temperature")   # これが無いと煙は動かない（021）

    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    rast.parm("attributes").set("density temperature")
    rast.parm("voxelsize").set(VOXEL)

    solver = geo.createNode("pyrosolver", "solve")
    solver.setFirstInput(rast)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)

    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(DOME)
    hou.node("/obj/report_key").parm("light_intensity").set(KEY)
    return geo, solver


def load(path):
    """透明度を白で埋めてから灰色にする。見たときの見え方に合わせる。"""
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
              and not (i % width > width * 0.70 and i // width > height * 0.84)]
    if not inside:
        return {"pixels": 0}
    mean = sum(inside) / len(inside)
    sd = math.sqrt(sum((v - mean) ** 2 for v in inside) / len(inside))
    row = height // 2
    profile = [px[row * width + x] for x in range(0, width, max(width // 24, 1))]
    return {"pixels": len(inside), "levels": len(set(inside)), "mean": mean,
            "sd": sd, "darkest": min(inside), "profile": profile,
            "size": [width, height]}


def main():
    geo, solver = build()
    hou.setFrame(FRAME)
    bbox = hou_tools.bbox_over_frames(solver.path(), [FRAME])

    gl_path = os.path.join(OUT, "024_opengl.png")
    start = time.perf_counter()
    hou_tools.render_preview(solver.path(), gl_path, res=RES, shading="smooth",
                             frame_bbox=bbox, margin=MARGIN)
    gl_sec = time.perf_counter() - start

    cam = hou.node("/obj/report_cam")
    karma = hou.node("/out").createNode("karma", "exp024_karma")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    ka_path = os.path.join(OUT, "024_karma.png")
    karma.parm("picture").set(ka_path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
    ka_sec = time.perf_counter() - start

    gl = describe(gl_path)
    ka = describe(ka_path)

    print("動く煙を2つのレンダラーで（同じカメラ・同じ露出）\n")
    print(f"{'':12s}{'時間':>8}{'煙の画素':>10}{'階調':>7}{'平均':>8}"
          f"{'ばらつき':>10}{'最も暗い':>10}")
    for name, sec, d in (("OpenGL ROP", gl_sec, gl), (f"Karma {SAMPLES}", ka_sec, ka)):
        print(f"{name:12s}{sec:7.2f}秒{d['pixels']:10d}{d['levels']:7d}"
              f"{d['mean']:8.1f}{d['sd']:10.2f}{d['darkest']:10d}")

    print("\n中心を横切る線の明るさ（左から右へ）")
    for name, d in (("OpenGL", gl), ("Karma ", ka)):
        print(f"  {name}: " + " ".join(f"{v:3d}" for v in d["profile"]))

    print("\n実験018（動かない煙）との比較")
    old = {"opengl": {"pixels": 29242, "levels": 235, "sd": 86.16, "darkest": 15},
           "karma": {"pixels": 21545, "levels": 200, "sd": 52.83, "darkest": 50}}
    print(f"{'':16s}{'018のOpenGL':>13}{'018のKarma':>12}"
          f"{'024のOpenGL':>13}{'024のKarma':>12}")
    for key, label in (("levels", "階調"), ("sd", "ばらつき"), ("darkest", "最も暗い")):
        print(f"{label:16s}{old['opengl'][key]:>13}{old['karma'][key]:>12}"
              f"{gl[key]:>13.2f}{ka[key]:>12.2f}"
              if key == "sd" else
              f"{label:16s}{old['opengl'][key]:>13}{old['karma'][key]:>12}"
              f"{gl[key]:>13}{ka[key]:>12}")

    with open(os.path.join(OUT, "024_stats.json"), "w", encoding="utf-8") as fp:
        json.dump({"frame": FRAME, "res": list(RES), "samples": SAMPLES,
                   "opengl": dict(gl, sec=gl_sec), "karma": dict(ka, sec=ka_sec),
                   "exp018": old}, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "024_graph.json"),
                          title="実験024 — 動く煙で Karma を撮り直す")
    hou_tools.save_hip(os.path.join(OUT, "024_karma.hipnc"))
    print("\n保存: out/024_stats.json, out/024_graph.json, out/024_karma.hipnc")


if __name__ == "__main__":
    main()
