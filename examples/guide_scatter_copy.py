"""手順ページ用の画像を作る — 「地面に物を生やす」（実験008の内容）。

実験ログは「何を測って何が分かったか」の記録なので、作り方を知りたい人には重い。
手順を1段ずつ組み立てて、各段の絵を撮る。

すべて同じカメラから撮るので、段が進むと何が増えたのかがそのまま見える。

    hython examples/guide_scatter_copy.py
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 420)
PREFIX = "guide008"


def shoot(sop, step, bbox):
    path = os.path.join(OUT, f"{PREFIX}_{step}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading="smoothwire",
                             frame_bbox=bbox)
    geo = sop.geometry()
    print(f"  {step}: {len(geo.points())}点 / {len(geo.prims())}プリミティブ → {path}")
    return path


def main():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "grow_things")

    # 1. 地面を作る
    ground = geo.createNode("grid", "ground")
    ground.parmTuple("size").set((10.0, 10.0))
    ground.parm("rows").set(40)
    ground.parm("cols").set(40)

    # 2. 地面をでこぼこにする
    hills = geo.createNode("mountain::2.0", "hills")
    hills.setFirstInput(ground)
    hills.parm("height").set(0.6)
    hills.parm("elementsize").set(3.0)

    # 3. 面の向き（法線 N）を作る。ばらまく<前>にやるのが肝で、
    #    点だけになってからでは面が無いので N を計算できない。
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(hills)

    # 4. 点をばらまく。N は面から受け継がれる
    scatter = geo.createNode("scatter::2.0", "scatter")
    scatter.setFirstInput(normal)
    scatter.parm("npts").set(200)

    # 5. 生やすもの。Z軸に伸ばしておくのが肝
    tree = geo.createNode("tube", "tree")
    tree.parm("type").set(1)          # 既定は Primitive で点が1個しか出ない
    tree.parm("rad1").set(0.02)
    tree.parm("rad2").set(0.14)
    tree.parm("height").set(1.0)
    tree.parmTuple("r").set((90.0, 0.0, 0.0))    # Y軸に立つ筒を Z軸に倒す

    tree_y = geo.createNode("tube", "tree_y")    # 比較用。倒さないもの
    tree_y.parm("type").set(1)
    tree_y.parm("rad1").set(0.02)
    tree_y.parm("rad2").set(0.14)
    tree_y.parm("height").set(1.0)

    # 6. 点の上に複製する
    copy_bad = geo.createNode("copytopoints::2.0", "copy_wrong")
    copy_bad.setInput(0, tree_y)
    copy_bad.setInput(1, scatter)

    copy_good = geo.createNode("copytopoints::2.0", "copy_right")
    copy_good.setInput(0, tree)
    copy_good.setInput(1, scatter)

    merge_bad = geo.createNode("merge", "result_wrong")
    merge_bad.setInput(0, hills)
    merge_bad.setInput(1, copy_bad)

    merge_good = geo.createNode("merge", "result_right")
    merge_good.setInput(0, hills)
    merge_good.setInput(1, copy_good)

    geo.layoutChildren()

    bbox = hou_tools.bbox_union([merge_good.path(), merge_bad.path()])
    print("各段を同じカメラで撮る")
    shoot(ground, "1_grid", bbox)
    shoot(hills, "2_mountain", bbox)
    shoot(scatter, "3_scatter", bbox)
    shoot(tree, "4_template", hou_tools.bbox_union([tree.path()]))
    shoot(merge_bad, "5_wrong", bbox)
    shoot(merge_good, "6_right", bbox)

    hou_tools.write_graph(geo.path(), os.path.join(OUT, f"{PREFIX}_graph.json"),
                          title="手順 — 地面に物を生やす")
    hou_tools.save_hip(os.path.join(OUT, f"{PREFIX}.hipnc"))
    print("保存:", f"out/{PREFIX}.hipnc")


if __name__ == "__main__":
    main()
