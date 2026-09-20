"""実験088 — 文字を光らせる。発光の強さは、絵の中でどう効くか。

立体文字を床の上に置き、文字の材質に発光（Emission）を入れて Karma で撮る。

  A. Emission Intensity を 0 / 1 / 4 / 16 / 64 と変える。
     文字の明るさ、白飛びした画素の割合、床の明るさ（こぼれた光）を測る
  B. Emission Illuminates Objects（emitillum）を切ると、床は暗くなるか

ライトはドームだけ弱く入れる（0.12）。発光の効き方だけを見たいため。

    hython examples/088_glow.py a
    hython examples/088_glow.py b
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
RES = (640, 400)
SAMPLES = 24


def build():
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "glow")

    text = geo.createNode("font", "letters")
    text.parm("text").set("SP")
    thick = geo.createNode("polyextrude::2.0", "thickness")
    thick.setFirstInput(text)
    thick.parm("dist").set(0.15)
    thick.parm("outputback").set(1)
    mid = thick.geometry().boundingBox().center()
    center = geo.createNode("xform", "center")
    center.setFirstInput(thick)
    center.parmTuple("t").set((-mid[0], -mid[1] + 0.42, -mid[2]))   # 床の上に立てる

    floor = geo.createNode("grid", "floor")
    floor.parmTuple("size").set((6.0, 4.0))
    floor.parm("rows").set(2)
    floor.parm("cols").set(2)

    mat = hou.node("/mat") or hou.node("/").createNode("mat")
    glow = mat.createNode("principledshader::2.0", "glow_mat")
    glow.parmTuple("emitcolor").set((1.0, 0.55, 0.15))
    glow.parm("emitint").set(0.0)
    glow.parmTuple("basecolor").set((0.2, 0.2, 0.2))
    plain = mat.createNode("principledshader::2.0", "floor_mat")
    plain.parmTuple("basecolor").set((0.6, 0.6, 0.62))
    plain.parm("rough").set(0.6)

    assign_text = geo.createNode("material", "assign_glow")
    assign_text.setFirstInput(center)
    assign_text.parm("shop_materialpath1").set(glow.path())
    assign_floor = geo.createNode("material", "assign_floor")
    assign_floor.setFirstInput(floor)
    assign_floor.parm("shop_materialpath1").set(plain.path())

    both = geo.createNode("merge", "scene")
    both.setInput(0, assign_floor)
    both.setInput(1, assign_text)
    both.setDisplayFlag(True)
    both.setRenderFlag(True)
    geo.layoutChildren()
    return geo, both, glow


def render(node, tag):
    import hou
    import hou_tools
    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(0.12)
    hou.node("/obj/report_key").parm("light_intensity").set(0.05)
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    bbox = hou.BoundingBox(-1.6, -0.05, -1.2, 1.6, 1.1, 1.2)
    hou_tools._frame_camera(cam, bbox, RES, (0.15, 0.35, 1.0), margin=1.05)

    karma = hou.node("/out").node(f"karma_{tag}") or hou.node("/out").createNode("karma", f"karma_{tag}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"088_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    return path, time.perf_counter() - start


def measure(path):
    """文字のあたり（真ん中）と、床のあたり（下の帯）の明るさを別々に見る。"""
    import numpy
    from PIL import Image
    img = numpy.asarray(Image.open(path).convert("RGB"), dtype=float)
    h, w, _ = img.shape
    letters = img[int(h * 0.30):int(h * 0.62), int(w * 0.25):int(w * 0.75)]
    floor = img[int(h * 0.82):int(h * 0.98), :]
    lum = img.mean(axis=2)
    return {"letters_mean": float(letters.mean()), "letters_max": float(letters.max()),
            "floor_mean": float(floor.mean()),
            "clipped_pct": float((lum > 250).mean() * 100),
            "image_mean": float(lum.mean())}


def part_a():
    print("A. Emission Intensity を変える（Karma 640×400・サンプル24）")
    geo, scene, glow = build()
    rows = []
    for emit in (0.0, 1.0, 4.0, 16.0, 64.0):
        glow.parm("emitint").set(emit)
        path, sec = render(scene, f"emit{int(emit)}")
        m = measure(path)
        m.update({"emit": emit, "seconds": sec, "file": os.path.basename(path)})
        rows.append(m)
        print(f"   Emission {emit:<5} | 文字 平均 {m['letters_mean']:6.2f} 最大 {m['letters_max']:5.1f} | "
              f"床 平均 {m['floor_mean']:6.2f} | 白飛び {m['clipped_pct']:.2f}% | {sec:.2f}秒")
    with open(os.path.join(OUT, "088_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/088_a.json")


def part_b():
    print("B. Emission Illuminates Objects の入り・切り（Emission 16）")
    geo, scene, glow = build()
    rows = []
    for illum in (1, 0):
        glow.parm("emitint").set(16.0)
        glow.parm("emitillum").set(illum)
        path, sec = render(scene, f"illum{illum}")
        m = measure(path)
        m.update({"emitillum": illum, "seconds": sec, "file": os.path.basename(path)})
        rows.append(m)
        print(f"   emitillum {'入' if illum else '切'} | 文字 平均 {m['letters_mean']:6.2f} | "
              f"床 平均 {m['floor_mean']:6.2f} | 白飛び {m['clipped_pct']:.2f}% | {sec:.2f}秒")
    with open(os.path.join(OUT, "088_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/088_b.json")


if __name__ == "__main__":
    {"a": part_a, "b": part_b}[sys.argv[1] if len(sys.argv) > 1 else "a"]()
