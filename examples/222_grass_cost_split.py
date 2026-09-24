# -*- coding: utf-8 -*-
"""実験222 — 草を何万本も並べると Karma が急に遅くなるのは、どの段階のせいか（実験215 の続き）。

制作の問い: 実験215 で、パックした草は 1 万本 17 秒なのに 10 万本は 13 分かかった。ポイントインスタンサーにしても、
地面を広げても変わらなかった。時間がかかっているのは、光の計算（画の大きさ・サンプル数に比例するはず）か、
場面を Karma に渡す段階（画の大きさによらない）か。草ごとの色（Cd）は関係するか。

  実験215 の場面（out/215_scene.hipnc）を読み、草の本数を 1 万本と 3 万本にして、次を撮る:
    big       … 640×360・8 サンプル＋ノイズ除去（実験215 と同じ）
    tiny      … 64×36・1 サンプル、ノイズ除去なし（光の計算をほぼ無くす。残りは渡す時間）
    big_nocd  … 640×360・8 サンプル、草ごとの色（Cd）を消す
  並べ方は、パックしたまま（switch 0）と、ポイントインスタンサー（switch 2）。
  はじめに小さく 1 枚撮って捨てる（Karma の立ち上がり）。1 通りずつ、ほかの重い処理は回さない。

    hython examples/222_grass_cost_split.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
CASES = [(n, mode, look) for n in (10000, 30000) for mode in (0, 2) for look in ("big", "tiny", "big_nocd")]


def main():
    import hou
    import hou_tools
    import sop_bench
    hou.hipFile.load(os.path.join(OUT, "215_scene.hipnc"), suppress_save_prompt=True)
    geo = hou.node("/obj/exp215")
    pts = geo.node("spots")
    pick = geo.node("packed_or_flat")
    grass = geo.node("assign_grass")
    # 色を消す枝: switch の後ろに attribdelete を挟み、入り切りを bypass で決める
    nocd = geo.createNode("attribdelete", "drop_color")
    nocd.setFirstInput(pick)
    nocd.parm("ptdel").set("Cd")
    grass.setFirstInput(nocd)
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())

    def setup(res, spp, dn):
        for n, v in (("resolutionx", res[0]), ("resolutiony", res[1]), ("samplesperpixel", spp), ("varianceaa_maxsamples", spp)):
            karma.parm(n).set(v)
        cam.parm("resx").set(res[0])
        cam.parm("resy").set(res[1])
        karma.parm("denoiser").set("oidn" if dn else "off")

    setup((64, 36), 1, False)
    karma.parm("picture").set(os.path.join(OUT, "_222_warm.png").replace("\\", "/"))
    pts.parm("npts").set(1000)
    karma.render(frame_range=(1, 1, 1), verbose=False)
    rows = []
    for n, mode, look in CASES:
        pts.parm("npts").set(n)
        pick.parm("input").set(mode)
        nocd.bypass(look != "big_nocd")
        if look == "tiny":
            setup((64, 36), 1, False)
        else:
            setup((640, 360), 8, True)
        pick.geometry()
        tag = f"{look}_{'inst' if mode == 2 else 'packed'}_{n // 1000}k"
        karma.parm("picture").set(os.path.join(OUT, f"222_{tag}.png").replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        sec = time.perf_counter() - t0
        rows.append({"case": tag, "count": n, "mode": mode, "look": look, "sec": round(sec, 2)})
        print(rows[-1], flush=True)
    nocd.bypass(True)
    pts.parm("npts").set(10000)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "222_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "222_graph.json"), title="実験222")
    sop_bench.save(222, rows, {"cases": len(rows)})


if __name__ == "__main__":
    main()
