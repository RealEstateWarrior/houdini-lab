"""実験041 — 凸凹の付け方3通り。輪郭が変わるのはどれか。

面を凸凹させる方法は3つある。

  1. ジオメトリを動かす … 点そのものを動かす。データが変わる
  2. displacement     … レンダのときだけ面を動かす。点は動かない
  3. bump             … 面は動かさず、光の当たり方だけ凸凹に見せる

見た目はどれも似る。<strong>決定的な違いは輪郭（シルエット）に出る</strong>はずである。
本当に面が動いていればフチがぎざぎざになり、光のごまかしならフチは滑らかなままになる。

そこで<strong>輪郭の長さ</strong>を測る。書き出した画の透明度から、
地形と背景の境目になっている画素を数えれば、フチのぎざぎざ具合が分かる。

  A. 3通りで、点の位置は変わるか
  B. 3通りで、輪郭の長さは変わるか
  C. 3通りで、画の細かさと時間はどうなるか

否定できる形にする。bump で輪郭の長さが増えるなら、
「bump は形を変えない」という見立てが違う。

    hython examples/041_displacement.py
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
BUMP = 6.0          # 凸凹の大きさ（地形の座標で）
TEXTURE = None      # 下ごしらえで作る凸凹のもと


def build(mode="plain"):
    """mode: plain / geo / disp / bump"""
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

    last = mesh
    if mode == "geo":
        # 点そのものを動かす。面の向きは高さから作る
        # （normal SOP の N はバーテックスに付くので点からは読めない。実験030・036）
        move = geo.createNode("attribwrangle", "displace")
        move.setFirstInput(mesh)
        move.setInput(1, erode)
        move.parm("class").set(2)
        move.parm("snippet").set(
            "float e = 2.0;\n"
            'float h0 = volumesample(1, "height", @P);\n'
            'float hx = volumesample(1, "height", @P + set(e, 0, 0));\n'
            'float hz = volumesample(1, "height", @P + set(0, 0, e));\n'
            "vector n = normalize(set(-(hx - h0) / e, 1.0, -(hz - h0) / e));\n"
            "// レンダ側の noise と同じ考え方の凸凹を、点そのものに足す\n"
            f"float d = noise(@P * 0.35) - 0.5;\n"
            f"@P += n * d * {BUMP};")
        last = move

    mat = hou.node("/mat") or hou.node("/").createNode("mat")
    shader = mat.createNode("principledshader::2.0", "terrain_mat")
    shader.parm("rough").set(0.75)
    shader.parmTuple("basecolor").set((0.55, 0.48, 0.40))
    if mode == "disp":
        # 同じ画を「高さ」として使う
        shader.parm("dispTex_enable").set(True)
        shader.parm("dispTex_texture").set(TEXTURE.replace("\\", "/"))
        shader.parm("dispTex_scale").set(BUMP)
    elif mode == "bump":
        # まったく同じ画を「凸凹に見せる」ためだけに使う。
        # 最初テクスチャを指定せずに有効化だけしたら、輪郭も細かさも
        # 何もしない場合と完全に同じ数字になり、効いていないと分かった。
        shader.parm("baseBumpAndNormal_enable").set(True)
        shader.parm("baseBumpAndNormal_type").set("bump")
        shader.parm("baseBump_bumpTexture").set(TEXTURE.replace("\\", "/"))
        shader.parm("baseBump_bumpScale").set(BUMP)

    assign = geo.createNode("material", "assign")
    assign.setFirstInput(last)
    assign.parm("shop_materialpath1").set(shader.path())
    assign.setDisplayFlag(True)
    assign.setRenderFlag(True)

    geo.layoutChildren()
    return geo, mesh, last, assign


def render(tag, node, bbox):
    hou_tools._ensure_lights()
    hou.node("/obj/report_dome").parm("light_intensity").set(DOME)
    hou.node("/obj/report_key").parm("light_intensity").set(KEY)
    obj = hou.node("/obj")
    cam = obj.node("report_cam") or obj.createNode("cam", "report_cam")
    cam.parm("resx").set(RES[0])
    cam.parm("resy").set(RES[1])
    hou_tools._frame_camera(cam, bbox, RES, (0.55, 0.30, 1.0), margin=1.04)

    karma = hou.node("/out").createNode("karma", f"exp041_{tag}")
    karma.parm("camera").set(cam.path())
    karma.parm("denoiser").set("off")
    karma.parm("resolutionx").set(RES[0])
    karma.parm("resolutiony").set(RES[1])
    karma.parm("samplesperpixel").set(SAMPLES)
    karma.parm("varianceaa_maxsamples").set(SAMPLES)
    path = os.path.join(OUT, f"041_{tag}.png")
    karma.parm("picture").set(path.replace("\\", "/"))
    start = time.perf_counter()
    karma.render(frame_range=(1, 1, 1), verbose=False)
    return path, time.perf_counter() - start


def measure(path):
    """輪郭の長さと、画の細かさ。

    輪郭＝地形と背景が隣り合っている画素の数。
    面が本当に動いていればフチがぎざぎざになり、この数が増える。
    """
    image = Image.open(path).convert("RGBA")
    array = numpy.asarray(image, dtype=numpy.float64)
    mask = array[:, :, 3] > 128
    grey = array[:, :, :3].mean(axis=2)

    # 左右・上下の隣と、地形かどうかが食い違う場所の数
    edge_x = (mask[:, 1:] != mask[:, :-1]).sum()
    edge_y = (mask[1:, :] != mask[:-1, :]).sum()

    dx = numpy.abs(numpy.diff(grey, axis=1))
    dxm = mask[:, 1:] & mask[:, :-1]
    dy = numpy.abs(numpy.diff(grey, axis=0))
    dym = mask[1:, :] & mask[:-1, :]
    return {
        "pixels": int(mask.sum()),
        "perimeter": int(edge_x + edge_y),
        "mean": float(grey[mask].mean()),
        "sd": float(grey[mask].std()),
        "detail": float((dx[dxm].mean() + dy[dym].mean()) / 2.0),
    }


def make_texture(path, res=1024, element=0.04, rough=0.6):
    """凸凹のもとになる画を COP で作る（実験039・040と同じ手順）。"""
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
    return path


def main():
    global TEXTURE
    stats = {"res": list(RES), "samples": SAMPLES, "bump": BUMP}

    print("下ごしらえ: 凸凹のもとになる画を作る")
    TEXTURE = make_texture(os.path.join(OUT, "041_tex.png"))
    print(f"   {os.path.basename(TEXTURE)}")
    stats["texture"] = os.path.basename(TEXTURE)

    print("\nA・B・C. 4通りを同じカメラで撮る")
    rows = []
    base_bbox = None
    print(f"   {'やり方':>16} {'点の数':>8} {'高さの幅':>10} {'秒':>7} "
          f"{'輪郭':>8} {'細かさ':>9} {'ばらつき':>10}")
    for label, mode in (("何もしない", "plain"),
                        ("ジオメトリを動かす", "geo"),
                        ("displacement", "disp"),
                        ("bump", "bump")):
        geo, mesh, last, assign = build(mode=mode)
        before = mesh.geometry()
        after = last.geometry()
        ys_before = [p.position()[1] for p in before.points()]
        ys_after = [p.position()[1] for p in after.points()]
        moved = max(abs(a - b) for a, b in zip(ys_before, ys_after))

        bbox = assign.geometry().boundingBox()
        if base_bbox is None:
            base_bbox = bbox
        path, seconds = render(mode, assign, base_bbox)
        info = measure(path)
        info.update({"label": label, "mode": mode, "seconds": seconds,
                     "points": len(after.points()),
                     "moved": float(moved),
                     "span": float(max(ys_after) - min(ys_after)),
                     "file": os.path.basename(path)})
        rows.append(info)
        print(f"   {label:>16} {info['points']:>8} {info['span']:>10.3f} "
              f"{seconds:>7.2f} {info['perimeter']:>8} "
              f"{info['detail']:>9.4f} {info['sd']:>10.2f}")
    stats["modes"] = rows

    plain = rows[0]
    print(f"\n   点が動いたか（元との最大の差）")
    for row in rows:
        print(f"     {row['label']:>16}: {row['moved']:.6f}")

    print(f"\n   輪郭の長さ（何もしないときを1とする）")
    for row in rows:
        print(f"     {row['label']:>16}: {row['perimeter']:>6} "
              f"（{row['perimeter'] / plain['perimeter']:.3f}倍）")
    stats["perimeter_ratio"] = {r["mode"]: r["perimeter"] / plain["perimeter"]
                                for r in rows}

    bump = next(r for r in rows if r["mode"] == "bump")
    disp = next(r for r in rows if r["mode"] == "disp")
    geo_row = next(r for r in rows if r["mode"] == "geo")
    print(f"\n   bump は輪郭を変えたか: "
          f"{'はい' if abs(bump['perimeter'] / plain['perimeter'] - 1) > 0.01 else 'いいえ'}")
    print(f"   displacement は輪郭を変えたか: "
          f"{'はい' if abs(disp['perimeter'] / plain['perimeter'] - 1) > 0.01 else 'いいえ'}")
    print(f"   ジオメトリを動かすと輪郭は変わったか: "
          f"{'はい' if abs(geo_row['perimeter'] / plain['perimeter'] - 1) > 0.01 else 'いいえ'}")

    with open(os.path.join(OUT, "041_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, mesh, last, assign = build(mode="geo")
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "041_graph.json"),
                          title="実験041 — 凸凹の付け方3通り")
    hou_tools.save_hip(os.path.join(OUT, "041_disp.hipnc"))
    print("\n保存: out/041_stats.json, out/041_graph.json, out/041_disp.hipnc")


if __name__ == "__main__":
    main()
