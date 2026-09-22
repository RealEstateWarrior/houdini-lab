# -*- coding: utf-8 -*-
"""実験181 — 近くの点を探す VEX 関数（pcfind・nearpoints・pcopen+pcfilter）は、速さと結果が違うか。

実験178 と同じ 10 万点（1 × 1 × 1 に一様）で、全部の点について「半径 0.05 以内の最大 50 点」の P の平均を出す。
1. pcfind で番号を取り、point() で P を読んで平均
2. nearpoints で番号を取り、同じく平均
3. pcopen で開いて pcfilter（距離で重みを付けた平均）
1 と 2 は同じ平均になるはず。3 は重み付きなので少し違う値になるはず。時間（2 回の速い方）と、1 との差を比べる。

    hython examples/181_pc_speed.py
"""
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

CODES = {
    "pcfind + point": "int n[] = pcfind(0, 'P', @P, 0.05 * ch('k'), 50); vector s = 0; foreach (int i; n) s += point(0, 'P', i); v@avg = s / len(n); i@cnt = len(n);",
    "nearpoints + point": "int n[] = nearpoints(0, @P, 0.05 * ch('k'), 50); vector s = 0; foreach (int i; n) s += point(0, 'P', i); v@avg = s / len(n); i@cnt = len(n);",
    "pcopen + pcfilter": "int h = pcopen(0, 'P', @P, 0.05 * ch('k'), 50); v@avg = pcfilter(h, 'P'); i@cnt = pcnumfound(h); pcclose(h);",
    "pcfind のみ（数えるだけ）": "int n[] = pcfind(0, 'P', @P, 0.05 * ch('k'), 50); i@cnt = len(n); v@avg = @P;",
}


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    fog = geo.createNode("isooffset", "fog")
    fog.setInput(0, box)
    sc = geo.createNode("scatter::2.0", "pts")
    sc.setInput(0, fog)
    sc.parm("forcetotal").set(1)
    sc.parm("npts").set(100000)
    sc.parm("relaxpoints").set(0)
    sc.geometry()
    rows, ref = [], None
    for name, code in CODES.items():
        w = geo.createNode("attribwrangle", "w%d" % len(rows))
        w.setInput(0, sc)
        w.addSpareParmTuple(hou.FloatParmTemplate("k", "k", 1, default_value=(1.0,)))
        w.parm("snippet").set(code)
        w.geometry()
        best = 1e9
        for i in range(2):
            w.parm("k").set(1.0 + (i + 1) * 1e-7)
            t0 = time.perf_counter()
            g = w.geometry()
            best = min(best, time.perf_counter() - t0)
        w.parm("k").set(1.0)
        g = w.geometry()
        avg = [p.attribValue("avg") for p in g.points()]
        cnt = g.pointIntAttribValues("cnt")
        if ref is None:
            ref = avg
        diff = [((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5 for a, b in zip(avg, ref)]
        rows.append({"method": name, "sec": round(best, 4), "us_per_point": round(best / 100000 * 1e6, 3),
                     "mean_found": round(statistics.fmean(cnt), 2), "max_diff_vs_pcfind": round(max(diff), 7),
                     "mean_diff_vs_pcfind": round(statistics.fmean(diff), 7)})
        print(rows[-1])
    sop_bench.save(181, rows)


if __name__ == "__main__":
    main()
