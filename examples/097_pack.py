# -*- coding: utf-8 -*-
"""実験097 — pack すると、どれだけ軽くなるのか。

copytopoints の「Pack and Instance」を入れると、複製を1点として扱う。
軽くなると言われるが、どこがどれだけ軽くなるのかは曖昧なままだった。
3つを測る。

  1. 持っている点と面の数
  2. 計算（cook）にかかる時間
  3. ディスクに書いたときのファイルの大きさ

複製する形は球（20×20＝400面・402点）。並べる数を 100 / 1,000 / 10,000 と変える。

    hython examples/097_pack.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

import sop_bench  # noqa: E402

COUNTS = [100, 1000, 10000]


def main():
    geo = sop_bench.fresh()

    # 複製する形
    sphere = geo.createNode("sphere", "unit")
    sphere.parm("type").set("polymesh")
    sphere.parm("rows").set(20)
    sphere.parm("cols").set(20)
    sphere.parmTuple("rad").set((0.05, 0.05, 0.05))
    unit = sphere.geometry()
    print(f"複製する形: {unit.intrinsicValue('pointcount')}点 "
          f"{unit.intrinsicValue('primitivecount')}面")

    # 並べ先の点
    grid = geo.createNode("grid", "field")
    grid.parmTuple("size").set((10.0, 10.0))
    grid.parm("rows").set(2)
    grid.parm("cols").set(2)

    rows = []
    for count in COUNTS:
        scatter = geo.createNode("scatter::2.0", f"pts_{count}")
        scatter.setInput(0, grid)
        scatter.parm("forcetotal").set(True)
        scatter.parm("npts").set(count)
        scatter.parm("seed").set(1)
        scatter.geometry()          # 先に点を作っておく（時間に混ぜない）

        for packed in (False, True):
            copy = geo.createNode("copytopoints::2.0",
                                  f"cp_{count}_{int(packed)}")
            copy.setInput(0, sphere)
            copy.setInput(1, scatter)
            copy.parm("pack").set(packed)
            start = time.perf_counter()
            out = copy.geometry()
            elapsed = time.perf_counter() - start

            # ディスクに書いて大きさを見る
            name = f"097_{count}_{'pack' if packed else 'raw'}.bgeo.sc"
            path = os.path.join(OUT, name)
            rop = geo.createNode("rop_geometry", f"rop_{count}_{int(packed)}")
            rop.setInput(0, copy)
            rop.parm("sopoutput").set(path)
            rop.parm("trange").set(0)
            start_w = time.perf_counter()
            rop.parm("execute").pressButton()
            write = time.perf_counter() - start_w
            size = os.path.getsize(path) if os.path.exists(path) else 0
            os.remove(path)

            row = {
                "count": count,
                "packed": packed,
                "points": out.intrinsicValue("pointcount"),
                "prims": out.intrinsicValue("primitivecount"),
                "seconds": round(elapsed, 4),
                "write_seconds": round(write, 4),
                "bytes": size,
                "mb": round(size / 1024 / 1024, 3),
            }
            rows.append(row)
            print(f"  {count:>6} 個 pack={'入' if packed else '切'} -> "
                  f"{row['points']:>9,}点 {row['prims']:>9,}面 "
                  f"計算 {elapsed:.3f}秒 書き出し {write:.3f}秒 {row['mb']}MB")

    sop_bench.save("097", rows,
                   {"unit_points": unit.intrinsicValue("pointcount"),
                    "unit_prims": unit.intrinsicValue("primitivecount")})


if __name__ == "__main__":
    main()
