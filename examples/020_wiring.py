"""実験020 第1歩 — POP のネットワークを組む。

分かっていること
  popobject  入力なし / 出力1つ   … 粒子の入れ物を作る
  popsolver  入力3つ / 出力1つ    … ヘルプいわく「緑の入力に POP の部品を挿す」
  popsource  入力なし / 出力1つ   … 粒を生む部品
  popforce   …                    … 力を加える部品

見当: popobject → popsolver の入力1、部品は入力2・3へ。
019と同じで、総当たりではなく役割から組む。
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")


def build(force_slot=2):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "pop_test")

    # 粒を出す元の形
    src_geo = geo.createNode("grid", "emitter")
    src_geo.parmTuple("size").set((1.0, 1.0))
    src_geo.parm("rows").set(10)
    src_geo.parm("cols").set(10)
    src_geo.parmTuple("t").set((0.0, 3.0, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    force = dop.createNode("popforce", "gravity")

    source.parm("soppath").set(src_geo.path())
    source.parm("emittype").set(0)            # All Points
    source.parm("constantactivate").set(True)
    source.parm("constantrate").set(200)      # 毎秒200個
    source.parm("impulseactiveate").set(False)
    if force.parmTuple("force") is not None:
        force.parmTuple("force").set((0.0, -9.80665, 0.0))

    solver.setInput(0, obj)
    solver.setInput(1, source)
    if force_slot < len(solver.inputNames()):
        solver.setInput(force_slot, force)

    solver.setDisplayFlag(True)
    dop.setDisplayFlag(True)

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.setDisplayFlag(True)
    imp.setRenderFlag(True)
    return geo, dop, solver, imp


def counts(node, frames):
    out = []
    for frame in frames:
        hou.setFrame(frame)
        try:
            g = node.geometry()
        except hou.Error as exc:
            return f"エラー: {exc}"
        out.append(0 if g is None else len(g.points()))
    return out


FRAMES = [1, 2, 5, 10, 20, 30]
for slot in (2, 1):
    geo, dop, solver, imp = build(force_slot=slot)
    hou.setFrame(1)
    try:
        imp.cook(force=True)
    except hou.Error:
        pass
    print(f"力を入力{slot + 1}へ: solver エラー {solver.errors() or 'なし'} / "
          f"import エラー {imp.errors() or 'なし'}")
    print("  粒の数:", counts(imp, FRAMES))
    if not imp.errors():
        hou.setFrame(20)
        g = imp.geometry()
        if g and len(g.points()):
            ys = [p.position()[1] for p in g.points()]
            print(f"  フレーム20の高さ: 最高 {max(ys):.4f} / 最低 {min(ys):.4f} / "
                  f"平均 {sum(ys) / len(ys):.4f}")
            print("  点アトリビュート:", [a.name() for a in g.pointAttribs()])
        break
