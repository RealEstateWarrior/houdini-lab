# -*- coding: utf-8 -*-
"""実験209 — 設定を振って何通りも回すとき、PDG で同時に何本回すと速いか。

制作の問い: 焚き火の揺れ（Turbulence）を 8 通り試して比べたい。1 つの Houdini の中で順に回すのと、
PDG（TOP ネットワークの wedge）で別々の Houdini に分けて同時に回すのとでは、どちらが速いか。同時に何本がよいか。

  実験202 の焚き火（Voxel Size 0.03）を 48 フレーム回して、フレーム 48 を書き出す仕事を、Turbulence 1・1.5・…・4.5 の 8 通り。
    inproc … 1 つの hython の中で、Turbulence を変えながら順に 8 回
    pdg1 / pdg2 / pdg4 / pdg8 … topnet の wedge（8 本）→ ropgeometry。localscheduler の同時に回す数（Total Slots）を 1・2・4・8 に
             （既定は「CPU の 1/4」。このパソコンは 32 スレッドなので 8）
  どちらも 48 フレームを毎フレーム書き出す（vel を消した形。実験204）。PDG は 1〜48 を 1 つの束（All Frames in One Batch）にする。
  全体にかかった時間と、フレーム 48 のファイルの大きさ（どのやり方でも同じになるか）を記録する。

    hython examples/209_pdg_wedge_slots.py
"""
import glob
import importlib.util
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
GEO = os.path.join(OUT, "_209_geo")
VOX = 0.03
FRAME = 48
COUNT = 8
SLOTS = [1, 2, 4, 8]


def main():
    import hou
    import hou_tools
    import sop_bench
    spec = importlib.util.spec_from_file_location("e202", os.path.join(HERE, "examples", "202_pyro_campfire_cost.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    hou.setFps(24)
    geo, solver, _ = m.build(VOX)
    # 書き出すのは速度 vel を消した形（実験204: 容量の 9 割以上が vel）。どちらのやり方も毎フレーム書き出す
    drop = geo.createNode("blast", "drop_vel")
    drop.setFirstInput(solver)
    drop.parm("group").set("@name=vel.*")
    drop.parm("grouptype").set("prims")
    os.makedirs(GEO, exist_ok=True)
    rows = []

    # --- 1 つの hython の中で順に回す ---
    turb = solver.parm("turbulence")
    t0 = time.perf_counter()
    for i in range(COUNT):
        turb.deleteAllKeyframes()
        turb.set(1.0 + 0.5 * i)
        for f in range(1, FRAME + 1):
            hou.setFrame(f)
            drop.geometry().saveToFile(os.path.join(GEO, f"inproc_{i}.{f:04d}.bgeo.sc"))
    inproc_sizes = [os.path.getsize(os.path.join(GEO, f"inproc_{i}.{FRAME:04d}.bgeo.sc")) for i in range(COUNT)]
    rows.append({"case": "inproc", "slots": 0, "sec": round(time.perf_counter() - t0, 2)})
    print(rows[-1], flush=True)

    # --- PDG ---
    turb.setExpression("1 + @wedgeindex * 0.5")
    hou.setFrame(1)
    top = hou.node("/obj").createNode("topnet", "wedge_turbulence")
    sched = [c for c in top.children() if c.type().name() == "localscheduler"][0]
    wedge = top.createNode("wedge", "eight_turbulences")
    wedge.parm("wedgecount").set(COUNT)
    wedge.parm("wedgeattributes").set(0)
    write = top.createNode("ropgeometry", "write_fire")
    write.setFirstInput(wedge)
    write.parm("soppath").set(drop.path())
    write.parm("sopoutput").set("$HIP/_209_geo/fire_`@wedgeindex`.$F4.bgeo.sc")
    # シミュレーションは 1 フレーム目から順に回さないと進まない。1〜48 を 1 つの束にして 1 つの hython で回させる。
    # 落とし穴（1・2 回目の測定で気づいた）: Evaluate Using の既定は Single Frame で、仕事 1 つにつき 1 フレーム目しか書かなかった
    # （燃え始めの 34 KB）。Valid Frame Range を Render Frame Range にしても変わらない。f1・f2 には最初から式が入っている
    labels = write.parm("framegeneration").parmTemplate().menuLabels()
    write.parm("framegeneration").set(1)       # Frame Range
    for k, v in (("f1", 1), ("f2", FRAME), ("f3", 1)):
        write.parm(k).deleteAllKeyframes()
        write.parm(k).set(v)
    write.parm("batchall").set(1)
    top.layoutChildren()
    geo.layoutChildren()
    hip = os.path.join(OUT, "209_scene.hipnc")
    # ropgeometry の仕事は、別の hython が保存済みの hip を開いて行う（実践「PDG で形違いを一度に書き出す」）
    hou_tools.save_hip(hip)
    sizes_ref = None
    for n in SLOTS:
        for old in glob.glob(os.path.join(GEO, "fire_*")):
            os.remove(old)
        sched.parm("maxprocsmenu").set(2)      # Custom Slot Count
        sched.parm("maxprocs").set(n)
        hou.hipFile.save(hip)
        write.dirtyAllWorkItems(True)
        t0 = time.perf_counter()
        write.cookWorkItems(block=True)
        sec = time.perf_counter() - t0
        files = sorted(glob.glob(os.path.join(GEO, "fire_*.bgeo.sc")))
        sizes = [os.path.getsize(os.path.join(GEO, f"fire_{i}.{FRAME:04d}.bgeo.sc")) for i in range(COUNT)
                 if os.path.exists(os.path.join(GEO, f"fire_{i}.{FRAME:04d}.bgeo.sc"))]
        rows.append({"case": f"pdg{n}", "slots": n, "sec": round(sec, 2), "files": len(files), "sizes": sizes})
        print({k: v for k, v in rows[-1].items() if k != "sizes"}, flush=True)
        sizes_ref = sizes_ref or sizes
    same = inproc_sizes
    turb.setExpression("1 + @wedgeindex * 0.5")
    hou_tools.save_hip(hip)
    hou_tools.write_graph(top.path(), os.path.join(OUT, "209_graph.json"), title="実験209")
    shutil.rmtree(GEO, ignore_errors=True)
    sop_bench.save(209, rows, {"vox": VOX, "frame": FRAME, "count": COUNT, "cpu": os.cpu_count(),
                              "inproc_sizes": same, "framegeneration_labels": list(labels),
                              "sched_menu": list(sched.parm("maxprocsmenu").parmTemplate().menuLabels())})


if __name__ == "__main__":
    main()
