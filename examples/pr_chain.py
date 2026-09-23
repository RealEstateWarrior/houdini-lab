# -*- coding: utf-8 -*-
"""実践「鎖を垂らす」— 2本の柱のあいだに、垂れた線（懸垂線）を引き、輪を1つおきに90度ひねって並べる。

本物の鎖は、輪が交互に向きを変えてかみ合い、両端を留めると真ん中がたるんだ弧（懸垂線）になる。
線を「輪1つぶんの間隔」で区切り、点ごとに輪を置いて、向きを1つおきに回せば、シミュレーションなしで作れる。

    hython examples/pr_chain.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_kit as kit  # noqa: E402

MAJOR = 0.04     # 輪の太さの中心までの半径
MINOR = 0.009    # 針金の太さ（半径）
STRETCH = 1.55   # 輪を縦長にする倍率
PITCH = round((MAJOR - MINOR) * 2 * STRETCH, 4)   # 輪の内側の長さ＝となりの輪との間隔


def main():
    import hou
    g = kit.Guide("chain", "鎖を垂らす",
                  "2本の柱のあいだに、真ん中がたるんだ線を引き、その線にそって輪を並べる。輪を1つおきに90度ひねると、"
                  "かみ合った鎖になる。動かすシミュレーションは使わず、線の形だけで作る。",
                  tags=["モデリング", "VEX", "複製", "Karma"])
    g.shot_dir = (0.35, 0.3, 1.2)
    line = g.node("line", "span", origin=(-1.0, 0, 0), dir=(1, 0, 0), dist=2.0, points=200)
    sag = g.node("attribwrangle", "hang", [line], snippet=(
        "// 懸垂線（鎖やロープが自分の重さで垂れた形）。a が小さいほど深くたるむ\n"
        "float a = chf('a');\n"
        "@P.y = a * cosh(@P.x / a) - a * cosh(1.0 / a) + 1.6;   // 両端（x = ±1）の高さを 1.6 m にそろえる"))
    kit_spare(sag, a=0.9)
    g.step(sag, "垂れた線を引く",
           "<code>line</code> で x = −1 から 1 まで、長さ 2 m・200 点の線を引く。<code>attribwrangle</code> で高さを "
           "<strong>a · cosh(x / a)</strong> の形にする。これは懸垂線と呼ばれ、鎖やロープが自分の重さで垂れたときの形そのもの。"
           "<strong>a = 0.9</strong>。小さくするほど深くたるむ。両端の高さは 1.6 m にそろえる。",
           cap="両端が同じ高さで、真ん中がたるんだ線。", shading="wire", ui_parm="a")

    links = g.node("resample", "one_per_link", [sag], dolength=1, length=PITCH)
    g.step(links, "輪1つぶんの間隔で区切る",
           f"<code>resample</code> の <strong>Length を {PITCH}</strong>（m）にして、線を等しい間隔の点に打ち直す。"
           "間隔は、輪の <strong>内側の長さ</strong> にする。となりの輪は、この内側にちょうど通る。"
           f"輪の大きさ（半径 {MAJOR}・針金の太さ {MINOR}・縦長 {STRETCH} 倍）から、(0.04 − 0.009) × 2 × 1.55 で出した。",
           cap="等しい間隔の点。点1つに輪が1つ乗る。", shading="wire", ui_parm="length")

    turn = g.node("attribwrangle", "twist_every_other", [links], snippet=(
        "// 線の向き（となりの点へ向かう向き）を求め、輪の長い向きをそれに合わせる\n"
        "vector next = point(0, 'P', min(@ptnum + 1, @numpt - 1));\n"
        "vector prev = point(0, 'P', max(@ptnum - 1, 0));\n"
        "vector along = normalize(next - prev);\n"
        "vector up = {0, 1, 0};\n"
        "// 1つおきに、輪の面を90度ひねる（となりの輪とかみ合う向き）\n"
        "if (@ptnum % 2 == 1) up = normalize(cross(along, up));\n"
        "p@orient = quaternion(maketransform(along, up));"))
    g.step(turn, "輪の向きを決め、1つおきにひねる",
           "<code>attribwrangle</code> で、点ごとに <strong>orient</strong>（向き）を作る。前後の点を結んだ向きを「輪の長い向き」にし、"
           "<strong>1つおきに（@ptnum % 2 == 1）輪の面を90度回す</strong>。本物の鎖も、輪の面が交互に縦・横になってかみ合っている。",
           cap="見た目は同じ。点ごとに向きが付いた。", shading="wire", ui_parm="snippet")

    ring = g.node("torus", "link", type="poly", orient="x", rad=(MAJOR, MINOR), rows=24, cols=12)
    oval = g.node("xform", "make_oval", [ring], s=(1, 1, STRETCH))
    chain = g.node("copytopoints::2.0", "chain", [oval, turn])
    n_links = len(turn.geometry().points())
    g.step(chain, "輪を作って、点に並べる",
           f"<code>torus</code>（Orientation を <strong>X Axis</strong>、半径 {MAJOR}・{MINOR}）で輪を作り、"
           f"<code>xform</code> で z 方向（長い向き）に <strong>{STRETCH} 倍</strong> して、鎖らしい縦長の輪にする。"
           f"<code>copytopoints</code> の左に輪、右に向きの付いた点をつなぐと、{n_links} 個の輪が交互にひねられて並ぶ。",
           cap=f"{n_links} 個の輪がかみ合った鎖。", shading="smooth", ui_parm="rad",
           bbox=hou.BoundingBox(-0.35, 0.95, -0.12, 0.35, 1.45, 0.12))

    posts = [g.node("tube", f"post{i}", type="poly", rad=(0.035, 0.035), height=1.75, cols=24, cap=1, t=(x, 0.875, 0))
             for i, x in enumerate((-1.04, 1.04))]
    steel = g.mat("steel_mat", basecolor=(0.62, 0.62, 0.6), metallic=1.0, rough=0.28)
    wood = g.mat("post_mat", basecolor=(0.22, 0.13, 0.07), rough=0.6)
    final = g.node("merge", "chain_and_posts",
                   [g.assign(chain, steel, "assign_steel"), g.assign(g.node("merge", "posts", posts), wood, "assign_posts")])
    g.step(final, "柱を立て、材質を当てる",
           "<code>tube</code> で両端に柱を2本立て、鎖の端を柱の中へ少し入れる。鎖は <code>principledshader</code> で "
           "<strong>Metallic 1・Roughness 0.28</strong>（使い込んだ鉄）。柱は茶色の木。金属はまわりを映して見えるので、"
           "撮るときはドームの光を少し強めにして、映り込むものを作る。",
           cap="材質を当てた状態。", shot=False)
    g.hero(final, "Karma で撮った仕上がり。輪が交互にひねられてかみ合い、真ん中がたるむ。",
           direction=(0.35, 0.22, 1.2), key=3.0, rim=7.0, dome=0.6, spp=64, margin=1.04,
           backdrop=(0.07, 0.07, 0.075), bbox=hou.BoundingBox(-1.1, 0.9, -0.2, 1.1, 1.75, 0.2))

    # ---- 落とし穴を測る ----
    links.parm("length").set(round(PITCH * 1.5, 4))
    n_wide = len(turn.geometry().points())
    links.parm("length").set(PITCH)
    turn.bypass(True)
    has_orient = chain.geometry().findPointAttrib("orient") is not None
    turn.bypass(False)
    sag.parm("a").set(0.5)
    deep = 1.6 - min(p.position()[1] for p in sag.geometry().points())
    sag.parm("a").set(0.9)
    shallow = 1.6 - min(p.position()[1] for p in sag.geometry().points())
    traps = [
        {"title": "間隔を広げると、輪が離れてしまう",
         "body": f"Length を 1.5 倍（{PITCH * 1.5:.3f}）にすると、輪は {n_links} 個から {n_wide} 個に減り、となりの輪の内側に届かなくなる。"
                 "間隔は必ず、輪の内側の長さ (太さの中心までの半径 − 針金の太さ) × 2 × 縦長の倍率 にする。",
         "img": "", "cap": ""},
        {"title": "向きを付けないと、輪が全部同じ向きになる",
         "body": "twist_every_other を外すと、copytopoints に向き（orient）が渡らず、輪はどれも元の向きのまま並ぶ"
                 + ("" if not has_orient else "") + "。線にも沿わず、かみ合いもしない。",
         "img": "", "cap": ""},
        {"title": "a でたるみの深さが決まる",
         "body": f"a = 0.9 で真ん中は端より {shallow:.2f} m 下がり、a = 0.5 では {deep:.2f} m 下がった。"
                 "鎖の長さは変わるので、輪の数も自動で増える。",
         "img": "", "cap": ""},
    ]
    g.save(facts=[["足すノード", "13個（材質2つ）"], ["輪の数", f"{n_links}個"]], traps=traps)


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
