"""手順ページ用の画像を作る — 「模様を作って貼る」（実験039〜041の内容）。

Houdini の中だけで模様の画を作り（Copernicus）、それを材質に貼って、
色として使う・凸凹に見せる・本当に形を変える、の3通りを撮り比べる。

輪郭を見れば、どれが本当に形を変えたかが分かる。

    hython examples/guide_texture.py
"""

import os
import sys
import time

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

RES = (640, 480)
SAMPLES = 9
PREFIX = "guide_tex"
TEXTURE = os.path.join(OUT, f"{PREFIX}_noise.png")
DOME = 1.0
KEY = 3.0
SCALE = 0.12


def make_texture(path, res=1024, element=0.06, rough=0.6):
    """模様のもとになる画を COP で作る。"""
    hou.hipFile.clear(suppress_save_prompt=True)
    net = hou.node("/obj").createNode("copnet", "cops")
    net.parm("setres").set(True)
    net.parm("res1").set(res)
    net.parm("res2").set(res)
    noise = net.createNode("fractalnoise", "noise")
    noise.parm("elementsize").set(element)
    noise.parm("rough").set(rough)
    rop = net.createNode("rop_image", "out")
    rop.setFirstInput(noise)
    rop.parm("trange").set(0)
    rop.parm("copoutput").set(path.replace("\\", "/"))
    rop.parm("execute").pressButton()
    print(f"  模様の画: {os.path.basename(path)}")
    return path


def build(mode):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    geo = hou.node("/obj").createNode("geo", "ball")

    ball = geo.createNode("sphere", "ball")
    ball.parm("type").set(2)
    ball.parm("rows").set(120)
    ball.parm("cols").set(120)

    uv = geo.createNode("uvunwrap", "uv")
    uv.setFirstInput(ball)

    normal = geo.createNode("normal", "normals")
    normal.setFirstInput(uv)

    mat = hou.node("/mat") or hou.node("/").createNode("mat")
    shader = mat.createNode("principledshader::2.0", f"tex_{mode}")
    shader.parm("rough").set(0.6)
    tex = TEXTURE.replace("\\", "/")

    if mode == "color":
        shader.parm("basecolor_useTexture").set(True)
        shader.parm("basecolor_texture").set(tex)
    elif mode == "bump":
        shader.parm("baseBumpAndNormal_enable").set(True)
        shader.parm("baseBumpAndNormal_type").set("bump")
        shader.parm("baseBump_bumpTexture").set(tex)
        shader.parm("baseBump_bumpScale").set(SCALE)
    elif mode == "disp":
        shader.parm("dispTex_enable").set(True)
        shader.parm("dispTex_texture").set(tex)
        shader.parm("dispTex_scale").set(SCALE)

    assign = geo.createNode("material", "assign")
    assign.setFirstInput(normal)
    assign.parm("shop_materialpath1").set(shader.path())
    assign.setDisplayFlag(True)
    assign.setRenderFlag(True)
    geo.layoutChildren()
    return geo, assign


def render(mode):
    geo, last = build(mode)
    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(DOME)
    hou.node("/obj/report_key").parm("light_intensity").set(KEY)
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    bbox = hou.BoundingBox(-1.2, -1.2, -1.2, 1.2, 1.2, 1.2)
    hou_tools._frame_camera(cam, bbox, RES, (0.5, 0.3, 1.0), margin=1.05)

    karma = hou.node("/out").createNode("karma", f"guidetex_{mode}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"{PREFIX}_{mode}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    print(f"  {mode}: {time.perf_counter() - start:.1f}秒 → "
          f"{os.path.basename(path)}")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "texture":
        make_texture(TEXTURE)
    elif what == "all":
        make_texture(TEXTURE)
    else:
        render(what)
