"""体積が分かっている水に表面を張って、正しく測れるかを確かめる。

落ちて広がった水では、張った面の体積が粒からの予測の2.1〜2.75倍になった。
これが「面の張り方のせい」なのか「形のせい」なのかを切り分ける。

器を水位まで満たせば、水の体積は計算で分かる。
  器は 3×3×3、原点中心。水位 0.0 なら深さ 1.5 なので 3 × 3 × 1.5 = 13.5

ここで面を張って 13.5 に近い値が出れば、面の張り方は正しい。

付属ヘルプ（sop/flipcontainer）にこう書いてある。
「境界の外側にも粒が作られる。面を張るときこの粒も数えられるので、メッシュが大きくなる。
　Particle Fluid Surface の Bounding Box で外側の粒を切り取れる」

その通りかを確かめる。
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
mesh_volume = namespace["mesh_volume"]

SEP = 0.07
BOX = 3.0
WATERLINE = 0.0
TRUE_VOLUME = BOX * BOX * (WATERLINE + BOX / 2.0)


def build():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "known")

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    solver.parm("donarrowband").set(False)
    solver.parm("dowaterline").set(True)
    solver.parm("waterline").set(WATERLINE)
    for channel in range(3):
        solver.setInput(channel, container, channel)

    surface = geo.createNode("particlefluidsurface", "surface")
    surface.setFirstInput(solver)
    surface.parm("particlesep").set(SEP)

    convert = geo.createNode("convert", "to_polygons")
    convert.setFirstInput(surface)

    geo.layoutChildren()
    return geo, solver, surface, convert


def measure(surface, convert, radius):
    surface.parm("influenceradius").set(radius)
    hou.setFrame(1)
    mesh = convert.geometry()
    if mesh is None or not mesh.prims():
        return None
    return abs(mesh_volume(mesh))


def main():
    geo, solver, surface, convert = build()
    hou.setFrame(1)
    particles = len(solver.geometry(0).points())
    print(f"水位 {WATERLINE} / 本当の体積 {TRUE_VOLUME:.4f} / 粒 {particles} 個")

    print(f"\n{'切り取り':>8} {'影響半径':>9} {'体積':>11} "
          f"{'本当との比':>11} {'ずれ':>9}")
    rows = []
    for clip in (False, True):
        surface.parm("dobbox").set(clip)
        if clip:
            for axis in ("x", "y", "z"):
                surface.parm(f"size{axis}").set(BOX)
                surface.parm(f"t{axis}").set(0.0)
            # これを入れないと切り口が開いたままになり、
            # 「囲まれた体積」という考え方が成り立たない
            surface.parm("closedends").set(True)
        for radius in (2.0, 3.0):
            volume = measure(surface, convert, radius)
            label = "あり" if clip else "なし"
            if volume is None:
                print(f"{label:>8} {radius:9.2f}  面ができない")
                continue
            gap = 100.0 * (volume - TRUE_VOLUME) / TRUE_VOLUME
            rows.append({"clip": clip, "radius": radius, "volume": volume,
                         "gap_pct": gap})
            print(f"{label:>8} {radius:9.2f} {volume:11.4f} "
                  f"{volume / TRUE_VOLUME:11.4f} {gap:8.1f}%")

    # 粒1つあたりの体積を、切り取ったあとの値から出し直す
    best = [r for r in rows if r["clip"]]
    if best:
        volume = best[0]["volume"]
        print(f"\n切り取ったあとの粒1つあたり: {TRUE_VOLUME / particles:.6f}"
              f"（本当の体積 ÷ 粒の数）")
        print(f"面から出した粒1つあたり: {volume / particles:.6f}")

    import json
    with open(os.path.join(OUT, "022_known.json"), "w", encoding="utf-8") as fp:
        json.dump({"true_volume": TRUE_VOLUME, "particles": particles,
                   "sep": SEP, "rows": rows}, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/022_known.json")


if __name__ == "__main__":
    main()
