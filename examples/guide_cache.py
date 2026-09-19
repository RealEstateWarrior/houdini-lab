"""手順ページ用の画像と .hipnc（シミュレーションをキャッシュする）。

煙（手順「煙を出す」と同じ組み方）の下に filecache を置き、
書き出す → 読む、を実際に通して、かかった時間とファイル数を記録する。
レンダは最後にまとめて撮る（hython はレンダ後に作り直すと固まる）。

    hython examples/guide_cache.py
"""

import os
import shutil
import sys
import time

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
CACHE_DIR = os.path.join(OUT, "guide_cache_cache")   # out/*_cache/ は .gitignore 済み
FRAMES = (1, 40)

import hou_tools  # noqa: E402

RES = (420, 560)   # 煙は縦に長いので縦長で撮る


def shoot(sop, name, bbox, frame):
    hou.setFrame(frame)
    path = os.path.join(OUT, f"{name}.png")
    hou_tools.render_preview(sop.path(), path, res=RES, shading="smooth",
                             frame_bbox=bbox)
    print(f"  {name}: F{frame}")


def sweep(node):
    start = time.perf_counter()
    for f in range(FRAMES[0], FRAMES[1] + 1):
        hou.setFrame(f)
        node.geometry()
    return time.perf_counter() - start


def main():
    if os.path.isdir(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)

    hou.hipFile.clear(suppress_save_prompt=True)
    hou_tools.save_hip(os.path.join(OUT, "guide_cache.hipnc"))  # $HIP を out/ に決める
    hou.playbar.setFrameRange(1, 240)                           # シーンの範囲は既定のまま
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
    rast.parm("voxelsize").set(0.05)

    solver = geo.createNode("pyrosolver", "solver")
    solver.setFirstInput(rast)

    cache = geo.createNode("filecache::2.0", "cache")
    cache.setFirstInput(solver)
    cache.parm("filemethod").set(1)
    cache.parm("file").set("$HIP/guide_cache_cache/smoke.$F4.bgeo.sc")
    cache.parm("trange").set(1)
    print("f1/f2 の既定:", cache.parm("f1").expression(), "/",
          cache.parm("f2").expression(), "→",
          cache.parm("f1").eval(), "〜", cache.parm("f2").eval())
    for name, value in zip(("f1", "f2"), FRAMES):
        parm = cache.parm(name)
        parm.deleteAllKeyframes()
        parm.set(value)
    print("f1/f2 を数値に:", cache.parm("f1").eval(), "〜", cache.parm("f2").eval())
    cache.setDisplayFlag(True)
    cache.setRenderFlag(True)
    geo.layoutChildren()

    for p in ("filemethod", "trange"):
        t = cache.parm(p).parmTemplate()
        print(f"  {p}: {list(zip(t.menuItems(), t.menuLabels()))}")

    cache.parm("loadfromdisk").set(False)
    sim_sec = sweep(cache)
    print(f"計算しながら {FRAMES[1]}フレーム: {sim_sec:.2f}秒")

    start = time.perf_counter()
    cache.parm("execute").pressButton()
    write_sec = time.perf_counter() - start
    files = sorted(f for f in os.listdir(CACHE_DIR) if f.endswith(".bgeo.sc"))
    size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)
    print(f"書き出し: {write_sec:.2f}秒 / {len(files)}ファイル / {size / 1024 / 1024:.1f} MB")

    cache.parm("loadfromdisk").set(True)
    cache.parm("reload").pressButton()
    load_sec = sweep(cache)
    print(f"読みながら {FRAMES[1]}フレーム: {load_sec:.2f}秒（{sim_sec / load_sec:.1f}倍）")

    hou_tools.save_hip(os.path.join(OUT, "guide_cache.hipnc"))

    hou.setFrame(40)
    bbox = cache.geometry().boundingBox()
    cache.parm("loadfromdisk").set(False)
    shoot(solver, "guide_cache_1_sim", bbox, 40)
    cache.parm("loadfromdisk").set(True)
    shoot(cache, "guide_cache_2_loaded", bbox, 40)


if __name__ == "__main__":
    main()
