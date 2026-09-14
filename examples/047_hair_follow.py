"""実験047 — 土台が動いたとき、毛は付いてくるのか。

<code>hairgen::2.0</code> の入力は5つある。実験043で確かめた入力ラベルは

    0: Rest Skin or Points   1: Guides   2: Animated Skin or Points
    3: Volumes               4: Guide Interpolation Mesh

つまり<strong>「元の形」と「動いている形」を別々に渡す</strong>作りになっている。
では、動いている形をつながなかったら毛はどうなるのか。

土台の球を <code>mountain</code> で少しずつ変形させ、
毛の根元が土台の表面からどれだけ離れるかをフレームごとに測る。

  A. 動いている形をつながない場合
  B. つないだ場合
  C. 変形の大きさと、離れ方の関係

    hython examples/047_hair_follow.py measure
    hython examples/047_hair_follow.py shot loose
    hython examples/047_hair_follow.py shot follow
    python  examples/047_hair_follow.py report
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "047_stats.json")

RES = (600, 600)
GUIDES = 200
LENGTH = 0.5
DENSITY = 200
RADIUS = 0.20
THICKNESS = 0.010
FRAMES = 25
AMP = 0.5            # 最終フレームでの変形の大きさ

GUIDE_VEX = f"""
int segs = 8;
float len = {LENGTH};
int n = npoints(0);
for (int i = 0; i < n; i++) {{
    vector p = point(0, "P", i);
    vector nn = point(0, "N", i);
    if (length(nn) < 1e-6) nn = normalize(p);
    vector r = set(rand(i*3+0.11), rand(i*3+1.31), rand(i*3+2.71)) - 0.5;
    nn = normalize(nn + r * 0.6);
    int sprim; vector suv;
    xyzdist(1, p, sprim, suv);
    int prim = addprim(0, "polyline");
    setprimattrib(0, "skinprim", prim, sprim);
    setprimattrib(0, "skinprimuv", prim, suv);
    for (int s = 0; s <= segs; s++) {{
        vector q = p + nn * (len * float(s)/float(segs));
        int pt = addpoint(0, q);
        setpointattrib(0, "rest", pt, q);   // 実験044の落とし穴
        addvertex(0, prim, pt);
    }}
}}
for (int i = n - 1; i >= 0; i--) removepoint(0, i);
"""

# 毛の根元から、動いている土台の表面までの距離。
# 付いてきていれば 0 のまま。取り残されれば変形の分だけ離れる。
DIST_VEX = """
int pts[] = primpoints(0, @primnum);
vector root = point(0, "P", pts[0]);
f@rootdist = xyzdist(1, root);
"""


def build(follow):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, FRAMES)
    geo = hou.node("/obj").createNode("geo", "groom")

    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)
    skin.parm("rows").set(40)
    skin.parm("cols").set(40)
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(skin)

    # 「元の形」。ここで rest を焼いておく
    rest = geo.createNode("rest", "rest")
    rest.setFirstInput(normal)

    # 「動いている形」。rest はそのまま流れていく
    move = geo.createNode("mountain", "deform")
    move.setFirstInput(rest)
    move.parm("height").setExpression(
        f"{AMP} * ($FF - 1) / {FRAMES - 1}")
    move.parm("elementsize").set(0.9)

    roots = geo.createNode("scatter::2.0", "roots")
    roots.setFirstInput(rest)
    roots.parm("npts").set(GUIDES)
    make = geo.createNode("attribwrangle", "make_guides")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)
    make.parm("snippet").set(GUIDE_VEX)

    gen = geo.createNode("hairgen::2.0", "hairgen")
    gen.setInput(0, rest)          # Rest Skin
    gen.setInput(1, make)          # Guides
    if follow:
        gen.setInput(2, move)      # Animated Skin
    gen.parm("density").set(DENSITY)
    gen.parm("influenceradius").set(RADIUS)
    gen.parm("thickness").set(THICKNESS)

    check = geo.createNode("attribwrangle", "rootdist")
    check.setFirstInput(gen)
    check.setInput(1, move)
    check.parm("class").set(1)
    check.parm("snippet").set(DIST_VEX)
    check.setDisplayFlag(True)
    check.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, rest, move, gen, check


def measure():
    import hou
    import numpy

    stats = {"frames": FRAMES, "amp": AMP, "guides": GUIDES,
             "density": DENSITY}
    for follow in (False, True):
        key = "follow" if follow else "loose"
        geo, skin, rest, move, gen, check = build(follow)
        rows = []
        label = "つなぐ" if follow else "つながない"
        print(f"\n{label}（Animated Skin 入力）")
        print(f"   {'frame':>6} {'変形の大きさ':>12} {'毛':>8} "
              f"{'根元の離れ 平均':>16} {'最大':>10} {'0.01未満の割合':>16}")
        for frame in (1, 5, 10, 15, 20, 25):
            hou.setFrame(frame)
            g = check.geometry()
            dist = numpy.asarray([p.attribValue("rootdist")
                                  for p in g.prims()])
            height = AMP * (frame - 1) / (FRAMES - 1)
            row = {"frame": frame, "height": height, "hairs": int(len(dist)),
                   "mean": float(dist.mean()), "max": float(dist.max()),
                   "on_surface": float((dist < 0.01).mean() * 100)}
            rows.append(row)
            print(f"   {frame:>6} {height:>12.5f} {len(dist):>8,} "
                  f"{dist.mean():>16.6f} {dist.max():>10.6f} "
                  f"{row['on_surface']:>15.1f}%")
        stats[key] = rows

    last_loose = stats["loose"][-1]
    last_follow = stats["follow"][-1]
    print(f"\n最終フレームの根元の離れ:")
    print(f"   つながない: {last_loose['mean']:.6f}")
    print(f"   つなぐ:     {last_follow['mean']:.6f}")
    stats["works"] = bool(last_follow["mean"] < last_loose["mean"] / 10)
    print(f"   付いてくると言えるか: {'はい' if stats['works'] else 'いいえ'}")
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print(f"\n保存: out/047_stats.json")


def shot(case):
    import hou
    import hou_tools
    geo, skin, rest, move, gen, check = build(case != "loose")
    hou.setFrame(1 if case == "start" else FRAMES)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, move)
    merged.setInput(1, check)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)

    r = 1.0 + AMP + LENGTH + 0.1
    bbox = hou.BoundingBox(-r, -r, -r, r, r, r)
    png = os.path.join(OUT, f"047_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.6, 0.35, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/047_{case}.png")


def scene():
    import hou
    import hou_tools
    geo, skin, rest, move, gen, check = build(True)
    hou.setFrame(FRAMES)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "047_graph.json"),
                          title="実験047 — 土台に毛を付いてこさせる")
    hou_tools.save_hip(os.path.join(OUT, "047_hair_follow.hipnc"))
    print("保存: out/047_graph.json, out/047_hair_follow.hipnc")


def report():
    with open(STATS, encoding="utf-8") as fp:
        stats = json.load(fp)
    for key, label in (("loose", "つながない"), ("follow", "つなぐ")):
        print(f"\n{label}")
        print(f"   {'frame':>6} {'変形の大きさ':>12} {'根元の離れ 平均':>16} "
              f"{'最大':>10} {'表面にいる割合':>16}")
        for r in stats[key]:
            print(f"   {r['frame']:>6} {r['height']:>12.5f} "
                  f"{r['mean']:>16.6f} {r['max']:>10.6f} "
                  f"{r['on_surface']:>15.1f}%")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "measure":
        measure()
    elif cmd == "shot":
        shot(sys.argv[2])
    elif cmd == "scene":
        scene()
    else:
        report()
