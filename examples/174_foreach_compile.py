# -*- coding: utf-8 -*-
"""実験174 — for-each（かけらごとの繰り返し）は、かけらの数に比例して遅くなるか。compile block で速くなるか。

N 個の箱（copytopoints で並べ、name でかけらを分ける）を、block_begin / block_end（Piece で name ごと）で1つずつ回す。
中の処理は「かけらの中心へ縮める」attribwrangle を1つだけ（@P = lerp(中心, @P, 0.8)）。
同じ処理を、繰り返しを使わず attribwrangle 1つで全部に一度にかけたものとも比べる（結果が同じか確かめる）。
compile_begin / compile_end で囲んだ場合も、同じ N で時間をはかる。Multithread when Compiled も入れる。

    hython examples/174_foreach_compile.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402

SHRINK = "vector c = getbbox_center(0); @P = lerp(c, @P, 0.8 * ch('k'));"


def timed(end, w):
    """cook(force=True) では VEX が計算し直さない（実験173）ので、w が読む k を少し変えてからはかる。"""
    if w.parm("k") is None:
        w.addSpareParmTuple(hou.FloatParmTemplate("k", "k", 1, default_value=(1.0,)))
    w.parm("k").set(1.0)
    end.geometry()
    best = 1e9
    for i in range(3):
        w.parm("k").set(1.0 + (i + 1) * 1e-7)
        t0 = time.perf_counter()
        end.geometry()
        best = min(best, time.perf_counter() - t0)
    w.parm("k").set(1.0)
    end.geometry()
    return best


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    box.parm("scale").set(0.3)
    rows = []
    for N in (10, 100, 1000):
        grid = geo.createNode("grid", f"grid{N}")
        side = int(round(N ** 0.5 + 0.49))
        grid.parm("rows").set(side)
        grid.parm("cols").set(side)
        grid.parmTuple("size").set((side, side))
        keep = geo.createNode("attribwrangle", f"keep{N}")
        keep.setInput(0, grid)
        keep.parm("snippet").set(f"if (@ptnum >= {N}) removepoint(0, @ptnum);")
        cp = geo.createNode("copytopoints::2.0", f"cp{N}")
        cp.setInput(0, box)
        cp.setInput(1, keep)
        nm = geo.createNode("attribwrangle", f"nm{N}")
        nm.setInput(0, cp)
        nm.parm("class").set("primitive")
        nm.parm("snippet").set('s@name = sprintf("p%d", @primnum / 6);')
        results = {}
        for mode in ("foreach", "compiled", "compiled_mt", "one_wrangle"):
            if mode == "one_wrangle":
                w = geo.createNode("attribwrangle", f"one{N}")
                w.setInput(0, nm)
                # かけらごとの中心を、同じ name の点の平均から出す
                w.parm("snippet").set('int pr[] = findattribval(0, "prim", "name", s@name);'
                                      ' vector lo = {1e9,1e9,1e9}, hi = {-1e9,-1e9,-1e9};'
                                      ' foreach (int p; pr) { int pts[] = primpoints(0, p); foreach (int q; pts) {'
                                      ' vector P = point(0, "P", q); lo = min(lo, P); hi = max(hi, P); } }'
                                      ' @P = lerp((lo + hi) / 2, @P, 0.8 * ch("k"));')
                nm_pt = geo.createNode("attribpromote", f"prom{N}")
                nm_pt.setInput(0, nm)
                nm_pt.parm("inname").set("name")
                nm_pt.parm("inclass").set("primitive")
                nm_pt.parm("outclass").set("point")
                nm_pt.parm("deletein").set(0)
                w.setInput(0, nm_pt)
                end = w
            else:
                bb = geo.createNode("block_begin", f"bb_{mode}_{N}")
                be = geo.createNode("block_end", f"be_{mode}_{N}")
                bb.parm("method").set("piece")
                bb.parm("blockpath").set(f"../{be.name()}")
                be.parm("itermethod").set("pieces")
                be.parm("method").set("merge")
                be.parm("class").set("primitive")
                be.parm("useattrib").set(1)
                be.parm("attrib").set("name")
                be.parm("blockpath").set(f"../{bb.name()}")
                be.parm("templatepath").set(f"../{bb.name()}")
                w = geo.createNode("attribwrangle", f"w_{mode}_{N}")
                w.parm("snippet").set(SHRINK)
                if mode == "foreach":
                    bb.setInput(0, nm)
                    w.setInput(0, bb)
                    be.setInput(0, w)
                    end = be
                else:
                    cb = geo.createNode("compile_begin", f"cb_{mode}_{N}")
                    ce = geo.createNode("compile_end", f"ce_{mode}_{N}")
                    cb.parm("blockpath").set(f"../{ce.name()}")
                    cb.setInput(0, nm)
                    bb.setInput(0, cb)
                    w.setInput(0, bb)
                    be.setInput(0, w)
                    be.parm("multithread").set(1 if mode == "compiled_mt" else 0)
                    ce.setInput(0, be)
                    end = ce
            sec = timed(end, w)
            g = end.geometry()
            results[mode] = [p.position() for p in g.points()]
            rows.append({"pieces": N, "mode": mode, "points": len(g.points()), "sec": round(sec, 4),
                         "ms_per_piece": round(sec / N * 1000, 4), "warn": " / ".join(end.warnings())[:120],
                         "err": " / ".join(end.errors())[:120]})
            print(rows[-1])
        ref = results["foreach"]
        for r in rows[-4:]:
            other = results[r["mode"]]
            r["max_diff"] = max((a - b).length() for a, b in zip(ref, other)) if len(other) == len(ref) else None
    sop_bench.save(174, rows)


if __name__ == "__main__":
    main()
