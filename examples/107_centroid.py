# -*- coding: utf-8 -*-
"""実験107 — extractcentroid の「中心」は、どの中心か。

中心には何通りもある。点の平均、囲む箱の中心、面積で重みを付けた中心、
体積で重みを付けた中心。形によっては、これらが全部ちがう値になる。
答えが計算で出る形を2つ用意して、Method ごとに出てくる値と突き合わせる。

A. L字の板（1枚の面、6頂点）: 2×2 の正方形から 1×1 の角を欠いたもの
   点の平均 (1, 1)、箱の中心 (1, 1)、面積の中心 (5/6, 5/6)
B. 四角錐（底 2×2、高さ3、閉じた面5枚）
   点の平均 y=0.6、箱の中心 y=1.5、体積の中心 y=0.75、表面積の中心 y≒0.7598

    hython examples/107_centroid.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

L_SHAPE = """
int p[];
vector pts[] = {{0,0,0},{2,0,0},{2,0,1},{1,0,1},{1,0,2},{0,0,2}};
foreach (vector q; pts) append(p, addpoint(0, q));
addprim(0, "poly", p);
"""

PYRAMID = """
int b0 = addpoint(0, {-1,0,-1});
int b1 = addpoint(0, { 1,0,-1});
int b2 = addpoint(0, { 1,0, 1});
int b3 = addpoint(0, {-1,0, 1});
int ap = addpoint(0, { 0,3, 0});
addprim(0, "poly", b0, b1, b2, b3);
addprim(0, "poly", b1, b0, ap);
addprim(0, "poly", b2, b1, ap);
addprim(0, "poly", b3, b2, ap);
addprim(0, "poly", b0, b3, ap);
"""


L_PRISM = """
vector pts[] = {{0,0,0},{2,0,0},{2,0,1},{1,0,1},{1,0,2},{0,0,2}};
int lo[], hi[];
foreach (vector q; pts) { append(lo, addpoint(0, q)); append(hi, addpoint(0, q + {0,1,0})); }
int n = len(pts);
int bottom[]; for (int i = n - 1; i >= 0; i--) append(bottom, lo[i]);
addprim(0, "poly", bottom);
addprim(0, "poly", hi);
for (int i = 0; i < n; i++) {
    int j = (i + 1) % n;
    addprim(0, "poly", lo[i], lo[j], hi[j], hi[i]);
}
"""

OPEN_PYRAMID = PYRAMID.replace('addprim(0, "poly", b0, b1, b2, b3);', '')


def slant_area_centroid():
    """四角錐の表面積の中心の y を式で出す。"""
    slant = math.sqrt(1 + 9)
    tri = 0.5 * 2 * slant
    return (4 * 0 + 4 * tri * 1.0) / (4 + 4 * tri)


SHAPES = {
    "L": (L_SHAPE, {"point_avg": (1.0, 0.0, 1.0), "bbox": (1.0, 0.0, 1.0),
                    "area": (5 / 6, 0.0, 5 / 6)}),
    "pyramid": (PYRAMID, {"point_avg": (0.0, 0.6, 0.0), "bbox": (0.0, 1.5, 0.0),
                          "volume": (0.0, 0.75, 0.0),
                          "area": (0.0, slant_area_centroid(), 0.0)}),
    # 底を抜いた四角錐。閉じていないと体積が無いので、面積の中心になるはず（側面だけなら y=1）
    "open_pyramid": (OPEN_PYRAMID, {"point_avg": (0.0, 0.6, 0.0), "bbox": (0.0, 1.5, 0.0),
                                    "area": (0.0, 1.0, 0.0), "hull_volume": (0.0, 0.75, 0.0)}),
    # L字を高さ1で立てた柱。凸包（五角柱）の中心と、本当の体積の中心がずれる
    "L_prism": (L_PRISM, {"point_avg": (1.0, 0.5, 1.0), "bbox": (1.0, 0.5, 1.0),
                          "volume": (5 / 6, 0.5, 5 / 6),
                          "hull_volume": (19 / 21, 0.5, 19 / 21)}),
}


def main():
    rows = []
    for shape, (code, answers) in SHAPES.items():
        geo = sop_bench.fresh()
        make = geo.createNode("attribwrangle", "make")
        make.parm("class").set(0)                 # 0 = Detail（1回だけ走らせる）
        make.parm("snippet").set(code)
        for method in ("com", "bbox", "convexhull"):
            for cls in ("prim", "point"):
                node = geo.createNode("extractcentroid", f"c_{method}_{cls}")
                node.setInput(0, make)
                node.parm("partitiontype").set("detail")
                node.parm("method").set(method)
                node.parm("class").set(cls)
                node.parm("output").set("points")
                out = node.geometry()
                pts = out.points()
                got = tuple(round(v, 6) for v in pts[0].position()) if pts else None
                match = [k for k, want in answers.items()
                         if got and all(abs(a - b) < 1e-5 for a, b in zip(got, want))]
                rows.append({"shape": shape, "method": method, "class": cls,
                             "got": got, "points_out": len(pts), "match": match})
                print(rows[-1])
    answers = {s: {k: [round(v, 6) for v in w] for k, w in a.items()}
               for s, (_, a) in SHAPES.items()}
    path = os.path.join(sop_bench.OUT, "107_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "answers": answers}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
