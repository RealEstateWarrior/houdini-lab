"""実験025 — シミュレーションのキャッシュ。速くなるが、結果は変わっていないか。

ここまでの実験で、同じ計算を何度も回してきた。018では同じ煙を何十回も描き直した。
シミュレーションは前のフレームの結果から次を作るので、途中から見ることができず、
毎回1フレーム目から計算し直している。

<code>filecache</code> は結果をファイルに書き出し、次からはそれを読む。
当然速くなるはずだが、<strong>速くなっても結果が変わっていたら意味がない</strong>。
両方を測る。

  時間 … 計算しながら回した場合と、ファイルから読んだ場合
  結果 … 密度の合計。読み込んだ結果が、計算した結果と<strong>完全に一致</strong>するか

「ほぼ同じ」ではなく「完全に同じ」を求める。書き出しと読み込みで値が変われば、
以降の測定がすべて信用できなくなる。

    hython examples/025_cache.py
"""

import json
import os
import shutil
import sys
import time

import hou
import numpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
CACHE_DIR = os.path.join(OUT, "025_cache")

import hou_tools  # noqa: E402

FRAMES = list(range(1, 41))
CHECK = [1, 10, 20, 30, 40]
VOXEL = 0.05


def build():
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "smoke")

    emitter = geo.createNode("sphere", "emitter")
    emitter.parm("type").set(2)
    emitter.parmTuple("rad").set((0.22, 0.22, 0.22))
    emitter.parmTuple("t").set((0.0, -0.9, 0.0))
    emitter.parm("rows").set(24)
    emitter.parm("cols").set(24)

    src = geo.createNode("pyrosource", "src")
    src.setFirstInput(emitter)
    src.parm("attributes").set(2)
    src.parm("attribute1").set("density")
    src.parm("attribute2").set("temperature")

    rast = geo.createNode("volumerasterizeattributes", "rasterize")
    rast.setFirstInput(src)
    rast.parm("attributes").set("density temperature")
    rast.parm("voxelsize").set(VOXEL)

    solver = geo.createNode("pyrosolver", "solve")
    solver.setFirstInput(rast)

    cache = geo.createNode("filecache::2.0", "cache")
    cache.setFirstInput(solver)
    cache.parm("filemethod").set(1)          # 自分でパスを決める
    cache.parm("file").set(os.path.join(CACHE_DIR, "smoke.$F4.bgeo.sc")
                           .replace("\\", "/"))
    cache.parm("trange").set(1)              # フレーム範囲を書き出す
    # f1 / f2 の既定は $FSTART / $FEND という式で、シーンの範囲（1〜240）を指す。
    # 数値を入れるだけでは式が残るので、式を消してから入れる。
    for name, value in (("f1", FRAMES[0]), ("f2", FRAMES[-1])):
        parm = cache.parm(name)
        parm.deleteAllKeyframes()
        parm.set(value)
    cache.setDisplayFlag(True)
    cache.setRenderFlag(True)
    return geo, solver, cache


def density_total(node, frame):
    hou.setFrame(frame)
    geo = node.geometry()
    if geo is None:
        return None
    for prim in geo.prims():
        if prim.type() == hou.primType.Volume and prim.attribValue("name") == "density":
            values = numpy.asarray(prim.allVoxels(), dtype=numpy.float64)
            return float(values[values > 1e-4].sum())
    return None


def sweep(node, frames):
    start = time.perf_counter()
    values = [density_total(node, f) for f in frames]
    return time.perf_counter() - start, values


def main():
    if os.path.isdir(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)

    hou.playbar.setFrameRange(FRAMES[0], FRAMES[-1])
    geo, solver, cache = build()
    print(f"書き出す範囲: {cache.parm('f1').eval():.0f}〜"
          f"{cache.parm('f2').eval():.0f} フレーム")

    print("1. 計算しながら40フレーム回す（キャッシュなし）")
    cache.parm("loadfromdisk").set(False)
    sim_sec, sim_values = sweep(cache, FRAMES)
    print(f"   {sim_sec:.2f}秒")

    print("\n2. 書き出す")
    start = time.perf_counter()
    cache.parm("execute").pressButton()
    write_sec = time.perf_counter() - start
    files = sorted(f for f in os.listdir(CACHE_DIR) if f.endswith(".bgeo.sc"))
    size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)
    print(f"   {write_sec:.2f}秒 / {len(files)}ファイル / "
          f"{size / 1024 / 1024:.1f} MB")

    print("\n3. ファイルから読んで40フレーム回す")
    cache.parm("loadfromdisk").set(True)
    cache.parm("reload").pressButton()
    load_sec, load_values = sweep(cache, FRAMES)
    print(f"   {load_sec:.2f}秒（計算より {sim_sec / load_sec:.1f}倍速い）")

    print("\n4. 結果は変わっていないか")
    print(f"{'フレーム':>8} {'計算した値':>16} {'読んだ値':>16} {'差':>14}")
    worst = 0.0
    mismatch = 0
    for frame in CHECK:
        i = FRAMES.index(frame)
        a, b = sim_values[i], load_values[i]
        if a is None or b is None:
            print(f"{frame:8d}  取れなかった")
            continue
        diff = abs(a - b)
        worst = max(worst, diff)
        if diff != 0.0:
            mismatch += 1
        print(f"{frame:8d} {a:16.6f} {b:16.6f} {diff:14.10f}")

    all_same = all(a == b for a, b in zip(sim_values, load_values)
                   if a is not None and b is not None)
    print(f"\n   40フレーム全部で完全に一致: {'はい' if all_same else 'いいえ'}")
    print(f"   最大の差: {worst:.10f}")

    stats = {"frames": len(FRAMES), "sim_sec": sim_sec, "write_sec": write_sec,
             "load_sec": load_sec, "speedup": sim_sec / load_sec,
             "files": len(files), "bytes": size,
             "identical": all_same, "worst_diff": worst,
             "check": [{"frame": f, "sim": sim_values[FRAMES.index(f)],
                        "load": load_values[FRAMES.index(f)]} for f in CHECK]}
    with open(os.path.join(OUT, "025_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "025_graph.json"),
                          title="実験025 — シミュレーションのキャッシュ")
    hou_tools.save_hip(os.path.join(OUT, "025_cache.hipnc"))
    print("\n保存: out/025_stats.json, out/025_graph.json, out/025_cache.hipnc")


if __name__ == "__main__":
    main()
