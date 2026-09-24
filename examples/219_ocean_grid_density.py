# -*- coding: utf-8 -*-
"""実験219 — 海の板の点の数は、どこまで減らしてよいか。撮る時間と見た目はどう変わるか。

制作の問い: 実践「冬の朝の七里ヶ浜」の映像は、1 枚 11.8 秒（960×540・16 サンプル）かかった。板は 1400 × 1600（224 万点）。
点を減らせば速くなるのか。どこから見た目が崩れるのか。

  pr_ocean_winter.hipnc の板（grid sea）の Rows・Columns を、1400×1600・990×1131（1/2 の点）・700×800（1/4）・
  350×400（1/16）にし、フレーム 30 を映像と同じ設定（960×540・16 サンプル）で撮る。1 通りずつ、ほかの処理は回さない。
  測るもの:
    計算の時間 … 板から泡までを作り直す時間（breaking_waves を強制で作り直す）
    撮る時間 … Karma の render にかかった時間（形を Karma に渡す時間も含む）
    見た目の差 … 1400×1600 の画との、画素ごとの差の平均（0〜255）。画を 3 つに分けて測る:
      空（上 40%）・沖（水平線から 40 m 先まで）・手前（40 m より手前、泡と砂）

    hython examples/219_ocean_grid_density.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (960, 540)
FRAME = 30
CASES = [("full", 1400, 1600), ("half", 990, 1131), ("quarter", 700, 800), ("sixteenth", 350, 400)]


def main():
    import hou
    import numpy as np
    from PIL import Image
    import hou_tools
    import sop_bench
    hou.hipFile.load(os.path.join(OUT, "pr_ocean_winter.hipnc"), suppress_save_prompt=True)
    hou.setFrame(FRAME)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 16), ("varianceaa_maxsamples", 16)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    grid = hou.node("/obj/ocean_winter/sea")
    surf = hou.node("/obj/ocean_winter/breaking_waves")
    rows, imgs = [], {}
    for name, r, c in CASES:
        grid.parm("rows").set(r)
        grid.parm("cols").set(c)
        t0 = time.perf_counter()
        surf.cook(force=True)
        cook = time.perf_counter() - t0
        pts = len(surf.geometry().points())
        png = os.path.join(OUT, f"219_{name}.png")
        karma.parm("picture").set(png.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(FRAME, FRAME, 1), verbose=False)
        sec = time.perf_counter() - t0
        imgs[name] = np.asarray(Image.open(png).convert("RGB"), dtype=float)
        rows.append({"case": name, "rows": r, "cols": c, "points": pts, "cook_sec": round(cook, 2), "render_sec": round(sec, 1)})
        print(rows[-1], flush=True)
    # 見た目の差（1400×1600 の画と）。水平線は縦 0.574（行 310）付近、40 m 先は行 340 付近
    ref = imgs["full"]
    h = ref.shape[0]
    zones = {"sky": (0, int(h * 0.40)), "far_sea": (int(h * 0.57), int(h * 0.63)), "near": (int(h * 0.63), h)}
    for row in rows:
        im = imgs[row["case"]]
        row["diff"] = {k: round(float(np.abs(im[a:b] - ref[a:b]).mean()), 2) for k, (a, b) in zones.items()}
    grid.parm("rows").set(1400)
    grid.parm("cols").set(1600)
    hou_tools.save_hip(os.path.join(OUT, "219_scene.hipnc"))
    hou_tools.write_graph("/obj/ocean_winter", os.path.join(OUT, "219_graph.json"), title="実験219")
    sop_bench.save(219, rows, {"res": RES, "frame": FRAME, "zones": zones})
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
