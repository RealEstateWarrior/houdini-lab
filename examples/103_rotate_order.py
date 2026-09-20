# -*- coding: utf-8 -*-
"""実験103 — 回転の順番を変えると、どこへ行くのか。

Transform には Rotate Order（xyz / xzy / yxz / yzx / zxy / zyx）がある。
同じ角度を入れても、掛ける順番で行き先が変わる。どれだけ変わるのかと、
Houdini の「xyz」が数式でいう何の順番なのかを確かめる。

やり方は、点を1つ（1, 0, 0）置いて、角度 (30°, 40°, 50°) で回す。
6通りすべての行き先を測り、それぞれを自分で行列を掛けて出した答えと
突き合わせる。**どの掛け順が合うかで、Houdini の並びの意味が決まる。**

    hython examples/103_rotate_order.py
"""
import itertools
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

ANGLES = (30.0, 40.0, 50.0)          # x, y, z の回転角
ORDERS = ["xyz", "xzy", "yxz", "yzx", "zxy", "zyx"]
START = (1.0, 0.0, 0.0)


def rot(axis, deg):
    """1軸まわりの回転行列（右手系・反時計回り）を3×3の入れ子で返す。"""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if axis == "y":
        return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def apply(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def by_order(order, angles, reverse):
    """order の並びどおりに回転を掛ける。reverse なら右から左へ。"""
    axes = list(order)
    if reverse:
        axes = axes[::-1]
    m = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for axis in axes:
        m = mul(rot(axis, angles["xyz".index(axis)]), m)
    return apply(m, START)


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main():
    geo = sop_bench.fresh()
    add = geo.createNode("add", "one_point")
    add.parm("points").set(1)
    add.parmTuple("pt0").set(START)

    rows = []
    got = {}
    for index, order in enumerate(ORDERS):
        node = geo.createNode("xform", f"r_{order}")
        node.setInput(0, add)
        node.parm("rOrd").set(index)
        node.parmTuple("r").set(ANGLES)
        point = node.geometry().points()[0].position()
        place = (point[0], point[1], point[2])
        got[order] = place

        # 2通りの掛け順で自分で計算し、どちらに合うか見る
        forward = by_order(order, ANGLES, reverse=False)
        backward = by_order(order, ANGLES, reverse=True)
        rows.append({
            "order": order,
            "x": round(place[0], 6),
            "y": round(place[1], 6),
            "z": round(place[2], 6),
            "diff_forward": round(dist(place, forward), 6),
            "diff_backward": round(dist(place, backward), 6),
        })
        print(f"  {order} -> ({place[0]:+.6f}, {place[1]:+.6f}, {place[2]:+.6f})"
              f"  左から掛けた式との差 {rows[-1]['diff_forward']:.6f}"
              f" / 右から {rows[-1]['diff_backward']:.6f}")

    # 6通りのあいだの距離。どれだけばらつくか
    pairs = []
    for a, b in itertools.combinations(ORDERS, 2):
        pairs.append({"a": a, "b": b, "dist": round(dist(got[a], got[b]), 6)})
    pairs.sort(key=lambda row: -row["dist"])
    print(f"  もっとも離れた2つ: {pairs[0]['a']} と {pairs[0]['b']} で "
          f"{pairs[0]['dist']:.6f}（点は原点から 1.0 の距離にある）")
    print(f"  もっとも近い2つ:   {pairs[-1]['a']} と {pairs[-1]['b']} で "
          f"{pairs[-1]['dist']:.6f}")

    # 1軸だけ回すときは、順番に関係なく同じになるはず
    single = []
    for index, order in enumerate(ORDERS):
        node = geo.createNode("xform", f"s_{order}")
        node.setInput(0, add)
        node.parm("rOrd").set(index)
        node.parmTuple("r").set((0.0, 40.0, 0.0))
        point = node.geometry().points()[0].position()
        single.append({"order": order,
                       "x": round(point[0], 6),
                       "y": round(point[1], 6),
                       "z": round(point[2], 6)})
    spread = max(dist((s["x"], s["y"], s["z"]),
                      (single[0]["x"], single[0]["y"], single[0]["z"]))
                 for s in single)
    print(f"  y だけ 40° 回したとき、6通りの差は最大 {spread:.9f}")

    sop_bench.save("103", rows,
                   {"angles": list(ANGLES), "start": list(START),
                    "pairs": pairs, "single": single,
                    "single_spread": round(spread, 9)})


if __name__ == "__main__":
    main()
