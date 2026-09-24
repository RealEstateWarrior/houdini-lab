# -*- coding: utf-8 -*-
"""実験208 — FLIP の水の粒を面にする（particlefluidsurface）とき、どの設定が見た目と時間に効くか。

制作の問い: FLIP を回したあと、粒を水の面にする。既定のままだと粒のつぶつぶが残る・しぶきが消える・水が増える、
といった見た目の問題が出る。Voxel Scale・Method・Filtering（ならし）のどれを触ると、何がどれだけ変わるのか。重くなるのはどれか。

  実験200 と同じダムブレイク（幅 0.6 × 高さ 0.9 × 奥行き 1 の水が崩れる。Particle Separation 0.02）を 60 フレーム回し、
  フレーム 36（右の壁にぶつかって跳ね上がる所）と 60 で、particlefluidsurface::3.0 を次の 8 通りにして面にする。
    default   … 既定（Method = Average Position、Voxel Scale 0.75、Influence Scale 3、Filtering なし）
    vox050 / vox150 … Voxel Scale 0.5 / 1.5
    infl2 / infl5   … Influence Scale 2 / 5
    spherical … Method = Spherical
    filter    … Dilate・Smooth・Erode を入れる（既定の値のまま）
    neural    … Method = Neural Point Surface（Neural Model = Balanced）
  測るもの: 面にかかる時間（4 回作り、1 回目を除いたいちばん短い回。1 回目は読み込みが混ざる）、面の数、体積（最初の水 0.54 m³ と比べる）、表面積（でこぼこが多いほど大きい）。
  フレーム 36 の形を、同じカメラのビューポートで撮って並べる。

    hython examples/208_flip_surface_settings.py
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
SEP = 0.02
FRAMES = 60
CHECK = [36, 60]
VARIANTS = {
    "default": {},
    "vox050": {"voxelsize": 0.5},
    "vox150": {"voxelsize": 1.5},
    "infl2": {"influenceradius": 2.0},
    "infl5": {"influenceradius": 5.0},
    "spherical": {"surfmethod": 1},
    "filter": {"dodilate": 1, "dosmooth": 1, "doerode": 1},
    "neural": {"surfmethod": 2, "model": 0},
}


def area_volume(geo_node):
    import hou
    parent = geo_node.parent()
    m = parent.createNode("measure::2.0", "bench_area")
    m.setInput(0, geo_node)
    m.parm("measure").set("area")
    tot = parent.createNode("attribpromote", "bench_sum")
    tot.setInput(0, m)
    tot.parm("inname").set("area")
    tot.parm("inclass").set("primitive")
    tot.parm("outclass").set("detail")
    tot.parm("method").set("sum")
    a = tot.geometry().attribValue("area")
    for n in (tot, m):
        n.destroy()
    return a


def main():
    import hou
    import hou_tools
    import sop_bench
    spec = importlib.util.spec_from_file_location("e200", os.path.join(HERE, "examples", "200_flip_dambreak_res.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    geo, solver, surf = m.build(SEP, tall=True)
    t0 = time.perf_counter()
    counts = {}
    for f in range(1, FRAMES + 1):
        hou.setFrame(f)
        g = solver.geometry(0)
        if f in CHECK:
            counts[f] = len(g.points())
    sim = time.perf_counter() - t0
    base = {p.name(): p.eval() for p in surf.parms() if p.name() in ("voxelsize", "influenceradius", "surfmethod", "model", "dodilate", "dosmooth", "doerode")}
    rows = []
    for name, parms in VARIANTS.items():
        for k, v in base.items():
            surf.parm(k).set(v)
        for k, v in parms.items():
            surf.parm(k).set(v)
        rec = {"case": name, "parms": parms}
        for f in CHECK:
            secs = []
            for rep in range(4):
                # つまみをわずかに動かすだけでは作り直さなかった（0.01 秒台になった）。
                # 1 つ前のフレームを作ってから目的のフレームに戻すと、粒は覚えたまま、面だけ作り直す
                hou.setFrame(f - 1)
                surf.geometry()
                hou.setFrame(f)
                t = time.perf_counter()
                sg = surf.geometry()
                secs.append(time.perf_counter() - t)
            # 1 回目は読み込み（Neural のモデルなど）が混ざるので、2 回目以降のいちばん短い回を使い、全部も残す
            secs_first, secs = secs[0], secs[1:]
            rec[f"f{f}"] = {"sec": round(min(secs), 3), "secs": [round(x, 3) for x in secs], "first": round(secs_first, 3), "polys": len(sg.prims()), "points": len(sg.points()),
                            "volume": round(sop_bench.volume(sg), 5), "area": round(area_volume(surf), 4),
                            "particles": counts[f]}
            if f == 36:
                surf.setDisplayFlag(True)
                hou_tools.render_preview(surf.path(), os.path.join(OUT, f"208_{name}.png"), res=(560, 360),
                                         direction=(-0.35, 0.35, 1.0), shading="smooth",
                                         frame_bbox=hou.BoundingBox(0.2, -0.75, -0.5, 1.5, 0.75, 0.5), margin=1.02)
        rows.append(rec)
        print(name, rec["f36"], flush=True)
    for k, v in base.items():
        surf.parm(k).set(v)
    hou.setFrame(36)
    geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "208_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "208_graph.json"), title="実験208")
    sop_bench.save(208, rows, {"sep": SEP, "sim_sec": round(sim, 2), "water_volume": m.WATER_VOL, "base": base})


if __name__ == "__main__":
    main()
