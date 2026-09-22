# -*- coding: utf-8 -*-
"""実験189 — 100 個の箱を sopimport で USD にすると、プリムはいくつできるか。Packed Primitives の扱いで変わるか。

SOP で箱を 100 個並べる（copytopoints）。Pack and Instance を入れたもの（パックした 100 個）と、入れないもの（ただの面 600 枚）を用意し、
LOP の sopimport で読み込んで、USD のステージのプリムの数（種類ごと）と、組み立ての時間をはかる。
パックしたものは Packed Primitives を Native Instances（既定）・Point Instancer・Xforms・Unpack で比べる。

    hython examples/189_usd_packed.py
"""
import collections
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import hou  # noqa: E402
import sop_bench  # noqa: E402


def main():
    geo = sop_bench.fresh()
    box = geo.createNode("box", "box")
    box.parm("scale").set(0.3)
    grid = geo.createNode("grid", "grid")
    grid.parm("rows").set(10)
    grid.parm("cols").set(10)
    grid.parmTuple("size").set((10, 10))
    packed = geo.createNode("copytopoints::2.0", "packed")
    packed.setInput(0, box)
    packed.setInput(1, grid)
    packed.parm("pack").set(1)
    plain = geo.createNode("copytopoints::2.0", "plain")
    plain.setInput(0, box)
    plain.setInput(1, grid)
    plain.parm("pack").set(0)
    stage = hou.node("/stage")
    for c in stage.children():
        c.destroy()
    # 1回目の LOP は USD の立ち上げで 20 秒ほどかかるので、先に1つ読み込んでおく
    warm = stage.createNode("sopimport", "warmup")
    warm.parm("soppath").set(box.path())
    warm.stage()
    rows = []
    cases = [("パックしない", plain, None)] + [("パックした", packed, m) for m in ("nativeinstances", "pointinstancer", "xforms", "unpack")]
    for label, src, mode in cases:
        si = stage.createNode("sopimport", f"imp_{src.name()}_{mode or 'none'}")
        si.parm("soppath").set(src.path())
        if mode:
            si.parm("enable_packedhandling").set(1)
            si.parm("packedhandling").set(mode)
        t0 = time.perf_counter()
        st = si.stage()
        sec = time.perf_counter() - t0
        types = collections.Counter(str(p.GetTypeName()) or "(型なし)" for p in st.Traverse())
        inst = sum(1 for p in st.Traverse() if p.IsInstance())
        protos = len(st.GetPrototypes()) if hasattr(st, "GetPrototypes") else None
        rows.append({"case": label, "mode": mode or "—", "prims": sum(types.values()), "types": dict(types),
                     "instances": inst, "prototypes": protos, "sec": round(sec, 4)})
        print(rows[-1])
    sop_bench.save(189, rows, {"sop_prims_plain": len(plain.geometry().prims()), "sop_prims_packed": len(packed.geometry().prims())})


if __name__ == "__main__":
    main()
