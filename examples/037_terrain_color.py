"""実験037 — 浸食のレイヤーで地形を塗り分ける。色は情報を持っているか。

実験034で、浸食が過程をレイヤーとして残すことが分かった。
実験035では <code>sediment</code> を散布の重みに、036では <code>flowdir</code> を向きに使った。
今回は<strong>色</strong>にする。

  岩肌 … 土が流れ去って何も溜まっていないところ
  土　 … 堆積が積もったところ
  水筋 … 水が集まって流れたところ

見た目を作るだけなら、適当に塗っても絵にはなる。そうではなく、
<strong>塗り分けが地形の形と対応しているか</strong>を数字で確かめる。

  A. どのレイヤーを、どのしきい値で分けるか（値の分布を見て決める）
  B. 分けた3つは、勾配で見て本当に別のものか
  C. 色を付けたあと、割合はどうなるか

否定できる形にする。3つの勾配の平均がどれも同じなら、
塗り分けは地形の形と無関係で、ただの模様である。

    hython examples/037_terrain_color.py
    hython examples/037_terrain_color.py shot plain
    hython examples/037_terrain_color.py shot color
"""

import json
import os
import sys

import hou
import numpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SIZE = 200.0
SPACING = 2.0
AMP = 120.0
ELEMENT = 80.0
ERODE = 4
SHOT_RES = (860, 560)
BBOX_PATH = os.path.join(OUT, "037_bbox.json")

# しきい値は A で分布を見てから決める。ここは決めた結果。
SOIL = 0.30            # sediment がこれ以上なら「土」
WATER = 1.60           # flow がこれ以上なら「水筋」


def build(colored=True):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 2)
    geo = hou.node("/obj").createNode("geo", "terrain")

    field = geo.createNode("heightfield", "field")
    field.parm("sizex").set(SIZE)
    field.parm("sizey").set(SIZE)
    field.parm("gridspacing").set(SPACING)

    noise = geo.createNode("heightfield_noise", "noise")
    noise.setFirstInput(field)
    noise.parm("amp").set(AMP)
    noise.parm("elementsize").set(ELEMENT)

    erode = geo.createNode("heightfield_erode", "erode")
    erode.setFirstInput(noise)
    erode.parm("iterations").set(ERODE)

    mesh = geo.createNode("convertheightfield", "mesh")
    mesh.setFirstInput(erode)

    # 勾配は高さから直接作る。normal SOP の N はバーテックスに付くので
    # 点のラングルからは読めない（実験030・036）。
    paint = geo.createNode("attribwrangle", "paint")
    paint.setFirstInput(mesh)
    paint.setInput(1, erode)
    paint.parm("class").set(2)
    body = (
        'f@sediment2 = volumesample(1, "sediment", @P);\n'
        'f@flow2 = volumesample(1, "flow", @P);\n'
        'f@debris2 = volumesample(1, "debris", @P);\n'
        "float e = 2.0;\n"
        'float h0 = volumesample(1, "height", @P);\n'
        'float hx = volumesample(1, "height", @P + set(e, 0, 0));\n'
        'float hz = volumesample(1, "height", @P + set(0, 0, e));\n'
        "f@slope = length(set(hx - h0, 0.0, hz - h0)) / e;\n"
        f"int water = (@flow2 >= {WATER}) ? 1 : 0;\n"
        f"int soil  = (@sediment2 >= {SOIL}) ? 1 : 0;\n"
        "i@kind = water ? 2 : (soil ? 1 : 0);\n"
    )
    if colored:
        body += (
            "// 0=岩肌（灰）1=土（茶）2=水筋（青）\n"
            "vector rock = set(0.62, 0.60, 0.58);\n"
            "vector soilc = set(0.45, 0.32, 0.18);\n"
            "vector waterc = set(0.20, 0.38, 0.55);\n"
            "@Cd = (@kind == 2) ? waterc : ((@kind == 1) ? soilc : rock);\n")
    else:
        body += "@Cd = set(0.72, 0.72, 0.72);\n"
    paint.parm("snippet").set(body)
    paint.setDisplayFlag(True)
    paint.setRenderFlag(True)

    geo.layoutChildren()
    return geo, erode, mesh, paint


def layer_values(geometry, name):
    for prim in geometry.prims():
        if prim.attribValue("name") == name:
            return numpy.asarray(prim.allVoxels(), dtype=numpy.float64)
    return None


def main():
    stats = {"size": SIZE, "erode": ERODE, "soil": SOIL, "water": WATER}

    print("A. しきい値を決めるために、値の分布を見る")
    geo, erode, mesh, paint = build(colored=True)
    eroded = erode.geometry()
    rows = []
    for name in ("sediment", "flow", "debris"):
        values = layer_values(eroded, name)
        qs = numpy.percentile(values, [10, 25, 50, 75, 90])
        rows.append({"layer": name, "min": float(values.min()),
                     "max": float(values.max()),
                     "p10": float(qs[0]), "p25": float(qs[1]),
                     "p50": float(qs[2]), "p75": float(qs[3]),
                     "p90": float(qs[4])})
        print(f"   {name:10} 最小 {values.min():7.4f} / 最大 {values.max():8.4f}")
        print(f"   {'':10} 下から 10% {qs[0]:7.4f} / 25% {qs[1]:7.4f} / "
              f"50% {qs[2]:7.4f} / 75% {qs[3]:7.4f} / 90% {qs[4]:7.4f}")
    stats["distribution"] = rows
    print(f"   → 土のしきい値は sediment {SOIL}、水筋は flow {WATER} にした")

    print("\nB. 分けた3つは、勾配で見て別のものか")
    points = paint.geometry().points()
    kind = numpy.asarray([p.attribValue("kind") for p in points])
    slope = numpy.asarray([p.attribValue("slope") for p in points])
    sediment = numpy.asarray([p.attribValue("sediment2") for p in points])
    flow = numpy.asarray([p.attribValue("flow2") for p in points])

    labels = {0: "岩肌", 1: "土", 2: "水筋"}
    table = []
    print(f"   {'種類':>6} {'点の数':>8} {'割合':>8} {'勾配の平均':>12} "
          f"{'勾配の中央':>12} {'堆積の平均':>12} {'流れの平均':>12}")
    for key in (0, 1, 2):
        pick = kind == key
        if not pick.any():
            continue
        row = {"kind": labels[key], "count": int(pick.sum()),
               "share": float(pick.mean() * 100),
               "slope_mean": float(slope[pick].mean()),
               "slope_median": float(numpy.median(slope[pick])),
               "sediment_mean": float(sediment[pick].mean()),
               "flow_mean": float(flow[pick].mean())}
        table.append(row)
        print(f"   {labels[key]:>6} {row['count']:>8} {row['share']:>7.1f}% "
              f"{row['slope_mean']:>12.5f} {row['slope_median']:>12.5f} "
              f"{row['sediment_mean']:>12.5f} {row['flow_mean']:>12.5f}")
    stats["classes"] = table

    rock = next(r for r in table if r["kind"] == "岩肌")
    soil = next(r for r in table if r["kind"] == "土")
    ratio = rock["slope_mean"] / soil["slope_mean"] if soil["slope_mean"] else 0
    print(f"\n   岩肌は土の {ratio:.2f}倍 急")
    stats["rock_over_soil"] = ratio
    stats["separates"] = ratio > 1.2

    print("\nC. 色を付けた結果")
    colored = paint.geometry()
    cds = numpy.asarray([p.attribValue("Cd") for p in colored.points()])
    uniq = {tuple(numpy.round(c, 4)) for c in cds}
    print(f"   点 {len(cds)} 個 / 使われた色 {len(uniq)} 種")
    for color in sorted(uniq):
        share = float((numpy.abs(cds - numpy.asarray(color)).sum(axis=1)
                       < 1e-4).mean() * 100)
        print(f"     {color}  {share:5.1f}%")
    stats["colors"] = len(uniq)

    with open(os.path.join(OUT, "037_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "037_graph.json"),
                          title="実験037 — 浸食のレイヤーで塗り分ける")
    hou_tools.save_hip(os.path.join(OUT, "037_color.hipnc"))
    print("\n保存: out/037_stats.json, out/037_graph.json, out/037_color.hipnc")


def shot(case):
    geo, erode, mesh, paint = build(colored=(case == "color"))
    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = paint.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"037_{case}.png")
    hou_tools.render_preview(paint.path(), png, res=SHOT_RES,
                             direction=(0.7, 0.5, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/037_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
