# -*- coding: utf-8 -*-
"""実験171 — VEX の curlnoise() は、本当に「湧き出しのない」（発散 0 の）流れか。

1 × 1 × 1 の中に 20³ = 8000 点を並べ、各点で
  v = curlnoise(P * f)          と      v = noise(P * f) を3成分にしたもの（ふつうのベクトルノイズ）
を中心差分（h = 0.001）で微分して、発散 ∂vx/∂x + ∂vy/∂y + ∂vz/∂z を出す。
curl（回転）から作った流れなら発散は 0 のはず。ふつうのノイズと比べて、どれだけ小さいかを見る。
発散の大きさは、速さの微分の大きさ（|∂vx/∂x| などの平均）で割って比べる。

    hython examples/171_curl_divergence.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

SNIPPET = r'''
float h = 0.001;
float f = chf("freq");
function vector F(vector p; float f; int kind) {
    if (kind == 0) return curlnoise(p * f);
    if (kind == 1) return vector(noise(p * f));
    return curlxnoise(p * f);
}
int kind = chi("kind");
vector dx = (F(@P + {1,0,0} * h, f, kind) - F(@P - {1,0,0} * h, f, kind)) / (2 * h);
vector dy = (F(@P + {0,1,0} * h, f, kind) - F(@P - {0,1,0} * h, f, kind)) / (2 * h);
vector dz = (F(@P + {0,0,1} * h, f, kind) - F(@P - {0,0,1} * h, f, kind)) / (2 * h);
f@div = dx.x + dy.y + dz.z;
f@scale = (abs(dx.x) + abs(dy.y) + abs(dz.z)) / 3;
v@vel = F(@P, f, kind);
'''


def main():
    geo = sop_bench.fresh()
    pts = geo.createNode("attribwrangle", "pts")
    pts.parm("class").set("detail")
    pts.parm("snippet").set("for (int i = 0; i < 20; i++) for (int j = 0; j < 20; j++) for (int k = 0; k < 20; k++)"
                            " addpoint(0, set(i, j, k) / 19.0 - 0.5);")
    rows = []
    for kind, label in ((0, "curlnoise"), (2, "curlxnoise"), (1, "noise（ふつう）")):
        for freq in (1.0, 4.0):
            w = geo.createNode("attribwrangle", f"w{kind}_{int(freq)}")
            w.setInput(0, pts)
            w.parm("snippet").set(SNIPPET)
            w.addSpareParmTuple(__import__("hou").FloatParmTemplate("freq", "freq", 1))
            w.addSpareParmTuple(__import__("hou").IntParmTemplate("kind", "kind", 1))
            w.parm("freq").set(freq)
            w.parm("kind").set(kind)
            t0 = time.perf_counter()
            g = w.geometry()
            sec = time.perf_counter() - t0
            div = g.pointFloatAttribValues("div")
            sc = g.pointFloatAttribValues("scale")
            mean_abs_div = sum(abs(x) for x in div) / len(div)
            mean_scale = sum(sc) / len(sc)
            speeds = [sum(c * c for c in p.attribValue("vel")) ** 0.5 for p in g.points()]
            rows.append({"kind": label, "freq": freq, "points": len(div), "mean_abs_div": mean_abs_div,
                         "max_abs_div": max(abs(x) for x in div), "mean_grad": round(mean_scale, 6),
                         "ratio": mean_abs_div / mean_scale, "mean_speed": round(sum(speeds) / len(speeds), 6), "sec": round(sec, 4)})
            print(rows[-1])
    sop_bench.save(171, rows)


if __name__ == "__main__":
    main()
