# -*- coding: utf-8 -*-
"""実験248 — MaterialX のガラスなら、Karma XPU でもグラスの場面が CPU と同じ絵になるか。

制作の問い: 実験232 で、氷の入ったグラスの水を XPU で撮ると、背景の幕が白く飛んで全体が明るくなった。この場面には点の色 Cd が無いので、
実験243（Cd があると principledshader の色が置き換わる）とは別の原因。材質を MaterialX（mtlxstandard_surface）に替えると揃うのか。

  実践「氷の入ったグラスの水」（out/pr_glasscup.hipnc）を、材質だけ替えて CPU と XPU で撮る（640×360・32 サンプル・ノイズ除去なし、条件ごとに別の hython）。
    principled … 実践のまま（principledshader）
    mtlx       … /mat の材質 5 つ（幕・ガラス・水・氷・氷の芯）を、同じ色と IOR の mtlxstandard_surface に替える
                 （透明なものは transmission 1、specular_IOR に IOR、specular_roughness に Roughness。幕は base_color と specular_roughness）
  測るもの: 画の明るさの平均（右下の透かしは除く）と、CPU の画との差（画素ごとの差の平均 0〜255）、撮る時間。

    hython examples/248_karma_xpu_mtlx_glass.py principled cpu
    python examples/248_karma_xpu_mtlx_glass.py combine
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (640, 360)


def to_mtlx():
    """/mat の principledshader を、同じ名前の場所に mtlxstandard_surface を作って差し替える（割り当ての先を書き換える）。"""
    import hou
    mat = hou.node("/mat")
    swap = {}
    for m in list(mat.children()):
        if not m.type().name().startswith("principledshader"):
            continue
        x = mat.createNode("mtlxstandard_surface", m.name() + "_mtlx")
        x.parmTuple("base_color").set(m.parmTuple("basecolor").eval())
        x.parm("specular_roughness").set(m.parm("rough").eval())
        x.parm("specular_IOR").set(m.parm("ior").eval())
        tr = m.parm("transparency").eval() if m.parm("transparency") else 0
        x.parm("transmission").set(tr)
        swap[m.path()] = x.path()
    for node in hou.node("/obj").allSubChildren():
        if node.type().name() == "material":
            for i in range(1, node.parm("num_materials").eval() + 1):
                p = node.parm(f"shop_materialpath{i}")
                if p is not None and p.eval() in swap:
                    p.set(swap[p.eval()])
    return swap


def run(kind, engine):
    import hou
    import numpy as np
    from PIL import Image
    hou.hipFile.load(os.path.join(OUT, "pr_glasscup.hipnc"), suppress_save_prompt=True)
    swapped = to_mtlx() if kind == "mtlx" else {}
    karma = hou.node("/out/hero_karma")
    cam = hou.node(karma.parm("camera").eval())
    for n, v in (("resolutionx", RES[0]), ("resolutiony", RES[1]), ("samplesperpixel", 32), ("varianceaa_maxsamples", 32)):
        karma.parm(n).set(v)
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    karma.parm("denoiser").set("off")
    karma.parm("engine").set(engine)
    karma.parm("picture").set(os.path.join(OUT, "_248_warm.png").replace("\\", "/"))
    karma.render(frame_range=(1, 1, 1), verbose=False)
    png = os.path.join(OUT, f"248_{kind}_{engine}.png")
    karma.parm("picture").set(png.replace("\\", "/"))
    t0 = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    sec = time.perf_counter() - t0
    a = np.asarray(Image.open(png).convert("RGB"), dtype=float)
    keep = np.ones(a.shape[:2], bool)
    keep[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False
    row = {"case": f"{kind}_{engine}", "kind": kind, "engine": engine, "sec": round(sec, 2), "mean": round(float(a[keep].mean()), 2),
           "swapped": len(swapped)}
    print(row, flush=True)
    with open(os.path.join(OUT, f"248_part_{kind}_{engine}.json"), "w", encoding="utf-8") as fp:
        json.dump(row, fp)
    if kind == "mtlx" and engine == "xpu":
        import hou_tools
        hou_tools.save_hip(os.path.join(OUT, "248_scene.hipnc"))


def combine():
    import numpy as np
    from PIL import Image
    import sop_bench
    rows = []
    for kind in ("principled", "mtlx"):
        ref = np.asarray(Image.open(os.path.join(OUT, f"248_{kind}_cpu.png")).convert("RGB"), dtype=float)
        keep = np.ones(ref.shape[:2], bool)
        keep[int(RES[1] * 0.85):, int(RES[0] * 0.7):] = False
        for engine in ("cpu", "xpu"):
            with open(os.path.join(OUT, f"248_part_{kind}_{engine}.json"), encoding="utf-8") as fp:
                r = json.load(fp)
            img = np.asarray(Image.open(os.path.join(OUT, f"248_{kind}_{engine}.png")).convert("RGB"), dtype=float)
            r["diff_to_cpu"] = round(float(np.abs(img - ref)[keep].mean()), 2)
            rows.append(r)
            print(r)
    sop_bench.save(248, rows, {"res": RES, "spp": 32})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run(sys.argv[1], sys.argv[2])
