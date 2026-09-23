# -*- coding: utf-8 -*-
"""実践「ネオン管の看板を作る」— 文字の輪郭に沿って細い管を通し、光る材質で撮る。

    hython examples/pr_neon.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    import hou
    g = kit.Guide("neon", "ネオン管の看板を作る",
                  "文字の輪郭を1本の線として取り出し、その線に沿って細い管を通す。光る材質を当てるだけで、"
                  "夜の看板になる。形は2ノード、光は材質1つ。",
                  tags=["モデリング", "レンダリング", "Karma", "材質", "看板"])
    g.shot_dir = (0.0, 0.1, 1.0)
    text = g.node("font", "letters", type="poly", text="NEON", fontsize=1.0, hole=0)
    g.step(text, "文字を置く",
           "<code>font</code> に文字を打ち、Type を <strong>Polygons Only</strong>、<strong>Hole Faces を切る</strong>。"
           "入れたままだと O の内側と外側が1本の線でつながり、管にその線が出る。"
           "文字は面（塗りつぶした形）として出てくるが、ほしいのはその輪郭の線。",
           cap="「NEON」の4文字。", shading="smoothwire")
    tube = g.node("sweep::2.0", "tube", [text], surfaceshape="tube", radius=0.018, cols=12, endcaptype="single")
    g.step(tube, "線に沿って管を通す",
           "<code>sweep</code> の Surface Shape を <strong>Round Tube</strong>、Radius を 0.018 にする。"
           "文字の面をそのままつなぐと、面の縁（輪郭）に沿って細い筒ができる。曲がったところには font がもともと細かく点を置いているので、並べ直しは要らない。<strong>Columns</strong> は筒の周りの分割数で、12 あれば丸く見える。",
           cap="輪郭がそのまま細い管になる。", ui_parm="radius")
    tb = text.geometry().boundingBox()
    cx, cy = tb.center()[0], tb.center()[1]
    back = g.node("box", "back_plate", size=(tb.sizevec()[0] + 0.5, tb.sizevec()[1] + 0.45, 0.04), t=(cx, cy, -0.08))
    g.step(back, "取り付ける板を置く",
           "管の後ろに <code>box</code> で薄い板を置く（文字より上下左右に少し大きく、厚み 0.04）。光が板に広がるので、看板らしく見える。",
           cap="文字の後ろの黒い板。")
    neon = g.mat("neon_mat", basecolor=(0.9, 0.3, 0.6), emitcolor=(1.0, 0.18, 0.55), emitint=9.0, rough=0.2)
    plate = g.mat("plate_mat", basecolor=(0.03, 0.03, 0.035), rough=0.35, reflect=0.5)
    a1 = g.assign(tube, neon, "assign_neon")
    a2 = g.assign(back, plate, "assign_plate")
    final = g.node("merge", "sign", [a1, a2])
    g.step(final, "光る材質を当てる",
           "<code>principledshader</code> を2つ作る。管には <strong>Emission Color をピンク、Emission Intensity を 9</strong>。"
           "板は Base Color をほぼ黒、Reflectivity 0.5 にして、光が映り込むようにする。<code>material</code> で割り当て、<code>merge</code> でまとめる。",
           cap="材質を当てた状態（ビューポートでは光らない）。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。明かりは管の発光がほとんど。", direction=(0.25, 0.12, 1.0),
           key=0.25, rim=0.4, dome=0.04, margin=1.12, spp=64)

    # ---- 落とし穴を測る ----
    cols_rows = {}
    for c in (4, 12, 32):
        tube.parm("cols").set(c)
        cols_rows[c] = tube.geometry().intrinsicValue("primitivecount")
    tube.parm("cols").set(12)
    print(cols_rows)
    traps = [
        {"title": "Hole Faces を入れたままだと、O に余計な線が出る",
         "body": "font の Hole Faces（既定で入）は、O や A の穴を外側の輪郭と1本の線でつないで1つの面にする。"
                 "その面の縁に管を通すと、つないだ線にも管ができ、O の上に縦の線が1本見えた。切ると外側と内側が別々の輪郭になり、線は消える。",
         "img": "", "cap": ""},
        {"title": "Columns を増やしても、見た目はほとんど変わらない",
         "body": f"管の周りの分割（Columns）を 4・12・32 にすると、面の数は {cols_rows[4]:,}・{cols_rows[12]:,}・{cols_rows[32]:,}。"
                 "管が細いので、12 を超えると画ではほぼ見分けられない。重くしたくなければ 8〜12。",
         "img": "", "cap": ""},
        {"title": "ビューポートでは光らない",
         "body": "発光はレンダラー（Karma）が計算するもので、ビューポートでは色が付くだけ。光り具合は Karma で撮って確かめる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "6個（形は2個）"], ["管の面の数", f"{cols_rows[12]:,}"]], traps=traps)


if __name__ == "__main__":
    main()
