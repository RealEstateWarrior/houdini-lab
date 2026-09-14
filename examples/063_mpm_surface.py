"""実験063 — MPM の粒を面に戻す。元の体積に戻るか。

実験061・062で、MPM は物を<strong>粒の集まり</strong>として持つと分かった。
ただし粒のままではレンダできない。<code>mpmsurface</code> で面に戻す。

ここで確かめられることがある。<strong>体積1.0 の箱を粒にして、面に戻したら、
また 1.0 になるか。</strong>往復させれば、どれだけ痩せる（太る）かが分かる。

実験059で obj の往復を測ったのと同じ考え方で、今度は形式ではなく
「粒を経由すること」で何が変わるかを見る。

  A. 箱（体積 1.0）→ 粒 → 面。体積はいくつになるか
  B. 面の細かさ（voxelscale）を変えると、体積と重さはどう変わるか
  C. 粒の間隔を変えると、どうなるか

    hython examples/063_mpm_surface.py
    hython examples/063_mpm_surface.py shot coarse
    hython examples/063_mpm_surface.py shot fine
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "063_stats.json")

RES = (620, 620)
BOX = 1.0
SEP = 0.1
SCALES = (2.0, 1.5, 1.0, 0.75, 0.5)
SEPS = (0.16, 0.12, 0.10, 0.08)


def build(sep=SEP, scale=None, size=BOX, method=None):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 2)
    geo = hou.node("/obj").createNode("geo", "mpm")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((size, size, size))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(sep)
    container.parm("sizex").set(4.0)
    container.parm("sizey").set(4.0)
    container.parm("sizez").set(4.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    surface = geo.createNode("mpmsurface", "surface")
    surface.setInput(0, source)
    # 既定は Surface VDB。面が欲しいので polygonmesh に変える
    surface.parm("outputtype").set("polygonmesh")
    if scale is not None:
        surface.parm("voxelscale").set(scale)
    if method is not None:
        surface.parm("surfacingmethod").set(method)
    # mpmsurface が出すのは polysoup（1プリミティブに全部の面が入る）。
    # 体積を面ごとに足したいので、ふつうのポリゴンに割る。
    split = geo.createNode("convert", "to_polygons")
    split.setFirstInput(surface)
    split.parm("totype").set("poly")
    split.setDisplayFlag(True)
    split.setRenderFlag(True)
    geo.layoutChildren()
    return geo, box, container, source, split


def volume_of(node):
    """面から体積を出す（実験052と同じやり方）。"""
    import numpy
    g = node.geometry()
    if g is None:
        return None
    total = 0.0
    for prim in g.prims():
        pts = [v.point().position() for v in prim.vertices()]
        if len(pts) < 3:
            continue
        a = numpy.asarray([pts[0][0], pts[0][1], pts[0][2]])
        for i in range(1, len(pts) - 1):
            b = numpy.asarray([pts[i][0], pts[i][1], pts[i][2]])
            c = numpy.asarray([pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]])
            total += float(numpy.dot(a, numpy.cross(b, c))) / 6.0
    return abs(total)


def main():
    stats = {"box": BOX, "sep": SEP}

    geo, box, container, source, surface = build()
    box_volume = volume_of(box)
    particles = len(source.geometry().points())
    print(f"元の箱: 1辺 {BOX} / 体積 {box_volume:.6f}")
    print(f"粒にすると: {particles:,}個（間隔 {SEP}）")
    stats["box_volume"] = box_volume
    stats["particles"] = particles

    print("\nA・B. 面の細かさ（voxelscale）を変える")
    print(f"   {'voxelscale':>11} {'点':>9} {'面':>9} {'体積':>12} "
          f"{'元との比':>10} {'秒':>8}")
    rows = []
    for scale in SCALES:
        geo, box, container, source, surface = build(scale=scale)
        start = time.perf_counter()
        g = surface.geometry()
        seconds = time.perf_counter() - start
        vol = volume_of(surface)
        rows.append({"scale": scale, "points": len(g.points()),
                     "prims": len(g.prims()), "volume": vol,
                     "ratio": vol / box_volume, "seconds": seconds})
        print(f"   {scale:>11} {len(g.points()):>9,} {len(g.prims()):>9,} "
              f"{vol:>12.6f} {vol / box_volume:>10.4f} {seconds:>7.2f}秒")
    stats["scales"] = rows
    ratios = [r["ratio"] for r in rows]
    print(f"   比の幅: {min(ratios):.4f} 〜 {max(ratios):.4f}")
    print(f"   細かくすると 1 に近づくか: "
          f"{'はい' if abs(ratios[-1] - 1) < abs(ratios[0] - 1) else 'いいえ'}")

    print("\nC. 粒の間隔を変える（voxelscale は既定）")
    print(f"   {'間隔':>8} {'粒':>9} {'点':>9} {'面':>9} {'体積':>12} "
          f"{'元との比':>10}")
    srows = []
    for sep in SEPS:
        geo, box, container, source, surface = build(sep=sep)
        pts = len(source.geometry().points())
        g = surface.geometry()
        vol = volume_of(surface)
        srows.append({"sep": sep, "particles": pts,
                      "points": len(g.points()), "prims": len(g.prims()),
                      "volume": vol, "ratio": vol / box_volume})
        print(f"   {sep:>8} {pts:>9,} {len(g.points()):>9,} "
              f"{len(g.prims()):>9,} {vol:>12.6f} "
              f"{vol / box_volume:>10.4f}")
    stats["seps"] = srows

    # 面は粒の外側を包むので、元の箱より一回り大きくなるはず。
    # 1辺が 1 + 2d に太ったと考えて d を出し、粒の間隔との比を見る。
    print(f"\n   膨らんだ厚み d（(1+2d)³ = 体積 として逆算）")
    print(f"   {'間隔':>8} {'元との比':>10} {'1 + 2d':>10} {'d':>10} "
          f"{'d ÷ 間隔':>10}")
    for r in srows:
        side = r["ratio"] ** (1.0 / 3.0)
        d = (side - 1.0) / 2.0
        r["thickness"] = d
        r["thickness_ratio"] = d / r["sep"]
        print(f"   {r['sep']:>8} {r['ratio']:>10.4f} {side:>10.5f} "
              f"{d:>10.5f} {d / r['sep']:>10.4f}")
    ratios = [r["thickness_ratio"] for r in srows]
    print(f"   d ÷ 間隔 の幅: {min(ratios):.4f} 〜 {max(ratios):.4f}")
    stats["thickness_ratio"] = [min(ratios), max(ratios)]

    print("\nD. 面の作り方を変える（ふつうの方法と、機械学習の方法）")
    print(f"   {'やり方':>22} {'点':>9} {'面':>9} {'体積':>12} "
          f"{'元との比':>10} {'秒':>8}")
    methods = []
    labels = {"vdbfromparticles": "VDB from Particles",
              "neuralpointsurfacing": "Neural Point Surface"}
    for method in ("vdbfromparticles", "neuralpointsurfacing"):
        geo, box, container, source, surface = build(method=method)
        start = time.perf_counter()
        try:
            g = surface.geometry()
            seconds = time.perf_counter() - start
            vol = volume_of(surface)
            methods.append({"method": method, "points": len(g.points()),
                            "prims": len(g.prims()), "volume": vol,
                            "ratio": vol / box_volume,
                            "seconds": seconds})
            print(f"   {labels[method]:>22} {len(g.points()):>9,} "
                  f"{len(g.prims()):>9,} {vol:>12.6f} "
                  f"{vol / box_volume:>10.4f} {seconds:>7.2f}秒")
        except Exception as exc:  # noqa: BLE001
            methods.append({"method": method,
                            "error": str(exc).replace("\n", " ")[:80]})
            print(f"   {labels[method]:>22} 失敗: "
                  f"{str(exc).replace(chr(10), ' ')[:60]}")
        for msg in surface.errors()[:1]:
            print(f"      {msg.replace(chr(10), ' ')[:120]}")
    stats["methods"] = methods

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    import hou_tools
    geo, box, container, source, surface = build(scale=0.75)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "063_graph.json"),
                          title="実験063 — MPM の粒を面に戻す")
    hou_tools.save_hip(os.path.join(OUT, "063_mpm_surface.hipnc"))
    print("\n保存: out/063_stats.json, out/063_graph.json, "
          "out/063_mpm_surface.hipnc")


def shot(case):
    import hou
    import hou_tools
    scale = 2.0 if case == "coarse" else 0.5
    geo, box, container, source, surface = build(scale=scale)
    bbox = hou.BoundingBox(-0.8, -0.8, -0.8, 0.8, 0.8, 0.8)
    png = os.path.join(OUT, f"063_{case}.png")
    hou_tools.render_preview(surface.path(), png, res=RES,
                             direction=(0.5, 0.35, 1.0),
                             shading="smoothwire",
                             frame_bbox=bbox, margin=1.05)
    print(f"保存: out/063_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
