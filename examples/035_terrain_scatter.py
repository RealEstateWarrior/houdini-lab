"""実験035 — 地形の上に生やし分ける。浸食が残した情報は使えるか。

実験008では平らな地面に木を200本立てた。どこに立てるかは完全に運任せで、
地形の形とは関係がなかった。

実験034で、浸食が<strong>過程をレイヤーとして残す</strong>ことが分かった。
がれき・堆積・流れ。これを「どこに生やすか」に使えるなら、
<strong>崖には生えず、土が溜まったところに生える</strong>地形が自動で作れる。

確かめること。

  A. 浸食のレイヤーは、地形のどこに値を持っているか（勾配との関係）
  B. レイヤーで重みを付けて散布すると、生える場所は本当に偏るか
  C. 重み無しの散布と比べて、どれだけ違うか

否定できる形にする。重みを付けた散布と付けない散布で、生えた場所の
勾配の分布が同じなら、レイヤーは効いていない。

    hython examples/035_terrain_scatter.py
    hython examples/035_terrain_scatter.py shot plain
    hython examples/035_terrain_scatter.py shot masked
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
TREES = 600
SHOT_RES = (820, 540)
BBOX_PATH = os.path.join(OUT, "035_bbox.json")


def build(masked=True, layer_name="sediment", trees=TREES):
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

    # 面の向きを作る。これが無いと複製が回らない（実験008・030）。
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(mesh)

    # 浸食のレイヤーを、メッシュの点のアトリビュートとして持ってくる。
    # ボリュームの値をその点の位置で読むだけ。
    sample = geo.createNode("attribwrangle", "read_layer")
    sample.setFirstInput(normal)
    sample.setInput(1, erode)
    sample.parm("class").set(2)          # 点
    sample.parm("snippet").set(
        f'f@layer = volumesample(1, "{layer_name}", @P);\n'
        "// 勾配も点ごとに持たせる。あとで「どこに生えたか」を測るのに使う\n"
        "vector up = set(0, 1, 0);\n"
        "f@slope = 1.0 - abs(dot(normalize(@N), up));")

    scatter = geo.createNode("scatter::2.0", "scatter")
    scatter.setFirstInput(sample)
    scatter.parm("npts").set(trees)
    if masked:
        # 密度に使うアトリビュートを指定する。値の大きいところほど多く置かれる。
        for name in ("usedensityattrib", "useattribtoscaledensity"):
            parm = scatter.parm(name)
            if parm is not None:
                parm.set(True)
        for name in ("densityattrib", "attribtoscaledensity"):
            parm = scatter.parm(name)
            if parm is not None:
                parm.set("layer")

    tree = geo.createNode("tube", "tree")
    tree.parm("type").set(1)             # Polygon
    tree.parm("rad1").set(0.6)
    tree.parm("rad2").set(0.05)
    tree.parm("height").set(6.0)
    tree.parm("rows").set(2)
    tree.parm("cols").set(8)
    # copy to points はテンプレートの Z 軸を N に合わせる（実験008）
    tree.parm("rx").set(90)

    copies = geo.createNode("copytopoints::2.0", "copies")
    copies.setInput(0, tree)
    copies.setInput(1, scatter)

    both = geo.createNode("merge", "both")
    both.setInput(0, mesh)
    both.setInput(1, copies)
    both.setDisplayFlag(True)
    both.setRenderFlag(True)

    geo.layoutChildren()
    return geo, erode, sample, scatter, copies, both


def layer_grid(geometry, name):
    for prim in geometry.prims():
        if prim.attribValue("name") == name:
            res = prim.resolution()
            values = numpy.asarray(prim.allVoxels(), dtype=numpy.float64)
            return values.reshape(res[2], res[1], res[0])[0]
    return None


def point_values(node, names):
    geometry = node.geometry()
    out = {name: [] for name in names}
    for point in geometry.points():
        for name in names:
            out[name].append(point.attribValue(name))
    return {name: numpy.asarray(values) for name, values in out.items()}


def where_scattered(scatter_node, mesh_node):
    """散布点が乗っている場所の勾配とレイヤー値を集める。

    scatter は元の点のアトリビュートを引き継ぐので、そのまま読める。
    """
    geometry = scatter_node.geometry()
    slope, layer = [], []
    has_slope = geometry.findPointAttrib("slope") is not None
    has_layer = geometry.findPointAttrib("layer") is not None
    for point in geometry.points():
        if has_slope:
            slope.append(point.attribValue("slope"))
        if has_layer:
            layer.append(point.attribValue("layer"))
    return numpy.asarray(slope), numpy.asarray(layer)


def main():
    stats = {"size": SIZE, "spacing": SPACING, "amp": AMP,
             "erode": ERODE, "trees": TREES}

    print("A. 浸食のレイヤーは、地形のどこに値を持っているか")
    geo, erode, sample, scatter, copies, both = build(masked=True)
    eroded = erode.geometry()
    names = [p.attribValue("name") for p in eroded.prims()]
    print(f"   レイヤー: {names}")
    fields = {}
    for name in names:
        grid = layer_grid(eroded, name)
        if grid is None:
            continue
        fields[name] = {"min": float(grid.min()), "max": float(grid.max()),
                        "mean": float(grid.mean()),
                        "nonzero": float((grid > 1e-6).mean() * 100)}
    print(f"   {'レイヤー':>12} {'最小':>10} {'最大':>10} {'平均':>10} "
          f"{'値のあるマス':>12}")
    for name, row in fields.items():
        print(f"   {name:>12} {row['min']:>10.4f} {row['max']:>10.4f} "
              f"{row['mean']:>10.4f} {row['nonzero']:>11.1f}%")
    stats["layers"] = fields

    # メッシュの点ごとに、勾配とレイヤー値の関係を見る
    values = point_values(sample, ["slope", "layer"])
    slope, layer = values["slope"], values["layer"]
    steep = slope > numpy.median(slope)
    print(f"\n   メッシュの点 {len(slope)} 個で、勾配の中央値で2つに分ける")
    print(f"   急なほう: レイヤーの平均 {layer[steep].mean():.5f}")
    print(f"   緩いほう: レイヤーの平均 {layer[~steep].mean():.5f}")
    if layer[steep].mean() > 0:
        print(f"   緩いほうが {layer[~steep].mean() / layer[steep].mean():.2f}倍 多い")
    stats["layer_vs_slope"] = {
        "points": int(len(slope)),
        "steep_mean": float(layer[steep].mean()),
        "flat_mean": float(layer[~steep].mean()),
    }

    print("\nB・C. 重みを付けた散布と、付けない散布を比べる")
    rows = []
    print(f"   {'':10} {'点の数':>8} {'勾配の平均':>12} {'勾配の中央':>12} "
          f"{'レイヤーの平均':>14}")
    for label, masked in (("重み無し", False), ("重みあり", True)):
        geo, erode, sample, scatter, copies, both = build(masked=masked)
        s, l = where_scattered(scatter, sample)
        row = {"label": label, "masked": masked, "count": int(len(s)),
               "slope_mean": float(s.mean()) if len(s) else None,
               "slope_median": float(numpy.median(s)) if len(s) else None,
               "layer_mean": float(l.mean()) if len(l) else None}
        rows.append(row)
        print(f"   {label:10} {len(s):>8} {row['slope_mean']:>12.5f} "
              f"{row['slope_median']:>12.5f} {row['layer_mean']:>14.5f}")
    stats["scatter"] = rows

    plain, masked = rows[0], rows[1]
    if plain["slope_mean"]:
        change = (masked["slope_mean"] - plain["slope_mean"]) \
            / plain["slope_mean"] * 100
        print(f"\n   重みを付けると、生えた場所の勾配の平均が {change:+.1f}%")
        stats["slope_change_percent"] = change
    if plain["layer_mean"]:
        lift = masked["layer_mean"] / plain["layer_mean"]
        print(f"   レイヤーの値の平均は {lift:.2f}倍")
        stats["layer_lift"] = lift
    stats["works"] = (masked["slope_mean"] < plain["slope_mean"])
    print(f"   緩いところに寄ったか: {'はい' if stats['works'] else 'いいえ'}")

    with open(os.path.join(OUT, "035_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, erode, sample, scatter, copies, both = build(masked=True)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "035_graph.json"),
                          title="実験035 — 地形の上に生やし分ける")
    hou_tools.save_hip(os.path.join(OUT, "035_scatter.hipnc"))
    print("\n保存: out/035_stats.json, out/035_graph.json, "
          "out/035_scatter.hipnc")


def shot(case):
    geo, erode, sample, scatter, copies, both = build(masked=(case == "masked"))
    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = both.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"035_{case}.png")
    hou_tools.render_preview(both.path(), png, res=SHOT_RES,
                             direction=(0.8, 0.42, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/035_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
