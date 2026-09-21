# -*- coding: utf-8 -*-
"""実験128 — extracttransform は、かけた変形をそのまま取り出せるか。

形（ばらばらの点を持つ塊）に、分かっている移動・回転・拡大をかけ、
元の形と変形後の形を extracttransform に渡す。取り出した変形を元の形にかけ直して、
変形後の形とどれだけずれるかを測る（ずれが0なら、正しく取り出せている）。
一様でない拡大（x だけ2倍）をかけたときに、どう出るかも見る。

    hython examples/128_extracttransform.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

CASES = [
    ("move", (1.0, 2.0, 3.0), (0, 0, 0), (1, 1, 1)),
    ("turn", (0, 0, 0), (10, 20, 30), (1, 1, 1)),
    ("all", (1.0, -0.5, 2.0), (10, 20, 30), (1.5, 1.5, 1.5)),
    ("stretch", (0, 0, 0), (0, 30, 0), (2.0, 1.0, 1.0)),
]


def main():
    import hou
    geo = sop_bench.fresh()
    src = geo.createNode("sphere", "src")
    src.parm("type").set("polymesh")
    src.parmTuple("t").set((0.3, 0.1, -0.2))
    rows = []
    for name, t, r, s in CASES:
        xf = geo.createNode("xform", "xf_" + name)
        xf.setInput(0, src)
        xf.parmTuple("t").set(t)
        xf.parmTuple("r").set(r)
        xf.parmTuple("s").set(s)
        ex = geo.createNode("extracttransform", "ex_" + name)
        ex.setInput(0, src)
        ex.setInput(1, xf)
        ex.parm("computedistortion").set(True)
        out = ex.geometry()
        attrs = [a.name() for a in out.pointAttribs()]
        pt = out.points()[0]
        # 取り出した変形: 点の位置 P と、transform（3×3）または orient/pscale
        # 出てくるのは P（新しい位置）・pivot（元の中心）・orient（回転）・distortion。拡大は無い
        m3 = hou.Quaternion(pt.attribValue("orient")).extractRotationMatrix3()
        pivot = hou.Vector3(pt.attribValue("P"))
        rest_pivot = hou.Vector3(pt.attribValue("pivot"))
        # 元の形の中心（extracttransform は中心のまわりの変形として出すはず）を仮定せず、
        # 元の点を「中心を引く → m3 → P を足す」でかけ直し、ずれの小さい方を採る
        rest = src.geometry().points()
        moved = xf.geometry().points()
        c = hou.Vector3(0, 0, 0)
        for p in rest:
            c += p.position()
        c /= len(rest)
        err = 0.0
        if m3 is not None:
            for a, b in zip(rest, moved):
                q = (a.position() - rest_pivot) * m3 + pivot
                err = max(err, (q - b.position()).length())
        dist = pt.attribValue("distortion") if "distortion" in attrs else None
        rows.append({"case": name, "t": t, "r": r, "s": s, "attrs": attrs,
                     "P": [round(v, 6) for v in pivot],
                     "pivot_attr": [round(v, 6) for v in rest_pivot],
                     "orient": [round(v, 6) for v in pt.attribValue("orient")],
                     "angle_deg": round(math.degrees(2 * math.acos(min(1.0, abs(pt.attribValue("orient")[3])))), 4),
                     "rest_center": [round(v, 6) for v in c],
                     "max_err": round(err, 6) if m3 is not None else None,
                     "distortion": round(dist, 6) if dist is not None else None,
                     "det": round(m3.determinant(), 6) if m3 is not None else None})
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "128_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
