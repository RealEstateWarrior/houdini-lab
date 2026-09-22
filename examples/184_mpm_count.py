# -*- coding: utf-8 -*-
"""実験184 — mpmsource が箱に詰める粒の数は、体積 ÷ Particle Separation³ か。粒の pscale と density は何が入るか。

1 × 1 × 1 の箱を mpmsource（入力 2 に mpmcontainer）で粒にする。mpmcontainer の Particle Separation s を
0.1・0.05・0.025 と変え、粒の数・粒の mass の合計・1粒あたりの体積の属性を読む。
粒の数 × s³ が 1（箱の体積）に近いか、mass の合計が density（既定 400）× 体積に近いかを見る。
Jitter Scale を 0 にしたときの並び（升目どおりか）も確かめる。

    hython examples/184_mpm_count.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    rows = []
    for s in (0.1, 0.05, 0.025):
        for jitter in (1.0, 0.0):
            cont = geo.createNode("mpmcontainer", f"c{int(s * 1000)}_{int(jitter)}")
            cont.parm("particlesep").set(s)
            src = geo.createNode("mpmsource", f"s{int(s * 1000)}_{int(jitter)}")
            src.setInput(0, box)
            src.setInput(1, cont)
            src.parm("jitterscale").set(jitter)
            t0 = time.perf_counter()
            g = src.geometry()
            sec = time.perf_counter() - t0
            n = len(g.points())
            attrs = [a.name() for a in g.pointAttribs()]
            mass = sum(g.pointFloatAttribValues("mass")) if "mass" in attrs else None
            vol = sum(g.pointFloatAttribValues("volume")) if "volume" in attrs else None
            xs = sorted({round(p.position()[0], 5) for p in g.points()}) if jitter == 0 else []
            ps = g.pointFloatAttribValues("pscale")
            dens = g.pointFloatAttribValues("density")
            rows.append({"sep": s, "jitter": jitter, "points": n, "n_s3": round(n * s ** 3, 5),
                         "pscale_min": round(min(ps), 6), "pscale_max": round(max(ps), 6),
                         "density_min": round(min(dens), 3), "density_max": round(max(dens), 3),
                         "mass_sum": round(mass, 4) if mass is not None else None,
                         "volume_sum": round(vol, 6) if vol is not None else None,
                         "x_layers": len(xs), "x_min": xs[0] if xs else None, "x_max": xs[-1] if xs else None,
                         "attrs": [a for a in attrs if a in ("mass", "volume", "pscale", "density", "v")],
                         "sec": round(sec, 3)})
            print(rows[-1])
    sop_bench.save(184, rows)


if __name__ == "__main__":
    main()
