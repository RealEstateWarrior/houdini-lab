# -*- coding: utf-8 -*-
"""実験225 — 明かりを何百・何千と置く場面（夜の街の窓・街灯）は、ライトで置くか、光る物で置くか。

制作の問い: 夜の街の窓明かりや街灯を何百も置きたい。1 つずつライト（hlight の point）を置くのと、小さな光る球（Emission の材質）を
置くのとで、Karma の時間とざらつきはどう違うか。何個まで置けるか。

  40 m 四方の地面に、箱 20 個（建物のつもり、高さ 2〜6 m）を並べる。その上 3 m の高さに、明かりを N 個、格子状に置く（N = 1・10・100・1000）。
  明かりの合計の強さは N によらず同じにする。
    lights … hlight（point）を N 個。Intensity 400 / N（Normalize Light Intensity to Area は既定のまま）
    glow   … 半径 0.1 m の球を N 個（1 つの geo にまとめる）。Emission の強さは、球 1 個が同じ強さの point ライトと同じ明るさを出すように決める
             （球の表面の明るさ L で球全体が出す光 = π × L × 表面積。point ライト Intensity I の出す光 = 4π × I）
  はじめに小さく 1 枚撮って捨てる。1 通りずつ、ほかの重い処理は回さない。
  測るもの: 480×270 で 16 サンプル（ノイズ除去なし）の撮る時間と、同じ条件の 64 サンプルの画との差（ざらつき、地面と箱の部分）。
  あわせて、地面の明るさの平均（ライトと光る球で同じ明るさになっているか）。
  ライトが無いと Karma が自動で明かりを足すので、明るさ 0 の環境ライトを置いて止める（はじめはこれを忘れ、光る球の場面が自動の明かりで照らされていた）。

    hython examples/225_karma_many_lights.py
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
RES = (480, 270)
COUNTS = (1, 10, 100, 1000)
TOTAL = 400.0
R = 0.1


def spots(n):
    """40 m 四方の上 3 m に、n 個をなるべく格子状に並べる。"""
    k = math.ceil(math.sqrt(n))
    out = []
    for i in range(n):
        x, z = i % k, i // k
        out.append(((x + 0.5) / k * 36 - 18, 3.0 + (i % 3) * 0.7, (z + 0.5) / k * 36 - 18))
    return out


def main():
    import hou
    import numpy as np
    import OpenImageIO as oiio
    import hou_tools
    import sop_bench
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    mat = hou.node("/mat")
    city = obj.createNode("geo", "city")
    ground = city.createNode("grid", "ground")
    ground.parmTuple("size").set((40, 40))
    boxes = city.createNode("attribwrangle", "buildings")
    boxes.parm("class").set(0)
    boxes.parm("snippet").set(
        "// 箱 20 個（建物のつもり）。場所と高さは乱数で決める\n"
        "for (int i = 0; i < 20; i++) {\n"
        "    vector c = set(fit01(rand(i), -15, 15), 0, fit01(rand(i + 50), -15, 15));\n"
        "    float h = fit01(rand(i + 99), 2, 6);\n"
        "    int p[];\n"
        "    for (int k = 0; k < 8; k++) {\n"
        "        vector o = set(k & 1 ? 1.2 : -1.2, k & 2 ? h : 0, k & 4 ? 1.2 : -1.2);\n"
        "        append(p, addpoint(0, c + o));\n"
        "    }\n"
        "    int f[] = {0,2,3,1, 4,5,7,6, 0,1,5,4, 2,6,7,3, 0,4,6,2, 1,3,7,5};\n"
        "    for (int q = 0; q < 6; q++) addprim(0, 'poly', p[f[q*4]], p[f[q*4+1]], p[f[q*4+2]], p[f[q*4+3]]);\n"
        "}")
    grey = mat.createNode("principledshader::2.0", "grey")
    grey.parmTuple("basecolor").set((0.5, 0.5, 0.5))
    grey.parm("rough").set(0.6)
    merge = city.createNode("merge", "ground_and_buildings")
    merge.setInput(0, ground)
    merge.setInput(1, boxes)
    asg = city.createNode("material", "assign_grey")
    asg.setFirstInput(merge)
    asg.parm("shop_materialpath1").set(grey.path())
    asg.setDisplayFlag(True)
    asg.setRenderFlag(True)
    # 光る球の置き場所（add で点 → 球を並べる）
    glow_geo = obj.createNode("geo", "glow_balls")
    pts = glow_geo.createNode("attribwrangle", "spots")
    pts.parm("class").set(0)
    ball = glow_geo.createNode("sphere", "ball")
    ball.parm("type").set("polymesh")
    ball.parmTuple("rad").set((R, R, R))
    cp = glow_geo.createNode("copytopoints::2.0", "balls")
    cp.setInput(0, ball)
    cp.setInput(1, pts)
    glow = mat.createNode("principledshader::2.0", "glow")
    glow.parmTuple("basecolor").set((0, 0, 0))
    glow.parm("reflect").set(0)
    glow.parmTuple("emitcolor").set((1.0, 0.8, 0.55))
    ga = glow_geo.createNode("material", "assign_glow")
    ga.setFirstInput(cp)
    ga.parm("shop_materialpath1").set(glow.path())
    ga.setDisplayFlag(True)
    ga.setRenderFlag(True)
    # ライトが 1 つも無いと、Karma は自動で明かりを足す。明るさ 0 の環境ライトを置いて止める（実験216 と同じ）
    dark = obj.createNode("envlight", "no_auto_light")
    dark.parm("light_intensity").set(0)
    cam = obj.createNode("cam", "cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    cam.parmTuple("t").set((0, 18, 30))
    cam.parmTuple("r").set((-32, 0, 0))
    karma = hou.node("/out").createNode("karma", "k")
    karma.parm("camera").set(cam.path())
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])

    def render(path, spp):
        karma.parm("samplesperpixel").set(spp)
        karma.parm("varianceaa_maxsamples").set(spp)
        karma.parm("picture").set(path.replace("\\", "/"))
        t0 = time.perf_counter()
        karma.render(frame_range=(1, 1, 1), verbose=False)
        return time.perf_counter() - t0

    lights = []

    def set_lights(n, on):
        for lt in lights:
            lt.destroy()
        lights.clear()
        if not on:
            return
        for i, p in enumerate(spots(n)):
            lt = obj.createNode("hlight::2.0", f"lamp_{i}")
            lt.parm("light_type").set("point")
            lt.parm("light_intensity").set(TOTAL / n)
            lt.parmTuple("light_color").set((1.0, 0.8, 0.55))
            lt.parmTuple("t").set(p)
            lights.append(lt)

    def set_balls(n, on):
        pts.parm("snippet").set("" if not on else "\n".join(f"addpoint(0, {{{p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f}}});" for p in spots(n)))
        # 球 1 個の出す光 = π L × 4π r² を、point ライトの 4π I にそろえる → L = I / (π r²)
        glow.parm("emitint").set((TOTAL / n) / (math.pi * R * R))
        glow_geo.setDisplayFlag(on)

    set_balls(1, False)
    set_lights(1, True)
    render(os.path.join(OUT, "_225_warm.png"), 1)
    rows = []
    for n in COUNTS:
        for kind in ("lights", "glow"):
            set_lights(n, kind == "lights")
            set_balls(n, kind == "glow")
            ref = os.path.join(OUT, f"_225_{kind}_{n}_ref.exr")
            img = os.path.join(OUT, f"225_{kind}_{n}.exr")
            sec = render(img, 16)
            sec_ref = render(ref, 64)
            a = oiio.ImageBuf(img).get_pixels(oiio.FLOAT)[:, :, :3]
            b = oiio.ImageBuf(ref).get_pixels(oiio.FLOAT)[:, :, :3]
            mask = slice(int(RES[1] * 0.35), RES[1])      # 地面と箱の部分（下 65%）
            lum = lambda x: x @ np.array([0.2126, 0.7152, 0.0722])  # noqa: E731
            la, lb = lum(a[mask]), lum(b[mask])
            noise = float(np.sqrt(np.mean((la - lb) ** 2)) / max(lb.mean(), 1e-6))
            view = np.clip(a, 0, 1) ** (1 / 2.2)
            ob = oiio.ImageBuf(oiio.ImageSpec(RES[0], RES[1], 3, oiio.UINT8))
            ob.set_pixels(oiio.ROI(0, RES[0], 0, RES[1], 0, 1, 0, 3), view.astype(np.float32))
            ob.write(os.path.join(OUT, f"225_{kind}_{n}.png"))
            rows.append({"count": n, "kind": kind, "sec": round(sec, 2), "sec_ref64": round(sec_ref, 2),
                         "noise": round(noise, 4), "mean": round(float(lb.mean()), 4)})
            print(rows[-1], flush=True)
            os.remove(img)
            os.remove(ref)
    set_lights(10, True)
    set_balls(10, False)
    city.layoutChildren()
    glow_geo.layoutChildren()
    hou_tools.save_hip(os.path.join(OUT, "225_scene.hipnc"))
    hou_tools.write_graph(glow_geo.path(), os.path.join(OUT, "225_graph.json"), title="実験225")
    sop_bench.save(225, rows, {"res": RES, "total": TOTAL, "radius": R})


if __name__ == "__main__":
    main()
