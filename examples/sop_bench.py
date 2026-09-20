# -*- coding: utf-8 -*-
"""SOP のつまみを振って測るための土台。

実験のたびに「組む・振る・測る・保存する」を書き直すのをやめる。
実験ごとに書くのは、組み方と測り方だけにする。

    import sop_bench
    rows = sop_bench.sweep(build, [0.5, 0.25, 0.1], measure=sop_bench.basic)
    sop_bench.save("091", rows)

build(value) は「測りたいノード」を返す。毎回シーンを捨てて組み直すので、
前の計算の結果が使い回されることはない（cook(force=True) は当てにならない）。
"""
import json
import os
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")


def fresh():
    """シーンを空にする。組み直しは毎回ここから。"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    return hou.node("/obj").createNode("geo", "bench")


def basic(geo):
    """点の数・面の数・囲む箱の大きさを返す。点の数は intrinsic で取る。

    len(geo.points()) は点が多いと非常に遅い（実験082で 22.1M点に 8.8秒）。
    """
    box = geo.boundingBox()
    return {
        "points": geo.intrinsicValue("pointcount"),
        "prims": geo.intrinsicValue("primitivecount"),
        "size": [round(v, 6) for v in box.sizevec()],
    }


def volume(geo):
    """囲む箱ではなく、実際の体積を測る（measure SOP を通す）。"""
    import hou
    parent = geo.sopNode().parent()
    node = parent.createNode("measure", "bench_volume")
    node.setInput(0, geo.sopNode())
    node.parm("measure").set("volume")
    node.parm("attribname").set("vol")
    total = 0.0
    out = node.geometry()
    for prim in out.prims():
        total += prim.attribValue("vol")
    node.destroy()
    return total


def spread(geo, other):
    """geo の各点から other の面までの最短距離を集めて、平均と最大を返す。

    形がどれだけずれたかを1つの数にする。xyzdist を VEX で回すのが速い。
    """
    import hou
    parent = geo.sopNode().parent()
    node = parent.createNode("attribwrangle", "bench_spread")
    node.setInput(0, geo.sopNode())
    node.setInput(1, other.sopNode())
    node.parm("class").set(2)          # 2 = Points（既定値も2。0 は Detail なので注意）
    node.parm("snippet").set('f@gap = xyzdist(1, @P);')
    out = node.geometry()
    values = out.pointFloatAttribValues("gap")
    node.destroy()
    if not values:
        return {"mean": None, "max": None}
    return {"mean": sum(values) / len(values), "max": max(values)}


def sweep(build, values, measure=basic, repeat=1):
    """values をひとつずつ build に渡し、掛かった時間と測った値を集める。"""
    rows = []
    for value in values:
        best = None
        for _ in range(repeat):
            node = build(value)
            start = time.perf_counter()
            geo = node.geometry()
            elapsed = time.perf_counter() - start
            if best is None or elapsed < best[0]:
                best = (elapsed, measure(geo), node)
        elapsed, measured, node = best
        row = {"value": value, "seconds": round(elapsed, 4)}
        row.update(measured)
        rows.append(row)
        print("  ", value, "->", row)
    return rows


def save(no, rows, extra=None):
    """out/NNN_stats.json に残す。記事はこのファイルから書く。"""
    payload = {"rows": rows}
    if extra:
        payload.update(extra)
    path = os.path.join(OUT, f"{no}_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    print("保存:", path)
    return path
