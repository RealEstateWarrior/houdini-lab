"""実験038 — 塗り分けた地形を Karma で出す。点の色はそのまま出るのか。

実験037で地形を3色に塗り分けた。ただしあれは確認用の速い描画（OpenGL）で、
点に付けた <code>@Cd</code> がそのまま画になっていた。

見せる絵にするときは Karma を使う。ここで素朴な疑問がある。

  <strong>点に付けた色は、Karma でもそのまま出るのか。</strong>

見立ては「材質を割り当てないと出ない」だった。<strong>外れた。</strong>
材質なしでも色は出る。代わりに別の問題が出た。<strong>白飛びである。</strong>
実験024で煙に合わせたライトのまま地形を撮ると、岩肌が真っ白に飛ぶ。

確かめること。

  A. 材質の有無で、出てくる色は変わるか
  B. ライトの強さを変えると、白飛びはどう減るか
  C. OpenGL と Karma で、時間と見え方はどれだけ違うか

    hython examples/038_karma_terrain.py
"""

import json
import os
import sys
import time

import hou
import numpy
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SIZE = 200.0
SPACING = 2.0
AMP = 120.0
ELEMENT = 80.0
ERODE = 4
SOIL = 0.30
WATER = 1.60
RES = (720, 460)
SAMPLES = 24
DOME = 1.0
KEY = 2.4


def build(with_material=True):
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

    paint = geo.createNode("attribwrangle", "paint")
    paint.setFirstInput(mesh)
    paint.setInput(1, erode)
    paint.parm("class").set(2)
    paint.parm("snippet").set(
        'float sed = volumesample(1, "sediment", @P);\n'
        'float flw = volumesample(1, "flow", @P);\n'
        f"int water = (flw >= {WATER}) ? 1 : 0;\n"
        f"int soil  = (sed >= {SOIL}) ? 1 : 0;\n"
        "i@kind = water ? 2 : (soil ? 1 : 0);\n"
        "vector rock = set(0.62, 0.60, 0.58);\n"
        "vector soilc = set(0.45, 0.32, 0.18);\n"
        "vector waterc = set(0.20, 0.38, 0.55);\n"
        "@Cd = (@kind == 2) ? waterc : ((@kind == 1) ? soilc : rock);")

    last = paint
    if with_material:
        # 見立てでは「材質が無いと点の色は出ない」はずだった。
        # 実際には既定の材質でも出る。principled shader の
        # 「点の色を使う」も既定でオンなので、割り当てても結果は変わらない。
        mat = hou.node("/mat") or hou.node("/").createNode("mat")
        shader = mat.createNode("principledshader::2.0", "terrain_mat")
        # 「点の色を使う」は既定でオンなので、割り当てるだけでよい。
        shader.parm("basecolor_usePointColor").set(True)
        shader.parm("rough").set(0.75)
        assign = geo.createNode("material", "assign")
        assign.setFirstInput(paint)
        assign.parm("shop_materialpath1").set(shader.path())
        last = assign

    last.setDisplayFlag(True)
    last.setRenderFlag(True)
    geo.layoutChildren()
    return geo, paint, last


def count_colors(path, sample=2):
    """画の色の散らばりと、白飛びの割合を見る。

    背景も真っ白なので、明るさで地形と背景を分けようとすると、
    白飛びした地形まで背景として捨ててしまう（最初これで 0% と出た）。
    書き出したPNGは透明度を持っているので、そちらで分ける。
    """
    image = Image.open(path).convert("RGBA")
    array = numpy.asarray(image, dtype=numpy.float64)[::sample, ::sample]
    flat = array.reshape(-1, 4)
    flat = flat[flat[:, 3] > 128][:, :3]
    if len(flat) == 0:
        return {"pixels": 0}
    rb = flat[:, 0] - flat[:, 2]
    clipped = (flat.max(axis=1) >= 250).mean() * 100
    return {
        "pixels": int(len(flat)),
        "brown": float((rb > 20).mean() * 100),
        "blue": float((rb < -20).mean() * 100),
        "grey": float((numpy.abs(rb) <= 20).mean() * 100),
        "clipped": float(clipped),
        "mean": float(flat.mean()),
        "sd": float(flat.mean(axis=1).std()),
    }


def render_karma(tag, with_material, key, dome=DOME):
    geo, paint, last = build(with_material=with_material)
    bbox = last.geometry().boundingBox()
    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(dome)
    hou.node("/obj/report_key").parm("light_intensity").set(key)
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    hou_tools._frame_camera(cam, bbox, RES, (0.7, 0.5, 1.0), margin=1.04)

    karma = hou.node("/out").createNode("karma", f"exp038_{tag}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"038_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    seconds = time.perf_counter() - start
    info = count_colors(path)
    info.update({"seconds": seconds, "file": os.path.basename(path),
                 "key": key, "dome": dome})
    return geo, paint, info


def main():
    stats = {"res": list(RES), "samples": SAMPLES}

    print("A. 材質を割り当てないときと、割り当てたとき（ライトは024と同じ）")
    rows = []
    for label, tag, with_material in (("材質なし", "karma_nomat", False),
                                      ("材質あり", "karma_mat", True)):
        geo, paint, info = render_karma(tag, with_material, KEY)
        info["label"] = label
        rows.append(info)
        print(f"   {label}: {info['seconds']:6.2f}秒 / "
              f"茶 {info['brown']:5.1f}% 青 {info['blue']:5.1f}% "
              f"灰 {info['grey']:5.1f}% / 白飛び {info['clipped']:5.1f}%")
    stats["karma"] = rows
    nomat, mat = rows[0], rows[1]
    same = abs(nomat["brown"] - mat["brown"]) < 2.0
    print(f"   材質なしでも色は出たか: "
          f"{'はい' if (nomat['brown'] + nomat['blue']) > 5 else 'いいえ'}")
    print(f"   材質のあるなしでほぼ同じか: {'はい' if same else 'いいえ'}")
    stats["color_without_material"] = (nomat["brown"] + nomat["blue"]) > 5
    stats["material_changes_nothing"] = same

    print("\nB. ライトを弱くすると、白飛びはどう減るか")
    lights = []
    print(f"   {'キーライト':>10} {'秒':>7} {'白飛び':>9} {'明るさ':>9} "
          f"{'ばらつき':>10} {'茶':>7} {'青':>7}")
    for key in (2.4, 1.2, 0.6, 0.3):
        geo, paint, info = render_karma(f"key{int(key * 10)}", True, key)
        lights.append(dict(info))
        print(f"   {key:>10} {info['seconds']:>7.2f} "
              f"{info['clipped']:>8.1f}% {info['mean']:>9.2f} "
              f"{info['sd']:>10.2f} {info['brown']:>6.1f}% "
              f"{info['blue']:>6.1f}%")
    stats["lights"] = lights
    best = min(lights, key=lambda r: abs(r["clipped"] - 1.0))
    print(f"   白飛びが1%に一番近いのは キーライト {best['key']}"
          f"（{best['clipped']:.1f}%）")
    stats["best_key"] = best["key"]

    print("\nC. OpenGL と比べる")
    geo, paint, last = build(with_material=True)
    bbox = last.geometry().boundingBox()
    gl_path = os.path.join(OUT, "038_opengl.png")
    start = time.perf_counter()
    hou_tools.render_preview(paint.path(), gl_path, res=RES,
                             direction=(0.7, 0.5, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    gl_sec = time.perf_counter() - start
    gl = count_colors(gl_path)
    print(f"   {'':10} {'秒':>8} {'白飛び':>9} {'明るさ':>9} {'ばらつき':>10} "
          f"{'茶':>7} {'青':>7}")
    print(f"   {'OpenGL':10} {gl_sec:>8.2f} {gl['clipped']:>8.1f}% "
          f"{gl['mean']:>9.2f} {gl['sd']:>10.2f} {gl['brown']:>6.1f}% "
          f"{gl['blue']:>6.1f}%")
    print(f"   {'Karma':10} {best['seconds']:>8.2f} {best['clipped']:>8.1f}% "
          f"{best['mean']:>9.2f} {best['sd']:>10.2f} {best['brown']:>6.1f}% "
          f"{best['blue']:>6.1f}%")
    print(f"   Karma は OpenGL の {best['seconds'] / gl_sec:.1f}倍の時間")
    stats["opengl"] = dict(gl, seconds=gl_sec)
    stats["karma_over_opengl"] = best["seconds"] / gl_sec

    with open(os.path.join(OUT, "038_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "038_graph.json"),
                          title="実験038 — 地形を Karma で出す")
    hou_tools.save_hip(os.path.join(OUT, "038_karma.hipnc"))
    print("\n保存: out/038_stats.json, out/038_graph.json, out/038_karma.hipnc")


if __name__ == "__main__":
    main()
