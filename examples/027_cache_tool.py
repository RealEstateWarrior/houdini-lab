"""実験027 — キャッシュを道具に組み込む。古いファイルを読んでしまう事故は防げるか。

実験025で <code>filecache</code> の挙動は測った。読み込みは4.6倍速く、値は完全に一致する。
ただし手で組むと毎回同じ手間がかかるうえ、<strong>もっと危ない落とし穴がある</strong>。

  <strong>上流を変えたのに、古いキャッシュを読んでしまう。</strong>

このとき画も数字も出てくる。エラーも出ない。ただ、それは前の設定の結果である。
測った値が静かに嘘になる。このプロジェクトで一番避けたい事故がこれ。

そこで <code>hou_tools.cache_sim()</code> に、上流のノードの種類と
「既定から動かしたパラメータ」をまとめた指紋（SHA-1）を持たせ、
キャッシュの隣に置いた。一致したときだけ読み、変わっていれば黙って計算し直す。

否定できる形にする。次の3つを、すべて数字で確かめる。

  1. キャッシュを通しても値は変わらないか（全フレームで差が 0 か）
  2. 2回目は本当に読むだけになるか（書き出しが起きないか）
  3. <strong>上流を1つ変えたとき、指紋が変わって計算し直すか</strong>
     変わらなければ、この仕組みは無意味である

    hython examples/027_cache_tool.py
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
CACHE_DIR = os.path.join(OUT, "027_cache")

import hou_tools  # noqa: E402

FRAMES = list(range(1, 31))
CHECK = [1, 10, 20, 30]
VOXEL = 0.06
SHOT_RES = (420, 560)


def build(dissipation=None):
    """煙をひとつ。dissipation は「上流を変える」ための取っ手。

    pyrosolver の dissipation は既定で有効・値は 0.1。
    つまり何も触らなくても煙は薄くなり続けている。None なら既定のまま。
    """
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(FRAMES[0], FRAMES[-1])
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
    if dissipation is not None:
        solver.parm("dissipation").set(dissipation)
    return geo, solver


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

    stats = {"frames": len(FRAMES)}

    print("1. キャッシュなしで30フレーム回す（答え合わせの基準）")
    geo, solver = build()
    stats["dissipation_default"] = solver.parm("dissipation").eval()
    stats["dissipation_enabled_default"] = bool(
        solver.parm("enable_dissipation").eval())
    print(f"   solver の dissipation の既定: "
          f"{stats['dissipation_default']}"
          f"（有効: {'はい' if stats['dissipation_enabled_default'] else 'いいえ'}）")
    raw_sec, raw_values = sweep(solver, FRAMES)
    print(f"   {raw_sec:.2f}秒")
    stats["raw_sec"] = raw_sec

    print("\n2. cache_sim() を通す（1回目・まだファイルがない）")
    cache, first = hou_tools.cache_sim(solver.path(), CACHE_DIR, "smoke", FRAMES)
    cached_sec, cached_values = sweep(cache, FRAMES)
    print(f"   読み出し {cached_sec:.2f}秒"
          f"（計算より {raw_sec / cached_sec:.1f}倍速い）")
    stats["first"] = first
    stats["cached_sec"] = cached_sec
    stats["speedup"] = raw_sec / cached_sec

    print("\n3. 値は変わっていないか")
    print(f"{'フレーム':>8} {'計算した値':>16} {'読んだ値':>16} {'差':>14}")
    worst = 0.0
    for frame in CHECK:
        i = FRAMES.index(frame)
        a, b = raw_values[i], cached_values[i]
        diff = abs(a - b)
        worst = max(worst, diff)
        print(f"{frame:8d} {a:16.6f} {b:16.6f} {diff:14.10f}")
    identical = all(a == b for a, b in zip(raw_values, cached_values))
    print(f"\n   {len(FRAMES)}フレーム全部で完全に一致: "
          f"{'はい' if identical else 'いいえ'}")
    stats["identical"] = identical
    stats["worst_diff"] = worst
    stats["check"] = [{"frame": f, "raw": raw_values[FRAMES.index(f)],
                       "cached": cached_values[FRAMES.index(f)]} for f in CHECK]

    print("\n4. 同じ設定でもう一度 cache_sim()（2回目・読むだけになるか）")
    geo, solver = build()
    cache2, second = hou_tools.cache_sim(solver.path(), CACHE_DIR, "smoke", FRAMES)
    again_sec, again_values = sweep(cache2, FRAMES)
    print(f"   書き出した: {'はい' if second['wrote'] else 'いいえ'}"
          f" / 読み出し {again_sec:.2f}秒")
    same_as_first = all(a == b for a, b in zip(cached_values, again_values))
    print(f"   1回目と完全に一致: {'はい' if same_as_first else 'いいえ'}")
    stats["second"] = second
    stats["second_sec"] = again_sec
    stats["second_identical"] = same_as_first

    print("\n5. 上流を1つ変える（dissipation 0.1 → 0.05。既定の半分にする）")
    geo, solver = build(dissipation=0.05)
    cache3, third = hou_tools.cache_sim(solver.path(), CACHE_DIR, "smoke", FRAMES)
    _, changed_values = sweep(cache3, FRAMES)
    print(f"   書き出した: {'はい' if third['wrote'] else 'いいえ'}"
          f" / 理由: {third['reason']}")
    print(f"   指紋 1回目 {first['digest'][:12]} → 変更後 {third['digest'][:12]}")
    moved = sum(1 for a, b in zip(cached_values, changed_values) if a != b)
    print(f"   値が変わったフレーム: {moved} / {len(FRAMES)}")
    f30 = changed_values[FRAMES.index(30)]
    base30 = cached_values[FRAMES.index(30)]
    print(f"   F30 の密度の合計: {base30:.2f} → {f30:.2f}"
          f"（{(f30 - base30) / base30 * 100:+.1f}%）")
    stats["third"] = third
    stats["digest_changed"] = first["digest"] != third["digest"]
    stats["moved_frames"] = moved
    stats["f30_base"] = base30
    stats["f30_changed"] = f30
    stats["dissipation_changed"] = 0.05

    print("\n6. 指紋のファイルを壊したらどうなるか")
    stamp = os.path.join(CACHE_DIR, "smoke.fingerprint.json")
    with open(stamp, "w", encoding="utf-8") as fp:
        fp.write("{ not json")
    geo, solver = build(dissipation=0.05)
    _, fourth = hou_tools.cache_sim(solver.path(), CACHE_DIR, "smoke", FRAMES)
    print(f"   書き出した: {'はい' if fourth['wrote'] else 'いいえ'}"
          f" / 理由: {fourth['reason']}")
    stats["fourth"] = fourth

    with open(os.path.join(OUT, "027_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "027_graph.json"),
                          title="実験027 — キャッシュを道具に組み込む")
    hou_tools.save_hip(os.path.join(OUT, "027_cache_tool.hipnc"))
    print("\n保存: out/027_stats.json, out/027_graph.json, out/027_cache_tool.hipnc")


BBOX_PATH = os.path.join(OUT, "027_bbox.json")


def shot(which):
    """F30 を1枚撮る。

    シーンを作り直してからレンダすると hython が固まるので、
    1プロセスにつき1枚だけ撮る。カメラをそろえるため、
    最初に撮ったときの枠を JSON に残して次のプロセスが読む。
    """
    dissipation = 0.05 if which == "halved" else None
    geo, solver = build(dissipation=dissipation)
    hou.setFrame(30)

    if os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = hou_tools.bbox_over_frames(solver.path(), [30])
        with open(BBOX_PATH, "w", encoding="utf-8") as fp:
            json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    name = "027_halved.png" if which == "halved" else "027_default.png"
    hou_tools.render_preview(solver.path(), os.path.join(OUT, name),
                             res=SHOT_RES, shading="smooth", frame_bbox=bbox,
                             margin=1.06)
    print(f"保存: out/{name}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        shot(sys.argv[1])
    else:
        main()
