"""実験022 — 液体に表面を張る。粒から求めた体積は当たっているのか。

実験019で、粒の数と水の量の関係を測った。

    粒の数 = 3415.7 × 体積 + 18130

この式から、増えた粒1つが担う体積は 1/3415.7 = 0.000293 と出た。
粒の間隔の3乗（0.07³ = 0.000343）の 0.854倍にあたる。

今回はそれを別の道から検算する。粒に表面を張って、
<strong>張った面で囲まれた体積</strong>を測る。両者が合えば、019の式は正しい。

    予測: 面の体積 ≒ 粒の数 × 0.000293

さらに、表面を張るときの「なめらかさ」の設定も振る。
実験002で、分割そのものではなく平滑化が形を縮ませると分かった。
同じことが起きるなら、なめらかにするほど体積は減るはず。

    hython examples/022_fluid_surface.py
"""

import json
import os
import sys
import time

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SEP = 0.07
BOX = 3.0
PER_PARTICLE = 0.000293      # 019 で求めた、増えた粒1つが担う体積
FRAME = 40


def mesh_volume(geometry):
    """閉じた面で囲まれた体積を、発散定理で求める。

    面ごとの measuredvolume を足しても求まらない。平らな面には体積が無いため。
    三角形ごとに原点との四面体の符号付き体積を足し合わせると、
    外側の分と内側の分が打ち消し合って、囲まれた体積だけが残る。
    """
    total = 0.0
    for prim in geometry.prims():
        points = [v.point().position() for v in prim.vertices()]
        for i in range(1, len(points) - 1):
            a, b, c = points[0], points[i], points[i + 1]
            total += a.dot(b.cross(c))
    return total / 6.0


def build():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "liquid")

    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)

    blob = geo.createNode("box", "blob")
    blob.parmTuple("size").set((0.9, 0.9, 0.9))
    blob.parmTuple("t").set((0.0, 1.0, 0.0))

    src = geo.createNode("flipsource", "src")
    src.setFirstInput(blob)
    src.parm("particlesep").set(SEP)
    src.parm("volumename").set("source")

    merge = geo.createNode("merge", "merge_sources")
    merge.setInput(0, container, 0)
    merge.setInput(1, src)

    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    solver.parm("donarrowband").set(False)
    solver.parm("useground").set(True)
    solver.parm("ground_posy").set(-BOX / 2.0)
    solver.setInput(0, merge)
    solver.setInput(1, container, 1)
    solver.setInput(2, container, 2)

    surface = geo.createNode("particlefluidsurface", "surface")
    surface.setFirstInput(solver)

    # 出力は PolySoup（多数の面を1つにまとめた形）で、体積を測る仕組みが使えない。
    # convert で普通のポリゴンに戻すと測れるようになる。
    convert = geo.createNode("convert", "to_polygons")
    convert.setFirstInput(surface)

    geo.layoutChildren()
    return geo, solver, surface, convert


def main():
    geo, solver, surface, convert = build()

    print("particlefluidsurface のパラメータ")
    names = [p.name() for p in surface.parms()]
    for key in ("particlesep", "voxelsize", "particleradiusscale", "influence",
                "smooth", "filter", "droplet"):
        hits = [n for n in names if key in n.lower()]
        if hits:
            print(f"  {key}: {hits[:6]}")

    hou.setFrame(FRAME)
    particles = len(solver.geometry(0).points())
    print(f"\nフレーム{FRAME}: 粒 {particles} 個")
    print(f"019の式から予測される体積: {particles * PER_PARTICLE:.5f}")

    # 粒の間隔をそろえる。ずれていると表面の太さが変わる
    if surface.parm("particlesep") is not None:
        surface.parm("particlesep").set(SEP)

    rows = []
    smooth_parm = None
    for candidate in ("smoothingiterations", "smoothiterations", "filteriterations"):
        if surface.parm(candidate) is not None:
            smooth_parm = candidate
            break
    print(f"なめらかさの設定: {smooth_parm}")

    values = [0, 1, 2, 4, 8] if smooth_parm else [0]
    print(f"\n{'なめらかさ':>10} {'点':>9} {'面':>9} {'体積':>11} "
          f"{'予測との比':>11} {'0回との比':>11} {'秒':>7}")
    base = None
    for value in values:
        if smooth_parm:
            surface.parm("dosmooth").set(value > 0)
            surface.parm(smooth_parm).set(max(value, 1))
        start = time.perf_counter()
        hou.setFrame(FRAME)
        mesh = convert.geometry()
        volume = mesh_volume(mesh)
        elapsed = time.perf_counter() - start
        base = base or volume
        rows.append({"smooth": value, "points": len(mesh.points()),
                     "prims": len(mesh.prims()), "volume": volume,
                     "sec": elapsed})
        print(f"{value:10d} {len(mesh.points()):9d} {len(mesh.prims()):9d} "
              f"{volume:11.5f} {volume / (particles * PER_PARTICLE):11.4f} "
              f"{volume / base:11.4f} {elapsed:7.1f}")

    hou.setFrame(FRAME)
    bbox = hou.BoundingBox(-BOX / 2, -BOX / 2, -BOX / 2, BOX / 2, BOX / 2, BOX / 2)
    if smooth_parm:
        surface.parm(smooth_parm).set(values[0])
    hou_tools.render_preview(solver.path(), os.path.join(OUT, "022_particles.png"),
                             res=(460, 400), shading="smooth", frame_bbox=bbox)
    hou_tools.render_preview(convert.path(), os.path.join(OUT, "022_surface.png"),
                             res=(460, 400), shading="smooth", frame_bbox=bbox)

    stats = {"sep": SEP, "frame": FRAME, "particles": particles,
             "per_particle": PER_PARTICLE,
             "predicted_volume": particles * PER_PARTICLE,
             "smooth_parm": smooth_parm, "rows": rows}
    with open(os.path.join(OUT, "022_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "022_graph.json"),
                          title="実験022 — 液体に表面を張る")
    hou_tools.save_hip(os.path.join(OUT, "022_surface.hipnc"))
    print("\n保存: out/022_stats.json, out/022_graph.json, out/022_surface.hipnc")


if __name__ == "__main__":
    main()
