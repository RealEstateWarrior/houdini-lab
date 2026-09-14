"""実験040 — 作ったテクスチャを地形に貼る。本当に貼れているか。

実験039で Copernicus のノイズを画像として書き出した。
実験038で地形を Karma で出した。今回はその2つをつなぐ。

貼ったつもりで貼れていない、というのはよくある。<strong>貼れたかどうかを
画の数字で判定する</strong>。テクスチャを貼れば、面の中に細かい濃淡が出るはずなので、

  <strong>貼る前と貼ったあとで、画の「細かさ」が増える</strong>

はずである。増えなければ貼れていない。

  A. UV はあるか。無ければテクスチャは貼りようがない
  B. テクスチャを貼ると、画の細かさは増えるか
  C. テクスチャの解像度を変えると、画はどう変わるか

    hython examples/040_texture_on_terrain.py
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
RES = (720, 460)
SAMPLES = 24
KEY = 0.3
DOME = 1.0


def make_texture(path, res=1024, element=0.02, rough=0.6):
    """COP でノイズを作り、画像として書き出す（実験039と同じ手順）。"""
    net = hou.node("/obj").createNode("copnet", "cops")
    net.parm("setres").set(True)
    net.parm("res1").set(res)
    net.parm("res2").set(res)

    noise = net.createNode("fractalnoise", "noise")
    noise.parm("elementsize").set(element)
    noise.parm("rough").set(rough)
    # 岩肌らしい色みにする。明暗を茶〜灰の間に収める
    noise.parm("post_dogain").set(True)
    noise.parm("post_gain").set(0.55)

    rop = net.createNode("rop_image", "out")
    rop.setFirstInput(noise)
    rop.parm("trange").set(0)
    rop.parm("copoutput").set(path.replace("\\", "/"))
    rop.parm("execute").pressButton()
    return net, path


def build(texture=None, tex_res=1024):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
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

    mat = hou.node("/mat") or hou.node("/").createNode("mat")
    shader = mat.createNode("principledshader::2.0", "terrain_mat")
    shader.parm("rough").set(0.75)
    if texture:
        shader.parm("basecolor_useTexture").set(True)
        shader.parm("basecolor_texture").set(texture.replace("\\", "/"))
    else:
        shader.parmTuple("basecolor").set((0.55, 0.48, 0.40))

    assign = geo.createNode("material", "assign")
    assign.setFirstInput(mesh)
    assign.parm("shop_materialpath1").set(shader.path())
    assign.setDisplayFlag(True)
    assign.setRenderFlag(True)

    geo.layoutChildren()
    return geo, mesh, assign


def render(tag, node, bbox):
    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(DOME)
    hou.node("/obj/report_key").parm("light_intensity").set(KEY)
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    hou_tools._frame_camera(cam, bbox, RES, (0.7, 0.5, 1.0), margin=1.04)

    karma = hou.node("/out").createNode("karma", f"exp040_{tag}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"040_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    return path, time.perf_counter() - start


def measure(path, sample=1):
    """地形の部分だけを取り出して、明るさと細かさを測る。

    背景と地形は透明度で分ける（実験038で、明るさで分けて失敗した）。
    """
    image = Image.open(path).convert("RGBA")
    array = numpy.asarray(image, dtype=numpy.float64)[::sample, ::sample]
    alpha = array[:, :, 3]
    grey = array[:, :, :3].mean(axis=2)
    mask = alpha > 128
    if not mask.any():
        return {"pixels": 0}
    # 細かさ＝隣り合う画素の差。地形どうしが隣り合うところだけ数える
    dx = numpy.abs(numpy.diff(grey, axis=1))
    dxm = mask[:, 1:] & mask[:, :-1]
    dy = numpy.abs(numpy.diff(grey, axis=0))
    dym = mask[1:, :] & mask[:-1, :]
    detail = float((dx[dxm].mean() + dy[dym].mean()) / 2.0)
    values = grey[mask]
    return {
        "pixels": int(mask.sum()),
        "mean": float(values.mean()),
        "sd": float(values.std()),
        "detail": detail,
    }


def main():
    stats = {"res": list(RES), "samples": SAMPLES}

    print("A. 地形は UV を持っているか")
    geo, mesh, assign = build(texture=None)
    attribs = sorted(a.name() for a in mesh.geometry().pointAttribs())
    has_uv = "uv" in attribs
    print(f"   convertheightfield の出力の点アトリビュート: {attribs}")
    print(f"   uv はあるか: {'はい' if has_uv else 'いいえ'}")
    stats["mesh_attribs"] = attribs
    stats["has_uv"] = has_uv

    print("\n下ごしらえ: テクスチャを作る（Copernicus）")
    tex_paths = {}
    for res in (256, 1024):
        hou.hipFile.clear(suppress_save_prompt=True)
        path = os.path.join(OUT, f"040_tex_{res}.png")
        make_texture(path, res=res)
        info = Image.open(path)
        tex_paths[res] = path
        print(f"   {res:>5} → {os.path.basename(path)} {info.size}")
    stats["textures"] = {str(k): os.path.basename(v)
                         for k, v in tex_paths.items()}

    print("\nB・C. 貼る前と、貼ったあと")
    rows = []
    plan = [("なし", None, None), ("256", tex_paths[256], 256),
            ("1024", tex_paths[1024], 1024)]
    print(f"   {'テクスチャ':>10} {'秒':>7} {'明るさ':>9} {'ばらつき':>10} "
          f"{'細かさ':>9}")
    for label, texture, res in plan:
        geo, mesh, assign = build(texture=texture)
        bbox = assign.geometry().boundingBox()
        tag = "plain" if texture is None else f"tex{res}"
        path, seconds = render(tag, assign, bbox)
        info = measure(path)
        info.update({"label": label, "seconds": seconds,
                     "file": os.path.basename(path)})
        rows.append(info)
        print(f"   {label:>10} {seconds:>7.2f} {info['mean']:>9.2f} "
              f"{info['sd']:>10.2f} {info['detail']:>9.4f}")
    stats["renders"] = rows

    plain = rows[0]
    big = rows[-1]
    lift = big["detail"] / plain["detail"] if plain["detail"] else 0
    print(f"\n   1024 を貼ると、細かさは {plain['detail']:.4f} → "
          f"{big['detail']:.4f}（{lift:.2f}倍）")
    print(f"   貼れたと言えるか: {'はい' if lift > 1.2 else 'いいえ'}")
    stats["detail_lift"] = lift
    stats["applied"] = lift > 1.2

    small = rows[1]
    print(f"   256 と 1024 の細かさ: {small['detail']:.4f} 対 "
          f"{big['detail']:.4f}（{big['detail'] / small['detail']:.2f}倍）")
    stats["res_ratio"] = big["detail"] / small["detail"]

    with open(os.path.join(OUT, "040_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, mesh, assign = build(texture=tex_paths[1024])
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "040_graph.json"),
                          title="実験040 — テクスチャを地形に貼る")
    hou_tools.save_hip(os.path.join(OUT, "040_texture.hipnc"))
    print("\n保存: out/040_stats.json, out/040_graph.json, "
          "out/040_texture.hipnc")


if __name__ == "__main__":
    main()
