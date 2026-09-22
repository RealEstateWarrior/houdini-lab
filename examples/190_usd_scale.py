# -*- coding: utf-8 -*-
"""実験190 — 1 万個の箱を USD にしたときの、読み込み時間とファイルの大きさ。Packed Primitives の扱いで何倍違うか。

実験189 と同じ作りで、箱を 100 × 100 = 1 万個にする。sopimport の読み込み時間（USD の立ち上げは先に済ませる）と、
ステージを .usdc（バイナリ）で書き出したファイルの大きさを、Packed Primitives の扱いごとに比べる。

    hython examples/190_usd_scale.py
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
    grid.parm("rows").set(100)
    grid.parm("cols").set(100)
    grid.parmTuple("size").set((100, 100))
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
        path = os.path.join(sop_bench.OUT, f"_190_{mode or 'plain'}.usdc")
        t1 = time.perf_counter()
        st.Export(path)
        wsec = time.perf_counter() - t1
        size = os.path.getsize(path)
        os.remove(path)
        rows.append({"case": label, "mode": mode or "—", "prims": sum(types.values()), "types": dict(types),
                     "instances": inst, "prototypes": protos, "sec": round(sec, 4), "write_sec": round(wsec, 4),
                     "bytes": size})
        print(rows[-1])
    sop_bench.save(190, rows, {"sop_prims_plain": len(plain.geometry().prims()), "sop_prims_packed": len(packed.geometry().prims())})


if __name__ == "__main__":
    main()
