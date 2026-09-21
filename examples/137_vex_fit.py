# -*- coding: utf-8 -*-
"""実験137 — VEX の fit・efit・lerp・smooth は、範囲の外でどうなるか。

x を −0.5〜1.5 まで 0.05 刻みで振り、次の関数の値を取る。
  fit(x, 0, 1, 0, 10)   efit(x, 0, 1, 0, 10)   fit01(x, 0, 10)
  lerp(0, 10, x)        smooth(0, 1, x)        clamp(x, 0, 1)
範囲の外で止まる（クランプする）か、そのまま伸びるかを数える。
smooth は 3x² − 2x³（スムーズステップ）と比べる。

    hython examples/137_vex_fit.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

FUNCS = ["fit(x, 0, 1, 0, 10)", "efit(x, 0, 1, 0, 10)", "fit01(x, 0, 10)",
         "lerp(0.0, 10.0, x)", "smooth(0.0, 1.0, x)", "clamp(x, 0.0, 1.0)"]


def main():
    geo = sop_bench.fresh()
    wr = geo.createNode("attribwrangle", "w")
    wr.parm("class").set(0)
    body = ["for (int i = 0; i <= 40; i++) {", "  float x = -0.5 + i * 0.05;",
            "  int p = addpoint(0, set(x, 0, 0));"]
    for k, f in enumerate(FUNCS):
        body.append(f'  setpointattrib(0, "f{k}", p, {f});')
    body.append("}")
    wr.parm("snippet").set("\n".join(body))
    g = wr.geometry()
    xs = [round(v, 4) for v in g.pointFloatAttribValues("P")[0::3]]
    out = {"x": xs}
    for k, f in enumerate(FUNCS):
        out[f] = [round(v, 6) for v in g.pointFloatAttribValues(f"f{k}")]
    path = os.path.join(sop_bench.OUT, "137_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    for f in FUNCS:
        print(f, out[f][0], out[f][10], out[f][20], out[f][30], out[f][40])
    print("書いた:", path)


if __name__ == "__main__":
    main()
