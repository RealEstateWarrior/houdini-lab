# -*- coding: utf-8 -*-
"""実験226 — ガラスを細かく割るほど、計算はどれだけ重くなるか。破片の縁のでこぼこは時間に効くか。

制作の問い: 窓ガラスを割る場面で、破片をもっと細かくしたい。rbdmaterialfracture（Glass）の Radial Crack Number（放射状のひびの数、既定 20）を
上げると、破片の数と、割る計算・Bullet の計算の時間はどう増えるか。Enable Edge Noise（破片の縁のでこぼこ、既定で入り）を切ると速くなるか。

  実践「窓ガラスを割る」と同じ場面（1 × 1.4 m・厚さ 8 mm の板に、半径 6 cm の球を秒速 14 m で当てる。枠に触れる破片は止める。
  破片どうしのつながりの強さ 0.8）を 48 フレーム回す。
    Radial Crack Number 8・20（既定）・40・80（Edge Noise 入り）と、20・80 で Edge Noise 切り
    ひびを増やすと割れにくくなったので、80 本でつながりの強さを 0.6・0.5・0.4・0.2・0.1 に下げたものも回す
  測るもの: 破片の数と面の数、割る計算の時間（rbdmaterialfracture を作り直す時間）、Bullet の 48 フレームの時間、
            48 フレーム目で 5 cm 以上動いた破片の数。1 通りずつ、ほかの処理は回さない。

    hython examples/226_rbd_glass_pieces.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
LAST = 48
HIT = (0.12, 0.9, 0.0)
CASES = [("r8", 8, 1, 0.8), ("r20", 20, 1, 0.8), ("r40", 40, 1, 0.8), ("r80", 80, 1, 0.8), ("r20_smooth", 20, 0, 0.8), ("r80_smooth", 80, 0, 0.8),
         # ひびを増やすと割れにくくなった。つながりの強さを下げて、20 本のときと同じくらい割れるかを見る
         ("r80_g06", 80, 1, 0.6), ("r80_g05", 80, 1, 0.5), ("r80_g04", 80, 1, 0.4), ("r80_g02", 80, 1, 0.2), ("r80_g01", 80, 1, 0.1)]


def main():
    import hou
    import hou_tools
    import sop_bench
    hou.setFps(24)
    geo = sop_bench.fresh()
    pane = geo.createNode("box", "pane")
    pane.parmTuple("size").set((1.0, 1.4, 0.008))
    pane.parmTuple("t").set((0, 0.75, 0))
    hit = geo.createNode("add", "hit_point")
    hit.parm("points").set(1)
    hit.parm("usept0").set(1)
    hit.parmTuple("pt0").set(HIT)
    frac = geo.createNode("rbdmaterialfracture", "crack")
    frac.setInput(0, pane)
    frac.setInput(3, hit)
    frac.parm("materialtype").set("glass")
    frac.parm("glass_useinput").set(1)
    ball = geo.createNode("sphere", "ball")
    ball.parm("type").set("polymesh")
    ball.parmTuple("rad").set((0.06, 0.06, 0.06))
    ball.parmTuple("t").set((HIT[0], HIT[1], 0.7))
    throw = geo.createNode("attribwrangle", "throw")
    throw.setFirstInput(ball)
    throw.parm("snippet").set("s@name = 'ball';\nv@v = {0, 0, -14};")
    both = geo.createNode("merge", "glass_and_ball")
    both.setInput(0, frac)
    both.setInput(1, throw)
    pack = geo.createNode("pack", "one_per_piece")
    pack.setFirstInput(both)
    pack.parm("packbyname").set(1)
    pack.parm("transfer_attributes").set("name v")
    held = geo.createNode("attribwrangle", "hold_edges")
    held.setFirstInput(pack)
    held.parm("snippet").set(
        "float b[] = primintrinsic(0, 'bounds', @ptnum);\n"
        "int on_frame = b[0] < -0.47 || b[1] > 0.47 || b[2] < 0.08 || b[3] > 1.42;\n"
        "string piece = prim(0, 'name', @ptnum);\n"
        "i@active = piece == 'ball' ? 1 : !on_frame;")
    glue = geo.createNode("attribwrangle", "weak_glue")
    glue.setInput(0, frac, 1)
    glue.parm("class").set(1)
    glue.parm("snippet").set("f@strength = 0.8;")
    solver = geo.createNode("rbdbulletsolver", "shatter")
    solver.setInput(0, held)
    solver.setInput(1, glue)
    solver.parm("useground").set(1)
    solver.parm("startframe").set(1)
    rows = []
    only = os.environ.get("ONLY")          # 実験246 から、条件を 1 つだけ回すのに使う
    for name, cracks, noise, strength in [c for c in CASES if not only or c[0] == only]:
        glue.parm("snippet").set(f"f@strength = {strength};")
        frac.parm("glass_radialcracknum").set(cracks)
        frac.parm("glass_enableedgenoise").set(noise)
        hou.setFrame(1)
        t0 = time.perf_counter()
        fg = frac.geometry()
        frac_sec = time.perf_counter() - t0
        names = set(fg.primStringAttribValues("name"))
        polys = len(fg.prims())
        held.geometry()
        start = {p.attribValue("name"): p.vertices()[0].point().position() for p in held.geometry().prims()}
        t0 = time.perf_counter()
        for f in range(1, LAST + 1):
            hou.setFrame(f)
            g = solver.geometry()
        sim_sec = time.perf_counter() - t0
        end = {p.attribValue("name"): p.vertices()[0].point().position() for p in g.prims()}
        moved = sum(1 for k in start if k != "ball" and k in end and (end[k] - start[k]).length() > 0.05)
        info = {"case": name, "radial_cracks": cracks, "edge_noise": noise, "glue": strength, "pieces": len(names), "polys": polys,
                "fracture_sec": round(frac_sec, 2), "sim_sec": round(sim_sec, 2), "moved": moved}
        rows.append(info)
        print(info, flush=True)
        if not only and name in ("r8", "r20", "r80", "r80_smooth", "r80_g06", "r80_g05", "r80_g04", "r80_g01"):
            hou_tools.render_preview(solver.path(), os.path.join(OUT, f"226_{name}.png"), res=(480, 480), direction=(0.35, 0.2, 1.0),
                                     shading="smoothwire", frame_bbox=hou.BoundingBox(-0.6, 0, -0.3, 0.6, 1.5, 0.3))
        solver.parm("resimulate").pressButton() if solver.parm("resimulate") else None
    if only:
        return
    frac.parm("glass_radialcracknum").set(20)
    frac.parm("glass_enableedgenoise").set(1)
    geo.layoutChildren()
    hou.setFrame(LAST)
    hou_tools.save_hip(os.path.join(OUT, "226_scene.hipnc"))
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "226_graph.json"), title="実験226")
    sop_bench.save(226, rows, {"last": LAST})


if __name__ == "__main__":
    main()
