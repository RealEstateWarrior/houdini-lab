# -*- coding: utf-8 -*-
"""実験227 — 地形を削る（heightfield_erode）フレーム数を増やすと、見た目と時間はどう変わるか。どこで止めればよいか。

制作の問い: 山の地形に川筋や崖を刻みたい。heightfield_erode は、フレームを進めながら少しずつ削り、Freeze at Frame（既定 5）で止まる。
何フレームまで削れば「削った地形」らしくなるのか。時間はどれだけかかるのか。

  heightfield（1000 m 四方、Grid Spacing 2 → 500 × 500）に heightfield_noise（Amplitude 500 は既定、Element Size 300）で山を作り、heightfield_erode（::3.0）で削る。
  Freeze at Frame を 5（既定）・20・50・100 にする（Iterations per Frame は 1 のまま）。
  測るもの: 削る時間（Freeze のフレームで作り直す時間。1 通りずつ、ほかの処理は回さない）、
            高さの標準偏差、斜面の傾きの平均（度）、細かい凸凹（となりの升との高さの差の、ならした形との違い）、
            削る前との高さの差（平均と最大）。
  画は、高さから描いた陰影図（北西から光を当てた地図。reports_227.py が描く）。

    hython examples/227_heightfield_erode_frames.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
FRAMES = (5, 20, 50, 100)


def heights(node):
    import numpy as np
    g = node.geometry()
    vol = [p for p in g.prims() if p.attribValue("name") == "height"][0]
    rx, ry, _ = vol.resolution()
    return np.array(vol.allVoxels()).reshape(ry, rx)


def stats(h, h0, spacing):
    import numpy as np
    gy, gx = np.gradient(h, spacing)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    # 細かい凸凹: 3 升でならした形との差の標準偏差
    k = (h[:-2, :-2] + h[1:-1, :-2] + h[2:, :-2] + h[:-2, 1:-1] + h[1:-1, 1:-1] + h[2:, 1:-1] + h[:-2, 2:] + h[1:-1, 2:] + h[2:, 2:]) / 9
    rough = float(np.std(h[1:-1, 1:-1] - k))
    d = h - h0
    return {"h_std": round(float(h.std()), 3), "slope_mean": round(float(slope.mean()), 3), "rough": round(rough, 4),
            "diff_mean": round(float(np.abs(d).mean()), 3), "diff_max": round(float(np.abs(d).max()), 3)}


def main():
    import hou
    import hou_tools
    import sop_bench
    geo = sop_bench.fresh()
    hf = geo.createNode("heightfield", "ground")
    hf.parm("gridspacing").set(2)
    noise = geo.createNode("heightfield_noise", "mountains")
    noise.setFirstInput(hf)
    noise.parm("elementsize").set(300)
    erode = geo.createNode("heightfield_erode::3.0", "erode")
    erode.setFirstInput(noise)
    h0 = heights(noise)
    import numpy as np
    np.save(os.path.join(OUT, "227_h_before.npy"), h0)
    base = stats(h0, h0, 2)
    base.update({"case": "before", "freeze": 0, "sec": 0.0})
    rows = [base]
    print(base, flush=True)
    hou_tools.render_preview(noise.path(), os.path.join(OUT, "227_before.png"), res=(640, 400), direction=(0.6, 0.7, 1.0), shading="smooth")
    for f in FRAMES:
        erode.parm("freezeframe").set(f)
        hou.setFrame(f)
        t0 = time.perf_counter()
        erode.cook(force=True)
        sec = time.perf_counter() - t0
        h = heights(erode)
        np.save(os.path.join(OUT, f"227_h_freeze{f}.npy"), h)
        info = stats(h, h0, 2)
        info.update({"case": f"freeze{f}", "freeze": f, "sec": round(sec, 2)})
        rows.append(info)
        print(info, flush=True)
        hou_tools.render_preview(erode.path(), os.path.join(OUT, f"227_freeze{f}.png"), res=(640, 400), direction=(0.6, 0.7, 1.0), shading="smooth")
    erode.parm("freezeframe").set(20)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "227_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "227_graph.json"), title="実験227")
    sop_bench.save(227, rows, {"spacing": 2})


if __name__ == "__main__":
    main()
