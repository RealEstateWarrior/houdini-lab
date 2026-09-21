# -*- coding: utf-8 -*-
"""実験126 — cluster（k-means）は、はっきり分かれた点の塊を正しく分けるか。

中心の分かっている4つの塊（各2,000点、ばらつき 0.1〜0.3）を作り、
cluster に「4つに分けて」と頼む。各塊の点が同じ番号にまとまるか（純度）と、
番号ごとの点の平均が、元の中心にどれだけ近いかを測る。
塊どうしを近づけたとき、純度がどう落ちるかも見る。

    hython examples/126_cluster.py
"""
import json
import math
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

PER = 2000


def blobs(geo, name, spread, sd):
    centers = [(-spread, 0, -spread), (spread, 0, -spread), (-spread, 0, spread), (spread, 0, spread)]
    code = ["vector cs[] = {" + ",".join("{%g,%g,%g}" % c for c in centers) + "};"]
    code.append(f"float sd = {sd};")
    code.append(f"for (int b = 0; b < 4; b++) for (int i = 0; i < {PER}; i++) {{")
    code.append("  vector u = rand(set(b, i, 0.5)); vector w = rand(set(b, i, 7.25));")
    code.append("  float r1 = sqrt(-2 * log(max(u.x, 1e-9))), r2 = sqrt(-2 * log(max(u.y, 1e-9)));")
    code.append("  vector g = set(r1 * cos(2 * PI * w.x), 0, r2 * cos(2 * PI * w.y));")
    code.append("  int p = addpoint(0, cs[b] + g * sd);")
    code.append("  setpointattrib(0, 'truth', p, b);")
    code.append("}")
    wr = geo.createNode("attribwrangle", name)
    wr.parm("class").set(0)
    wr.parm("snippet").set("\n".join(code).replace("'", '"'))
    return wr, centers


def main():
    geo = sop_bench.fresh()
    rows = []
    for spread, sd in ((2.0, 0.2), (1.0, 0.3), (0.5, 0.3), (0.3, 0.3)):
        src, centers = blobs(geo, f"b_{spread}".replace(".", "_"), spread, sd)
        cl = geo.createNode("cluster", f"cl_{spread}".replace(".", "_"))
        cl.setInput(0, src)
        cl.parm("num_clusters").set(4)
        t0 = time.perf_counter()
        out = cl.geometry()
        sec = time.perf_counter() - t0
        attr = cl.parm("cluster_attrib").evalAsString()
        labels = out.pointIntAttribValues(attr) if out.findPointAttrib(attr).dataType().name() == "Int" \
            else [int(v) for v in out.pointFloatAttribValues(attr)]
        truth = out.pointIntAttribValues("truth")
        pos = out.pointFloatAttribValues("P")
        # 純度: 元の塊ごとに、いちばん多い番号の割合
        purity = []
        for b in range(4):
            c = Counter(l for l, t in zip(labels, truth) if t == b)
            purity.append(c.most_common(1)[0][1] / PER)
        # 番号ごとの平均と、いちばん近い元の中心との距離
        errs = []
        for lab in sorted(set(labels)):
            idx = [i for i, l in enumerate(labels) if l == lab]
            m = (sum(pos[3 * i] for i in idx) / len(idx), sum(pos[3 * i + 2] for i in idx) / len(idx))
            errs.append(min(math.hypot(m[0] - c[0], m[1] - c[2]) for c in centers))
        rows.append({"spread": spread, "sd": sd, "gap_over_sd": round(2 * spread / sd, 2),
                     "clusters": len(set(labels)), "purity": [round(p, 4) for p in purity],
                     "center_err_max": round(max(errs), 5), "attr": attr, "sec": round(sec, 4)})
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "126_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"per": PER, "rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
