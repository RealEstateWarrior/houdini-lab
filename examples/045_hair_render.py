"""実験045 — 毛を Karma で出す。指定した太さは、画のどこに出るのか。

<code>hairgen</code> は毛1本ごとに <code>width</code> という太さの数値を書き出す
（<code>thickness</code>、既定 0.001）。ではその 0.001 は、画の上で何ピクセルになるのか。

素直に考えれば

    見かけの太さ(px) = thickness × (1世界単位あたりのピクセル数)

になるはずだ。<strong>ただし width が「直径」なのか「半径」なのかで、答えは2倍違う。</strong>
先に式を立てて、実測と突き合わせる。

測り方は、<strong>毛を1本だけ置いて真横から撮る</strong>。毛玉のままでは毛が重なって
面積から太さを割り出せない。1本なら、縦に並ぶピクセルの数がそのまま太さになる。
PNG の透明度を足し合わせるので、輪郭のぼけも 0.01px まで拾える。

  A. 太さ4通りで、予測と実測を比べる（width は直径か半径か）
  B. 本数を変えたときのレンダ時間
  C. OpenGL と Karma の差

レンダしたあとにシーンを作り直すと hython が固まるので、1プロセス1レンダにする。

    hython examples/045_hair_render.py one 0.01
    hython examples/045_hair_render.py ball 250
    hython examples/045_hair_render.py shot guided
    python  examples/045_hair_render.py report
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "045_stats.json")

RES = (600, 600)
SAMPLES = 9
HAIR_LENGTH = 1.0
GUIDES = 300
LENGTH = 0.5
RADIUS = 0.20
DOME = 1.0
KEY = 3.0


def load():
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as fp:
            return json.load(fp)
    return {"res": list(RES), "samples": SAMPLES, "hair_length": HAIR_LENGTH,
            "one": [], "ball": [], "opengl": []}


def save(stats):
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)


# Apprentice のレンダには右下に Houdini のロゴが焼き込まれる。
# 透明度を持っているので、何も考えずに足すと測定値に混ざる（合計 4163.3）。
# 600×600 のときの箱。ここを 0 にしてから測る。
LOGO_BOX = (521, 567, 343, 567)


def drop_logo(alpha):
    alpha = alpha.copy()
    alpha[LOGO_BOX[0]:LOGO_BOX[1], LOGO_BOX[2]:LOGO_BOX[3]] = 0.0
    return alpha


def measure_width(path):
    """PNG から、毛の太さ（px）と長さ（px）を測る。

    透明度をそのまま足す。1列に 0.4 + 1 + 0.6 と乗っていれば太さは 2.0px。
    端は丸まっているかもしれないので、真ん中の6割の列だけを使う。
    """
    from PIL import Image
    import numpy

    image = Image.open(path).convert("RGBA")
    alpha = drop_logo(numpy.asarray(image, dtype=numpy.float64)[:, :, 3]
                      / 255.0)
    cols = alpha.sum(axis=0)                  # 列ごとの「濃さの合計」＝太さ
    used = numpy.nonzero(cols > 0.01)[0]
    if len(used) == 0:
        return {"width_px": 0.0, "length_px": 0.0, "coverage": 0.0}
    x0, x1 = used[0], used[-1]
    span = x1 - x0 + 1
    lo = x0 + int(span * 0.2)
    hi = x1 - int(span * 0.2)
    middle = cols[lo:hi + 1]
    return {"width_px": float(numpy.median(middle)),
            "width_px_mean": float(middle.mean()),
            "length_px": float(span),
            "coverage": float(alpha.sum())}


def camera_scale(cam):
    """カメラから「1世界単位が何ピクセルか」を出す。

    画に写る横幅 = aperture × 距離 ÷ focal（ピンホールの相似）。
    画像の中の毛の長さから逆算すると、丸い端の分だけずれるので、
    こちらを正とする。
    """
    import hou
    focal = cam.parm("focal").eval()
    aperture = cam.parm("aperture").eval()
    pos = cam.worldTransform().extractTranslates()
    distance = hou.Vector3(pos).length()      # 被写体は原点にある
    world_width = aperture * distance / focal
    return RES[0] / world_width, distance, focal, aperture


def render(node_path, tag, bbox, direction, margin=1.02, want_scale=False):
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

    karma = hou.node("/out").createNode("karma", f"exp045_{tag}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"045_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    scale = camera_scale(cam) if want_scale else None
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    seconds = time.perf_counter() - start
    if want_scale:
        return path, seconds, scale
    return path, seconds


def one(thickness):
    """毛を1本だけ置いて、真横から撮る。"""
    import hou

    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "one_hair")

    line = geo.createNode("line", "hair")
    line.parm("originx").set(-HAIR_LENGTH / 2.0)
    line.parm("dirx").set(1.0)
    line.parm("diry").set(0.0)
    line.parm("dist").set(HAIR_LENGTH)
    line.parm("points").set(2)

    wide = geo.createNode("attribwrangle", "width")
    wide.setFirstInput(line)
    wide.parm("class").set(2)          # ポイント
    wide.parm("snippet").set(f"f@width = {thickness!r};")
    wide.setDisplayFlag(True)
    wide.setRenderFlag(True)
    geo.layoutChildren()

    # 毛だけだと枠が潰れる。太さによらず同じ枠にして、撮る条件をそろえる
    pad = 0.06
    bbox = hou.BoundingBox(-HAIR_LENGTH / 2 - pad, -pad, -pad,
                           HAIR_LENGTH / 2 + pad, pad, pad)
    path, seconds, cam_info = render(wide.path(), f"one_{thickness}", bbox,
                                     (0.0, 0.0, 1.0), margin=1.0,
                                     want_scale=True)
    scale, distance, focal, aperture = cam_info
    info = measure_width(path)
    predicted = thickness * scale
    row = {"thickness": thickness, "seconds": seconds, "scale_px": scale,
           "distance": distance, "focal": focal, "aperture": aperture,
           "predicted_px": predicted, "ratio": (info["width_px"] / predicted
                                                if predicted else 0.0),
           "length_world": info["length_px"] / scale,
           **info}
    stats = load()
    stats["one"] = [r for r in stats["one"] if r["thickness"] != thickness]
    stats["one"].append(row)
    stats["one"].sort(key=lambda r: r["thickness"])
    save(stats)
    print(f"太さ {thickness}: 予測 {predicted:.3f}px / 実測 "
          f"{info['width_px']:.3f}px / 比 {row['ratio']:.4f} "
          f"（{seconds:.1f}秒）")


def build_ball(density, thickness=None):
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
    make.parm("snippet").set(f"""
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
""")

    gen = geo.createNode("hairgen::2.0", "hairgen")
    gen.setInput(0, rest)
    gen.setInput(1, make)
    gen.parm("density").set(density)
    gen.parm("influenceradius").set(RADIUS)
    if thickness is not None:
        gen.parm("thickness").set(thickness)

    merged = geo.createNode("merge", "out")
    merged.setInput(0, skin)
    merged.setInput(1, gen)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()
    return geo, gen, merged


def ball_bbox():
    """density によらず同じ枠にする。毛の伸びた先で枠が動くと比較にならない。"""
    import hou
    r = 1.0 + LENGTH + 0.05
    return hou.BoundingBox(-r, -r, -r, r, r, r)


def ball(density):
    geo, gen, merged = build_ball(density)
    hairs = len(gen.geometry().prims())
    bbox = ball_bbox()
    path, seconds = render(merged.path(), f"ball_{density}", bbox,
                           (0.6, 0.35, 1.0), margin=1.06)
    from PIL import Image
    import numpy
    alpha = drop_logo(numpy.asarray(Image.open(path).convert("RGBA"),
                                    dtype=numpy.float64)[:, :, 3] / 255.0)
    row = {"density": density, "hairs": hairs, "seconds": seconds,
           "coverage": float(alpha.sum()),
           "file": os.path.basename(path)}
    stats = load()
    stats["ball"] = [r for r in stats["ball"] if r["density"] != density]
    stats["ball"].append(row)
    stats["ball"].sort(key=lambda r: r["density"])
    save(stats)
    print(f"density {density}: 毛 {hairs:,}本 / {seconds:.1f}秒")


def thick(thickness):
    """毛玉のまま太さを変える。既定の 0.001 は1ピクセルより細い。"""
    from PIL import Image
    import numpy
    geo, gen, merged = build_ball(1000, thickness=thickness)
    hairs = len(gen.geometry().prims())
    bbox = ball_bbox()
    tag = f"thick_{thickness}"
    path, seconds, cam_info = render(merged.path(), tag, bbox,
                                     (0.6, 0.35, 1.0), margin=1.06,
                                     want_scale=True)
    scale = cam_info[0]
    alpha = drop_logo(numpy.asarray(Image.open(path).convert("RGBA"),
                                    dtype=numpy.float64)[:, :, 3] / 255.0)
    inside = alpha[alpha > 0.004]
    row = {"thickness": thickness, "hairs": hairs, "seconds": seconds,
           "scale_px": scale, "width_px": thickness * scale,
           "coverage": float(alpha.sum()),
           "touched": int((alpha > 0.004).sum()),
           "mean_alpha": float(inside.mean()) if len(inside) else 0.0,
           "file": os.path.basename(path)}
    stats = load()
    rows = [r for r in stats.get("thick", []) if r["thickness"] != thickness]
    rows.append(row)
    rows.sort(key=lambda r: r["thickness"])
    stats["thick"] = rows
    save(stats)
    print(f"太さ {thickness}: 画の上で {row['width_px']:.3f}px / "
          f"覆った面積 {row['coverage']:.0f} / "
          f"触れたピクセル {row['touched']:,} / "
          f"平均の濃さ {row['mean_alpha']:.3f}（{seconds:.1f}秒）")


def scene():
    import hou_tools
    geo, gen, merged = build_ball(1000, thickness=0.008)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "045_graph.json"),
                          title="実験045 — 毛を Karma で出す")
    hou_tools.save_hip(os.path.join(OUT, "045_hair_render.hipnc"))
    print("保存: out/045_graph.json, out/045_hair_render.hipnc")


def opengl(density):
    """同じ絵を OpenGL でも撮って、時間を比べる。"""
    import hou_tools
    geo, gen, merged = build_ball(density)
    hairs = len(gen.geometry().prims())
    bbox = ball_bbox()
    path = os.path.join(OUT, f"045_gl_{density}.png")
    start = time.perf_counter()
    hou_tools.render_preview(merged.path(), path, res=RES,
                             direction=(0.6, 0.35, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.06)
    seconds = time.perf_counter() - start
    stats = load()
    stats["opengl"] = [r for r in stats["opengl"] if r["density"] != density]
    stats["opengl"].append({"density": density, "hairs": hairs,
                            "seconds": seconds,
                            "file": os.path.basename(path)})
    stats["opengl"].sort(key=lambda r: r["density"])
    save(stats)
    print(f"OpenGL density {density}: 毛 {hairs:,}本 / {seconds:.2f}秒")


def report():
    stats = load()
    print("A. 太さは指定どおりに出るか（毛1本を真横から）")
    print(f"   {'thickness':>10} {'1単位のpx':>10} {'予測(px)':>10} "
          f"{'実測(px)':>10} {'実測÷予測':>11} {'長さ(世界)':>12}")
    for r in stats["one"]:
        print(f"   {r['thickness']:>10} {r['scale_px']:>10.2f} "
              f"{r['predicted_px']:>10.3f} {r['width_px']:>10.3f} "
              f"{r['ratio']:>11.4f} {r.get('length_world', 0):>12.5f}")
    if stats["one"]:
        ratios = [r["ratio"] for r in stats["one"]]
        lo, hi = min(ratios), max(ratios)
        print(f"   比の幅: {lo:.4f} 〜 {hi:.4f}")
        print("   1.0 に近ければ width は直径、2.0 に近ければ半径")

    print("\nB. 本数とレンダ時間")
    print(f"   {'density':>8} {'毛':>10} {'時間':>9} {'1本あたり':>12} "
          f"{'覆った面積':>12}")
    for r in stats["ball"]:
        print(f"   {r['density']:>8} {r['hairs']:>10,} "
              f"{r['seconds']:>8.1f}秒 "
              f"{r['seconds'] / r['hairs'] * 1000:>11.4f}ms "
              f"{r['coverage']:>12.0f}")

    print("\nD. 毛玉のまま太さを変える（毛 12,516本）")
    print(f"   {'thickness':>10} {'画の上の太さ':>14} {'触れたピクセル':>14} "
          f"{'平均の濃さ':>12} {'覆った面積':>12} {'時間':>8}")
    for r in stats.get("thick", []):
        print(f"   {r['thickness']:>10} {r['width_px']:>13.3f}px "
              f"{r['touched']:>14,} {r['mean_alpha']:>12.3f} "
              f"{r['coverage']:>12.0f} {r['seconds']:>7.1f}秒")

    print("\nC. OpenGL と Karma")
    print(f"   {'density':>8} {'毛':>10} {'OpenGL':>10} {'Karma':>10} "
          f"{'倍率':>8}")
    karma = {r["density"]: r for r in stats["ball"]}
    for r in stats["opengl"]:
        k = karma.get(r["density"])
        if not k:
            continue
        print(f"   {r['density']:>8} {r['hairs']:>10,} "
              f"{r['seconds']:>9.2f}秒 {k['seconds']:>9.1f}秒 "
              f"{k['seconds'] / r['seconds']:>7.1f}倍")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "one":
        one(float(sys.argv[2]))
    elif cmd == "ball":
        ball(int(sys.argv[2]))
    elif cmd == "scene":
        scene()
    elif cmd == "thick":
        thick(float(sys.argv[2]))
    elif cmd == "opengl":
        opengl(int(sys.argv[2]))
    else:
        report()
