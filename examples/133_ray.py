# -*- coding: utf-8 -*-
"""実験133 — ray で点を球に落とすと、式の位置に来るか。

半径1の球（polymesh・段数を変える）の上に、1辺 1.6 の格子（31×31点、高さ2）を置く。
1. Method = Project・向き (0, −1, 0): 真下に落とす。当たれば y = √(1 − x² − z²)
2. Method = Minimum Distance: いちばん近い面の点へ動かす。答えは 点 ÷ 長さ（中心から放射状）
どちらも球は多角形なので、多角形の分だけ内側にずれるはず。当たらなかった点の扱いも見る。

    hython examples/133_ray.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


ENTITY = "point"


def main():
    import hou
    geo = sop_bench.fresh()
    probe = geo.createNode("ray", "probe")
    before = [p.expression() if p.keyframes() else None for p in probe.parmTuple("dir")]
    probe.parmTuple("dir").set((0.0, -1.0, 0.0))
    kept = list(probe.parmTuple("dir").eval())
    out = {"dir_expressions": before, "dir_after_plain_set": kept, "point": run()}
    path = os.path.join(sop_bench.OUT, "133_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


def run():
    geo = sop_bench.fresh()
    grid = geo.createNode("grid", "g")
    grid.parmTuple("size").set((1.6, 1.6))
    grid.parm("rows").set(31)
    grid.parm("cols").set(31)
    grid.parmTuple("t").set((0.0, 2.0, 0.0))
    rows = []
    for res in (24, 96):
        sp = geo.createNode("sphere", f"sp{res}")
        sp.parm("type").set("polymesh")
        sp.parm("rows").set(res)
        sp.parm("cols").set(res * 2)
        for method in ("project", "minimum"):
            ray = geo.createNode("ray", f"ray_{method}_{res}")
            ray.setInput(0, grid)
            ray.setInput(1, sp)
            ray.parm("method").set(method)
            ray.parm("entity").set(ENTITY)
            ray.parm("dirmethod").set("vector")
            # Direction には最初から @N.x などの式が入っている。式を消さないと set しても値が変わらない
            for p in ray.parmTuple("dir"):
                p.deleteAllKeyframes()
            ray.parmTuple("dir").set((0.0, -1.0, 0.0))
            t0 = time.perf_counter()
            pos = ray.geometry().pointFloatAttribValues("P")
            sec = time.perf_counter() - t0
            src = grid.geometry().pointFloatAttribValues("P")
            errs, radii, missed = [], [], 0
            for i in range(len(pos) // 3):
                x0, z0 = src[3 * i], src[3 * i + 2]
                x, y, z = pos[3 * i:3 * i + 3]
                if method == "project":
                    if x0 * x0 + z0 * z0 >= 1.0:
                        missed += abs(y - 2.0) < 1e-9
                        continue
                    errs.append(y - math.sqrt(1 - x0 * x0 - z0 * z0))
                    errs[-1] = abs(errs[-1])
                    radii.append(math.sqrt(x * x + y * y + z * z))
                else:
                    L = math.sqrt(x0 * x0 + 4.0 + z0 * z0)
                    want = (x0 / L, 2.0 / L, z0 / L)
                    errs.append(math.dist((x, y, z), want))
                    radii.append(math.sqrt(x * x + y * y + z * z))
            rows.append({"res": res, "method": method, "hits": len(errs), "missed_stayed": missed,
                         "err_max": round(max(errs), 6), "err_mean": round(sum(errs) / len(errs), 6),
                         "r_min": round(min(radii), 6), "r_max": round(max(radii), 6),
                         "sec": round(sec, 4)})
            print(ENTITY, rows[-1])
    return rows


if __name__ == "__main__":
    main()
