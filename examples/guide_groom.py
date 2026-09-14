"""手順ページ用の画像を作る — 「毛を生やして束ねる」（実験042〜046の内容）。

実験ログは「何を測って何が分かったか」の記録なので、作り方を知りたい人には重い。
手順を1段ずつ組み立てて、各段の絵を撮る。

すべて同じカメラから撮るので、段が進むと何が増えたのかがそのまま見える。

    hython examples/guide_groom.py
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 420)
PREFIX = "guide_groom"
GUIDES = 300
SEGMENTS = 8
LENGTH = 0.5
DENSITY = 1000
RADIUS = 0.20
THICKNESS = 0.008

GUIDE_VEX = f"""
int segs = {SEGMENTS};
float len = {LENGTH};
int n = npoints(0);
for (int i = 0; i < n; i++) {{
    vector p = point(0, "P", i);
    vector nn = point(0, "N", i);
    if (length(nn) < 1e-6) nn = normalize(p);

    // どの面から生えたか。グルームの道具はこの番号が無いと動かない
    int sprim; vector suv;
    xyzdist(1, p, sprim, suv);
    int prim = addprim(0, "polyline");
    setprimattrib(0, "skinprim", prim, sprim);
    setprimattrib(0, "skinprimuv", prim, suv);

    for (int s = 0; s <= segs; s++) {{
        vector q = p + nn * (len * float(s) / float(segs));
        int pt = addpoint(0, q);
        // ここを忘れると rest が (0,0,0) のまま入り、
        // hairgen からはガイドが全部原点にあるように見える
        setpointattrib(0, "rest", pt, q);
        addvertex(0, prim, pt);
    }}
}}
for (int i = n - 1; i >= 0; i--) removepoint(0, i);
"""

COLOR_VEX = """
int cid = @clumpid;
vector c = set(rand(cid * 3 + 0.1), rand(cid * 3 + 1.7), rand(cid * 3 + 2.3));
int pts[] = primpoints(0, @primnum);
foreach (int pt; pts) setpointattrib(0, "Cd", pt, 0.2 + 0.8 * c);
"""


def shoot(sop, step, bbox, shading="smoothwire"):
    path = os.path.join(OUT, f"{PREFIX}_{step}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             frame_bbox=bbox, margin=1.04)
    geo = sop.geometry()
    print(f"  {step}: {len(geo.points())}点 / "
          f"{len(geo.prims())}プリミティブ → {path}")
    return path


def main():
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "groom")

    # 1. 土台を作る
    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)              # polymesh。既定のままでは面が無い
    skin.parm("rows").set(40)
    skin.parm("cols").set(40)

    # 2. 面の向きを作る
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(skin)

    # 3. 元の位置を覚えさせる。これが無いと hairgen が止まる
    rest = geo.createNode("rest", "rest")
    rest.setFirstInput(normal)

    # 4. 根元をばらまく
    roots = geo.createNode("scatter::2.0", "roots")
    roots.setFirstInput(rest)
    roots.parm("npts").set(GUIDES)

    # 5. ガイドを組む
    make = geo.createNode("attribwrangle", "make_guides")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)             # ディテール（1回だけ走る）
    make.parm("snippet").set(GUIDE_VEX)

    # 6. 毛を増やす。入力は「土台 → ガイド」
    gen = geo.createNode("hairgen::2.0", "hairgen")
    gen.setInput(0, rest)
    gen.setInput(1, make)
    gen.parm("density").set(DENSITY)
    gen.parm("influenceradius").set(RADIUS)
    gen.parm("thickness").set(THICKNESS)

    # 既定のままの比較用（influenceradius 0.05）
    thin = geo.createNode("hairgen::2.0", "hairgen_default")
    thin.setInput(0, rest)
    thin.setInput(1, make)
    thin.parm("density").set(DENSITY)
    thin.parm("thickness").set(THICKNESS)

    # 7. 束ねる。入力は「毛 → 土台」で hairgen とは逆
    clump = geo.createNode("hairclump::2.0", "clump")
    clump.setInput(0, gen)
    clump.setInput(1, rest)
    clump.parm("clumpsize").set(0.4)

    # 8. 束ごとに色を変える
    tint = geo.createNode("attribwrangle", "tint")
    tint.setFirstInput(clump)
    tint.parm("class").set(1)
    tint.parm("snippet").set(COLOR_VEX)

    out_plain = geo.createNode("merge", "result")
    out_plain.setInput(0, skin)
    out_plain.setInput(1, clump)

    out_color = geo.createNode("merge", "result_color")
    out_color.setInput(0, skin)
    out_color.setInput(1, tint)

    out_loose = geo.createNode("merge", "result_loose")
    out_loose.setInput(0, skin)
    out_loose.setInput(1, gen)

    out_thin = geo.createNode("merge", "result_default")
    out_thin.setInput(0, skin)
    out_thin.setInput(1, thin)

    out_color.setDisplayFlag(True)
    out_color.setRenderFlag(True)
    geo.layoutChildren()

    bbox = hou_tools.bbox_union([out_plain.path()])
    print("各段を同じカメラで撮る")
    shoot(skin, "1_skin", bbox)
    shoot(roots, "2_roots", bbox)
    shoot(make, "3_guides", bbox)
    shoot(out_loose, "4_hairgen", bbox, shading="smooth")
    shoot(out_plain, "5_clump", bbox, shading="smooth")
    shoot(out_color, "6_color", bbox, shading="smooth")
    shoot(out_thin, "7_default", bbox, shading="smooth")

    hou_tools.write_graph(geo.path(),
                          os.path.join(OUT, f"{PREFIX}_graph.json"),
                          title="手順 — 毛を生やして束ねる")
    hou_tools.save_hip(os.path.join(OUT, f"{PREFIX}.hipnc"))
    print("保存:", f"out/{PREFIX}.hipnc")


if __name__ == "__main__":
    main()
