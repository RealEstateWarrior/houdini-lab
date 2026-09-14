"""実験049 — 毛に風を当てる。流され方は風速に比例するのか。

実験029で、粒に当てる <code>popwind</code> は<strong>二次の抵抗</strong>
（dv/dt = a(W−v)²）だと突き止めた。毛の場合はどうか。

毛は伸びないので、流される量には上限がある。根元から毛先までの距離は
どんなに強い風でも毛の長さ（0.596）を超えられない。
つまり<strong>比例するはずがなく、どこかで頭打ちになる</strong>。
問題はその近づき方で、2つの候補を先に立てる。

    一次の抵抗なら   s = W / (W + k)
    二次の抵抗なら   s = W² / (W² + k²)

s は「流され具合」＝（毛先の x − 根元の x）÷ 毛の長さ。
6通りの風速で測り、どちらの式によく乗るかを見る。

  A. 風速を変えて、流され具合を測る
  B. 2つの式にあてはめて、残差を比べる
  C. 長さは保たれるか（実験048と同じ保存量）

    hython examples/049_hair_wind.py measure
    hython examples/049_hair_wind.py shot calm
    hython examples/049_hair_wind.py shot windy
    python  examples/049_hair_wind.py report
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "049_stats.json")

RES = (620, 620)
GUIDES = 120
LENGTH = 0.6
DENSITY = 50
RADIUS = 0.25
THICKNESS = 0.012
LAST = 48
BEND = 0.05
SPEEDS = (0.0, 2.0, 5.0, 10.0, 20.0, 40.0)

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

# 根元を留める。実験048で、Pin to Target は効かず
# stopped アトリビュートを直接立てるのが正解だと分かった。
ROOT_VEX = """
int pts[] = primpoints(0, @primnum);
setpointgroup(0, "roots", pts[0], 1);
setpointattrib(0, "stopped", pts[0], 1);
"""


def build(speed, last=LAST):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "hairwind")

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
    hair.parm("bendstiffness").set(BEND)
    hair.parm("domass").set(1)       # 既定はオフ（実験048）

    solver = geo.createNode("vellumsolver", "solve")
    solver.setInput(0, hair, 0)
    solver.setInput(1, hair, 1)
    solver.parm("startframe").set(1)
    if speed > 0:
        solver.parm("dowind").set(1)
        solver.parm("windx").set(1.0)
        solver.parm("windy").set(0.0)
        solver.parm("windz").set(0.0)
        solver.parm("windspeed").set(speed)

    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, skin, hair, solver


def stats_of(geometry):
    import numpy
    lengths, push, tips = [], [], []
    for prim in geometry.prims():
        pts = [v.point().position() for v in prim.vertices()]
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            total += (b - a).length()
        lengths.append(total)
        # 流され具合。風は +x 向きなので、毛先が根元よりどれだけ x 側にいるか
        push.append((pts[-1][0] - pts[0][0]) / total if total else 0.0)
        tips.append([pts[-1][0], pts[-1][1], pts[-1][2]])
    lengths = numpy.asarray(lengths)
    push = numpy.asarray(push)
    tips = numpy.asarray(tips)
    return {"hairs": int(len(lengths)),
            "len_mean": float(lengths.mean()),
            "push": float(push.mean()),
            "push_sd": float(push.std()),
            "tip_x": float(tips[:, 0].mean()),
            "tip_y": float(tips[:, 1].mean())}


def fit(speeds, values, kind):
    """s = W/(W+k) か s = W²/(W²+k²) に、k を総当たりで合わせる。"""
    best = None
    for i in range(1, 20001):
        k = i * 0.01
        err = 0.0
        for w, v in zip(speeds, values):
            if kind == "linear":
                pred = w / (w + k)
            else:
                pred = (w * w) / (w * w + k * k)
            err += (pred - v) ** 2
        if best is None or err < best[1]:
            best = (k, err)
    k, err = best
    preds = [(w / (w + k)) if kind == "linear"
             else (w * w) / (w * w + k * k) for w in speeds]
    worst = max(abs(p - v) for p, v in zip(preds, values))
    return {"k": k, "sse": err, "rmse": math.sqrt(err / len(values)),
            "worst": worst, "pred": preds}


def measure():
    import hou
    rows = []
    print("A. 風速を変えて、流され具合を測る")
    print(f"   {'風速':>8} {'毛':>8} {'流され具合':>12} {'ばらつき':>10} "
          f"{'毛先の x':>10} {'毛先の高さ':>12} {'長さの平均':>12}")
    for speed in SPEEDS:
        geo, skin, hair, solver = build(speed)
        start = stats_of(hair.geometry())
        hou.setFrame(LAST)
        info = stats_of(solver.geometry())
        info["speed"] = speed
        info["len_ratio"] = info["len_mean"] / start["len_mean"]
        rows.append(info)
        print(f"   {speed:>8} {info['hairs']:>8,} {info['push']:>12.6f} "
              f"{info['push_sd']:>10.6f} {info['tip_x']:>10.6f} "
              f"{info['tip_y']:>12.6f} {info['len_mean']:>12.6f}")

    # 風速 0 のときの値を差し引いて、「風で動いた分」だけを見る
    base = rows[0]["push"]
    speeds = [r["speed"] for r in rows if r["speed"] > 0]
    values = [(r["push"] - base) / (1.0 - base) for r in rows
              if r["speed"] > 0]
    print(f"\n   風速0のときの流され具合: {base:.6f}（これを 0 とみなす）")

    print("\nB. 2つの式にあてはめる")
    linear = fit(speeds, values, "linear")
    square = fit(speeds, values, "square")
    print(f"   {'風速':>8} {'実測':>12} {'一次 W/(W+k)':>16} "
          f"{'二次 W²/(W²+k²)':>18}")
    for w, v, a, b in zip(speeds, values, linear["pred"], square["pred"]):
        print(f"   {w:>8} {v:>12.6f} {a:>16.6f} {b:>18.6f}")
    print(f"   一次: k = {linear['k']:.2f} / "
          f"残差の二乗和 {linear['sse']:.6f} / 最大のずれ {linear['worst']:.4f}")
    print(f"   二次: k = {square['k']:.2f} / "
          f"残差の二乗和 {square['sse']:.6f} / 最大のずれ {square['worst']:.4f}")
    better = "二次" if square["sse"] < linear["sse"] else "一次"
    ratio = (max(linear["sse"], square["sse"])
             / max(min(linear["sse"], square["sse"]), 1e-12))
    print(f"   よく乗るのは: {better}（残差の比 {ratio:.1f}倍）")

    worst_len = max(abs(r["len_ratio"] - 1.0) for r in rows)
    print(f"\nC. 長さの最大のずれ: {worst_len * 100:.4f}%")

    out = {"speeds": list(SPEEDS), "rows": rows, "base": base,
           "norm": values, "linear": linear, "square": square,
           "better": better, "sse_ratio": ratio, "len_worst": worst_len}
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/049_stats.json")


def shot(case):
    import hou
    import hou_tools
    speed = 0.0 if case == "calm" else 40.0
    geo, skin, hair, solver = build(speed)
    hou.setFrame(LAST)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, skin)
    merged.setInput(1, solver)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)

    r = 1.0 + LENGTH + 0.15
    bbox = hou.BoundingBox(-r, -r - 0.2, -r, r + 0.2, r, r)
    png = os.path.join(OUT, f"049_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.0, 0.25, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/049_{case}.png")


def scene():
    import hou
    import hou_tools
    geo, skin, hair, solver = build(20.0)
    hou.setFrame(LAST)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "049_graph.json"),
                          title="実験049 — 毛に風を当てる")
    hou_tools.save_hip(os.path.join(OUT, "049_hair_wind.hipnc"))
    print("保存: out/049_graph.json, out/049_hair_wind.hipnc")


def report():
    with open(STATS, encoding="utf-8") as fp:
        s = json.load(fp)
    print("A. 風速を変えて、流され具合を測る")
    print(f"   {'風速':>8} {'流され具合':>12} {'毛先の x':>10} "
          f"{'毛先の高さ':>12} {'長さの平均':>12}")
    for r in s["rows"]:
        print(f"   {r['speed']:>8} {r['push']:>12.6f} {r['tip_x']:>10.6f} "
              f"{r['tip_y']:>12.6f} {r['len_mean']:>12.6f}")
    print("\nB. 2つの式")
    print(f"   一次: k = {s['linear']['k']:.2f} / "
          f"残差 {s['linear']['sse']:.6f}")
    print(f"   二次: k = {s['square']['k']:.2f} / "
          f"残差 {s['square']['sse']:.6f}")
    print(f"   よく乗るのは {s['better']}（{s['sse_ratio']:.1f}倍）")


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
