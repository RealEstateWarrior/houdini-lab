# -*- coding: utf-8 -*-
"""実験094 — 升目を半分にすると、何倍重くなるか。

VDB は空間を升目に区切る。1辺を半分にすると、升目の数は8倍になるはず。
ただし VDB は「表面の近くだけ」持つので、増え方は8倍より小さいのではないか。
実際に測る。

測るもの: 変換にかかる時間、VDB の中に入っている升目の数（面に戻す前）、
面に戻したときの面の数、そして元の形からのずれ。

    hython examples/094_vdb_voxel.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

VOXEL = [0.2, 0.1, 0.05, 0.025, 0.0125]


def main():
    geo = sop_bench.fresh()
    sphere = geo.createNode("sphere", "src_sphere")
    sphere.parm("type").set("polymesh")
    sphere.parm("rows").set(50)
    sphere.parm("cols").set(50)
    mountain = geo.createNode("mountain", "src_mountain")
    mountain.setInput(0, sphere)
    mountain.parm("height").set(0.15)
    mountain.parm("elementsize").set(0.6)
    mountain.parmTuple("offset").set((11.0, 0.0, 0.0))
    base = mountain.geometry()
    print(f"元: {base.intrinsicValue('primitivecount')} 面")

    rows = []
    prev_voxels = None
    for voxel in VOXEL:
        vdb = geo.createNode("vdbfrompolygons", f"vdb_{voxel}")
        vdb.setInput(0, mountain)
        vdb.parm("voxelsize").set(voxel)
        start = time.perf_counter()
        vgeo = vdb.geometry()
        make = time.perf_counter() - start

        # VDB の中の升目の数。prim ごとに intrinsic で聞く
        voxels = 0
        for prim in vgeo.prims():
            try:
                voxels += prim.intrinsicValue("activevoxelcount")
            except hou_error():
                pass

        back = geo.createNode("convertvdb", f"back_{voxel}")
        back.setInput(0, vdb)
        back.parm("conversion").set("poly")
        start = time.perf_counter()
        out = back.geometry()
        convert = time.perf_counter() - start
        gap = sop_bench.spread(out, base)

        row = {
            "voxel": voxel,
            "voxels": voxels,
            "voxel_ratio": round(voxels / prev_voxels, 3) if prev_voxels else None,
            "prims": out.intrinsicValue("primitivecount"),
            "make_seconds": round(make, 4),
            "convert_seconds": round(convert, 4),
            "gap_mean": round(gap["mean"], 6),
            "gap_max": round(gap["max"], 6),
        }
        prev_voxels = voxels
        rows.append(row)
        print(f"  升目 {voxel:<7} -> 升目数 {voxels:>9} "
              + (f"(前の {row['voxel_ratio']}倍) " if row["voxel_ratio"] else "")
              + f"作る {make:.3f}秒 戻す {convert:.3f}秒 "
              f"{row['prims']} 面 ずれ 平均 {row['gap_mean']:.6f}")

    sop_bench.save("094", rows)


def hou_error():
    import hou
    return hou.OperationFailed


if __name__ == "__main__":
    main()
