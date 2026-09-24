# -*- coding: utf-8 -*-
"""実験230 — 速く回る物（羽・車輪）のブレを、Karma で弧にするには何サンプル要るか。

制作の問い: 扇風機の羽や車輪のように速く回る物をモーションブラーで撮ると、ブレが弧ではなく、まっすぐな線になることがある。
Karma の Transform Time Samples（既定 2）・Motion Blur Style（既定 Rotation Blur）・Geometry Time Samples（既定 2）の、どれをいくつにすればよいか。

  中心から 1 m の所に、半径 5 cm の光る球を置き、1 フレームで 180° 回す（z 軸まわり）。カメラのシャッターは既定の 0.5 フレームなので、
  本物なら 90° の弧のブレになる。真正面から平行投影（幅 3 m）で 400×400 に撮り、ブレの筋の画素が中心からどれだけ離れているかを測る。
  弧ならどこも 1 m。まっすぐな線（弦）なら、真ん中が 0.71 m まで内側に寄る。
    obj_rot_2    … オブジェクトごと回す。Transform Time Samples 2・Rotation Blur（既定）
    obj_lin_2    … 同じで Linear Blur
    obj_lin_8    … Linear Blur・Transform Time Samples 8
    sop_2・4・8・16 … オブジェクトは止めて、中の transform（SOP）で回す。Geometry Time Samples 2・4・8・16
  測るもの: ブレの筋（明るさ 0.05 超の画素。右下の透かしは除く）の、中心からの距離の平均と 5 パーセンタイル（いちばん内側）、筋が広がる角度、撮る時間。

    hython examples/230_karma_rotation_blur.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = 400
WIDTH = 3.0
FRAME = 10
CASES = [("obj_rot_2", "obj", 2, "Rotation Blur", 2), ("obj_lin_2", "obj", 2, "Linear Blur", 2), ("obj_lin_8", "obj", 8, "Linear Blur", 2),
         ("sop_2", "sop", 2, "Rotation Blur", 2), ("sop_4", "sop", 2, "Rotation Blur", 4), ("sop_8", "sop", 2, "Rotation Blur", 8),
         ("sop_16", "sop", 2, "Rotation Blur", 16)]


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.setFps(24)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "spinner")
    ball = geo.createNode("sphere", "ball")
    ball.parm("type").set("polymesh")
    ball.parmTuple("rad").set((0.05, 0.05, 0.05))
    ball.parmTuple("t").set((1, 0, 0))
    spin = geo.createNode("xform", "spin_in_sop")
    spin.setFirstInput(ball)
    mat = hou.node("/mat").createNode("principledshader::2.0", "glow")
    mat.parmTuple("basecolor").set((0, 0, 0))
    mat.parm("reflect").set(0)
    mat.parmTuple("emitcolor").set((1, 1, 1))
    mat.parm("emitint").set(4)
    asg = geo.createNode("material", "assign")
    asg.setFirstInput(spin)
    asg.parm("shop_materialpath1").set(mat.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    dark = obj.createNode("envlight", "no_auto_light")
    dark.parm("light_intensity").set(0)
    cam = obj.createNode("cam", "cam")
    cam.parm("projection").set("ortho")
    cam.parm("orthowidth").set(WIDTH)
    cam.parmTuple("t").set((0, 0, 5))
    cam.parm("resx").set(RES)
    cam.parm("resy").set(RES)
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    karma.parm("resolutionx").set(RES)
    karma.parm("resolutiony").set(RES)
    karma.parm("samplesperpixel").set(64)
    karma.parm("varianceaa_maxsamples").set(64)
    rows = []
    hou.setFrame(FRAME)
    for name, where, xs, style, gs in CASES:
        # 回し方を切り替える（1 フレームで 180°）
        geo.parm("rz").setExpression("$FF * 180" if where == "obj" else "0")
        spin.parm("rz").setExpression("$FF * 180" if where == "sop" else "0")
        karma.parm("xformsamples").set(xs)
        karma.parm("blurstyle").set(style)
        karma.parm("geosamples").set(gs)
        exr = os.path.join(OUT, f"_230_{name}.exr")
        karma.parm("picture").set(exr.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        sec = time.perf_counter() - t0
        px = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[:, :, :3].mean(axis=2)
        ys, xs_ = np.nonzero(px > 0.05)
        # 画素 → 世界の座標（平行投影、中心が原点、幅 3 m。画の上が +y）
        wx = (xs_ + 0.5) / RES * WIDTH - WIDTH / 2
        wy = WIDTH / 2 - (ys + 0.5) / RES * WIDTH
        keep = wy > -1.0          # 画の右下の Apprentice の透かしは数えない（ブレは右上の 4 分の 1 に出る）
        wx, wy = wx[keep], wy[keep]
        r = np.hypot(wx, wy)
        ang = np.degrees(np.arctan2(wy, wx))
        span = float(ang.max() - ang.min()) if len(ang) else 0.0
        info = {"case": name, "where": where, "xformsamples": xs, "blurstyle": style, "geosamples": gs, "sec": round(sec, 2),
                "pixels": int(len(r)), "r_mean": round(float(r.mean()), 4), "r_p5": round(float(np.percentile(r, 5)), 4),
                "span_deg": round(span, 1)}
        rows.append(info)
        print(info, flush=True)
        view = np.clip(oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[:, :, :3], 0, 1) ** (1 / 2.2)
        ob = oiio.ImageBuf(oiio.ImageSpec(RES, RES, 3, oiio.UINT8))
        ob.set_pixels(oiio.ROI(0, RES, 0, RES, 0, 1, 0, 3), view.astype(np.float32))
        ob.write(os.path.join(OUT, f"230_{name}.png"))
        os.remove(exr)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "230_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "230_graph.json"), title="実験230")
    sop_bench.save(230, rows, {"res": RES, "width": WIDTH, "frame": FRAME})


if __name__ == "__main__":
    main()
