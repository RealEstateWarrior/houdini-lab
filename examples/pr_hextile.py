# -*- coding: utf-8 -*-
"""実践「六角形のタイルを敷く」— 六角形を、1列おきに半分ずらしてすき間なく並べ、1枚ずつ色と高さを少し変える。

本物の六角タイルの床は、1枚ずつ焼き色が少しずつ違い、目地（すき間）に灰色のモルタルが見える。
六角形は、横に √3 × 半径、縦に 1.5 × 半径 の間隔で、1列おきに半分ずらすと、すき間なく並ぶ。

    hython examples/pr_hextile.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

R = 0.1        # 六角形の中心から角までの長さ
JOINT = 0.006  # 目地の幅


def main():
    import hou
    g = kit.Guide("hextile", "六角形のタイルを敷く",
                  "六角形は、横に √3 × 半径、縦に 1.5 × 半径 の間隔で、1列おきに横へ半分ずらすと、すき間なく並ぶ。"
                  "その位置に、目地のぶんだけ小さくした六角形のタイルを置き、1枚ずつ色と高さを少し変える。",
                  tags=["モデリング", "VEX", "複製", "Karma"])
    g.shot_dir = (0.5, 0.9, 1.0)
    spots = g.node("attribwrangle", "hex_grid", snippet=(
        "// 六角形の中心の並び。横の間隔 √3·R、縦の間隔 1.5·R、奇数の列は横に半分ずらす\n"
        "float R = chf('radius');\n"
        "float dx = sqrt(3) * R;\n"
        "float dz = 1.5 * R;\n"
        "for (int row = -8; row <= 8; row++) {\n"
        "    for (int col = -10; col <= 10; col++) {\n"
        "        float x = col * dx + (abs(row) % 2) * dx * 0.5;\n"
        "        int p = addpoint(0, set(x, 0, row * dz));\n"
        "        float s = row * 100 + col;\n"
        "        // 1枚ずつ、焼き色（テラコッタ）と、ごくわずかな高さの違い\n"
        "        setpointattrib(0, 'Cd', p, {0.62, 0.3, 0.17} * fit01(rand(s), 0.75, 1.2) + {0.04, 0.04, 0.03} * rand(s + 1));\n"
        "        setpointattrib(0, 'P', p, set(x, (rand(s + 2) - 0.5) * 0.002, row * dz));\n"
        "    }\n"
        "}"))
    spots.parm("class").set(0)
    kit_spare(spots, radius=R)
    g.step(spots, "六角形の中心を並べる",
           "何もつながない <code>attribwrangle</code>（Run Over は Detail）で、タイルの中心になる点を並べる。"
           f"半径 R = {R} m のとき、横の間隔は <strong>√3 × R</strong>（{math.sqrt(3) * R:.4f} m）、縦の間隔は <strong>1.5 × R</strong>（{1.5 * R:.3f} m）。"
           "<strong>1列おきに横へ半分ずらす</strong>と、六角形がすき間なくはまる並びになる。点ごとに焼き色 Cd と、ごくわずかな高さの差（2 mm 以内）も付ける。",
           cap="半分ずつずれた点の並び。", shading="wire", ui_parm="radius",
           bbox=hou.BoundingBox(-1.2, -0.05, -0.9, 1.2, 0.05, 0.9))

    hexagon = g.node("circle", "hexagon", type="poly", divs=6, orient=2, radx=R - JOINT, rady=R - JOINT, r=(0, 30, 0))
    thick = g.node("polyextrude::2.0", "tile_thickness", [hexagon], dist=0.012, outputback=1)
    soft = g.node("polybevel::3.0", "soft_edges", [thick], offset=0.0015, divisions=2)
    g.step(soft, "タイルを1枚作る",
           f"<code>circle</code> の Divisions を <strong>6</strong> にすると六角形になる。半径は目地のぶん小さい {R - JOINT} m、"
           "寝かせて（Orientation を ZX）、Rotate Y を 30度回して、角を横の並びに合わせる。"
           "<code>polyextrude</code> で厚さ 12 mm、<code>polybevel</code> で角を 1.5 mm 丸める。",
           cap="六角形のタイル1枚。", shading="smoothwire", bbox=hou.BoundingBox(-0.12, -0.01, -0.12, 0.12, 0.02, 0.12))

    tiles = g.node("copytopoints::2.0", "tiles", [soft, spots], targetattribs=1)
    tiles.parm("applyto1").set("points")
    tiles.parm("applyattribs1").set("Cd")
    grout = g.node("grid", "grout", size=(4, 3), rows=2, cols=2, t=(0, 0.004, 0))
    floor = g.node("merge", "tiled_floor", [tiles, grout])
    n_tiles = len(spots.geometry().points())
    g.step(floor, "並べて、目地を入れる",
           f"<code>copytopoints</code> でタイルを点に並べる（{n_tiles} 枚）。色は Target Attributes の「Apply to: Points」「Cd」で移す。"
           "タイルの厚みの途中の高さ（4 mm）に灰色の <code>grid</code> を敷くと、すき間から目地のモルタルが見える。",
           cap=f"{n_tiles} 枚の六角タイルの床。", shading="smooth",
           bbox=hou.BoundingBox(-1.2, -0.05, -0.9, 1.2, 0.05, 0.9))

    clay = g.mat("tile_mat", basecolor=(1, 1, 1), rough=0.35, coat=0.3)
    mortar = g.mat("grout_mat", basecolor=(0.5, 0.49, 0.46), rough=0.95)
    final = g.node("merge", "floor", [g.assign(tiles, clay, "assign_tile"), g.assign(grout, mortar, "assign_grout")])
    g.step(final, "材質を当てる",
           "タイルは Base Color を白にして点の色 Cd を使い、Roughness 0.35・Coat 0.3（うわぐすりのつや）。目地は灰色で Roughness 0.95。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。1枚ずつ焼き色の違う、六角形のテラコッタタイル。", direction=(0.35, 0.55, 1.0),
           key=3.0, rim=6.0, dome=0.5, spp=48, margin=0.6, floor=False, bbox=hou.BoundingBox(-1.2, -0.02, -0.9, 1.2, 0.02, 0.9))

    # ---- 落とし穴を測る ----
    def overlap_gap(dz_scale):
        """となりの列のタイルの中心どうしの、いちばん近い距離（重なるなら 2 × 内接円半径より小さい）。"""
        snippet = spots.parm("snippet").eval()
        spots.parm("snippet").set(snippet.replace("float dz = 1.5 * R;", f"float dz = {dz_scale} * R;"))
        pts = [p.position() for p in spots.geometry().points()]
        spots.parm("snippet").set(snippet)
        best = min((pts[i] - pts[j]).length() for i in range(len(pts)) for j in range(i + 1, min(i + 60, len(pts))))
        return best

    near_ok = overlap_gap(1.5)
    near_bad = overlap_gap(1.3)
    inner = math.sqrt(3) * R
    traps = [
        {"title": "縦の間隔は 1.5 × 半径",
         "body": f"となり合うタイルの中心どうしの、いちばん近い距離は {near_ok:.4f} m（縦 1.5·R のとき）。六角形がぴったり接する距離 √3·R = {inner:.4f} m と一致する。"
                 f"縦を 1.3·R にすると {near_bad:.4f} m に縮み、タイルどうしが重なる。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "11個（材質2つ）"], ["タイル", f"{n_tiles}枚"]], traps=traps)


def kit_spare(node, **values):
    """wrangle の chf のつまみを作って値を入れる（GUI の「Create spare parameters」ボタンと同じこと）。"""
    import hou
    group = node.parmTemplateGroup()
    for name, value in values.items():
        group.append(hou.FloatParmTemplate(name, name, 1, default_value=(value,)))
    node.setParmTemplateGroup(group)
    for name, value in values.items():
        node.parm(name).set(value)


if __name__ == "__main__":
    main()
