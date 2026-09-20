"""実験086 — 葉を風で舞わせる。乱れ（Noise）のつまみは、散らばり方をどう変えるか。

粒を風で流し、popwind の Noise（Amplitude・Swirl Size）で舞わせる。
葉に見せるため、粒に小さな板を配り、進む向きに合わせる。

  A. Amplitude を 0 / 0.5 / 1 / 2 / 4 と変える。3秒後の散らばり（上下・前後の標準偏差）と、
     進んだ距離、計算の時間を測る
  B. Swirl Size を 0.5 / 2 / 8 と変える（Amplitude 2）。散らばりと、速さのばらつきを見る

    hython examples/086_leaves.py a
    hython examples/086_leaves.py b
    hython examples/086_leaves.py shot
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 72
FPS = 24.0
COUNT = 600


def build(amp=2.0, swirl=2.0, leaves=False):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "leaves")

    src_geo = geo.createNode("grid", "source_area")
    src_geo.parmTuple("size").set((1.0, 2.0))
    src_geo.parm("orient").set("zx")
    src_geo.parmTuple("t").set((0.0, 2.5, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    source.parm("soppath").set(src_geo.path())
    source.parm("emittype").set("surface")
    source.parm("constantactivate").set(True)
    source.parm("constantrate").set(COUNT / 3.0)      # 3秒で COUNT 個
    source.parm("impulseactiveate").set(False)
    source.parm("life").set(8.0)
    source.parm("initvel").set("set")
    for axis in "xyz":
        source.parm(f"var{axis}").set(0.2)

    grav = dop.createNode("popforce", "gravity")
    grav.parmTuple("force").set((0.0, -2.0, 0.0))     # 葉は軽いので弱めの重力

    wind = dop.createNode("popwind", "wind")
    wind.parmTuple("wind").set((2.0, 0.0, 0.0))
    wind.parm("windspeed").set(1.0)
    wind.parm("airresist").set(2.0)
    wind.parm("amp").set(amp)
    wind.parm("swirlsize").set(swirl)
    wind.setFirstInput(grav)

    solver.setInput(0, obj)
    solver.setInput(1, wind)
    solver.setInput(2, source)
    solver.setDisplayFlag(True)
    dop.layoutChildren()

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    out = imp
    if leaves:
        aim = geo.createNode("attribwrangle", "aim")
        aim.setFirstInput(imp)
        aim.parm("class").set(2)
        aim.parm("snippet").set(
            "@N = normalize(v@v);\n"
            "v@up = {0, 1, 0};\n"
            "@pscale = 0.6;")
        leaf = geo.createNode("grid", "leaf")
        leaf.parmTuple("size").set((0.12, 0.07))
        leaf.parm("orient").set("zx")
        leaf.parm("rows").set(2)
        leaf.parm("cols").set(2)
        copies = geo.createNode("copytopoints::2.0", "leaf_copies")
        copies.setInput(0, leaf)
        copies.setInput(1, aim)
        copies.parm("pack").set(1)
        out = copies
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    geo.layoutChildren()
    return geo, imp, out


def run(amp=2.0, swirl=2.0):
    import hou
    import hou_tools
    import numpy
    geo, imp, out = build(amp, swirl)
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        imp.geometry()
    sec = time.perf_counter() - start
    p = hou_tools.point_array(imp.geometry())
    v = hou_tools.point_array(imp.geometry(), "v")
    speed = numpy.linalg.norm(v, axis=1)
    return {"amp": amp, "swirl": swirl, "count": int(len(p)),
            "x_mean": float(p[:, 0].mean()), "x_max": float(p[:, 0].max()),
            "spread_y": float(p[:, 1].std()), "spread_z": float(p[:, 2].std()),
            "speed_mean": float(speed.mean()), "speed_sd": float(speed.std()),
            "seconds": sec}


def show(r):
    print(f"   Amplitude {r['amp']:<4} Swirl Size {r['swirl']:<4} | {r['count']}粒 | "
          f"進んだ x 平均 {r['x_mean']:.3f} 最大 {r['x_max']:.3f} | "
          f"散らばり 上下 {r['spread_y']:.4f} 前後 {r['spread_z']:.4f} | "
          f"速さ 平均 {r['speed_mean']:.3f} ばらつき {r['speed_sd']:.4f} | {r['seconds']:.2f}秒")


def part_a():
    print("A. 乱れの大きさ（Amplitude）を変える（Swirl Size 2）")
    rows = []
    for amp in (0.0, 0.5, 1.0, 2.0, 4.0):
        r = run(amp, 2.0)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "086_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/086_a.json")


def part_b():
    print("B. 渦の大きさ（Swirl Size）を変える（Amplitude 2）")
    rows = []
    for swirl in (0.5, 2.0, 8.0):
        r = run(2.0, swirl)
        rows.append(r)
        show(r)
    with open(os.path.join(OUT, "086_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/086_b.json")


def shot(amp="2"):
    import hou
    import hou_tools
    geo, imp, out = build(float(amp), 2.0, leaves=True)
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        out.geometry()
    if amp == "2":
        hou_tools.save_hip(os.path.join(OUT, "086_leaves.hipnc"))
    bbox = hou.BoundingBox(-1.0, -0.5, -2.0, 7.0, 3.2, 2.0)
    png = os.path.join(OUT, f"086_leaves_{amp.replace('.', '_')}.png")
    hou_tools.render_preview(out.path(), png, res=(760, 420), direction=(0.1, 0.35, 1.0),
                             shading="smooth", frame_bbox=bbox, margin=1.03)
    print(f"保存: {png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "2")
    else:
        {"a": part_a, "b": part_b}[arg]()
