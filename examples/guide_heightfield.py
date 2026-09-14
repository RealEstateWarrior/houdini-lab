"""手順ページ用の画像を作る — 「地形を削って草を生やす」（実験034〜037の内容）。

HeightField は高さを数の並び（ボリューム）として持つ仕組みで、
ポリゴンの地形では難しい「水で削る」がそのまま計算できる。

各段を同じカメラから撮るので、段が進むと何が増えたのかがそのまま見える。

    hython examples/guide_heightfield.py
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 420)
PREFIX = "guide_hf"
SIZE = 200.0
SPACING = 2.0
AMP = 120.0
ELEMENT = 80.0
ERODE = 4
BLADES = 900

LAYER_VEX = """
// 浸食が残したレイヤーを、点に読み込む。
f@sediment = volumesample(1, "sediment", @P);

// 下り坂の向きは、高さそのものから作る。
// normal SOP は N をバーテックスに書くので、点のラングルからは読めない。
float e = 2.0;
float h0 = volumesample(1, "height", @P);
float hx = volumesample(1, "height", @P + set(e, 0, 0));
float hz = volumesample(1, "height", @P + set(0, 0, e));
vector down = set(-(hx - h0), 0.0, -(hz - h0));
f@slope = length(down) / e;
v@downhill = (length(down) > 1e-9) ? normalize(down) : set(1, 0, 0);
"""

AIM_VEX = """
// 草は上に立てる。斜面の向きに倒したいときは downhill を混ぜる。
@N = set(0, 1, 0);
@pscale = 0.6 + 0.8 * rand(@ptnum);
"""


def shoot(sop, step, bbox, shading="smoothwire"):
    path = os.path.join(OUT, f"{PREFIX}_{step}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading=shading,
                             frame_bbox=bbox, margin=1.03)
    geo = sop.geometry()
    print(f"  {step}: {len(geo.points())}点 / "
          f"{len(geo.prims())}プリミティブ → {path}")
    return path


def main():
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "terrain")

    # 1. 地形の土台。面も点も無く、height と mask の2枚だけ
    field = geo.createNode("heightfield", "field")
    field.parm("sizex").set(SIZE)
    field.parm("sizey").set(SIZE)
    field.parm("gridspacing").set(SPACING)

    # 2. 起伏を足す
    noise = geo.createNode("heightfield_noise", "noise")
    noise.setFirstInput(field)
    noise.parm("amp").set(AMP)
    noise.parm("elementsize").set(ELEMENT)

    # 3. 水で削る。レイヤーが2枚から7枚に増える
    erode = geo.createNode("heightfield_erode", "erode")
    erode.setFirstInput(noise)
    erode.parm("iterations").set(ERODE)

    # 撮影用。削る前と後を同じ形式で見るために2つ用意する
    mesh_raw = geo.createNode("convertheightfield", "mesh_raw")
    mesh_raw.setFirstInput(noise)

    # 4. メッシュに直す
    mesh = geo.createNode("convertheightfield", "mesh")
    mesh.setFirstInput(erode)

    # 5. 面の向きを作る
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(mesh)

    # 6. 浸食のレイヤーを点に読む
    layers = geo.createNode("attribwrangle", "read_layers")
    layers.setFirstInput(normal)
    layers.setInput(1, erode)
    layers.parm("class").set(2)
    layers.parm("snippet").set(LAYER_VEX)

    # 7. 草を散らす
    scatter = geo.createNode("scatter::2.0", "scatter")
    scatter.setFirstInput(layers)
    scatter.parm("npts").set(BLADES)

    aim = geo.createNode("attribwrangle", "aim")
    aim.setFirstInput(scatter)
    aim.parm("class").set(2)
    aim.parm("snippet").set(AIM_VEX)

    # 8. 草を複製する
    blade = geo.createNode("tube", "blade")
    blade.parm("type").set(1)
    blade.parm("rad1").set(0.35)
    blade.parm("rad2").set(0.02)
    blade.parm("height").set(7.0)
    blade.parm("rows").set(2)
    blade.parm("cols").set(6)
    blade.parm("rx").set(90)        # Z 軸向きにする（実験008）

    copies = geo.createNode("copytopoints::2.0", "copies")
    copies.setInput(0, blade)
    copies.setInput(1, aim)

    result = geo.createNode("merge", "result")
    result.setInput(0, layers)
    result.setInput(1, copies)
    result.setDisplayFlag(True)
    result.setRenderFlag(True)
    geo.layoutChildren()

    bbox = hou_tools.bbox_union([result.path()])
    print("各段を同じカメラで撮る")
    shoot(mesh_raw, "1_noise", bbox)
    shoot(mesh, "2_erode", bbox)
    shoot(normal, "3_mesh", bbox, shading="smooth")
    shoot(aim, "4_scatter", bbox, shading="smooth")
    shoot(result, "5_grass", bbox, shading="smooth")

    hou_tools.write_graph(geo.path(),
                          os.path.join(OUT, f"{PREFIX}_graph.json"),
                          title="手順 — 地形を削って草を生やす")
    hou_tools.save_hip(os.path.join(OUT, f"{PREFIX}.hipnc"))
    print("保存:", f"out/{PREFIX}.hipnc")


if __name__ == "__main__":
    main()
