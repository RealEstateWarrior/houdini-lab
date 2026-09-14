"""実験044 — つないだのに、ガイドが1本も使われていなかった。

実験043でガイドを自作して <code>hairgen::2.0</code> につないだ。毛は 12,516本出た。
ところが今回、<strong>ガイドの向きをばらばらに傾けても、毛先が小数点以下5桁まで
1ミリも動かなかった</strong>。本数も束の数も同じ。ガイドを 100本にしても 900本にしても同じ。

つまり<strong>ガイドは1本も使われていなかった</strong>。エラーも警告も出ない。

原因は <code>influenceradius</code>（既定 0.05）。
ガイドはこの半径の中にいる毛にしか効かない。半径1の球に300本なら間隔は約0.2で、
どの毛もガイドから遠い。そして <code>growunguided</code>（既定 オン）が、
拾われなかった毛を <code>unguidedlength</code>（既定 0.05）の短い毛として生やす。

  A. <code>growunguided</code> を切る。残った本数＝ガイドに拾われた毛の数
  B. <code>influenceradius</code> を上げると、拾われる割合はどう変わるか
  C. 毛の長さで見分ける（拾われていない毛は 0.05、ガイドに従えば 0.5）
  D. ガイドの向きをばらす。半径を上げたときだけ追従するか
  E. clumpid の正体（ちゃんと導かれた毛で測り直す）

    hython examples/044_influence.py
    hython examples/044_influence.py shot ignored
    hython examples/044_influence.py shot guided
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
CLUMPSIZE = 0.4
DEFAULT_RADIUS = 0.05
SHOT_RES = (620, 620)
BBOX_PATH = os.path.join(OUT, "044_bbox.json")

GUIDE_VEX = f"""
int segs = {SEGMENTS};
float len = {LENGTH};
float jitter = __JITTER__;
int n = npoints(0);
for (int i = 0; i < n; i++) {{
    vector p = point(0, "P", i);
    vector nn = point(0, "N", i);
    if (length(nn) < 1e-6) nn = normalize(p);
    // ガイドごとに向きをばらす。0 なら全部まっすぐ外向き
    if (jitter > 0) {{
        vector r = set(rand(i * 3 + 0.11), rand(i * 3 + 1.31),
                       rand(i * 3 + 2.71)) - 0.5;
        nn = normalize(nn + r * jitter);
    }}
    int sprim; vector suv;
    xyzdist(1, p, sprim, suv);
    int prim = addprim(0, "polyline");
    setprimattrib(0, "skinprim", prim, sprim);
    setprimattrib(0, "skinprimuv", prim, suv);
    for (int s = 0; s <= segs; s++) {{
        vector q = p + nn * (len * float(s) / float(segs));
        int pt = addpoint(0, q);
        // ここが要。addpoint で作った点の rest は (0,0,0) のまま。
        // hairgen は rest 空間で距離を測るので、直さないとガイドは
        // 全部が原点にあることになり、どの毛にも届かない。
        __REST__
        addvertex(0, prim, pt);
    }}
}}
for (int i = n - 1; i >= 0; i--) removepoint(0, i);
"""

COLOR_VEX = """
int cid = @clumpid;
vector c = set(rand(cid * 3 + 0.1), rand(cid * 3 + 1.7), rand(cid * 3 + 2.3));
c = 0.25 + 0.75 * c;
int pts[] = primpoints(0, @primnum);
foreach (int pt; pts) {
    setpointattrib(0, "Cd", pt, c);
}
"""


def build(radius=DEFAULT_RADIUS, guides=GUIDES, density=DENSITY,
          jitter=0.0, unguided=True, clump=False, color=False,
          fix_rest=True):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "groom")

    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)
    skin.parm("rows").set(40)
    skin.parm("cols").set(40)

    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(skin)

    rest = geo.createNode("rest", "rest")
    rest.setFirstInput(normal)

    roots = geo.createNode("scatter::2.0", "roots")
    roots.setFirstInput(rest)
    roots.parm("npts").set(guides)

    make = geo.createNode("attribwrangle", "make_guides")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)
    snippet = GUIDE_VEX.replace("__JITTER__", repr(jitter))
    snippet = snippet.replace(
        "__REST__", 'setpointattrib(0, "rest", pt, q);' if fix_rest else "")
    make.parm("snippet").set(snippet)

    gen = geo.createNode("hairgen::2.0", "hairgen")
    gen.setInput(0, rest)        # Rest Skin or Points
    gen.setInput(1, make)        # Guides
    gen.parm("density").set(density)
    gen.parm("influenceradius").set(radius)
    gen.parm("growunguided").set(1 if unguided else 0)

    last = gen
    if clump:
        node = geo.createNode("hairclump::2.0", "clump")
        node.setInput(0, gen)    # Guides（＝毛）
        node.setInput(1, rest)   # Skin
        node.parm("clumpsize").set(CLUMPSIZE)
        last = node
        if color:
            tint = geo.createNode("attribwrangle", "tint")
            tint.setFirstInput(node)
            tint.parm("class").set(1)
            tint.parm("snippet").set(COLOR_VEX)
            last = tint

    last.setDisplayFlag(True)
    last.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, rest, make, gen, last


def curve_lengths(geometry):
    out = []
    for prim in geometry.prims():
        pts = [v.point().position() for v in prim.vertices()]
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            total += (b - a).length()
        out.append(total)
    return numpy.asarray(out)


def tips_of(geometry):
    return numpy.asarray([[v for v in p.vertices()[-1].point().position()]
                          for p in geometry.prims()])


def roots_of(geometry):
    return numpy.asarray([[v for v in p.vertices()[0].point().position()]
                          for p in geometry.prims()])


def neighbour_purity(points, ids, limit=1400):
    if len(points) > limit:
        step = len(points) // limit + 1
        points, ids = points[::step], ids[::step]
    diff = points[:, None, :] - points[None, :, :]
    dist = numpy.sqrt((diff ** 2).sum(axis=2))
    numpy.fill_diagonal(dist, numpy.inf)
    nearest = dist.argmin(axis=1)
    same = (ids[nearest] == ids)
    clumps = len(numpy.unique(ids))
    return {"checked": int(len(ids)), "same": int(same.sum()),
            "rate": float(same.mean()),
            "clumps_in_sample": int(clumps),
            "if_random": 1.0 / clumps}


def main():
    stats = {"guides": GUIDES, "density": DENSITY, "length": LENGTH,
             "default_radius": DEFAULT_RADIUS}

    print("A. rest を直す前と後")
    print(f"   {'rest':>10} {'ばらつき':>10} {'毛':>10} {'長さの平均':>12} "
          f"{'長さの最大':>12} {'毛先の広がり':>14}")
    arows = []
    for fix in (False, True):
        for jitter in (0.0, 1.2):
            geo, skin, rest, make, gen, last = build(jitter=jitter,
                                                     fix_rest=fix)
            g = last.geometry()
            lens = curve_lengths(g)
            tips = tips_of(g)
            row = {"fix_rest": fix, "jitter": jitter,
                   "hairs": len(g.prims()),
                   "len_mean": float(lens.mean()),
                   "len_max": float(lens.max()),
                   "tip_spread": float(tips.std(axis=0).mean())}
            arows.append(row)
            print(f"   {'直した' if fix else '(0,0,0)':>10} {jitter:>10} "
                  f"{row['hairs']:>10,} {row['len_mean']:>12.5f} "
                  f"{row['len_max']:>12.5f} {row['tip_spread']:>14.5f}")
    stats["rest_fix"] = arows
    before = abs(arows[1]["tip_spread"] - arows[0]["tip_spread"])
    after = abs(arows[3]["tip_spread"] - arows[2]["tip_spread"])
    print(f"   直す前、ガイドをばらしたときの毛先の差: {before:.6f}")
    print(f"   直した後、ガイドをばらしたときの毛先の差: {after:.6f}")
    print(f"   ガイドが効くようになったか: "
          f"{'はい' if after > 1e-4 and before < 1e-9 else 'いいえ'}")
    stats["rest_fix_works"] = bool(after > 1e-4 and before < 1e-9)

    print("\nB. influenceradius を上げると、ガイドに拾われる毛はどう増えるか")
    print(f"   {'半径':>8} {'全部の毛':>10} {'拾われた毛':>12} {'割合':>9} "
          f"{'長さの平均':>12} {'長さの最大':>12}")
    rows = []
    for radius in (0.05, 0.10, 0.20, 0.40, 0.80):
        # growunguided を切る。残るのはガイドに拾われた毛だけ
        geo, skin, rest, make, gen, last = build(radius=radius,
                                                 unguided=False)
        taken = len(last.geometry().prims())
        geo, skin, rest, make, gen, last = build(radius=radius,
                                                 unguided=True)
        g = last.geometry()
        total = len(g.prims())
        lens = curve_lengths(g)
        row = {"radius": radius, "total": total, "taken": taken,
               "rate": taken / total if total else 0.0,
               "len_mean": float(lens.mean()),
               "len_max": float(lens.max())}
        rows.append(row)
        print(f"   {radius:>8} {total:>10,} {taken:>12,} "
              f"{row['rate'] * 100:>8.1f}% {row['len_mean']:>12.5f} "
              f"{row['len_max']:>12.5f}")
    stats["radius"] = rows
    print(f"   ガイドの長さは {LENGTH}、unguidedlength の既定は 0.05")

    print("\nC. clumpid の正体（ガイドに導かれた毛で測る）")
    geo, skin, rest, make, gen, last = build(radius=0.40, clump=True)
    g = last.geometry()
    ids = numpy.asarray([p.attribValue("clumpid") for p in g.prims()])
    hair_ids = numpy.asarray([p.attribValue("id") for p in g.prims()])
    uniq = numpy.unique(ids)
    tidy = bool(uniq[0] == 0 and len(uniq) == uniq[-1] - uniq[0] + 1)
    inside = int(numpy.isin(uniq, hair_ids).sum())
    lookup = {int(v): int(i) for i, v in enumerate(hair_ids)}
    leader = sum(1 for v in uniq
                 if int(v) in lookup and ids[lookup[int(v)]] == v)
    print(f"   毛 {len(ids):,}本 / 束 {len(uniq)}個")
    print(f"   番号の範囲: {int(uniq.min())} 〜 {int(uniq.max())}")
    print(f"   0 から連番か: {'はい' if tidy else 'いいえ'}")
    print(f"   番号が毛の id の中にあるか: {inside} / {len(uniq)}")
    print(f"   その id の毛自身が同じ束にいるか: {leader} / {len(uniq)}")
    pur = neighbour_purity(roots_of(g), ids)
    print(f"   ばらばらなら、隣が同じ束になる率は "
          f"{pur['if_random'] * 100:.2f}%（1 ÷ {pur['clumps_in_sample']}）")
    print(f"   実際: {pur['same']} / {pur['checked']} = "
          f"{pur['rate'] * 100:.2f}%")
    stats["clumpid"] = {"hairs": int(len(ids)), "clumps": int(len(uniq)),
                        "id_min": int(uniq.min()), "id_max": int(uniq.max()),
                        "sequential": tidy, "id_in_hairids": inside,
                        "leader_in_own_clump": leader, "purity": pur}

    with open(os.path.join(OUT, "044_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, skin, rest, make, gen, last = build(radius=0.40, clump=True,
                                             color=True)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "044_graph.json"),
                          title="実験044 — influenceradius")
    hou_tools.save_hip(os.path.join(OUT, "044_influence.hipnc"))
    print("\n保存: out/044_stats.json, out/044_graph.json, "
          "out/044_influence.hipnc")


def shot(case):
    # ignored: rest が (0,0,0) のまま（ガイドが1本も使われない）
    # guided:  rest を直した（ガイドどおりに毛が伸びる）
    geo, skin, rest, make, gen, last = build(radius=0.20, jitter=1.2,
                                             fix_rest=(case == "guided"))
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

    png = os.path.join(OUT, f"044_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=SHOT_RES,
                             direction=(0.6, 0.35, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.06)
    print(f"保存: out/044_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
