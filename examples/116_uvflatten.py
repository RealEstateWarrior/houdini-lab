# -*- coding: utf-8 -*-
"""実験116 — uvflatten は、ゆがまずに開ける形をゆがまずに開くか。

円筒の側面は、切り開けばゆがみなく長方形になる（展開できる形）。
半球はどう開いてもゆがむ（ガウス曲率がある）。
どちらも辺ごとに「UV の長さ ÷ 3D の長さ」を出し、そのばらつき（標準偏差÷平均）で
ゆがみを測る。ゆがみが無ければ、比はどの辺でも同じ（ばらつき0）になるはず。
円筒は板を丸めて作るので、最初から1本の切れ目がある。

円筒: 半径1・高さ2 → 開いた長方形の縦横比は 2π·(k角形の補正) : 2

    hython examples/116_uvflatten.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

COLS, ROWS = 49, 17        # 板の点の数（横・縦）


def edge_ratios(geo):
    """面の辺ごとに UV の長さ ÷ 3D の長さ。uv は頂点の属性。"""
    ratios = []
    for prim in geo.prims():
        vs = prim.vertices()
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            d3 = (a.point().position() - b.point().position()).length()
            ua, ub = a.attribValue("uv"), b.attribValue("uv")
            duv = math.hypot(ua[0] - ub[0], ua[1] - ub[1])
            if d3 > 1e-9:
                ratios.append(duv / d3)
    mean = sum(ratios) / len(ratios)
    sd = math.sqrt(sum((r - mean) ** 2 for r in ratios) / len(ratios))
    return mean, sd / mean


def uv_box(geo):
    us = [v.attribValue("uv") for p in geo.prims() for v in p.vertices()]
    return (max(u[0] for u in us) - min(u[0] for u in us),
            max(u[1] for u in us) - min(u[1] for u in us))


def main():
    geo = sop_bench.fresh()
    plate = geo.createNode("grid", "plate")
    plate.parmTuple("size").set((1.0, 1.0))
    plate.parm("rows").set(ROWS)
    plate.parm("cols").set(COLS)
    shapes = {
        # 板を丸めて円筒に（x → 角度、z → 高さ）。両端の点はくっつけない
        "cylinder": 'float a = (@P.x + 0.5) * 2 * PI; float h = (@P.z + 0.5) * 2;\n'
                    '@P = set(cos(a), h, sin(a));',
        # 板を半球に（x → 経度、z → 緯度 0〜90°）。てっぺんは1点に集まらないよう少し残す
        "hemisphere": 'float a = (@P.x + 0.5) * 2 * PI; float t = (@P.z + 0.5) * 0.49 * PI;\n'
                      '@P = set(cos(a) * cos(t), sin(t), sin(a) * cos(t));',
    }
    rows = []
    for name, code in shapes.items():
        wr = geo.createNode("attribwrangle", "make_" + name)
        wr.setInput(0, plate)
        wr.parm("snippet").set(code)
        for method in ("scp", "abf"):
            fl = geo.createNode("uvflatten::3.0", f"{name}_{method}")
            fl.setInput(0, wr)
            fl.parm("method").set(method)
            t0 = time.perf_counter()
            out = fl.geometry()
            sec = time.perf_counter() - t0
            mean, spread = edge_ratios(out)
            w, h = uv_box(out)
            segs = []
            for prim in out.prims():
                uvs = [v.attribValue("uv") for v in prim.vertices()]
                segs.append([[round(u[0], 4), round(u[1], 4)] for u in uvs])
            with open(os.path.join(sop_bench.OUT, f"116_uv_{name}_{method}.json"), "w") as fp:
                json.dump(segs, fp)
            rows.append({"shape": name, "method": method, "ratio_mean": round(mean, 6),
                         "spread": round(spread, 6), "uv_w": round(w, 6), "uv_h": round(h, 6),
                         "aspect": round(w / h, 6), "sec": round(sec, 4)})
            print(rows[-1])
    k = COLS - 1
    want_aspect = k * 2 * math.sin(math.pi / k) / 2.0     # k角形の周 ÷ 高さ
    path = os.path.join(sop_bench.OUT, "116_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows, "want_aspect": round(want_aspect, 6), "cols": COLS,
                   "rows_n": ROWS}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path, "式の縦横比", want_aspect)


if __name__ == "__main__":
    main()
