# -*- coding: utf-8 -*-
"""実験217 — テーブルクロスの曲げの硬さ（Bend Stiffness）を変えると、ひだと垂れ方はどう変わるか。

制作の問い: 薄い布（シルク）と厚い布（帆布）を見せ分けたい。vellumconstraints の Cloth の曲げの硬さ（Bend の Stiffness、
既定 1 × 10⁻¹ = 0.1）をいくつにすると、ひだの細かさ・垂れ方がどう変わるのか。

  実験206・211 と同じ机と布（66×84）を 72 フレーム落とす。曲げの硬さだけを 0.001・0.1（既定）・1・3・10・1000 にする
  （Stiffness と、× の指数 bendstiffnessexp で）。
  測るもの:
    - 布のいちばん低い点（角の垂れ）と、四辺の真ん中の裾の高さ
    - 机の +x 側（脚の間、|z| < 0.3）に垂れた面の「出入り」: 天板より下（y < 0.7）の点の x のばらつき（標準偏差）。
      まっすぐ垂れると小さく、ひだが多い・深いと大きい
    - 既定（10⁻¹）の形との距離（平均と最大）
  （計算時間は、点検（実験210）と同時に回したので比べない）

    hython examples/217_vellum_cloth_bend.py
"""
import importlib.util
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
ROWS, COLS = 66, 84
# 値 = (Stiffness, 指数)。0.1 と 10 の間（1・3）はあとから足した
CASES = {"b-3": (1, -3), "b-1": (1, -1), "b0": (1, 0), "b0s3": (3, 0), "b1": (1, 1), "b3": (1, 3)}


def main():
    import hou
    import hou_tools
    import sop_bench
    spec = importlib.util.spec_from_file_location("e206", os.path.join(HERE, "examples", "206_vellum_cloth_preview_res.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    hou.setFps(24)
    geo = sop_bench.fresh()
    table = m.build_table(geo)
    built = {}
    for name, e in CASES.items():
        vs, vc = m.build_cloth(geo, table, ROWS, COLS)
        vs.setName(f"drop_{name.replace('-', 'm')}")
        vc.setName(f"cloth_setup_{name.replace('-', 'm')}")
        vc.parm("bendstiffness").set(e[0])
        vc.parm("bendstiffnessexp").set(e[1])
        built[name] = vs
    rows, finals = [], {}
    for name, vs in built.items():
        for f in range(1, m.LAST + 1):
            hou.setFrame(f)
            vs.geometry()
        g = vs.geometry()
        pts = [p.position() for p in g.points()]
        side = [p[0] for p in pts if p[0] > 0.55 and abs(p[2]) < 0.3 and p[1] < 0.7]
        info = {"case": name, "bend": CASES[name][0] * 10.0 ** CASES[name][1], "lowest": round(min(p[1] for p in pts), 4),
                "hem": m.hem(g)["hem"], "side_points": len(side),
                "side_x_std_mm": round(statistics.pstdev(side) * 1000, 2) if len(side) > 1 else None,
                "side_x_mean": round(statistics.fmean(side), 4) if side else None}
        stash = geo.createNode("stash", f"final_{name.replace('-', 'm')}")
        stash.setInput(0, vs)
        stash.parm("stashinput").pressButton()
        stash.setInput(0, None)
        finals[name] = stash
        rows.append(info)
        print(info, flush=True)
    for info in rows:
        if info["case"] != "b-1":
            info["to_default"] = sop_bench.spread(finals["b-1"].geometry(), finals[info["case"]].geometry())
    show = geo.createNode("merge", "show")
    show.setInput(0, table)
    for name in CASES:
        show.setInput(1, finals[name])
        hou_tools.render_preview(show.path(), os.path.join(OUT, f"217_{name.replace('-', 'm')}.png"), res=(560, 360),
                                 direction=(1.0, 0.45, 0.9), shading="smooth",
                                 frame_bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))
    show.setInput(1, finals["b-1"])
    geo.layoutChildren()
    hou.setFrame(m.LAST)
    hou_tools.save_hip(os.path.join(OUT, "217_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "217_graph.json"), title="実験217")
    sop_bench.save(217, rows, {"grid_rows": ROWS, "grid_cols": COLS, "last": m.LAST})


if __name__ == "__main__":
    main()
