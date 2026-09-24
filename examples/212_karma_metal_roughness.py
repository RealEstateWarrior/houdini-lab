# -*- coding: utf-8 -*-
"""実験212 — 金属の球の Roughness を変えると、光の点（ハイライト）の大きさと明るさはどう変わるか。

制作の問い: 金属を「つやつや」から「つや消し」まで見せ分けたい。principledshader の Roughness をいくつにすると、
ハイライトがどれだけ広がって、どれだけ暗くなるのか。見た目の目安になる数字がほしい。

  半径 0.5 の球（Polygon Mesh 64×64）に、Base Color 0.9 の金属（Metallic 1）を当て、Roughness を
  0・0.05・0.1・0.2・0.3・0.5・0.7 にして、practice_kit と同じ撮り方（暗い幕・キー・リム・ドーム。キーは板の明かり）で
  640×640・16 サンプル＋ノイズ除去で撮る。画は EXR（明るさが 1 を超えても切れない）で書き、OpenImageIO で読む。
  測るもの:
    - キーの明かりが映った所（画の右上の 4 分の 1）の、いちばん明るい画素の明るさ（輝度）
    - その半分より明るい画素の数（ハイライトの大きさ）を、球が写っている画素の数で割った割合
    - 球が写っている所の平均の明るさ

    hython examples/212_karma_metal_roughness.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
ROUGH = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7]
RES = (640, 640)


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import practice_kit as kit
    import sop_bench
    g = kit.Guide("exp212", "実験212", "", tags=[])
    ball = g.node("sphere", "ball", type=2, rad=(0.5, 0.5, 0.5), rows=64, cols=64, t=(0, 0.5, 0))
    metal = g.mat("metal_mat", basecolor=(0.9, 0.9, 0.9), rough=0.0, metallic=1.0)
    final = g.assign(ball, metal, "assign_metal")
    g.hero(final, "", res=RES, spp=16, denoise=True, bbox=hou.BoundingBox(-0.5, 0, -0.5, 0.5, 1.0, 0.5))
    karma = hou.node("/out/hero_karma")
    rows = []
    for r in ROUGH:
        metal.parm("rough").set(r)
        path = os.path.join(OUT, f"212_r{int(r * 100):03d}.exr")
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(hou.frame(), hou.frame(), 1), verbose=False)
        sec = time.perf_counter() - t0
        buf = oiio.ImageBuf(path)
        a = buf.get_pixels(oiio.FLOAT)[..., :3]
        # 表示用の PNG（sRGB にして 0〜1 で切る）
        png = oiio.ImageBufAlgo.colorconvert(buf, "linear", "sRGB")
        png.write(path.replace(".exr", ".png"), "uint8")
        rows.append({"rough": r, "sec": round(sec, 2), "lum": lum(a).astype("float32")})
        print(r, round(sec, 1), flush=True)
    # 球の画素: どの Roughness でも、背景（幕）より明るい所を「球」とみなすと、つや消しで暗い縁が抜けるので、
    # 球の位置と大きさは幾何で決める（画の上の球の中心と半径を、Roughness 0.7 の画の明るい所の外接円から取る）
    h, w = rows[0]["lum"].shape
    ref = rows[-1]["lum"]
    bg = float(np.median(ref[: h // 10, :]))                  # 画の上 1 割（幕の奥）の明るさ
    ys, xs = np.nonzero(ref > bg * 3 + 0.01)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    rad = (xs.max() - xs.min()) / 2
    yy, xx = np.mgrid[0:h, 0:w]
    sphere = (yy - cy) ** 2 + (xx - cx) ** 2 <= (rad * 0.98) ** 2
    upper_right = sphere & (yy < cy) & (xx > cx - rad * 0.2)
    out = []
    for row in rows:
        L = row["lum"]
        peak = float(L[upper_right].max())
        half = int(((L >= peak * 0.5) & sphere).sum())
        out.append({"rough": row["rough"], "sec": row["sec"], "peak": round(peak, 4), "half_area_px": half,
                    "half_area_frac": round(half / int(sphere.sum()), 5), "mean_on_sphere": round(float(L[sphere].mean()), 5)})
        print(out[-1], flush=True)
    import hou_tools
    g.geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "212_scene.hipnc"))
    hou_tools.write_graph(g.geo.path(), os.path.join(OUT, "212_graph.json"), title="実験212")
    sop_bench.save(212, out, {"res": RES, "sphere_px": int(sphere.sum()), "center": [float(cx), float(cy)], "radius_px": float(rad),
                              "background": bg})


if __name__ == "__main__":
    main()
