# -*- coding: utf-8 -*-
"""実践「石灯籠に雪を積もらせる」— 上を向いた面にだけ雪の粒をまき、屋根の下を除いてから、粒をつないで雪の塊にする。

    hython examples/pr_snow.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

VOX = 0.006


def main():
    import hou
    g = kit.Guide("snow", "石灯籠に雪を積もらせる",
                  "雪は上から降るので、積もるのは「上を向いていて、上に何もない面」だけ。その面に粒をまき、"
                  "粒をまとめて1つの塊（VDB）にすると、角の丸い、ぽってりした雪になる。形を選ばず、どんなモデルにも使える。",
                  tags=["モデリング", "VDB", "雪", "Karma", "制作"])
    g.shot_dir = (0.9, 0.55, 1.2)
    parts = [
        g.node("box", "base", size=(0.8, 0.12, 0.8), t=(0, 0.06, 0)),
        g.node("tube", "pillar", type="poly", rad=(0.08, 0.08), height=0.48, cols=24, cap=1, t=(0, 0.36, 0)),
        g.node("box", "shelf", size=(0.44, 0.08, 0.44), t=(0, 0.64, 0)),
        g.node("box", "light_box", size=(0.26, 0.24, 0.26), t=(0, 0.8, 0)),
        g.node("tube", "roof", type="poly", rad=(0.03, 0.44), height=0.2, cols=4, cap=1, t=(0, 1.02, 0), r=(0, 45, 0)),
        g.node("sphere", "top_ball", type="polymesh", rad=(0.05, 0.05, 0.05), t=(0, 1.16, 0)),
    ]
    stone = g.node("merge", "lantern", [p for i, p in enumerate(parts) if i != 3])
    lamp = parts[3]
    whole = g.node("merge", "lantern_all", [stone, lamp])
    g.step(whole, "石灯籠を組む",
           "<code>box</code>・<code>tube</code>・<code>sphere</code> を積んで灯籠にする。屋根は <code>tube</code> の "
           "<strong>Columns を 4</strong>、上の半径を小さく（0.03）すると四角すいになる。45 度回して箱と向きをそろえる。"
           "火袋（明かりの箱）だけは、あとで光る材質を当てるので別にしておく。",
           cap="台・竿・中台・火袋・屋根・宝珠。", shading="smoothwire")
    up = g.node("attribwrangle", "keep_up_faces", [whole], **{"class": 1},
                snippet="// 上を向いていない面を消す（N.y が 0.5 より小さい = 60度より急な面）\n"
                        "vector n = prim_normal(0, @primnum, 0.5, 0.5);\n"
                        "if (n.y < 0.5) removeprim(0, @primnum, 1);")
    g.step(up, "上を向いた面だけ残す",
           "<code>attribwrangle</code> の Run Over を <strong>Primitives</strong> にして、面の向き（<code>prim_normal</code>）の上向きの成分 "
           "<strong>y が 0.5 より小さい面を消す</strong>。壁や下向きの面が消え、屋根や台の上だけが残る。",
           cap="上向きの面だけが残る。", shading="smoothwire", ui_parm="snippet")
    flakes = g.node("scatter::2.0", "flakes", [up], npts=40000, seed=3)
    g.step(flakes, "雪の粒をまく",
           "<code>scatter</code> で、残った面に <strong>4 万個</strong>の点をまく。1つの点が1粒の雪になる。",
           cap="上向きの面にまいた点。", shading="smoothwire", ui_parm="npts")
    cover = g.node("attribwrangle", "under_roof", [flakes, whole],
                   snippet="// 真上に何かあれば（屋根の下など）、雪は届かないので消す\n"
                           "vector hit; float u, v;\n"
                           "if (intersect(1, @P + {0, 0.002, 0}, {0, 5, 0}, hit, u, v) >= 0) removepoint(0, @ptnum);\n"
                           "// 粒の大きさ（雪の厚み）を少しずつ変える\n"
                           "f@pscale = 0.028 * fit01(rand(@ptnum), 0.7, 1.2);")
    g.step(cover, "屋根の下の粒を消す",
           "<code>attribwrangle</code> の2つ目の入力に灯籠全体をつなぎ、各点から<strong>真上へ光線を飛ばす</strong>"
           "（<code>intersect</code>）。何かに当たれば、その点は屋根の下なので消す。残った点には粒の大きさ <code>pscale</code>（約 2.8 cm）を付ける。",
           cap="中台と火袋の上の点が消えた。", shading="smoothwire", ui_parm="snippet")
    blob = g.node("vdbfromparticles", "clump", [cover], voxelsize=VOX)
    smooth = g.node("vdbsmoothsdf", "soften", [blob], iterations=6)
    snow = g.node("convertvdb", "snow_mesh", [smooth], conversion="poly")
    t0 = time.perf_counter()
    n_snow = snow.geometry().intrinsicValue("primitivecount")
    snow_sec = time.perf_counter() - t0
    g.step(snow, "粒をつないで雪の塊にする",
           f"<code>vdbfromparticles</code> で粒を1つの形（VDB）にまとめる。<strong>Voxel Size は {VOX}</strong>（粒の半径の 1/5 くらい）。"
           "<code>vdbsmoothsdf</code> で角を丸め（Iterations 6）、<code>convertvdb</code> の Convert To を <strong>Polygons</strong> にして面に戻す。",
           cap="ぽってり積もった雪。", shading="smooth", ui_parm="voxelsize")
    ground = g.node("grid", "ground", size=(10, 10), rows=160, cols=160, t=(0, 0.035, 0))
    bumps = g.node("mountain::2.0", "drifts", [ground], height=0.03, elementsize=0.4)
    rock = g.mat("stone_mat", basecolor=(0.3, 0.29, 0.27), rough=0.9)
    glow = g.mat("paper_mat", basecolor=(0.9, 0.7, 0.45), emitcolor=(1.0, 0.55, 0.2), emitint=2.0)
    white = g.mat("snow_mat", basecolor=(0.9, 0.93, 0.97), rough=0.55, sss=0.6, ssscolor=(0.75, 0.88, 1.0), sssdist=0.03)
    final = g.node("merge", "snowy_lantern", [g.assign(stone, rock, "assign_stone"), g.assign(lamp, glow, "assign_paper"),
                                              g.assign(snow, white, "assign_snow"), g.assign(bumps, white, "assign_ground")])
    g.step(final, "雪の地面を敷き、材質を当てる",
           "<code>grid</code> を少し持ち上げ（起伏で床の下にもぐらないように）、<code>mountain</code> で起伏を付けて雪の地面にする。雪の材質は白く、<strong>Subsurface 0.6</strong>"
           "（光が少し中に入る）で青みを足す。火袋には Emission Intensity 2 の暖かい光（強くすると白く飛ぶ）。石は暗い灰色。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。青い夜の光と、火袋の暖かい光。", direction=(0.85, 0.35, 1.2),
           key=1.2, key_color=(0.7, 0.8, 1.0), rim=3.0, rim_color=(0.6, 0.72, 1.0), dome=0.3, dome_color=(0.45, 0.55, 0.9),
           spp=96, margin=1.1, backdrop=(0.35, 0.4, 0.52), bbox=hou.BoundingBox(-0.4, 0, -0.4, 0.4, 1.25, 0.4))

    # ---- 落とし穴を測る ----
    n_up = len(flakes.geometry().points())
    n_kept = len(cover.geometry().points())
    snip = up.parm("snippet").eval()
    up.parm("snippet").set(snip.replace("n.y < 0.5", "n.y < 0.0"))
    faces_loose = up.geometry().intrinsicValue("primitivecount")
    up.parm("snippet").set(snip)
    faces_ok = up.geometry().intrinsicValue("primitivecount")
    blob.parm("voxelsize").set(VOX * 2)
    t0 = time.perf_counter()
    n_coarse = snow.geometry().intrinsicValue("primitivecount")
    coarse_sec = time.perf_counter() - t0
    blob.parm("voxelsize").set(VOX)
    traps = [
        {"title": "屋根の下にも雪が積もってしまう",
         "body": f"上向きの面は、屋根に隠れた中台や火袋の上にもある。真上への光線で調べると、まいた {n_up:,} 点のうち "
                 f"{n_up - n_kept:,} 点が屋根などの下にあった。消さないと、屋根の下に雪の塊ができる。",
         "img": "", "cap": ""},
        {"title": "向きのしきい値で、雪の付く面が変わる",
         "body": f"N.y < 0.5 で消すと、残る面は {faces_ok} 枚。0 にする（下向きだけ消す）と {faces_loose} 枚が残り、"
                 "壁のような縦の面にまで粒がまかれる。急な面に雪は残らないので、0.5 前後から始める。",
         "img": "", "cap": ""},
        {"title": "Voxel Size で、雪の細かさと重さが決まる",
         "body": f"Voxel Size {VOX} で雪の面は {n_snow:,} 枚（{snow_sec:.1f} 秒）。倍の {VOX * 2} にすると {n_coarse:,} 枚（{coarse_sec:.1f} 秒）。"
                 "形を決めるまでは粗くして、最後に細かくする。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "18個（材質3つ）"], ["雪の粒", f"{n_kept:,}個"], ["雪の面", f"{n_snow:,}枚"]], traps=traps)


if __name__ == "__main__":
    main()
