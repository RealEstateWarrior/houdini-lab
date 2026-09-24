# -*- coding: utf-8 -*-
"""実験213 — サブサーフェス（SSS）の Subsurface Distance を変えると、影の側の明るさ（透け方）はどれだけ変わるか。

制作の問い: ろうそく・雪・肌・石けんのような「光が中に入って透ける」物を作りたい。principledshader の Subsurface を入れたとき、
Subsurface Distance（光が中で散らばる距離、既定 0.1）をいくつにすると、どれだけ透けて見えるのか。物の大きさとの関係は。

  半径 0.5 の球に、Base Color (0.9, 0.85, 0.75)・Roughness 0.4 の材質を当て、実践と同じ撮り方（暗い幕・板のキー・リム・弱いドーム）で
  640×640・16 サンプル＋ノイズ除去、EXR で撮る。
    none   … Subsurface 0（ふつうの白い球）
    d001 / d005 / d010（既定）/ d030 / d100 … Subsurface 1、Subsurface Distance 0.01・0.05・0.1・0.3・1（Subsurface Color は白）
    rw010  … d010 の SSS Mode を Random Walk (Karma) に
  正面寄りの明かり（front）と、キーを球の真後ろに回した逆光（back。リムは消し、ドームは 0.02）の 2 通りで撮る。
  測るもの（OpenImageIO で EXR を読む）: 球が写っている所の平均の明るさ（front と back）、
  逆光の画の、球の真ん中（半径の 5 割の内側。厚い所）と縁（7 割より外。薄い所）の平均。
  （はじめは正面の明かりだけで「影の側」を測ろうとしたが、明かりがほぼ正面から当たっていて透けは測れなかった）
  （撮る時間は、点検（実験210）と同時に回したので比べない）

    hython examples/213_karma_sss_distance.py
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 640)
CASES = {"none": (0.0, 0.1, None), "d001": (1.0, 0.01, None), "d005": (1.0, 0.05, None), "d010": (1.0, 0.1, None),
         "d030": (1.0, 0.3, None), "d100": (1.0, 1.0, None), "rw010": (1.0, 0.1, "pbrrwalksss")}


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import practice_kit as kit
    import sop_bench
    g = kit.Guide("exp213", "実験213", "", tags=[])
    ball = g.node("sphere", "ball", type=2, rad=(0.5, 0.5, 0.5), rows=64, cols=64, t=(0, 0.5, 0))
    wax = g.mat("wax_mat", basecolor=(0.9, 0.85, 0.75), rough=0.4)
    final = g.assign(ball, wax, "assign_wax")
    g.hero(final, "", res=RES, spp=16, denoise=True, bbox=hou.BoundingBox(-0.5, 0, -0.5, 0.5, 1.0, 0.5))
    karma = hou.node("/out/hero_karma")
    modes = wax.parm("sssmodel").parmTemplate().menuItems()
    print("SSS Mode:", list(modes), flush=True)
    imgs = {}

    def shoot_all(light):
        for name, (w, dist, mode) in CASES.items():
            wax.parm("sss").set(w)
            wax.parm("sssdist").set(dist)
            wax.parm("sssmodel").set(mode or "pbrsss")
            path = os.path.join(OUT, f"213_{light}_{name}.exr")
            karma.parm("picture").set(path.replace("\\", "/"))
            karma.render(frame_range=(hou.frame(), hou.frame(), 1), verbose=False)
            buf = oiio.ImageBuf(path)
            oiio.ImageBufAlgo.colorconvert(buf, "linear", "sRGB").write(path.replace(".exr", ".png"), "uint8")
            imgs[(light, name)] = lum(buf.get_pixels(oiio.FLOAT)[..., :3])
            print(light, name, flush=True)

    shoot_all("front")
    # 逆光: キーの明かりを球の真後ろ（カメラの反対側）に回し、リムとドームを消す。透けた光だけが前に出る
    cam = hou.node("/obj/hero_cam")
    cpos = cam.worldTransform().extractTranslates()
    c = hou.Vector3(0, 0.5, 0)
    back = c - (cpos - c).normalized() * 2.0
    key = hou.node("/obj/hero_key")
    key.parmTuple("t").set(back)
    key.parmTuple("r").set(hou.hmath.buildRotateLookAt(back, c, hou.Vector3(0, 1, 0)).extractRotates())
    key.parm("light_intensity").set(8.0)
    hou.node("/obj/hero_rim").parm("light_intensity").set(0)
    hou.node("/obj/hero_dome").parm("light_intensity").set(0.02)
    shoot_all("back")
    # 球の位置は、正面から撮った SSS なしの画の明るい所の外接円から取る
    ref = imgs[("front", "none")]
    h, w = ref.shape
    bg = float(np.median(ref[: h // 10, :]))
    ys, xs = np.nonzero(ref > bg * 3 + 0.01)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    rad = (xs.max() - xs.min()) / 2
    yy, xx = np.mgrid[0:h, 0:w]
    sphere = (yy - cy) ** 2 + (xx - cx) ** 2 <= (rad * 0.97) ** 2
    rr = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2) / rad
    center = sphere & (rr < 0.5)                  # 球の厚い真ん中
    edge = sphere & (rr > 0.7)                    # 薄い縁
    rows = []
    for name, (wt, dist, mode) in CASES.items():
        f, b = imgs[("front", name)], imgs[("back", name)]
        rows.append({"case": name, "sss": wt, "dist": dist, "mode": mode or "pbrsss",
                     "front_all": round(float(f[sphere].mean()), 5),
                     "back_all": round(float(b[sphere].mean()), 5), "back_center": round(float(b[center].mean()), 5),
                     "back_edge": round(float(b[edge].mean()), 5)})
        print(rows[-1], flush=True)
    import hou_tools
    g.geo.layoutChildren()
    wax.parm("sss").set(1.0)
    wax.parm("sssdist").set(0.1)
    hou_tools.save_hip(os.path.join(OUT, "213_scene.hipnc"))
    hou_tools.write_graph(g.geo.path(), os.path.join(OUT, "213_graph.json"), title="実験213")
    sop_bench.save(213, rows, {"res": RES, "radius_m": 0.5, "sphere_px": int(sphere.sum()), "background": bg, "modes": list(modes)})


if __name__ == "__main__":
    main()
