# -*- coding: utf-8 -*-
"""実験093 — ならすと、どれだけ縮むか。

smooth は点を近所の平均へ寄せる。凹凸が消えるのは狙い通りだが、
同時に形そのものが小さくなる（縮む）と言われる。どれだけ縮むかを測る。

体積は measure SOP（Measure を Volume）で測る。閉じた形なら面ごとの値を足せば全体になる。
つまみは Strength（既定 10）。0 から 160 まで振って、体積と元からのずれを取る。

    hython examples/093_smooth_volume.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

STRENGTH = [0.0, 2.5, 5.0, 10.0, 20.0, 40.0, 80.0, 160.0]


def volume_of(parent, node):
    """measure で体積を測る。閉じた形なら面ごとの値を足せば全体になる。"""
    meas = parent.createNode("measure", "vol_tmp")
    meas.setInput(0, node)
    meas.parm("measure").set("volume")
    meas.parm("attribname").set("vol")
    out = meas.geometry()
    total = sum(prim.attribValue("vol") for prim in out.prims())
    meas.destroy()
    return total


def main():
    geo = sop_bench.fresh()
    sphere = geo.createNode("sphere", "src_sphere")
    sphere.parm("type").set("polymesh")
    sphere.parm("rows").set(60)
    sphere.parm("cols").set(60)
    mountain = geo.createNode("mountain", "src_mountain")
    mountain.setInput(0, sphere)
    mountain.parm("height").set(0.2)
    mountain.parm("elementsize").set(0.7)
    mountain.parmTuple("offset").set((5.0, 0.0, 0.0))

    base = mountain.geometry()
    base_vol = volume_of(geo, mountain)
    print(f"元: {base.intrinsicValue('primitivecount')} 面 / 体積 {base_vol:.6f}")

    rows = []
    for strength in STRENGTH:
        node = geo.createNode("smooth", f"sm_{strength}")
        node.setInput(0, mountain)
        node.parm("strength").set(strength)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        vol = volume_of(geo, node)
        gap = sop_bench.spread(out, base)
        row = {
            "strength": strength,
            "volume": round(vol, 6),
            "volume_pct": round(vol / base_vol * 100, 4),
            "seconds": round(elapsed, 4),
            "gap_mean": round(gap["mean"], 6),
            "gap_max": round(gap["max"], 6),
        }
        rows.append(row)
        print(f"  強さ {strength:>6} -> 体積 {vol:.6f}"
              f"（元の {row['volume_pct']:.2f}%） {elapsed:.3f}秒 "
              f"ずれ 平均 {row['gap_mean']:.6f}")

    # ならし方（Method）を変えても縮み方が同じかを見る。強さは最大の160で揃える。
    methods = []
    for index, name in ((0, "uniform"), (1, "scaledominant"), (2, "curvaturedominant")):
        node = geo.createNode("smooth", f"sm_m{index}")
        node.setInput(0, mountain)
        node.parm("strength").set(160.0)
        node.parm("method").set(index)
        start = time.perf_counter()
        out = node.geometry()
        elapsed = time.perf_counter() - start
        vol = volume_of(geo, node)
        gap = sop_bench.spread(out, base)
        row = {
            "method": name,
            "strength": 160.0,
            "volume": round(vol, 6),
            "volume_pct": round(vol / base_vol * 100, 4),
            "seconds": round(elapsed, 4),
            "gap_mean": round(gap["mean"], 6),
            "gap_max": round(gap["max"], 6),
        }
        methods.append(row)
        print(f"  強さ160 / {name:<18} -> 体積 {vol:.6f}"
              f"（元の {row['volume_pct']:.2f}%） ずれ 平均 {row['gap_mean']:.6f}")

    sop_bench.save("093", rows,
                   {"base_volume": round(base_vol, 6), "methods": methods})


if __name__ == "__main__":
    main()
