# -*- coding: utf-8 -*-
"""実験218 — 海のきらめき（太陽の下の光の道）の幅と細かさは、水の Roughness とさざ波の高さのどちらで決まるか。

制作の問い: 海の画で「光の道をもっと広く」「もっと細かくきらめかせたい」とき、どのつまみを動かせばよいか。
実践「冬の朝の七里ヶ浜」（pr_ocean_winter.hipnc）の場面を使う。太陽は高さ 15°・左へ 12°、カメラは砂浜の目の高さ 1.5 m。

  水の材質（sea_mat）の Roughness: 0.005・0.02・0.04（実践の値）・0.08・0.15
  さざ波（ripples、Grid Size 1.3 m）の Amplitude の Scale: 0.4・1.6（実践の値）・3.2
  の 15 通りを、Karma で 480×270・8 サンプル、フレーム 30 で EXR に撮る（明るさを頭打ちさせずに測るため）。
  測る所: 画面の縦 160〜190 行（カメラから約 60 m〜12 m 先の水面。太陽は 186 列目の上）。
    背景 … 太陽から離れた列（330 列より右）の明るさの中央値
    光の道の幅 … 列ごとの平均の明るさが、背景の 3 倍を超える列の数（1 列 ≈ 0.18°）
    光の道の強さ … 背景を引いた明るさの合計を、測る所の画素の数で割ったもの
    粒の割合 … 光の道の列の中で、背景の 20 倍を超える画素の割合（細かく光る粒の多さ）

    hython examples/218_ocean_glitter_rough.py
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (480, 270)
ROWS = (160, 190)
FAR_COL = 330
ROUGH = (0.005, 0.02, 0.04, 0.08, 0.15)
AMP = (0.4, 1.6, 3.2)
FRAME = 30


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.load(os.path.join(OUT, "pr_ocean_winter.hipnc"), suppress_save_prompt=True)
    hou.setFrame(FRAME)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 8), ("varianceaa_maxsamples", 8)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    water = hou.node("/mat/sea_mat")
    ripples = hou.node("/obj/ocean_winter/ripples")
    rows = []
    for amp in AMP:
        ripples.parm("ampscale").set(amp)
        for rough in ROUGH:
            water.parm("rough").set(rough)
            name = f"218_r{rough:g}_a{amp:g}".replace(".", "p")
            exr = os.path.join(OUT, "_" + name + ".exr")
            karma.parm("picture").set(exr.replace("\\", "/"))
            karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
            px = oiio.ImageBuf(exr).get_pixels(oiio.FLOAT)[:, :, :3]
            lum = px @ np.array([0.2126, 0.7152, 0.0722])
            band = lum[ROWS[0]:ROWS[1]]
            bg = float(np.median(band[:, FAR_COL:]))
            colmean = band.mean(axis=0)
            path = colmean > 3 * bg
            cols = np.nonzero(path)[0]
            energy = float(np.clip(band - bg, 0, None)[:, path].sum() / band.size)
            spark = float((band[:, path] > 20 * bg).mean()) if path.any() else 0.0
            info = {"rough": rough, "amp": amp, "bg": round(bg, 4), "width_px": int(path.sum()),
                    "span": [int(cols.min()), int(cols.max())] if len(cols) else None,
                    "energy": round(energy, 4), "spark": round(spark, 4), "peak": round(float(band.max()), 1)}
            rows.append(info)
            print(info, flush=True)
            # 見る用の PNG（明るさを 0〜1 に切って、ガンマ 2.2）
            view = np.clip(px, 0, 1) ** (1 / 2.2)
            ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
            ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
            ob.write(os.path.join(OUT, name + ".png"))
            os.remove(exr)
    water.parm("rough").set(0.04)
    ripples.parm("ampscale").set(1.6)
    hou_tools.save_hip(os.path.join(OUT, "218_scene.hipnc"))
    hou_tools.write_graph("/obj/ocean_winter", os.path.join(OUT, "218_graph.json"), title="実験218")
    sop_bench.save(218, rows, {"res": RES, "band_rows": ROWS, "far_col": FAR_COL, "frame": FRAME})


if __name__ == "__main__":
    main()
