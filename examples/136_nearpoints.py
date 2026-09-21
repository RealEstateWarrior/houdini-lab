# -*- coding: utf-8 -*-
"""実験136 — nearpoints() は、自分を数えるか・半径ちょうどを含むか・どの順に返すか。

間隔1の格子（21×21）の真ん中の点で、nearpoints(0, P, 半径, 最大数) を呼ぶ。
格子なら、半径ごとの答えが数えられる:
  半径 0.5 → 自分だけ（1）
  半径 1.0 → 自分＋上下左右（5）… 半径ちょうどを含むなら
  半径 √2 → さらに斜め4つ（9）
  半径 2.0 → さらに2つ先の上下左右（13）
最大数を小さくしたとき、近い順に切られるか、自分が先頭かも見る。
pcfind() も同じ条件で比べる。

    hython examples/136_nearpoints.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "g")
    grid.parmTuple("size").set((20.0, 20.0))
    grid.parm("rows").set(21)
    grid.parm("cols").set(21)
    center = 220        # 10*21+10
    rows = []
    cases = [(0.5, 100), (0.999, 100), (1.0, 100), (1.001, 100), (math.sqrt(2), 100),
             (math.sqrt(2) + 1e-4, 100), (2.0, 100), (2.0, 3), (2.0, 1)]
    for radius, maxn in cases:
        for fn in ("nearpoints", "pcfind"):
            wr = geo.createNode("attribwrangle", "w")
            wr.setInput(0, grid)
            wr.parm("class").set(0)
            wr.parm("snippet").set(
                f'vector c = point(0, "P", {center});\n'
                f'int found[] = {fn}(0, {"" if fn == "nearpoints" else chr(34) + "P" + chr(34) + ", "}c, {radius!r}, {maxn});\n'
                'i[]@found = found;\n'
                'float d[]; foreach (int p; found) append(d, distance(c, point(0, "P", p)));\n'
                'f[]@dist = d;')
            g = wr.geometry()
            found = list(g.intListAttribValue("found"))
            dist = [round(x, 6) for x in g.floatListAttribValue("dist")]
            rows.append({"fn": fn, "radius": round(radius, 6), "max": maxn, "count": len(found),
                         "self_first": bool(found) and found[0] == center,
                         "sorted": dist == sorted(dist), "dist": dist[:14]})
            print(rows[-1])
            wr.destroy()
    path = os.path.join(sop_bench.OUT, "136_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
