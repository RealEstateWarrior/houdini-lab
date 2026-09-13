"""実験036 — 流れの向きに草を寝かせる。flowdir は何を指しているのか。

実験035では浸食のレイヤーのうち <code>sediment</code>（堆積）だけを使った。
残っているのが <code>flowdir.x</code> と <code>flowdir.y</code>、水が流れた向きである。

名前からすると「下り坂の向き」のはずだが、確かめていない。
確かめてから、草をその向きに寝かせる。

  A. flowdir は本当に下り坂を向いているか（高さの勾配と突き合わせる）
  B. その向きを N に入れると、複製は本当にその向きを向くか
  C. 向きを付けない場合と、どれだけ違うか

否定できる形にする。flowdir と下り坂の向きの角度がばらばら（平均90度前後）なら、
「flowdir は下り坂を向く」とは言えない。

    hython examples/036_flow_grass.py
    hython examples/036_flow_grass.py shot flat
    hython examples/036_flow_grass.py shot flow
"""

import json
import math
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
BLADES = 900
SHOT_RES = (820, 540)
BBOX_PATH = os.path.join(OUT, "036_bbox.json")


def build(use_flow=True, blades=BLADES):
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

    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(mesh)

    # 浸食のレイヤーを点に読む。flowdir は x と y の2枚に分かれていて、
    # 地形は水平なので、その2つが「地面の上での向き」になる。
    sample = geo.createNode("attribwrangle", "read_layers")
    sample.setFirstInput(normal)
    sample.setInput(1, erode)
    sample.parm("class").set(2)
    sample.parm("snippet").set(
        'f@layer = volumesample(1, "sediment", @P);\n'
        'float fx = volumesample(1, "flowdir.x", @P);\n'
        'float fy = volumesample(1, "flowdir.y", @P);\n'
        "f@fx = fx;\n"
        "f@fy = fy;\n"
        "// 素直に set(fx, 0, fy) と書くと下り坂を向かない（平均96.5度＝でたらめ）。\n"
        "// 8通り総当たりで測ったところ、入れ替えた set(fy, 0, fx) だけが\n"
        "// 平均39.9度まで下がる。x と y は入れ替えて使う。\n"
        "v@flowvec = set(fy, 0.0, fx);\n"
        "f@flowlen = length(v@flowvec);\n"
        "// 下り坂の向きは、高さそのものから作る。\n"
        "// normal SOP は N を点ではなくバーテックスに書くので（実験030）、\n"
        "// 点のラングルから @N を読んでも空で、当てにできない。\n"
        "float e = 2.0;\n"
        'float h0 = volumesample(1, "height", @P);\n'
        'float hx = volumesample(1, "height", @P + set(e, 0, 0));\n'
        'float hz = volumesample(1, "height", @P + set(0, 0, e));\n'
        "vector down = set(-(hx - h0), 0.0, -(hz - h0));\n"
        "f@drop = length(down);\n"
        "v@downhill = (@drop > 1e-9) ? normalize(down) : set(1, 0, 0);\n"
        "f@slope = @drop / e;")

    scatter = geo.createNode("scatter::2.0", "scatter")
    scatter.setFirstInput(sample)
    scatter.parm("npts").set(blades)

    # 草の向きを決める。copy to points はテンプレートの Z 軸を N に合わせるので、
    # N に流れの向きを入れると、草はその向きへ倒れる。
    aim = geo.createNode("attribwrangle", "aim")
    aim.setFirstInput(scatter)
    aim.parm("class").set(2)
    if use_flow:
        aim.parm("snippet").set(
            "if (length(v@flowvec) > 1e-6) {\n"
            "    @N = normalize(v@flowvec);\n"
            "} else {\n"
            "    @N = set(0, 1, 0);\n"
            "}")
    else:
        aim.parm("snippet").set("@N = set(0, 1, 0);")

    blade = geo.createNode("tube", "blade")
    blade.parm("type").set(1)
    blade.parm("rad1").set(0.35)
    blade.parm("rad2").set(0.02)
    blade.parm("height").set(7.0)
    blade.parm("rows").set(2)
    blade.parm("cols").set(6)
    blade.parm("rx").set(90)             # Z 軸向きにする（実験008）

    copies = geo.createNode("copytopoints::2.0", "copies")
    copies.setInput(0, blade)
    copies.setInput(1, aim)

    both = geo.createNode("merge", "both")
    both.setInput(0, mesh)
    both.setInput(1, copies)
    both.setDisplayFlag(True)
    both.setRenderFlag(True)

    geo.layoutChildren()
    return geo, erode, sample, scatter, aim, copies, both


def angle_between(a, b):
    """2つの向きの角度（度）。どちらも長さがある前提。"""
    na = a / numpy.linalg.norm(a)
    nb = b / numpy.linalg.norm(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(na.dot(nb))))))


def main():
    stats = {"size": SIZE, "erode": ERODE, "blades": BLADES}

    print("A. flowdir は本当に下り坂を向いているか")
    print("   （flowvec は入れ替え済みの set(fy, 0, fx)。素直な並びは下の総当たりで）")
    geo, erode, sample, scatter, aim, copies, both = build(use_flow=True)
    # convertheightfield がレイヤーを点のアトリビュートとして持ち込む。
    # 同じ名前で書こうとすると衝突するので、何が来ているか先に見ておく。
    incoming = sorted(a.name() for a in
                      sample.inputs()[0].geometry().pointAttribs())
    print(f"   メッシュが持っている点アトリビュート: {incoming}")
    stats["mesh_attribs"] = incoming
    points = sample.geometry().points()
    angles, lengths = [], []
    for point in points:
        flow = numpy.asarray(point.attribValue("flowvec"))
        down = numpy.asarray(point.attribValue("downhill"))
        length = float(numpy.linalg.norm(flow))
        lengths.append(length)
        if length < 1e-6:
            continue
        angles.append(angle_between(flow, down))
    angles = numpy.asarray(angles)
    lengths = numpy.asarray(lengths)
    print(f"   メッシュの点 {len(points)} 個のうち、流れのある点 {len(angles)} 個")
    print(f"   下り坂の向きとの角度: 平均 {angles.mean():.2f}度 / "
          f"中央 {numpy.median(angles):.2f}度")
    for limit in (30, 60, 90, 120):
        share = float((angles < limit).mean() * 100)
        print(f"     {limit}度未満: {share:5.1f}%")
    print(f"   でたらめなら平均90度になる。実測は {angles.mean():.2f}度")

    # 軸の対応（x/y をどう 3D の x/z に割り当てるか）を総当たりで試す。
    # 平均が 90度から大きく外れる組み合わせがあれば、それが正しい対応になる。
    print("\n   x/y の割り当てを8通り試す（でたらめなら どれも90度）")
    fx = numpy.asarray([p.attribValue("fx") for p in points])
    fy = numpy.asarray([p.attribValue("fy") for p in points])
    downs = numpy.asarray([p.attribValue("downhill") for p in points])
    keep = numpy.hypot(fx, fy) > 1e-6
    combos = {
        "( fx, 0,  fy)": (fx, fy), "(-fx, 0, -fy)": (-fx, -fy),
        "( fy, 0,  fx)": (fy, fx), "(-fy, 0, -fx)": (-fy, -fx),
        "( fx, 0, -fy)": (fx, -fy), "(-fx, 0,  fy)": (-fx, fy),
        "( fy, 0, -fx)": (fy, -fx), "(-fy, 0,  fx)": (-fy, fx),
    }
    combo_rows = []
    for label, (ax, az) in combos.items():
        vec = numpy.stack([ax[keep], numpy.zeros(keep.sum()), az[keep]], axis=1)
        vec /= numpy.linalg.norm(vec, axis=1, keepdims=True)
        ref = downs[keep]
        ref = ref / numpy.linalg.norm(ref, axis=1, keepdims=True)
        cos = numpy.clip((vec * ref).sum(axis=1), -1.0, 1.0)
        deg = numpy.degrees(numpy.arccos(cos))
        combo_rows.append({"combo": label, "mean": float(deg.mean()),
                           "median": float(numpy.median(deg))})
        print(f"     {label}  平均 {deg.mean():6.2f}度 / "
              f"中央 {numpy.median(deg):6.2f}度")
    stats["axis_combos"] = combo_rows
    best = min(combo_rows, key=lambda r: r["mean"])
    print(f"   一番小さいのは {best['combo']} の {best['mean']:.2f}度")
    stats["best_combo"] = best

    stats["flow_vs_downhill"] = {
        "points": len(points), "with_flow": int(len(angles)),
        "mean": float(angles.mean()), "median": float(numpy.median(angles)),
        "under30": float((angles < 30).mean() * 100),
        "under90": float((angles < 90).mean() * 100),
        "flow_len_mean": float(lengths.mean()),
    }

    print("\nB・C. 複製は、入れた向きを向くか")
    rows = []
    for label, use_flow in (("向き無し（真上）", False), ("流れの向き", True)):
        geo, erode, sample, scatter, aim, copies, both = build(
            use_flow=use_flow)
        aimed = aim.geometry()
        copied = copies.geometry()
        blade_points = len(copied.points()) // len(aimed.points())
        # 草1本の軸。tube は2つの輪でできているので、輪の重心どうしを結ぶ。
        # 並びは「後半 → 前半」が Z 軸の向きだった（最初は逆に取って
        # ぴったり180度ずれ、それで気づいた）。
        # 端の点1つずつで測ると、輪のどの点を選ぶかで向きがぶれる。
        half = blade_points // 2
        up = numpy.asarray([0.0, 1.0, 0.0])
        gaps, tilts = [], []
        for index, point in enumerate(aimed.points()):
            base = index * blade_points
            near = numpy.mean([numpy.asarray(copied.point(base + k).position())
                               for k in range(half)], axis=0)
            far = numpy.mean([numpy.asarray(copied.point(base + half + k)
                                            .position())
                              for k in range(blade_points - half)], axis=0)
            axis = near - far
            if numpy.linalg.norm(axis) < 1e-6:
                continue
            target = numpy.asarray(point.attribValue("N"))
            gaps.append(angle_between(axis, target))
            tilts.append(angle_between(axis, up))
        gaps = numpy.asarray(gaps)
        tilts = numpy.asarray(tilts)
        row = {"label": label, "use_flow": use_flow,
               "blades": int(len(gaps)),
               "gap_mean": float(gaps.mean()),
               "gap_max": float(gaps.max()),
               "tilt_mean": float(tilts.mean()),
               "tilt_std": float(tilts.std())}
        rows.append(row)
        print(f"   {label:16} 狙いとのずれ 平均 {row['gap_mean']:6.3f}度 / "
              f"最大 {row['gap_max']:6.3f}度 / "
              f"真上からの傾き 平均 {row['tilt_mean']:6.2f}度 "
              f"（ばらつき {row['tilt_std']:.2f}）")
    stats["copies"] = rows

    print(f"\n   向きを付けると、真上からの傾きが "
          f"{rows[0]['tilt_mean']:.2f}度 → {rows[1]['tilt_mean']:.2f}度")
    stats["tilt_change"] = rows[1]["tilt_mean"] - rows[0]["tilt_mean"]

    with open(os.path.join(OUT, "036_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, erode, sample, scatter, aim, copies, both = build(use_flow=True)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "036_graph.json"),
                          title="実験036 — 流れの向きに草を寝かせる")
    hou_tools.save_hip(os.path.join(OUT, "036_flow.hipnc"))
    print("\n保存: out/036_stats.json, out/036_graph.json, out/036_flow.hipnc")


def shot(case):
    geo, erode, sample, scatter, aim, copies, both = build(
        use_flow=(case == "flow"))
    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = both.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"036_{case}.png")
    hou_tools.render_preview(both.path(), png, res=SHOT_RES,
                             direction=(0.55, 0.75, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/036_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
