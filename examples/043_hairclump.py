"""実験043 — 毛を束ねる。つなぐ順番と、要る属性。

実験042では <code>fur</code> で手早く毛を生やした。ただし <code>fur</code> の出力は
<code>N</code> と <code>P</code> しか持っていない。束ねる <code>hairclump</code> につなぐと
<strong>「Couldn't find skinprim attribute.」</strong>で止まる。

グルームの道具は「この毛は土台のどの面から生えたか」を知りたがる。
それが <code>skinprim</code> という番号で、<code>fur</code> はこれを出さない。

そこで<strong>ガイドを自分で組んだ</strong>。散らした点から1本ずつ線を伸ばし、
<code>xyzdist</code> で一番近い面の番号を調べて <code>skinprim</code> に入れる。

そこでもう一度つまずいた。<strong>つなぐ順番が逆だった。</strong>

  A. 入力の順番はどちらが正しいか（総当たりで決める）
  B. 束ねると何が付くか。<code>clumpsize</code> で束の数はどう変わるか
  C. 毛先は本当に寄るのか（いちばん近い毛先までの距離）

    hython examples/043_hairclump.py
    hython examples/043_hairclump.py shot loose
    hython examples/043_hairclump.py shot clumped
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

GUIDES = 300
SEGMENTS = 8
LENGTH = 0.5
DENSITY = 1000
SHOT_RES = (620, 620)
BBOX_PATH = os.path.join(OUT, "043_bbox.json")

GUIDE_VEX = f"""
int segs = {SEGMENTS};
float len = {LENGTH};
int n = npoints(0);
for (int i = 0; i < n; i++) {{
    vector p = point(0, "P", i);
    vector nn = point(0, "N", i);
    if (length(nn) < 1e-6) nn = normalize(p);
    // 一番近い面の番号を調べて、ガイドに覚えさせる。
    // グルームの道具はこの番号（skinprim）が無いと動かない。
    int sprim; vector suv;
    xyzdist(1, p, sprim, suv);
    int prim = addprim(0, "polyline");
    setprimattrib(0, "skinprim", prim, sprim);
    setprimattrib(0, "skinprimuv", prim, suv);
    for (int s = 0; s <= segs; s++) {{
        int pt = addpoint(0, p + nn * (len * float(s) / float(segs)));
        addvertex(0, prim, pt);
    }}
}}
// 元の散布点は要らないので消す
for (int i = n - 1; i >= 0; i--) removepoint(0, i);
"""


def build(clump=True, clumpsize=0.2, density=DENSITY, guides=GUIDES):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "groom")

    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)
    skin.parm("rows").set(40)
    skin.parm("cols").set(40)

    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(skin)

    # rest（元の位置）が無いと、土台として受け付けてもらえない
    rest = geo.createNode("rest", "rest")
    rest.setFirstInput(normal)

    roots = geo.createNode("scatter::2.0", "roots")
    roots.setFirstInput(rest)
    roots.parm("npts").set(guides)

    make = geo.createNode("attribwrangle", "make_guides")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)            # ディテール（1回だけ走る）
    make.parm("snippet").set(GUIDE_VEX)

    gen = geo.createNode("hairgen::2.0", "hairgen")
    # 順番に注意。土台が先、ガイドが後
    gen.setInput(0, rest)
    gen.setInput(1, make)
    gen.parm("density").set(density)

    last = gen
    node = None
    if clump:
        node = geo.createNode("hairclump::2.0", "clump")
        # こちらは逆。毛が先、土台が後
        node.setInput(0, gen)
        node.setInput(1, rest)
        node.parm("clumpsize").set(clumpsize)
        last = node

    last.setDisplayFlag(True)
    last.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, rest, make, gen, node, last


def tips(geometry):
    out = []
    for prim in geometry.prims():
        verts = prim.vertices()
        if verts:
            p = verts[-1].point().position()
            out.append([p[0], p[1], p[2]])
    return numpy.asarray(out)


def nearest_spacing(points, limit=1500):
    """いちばん近い相手までの距離。束になれば小さくなるはず。"""
    if len(points) > limit:
        step = len(points) // limit + 1
        points = points[::step]
    diff = points[:, None, :] - points[None, :, :]
    dist = numpy.sqrt((diff ** 2).sum(axis=2))
    numpy.fill_diagonal(dist, numpy.inf)
    nearest = dist.min(axis=1)
    return {"count": int(len(points)), "mean": float(nearest.mean()),
            "median": float(numpy.median(nearest)),
            "sd": float(nearest.std())}


def clump_counts(geometry):
    if geometry.findPrimAttrib("clumpid") is None:
        return None
    ids = numpy.asarray([p.attribValue("clumpid") for p in geometry.prims()])
    values, counts = numpy.unique(ids, return_counts=True)
    return {"clumps": int(len(values)),
            "per_clump_mean": float(counts.mean()),
            "per_clump_max": int(counts.max()),
            "per_clump_min": int(counts.min())}


def order_test():
    """入力の順番を総当たりで決める。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "order")
    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)
    skin.parm("rows").set(40)
    skin.parm("cols").set(40)
    normal = geo.createNode("normal", "n")
    normal.setFirstInput(skin)
    rest = geo.createNode("rest", "rest")
    rest.setFirstInput(normal)
    roots = geo.createNode("scatter::2.0", "roots")
    roots.setFirstInput(rest)
    roots.parm("npts").set(GUIDES)
    make = geo.createNode("attribwrangle", "make")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)
    make.parm("snippet").set(GUIDE_VEX)

    rows = []
    for label, first, second in (("土台 → ガイド", rest, make),
                                 ("ガイド → 土台", make, rest)):
        node = geo.createNode("hairgen::2.0",
                              "hg_" + ("a" if first is rest else "b"))
        node.setInput(0, first)
        node.setInput(1, second)
        node.parm("density").set(DENSITY)
        try:
            g = node.geometry()
            made = None if g is None else len(g.prims())
        except hou.Error:
            made = None
        rows.append({"node": "hairgen", "order": label,
                     "hairs": made,
                     "error": (node.errors()[0].splitlines()[0][:60]
                               if node.errors() else "")})

    good = geo.createNode("hairgen::2.0", "hg_ok")
    good.setInput(0, rest)
    good.setInput(1, make)
    good.parm("density").set(DENSITY)
    for label, first, second in (("毛 → 土台", good, rest),
                                 ("土台 → 毛", rest, good)):
        node = geo.createNode("hairclump::2.0",
                              "cl_" + ("a" if first is good else "b"))
        node.setInput(0, first)
        node.setInput(1, second)
        node.parm("clumpsize").set(0.2)
        try:
            g = node.geometry()
            made = None if g is None else len(g.prims())
        except hou.Error:
            made = None
        rows.append({"node": "hairclump", "order": label,
                     "hairs": made,
                     "error": (node.errors()[0].splitlines()[0][:60]
                               if node.errors() else "")})
    return rows


def clump_spread():
    """束1つの太さを測る。毛先が「どこに集まるか」ではなく「どれだけ広がっているか」。

    C で clumpsize 0.8 が 0.2 より広がったのはなぜか、を数字で確かめるため。
    """
    print(f"   {'clumpsize':>10} {'束の数':>8} {'束の根元の広がり':>16} "
          f"{'束の毛先の広がり':>16} {'毛先÷根元':>11}")
    rows = []
    for size in (0.05, 0.10, 0.20, 0.40, 0.80):
        geo, skin, rest, make, gen, node, last = build(clump=True,
                                                       clumpsize=size)
        g = last.geometry()
        groups = {}
        for prim in g.prims():
            cid = prim.attribValue("clumpid")
            verts = prim.vertices()
            root = verts[0].point().position()
            tip = verts[-1].point().position()
            groups.setdefault(cid, []).append(
                ([root[0], root[1], root[2]], [tip[0], tip[1], tip[2]]))
        root_spread, tip_spread = [], []
        for cid, pairs in groups.items():
            if len(pairs) < 2:
                continue
            roots = numpy.asarray([p[0] for p in pairs])
            ts = numpy.asarray([p[1] for p in pairs])
            root_spread.append(
                float(numpy.sqrt(((roots - roots.mean(axis=0)) ** 2)
                                 .sum(axis=1)).mean()))
            tip_spread.append(
                float(numpy.sqrt(((ts - ts.mean(axis=0)) ** 2)
                                 .sum(axis=1)).mean()))
        rs = float(numpy.mean(root_spread))
        ts_ = float(numpy.mean(tip_spread))
        rows.append({"clumpsize": size, "clumps": len(groups),
                     "root_spread": rs, "tip_spread": ts_,
                     "ratio": ts_ / rs})
        print(f"   {size:>10} {len(groups):>8} {rs:>16.5f} "
              f"{ts_:>16.5f} {ts_ / rs:>11.3f}")
    path = os.path.join(OUT, "043_stats.json")
    with open(path, encoding="utf-8") as fp:
        stats = json.load(fp)
    stats["clump_spread"] = rows
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n追記: out/043_stats.json")


def main():
    stats = {"guides": GUIDES, "density": DENSITY, "length": LENGTH}

    print("A. 入力の順番を総当たりで決める")
    orders = order_test()
    print(f"   {'ノード':>12} {'つなぎ方':>14} {'出てきた本数':>14} {'エラー'}")
    for row in orders:
        made = "—" if row["hairs"] is None else f"{row['hairs']:,}"
        print(f"   {row['node']:>12} {row['order']:>14} {made:>14} "
              f"{row['error']}")
    stats["orders"] = orders

    print("\nB. 束ねると何が付くか")
    geo, skin, rest, make, gen, node, last = build(clump=False)
    loose = gen.geometry()
    loose_attribs = sorted(a.name() for a in loose.primAttribs())
    loose_space = nearest_spacing(tips(loose))
    guide_count = len(make.geometry().prims())
    hair_count = len(loose.prims())
    print(f"   ガイド: {guide_count}本 → "
          f"毛: {hair_count}本（{hair_count / GUIDES:.1f}倍）")
    print(f"   束ねる前のアトリビュート: {loose_attribs}")

    geo, skin, rest, make, gen, node, last = build(clump=True)
    clumped = last.geometry()
    clumped_attribs = sorted(a.name() for a in clumped.primAttribs())
    added = [a for a in clumped_attribs if a not in loose_attribs]
    print(f"   束ねた後のアトリビュート: {clumped_attribs}")
    print(f"   増えたのは: {added}")
    stats["loose_attribs"] = loose_attribs
    stats["added_attribs"] = added
    stats["hairs"] = hair_count
    stats["guides_made"] = guide_count
    stats["guide_to_hair"] = hair_count / GUIDES

    print("\n   clumpsize を変えると、束の数はどう変わるか")
    rows = []
    print(f"   {'clumpsize':>10} {'束の数':>8} {'1束の本数':>11} "
          f"{'いちばん大きい束':>16}")
    for size in (0.05, 0.10, 0.20, 0.40, 0.80):
        geo, skin, rest, make, gen, node, last = build(clump=True,
                                                       clumpsize=size)
        info = clump_counts(last.geometry())
        row = dict(info or {})
        row["clumpsize"] = size
        rows.append(row)
        print(f"   {size:>10} {info['clumps']:>8} "
              f"{info['per_clump_mean']:>11.2f} {info['per_clump_max']:>16}")
    stats["clumpsize"] = rows
    fewer = rows[-1]["clumps"] < rows[0]["clumps"]
    print(f"   clumpsize を上げると束の数は減るか: {'はい' if fewer else 'いいえ'}")
    stats["fewer_clumps"] = fewer

    print("\nC. 毛先は本当に寄るのか")
    spaces = [{"label": "束ねない", "clumpsize": None, **loose_space}]
    print(f"   {'':14} {'測った毛先':>10} {'いちばん近い毛先まで':>20} "
          f"{'中央値':>10}")
    print(f"   {'束ねない':14} {loose_space['count']:>10} "
          f"{loose_space['mean']:>20.5f} {loose_space['median']:>10.5f}")
    for size in (0.05, 0.20, 0.80):
        geo, skin, rest, make, gen, node, last = build(clump=True,
                                                       clumpsize=size)
        space = nearest_spacing(tips(last.geometry()))
        space["label"] = f"clumpsize {size}"
        space["clumpsize"] = size
        spaces.append(space)
        print(f"   {space['label']:14} {space['count']:>10} "
              f"{space['mean']:>20.5f} {space['median']:>10.5f}")
    stats["spacing"] = spaces

    tight = spaces[-1]
    drop = (loose_space["mean"] - tight["mean"]) / loose_space["mean"] * 100
    print(f"\n   束ねると、いちばん近い毛先までの距離が {drop:.1f}% 縮んだ")
    print(f"   寄ったと言えるか: {'はい' if drop > 10 else 'いいえ'}")
    stats["spacing_drop_percent"] = drop
    stats["tips_gather"] = drop > 10

    with open(os.path.join(OUT, "043_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, skin, rest, make, gen, node, last = build(clump=True)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "043_graph.json"),
                          title="実験043 — 毛を束ねる")
    hou_tools.save_hip(os.path.join(OUT, "043_clump.hipnc"))
    print("\n保存: out/043_stats.json, out/043_graph.json, out/043_clump.hipnc")


def shot(case):
    geo, skin, rest, make, gen, node, last = build(clump=(case == "clumped"),
                                                   clumpsize=0.40)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, skin)
    merged.setInput(1, last)
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

    png = os.path.join(OUT, f"043_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=SHOT_RES,
                             direction=(0.6, 0.35, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.06)
    print(f"保存: out/043_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "spread":
        print("D. 束1つはどれだけ広がっているか")
        clump_spread()
    else:
        main()
