# -*- coding: utf-8 -*-
"""実験125 — 点と面の数は、式で先に分かるか（divide・facet・convertline・edgedivide・polysoup）。

1. divide（既定: 三角形に割る）: n 角形1枚 → 三角形 n−2 枚
2. facet の Unique Points: 点の数 = 頂点の数（面ごとに点を持つ）
3. convertline: 線の本数 = 辺の数。閉じた形なら オイラーの式 V − E + F = 2 から E = V + F − 2
4. edgedivide（Divisions k）: 選んだ辺1本につき、点が k−1 個増える
5. polysoup: 面の数が1つになるか

形は box（8点・6面）、grid 5×5（25点・16面）、sphere polymesh 12×24、circle（n角形1枚）。

    hython examples/125_counts.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def counts(node):
    g = node.geometry()
    return {"points": g.intrinsicValue("pointcount"), "prims": g.intrinsicValue("primitivecount"),
            "vertices": g.intrinsicValue("vertexcount")}


def main():
    geo = sop_bench.fresh()
    rows = []
    # 1. n 角形 → 三角形
    for n in (3, 4, 5, 8, 24, 100):
        c = geo.createNode("circle", f"c{n}")
        c.parm("type").set("poly")
        c.parm("divs").set(n)
        dv = geo.createNode("divide", f"dv{n}")
        dv.setInput(0, c)
        rows.append({"test": "divide", "n": n, "before": counts(c), "after": counts(dv),
                     "want_prims": n - 2})
        print(rows[-1])

    shapes = {}
    b = geo.createNode("box", "box")
    shapes["box"] = b
    gr = geo.createNode("grid", "grid")
    gr.parm("rows").set(5)
    gr.parm("cols").set(5)
    shapes["grid"] = gr
    sp = geo.createNode("sphere", "sphere")
    sp.parm("type").set("polymesh")
    sp.parm("rows").set(12)
    sp.parm("cols").set(24)
    shapes["sphere"] = sp
    for name, node in shapes.items():
        base = counts(node)
        fc = geo.createNode("facet", f"fc_{name}")
        fc.setInput(0, node)
        fc.parm("unique").set(True)
        cl = geo.createNode("convertline", f"cl_{name}")
        cl.setInput(0, node)
        ps = geo.createNode("polysoup", f"ps_{name}")
        ps.setInput(0, node)
        closed = name != "grid"
        rows.append({"test": "facet_unique", "shape": name, "before": base, "after": counts(fc),
                     "want_points": base["vertices"]})
        rows.append({"test": "convertline", "shape": name, "before": base, "after": counts(cl),
                     "want_prims": base["points"] + base["prims"] - 2 if closed else None})
        rows.append({"test": "polysoup", "shape": name, "before": base, "after": counts(ps),
                     "soup_types": sorted({p.type().name() for p in ps.geometry().prims()})})
        for r in rows[-3:]:
            print(r)

    # 4. edgedivide: box の辺を全部 k 分割
    for k in (2, 3, 5):
        ed = geo.createNode("edgedivide", f"ed{k}")
        ed.setInput(0, b)
        ed.parm("group").set("*")
        ed.parm("numdivs").set(k)
        rows.append({"test": "edgedivide", "k": k, "before": counts(b), "after": counts(ed),
                     "want_points": 8 + 24 * (k - 1), "want_shared": 8 + 12 * (k - 1)})
        # Share New Points を入れると、隣の面と新しい点を共有する
        sh = geo.createNode("edgedivide", f"eds{k}")
        sh.setInput(0, b)
        sh.parm("group").set("*")
        sh.parm("numdivs").set(k)
        sh.parm("sharedpoints").set(True)
        rows[-1]["after_shared"] = counts(sh)
        print(rows[-1])

    path = os.path.join(sop_bench.OUT, "125_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
