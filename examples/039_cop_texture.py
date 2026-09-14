"""実験039 — Copernicus でテクスチャを作る。画の細かさは何が決めるのか。

ここまではすべて形（ジオメトリ）の話だった。Houdini には画そのものを作る
仕組みもある。<strong>Copernicus</strong>（COP）で、専用のノードが262種ある。

地形に貼る模様や、汚し、マスク。テクスチャを外で作って読み込むのではなく、
Houdini の中で手続きとして作れる。

確かめること。

  A. 画の大きさ（解像度）はどこで決まるのか
  B. ノイズのパラメータは、画の細かさにどう効くか
  C. 細かさの指標は、解像度によらない量になるか

C は実験007と同じ問いである。あのときは地形の勾配が解像度とともに増え続け、
「解像度によらない量」にはならなかった。画でも同じことが起きるはずだが、
確かめていない。

    hython examples/039_cop_texture.py
"""

import json
import os
import sys

import hou
import numpy
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

ELEMENT = 0.10
ROUGH = 0.5
OCT = 8


def build(res=None, element=ELEMENT, rough=ROUGH, oct_count=OCT):
    """ノイズ1枚だけの COP ネットワーク。

    解像度は copnet 側で決める。ノイズのノードには解像度の欄が無い。
    """
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 1)
    net = hou.node("/obj").createNode("copnet", "cops")
    if res is not None:
        net.parm("setres").set(True)
        net.parm("res1").set(res)
        net.parm("res2").set(res)

    noise = net.createNode("fractalnoise", "noise")
    noise.parm("elementsize").set(element)
    noise.parm("rough").set(rough)
    noise.parm("oct").set(oct_count)

    rop = net.createNode("rop_image", "out")
    rop.setFirstInput(noise)
    rop.parm("trange").set(0)
    return net, noise, rop


def write(rop, path):
    rop.parm("copoutput").set(path.replace("\\", "/"))
    rop.parm("execute").pressButton()
    return path


def measure(path):
    """書き出した画から、明るさと「細かさ」を測る。

    細かさ＝隣り合う画素の差の平均。実験004・007で使った指標と同じ考え方で、
    なだらかな模様なら小さく、細かい模様なら大きくなる。
    """
    image = Image.open(path).convert("L")
    array = numpy.asarray(image, dtype=numpy.float64)
    dx = numpy.abs(numpy.diff(array, axis=1)).mean()
    dy = numpy.abs(numpy.diff(array, axis=0)).mean()
    return {
        "width": int(array.shape[1]), "height": int(array.shape[0]),
        "mean": float(array.mean()), "sd": float(array.std()),
        "min": float(array.min()), "max": float(array.max()),
        "detail": float((dx + dy) / 2.0),
        "levels": int(len(numpy.unique(array))),
    }


def main():
    stats = {"element": ELEMENT, "rough": ROUGH, "oct": OCT}

    print("A. 解像度はどこで決まるか")
    rows = []
    for label, res in (("setres オフ（既定）", None), ("256", 256),
                       ("512", 512), ("1024", 1024)):
        net, noise, rop = build(res=res)
        path = os.path.join(OUT, f"039_res_{res or 'default'}.png")
        write(rop, path)
        info = measure(path)
        info["label"] = label
        rows.append(info)
        print(f"   {label:20} → {info['width']}×{info['height']} / "
              f"階調 {info['levels']}")
    stats["resolution"] = rows
    default = rows[0]
    print(f"   copnet の res1/res2 の既定値は 1024。"
          f"setres がオフのときの実際は {default['width']}×{default['height']}")

    print("\nB. ノイズのパラメータは、細かさにどう効くか（1024×1024）")
    print(f"   {'elementsize':>12} {'明るさ':>9} {'ばらつき':>10} {'細かさ':>9}")
    elements = []
    for element in (0.05, 0.10, 0.20, 0.40):
        net, noise, rop = build(res=1024, element=element)
        path = os.path.join(OUT, f"039_el_{int(element * 100):03d}.png")
        write(rop, path)
        info = measure(path)
        info["element"] = element
        elements.append(info)
        print(f"   {element:>12} {info['mean']:>9.2f} {info['sd']:>10.2f} "
              f"{info['detail']:>9.4f}")
    stats["elementsize"] = elements

    print(f"\n   {'rough':>12} {'明るさ':>9} {'ばらつき':>10} {'細かさ':>9}")
    roughs = []
    for rough in (0.0, 0.25, 0.50, 0.75, 1.0):
        net, noise, rop = build(res=1024, rough=rough)
        path = os.path.join(OUT, f"039_rough_{int(rough * 100):03d}.png")
        write(rop, path)
        info = measure(path)
        info["rough"] = rough
        roughs.append(info)
        print(f"   {rough:>12} {info['mean']:>9.2f} {info['sd']:>10.2f} "
              f"{info['detail']:>9.4f}")
    stats["rough"] = roughs

    print("\nC. 細かさは解像度によらない量になるか（実験007と同じ問い）")
    print(f"   {'解像度':>8} {'細かさ':>9} {'前との比':>10} "
          f"{'細かさ×解像度':>14} {'前との比':>10} {'ばらつき':>10}")
    scale = []
    previous = None
    prev_norm = None
    for res in (128, 256, 512, 1024):
        net, noise, rop = build(res=res)
        path = os.path.join(OUT, f"039_scale_{res}.png")
        write(rop, path)
        info = measure(path)
        info["res"] = res
        info["ratio"] = info["detail"] / previous if previous else None
        # 画素1つぶんの差をそのまま見ると、画素が細かくなるほど小さくなる。
        # 解像度を掛けると「画全体を1とした長さあたりの差」になり、
        # 実験007の勾配と同じ土俵で比べられる。
        info["normalized"] = info["detail"] * res
        info["norm_ratio"] = (info["normalized"] / prev_norm
                              if prev_norm else None)
        scale.append(info)
        col1 = "—" if info["ratio"] is None else f"{info['ratio']:.3f}"
        col2 = "—" if info["norm_ratio"] is None else f"{info['norm_ratio']:.3f}"
        print(f"   {res:>8} {info['detail']:>9.4f} {col1:>10} "
              f"{info['normalized']:>14.1f} {col2:>10} {info['sd']:>10.2f}")
        previous = info["detail"]
        prev_norm = info["normalized"]
    stats["scale"] = scale
    grows = scale[-1]["detail"] > scale[0]["detail"]
    print(f"   解像度を上げると細かさは増えるか: "
          f"{'はい' if grows else 'いいえ'}")
    print(f"   ばらつきは {scale[0]['sd']:.2f} → {scale[-1]['sd']:.2f} で"
          f"{'ほぼ一定' if abs(scale[-1]['sd'] - scale[0]['sd']) < 3 else '変わる'}")
    stats["detail_grows_with_res"] = grows

    with open(os.path.join(OUT, "039_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    net, noise, rop = build(res=1024)
    hou_tools.write_graph(net.path(), os.path.join(OUT, "039_graph.json"),
                          title="実験039 — Copernicus でテクスチャを作る")
    hou_tools.save_hip(os.path.join(OUT, "039_cop.hipnc"))
    print("\n保存: out/039_stats.json, out/039_graph.json, out/039_cop.hipnc")


if __name__ == "__main__":
    main()
