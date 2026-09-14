"""実験048 — 毛を揺らす。Vellum で毛は伸びるのか、伸びないのか。

毛はここまで「生やす」「束ねる」「色を付ける」「土台に付いてこさせる」と進めてきた。
今回は動かす。<code>vellumconstraints</code> の種類に <strong>Hair</strong> があり、
これでカーブを毛として扱える。根元は <code>pin</code> で土台に留める。

このシリーズで毎回やっているのと同じ問いを立てる。<strong>保たれるはずの量は何か。</strong>
毛は伸び縮みしないはずなので、<strong>毛の長さ</strong>がそれにあたる。

  A. 重力だけで垂らす。毛先はどこまで落ちるか
  B. 毛の長さは何フレーム経っても保たれるか
  C. <code>bendstiffness</code>（曲がりにくさ）を変えると垂れ方はどう変わるか

    hython examples/048_hair_sim.py measure
    hython examples/048_hair_sim.py stiff
    hython examples/048_hair_sim.py shot start
    hython examples/048_hair_sim.py shot fall
    python  examples/048_hair_sim.py report
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "048_stats.json")

RES = (620, 620)
GUIDES = 120
LENGTH = 0.6
DENSITY = 50
RADIUS = 0.25
THICKNESS = 0.012
LAST = 48
BEND = 0.05

GUIDE_VEX = f"""
int segs = 10;
float len = {LENGTH};
int n = npoints(0);
for (int i = 0; i < n; i++) {{
    vector p = point(0, "P", i);
    vector nn = point(0, "N", i);
    if (length(nn) < 1e-6) nn = normalize(p);
    int sprim; vector suv;
    xyzdist(1, p, sprim, suv);
    int prim = addprim(0, "polyline");
    setprimattrib(0, "skinprim", prim, sprim);
    setprimattrib(0, "skinprimuv", prim, suv);
    for (int s = 0; s <= segs; s++) {{
        vector q = p + nn * (len * float(s)/float(segs));
        int pt = addpoint(0, q);
        setpointattrib(0, "rest", pt, q);
        addvertex(0, prim, pt);
    }}
}}
for (int i = n - 1; i >= 0; i--) removepoint(0, i);
"""

# 毛の根元（各カーブの最初の点）だけを留める。
# vellumconstraints の「Pin to Target」は思ったように効かなかったので、
# Vellum が見る stopped アトリビュートを直接立てる。
ROOT_VEX = """
int pts[] = primpoints(0, @primnum);
setpointgroup(0, "roots", pts[0], 1);
setpointattrib(0, "stopped", pts[0], 1);
"""


def build(bend=BEND, last=LAST, domass=True):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "hairsim")

    skin = geo.createNode("sphere", "skin")
    skin.parm("type").set(2)
    skin.parm("rows").set(30)
    skin.parm("cols").set(30)
    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(skin)
    rest = geo.createNode("rest", "rest")
    rest.setFirstInput(normal)

    roots = geo.createNode("scatter::2.0", "roots")
    roots.setFirstInput(rest)
    roots.parm("npts").set(GUIDES)
    make = geo.createNode("attribwrangle", "make_guides")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)
    make.parm("snippet").set(GUIDE_VEX)

    gen = geo.createNode("hairgen::2.0", "hairgen")
    gen.setInput(0, rest)
    gen.setInput(1, make)
    gen.parm("density").set(DENSITY)
    gen.parm("influenceradius").set(RADIUS)
    gen.parm("thickness").set(THICKNESS)

    mark = geo.createNode("attribwrangle", "mark_roots")
    mark.setFirstInput(gen)
    mark.parm("class").set(1)
    mark.parm("snippet").set(ROOT_VEX)

    hair = geo.createNode("vellumconstraints", "hair")
    hair.setFirstInput(mark)
    hair.parm("constrainttype").set("hair")
    hair.parm("bendstiffness").set(bend)
    # 「質量を計算する」は既定でオフ。オフのままだと mass が -1、
    # 逆数の w が 0 になり、全部の点が動かない状態になる。
    hair.parm("domass").set(1 if domass else 0)

    pin = hair

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, hair, 0)
    solver.setInput(1, hair, 1)
    solver.parm("startframe").set(1)

    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, rest, gen, pin, solver


def curve_stats(geometry):
    import numpy
    lengths, tips, straight = [], [], []
    for prim in geometry.prims():
        pts = [v.point().position() for v in prim.vertices()]
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            total += (b - a).length()
        lengths.append(total)
        tips.append([pts[-1][0], pts[-1][1], pts[-1][2]])
        # まっすぐさ。根元から毛先までの直線距離 ÷ 毛の長さ。
        # 1 なら一直線、小さいほど曲がっている。
        straight.append((pts[-1] - pts[0]).length() / total if total else 0.0)
    lengths = numpy.asarray(lengths)
    tips = numpy.asarray(tips)
    straight = numpy.asarray(straight)
    return {
        "hairs": int(len(lengths)),
        "len_mean": float(lengths.mean()),
        "len_sd": float(lengths.std()),
        "len_min": float(lengths.min()),
        "len_max": float(lengths.max()),
        "tip_y_mean": float(tips[:, 1].mean()),
        "tip_r_mean": float(numpy.sqrt((tips ** 2).sum(axis=1)).mean()),
        "straight": float(straight.mean()),
        "straight_min": float(straight.min()),
    }


def measure():
    import hou
    geo, skin, rest, gen, pin, solver = build()
    start = curve_stats(pin.geometry())
    print(f"止まっている毛: {start['hairs']:,}本 / "
          f"長さ {start['len_mean']:.6f}")
    print("\nA・B. 重力だけで垂らす")
    print(f"   {'frame':>6} {'毛先の高さ 平均':>16} {'中心からの距離':>16} "
          f"{'長さの平均':>12} {'長さのばらつき':>14} {'最大 ÷ 最初':>12} "
          f"{'秒':>7}")
    rows = []
    t0 = time.perf_counter()
    for frame in (1, 4, 8, 12, 18, 24, 36, 48):
        hou.setFrame(frame)
        solver.cook(force=True)
        info = curve_stats(solver.geometry())
        info["frame"] = frame
        info["len_ratio"] = info["len_mean"] / start["len_mean"]
        info["seconds"] = time.perf_counter() - t0
        rows.append(info)
        print(f"   {frame:>6} {info['tip_y_mean']:>16.6f} "
              f"{info['tip_r_mean']:>16.6f} {info['len_mean']:>12.6f} "
              f"{info['len_sd']:>14.6f} "
              f"{info['len_max'] / start['len_max']:>12.6f} "
              f"{info['seconds']:>7.1f}")
    worst = max(abs(r["len_ratio"] - 1.0) for r in rows)
    print(f"\n   長さの最大のずれ: {worst * 100:.4f}%")
    print(f"   長さは保たれたか: {'はい' if worst < 0.01 else 'いいえ'}")
    drop = start["tip_y_mean"] - rows[-1]["tip_y_mean"]
    print(f"   毛先の平均の高さ: {start['tip_y_mean']:.6f} → "
          f"{rows[-1]['tip_y_mean']:.6f}（{drop:+.6f}）")
    stats = {"guides": GUIDES, "density": DENSITY, "length": LENGTH,
             "bend": BEND, "last": LAST, "start": start, "frames": rows,
             "len_worst": worst, "len_kept": bool(worst < 0.01),
             "tip_drop": drop}
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as fp:
            stats = {**json.load(fp), **stats}
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/048_stats.json")


def stiff():
    import hou
    print("C. bendstiffness を変えると垂れ方はどう変わるか（最終フレーム）")
    print(f"   {'bendstiffness':>14} {'毛先の高さ 平均':>16} "
          f"{'中心からの距離':>16} {'まっすぐさ':>12} "
          f"{'いちばん曲がった毛':>18} {'長さのずれ':>12}")
    rows = []
    for bend in (0.0, 0.05, 1.0, 100.0, 10000.0, 1000000.0):
        geo, skin, rest, gen, pin, solver = build(bend=bend)
        start = curve_stats(pin.geometry())
        hou.setFrame(LAST)
        info = curve_stats(solver.geometry())
        info["bend"] = bend
        info["len_ratio"] = info["len_mean"] / start["len_mean"]
        rows.append(info)
        print(f"   {bend:>14} {info['tip_y_mean']:>16.6f} "
              f"{info['tip_r_mean']:>16.6f} {info['straight']:>12.6f} "
              f"{info['straight_min']:>18.6f} "
              f"{(info['len_ratio'] - 1) * 100:>11.4f}%")
    stats = {}
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as fp:
            stats = json.load(fp)
    stats["stiffness"] = rows
    higher = rows[-1]["tip_y_mean"] > rows[0]["tip_y_mean"]
    print(f"   固くすると毛先は高い位置に残るか: {'はい' if higher else 'いいえ'}")
    stats["stiff_holds"] = bool(higher)
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)


def shot(case):
    import hou
    import hou_tools
    geo, skin, rest, gen, pin, solver = build()
    hou.setFrame(1 if case == "start" else LAST)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, skin)
    merged.setInput(1, solver)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)

    r = 1.0 + LENGTH + 0.15
    bbox = hou.BoundingBox(-r, -r - 0.2, -r, r, r, r)
    png = os.path.join(OUT, f"048_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.6, 0.25, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/048_{case}.png")


def scene():
    import hou
    import hou_tools
    geo, skin, rest, gen, pin, solver = build()
    hou.setFrame(LAST)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "048_graph.json"),
                          title="実験048 — 毛を揺らす")
    hou_tools.save_hip(os.path.join(OUT, "048_hair_sim.hipnc"))
    print("保存: out/048_graph.json, out/048_hair_sim.hipnc")


def report():
    with open(STATS, encoding="utf-8") as fp:
        stats = json.load(fp)
    print("A・B. 重力だけで垂らす")
    print(f"   {'frame':>6} {'毛先の高さ 平均':>16} {'中心からの距離':>16} "
          f"{'長さの平均':>12} {'長さのばらつき':>14}")
    for r in stats["frames"]:
        print(f"   {r['frame']:>6} {r['tip_y_mean']:>16.6f} "
              f"{r['tip_r_mean']:>16.6f} {r['len_mean']:>12.6f} "
              f"{r['len_sd']:>14.6f}")
    print(f"   長さの最大のずれ: {stats['len_worst'] * 100:.4f}%")
    if "stiffness" in stats:
        print("\nC. bendstiffness")
        print(f"   {'bendstiffness':>14} {'毛先の高さ 平均':>16} "
              f"{'中心からの距離':>16} {'長さの平均':>12}")
        for r in stats["stiffness"]:
            print(f"   {r['bend']:>14} {r['tip_y_mean']:>16.6f} "
                  f"{r['tip_r_mean']:>16.6f} {r['len_mean']:>12.6f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "measure":
        measure()
    elif cmd == "stiff":
        stiff()
    elif cmd == "shot":
        shot(sys.argv[2])
    elif cmd == "scene":
        scene()
    else:
        report()
