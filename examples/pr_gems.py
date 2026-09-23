# -*- coding: utf-8 -*-
"""実践「宝石を散らす」— 角ばった宝石を1つ作り、色と大きさを変えて散らし、ガラスの材質で撮る。

    hython examples/pr_gems.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402


def main():
    g = kit.Guide("gems", "宝石を散らす",
                  "分割の少ない球を平らな面に分けるだけで、宝石のカットになる。色と大きさを1つずつ変えて散らし、"
                  "光を通す材質を当てれば、光が中で屈折してきらめく。",
                  tags=["モデリング", "複製", "レンダリング", "Karma", "材質", "ガラス"])
    g.shot_dir = (0.8, 0.9, 1.0)
    gem = g.node("sphere", "cut", type="polymesh", rows=5, cols=10, rad=(0.5, 0.36, 0.5))
    g.step(gem, "分割の少ない球を置く",
           "<code>sphere</code> の Primitive Type を Polygon Mesh にし、<strong>Rows 5・Columns 10</strong> と少なくする。"
           "縦を 0.36 に縮めると、上下がとがった宝石の形になる。",
           cap="縦5・周り10の、角ばった球。", shading="smoothwire", ui_parm="rows")
    flat = g.node("facet", "flat_faces", [gem], unique=1, postnml=1)
    g.step(flat, "面を平らに見せる",
           "<code>facet</code> で <strong>Unique Points</strong> と <strong>Post-Compute Normals</strong> を入れる。"
           "面ごとに点を分けて向きを付け直すので、なめらかな球ではなく、平らなカット面として光を返す。",
           cap="面の1枚1枚がはっきりする。", shading="flat", ui_parm="unique")
    ground = g.node("grid", "spread_area", size=(3.2, 2.0), rows=2, cols=2)
    pts = g.node("scatter::2.0", "places", [ground], npts=7, seed=11, relaxpoints=1, relaxiterations=40)
    rnd = g.node("attribwrangle", "vary", [pts],
                 snippet="// 大きさ・向き・色を1つずつ変える\n"
                         "f@pscale = fit01(rand(@ptnum + 3), 0.35, 0.8);\n"
                         "vector axis = normalize(set(rand(@ptnum + 7) - 0.5, 1.0, rand(@ptnum + 9) - 0.5));\n"
                         "p@orient = quaternion(rand(@ptnum + 5) * 6.28, axis);\n"
                         "vector palette[] = array({0.9, 0.08, 0.15}, {0.1, 0.35, 0.95}, {0.1, 0.8, 0.35},\n"
                         "                         {0.95, 0.75, 0.1}, {0.6, 0.15, 0.9});\n"
                         "v@Cd = palette[@ptnum % 5];\n"
                         "@P.y += f@pscale * 0.36;")
    g.step(rnd, "置く場所を決め、1つずつ変える",
           "<code>grid</code> の上に <code>scatter</code> で7点ばらまき（Relax を入れると重なりにくい）、"
           "<code>attribwrangle</code> で点ごとに大きさ（pscale）・向き（orient）・色（Cd）を決める。"
           "色は5色の表から順に選ぶ。最後の行で、宝石が床に埋まらないよう少し持ち上げる。",
           cap="7つの点。色の付いた点が置き場所。", shading="smoothwire", ui_parm="snippet")
    copies = g.node("copytopoints::2.0", "place_gems", [flat, rnd], targetattribs=1)
    copies.parm("applyto1").set("prims")
    copies.parm("applyattribs1").set("Cd")
    g.step(copies, "宝石を点に並べる",
           "<code>copytopoints</code> の左に宝石、右に点をつなぐ。点の pscale・orient で、大きさと向きの違う7つになる。"
           "<strong>色は、Target Attributes に1行足して「Apply to: Primitives」「Attributes: Cd」と書かないと移らない</strong>"
           "（既定では何も移さない）。",
           cap="色も大きさも違う7つの宝石。", shading="flat", ui_parm="targetattribs")
    glass = g.mat("gem_mat", basecolor=(1, 1, 1), rough=0.0, reflect=1.0, ior=2.2, transparency=1.0,
                  transcolor=(1, 1, 1), transcolor_usePointColor=1, transdist=1.0, dispersion=0.4)
    final = g.assign(copies, glass, "assign_gem")
    g.step(final, "光を通す材質を当てる",
           "<code>principledshader</code> で <strong>Transparency 1</strong>（光を通す）、<strong>IOR 2.2</strong>（曲がり方。ダイヤは約2.4、ガラスは1.5）、"
           "Roughness 0 にする。<strong>Transmission Color の Use Point Color</strong> を入れると、面に移した色（Cd）が宝石の色になる。"
           "<strong>Dispersion 0.4</strong> で、光が虹色に分かれる。材質は1つで7色すべてに使える。",
           cap="材質を当てた状態（ビューポートでは透けない）。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。宝石の中で光が曲がり、床に色が落ちる。", direction=(0.6, 0.55, 1.0),
           key=7.0, rim=12.0, dome=0.2, spp=128, margin=1.0, backdrop=(0.09, 0.09, 0.1))

    # ---- 落とし穴を測る: facet の有無で面の数と点の数がどう変わるか ----
    import hou
    n_smooth = gem.geometry().intrinsicValue("pointcount")
    n_facet = flat.geometry().intrinsicValue("pointcount")
    traps = [
        {"title": "facet を省くと、カット面にならない",
         "body": f"球のままだと点は {n_smooth} 個で、となりの面と点を共有しているので、Karma は面の境目をなめらかにつないで描く。"
                 f"facet で Unique Points を入れると点は {n_facet} 個に増え、面ごとに向きが切れる。これが宝石のきらめきの元。",
         "img": "", "cap": ""},
        {"title": "copytopoints は、既定では色を移さない",
         "body": "Target Attributes を空のまま複製すると、できた宝石に残る属性は P と N だけで、Cd が無かった。"
                 "そのまま撮ると、7つとも無色のガラスになる。移したい属性は自分で書き足す。",
         "img": "", "cap": ""},
        {"title": "透ける材質は撮るのが重い",
         "body": f"この絵は Karma 1280×720・128 サンプルで {g.hero_sec:.0f} 秒。サンプルを下げると、宝石の中がざらつく。"
                 "まず小さい解像度で色と形を決めてから、最後に大きく撮る。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "7個"], ["宝石1つの面", f"{gem.geometry().intrinsicValue('primitivecount')}枚"]], traps=traps)


if __name__ == "__main__":
    main()
