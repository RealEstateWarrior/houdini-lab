# -*- coding: utf-8 -*-
"""実験183 — rbdbulletsolver の Bounce と跳ね返りの高さ、Bullet Substeps と当たった瞬間の沈み込み。

実験167 と同じ箱（中心 y = 2、底は 1.5 から落ちる）を Ground Plane に落とす。
1. Bounce（箱と地面の両方に同じ値）を 0・0.25・0.5・0.75・1 にして、最初の跳ね返りの高さ（底の y の最大）を読む。
   跳ね返り係数 e なら、跳ね返りの高さは落とした高さ × e²。箱と地面の e を掛け合わせるなら × b⁴。
2. Bullet Substeps（既定 10）を 1・10・50 にして、当たった瞬間の沈み込み（底の y の最小）を読む。

    hython examples/183_rbd_bounce.py
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
    cases = [(0.02, b, 10) for b in (0.0, 0.25, 0.5, 0.75, 1.0)] + [(0.02, 0.5, s) for s in (1, 50)]
    for margin, bounce, bsub in cases:
        if True:
            sv = geo.createNode("rbdbulletsolver", f"rbd_{int(bounce * 100)}_{bsub}")
            sv.setInput(0, nm)
            sv.parm("useground").set("1")
            sv.parm("margin").set(margin)
            sv.parm("bounce").set(bounce)
            sv.parm("ground_bounce").set(bounce)
            sv.parm("substeps").set(bsub)
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
            key = f"b{bounce:g}_s{bsub}"
            tracks[key] = [round(y, 4) for y in ys]
            rows.append({"bounce": bounce, "bullet_substeps": bsub, "bottom_rest": round(ys[-1], 6), "center_rest": round(cy, 6),
                         "lowest": round(min(ys), 6), "first_hit_frame": first_hit + 1, "rebound": round(rebound, 4),
                         "sec_97f": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(183, rows, {"tracks": tracks})


if __name__ == "__main__":
    main()
