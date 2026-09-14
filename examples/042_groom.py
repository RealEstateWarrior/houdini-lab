"""実験042 — 毛を生やす。density と length は何を決めるのか。

新しい分野に入る。Houdini には毛（グルーム）の仕組みがあり、
<code>guide</code> で始まるノードだけで26種ある。

ただし最初の1本は <code>fur</code> で足りる。面を渡すと毛が生えてくる。
まずここの数の関係を押さえる。

  A. <code>density</code> は本数をどう決めるか。指定した数がそのまま本数になるのか
  B. 毛1本は何点でできているか
  C. <code>length</code> は純粋な倍率か（実験006・034と同じ問い）

C は否定できる形にする。長さを2倍にして、毛の長さの平均が2倍にならなければ、
<code>length</code> は単純な倍率ではない。

    hython examples/042_groom.py
    hython examples/042_groom.py shot thin
    hython examples/042_groom.py shot thick
"""

import json
import os
import sys
import time

import hou
import numpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SHOT_RES = (620, 620)
BBOX_PATH = os.path.join(OUT, "042_bbox.json")


def build(density=100, length=0.5, radius=0.1, seed=0):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "groom")

    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)            # Polygon Mesh（rows/cols が効く型。実験030）
    skin.parm("rows").set(40)
    skin.parm("cols").set(40)

    # 毛は面の向きに沿って生える。N が要る（実験008・030）
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(skin)

    fur = geo.createNode("fur", "fur")
    fur.setFirstInput(normal)
    fur.parm("density").set(density)
    fur.parm("length").set(length)
    fur.parm("guideradius").set(radius)
    fur.parm("seed").set(seed)
    fur.setDisplayFlag(True)
    fur.setRenderFlag(True)

    geo.layoutChildren()
    return geo, skin, normal, fur


def strands(geometry):
    """1本ずつの長さと点数。毛はプリミティブ1つが1本。"""
    lengths, counts = [], []
    for prim in geometry.prims():
        points = [v.point().position() for v in prim.vertices()]
        counts.append(len(points))
        total = 0.0
        for i in range(len(points) - 1):
            total += (points[i + 1] - points[i]).length()
        lengths.append(total)
    return numpy.asarray(lengths), numpy.asarray(counts)


def main():
    stats = {}

    print("下ごしらえ: 何が出てくるか")
    geo, skin, normal, fur = build()
    surface = normal.geometry()
    hair = fur.geometry()
    lengths, counts = strands(hair)
    area = sum(p.intrinsicValue("measuredarea") for p in surface.prims())
    print(f"   土台の球: {len(surface.points())}点 / {len(surface.prims())}面 / "
          f"面積 {area:.5f}")
    print(f"   生えた毛: {len(hair.prims())}本 / {len(hair.points())}点")
    print(f"   毛1本の点数: {counts.min()}〜{counts.max()}"
          f"（平均 {counts.mean():.2f}）")
    stats["skin"] = {"points": len(surface.points()),
                     "prims": len(surface.prims()), "area": float(area)}
    stats["first"] = {"hairs": len(hair.prims()), "points": len(hair.points()),
                      "seg_min": int(counts.min()), "seg_max": int(counts.max())}

    print("\nA. density は本数をどう決めるか")
    rows = []
    print(f"   {'density':>9} {'本数':>8} {'density との比':>16} "
          f"{'面積あたり':>12} {'秒':>7}")
    for density in (50, 100, 200, 400):
        start = time.perf_counter()
        geo, skin, normal, fur = build(density=density)
        made = fur.geometry()
        seconds = time.perf_counter() - start
        row = {"density": density, "hairs": len(made.prims()),
               "ratio": len(made.prims()) / density,
               "per_area": len(made.prims()) / area,
               "seconds": seconds}
        rows.append(row)
        print(f"   {density:>9} {row['hairs']:>8} {row['ratio']:>15.3f} "
              f"{row['per_area']:>12.3f} {seconds:>7.2f}")
    stats["density"] = rows
    ratios = [r["ratio"] for r in rows]
    steady = (max(ratios) - min(ratios)) / numpy.mean(ratios) < 0.05
    print(f"   本数 ÷ density はほぼ一定か: {'はい' if steady else 'いいえ'}"
          f"（{min(ratios):.3f}〜{max(ratios):.3f}）")
    print(f"   指定した数がそのまま本数になるか: "
          f"{'はい' if abs(numpy.mean(ratios) - 1) < 0.05 else 'いいえ'}")
    stats["density_linear"] = bool(steady)

    print("\nB・C. length は純粋な倍率か")
    lens = []
    print(f"   {'length':>9} {'本数':>8} {'長さの平均':>12} "
          f"{'平均÷length':>14} {'長さのばらつき':>15} {'1本の点数':>11}")
    for length in (0.125, 0.25, 0.50, 1.00):
        geo, skin, normal, fur = build(length=length)
        made = fur.geometry()
        lengths, counts = strands(made)
        row = {"length": length, "hairs": len(made.prims()),
               "mean": float(lengths.mean()),
               "ratio": float(lengths.mean() / length),
               "sd": float(lengths.std()),
               "segments": float(counts.mean())}
        lens.append(row)
        print(f"   {length:>9} {row['hairs']:>8} {row['mean']:>12.5f} "
              f"{row['ratio']:>14.5f} {row['sd']:>15.5f} "
              f"{row['segments']:>11.2f}")
    stats["length"] = lens
    r = [x["ratio"] for x in lens]
    pure = (max(r) - min(r)) < 1e-3
    print(f"   平均÷length のばらつき: {max(r) - min(r):.6f}")
    print(f"   純粋な倍率と言えるか: {'はい' if pure else 'いいえ'}")
    stats["length_pure_scale"] = bool(pure)

    with open(os.path.join(OUT, "042_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, skin, normal, fur = build()
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "042_graph.json"),
                          title="実験042 — 毛を生やす")
    hou_tools.save_hip(os.path.join(OUT, "042_groom.hipnc"))
    print("\n保存: out/042_stats.json, out/042_graph.json, out/042_groom.hipnc")


def shot(case):
    density = 60 if case == "thin" else 600
    geo, skin, normal, fur = build(density=density, length=0.5)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, skin)
    merged.setInput(1, fur)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)

    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = merged.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"042_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=SHOT_RES,
                             direction=(0.6, 0.35, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.06)
    print(f"保存: out/042_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
