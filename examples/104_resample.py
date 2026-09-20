# -*- coding: utf-8 -*-
"""実験104 — 線を刻むと、点はいくつになるのか。

resample の Maximum Segment Length に s を入れると、長さ L の線は
何個の点になるのか。切り上げなら ceil(L/s)+1、四捨五入なら round(L/s)+1。
どちらなのかを、割り切れない値で確かめる。

あわせて carve も測る。0〜1 の範囲を指定して線の一部を取り出す箱なので、
0.25〜0.75 を取れば長さは元の半分になるはず。

つまずいた点: carve の First U / Second U というつまみは「使うかどうか」の入切で、
値は domainu1 / domainu2 という別のつまみに入っている。既定では First U だけが入で
domainu1 が 0.25 なので、何も触らないと 0.25〜1.0 が取り出される（長さ 5.25）。

長さは measure（Measure = Perimeter）を面ごとに足して出す。

    hython examples/104_resample.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

LENGTH = 7.0
SEGS = [1.0, 0.7, 0.5, 0.3, 0.25, 0.2, 1.5, 2.0, 3.0]
CARVES = [(0.0, 1.0), (0.0, 0.5), (0.25, 0.75), (0.1, 0.9), (0.5, 0.5)]


def length_of(parent, node, tag):
    meas = parent.createNode("measure", f"len_{tag}")
    meas.setInput(0, node)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    total = sum(prim.attribValue("len") for prim in meas.geometry().prims())
    meas.destroy()
    return total


def main():
    geo = sop_bench.fresh()
    line = geo.createNode("line", "the_line")
    line.parmTuple("origin").set((0.0, 0.0, 0.0))
    line.parmTuple("dir").set((1.0, 0.0, 0.0))
    line.parm("dist").set(LENGTH)
    line.parm("points").set(2)
    base_len = length_of(geo, line, "base")
    print(f"元の線: 長さ {base_len:.6f}（指定 {LENGTH}）/ "
          f"{line.geometry().intrinsicValue('pointcount')}点")

    rows = []
    for seg in SEGS:
        node = geo.createNode("resample", f"rs_{seg}")
        node.setInput(0, line)
        node.parm("dolength").set(True)
        node.parm("length").set(seg)
        out = node.geometry()
        points = out.intrinsicValue("pointcount")
        got_len = length_of(geo, node, f"r{seg}")
        ceil_pts = math.ceil(LENGTH / seg) + 1
        round_pts = round(LENGTH / seg) + 1
        rows.append({
            "seg": seg,
            "ratio": round(LENGTH / seg, 4),
            "points": points,
            "ceil_points": ceil_pts,
            "round_points": round_pts,
            "matches_ceil": points == ceil_pts,
            "matches_round": points == round_pts,
            "actual_seg": round(got_len / (points - 1), 6) if points > 1 else None,
            "length": round(got_len, 6),
        })
        print(f"  刻み {seg:<5} (L/s = {LENGTH / seg:.4f}) -> {points:>3}点 "
              f"切り上げ {ceil_pts} / 四捨五入 {round_pts} "
              f"| 実際の刻み {rows[-1]['actual_seg']} 長さ {got_len:.6f}")

    carve_rows = []
    for first, second in CARVES:
        node = geo.createNode("carve", f"cv_{first}_{second}")
        node.setInput(0, line)
        # firstu / secondu は「使うかどうか」の入切。値は domainu1 / domainu2。
        # 既定では firstu だけが入で domainu1 が 0.25 なので、そのままだと
        # 0.25〜1.0 が取り出される（長さ 5.25）。両方を入にして値を入れる。
        node.parm("firstu").set(True)
        node.parm("secondu").set(True)
        node.parm("domainu1").set(first)
        node.parm("domainu2").set(second)
        out = node.geometry()
        got_len = length_of(geo, node, f"c{first}_{second}")
        want = LENGTH * (second - first)
        carve_rows.append({
            "first": first, "second": second,
            "points": out.intrinsicValue("pointcount"),
            "prims": out.intrinsicValue("primitivecount"),
            "length": round(got_len, 6),
            "want": round(want, 6),
            "diff": round(got_len - want, 6),
        })
        print(f"  carve {first}〜{second} -> 長さ {got_len:.6f} / "
              f"式 {want:.6f}（差 {got_len - want:+.6f}）"
              f" {out.intrinsicValue('pointcount')}点")

    sop_bench.save("104", rows,
                   {"length": LENGTH, "base_length": round(base_len, 6),
                    "carve_rows": carve_rows})


if __name__ == "__main__":
    main()
