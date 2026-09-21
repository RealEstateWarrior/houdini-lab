# -*- coding: utf-8 -*-
"""実験131 — bend で曲げた線は、長さを保ったまま円弧になるか。

z 方向に長さ1の線（100分割）を、捕まえる範囲（origin 0・dir z・length 1）いっぱいに
角度 θ だけ曲げる。長さを保って円弧になるなら、半径 R = 1/θ（ラジアン）で、
端の点は（曲げる向きを y とすると）y = R(1 − cos θ)、z = R sin θ になる。
長さ2の線（範囲の外に1はみ出す）では、外の部分がまっすぐ接線の向きに伸びるはず。

    hython examples/131_bend.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def length_of(parent, node):
    meas = parent.createNode("measure", "len")
    meas.setInput(0, node)
    meas.parm("measure").set("perimeter")
    meas.parm("attribname").set("len")
    total = sum(p.attribValue("len") for p in meas.geometry().prims())
    meas.destroy()
    return total


def main():
    geo = sop_bench.fresh()
    rows = []
    for total_len in (1.0, 2.0):
        line = geo.createNode("line", f"line{int(total_len)}")
        line.parmTuple("dir").set((0.0, 0.0, 1.0))
        line.parm("dist").set(total_len)
        line.parm("points").set(int(100 * total_len) + 1)
        for deg in (45, 90, 180, 270, 360):
            bd = geo.createNode("bend", f"bd_{int(total_len)}_{deg}")
            bd.setInput(0, line)
            bd.parm("bend").set(deg)
            bd.parmTuple("origin").set((0.0, 0.0, 0.0))
            bd.parmTuple("dir").set((0.0, 0.0, 1.0))
            bd.parm("length").set(1.0)
            g = bd.geometry()
            pts = g.points()
            mid = pts[100].position()      # 範囲の終わり（z=1 だった点）
            end = pts[-1].position()
            th = math.radians(deg)
            R = 1 / th
            want_mid = (0.0, R * (1 - math.cos(th)), R * math.sin(th))
            # 範囲の外は、接線（cos θ・sin θ の向き）にまっすぐ伸びる
            extra = total_len - 1.0
            want_end = (0.0, want_mid[1] + extra * math.sin(th), want_mid[2] + extra * math.cos(th))
            rows.append({"line": total_len, "deg": deg, "length": round(length_of(geo, bd), 6),
                         "mid": [round(v, 6) for v in mid], "want_mid": [round(v, 6) for v in want_mid],
                         "mid_err": round(math.dist(mid, want_mid), 6),
                         "end": [round(v, 6) for v in end], "want_end": [round(v, 6) for v in want_end],
                         "end_err": round(math.dist(end, want_end), 6)})
            print(rows[-1])
    path = os.path.join(sop_bench.OUT, "131_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
