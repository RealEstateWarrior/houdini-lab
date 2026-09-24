# -*- coding: utf-8 -*-
"""実験224 — Vellum の布が伸びて見えるのは、計算の回数（Substeps・Constraint Iterations）が足りないせいか。

制作の問い: テーブルクロスやカーテンが、ゴムのように伸びて垂れて見えることがある。vellumsolver の Substeps と
Constraint Iterations（既定 100）をいくつにすれば伸びなくなるのか。時間はどれだけ延びるのか。布の目を細かくすると伸びやすいのか。

  実験206 と同じ机とテーブルクロス（1.9 × 1.45 m、66×84、Cloth の既定の硬さ）を 72 フレーム落とす。
    substeps 1・2・5（実験206 の値）・10（Constraint Iterations 100）
    Constraint Iterations 25・50・200・400（Substeps 5）
    布の目を 2 倍（132×168）にして Substeps 5・Constraint Iterations 100 と 400
  測るもの（72 フレーム目）:
    伸び … 布の四角形の辺の長さを、落とす前の grid の同じ辺と比べた割合。平均と、いちばん伸びた 1%（99 パーセンタイル）と最大
    角のいちばん低い点の高さ（伸びるほど低く垂れる）
    72 フレームを計算する時間（1 通りずつ、ほかの処理は回さない）

    hython examples/224_vellum_cloth_stretch.py
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
CASES = [("sub1", 66, 84, 1, 100), ("sub2", 66, 84, 2, 100), ("sub5", 66, 84, 5, 100), ("sub10", 66, 84, 10, 100),
         ("it25", 66, 84, 5, 25), ("it50", 66, 84, 5, 50), ("it200", 66, 84, 5, 200), ("it400", 66, 84, 5, 400),
         ("fine_it100", 132, 168, 5, 100), ("fine_it400", 132, 168, 5, 400)]


def edges(geo):
    out = []
    for prim in geo.prims():
        vs = [v.point().number() for v in prim.vertices()]
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            out.append((min(a, b), max(a, b)))
    return sorted(set(out))


def main():
    import hou
    import numpy as np
    import hou_tools
    import sop_bench
    spec = importlib.util.spec_from_file_location("e206", os.path.join(HERE, "examples", "206_vellum_cloth_preview_res.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    hou.setFps(24)
    geo = sop_bench.fresh()
    table = m.build_table(geo)
    rows = []
    for name, r, c, sub, it in CASES:
        vs, vc = m.build_cloth(geo, table, r, c)
        vs.setName(f"drop_{name}")
        vc.setName(f"cloth_setup_{name}")
        vs.parm("substeps").set(sub)
        vs.parm("niter").set(it)
        rest = vc.inputs()[0].geometry()
        e = np.array(edges(rest))
        P0 = np.array(rest.pointFloatAttribValues("P")).reshape(-1, 3)
        L0 = np.linalg.norm(P0[e[:, 0]] - P0[e[:, 1]], axis=1)
        t0 = time.perf_counter()
        for f in range(1, m.LAST + 1):
            hou.setFrame(f)
            g = vs.geometry()
        sec = time.perf_counter() - t0
        P = np.array(g.pointFloatAttribValues("P")).reshape(-1, 3)
        L = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1)
        s = (L / L0 - 1) * 100
        info = {"case": name, "grid": [r, c], "substeps": sub, "niter": it, "sec": round(sec, 2),
                "stretch_mean": round(float(s.mean()), 3), "stretch_p99": round(float(np.percentile(s, 99)), 3),
                "stretch_max": round(float(s.max()), 3), "lowest": round(float(P[:, 1].min()), 4)}
        rows.append(info)
        print(info, flush=True)
        # 画: 72 フレーム目
        hou_tools.render_preview(vs.path(), os.path.join(OUT, f"224_{name}.png"), res=(480, 300), direction=(1.0, 0.45, 0.9),
                                 shading="smooth", frame_bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))
        vs.bypass(False)
    geo.layoutChildren()
    hou.setFrame(m.LAST)
    hou_tools.save_hip(os.path.join(OUT, "224_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "224_graph.json"), title="実験224")
    sop_bench.save(224, rows, {"last": m.LAST})


if __name__ == "__main__":
    main()
