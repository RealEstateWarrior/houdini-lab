"""実験019 第1歩 — FLIP の正しい配線を突き止める。

017では4通り試して全部「Not enough sources specified.」だった。
付属ヘルプ（nodes.zip）を読んで2つ分かった。

1. flipsolver の入力は 1=Sources（液体の粒）、2=Container、3=Collisions、4=Boundary Flow
2. <strong>flipcontainer にも同じ3つの入力と3つの出力がある</strong>

2が鍵だった。コンテナは単なる箱ではなく、3つのチャンネル（粒・容器・衝突）を
束ねて流す中継点になっている。粒はソルバに直接つなぐのではなく、
いったんコンテナに入れて、コンテナの3出力をソルバの3入力へ渡す。

    tank ──→ container(入力1) ──┬─出力1─→ solver(入力1)
                                ├─出力2─→ solver(入力2)
                                └─出力3─→ solver(入力3)

017で試した4通りは、どれもこの形になっていなかった。
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SEP = 0.08


def describe(node, index=0):
    try:
        geo = node.geometry(index)
    except hou.Error as exc:
        return f"エラー({exc})"
    if geo is None:
        return "なし"
    return f"{len(geo.points()):6d}点 / {len(geo.prims()):5d}prim"


def build():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "flip_test")

    tank = geo.createNode("particlefluidtank", "tank")
    tank.parm("particlesep").set(SEP)
    tank.parmTuple("size").set((1.4, 1.4, 1.4))

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((3.0, 3.0, 3.0))
    container.parm("particlesep").set(SEP)
    container.setInput(0, tank)          # 粒はコンテナの入力1へ

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    for channel in range(3):             # 3チャンネルをそのまま渡す
        solver.setInput(channel, container, channel)

    return geo, tank, container, solver


def main():
    geo, tank, container, solver = build()

    print("配線: tank → container(入力1)、container の3出力 → solver の3入力")
    hou.setFrame(1)
    try:
        solver.cook(force=True)
    except hou.Error as exc:
        print("  cook が失敗:", exc)
    print("  エラー:", solver.errors() or "なし")
    print("  警告:", solver.warnings() or "なし")

    names = solver.outputNames()
    for index in range(len(names)):
        print(f"    solver 出力{index + 1}: {describe(solver, index)}")
    print("  container の出力:")
    for index in range(len(container.outputNames())):
        print(f"    出力{index + 1}: {describe(container, index)}")
    print("  tank:", describe(tank))

    if solver.errors():
        print("\nまだ動かない。ここで止める。")
        return

    print("\n  フレームを進める（出力1＝液体の粒）")
    for frame in (1, 2, 5, 10, 20, 40):
        hou.setFrame(frame)
        print(f"    フレーム{frame:3d}: {describe(solver, 0)}")

    hou_tools.write_graph(geo.path(), os.path.join(OUT, "019_graph.json"),
                          title="実験019 — FLIP の配線")
    hou_tools.save_hip(os.path.join(OUT, "019_flip.hipnc"))
    print("\n保存: out/019_flip.hipnc, out/019_graph.json")


if __name__ == "__main__":
    main()
