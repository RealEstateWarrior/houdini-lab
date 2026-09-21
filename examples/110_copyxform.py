# -*- coding: utf-8 -*-
"""実験110 — copyxform は、同じ変形を何回重ねているのか。

copyxform（Copy and Transform）は、1つ置くたびに同じ移動・回転・拡大を
重ねていくはず。i 個目は「1回分の変形を i 回かけたもの」になる。
答えが計算で出る置き方で確かめる。

1. 移動だけ（x に1ずつ）: i 個目の中心の x は 0.5 + i
2. 拡大だけ（0.8倍ずつ）: i 個目の大きさは 0.2×0.8^i、中心の x は 0.5×0.8^i
3. 回転72° と移動: 5回で1周するので、6個目（i=5）が1個目（i=0）と重なるはず。
   5個の中心は正五角形になる（辺の長さが全部同じ）
4. 3 と同じ値で、Transform Order を SRT から TRS に変えると、どこが変わるか

元の形は、x=0.5 に置いた一辺 0.2 の箱（原点からずらして、回転が効くようにする）。

    hython examples/110_copyxform.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def copies(node):
    """箱1つ = 8点。i 個目の中心と大きさ（x方向の幅）を返す。"""
    pts = [p.position() for p in node.geometry().points()]
    out = []
    for i in range(0, len(pts), 8):
        chunk = pts[i:i + 8]
        center = [sum(p[k] for p in chunk) / 8 for k in range(3)]
        width = max(math.dist(a, b) for a in chunk for b in chunk) / math.sqrt(3)
        out.append({"center": [round(v, 6) for v in center], "width": round(width, 6)})
    return out


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "b")
    box.parmTuple("size").set((0.2, 0.2, 0.2))
    box.parmTuple("t").set((0.5, 0.0, 0.0))

    cases = {
        "move": {"ncy": 5, "t": (1, 0, 0)},
        "scale": {"ncy": 5, "scale": 0.8},
        "turn": {"ncy": 6, "t": (2, 0, 0), "r": (0, 72, 0)},
        "turn_trs": {"ncy": 6, "t": (2, 0, 0), "r": (0, 72, 0), "xOrd": "trs"},
    }
    result = {}
    for name, setup in cases.items():
        node = geo.createNode("copyxform", name)
        node.setInput(0, box)
        for key, value in setup.items():
            if isinstance(value, tuple):
                node.parmTuple(key).set(value)
            else:
                node.parm(key).set(value)
        result[name] = {"setup": {k: v for k, v in setup.items()},
                        "prims": node.geometry().intrinsicValue("primitivecount"),
                        "copies": copies(node)}
        print(name, result[name]["prims"], result[name]["copies"])

    path = os.path.join(sop_bench.OUT, "110_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
