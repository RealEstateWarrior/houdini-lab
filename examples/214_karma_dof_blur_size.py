# -*- coding: utf-8 -*-
"""実験214 — カメラの F-Stop を変えると、背景のぼけは何画素になるか。レンズの式どおりか。

制作の問い: 実験205 で、F-Stop 0.7 でも背景があまりぼけなかった。狙った大きさのぼけにするには、F-Stop・焦点距離・ピントの距離を
どう決めればよいのか。Houdini のカメラの数字は、写真のレンズの式どおりに効くのか。

  真っ暗な中に、光る球（半径 5 cm。ピントが合うと直径約 8 画素）を 1 つ置き、カメラ（焦点距離 100 mm、Aperture 41.4214 mm）を 20 m 手前に置く。
  ピント（Focus Distance）は 2 m。球はピントより 18 m 奥にあるので、ぼけた円盤として写る。
  F-Stop を 1・2・4・8・16 にして 640×360 で撮り（Enable Depth of Field を入れる）、円盤の直径を画素で測る。
  測り方: 画の真ん中の窓（右下の透かしを避ける）で、明るさで重みを付けた中心からの距離の二乗平均（r_rms）を取る。
  一様に明るい円盤なら直径 = 2√2 × r_rms。ざらつきがあっても平均で消える。ピントを球に合わせた画（ぼけ無し）も撮り、
  広がりは足し算になる（r_rms² = 球の分² + ぼけの分²）ので、球の分を差し引いてぼけだけの直径を出す。
  （半径 5 mm の球では、ぼけた円盤がまばらな点になって測れなかった）
  （はじめは「いちばん明るい所の 2 割より明るい画素」の面積で測ったが、透かしを数えてしまい、どの F でも直径 53 画素と出た）
  式（薄いレンズ）: 画の上のぼけの直径（mm）= (f / N) × f × (d − s) / (d × (s − f))。f = 焦点距離、N = F-Stop、s = ピント、d = 球までの距離。
  これを Aperture（画の横幅 41.4214 mm）で割って 640 を掛けると画素になる。

    hython examples/214_karma_dof_blur_size.py
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)
FOCAL = 100.0
DIST = 20.0
FOCUS = 2.0
STOPS = [1, 2, 4, 8, 16]
BALL = 0.05


def formula_px(n, aperture):
    f, s, d = FOCAL, FOCUS * 1000, DIST * 1000
    coc_mm = (f / n) * f * (d - s) / (d * (s - f))
    return coc_mm / aperture * RES[0]


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "glow")
    ball = geo.createNode("sphere", "tiny_light_ball")
    ball.parm("type").set(2)
    ball.parmTuple("rad").set((BALL, BALL, BALL))
    ball.parm("rows").set(24)
    ball.parm("cols").set(24)
    matnet = hou.node("/mat")
    glow = matnet.createNode("principledshader::2.0", "glow_mat")
    glow.parmTuple("basecolor").set((0, 0, 0))
    glow.parmTuple("emitcolor").set((1, 1, 1))
    glow.parm("emitint").set(2000.0)
    asg = geo.createNode("material", "assign_glow")
    asg.setFirstInput(ball)
    asg.parm("shop_materialpath1").set(glow.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    cam = obj.createNode("cam", "lens")
    cam.parmTuple("t").set((0, 0, DIST))
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    cam.parm("focal").set(FOCAL)
    aperture = cam.parm("aperture").eval()
    karma = hou.node("/out").createNode("karma", "karma_lens")
    karma.parm("camera").set(cam.path())
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(256)
    karma.parm("varianceaa_maxsamples").set(256)
    karma.parm("enabledof").set(1)
    rows = []

    def shoot(tag, fstop, focus):
        cam.parm("fstop").set(fstop)
        cam.parm("focus").set(focus)
        path = os.path.join(OUT, f"214_{tag}.exr")
        karma.parm("picture").set(path.replace("\\", "/"))
        karma.render(frame_range=(1, 1, 1), verbose=False)
        buf = oiio.ImageBuf(path)
        a = buf.get_pixels(oiio.FLOAT)[..., :3].mean(axis=2)
        # 画の右下には Apprentice の透かしが入るので、真ん中の窓（横 200〜440、縦 60〜280）だけで測る
        w = a[60:280, 200:440].astype("float64")
        peak = float(w.max())
        area = int((w > peak * 0.2).sum())
        tot = float(w.sum())
        yy, xx = np.mgrid[0:w.shape[0], 0:w.shape[1]]
        cy, cx = (w * yy).sum() / tot, (w * xx).sum() / tot
        r_rms = float(np.sqrt((w * ((yy - cy) ** 2 + (xx - cx) ** 2)).sum() / tot))
        oiio.ImageBufAlgo.colorconvert(buf, "linear", "sRGB").write(path.replace(".exr", ".png"), "uint8")
        return {"tag": tag, "fstop": fstop, "focus": focus, "peak": round(peak, 4), "area_px": area,
                "diameter_px": round(2 * (area / np.pi) ** 0.5, 2), "total": round(tot, 3),
                "r_rms_px": round(r_rms, 3), "diameter_rms_px": round(2 * 2 ** 0.5 * r_rms, 2)}

    rows.append(shoot("sharp", 16, DIST))          # ピントを球に合わせる
    print(rows[-1], flush=True)
    r0 = rows[0]["r_rms_px"]
    for n in STOPS:
        r = shoot(f"f{n}", n, FOCUS)
        r["formula_px"] = round(formula_px(n, aperture), 2)
        # 広がり（分散）は足し算になるので、球そのものの大きさの分を差し引いて、ぼけだけの直径にする
        r["blur_diameter_px"] = round(2 * 2 ** 0.5 * max(r["r_rms_px"] ** 2 - r0 ** 2, 0) ** 0.5, 2)
        rows.append(r)
        print(r, flush=True)
    hou_tools.save_hip(os.path.join(OUT, "214_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "214_graph.json"), title="実験214")
    sop_bench.save(214, rows, {"res": RES, "focal_mm": FOCAL, "aperture_mm": aperture, "dist_m": DIST, "focus_m": FOCUS,
                               "ball_radius_m": BALL})


if __name__ == "__main__":
    main()
