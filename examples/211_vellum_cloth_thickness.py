# -*- coding: utf-8 -*-
"""実験211 — テーブルクロスが机から浮いて見えるのは、布の厚み（Thickness）のせいか。いくつにすればよいか。

制作の問い: 実験206 で、天板（上面の高さ 0.76 m）の上に乗った布の高さは平均 0.770 m だった。1 cm 浮いている。
vellumsolver の Default Thickness の既定 0.01 と同じ値。厚みを変えると浮きは消えるか。薄くしすぎると机にめり込まないか。垂れ方は変わるか。

  実験206 と同じ机と布（66×84 に分割、辺の長さ約 2.3 cm）を 72 フレーム落とす。
    t020 / t010（既定）/ t005 / t0025 … vellumsolver の Default Thickness（vellumconstraints の Thickness は既定の Unchanged のまま）
    calc                              … vellumconstraints の Thickness を Calculate Uniform（辺の長さ × Edge Length Scale 0.25）
  測るもの: 布の点に入った pscale（半径として使われる厚み）、天板の上の点の高さ（平均・最小）と天板からの浮き、
            天板より下にめり込んだ点の数、いちばん低い点の高さ、72 フレームの形を t0025 と比べた距離。
  （計算時間は、点検（実験210）と同時に回したので比べない）

    hython examples/211_vellum_cloth_thickness.py
"""
import importlib.util
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
TOP = 0.76          # 天板の上面（box の中心 0.74 + 厚み 0.04 / 2）
ROWS, COLS = 66, 84
CASES = {"t020": 0.02, "t010": 0.01, "t005": 0.005, "t0025": 0.0025, "calc": None}


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
    for name, th in CASES.items():
        vs, vc = m.build_cloth(geo, table, ROWS, COLS)
        vs.setName(f"drop_{name}")
        vc.setName(f"cloth_setup_{name}")
        if th is None:
            vc.parm("dothickness").set(2)       # Calculate Uniform
        else:
            vs.parm("thickness").set(th)
        built[name] = vs
    rows, finals = [], {}
    for name, vs in built.items():
        for f in range(1, m.LAST + 1):
            hou.setFrame(f)
            vs.geometry()
        g = vs.geometry()
        pts = [p.position() for p in g.points()]
        ps = g.findPointAttrib("pscale")
        pscale = statistics.fmean(g.pointFloatAttribValues("pscale")) if ps else None
        on_top = [p[1] for p in pts if abs(p[0]) < 0.55 and abs(p[2]) < 0.35]
        info = {"case": name, "thickness": CASES[name], "pscale": round(pscale, 5) if pscale else None,
                "top_mean": round(statistics.fmean(on_top), 5), "top_min": round(min(on_top), 5),
                "gap_mm": round((statistics.fmean(on_top) - TOP) * 1000, 2),
                "below_top": sum(1 for y in on_top if y < TOP), "on_top_points": len(on_top),
                "lowest": round(min(p[1] for p in pts), 4), "hem": m.hem(g)["hem"]}
        stash = geo.createNode("stash", f"final_{name}")
        stash.setInput(0, vs)
        stash.parm("stashinput").pressButton()
        stash.setInput(0, None)
        finals[name] = stash
        rows.append(info)
        print(info, flush=True)
    for info in rows:
        if info["case"] != "t0025":
            info["to_t0025"] = sop_bench.spread(finals["t0025"].geometry(), finals[info["case"]].geometry())
    # 撮る: 天板の縁を横から近くで見る（浮きが見える向き）
    show = geo.createNode("merge", "show")
    show.setInput(0, table)
    for name in CASES:
        show.setInput(1, finals[name])
        hou_tools.render_preview(show.path(), os.path.join(OUT, f"211_{name}.png"), res=(560, 320),
                                 direction=(0.0, 0.08, 1.0), shading="smoothwire",
                                 frame_bbox=hou.BoundingBox(0.2, 0.66, 0.2, 0.75, 0.82, 0.45), margin=1.0)
        hou_tools.render_preview(show.path(), os.path.join(OUT, f"211_{name}_wide.png"), res=(560, 360),
                                 direction=(1.0, 0.7, 1.25), shading="smooth",
                                 frame_bbox=hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8))
    show.setInput(1, finals["t005"])
    geo.layoutChildren()
    hou.setFrame(m.LAST)
    hou_tools.save_hip(os.path.join(OUT, "211_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "211_graph.json"), title="実験211")
    sop_bench.save(211, rows, {"grid_rows": ROWS, "grid_cols": COLS, "top": TOP, "last": m.LAST})


if __name__ == "__main__":
    main()
