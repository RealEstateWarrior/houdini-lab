"""実験046 — 毛に色を付ける。根元から毛先へ、思ったとおりに変わるか。

実験045で毛を Karma に出せた。次は色を付ける。
ところが<strong>毛が持っているアトリビュートは <code>P</code> と <code>width</code> だけ</strong>だった。
「この点は根元から何割の位置か」を示す数値は付いてこない。自分で作るしかない。

  A. 毛が持っている属性を数える
  B. <code>width</code> は根元から先まで一定か（<code>hairprofile</code> という
     先細りのカーブがパラメータにある）
  C. 根元を赤、毛先を青にする。画の上で色は位置に比例して変わるか
  D. 束ごとに色を変えた毛玉を Karma で出す。色は出るか、時間は変わるか

    hython examples/046_hair_color.py attrs
    hython examples/046_hair_color.py gradient
    hython examples/046_hair_color.py ball plain
    hython examples/046_hair_color.py ball clump
    python  examples/046_hair_color.py report
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "046_stats.json")

RES = (600, 600)
SAMPLES = 9
GUIDES = 300
LENGTH = 0.5
RADIUS = 0.20
THICKNESS = 0.008
DOME = 1.0
KEY = 3.0

GUIDE_VEX = f"""
int segs = 8;
float len = {LENGTH};
int n = npoints(0);
for (int i = 0; i < n; i++) {{
    vector p = point(0, "P", i);
    vector nn = point(0, "N", i);
    if (length(nn) < 1e-6) nn = normalize(p);
    vector r = set(rand(i*3+0.11), rand(i*3+1.31), rand(i*3+2.71)) - 0.5;
    nn = normalize(nn + r * 0.8);
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

# 毛のどこかを示す数値は付いてこないので、自分で作る。
# プリミティブごとに走って、頂点の並び順から 0〜1 を振る。
ALONG_VEX = """
int pts[] = primpoints(0, @primnum);
int n = len(pts);
for (int i = 0; i < n; i++) {
    float u = (n > 1) ? float(i) / float(n - 1) : 0.0;
    setpointattrib(0, "alongu", pts[i], u);
    __COLOR__
}
"""

ROOT_TO_TIP = 'setpointattrib(0, "Cd", pts[i], lerp(set(1,0,0), set(0,0,1), u));'
BY_CLUMP = """
int cid = primattrib(0, "clumpid", @primnum, 0);
vector c = set(rand(cid*3+0.1), rand(cid*3+1.7), rand(cid*3+2.3));
setpointattrib(0, "Cd", pts[i], 0.15 + 0.85 * c);
"""


# Apprentice のレンダには右下に Houdini のロゴが焼き込まれ、透明度も持っている。
# 何も考えずに数えると測定値に混ざる（実験045でこれに掛かった）。
LOGO_BOX = (521, 567, 343, 567)


def drop_logo(alpha):
    alpha = alpha.copy()
    alpha[LOGO_BOX[0]:LOGO_BOX[1], LOGO_BOX[2]:LOGO_BOX[3]] = 0.0
    return alpha


def load():
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as fp:
            return json.load(fp)
    return {"res": list(RES), "samples": SAMPLES}


def save(stats):
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)


def hair_scene(density=1000, clump=False, color=None, thickness=THICKNESS):
    import hou
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
    roots.parm("npts").set(GUIDES)
    make = geo.createNode("attribwrangle", "make_guides")
    make.setFirstInput(roots)
    make.setInput(1, rest)
    make.parm("class").set(0)
    make.parm("snippet").set(GUIDE_VEX)

    gen = geo.createNode("hairgen::2.0", "hairgen")
    gen.setInput(0, rest)
    gen.setInput(1, make)
    gen.parm("density").set(density)
    gen.parm("influenceradius").set(RADIUS)
    gen.parm("thickness").set(thickness)
    last = gen

    if clump:
        node = geo.createNode("hairclump::2.0", "clump")
        node.setInput(0, gen)
        node.setInput(1, rest)
        node.parm("clumpsize").set(0.4)
        last = node

    if color:
        tint = geo.createNode("attribwrangle", "tint")
        tint.setFirstInput(last)
        tint.parm("class").set(1)          # プリミティブごと
        tint.parm("snippet").set(ALONG_VEX.replace("__COLOR__", color))
        last = tint

    return geo, skin, rest, gen, last


def with_material(geo, node, use_point_color=True, unlit=False):
    """材質を割り当てる。

    unlit にすると、点の色を「発光」として出す。こうすると光の当たり方が
    混ざらないので、色そのものを測れる。
    """
    import hou
    mat = hou.node("/mat") or hou.node("/").createNode("mat")
    name = "hair_unlit" if unlit else "hair_shader"
    shader = (mat.node(name)
              or mat.createNode("principledshader::2.0", name))
    shader.parm("basecolor_usePointColor").set(use_point_color and not unlit)
    shader.parm("rough").set(0.45)
    if unlit:
        for parm in ("basecolorr", "basecolorg", "basecolorb"):
            shader.parm(parm).set(0.0)
        shader.parm("reflect").set(0.0)
        shader.parm("emitcolor_usePointColor").set(True)
        shader.parm("emitint").set(1.0)
    assign = geo.createNode("material", "assign")
    assign.setFirstInput(node)
    assign.parm("shop_materialpath1").set(shader.path())
    return assign


def render(tag, last, bbox, direction, margin=1.02):
    import hou
    import hou_tools
    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(DOME)
    hou.node("/obj/report_key").parm("light_intensity").set(KEY)
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    hou_tools._frame_camera(cam, bbox, RES, direction, margin=margin)

    karma = hou.node("/out").createNode("karma", f"exp046_{tag}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"046_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    return path, time.perf_counter() - start


def attrs():
    """A・B. 毛が持っている属性と、width の変わり方。"""
    import numpy
    geo, skin, rest, gen, last = hair_scene(density=200)
    g = gen.geometry()
    rows = {
        "point": sorted(a.name() for a in g.pointAttribs()),
        "vertex": sorted(a.name() for a in g.vertexAttribs()),
        "prim": sorted(a.name() for a in g.primAttribs()),
        "detail": sorted(a.name() for a in g.globalAttribs()),
        "hairs": len(g.prims()),
        "points_per_hair": len(g.prims()[0].vertices()),
    }
    print("A. 毛が持っている属性")
    for key in ("point", "vertex", "prim", "detail"):
        print(f"   {key:>7}: {rows[key]}")
    print(f"   毛 {rows['hairs']:,}本 / 1本 {rows['points_per_hair']}点")

    print("\nB. width は根元から先まで一定か")
    widths = numpy.zeros((len(g.prims()), rows["points_per_hair"]))
    for i, prim in enumerate(g.prims()):
        for j, vtx in enumerate(prim.vertices()):
            widths[i, j] = vtx.point().attribValue("width")
    mean = widths.mean(axis=0)
    print(f"   {'位置':>6} {'width の平均':>14} {'根元との比':>12} "
          f"{'ばらつき':>12}")
    prof = []
    for j, value in enumerate(mean):
        u = j / (len(mean) - 1)
        prof.append({"index": j, "u": u, "width": float(value),
                     "ratio": float(value / mean[0]),
                     "sd": float(widths[:, j].std())})
        print(f"   {u:>6.3f} {value:>14.6f} {value / mean[0]:>12.4f} "
              f"{widths[:, j].std():>12.8f}")
    flat = bool(abs(mean.max() - mean.min()) < 1e-9)
    print(f"   一定か: {'はい' if flat else 'いいえ（先細りする）'}")
    stats = load()
    stats["attribs"] = rows
    stats["profile"] = prof
    stats["width_flat"] = flat
    save(stats)


def gradient(mode="lit"):
    """C. 毛1本を根元から毛先へ赤→青にして、真横から撮る。"""
    import hou
    import numpy
    from PIL import Image

    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "one_hair")
    line = geo.createNode("line", "hair")
    line.parm("originx").set(-0.5)
    line.parm("dirx").set(1.0)
    line.parm("diry").set(0.0)
    line.parm("dist").set(1.0)
    line.parm("points").set(33)

    tint = geo.createNode("attribwrangle", "tint")
    tint.setFirstInput(line)
    tint.parm("class").set(1)
    tint.parm("snippet").set(ALONG_VEX.replace("__COLOR__", ROOT_TO_TIP))
    wide = geo.createNode("attribwrangle", "width")
    wide.setFirstInput(tint)
    wide.parm("class").set(2)
    wide.parm("snippet").set("f@width = 0.04;")

    assign = with_material(geo, wide, unlit=(mode == "unlit"))
    assign.setDisplayFlag(True)
    assign.setRenderFlag(True)
    geo.layoutChildren()

    pad = 0.06
    bbox = hou.BoundingBox(-0.5 - pad, -pad, -pad, 0.5 + pad, pad, pad)
    path, seconds = render(f"gradient_{mode}", assign, bbox, (0.0, 0.0, 1.0),
                           margin=1.0)

    array = numpy.asarray(Image.open(path).convert("RGBA"),
                          dtype=numpy.float64)
    alpha = drop_logo(array[:, :, 3] / 255.0)
    weight = alpha.sum(axis=0)
    used = numpy.nonzero(weight > 0.5)[0]
    x0, x1 = used[0], used[-1]
    def to_linear(value):
        """PNG は sRGB で書かれている。割合を測る前に線形の明るさへ戻す。"""
        c = value / 255.0
        return (c / 12.92 if c <= 0.04045
                else ((c + 0.055) / 1.055) ** 2.4)

    rows = []
    label = "光を当てて" if mode == "lit" else "発光にして（光の影響を外す）"
    print(f"C. 根元（赤）から毛先（青）へ。{label}")
    print(f"   {'位置':>8} {'赤(sRGB)':>10} {'青(sRGB)':>10} "
          f"{'青の割合(線形)':>16}")
    fracs = [i / 20.0 for i in range(2, 19)]   # 端の丸みを避けて 0.1〜0.9
    for frac in fracs:
        col = int(round(x0 + (x1 - x0) * frac))
        w = alpha[:, col]
        if w.sum() < 0.5:
            continue
        r8 = float((array[:, col, 0] * w).sum() / w.sum())
        b8 = float((array[:, col, 2] * w).sum() / w.sum())
        r, b = to_linear(r8), to_linear(b8)
        share = b / (r + b) if (r + b) else 0.0
        rows.append({"frac": frac, "red8": r8, "blue8": b8,
                     "red": r, "blue": b, "blue_share": share})
    # 明るさの底上げ（周囲の光）は赤にも青にも同じだけ乗るので、
    # 割合は「位置の1次式」になるはず。直線に乗るかどうかを見る。
    xs = numpy.asarray([r["frac"] for r in rows])
    ys = numpy.asarray([r["blue_share"] for r in rows])
    slope, intercept = numpy.polyfit(xs, ys, 1)
    fit = slope * xs + intercept
    resid = ys - fit
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((ys - ys.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    for row, f, d in zip(rows, fit, resid):
        row["fit"] = float(f)
        row["resid"] = float(d)
    for row in rows[::4]:
        print(f"   {row['frac']:>8.2f} {row['red8']:>10.1f} "
              f"{row['blue8']:>10.1f} {row['blue_share']:>16.4f}")
    worst = float(numpy.abs(resid).max())
    print(f"   直線あてはめ: 青の割合 = {slope:.4f} × 位置 + {intercept:.4f}")
    print(f"   決定係数 R² = {r2:.5f} / 直線からの最大のずれ {worst:.4f}")
    print(f"   位置に比例していると言えるか: "
          f"{'はい' if r2 > 0.99 and worst < 0.03 else 'いいえ'}")
    stats = load()
    stats.setdefault("gradient", {})[mode] = {
        "rows": rows, "slope": float(slope), "intercept": float(intercept),
        "r2": r2, "worst": worst, "seconds": seconds, "points": len(rows)}
    save(stats)


def ball(case):
    """D. 毛玉に色を付けて Karma で出す。"""
    import hou
    import numpy
    from PIL import Image

    color = {"plain": None, "tip": ROOT_TO_TIP, "clump": BY_CLUMP}[case]
    geo, skin, rest, gen, last = hair_scene(density=1000,
                                            clump=(case == "clump"),
                                            color=color)
    hairs = len(gen.geometry().prims())
    node = with_material(geo, last) if color else last
    merged = geo.createNode("merge", "out")
    merged.setInput(0, skin)
    merged.setInput(1, node)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()

    r = 1.0 + LENGTH + 0.05
    bbox = hou.BoundingBox(-r, -r, -r, r, r, r)
    path, seconds = render(f"ball_{case}", merged, bbox, (0.6, 0.35, 1.0),
                           margin=1.06)

    array = numpy.asarray(Image.open(path).convert("RGBA"),
                          dtype=numpy.float64)
    alpha = drop_logo(array[:, :, 3] / 255.0)
    mask = alpha > 0.02
    rgb = array[:, :, :3][mask]
    sat = ((rgb.max(axis=1) - rgb.min(axis=1)) / numpy.maximum(
        rgb.max(axis=1), 1.0))
    row = {"case": case, "hairs": hairs, "seconds": seconds,
           "pixels": int(mask.sum()),
           "colorful": float((sat > 0.15).mean() * 100),
           "sat_mean": float(sat.mean()),
           "file": os.path.basename(path)}
    stats = load()
    balls = [r for r in stats.get("ball", []) if r["case"] != case]
    balls.append(row)
    order = {"plain": 0, "tip": 1, "clump": 2}
    balls.sort(key=lambda r: order.get(r["case"], 9))
    stats["ball"] = balls
    save(stats)
    print(f"{case}: 毛 {hairs:,}本 / {seconds:.1f}秒 / "
          f"色のあるピクセル {row['colorful']:.1f}% / "
          f"彩度の平均 {row['sat_mean']:.4f}")


def scene():
    import hou_tools
    geo, skin, rest, gen, last = hair_scene(density=1000, clump=True,
                                            color=BY_CLUMP)
    with_material(geo, last)
    geo.layoutChildren()
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "046_graph.json"),
                          title="実験046 — 毛に色を付ける")
    hou_tools.save_hip(os.path.join(OUT, "046_hair_color.hipnc"))
    print("保存: out/046_graph.json, out/046_hair_color.hipnc")


def report():
    stats = load()
    print("A. 毛が持っている属性")
    a = stats.get("attribs", {})
    for key in ("point", "vertex", "prim", "detail"):
        print(f"   {key:>7}: {a.get(key)}")

    print("\nB. width は根元から先まで一定か")
    print(f"   {'位置':>6} {'width の平均':>14} {'根元との比':>12}")
    for r in stats.get("profile", []):
        print(f"   {r['u']:>6.3f} {r['width']:>14.6f} {r['ratio']:>12.4f}")

    print("\nC. 根元（赤）から毛先（青）へ")
    for mode in ("lit", "unlit"):
        grad = stats.get("gradient", {}).get(mode)
        if not grad:
            continue
        label = "光を当てて" if mode == "lit" else "発光にして"
        print(f"   {label}")
        print(f"   {'位置':>8} {'赤(sRGB)':>10} {'青(sRGB)':>10} "
              f"{'青の割合':>10} {'直線との差':>12}")
        for r in grad["rows"][::4]:
            print(f"   {r['frac']:>8.2f} {r['red8']:>10.1f} "
                  f"{r['blue8']:>10.1f} {r['blue_share']:>10.4f} "
                  f"{r['resid']:>+12.4f}")
        print(f"   青の割合 = {grad['slope']:.4f} × 位置 "
              f"+ {grad['intercept']:.4f} / R² = {grad['r2']:.5f} / "
              f"最大のずれ {grad['worst']:.4f}")
        print(f"   傾き + 2×切片 = "
              f"{grad['slope'] + 2 * grad['intercept']:.4f}（1 になるはず）")

    print("\nD. 毛玉に色を付ける")
    print(f"   {'条件':>8} {'毛':>10} {'時間':>9} {'色のあるピクセル':>18} "
          f"{'彩度の平均':>12}")
    for r in stats.get("ball", []):
        print(f"   {r['case']:>8} {r['hairs']:>10,} {r['seconds']:>8.1f}秒 "
              f"{r['colorful']:>17.1f}% {r['sat_mean']:>12.4f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "attrs":
        attrs()
    elif cmd == "gradient":
        gradient(sys.argv[2] if len(sys.argv) > 2 else "lit")
    elif cmd == "ball":
        ball(sys.argv[2])
    elif cmd == "scene":
        scene()
    else:
        report()
