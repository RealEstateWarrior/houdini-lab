# -*- coding: utf-8 -*-
"""実験167 — rbdbulletsolver で落とした 1×1×1 の箱は、どの高さで止まるか。Collision Padding はどう効くか。

箱（中心 y = 2）に name を付けて rbdbulletsolver に入れ、Ground Type = Ground Plane（y = 0）に落とす。
止まったあと（4 秒後）の箱の底（点の y の最小）と中心の高さを読む。
Collision Padding（形のまわりに付ける余白）が 0・0.02（既定）・0.05 のとき、底が 0 から浮くか、沈むかを見る。
最初に地面に当たったあとの、いちばん高く跳ね返った高さ（Bounce の効き方）も残す。

    hython examples/167_rbd_rest.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def main():
    hou.setFps(24)
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    box.parmTuple("t").set((0, 2, 0))
    nm = geo.createNode("attribwrangle", "name")
    nm.setInput(0, box)
    nm.parm("class").set("primitive")
    nm.parm("snippet").set('s@name = "box";')
    rows, tracks = [], {}
    for margin in (0.0, 0.02, 0.05):
        for bounce in (0.25, 0.8):
            sv = geo.createNode("rbdbulletsolver", f"rbd_{int(margin * 100)}_{int(bounce * 100)}")
            sv.setInput(0, nm)
            sv.parm("useground").set("1")
            sv.parm("margin").set(margin)
            sv.parm("bounce").set(bounce)
            sv.parm("ground_bounce").set(bounce)
            ys = []
            t0 = time.perf_counter()
            for F in range(1, 98):
                hou.setFrame(F)
                g = sv.geometry()
                ys.append(min(p.position()[1] for p in g.points()))
            sec = time.perf_counter() - t0
            first_hit = next(i for i, y in enumerate(ys) if y < 0.05)
            rebound = max(ys[first_hit:first_hit + 24])
            g = sv.geometry()
            cy = sum(p.position()[1] for p in g.points()) / len(g.points())
            key = f"m{margin:g}_b{bounce:g}"
            tracks[key] = [round(y, 4) for y in ys]
            rows.append({"margin": margin, "bounce": bounce, "bottom_rest": round(ys[-1], 6), "center_rest": round(cy, 6),
                         "lowest": round(min(ys), 6), "first_hit_frame": first_hit + 1, "rebound": round(rebound, 4),
                         "sec_97f": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(167, rows, {"tracks": tracks})


if __name__ == "__main__":
    main()
