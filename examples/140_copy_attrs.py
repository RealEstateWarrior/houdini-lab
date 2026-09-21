# -*- coding: utf-8 -*-
"""実験140 — copytopoints は、点のどの属性をどう使って向きと大きさを決めるのか。

元の形は、+z 方向に伸びた目印の「矢」（原点 → (0, 0, 1) の点と、(0, 1, 0) の点を持つ3点の形）。
点1つに属性を付けてコピーし、矢の先がどこを向いたかを見る。
  1. N = (1, 0, 0) だけ          → +z が N の向きになるか
  2. N と up = (0, 0, 1)          → 横倒しの向き（+y）が up に合うか
  3. orient（y 軸まわり 90°）と N  → どちらが勝つか
  4. pscale = 2                   → 2倍になるか
  5. scale = (1, 2, 3) と pscale 2 → 掛け合わさるか
  6. 何も付けない                  → そのまま

    hython examples/140_copy_attrs.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

CASES = {
    "none": "",
    "N": "v@N = {1, 0, 0};",
    "N_up": "v@N = {1, 0, 0}; v@up = {0, 0, 1};",
    # orient は x 軸まわり 90°（+z を −y へ）。N（+x）とは違う向きにして、どちらが勝つかを見る
    "orient_and_N": "v@N = {1, 0, 0}; p@orient = quaternion(radians(90), {1, 0, 0});",
    "orient_only": "p@orient = quaternion(radians(90), {1, 0, 0});",
    "pscale": "f@pscale = 2;",
    "scale_pscale": "f@pscale = 2; v@scale = {1, 2, 3};",
}


def main():
    geo = sop_bench.fresh()
    arrow = geo.createNode("attribwrangle", "arrow")
    arrow.parm("class").set(0)
    arrow.parm("snippet").set(
        "int a = addpoint(0, {0,0,0}); int b = addpoint(0, {0,0,1}); int c = addpoint(0, {0,1,0});\n"
        'addprim(0, "poly", a, b, c);')
    rows = []
    for name, code in CASES.items():
        pt = geo.createNode("attribwrangle", "pt_" + name)
        pt.parm("class").set(0)
        pt.parm("snippet").set("int p = addpoint(0, {5, 0, 0});")
        # 属性は点に付けたいので、detail で点を作ってから点ごとに書く
        per = geo.createNode("attribwrangle", "per_" + name)
        per.setInput(0, pt)
        per.parm("snippet").set(code)
        cp = geo.createNode("copytopoints::2.0", "cp_" + name)
        cp.setInput(0, arrow)
        cp.setInput(1, per)
        g = cp.geometry()
        P = [tuple(round(v, 6) for v in p.position()) for p in g.points()]
        o = P[0]
        tip = tuple(round(b - a, 6) for a, b in zip(o, P[1]))
        side = tuple(round(b - a, 6) for a, b in zip(o, P[2]))
        rows.append({"case": name, "origin": o, "z_axis_to": tip, "y_axis_to": side,
                     "z_len": round(math.sqrt(sum(v * v for v in tip)), 6),
                     "y_len": round(math.sqrt(sum(v * v for v in side)), 6)})
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "140_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
