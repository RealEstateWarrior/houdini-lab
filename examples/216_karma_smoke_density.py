# -*- coding: utf-8 -*-
"""実験216 — 煙の Density Scale を倍にすると、向こうの透け具合はどう変わるか。光の吸収の式（ベールの法則）どおりか。

制作の問い: 煙が薄すぎる・濃すぎるとき、kma_pyroshader の Density Scale をいくつにすればよいか。
「倍にすると倍濃くなる」のか。煙の厚み（奥行き）とどう関係するのか。

  真っ白に光る板（Emission 1）の手前に、濃さ（density）1 の一様な煙の箱（1 × 1 × 厚み L）を置き、正面から撮る。
  明かりは入れない（明るさ 0 のドームを置き、Karma が自動で足す明かりも止める）。煙の Enable Scatter は切ったまま（既定）なので、
  煙は光を減らすだけになる。板の光のうち、煙を通って届いた割合 T を、EXR の明るさ（煙の中 ÷ 煙の外）で測る。
    Density Scale: 0.25・0.5・1・2・4（L = 0.5 m）と、L = 1 m で Density Scale 1
    濃い煙で式とのずれが出たので、Karma の Volume Step Rate（既定 0.25）を 0.05・1 にしたものも撮る
  式（ベールの法則）: T = exp(−k × Density Scale × density × L)。k は 1 m あたりの減り方。
  もし k = 1 なら、L = 0.5・Density Scale 1 で T = exp(−0.5) = 0.607。

    hython examples/216_karma_smoke_density.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)
CASES = [("s025", 0.25, 0.5, 0.25), ("s050", 0.5, 0.5, 0.25), ("s100", 1.0, 0.5, 0.25), ("s200", 2.0, 0.5, 0.25), ("s400", 4.0, 0.5, 0.25),
         ("s100_L1", 1.0, 1.0, 0.25),
         # 濃いほど式より明るく出た（4 で +12%）。Volume Step Rate（既定 0.25）を変えて切り分ける
         ("s400_step005", 4.0, 0.5, 0.05), ("s400_step1", 4.0, 0.5, 1.0), ("s200_step005", 2.0, 0.5, 0.05)]


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "smoke_box")
    vol = geo.createNode("volume", "fog")
    vol.parm("name").set("density")
    vol.parm("divsize").set(0.05)
    fill = geo.createNode("volumewrangle", "density_one")
    fill.setFirstInput(vol)
    fill.parm("snippet").set("// 箱の中を濃さ 1 で満たす\n@density = 1;")
    smoke = hou.node("/mat").createNode("kma_pyroshader", "smoke_mat")
    asg = geo.createNode("material", "assign_smoke")
    asg.setFirstInput(fill)
    asg.parm("shop_materialpath1").set(smoke.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    back = obj.createNode("geo", "glow_board")
    board = back.createNode("grid", "board")
    board.parm("orient").set("xy")
    board.parmTuple("size").set((6, 4))
    board.parmTuple("t").set((0, 0, -2))
    glow = hou.node("/mat").createNode("principledshader::2.0", "board_glow")
    glow.parmTuple("basecolor").set((0, 0, 0))
    glow.parmTuple("emitcolor").set((1, 1, 1))
    glow.parm("emitint").set(1.0)
    gasg = back.createNode("material", "assign_glow")
    gasg.setFirstInput(board)
    gasg.parm("shop_materialpath1").set(glow.path())
    gasg.setDisplayFlag(True)
    gasg.setRenderFlag(True)
    dark = obj.createNode("envlight", "no_light")          # 明かり 0（Karma が自動で明かりを足さないように）
    dark.parm("light_intensity").set(0)
    cam = obj.createNode("cam", "front")
    cam.parmTuple("t").set((0, 0, 6))
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma = hou.node("/out").createNode("karma", "karma_smoke")
    karma.parm("camera").set(cam.path())
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(32)
    karma.parm("varianceaa_maxsamples").set(32)
    rows = []
    for tag, scale, L, step in CASES:
        vol.parmTuple("size").set((1.0, 1.0, L))
        smoke.parm("densityscale").set(scale)
        karma.parm("volumesteprate").set(step)
        path = os.path.join(OUT, f"216_{tag}.exr")
        karma.parm("picture").set(path.replace("\\", "/"))
        karma.render(frame_range=(1, 1, 1), verbose=False)
        buf = oiio.ImageBuf(path)
        a = buf.get_pixels(oiio.FLOAT)[..., :3].mean(axis=2).astype("float64")
        oiio.ImageBufAlgo.colorconvert(buf, "linear", "sRGB").write(path.replace(".exr", ".png"), "uint8")
        h, w = a.shape
        inside = a[h // 2 - 20:h // 2 + 20, w // 2 - 20:w // 2 + 20].mean()      # 煙の箱の真ん中
        outside = a[h // 2 - 20:h // 2 + 20, 150:190].mean()                      # 箱の左の、煙の無い所（板だけ。端の外は暗いので避ける）
        T = inside / outside
        rows.append({"case": tag, "scale": scale, "L": L, "step": step, "inside": round(float(inside), 5), "outside": round(float(outside), 5),
                     "T": round(float(T), 5), "k": round(-math.log(T) / (scale * L), 4) if T > 0 else None,
                     "T_if_k1": round(math.exp(-scale * L), 5)})
        print(rows[-1], flush=True)
    vol.parmTuple("size").set((1.0, 1.0, 0.5))
    smoke.parm("densityscale").set(1.0)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "216_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "216_graph.json"), title="実験216")
    sop_bench.save(216, rows, {"res": RES})


if __name__ == "__main__":
    main()
