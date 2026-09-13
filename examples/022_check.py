"""張った面の体積が、粒から予測した値の2.75倍になった。原因を切り分ける。

考えられること
  1. 面が閉じていない。閉じていないと、囲まれた体積という考え方が成り立たない
  2. 面が粒より太く張られている。粒の半径ぶん膨らんでいるなら大きく出る
  3. 019で求めた「粒1つ分の体積」が間違っている

1から順に潰す。
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

EXPERIMENT = os.path.join(HERE, "examples", "022_fluid_surface.py")
namespace = {"__name__": "notmain", "__file__": EXPERIMENT}
exec(compile(open(EXPERIMENT, encoding="utf-8").read(), EXPERIMENT, "exec"), namespace)
build = namespace["build"]
mesh_volume = namespace["mesh_volume"]
FRAME = namespace["FRAME"]
SEP = namespace["SEP"]
PER_PARTICLE = namespace["PER_PARTICLE"]


def open_edges(geometry):
    """2つの面に共有されていない辺の数。閉じた面なら0になる。"""
    counts = {}
    for prim in geometry.prims():
        points = [v.point().number() for v in prim.vertices()]
        for i in range(len(points)):
            a, b = points[i], points[(i + 1) % len(points)]
            key = (a, b) if a < b else (b, a)
            counts[key] = counts.get(key, 0) + 1
    return sum(1 for n in counts.values() if n != 2), len(counts)


def main():
    geo, solver, surface, convert = build()
    hou.setFrame(FRAME)
    particles = len(solver.geometry(0).points())
    predicted = particles * PER_PARTICLE
    print(f"粒 {particles} 個 / 019の式からの予測 {predicted:.5f}")

    mesh = convert.geometry()
    bad, total = open_edges(mesh)
    print(f"\n1. 面は閉じているか: 共有されていない辺 {bad} / 全 {total} 本")
    print(f"   → {'閉じている' if bad == 0 else '閉じていない'}")
    print(f"   体積（符号付き）: {mesh_volume(mesh):.5f}")

    print("\n2. 面の太さを決める設定")
    names = [p.name() for p in surface.parms()]
    for key in ("radius", "influence", "particlesep", "voxel"):
        hits = [n for n in names if key in n.lower()]
        if hits:
            for n in hits[:5]:
                parm = surface.parm(n)
                if parm is not None:
                    print(f"   {n} = {parm.eval()!r}")

    # 太さを決めているのは influenceradius（粒の間隔の何倍まで届くか）
    surface.parm("particlesep").set(SEP)
    print(f"\n3. influenceradius を振ったときの体積（particlesep は {SEP} に固定）")
    print(f"{'影響半径':>10} {'実際の半径':>12} {'体積':>11} {'予測との比':>11}")
    for radius in (1.0, 1.5, 2.0, 2.5, 3.0):
        surface.parm("influenceradius").set(radius)
        hou.setFrame(FRAME)
        try:
            mesh = convert.geometry()
        except hou.Error as exc:
            mesh = None
            print(f"{radius:10.2f} エラー: {exc}")
            continue
        if mesh is None or not mesh.prims():
            print(f"{radius:10.2f} {radius * SEP:12.4f}  面ができない"
                  f"（surface のエラー: {surface.errors() or None}）")
            continue
        volume = abs(mesh_volume(mesh))
        print(f"{radius:10.2f} {radius * SEP:12.4f} {volume:11.5f} "
              f"{volume / predicted:11.4f}")


if __name__ == "__main__":
    main()
