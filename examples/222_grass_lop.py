# -*- coding: utf-8 -*-
"""実験222 の後半 — 同じ草を Solaris（LOP）の sopimport で読み、並べ方を選んで Karma で撮る。

前半（222_grass_cost_split.py）で、/obj の Karma で撮ると時間の 9 割近くが「場面を Karma に渡す」段階だと分かった。
LOP の sopimport は、パックした形の渡し方（Packed Primitives）を選べる:
  Create Point Instancer（pointinstancer）… 形 1 つ＋置く点の並び
  Create Native Instances（nativeinstances、既定）… 1 本ずつ、中身を共有する物として
  Create Xforms（xforms）… 1 本ずつ別の物として
カメラとライトは sceneimport で /obj から読む。karmarendersettings で 8 サンプル・ノイズ除去（OIDN）にそろえ、
usdrender ROP で 640×360 に撮る。はじめに小さく 1 枚撮って捨てる。

    hython examples/222_grass_lop.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
CASES = [("pointinstancer", 10000), ("pointinstancer", 30000), ("pointinstancer", 100000), ("pointinstancer", 1000000),
         ("nativeinstances", 30000), ("xforms", 30000)]


def main():
    import hou
    hou.hipFile.load(os.path.join(OUT, "222_scene.hipnc"), suppress_save_prompt=True)
    pts = hou.node("/obj/exp215/spots")
    hou.node("/obj/exp215/packed_or_flat").parm("input").set(0)
    st = hou.node("/stage")
    si = st.createNode("sceneimport::2.0", "camera_and_lights")
    si.parm("objects").set("/obj/hero_cam /obj/hero_key /obj/hero_rim /obj/hero_dome")
    sp = st.createNode("sopimport", "grass")
    sp.parm("soppath").set("/obj/exp215/field")
    sp.parm("enable_packedhandling").set(1)
    sp.setInput(0, si)
    ks = st.createNode("karmarendersettings", "settings")
    ks.setInput(0, sp)
    for name, value in (("samplesperpixel", 8),):   # 解像度は usdrender 側で 640×360 に上書きする
        if ks.parm(name) is not None:
            ks.parm(name).set(value)
    st.layoutChildren()
    rop = hou.node("/out").createNode("usdrender", "lop_karma")
    rop.parm("loppath").set(ks.path())
    rop.parm("renderer").set("BRAY_HdKarma")
    rop.parm("override_camera").set("/hero_cam")
    rop.parm("override_res").set("specific")
    rop.parmTuple("res_user").set((640, 360))
    settings = {p.name(): p.eval() for p in ks.parms() if p.name() in ("samplesperpixel", "resolutionx", "resolutiony")}
    # 温め
    sp.parm("packedhandling").set("pointinstancer")
    pts.parm("npts").set(1000)
    rop.parm("outputimage").set(os.path.join(OUT, "_222_lop_warm.png").replace("\\", "/"))
    rop.render(verbose=False)
    rows = []
    for mode, n in CASES:
        sp.parm("packedhandling").set(mode)
        pts.parm("npts").set(n)
        hou.node("/obj/exp215/field").geometry()
        tag = f"lop_{mode}_{n // 1000}k"
        rop.parm("outputimage").set(os.path.join(OUT, f"222_{tag}.png").replace("\\", "/"))
        t0 = time.perf_counter()
        rop.render(verbose=False)
        rows.append({"case": tag, "count": n, "packed": mode, "sec": round(time.perf_counter() - t0, 2)})
        print(rows[-1], flush=True)
    pts.parm("npts").set(10000)
    sp.parm("packedhandling").set("pointinstancer")
    hou.hipFile.save(os.path.join(OUT, "222_scene.hipnc"))
    with open(os.path.join(OUT, "222_lop.json"), "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "settings": settings}, fp, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
