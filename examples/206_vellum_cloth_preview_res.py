# -*- coding: utf-8 -*-
"""実験206 — テーブルクロスを粗い布で試してから細かくすると、落ち方は同じになるか。どこまで粗くしてよいか。

制作の問い: 実践「テーブルクロスを掛ける」では「粗いうちに落ち方を決めて、最後に細かくする」と書いた。
でも、粗い布で決めた落ち方（垂れる長さ・ひだの位置）は、細かい布でも同じになるのか。どこまで粗くしても形が崩れないのか。

  実践と同じ机（天板 1.2 × 0.04 × 0.8 m、高さ 0.74 m、脚 4 本）と布（1.9 × 1.45 m を天板の 12 cm 上に置き、4° 回す）を、
  布の分割だけ変えて vellumsolver（Substeps 5、地面あり）で 72 フレーム（3 秒）落とす。
    Rows × Columns = 22×28・44×56・66×84・110×140（実践の値）・165×210
  測るもの:
    - 72 フレームの計算時間
    - いちばん細かい布（165×210）との形の違い: 細かい布の各点から、粗い布の面までの距離の平均と最大
    - 垂れの長さ: 布のいちばん低い点の高さ、四辺の真ん中の裾の高さ
    - 天板の上に乗った部分の平らさ: 天板の範囲にある点の高さのばらつき（標準偏差）
  できた形は、同じ向きのビューポートで撮って並べる。

    hython examples/206_vellum_cloth_preview_res.py
"""
import json
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
LAST = 72
RES = [(22, 28), (44, 56), (66, 84), (110, 140), (165, 210)]


def build_table(geo):
    top = geo.createNode("box", "table_top")
    top.parmTuple("size").set((1.2, 0.04, 0.8))
    top.parmTuple("t").set((0, 0.74, 0))
    m = geo.createNode("merge", "table")
    m.setInput(0, top)
    for i, (x, z) in enumerate([(-0.54, -0.34), (0.54, -0.34), (-0.54, 0.34), (0.54, 0.34)]):
        leg = geo.createNode("box", f"leg{i}")
        leg.parmTuple("size").set((0.05, 0.72, 0.05))
        leg.parmTuple("t").set((x, 0.36, z))
        m.setInput(i + 1, leg)
    return m


def build_cloth(geo, table, rows, cols):
    cloth = geo.createNode("grid", f"cloth_{rows}")
    cloth.parmTuple("size").set((1.9, 1.45))
    cloth.parm("rows").set(rows)
    cloth.parm("cols").set(cols)
    cloth.parmTuple("t").set((0, 0.86, 0))
    cloth.parmTuple("r").set((0, 4, 0))
    vc = geo.createNode("vellumconstraints", f"cloth_setup_{rows}")
    vc.setInput(0, cloth)
    vc.parm("constrainttype").set("cloth")
    vs = geo.createNode("vellumsolver", f"drop_{rows}")
    vs.setInput(0, vc, 0)
    vs.setInput(1, vc, 1)
    vs.setInput(2, table)
    vs.parm("substeps").set(5)
    vs.parm("useground").set(1)
    return vs, vc


def hem(geo):
    """布の縁の点のうち、四辺の真ん中あたり（机の中心から見た向きで ±10°）の最も低い高さ。"""
    pts = [p.position() for p in geo.points()]
    lowest = min(p[1] for p in pts)
    out = {}
    for name, ang in (("+x", 0), ("+z", 90), ("-x", 180), ("-z", 270)):
        ys = [p[1] for p in pts
              if abs(((math.degrees(math.atan2(p[2], p[0])) - ang + 180) % 360) - 180) < 10
              and math.hypot(p[0], p[2]) > 0.3]
        out[name] = round(min(ys), 4) if ys else None
    on_top = [p[1] for p in pts if abs(p[0]) < 0.55 and abs(p[2]) < 0.35]
    return {"lowest": round(lowest, 4), "hem": out,
            "top_std_mm": round(statistics.pstdev(on_top) * 1000, 3) if len(on_top) > 1 else None,
            "top_mean": round(statistics.fmean(on_top), 4) if on_top else None}


def main():
    import hou
    import hou_tools
    import sop_bench
    hou.setFps(24)
    hou.playbar.setFrameRange(1, LAST)
    geo = sop_bench.fresh()
    table = build_table(geo)
    solvers = [(r, c, *build_cloth(geo, table, r, c)) for r, c in RES]
    # 温め（1 回目は起動の分だけ遅い）
    hou.setFrame(1)
    solvers[0][2].geometry()
    rows = []
    finals = {}
    for r, c, vs, vc in solvers:
        t0 = time.perf_counter()
        for f in range(1, LAST + 1):
            hou.setFrame(f)
            vs.geometry()
        sec = time.perf_counter() - t0
        g = vs.geometry()
        info = {"rows": r, "cols": c, "points": len(g.points()), "sec": round(sec, 2),
                "thickness": vc.parm("thickness").eval() if vc.parm("thickness") else None, **hem(g)}
        # 72 フレームの形を stash に写して固める（あとで距離を測る・撮るため）
        stash = geo.createNode("stash", f"final_{r}")
        stash.setInput(0, vs)
        stash.parm("stashinput").pressButton()
        stash.setInput(0, None)
        finals[r] = stash
        rows.append(info)
        print(info, flush=True)
    ref = finals[RES[-1][0]]
    for info in rows:
        if info["rows"] == RES[-1][0]:
            continue
        d = sop_bench.spread(ref.geometry(), finals[info["rows"]].geometry())
        info["to_finest"] = d
        print(info["rows"], d, flush=True)
    # 撮る（全部作り終えてから）
    box = hou.BoundingBox(-1.0, 0, -0.8, 1.0, 0.9, 0.8)
    show = geo.createNode("merge", "show")
    show.setInput(0, table)
    for r, c in RES:
        show.setInput(1, finals[r])
        hou_tools.render_preview(show.path(), os.path.join(OUT, f"206_r{r}.png"), res=(640, 400),
                                 direction=(1.0, 0.7, 1.25), shading="smoothwire" if r <= 66 else "smooth", frame_bbox=box)
    show.setInput(1, finals[110])
    geo.layoutChildren()
    hou.setFrame(LAST)
    hou_tools.save_hip(os.path.join(OUT, "206_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "206_graph.json"), title="実験206")
    sop_bench.save(206, rows, {"last": LAST})


if __name__ == "__main__":
    main()
