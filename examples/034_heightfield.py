"""実験034 — HeightField で地形を作る。ポリゴンの地形と何が違うのか。

実験007では grid に mountain をかけて地形を作った。点を並べて高さをずらす、
ポリゴンのやり方である。Houdini にはもう1つ、<strong>HeightField</strong> という
仕組みがあり、こちらは専用のノードが45種もある。

違いは持ち方にある。HeightField は<strong>高さを2次元のボリュームとして持つ</strong>。
面も点も持たない。そのぶん、ポリゴンでは難しい「浸食」のような計算ができる。

確かめること。

  A. HeightField は中身として何を持っているか。メッシュに直すと何になるか
  B. 解像度は何が決めるのか（size / gridspacing / gridsamples のどれか）
  C. 浸食（erode）は何を変えるか。レイヤー・高さ・勾配・時間
  D. 浸食は地形をなだらかにするのか

D は否定できる形にする。浸食して勾配が<strong>上がる</strong>なら、
「削ってならす」という見立てが違うことになる。

    hython examples/034_heightfield.py
    hython examples/034_heightfield.py shot raw
    hython examples/034_heightfield.py shot eroded
"""

import json
import os
import sys
import time

import hou
import numpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

SIZE = 200.0
SPACING = 2.0
AMP = 30.0
ELEMENT = 80.0
SHOT_RES = (760, 520)
SHOT_AMP = 120.0
BBOX_PATH = os.path.join(OUT, "034_bbox.json")


def build(size=SIZE, spacing=SPACING, iterations=0, amp=AMP,
          element=ELEMENT):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, 2)
    geo = hou.node("/obj").createNode("geo", "terrain")

    field = geo.createNode("heightfield", "field")
    field.parm("sizex").set(size)
    field.parm("sizey").set(size)
    field.parm("gridspacing").set(spacing)

    noise = geo.createNode("heightfield_noise", "noise")
    noise.setFirstInput(field)
    noise.parm("amp").set(amp)
    noise.parm("elementsize").set(element)

    upstream = noise
    if iterations:
        erode = geo.createNode("heightfield_erode", "erode")
        erode.setFirstInput(noise)
        erode.parm("iterations").set(iterations)
        upstream = erode

    mesh = geo.createNode("convertheightfield", "mesh")
    mesh.setFirstInput(upstream)
    mesh.setDisplayFlag(True)
    mesh.setRenderFlag(True)

    geo.layoutChildren()
    return geo, field, noise, upstream, mesh


def layer(geometry, name):
    """名前の付いたボリュームを取り出す。"""
    for prim in geometry.prims():
        if prim.attribValue("name") == name:
            return prim
    return None


def height_grid(geometry):
    """高さのボリュームを numpy の2次元配列にする。"""
    prim = layer(geometry, "height")
    if prim is None:
        return None
    res = prim.resolution()
    values = numpy.asarray(prim.allVoxels(), dtype=numpy.float64)
    return values.reshape(res[2], res[1], res[0])[0]


def slope_of(grid, spacing):
    """隣のマスとの高さの差を、マスの間隔で割ったもの（勾配）。

    実験007と同じ考え方の指標。解像度が同じなら比べられる。
    """
    dx = numpy.abs(numpy.diff(grid, axis=1)) / spacing
    dy = numpy.abs(numpy.diff(grid, axis=0)) / spacing
    return float((dx.mean() + dy.mean()) / 2.0)


def describe(grid):
    return {"min": float(grid.min()), "max": float(grid.max()),
            "mean": float(grid.mean()), "std": float(grid.std())}


def main():
    stats = {"size": SIZE, "spacing": SPACING, "amp": AMP,
             "element": ELEMENT}

    print("A. HeightField は何を持っているか")
    geo, field, noise, upstream, mesh = build()
    plain = field.geometry()
    noisy = noise.geometry()
    meshed = mesh.geometry()
    res = layer(noisy, "height").resolution()
    stats["contents"] = {
        "hf_points": len(noisy.points()), "hf_prims": len(noisy.prims()),
        "layers": [p.attribValue("name") for p in noisy.prims()],
        "resolution": list(res),
        "mesh_points": len(meshed.points()), "mesh_prims": len(meshed.prims()),
    }
    print(f"   HeightField: {len(noisy.points())}点 / "
          f"{len(noisy.prims())}プリミティブ")
    print(f"   レイヤー: {stats['contents']['layers']}")
    print(f"   高さの解像度: {res[0]}×{res[1]}×{res[2]}")
    print(f"   メッシュに直すと: {len(meshed.points())}点 / "
          f"{len(meshed.prims())}面")
    print(f"   {res[0]}×{res[1]} = {res[0] * res[1]} なので、"
          f"点の数は解像度そのもの")

    print("\nB. 解像度は何が決めるか")
    table = []
    print(f"   {'size':>8} {'gridspacing':>12} {'解像度':>14} "
          f"{'size÷spacing':>14}")
    for size, spacing in ((200.0, 2.0), (200.0, 1.0), (200.0, 4.0),
                          (400.0, 2.0), (100.0, 2.0)):
        geo, field, noise, upstream, mesh = build(size=size, spacing=spacing)
        res = layer(noise.geometry(), "height").resolution()
        row = {"size": size, "spacing": spacing,
               "resolution": [res[0], res[1]],
               "expected": int(size / spacing)}
        table.append(row)
        print(f"   {size:>8} {spacing:>12} {res[0]:>6}×{res[1]:<7} "
              f"{int(size / spacing):>14}")
    stats["resolution_table"] = table
    ok = all(r["resolution"][0] == r["expected"] for r in table)
    print(f"   すべて size ÷ gridspacing と一致: {'はい' if ok else 'いいえ'}")
    stats["resolution_rule_holds"] = ok

    print("\n   gridsamples を変えても解像度は動くか")
    samples = []
    for value in (128, 512, 1024):
        geo, field, noise, upstream, mesh = build()
        field.parm("gridsamples").set(value)
        res = layer(noise.geometry(), "height").resolution()
        samples.append({"gridsamples": value, "resolution": [res[0], res[1]]})
        print(f"   gridsamples {value:>5} → {res[0]}×{res[1]}")
    stats["gridsamples"] = samples

    print("\nC. 浸食は何を変えるか")
    rows = []
    base_grid = None
    print(f"   {'回数':>5} {'秒':>7} {'レイヤー':>6} {'最低':>9} {'最高':>9} "
          f"{'平均':>9} {'勾配':>9}")
    for iterations in (0, 1, 2, 4):
        geo, field, noise, upstream, mesh = build(iterations=iterations)
        start = time.perf_counter()
        cooked = upstream.geometry()
        seconds = time.perf_counter() - start
        grid = height_grid(cooked)
        if base_grid is None:
            base_grid = grid
        shape = describe(grid)
        slope = slope_of(grid, SPACING)
        row = {"iterations": iterations, "seconds": seconds,
               "layers": [p.attribValue("name") for p in cooked.prims()],
               "height": shape, "slope": slope}
        rows.append(row)
        print(f"   {iterations:>5} {seconds:>7.2f} "
              f"{len(row['layers']):>6} {shape['min']:>9.3f} "
              f"{shape['max']:>9.3f} {shape['mean']:>9.3f} {slope:>9.5f}")
    stats["erosion"] = rows
    print(f"   浸食で増えるレイヤー: "
          f"{[n for n in rows[-1]['layers'] if n not in rows[0]['layers']]}")

    print("\nD. 浸食は地形をなだらかにするか")
    first, last = rows[0], rows[-1]
    change = (last["slope"] - first["slope"]) / first["slope"] * 100
    print(f"   勾配 {first['slope']:.5f} → {last['slope']:.5f}"
          f"（{change:+.1f}%）")
    print(f"   高さの幅 "
          f"{first['height']['max'] - first['height']['min']:.3f} → "
          f"{last['height']['max'] - last['height']['min']:.3f}")
    print(f"   なだらかになったか: "
          f"{'はい' if last['slope'] < first['slope'] else 'いいえ'}")
    stats["smoother"] = last["slope"] < first["slope"]
    stats["slope_change_percent"] = change

    print("\nE. amp は高さの倍率か（実験006と同じ問い）")
    amps = []
    print(f"   {'amp':>8} {'高さの幅':>10} {'幅÷amp':>10}")
    for amp in (7.5, 15.0, 30.0, 60.0):
        geo, field, noise, upstream, mesh = build(amp=amp)
        grid = height_grid(noise.geometry())
        span = float(grid.max() - grid.min())
        amps.append({"amp": amp, "span": span, "ratio": span / amp})
        print(f"   {amp:>8} {span:>10.4f} {span / amp:>10.5f}")
    stats["amp_table"] = amps
    ratios = [r["ratio"] for r in amps]
    print(f"   幅÷amp のばらつき: {max(ratios) - min(ratios):.6f}")
    stats["amp_is_pure_scale"] = (max(ratios) - min(ratios)) < 1e-4

    with open(os.path.join(OUT, "034_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    geo, field, noise, upstream, mesh = build(iterations=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "034_graph.json"),
                          title="実験034 — HeightField で地形を作る")
    hou_tools.save_hip(os.path.join(OUT, "034_heightfield.hipnc"))
    print("\n保存: out/034_stats.json, out/034_graph.json, "
          "out/034_heightfield.hipnc")


def shot(case):
    """レンダはプロセスの最後に1枚だけ（実験027で学んだ癖）。"""
    # 画では起伏を見せたいので、測定より大きい amp にする。
    # amp は純粋な倍率（E で確かめた）なので、形は変わらず高さだけ伸びる。
    geo, field, noise, upstream, mesh = build(
        iterations=4 if case == "eroded" else 0, amp=SHOT_AMP)
    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = mesh.geometry().boundingBox()
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"034_{case}.png")
    hou_tools.render_preview(mesh.path(), png, res=SHOT_RES,
                             direction=(0.9, 0.38, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/034_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
