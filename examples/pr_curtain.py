# -*- coding: utf-8 -*-
"""実践「カーテンを風になびかせる」— 布を1枚吊るし、窓から風を当てて、逆光の窓辺として撮る。

    hython examples/pr_curtain.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

FRAME = 48


def run(solver, last):
    import hou
    t0 = time.perf_counter()
    for f in range(1, last + 1):
        hou.setFrame(f)
        solver.geometry()
    return time.perf_counter() - t0


def main():
    import hou
    g = kit.Guide("curtain", "カーテンを風になびかせる",
                  "布（Vellum の cloth）を1枚、上の端だけ留めて吊るし、窓の外から風を当てる。"
                  "ひだを最初に付けておくと、風を受けたときにカーテンらしくふくらむ。ノードは布の3つ（形・性質・計算）が中心。",
                  tags=["シミュレーション", "Vellum", "布", "Karma", "制作"])
    g.shot_dir = (1.0, 0.35, 1.3)
    panel = g.node("grid", "fabric", orient="xy", size=(0.85, 2.2), t=(-0.43, 1.15, 0), rows=56, cols=24)
    cloth = g.node("copyxform", "two_panels", [panel], ncy=2, tx=0.86)
    g.step(cloth, "布の板を立てる",
           "<code>grid</code> の Orientation を <strong>XY Plane</strong>（縦に立てる）、大きさ 0.85 × 2.2、"
           "<strong>Rows 56・Columns 24</strong> にする。升目が細かいほど布はなめらかに曲がるが、計算は重くなる。"
           "<code>copyxform</code> で右へ 0.86 ずらした2枚目を作り、左右1組のカーテンにする。",
           cap="縦に立てた2枚の板。", shading="smoothwire")
    pleat = g.node("attribwrangle", "pleats_and_top", [cloth],
                   snippet="// ひだを付ける（横方向に波打たせる）\n"
                           "@P.z += sin(@P.x * 38) * 0.03;\n"
                           "// 上の端の点を「top」というグループにする（ここを留める）\n"
                           "i@group_top = @P.y > 2.24;")
    g.step(pleat, "ひだを付け、留める所を決める",
           "<code>attribwrangle</code> で、横方向に <code>sin</code> の波を付けてひだにする。"
           "もう1行で、いちばん上の列の点を <strong>top</strong> というグループにまとめる。あとでここを留める。",
           cap="波打ったひだ。上の列が top。", shading="smoothwire", ui_parm="snippet")
    vc = g.node("vellumconstraints", "cloth_setup", [pleat], constrainttype="cloth", pingroup="top")
    g.step(vc, "布の性質を付けて、上を留める",
           "<code>vellumconstraints</code> の Constraint Type を <strong>Cloth</strong> にし、"
           "<strong>Pin Points に top</strong> と書く。これで上の列は動かず、ほかの点は布として引っぱり合う。"
           "出口は2つあり、左が布、右が「つながり（拘束）」。",
           cap="見た目は同じ。点どうしのつながりが付いた。", shading="smoothwire", ui_parm="pingroup")
    solver = g.node("vellumsolver", "wind_sim", [vc], substeps=5, dowind=1, windx=0.15, windy=0.0, windz=1.0,
                    windspeed=1.8, winddrag=0.3, useground=1)
    solver.setInput(1, vc, 1)
    sim_sec = run(solver, FRAME)
    g.step(solver, "風を当てて計算する",
           "<code>vellumsolver</code> の左に布、<strong>真ん中に vellumconstraints の右の出口</strong>をつなぐ。"
           "<strong>Built-in Wind</strong> を入れて向きを (0.15, 0, 1)（窓から部屋の中へ）、Built-in Wind Speed 1.8、Built-in Wind Drag 0.3。"
           f"Substeps は 5 にする（布が伸びすぎない）。再生すると布がふくらむ。フレーム {FRAME}（2 秒）で止めて撮る。",
           cap=f"フレーム {FRAME}。上が留まったまま、下がふくらむ。", shading="smoothwire", ui_parm="dowind")
    rod = g.node("tube", "rod", type="poly", orient="x", rad=(0.018, 0.018), height=1.9, cols=16, cap=1, t=(0, 2.28, 0))
    wall = g.node("grid", "wall", orient="xy", size=(7, 4.5), t=(0, 1.6, -0.45), rows=2, cols=2)
    sky = g.node("grid", "window_light", orient="xy", size=(1.5, 2.1), t=(0, 1.2, -0.44), rows=2, cols=2)
    bar_v = g.node("box", "bar_v", size=(0.05, 2.1, 0.05), t=(0, 1.2, -0.42))
    bar_h = g.node("box", "bar_h", size=(1.5, 0.05, 0.05), t=(0, 1.45, -0.42))
    frame_parts = g.node("merge", "window_frame", [bar_v, bar_h])
    sheer = g.mat("sheer_mat", basecolor=(0.95, 0.92, 0.86), rough=0.6, transparency=0.45, ior=1.0, sheen=0.5)
    metal = g.mat("rod_mat", basecolor=(0.6, 0.5, 0.35), metallic=1.0, rough=0.3)
    plaster = g.mat("wall_mat", basecolor=(0.72, 0.68, 0.62), rough=0.9)
    light = g.mat("sky_mat", basecolor=(0, 0, 0), emitcolor=(1.0, 0.93, 0.8), emitint=1.4)
    parts = [g.assign(solver, sheer, "assign_sheer"), g.assign(rod, metal, "assign_rod"),
             g.assign(wall, plaster, "assign_wall"), g.assign(sky, light, "assign_sky"),
             g.assign(frame_parts, plaster, "assign_frame")]
    final = g.node("merge", "window_scene", parts)
    g.step(final, "窓辺を組んで、材質を当てる",
           "後ろに壁（<code>grid</code>）と、窓の形の光る板（Emission Intensity 1.4）、窓の桟（細い <code>box</code> 2本）を置き、"
           "上にカーテンレール（細い <code>tube</code>）を渡す。カーテンの材質は <strong>Transparency 0.45・IOR 1</strong>"
           "（光を通すが曲げない＝薄い布）、Sheen 0.5。窓の光を強くしすぎると、布を通した光まで白く飛んで布が消えるので、1.4 程度に抑える。",
           cap="材質を当てた状態（ビューポートでは透けない）。", shot=False)
    g.hero(final, f"Karma で撮った仕上がり（フレーム{FRAME}）。明かりは窓の光と弱いキー。", direction=(0.85, 0.18, 1.1),
           key=1.2, rim=0.0, dome=0.15, spp=96, margin=1.0, frame=FRAME, floor=True,
           bbox=hou.BoundingBox(-1.1, 0, -0.45, 1.1, 2.35, 0.8))

    # ---- 落とし穴を測る ----
    geo = solver.geometry()
    top_y = geo.boundingBox().maxvec()[1]
    reach = geo.boundingBox().maxvec()[2]
    vc.parm("pingroup").set("")
    run(solver, FRAME)
    nopin_top = solver.geometry().boundingBox().maxvec()[1]
    vc.parm("pingroup").set("top")
    solver.parm("dowind").set(0)
    run(solver, FRAME)
    still_reach = solver.geometry().boundingBox().maxvec()[2]
    hi_len = 2.25 - solver.geometry().boundingBox().minvec()[1]   # 風なし・Substeps 5 で吊るした長さ
    solver.parm("substeps").set(1)
    run(solver, FRAME)
    low_len = 2.25 - solver.geometry().boundingBox().minvec()[1]
    solver.parm("substeps").set(5)
    solver.parm("dowind").set(1)
    run(solver, FRAME)
    traps = [
        {"title": "上を留めないと、布はそのまま落ちる",
         "body": f"Pin Points を空にすると、{FRAME} フレームで布のいちばん高い所が {top_y:.2f} m から {nopin_top:.2f} m まで下がった。"
                 "Vellum の布は、留めた点がなければ全部が重力で落ちる。吊るす物は、まず留める所をグループにする。",
         "img": "", "cap": ""},
        {"title": "風は Built-in Wind を入れないと吹かない",
         "body": f"Built-in Wind を切ると、布のいちばん手前は z = {still_reach:.2f} m（ひだの厚みだけ）。入れると {reach:.2f} m までふくらんだ。"
                 "Built-in Wind Speed だけ上げても、Built-in Wind のチェックが切れていれば何も起きない。",
         "img": "", "cap": ""},
        {"title": "Substeps 1 だと布が伸びる",
         "body": f"風を切って吊るすだけにすると、長さ 2.2 m の布が Substeps 5 では {hi_len:.3f} m、Substeps 1 では {low_len:.3f} m になった。"
                 "1回の計算で動く量が大きいと、つながりを保ちきれず、布が自分の重さで伸びる。布は Substeps を上げて固さを保つ。",
         "img": "", "cap": ""},
        {"title": "布の計算時間",
         "body": f"点 {len(geo.points()):,} 個の布を Substeps 5 で {FRAME} フレーム回すのに {sim_sec:.1f} 秒。"
                 "升目を倍にすると点は4倍になる。動きを決めるまでは粗い布で回す。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "5個（布の部分）"], [f"{FRAME} フレームの計算", f"{sim_sec:.1f}秒"]], traps=traps)


if __name__ == "__main__":
    main()
