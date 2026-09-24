# -*- coding: utf-8 -*-
"""実験237 — 風船をねらった大きさにふくらませるには、Vellum の Pressure の Rest Length Scale をいくつにすればよいか。

制作の問い: 実践「風船をふくらませる」では、Pressure の Rest Length Scale を 3 にした（「今の 3 倍の体積が本来の大きさ」）。
では、体積は本当に 3 倍になるのか。ゴムの膜の硬さ（Cloth の Stretch Stiffness）で、ふくらみ方は変わるのか。何フレームで落ち着くのか。

  実践と同じ、しぼんだしずく形の風船（sphere 24×32 を下半分だけ細くした、体積 0.00486 m³ ほど）に、
  Cloth（Stretch Stiffness 1 × 10³）と Pressure をかけ、重力 0・Substeps 5 で 48 フレーム回す。
    Rest Length Scale 1.5・2・3（実践）・4・6（膜の硬さ 10³）
    膜の硬さ 10²・10⁴（Rest Length Scale 3）
  測るもの: フレームごとの体積（はじめの体積との比）。48 フレーム目の比と、ねらった比（Rest Length Scale）との違い。
            体積が 48 フレーム目の 95% に達したフレーム。48 フレーム目の外枠の縦 ÷ 横（しずく形が残っていれば 1 より大きい）。

    hython examples/237_vellum_balloon_pressure.py
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
LAST = 48
CASES = [("r1.5", 1.5, 3), ("r2", 2.0, 3), ("r3", 3.0, 3), ("r4", 4.0, 3), ("r6", 6.0, 3), ("r3_soft", 3.0, 2), ("r3_hard", 3.0, 4)]


def main():
    import hou
    import hou_tools
    import sop_bench
    spec = importlib.util.spec_from_file_location("prb", os.path.join(HERE, "examples", "pr_balloon.py"))
    prb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prb)
    hou.setFps(24)
    geo = sop_bench.fresh()
    ball = geo.createNode("sphere", "rubber")
    ball.parm("type").set("polymesh")
    ball.parm("rows").set(24)
    ball.parm("cols").set(32)
    ball.parmTuple("rad").set((0.11, 0.13, 0.11))
    shape = geo.createNode("attribwrangle", "teardrop")
    shape.setFirstInput(ball)
    shape.parm("snippet").set("if (@P.y < 0) {\n    float k = fit(@P.y, -0.13, 0, 0.3, 1);\n    @P.x *= k;  @P.z *= k;\n}\n"
                              "i@group_knot = @P.y < -0.125;")
    skin = geo.createNode("vellumconstraints", "rubber_skin")
    skin.setFirstInput(shape)
    skin.parm("constrainttype").set("cloth")
    skin.parm("pingroup").set("knot")
    skin.parm("stretchstiffness").set(1.0)
    air = geo.createNode("vellumconstraints", "air_pressure")
    air.setInput(0, skin, 0)
    air.setInput(1, skin, 1)
    air.parm("constrainttype").set("pressure")
    solver = geo.createNode("vellumsolver", "inflate")
    solver.setInput(0, air, 0)
    solver.setInput(1, air, 1)
    solver.parm("substeps").set(5)
    solver.parmTuple("gravity").set((0, 0, 0))
    v0 = prb.volume(shape.geometry())
    b0 = shape.geometry().boundingBox().sizevec()
    aspect0 = b0[1] / max(b0[0], b0[2])
    rows = []
    for name, rls, exp in CASES:
        air.parm("stretchrestscale").set(rls)
        skin.parm("stretchstiffnessexp").set(exp)
        vols = []
        t0 = time.perf_counter()
        for f in range(1, LAST + 1):
            hou.setFrame(f)
            vols.append(prb.volume(solver.geometry()) / v0)
        sec = time.perf_counter() - t0
        final = vols[-1]
        bb = solver.geometry().boundingBox()
        size = bb.sizevec()
        aspect = size[1] / max(size[0], size[2])      # 縦 ÷ 横（しずく形は 1 より大きく、球は 1）
        settle = next(i + 1 for i, v in enumerate(vols) if abs(v - 1) >= 0.95 * abs(final - 1))
        rows.append({"case": name, "rest_length_scale": rls, "stiffness_exp": exp, "ratio_final": round(final, 4),
                     "ratio_f12": round(vols[11], 4), "ratio_f24": round(vols[23], 4), "settle_frame": settle,
                     "sec": round(sec, 2), "height": round(size[1], 4), "width": round(max(size[0], size[2]), 4), "aspect": round(aspect, 4),
                     "ratios": [round(v, 4) for v in vols]})
        print({k: v for k, v in rows[-1].items() if k != "ratios"}, flush=True)
        if name in ("r1.5", "r3", "r6", "r3_hard"):
            hou_tools.render_preview(solver.path(), os.path.join(OUT, f"237_{name.replace('.', 'p')}.png"), res=(360, 400),
                                     direction=(1.0, 0.2, 1.0), shading="smoothwire",
                                     frame_bbox=hou.BoundingBox(-0.3, -0.2, -0.3, 0.3, 0.5, 0.3))
    air.parm("stretchrestscale").set(3.0)
    skin.parm("stretchstiffnessexp").set(3)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "237_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "237_graph.json"), title="実験237")
    sop_bench.save(237, rows, {"last": LAST, "v0": round(v0, 6), "aspect0": round(aspect0, 4)})


if __name__ == "__main__":
    main()
