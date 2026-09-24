# -*- coding: utf-8 -*-
"""実験201 — 焚き火くらいの炎（高さ 1 m 前後で揺れる）にするには、Pyro のどのつまみを動かすか。

制作の問い: pyrosource の Source Burn と pyrosolver の既定のまま燃やすと、幅 0.6 の薪から炎が 2 秒で 15 m 以上伸び続け、
焚き火にならなかった（実験202 の下準備で測った）。炎の高さを決めているのはどれか。

  実験202 と同じ薪（平たい球、半径 0.3・高さ 0.18）・同じ発生源で、Voxel Size 0.04、72 フレーム（24 fps で 3 秒）回す。
  pyrosolver の次の3つを1つずつ変える。
    Flame Lifespan（flames_lifespan、既定 2 秒）: 2・1・0.5・0.25
    Buoyancy Scale（buoyancylift、既定 1）     : Flame Lifespan 0.5 のまま 0.5・0.25
    Cooling Rate（tempcooling、既定 0.5）      : Flame Lifespan 0.5 のまま 1・2
  毎フレーム、炎（flame > 0.1）の上から 1% の高さ・炎の量・上へ伸びる速さを記録し、
  フレーム 36〜72 の高さの平均（落ち着いた高さ）と標準偏差（揺らぎ）を出す。フレーム 48・72 の炎を正面に投影して並べる。
  そのあと、Cooling Rate の頭打ちの確かめ（0.75・1.5）、3つを組み合わせて 1 m 前後を狙う条件、
  揺らぎを戻す Disturbance・Turbulence（どちらも既定の強さで入れるだけ）も回す。

    hython examples/201_pyro_flame_height.py life2      （条件を1つずつ）
    hython examples/201_pyro_flame_height.py combine
"""
import importlib.util
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

_spec = importlib.util.spec_from_file_location("e202", os.path.join(HERE, "examples", "202_pyro_campfire_cost.py"))
e202 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e202)

VOX = 0.04
FRAMES = 72
SHOTS = [48, 72]
CASES = {
    "life2": {"flames_lifespan": 2.0},
    "life1": {"flames_lifespan": 1.0},
    "life05": {"flames_lifespan": 0.5},
    "life025": {"flames_lifespan": 0.25},
    "buoy05": {"flames_lifespan": 0.5, "buoyancylift": 0.5},
    "buoy025": {"flames_lifespan": 0.5, "buoyancylift": 0.25},
    "cool1": {"flames_lifespan": 0.5, "tempcooling": 1.0},
    "cool2": {"flames_lifespan": 0.5, "tempcooling": 2.0},
    # 頭打ちの確かめ（1 と 2 が同じだったため）
    "cool075": {"flames_lifespan": 0.5, "tempcooling": 0.75},
    "cool15": {"flames_lifespan": 0.5, "tempcooling": 1.5},
    # 組み合わせて 1 m 前後を狙う
    "l025b025": {"flames_lifespan": 0.25, "buoyancylift": 0.25},
    "l025c1": {"flames_lifespan": 0.25, "tempcooling": 1.0},
    "l025b025c1": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0},
    "l025b01c1": {"flames_lifespan": 0.25, "buoyancylift": 0.1, "tempcooling": 1.0},
    # 揺らぎを戻す（Disturbance を入れる）
    "l025b025c1_dist": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_disturbance": 1},
    "l025b025c1_turb": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_turbulence": 1},
    # 揺らぎを出す強さを探す
    "fire_dist2": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_disturbance": 1, "disturbance": 2.0},
    "fire_dist5": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_disturbance": 1, "disturbance": 5.0},
    "fire_turb1": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_turbulence": 1, "turbulence": 1.0, "turbulence_usecontrol": 0},
    "fire_turb1_ctrl": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_turbulence": 1, "turbulence": 1.0},
    "fire_turb3": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_turbulence": 1, "turbulence": 3.0, "turbulence_usecontrol": 0},
    "fire_shred2": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_shredding": 1, "shredding": 2.0},
    "fire_mix": {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0, "enable_disturbance": 1, "disturbance": 2.0,
                 "enable_turbulence": 1, "turbulence": 1.0, "turbulence_usecontrol": 0, "enable_shredding": 1, "shredding": 2.0},
}


def run_one(name):
    import hou
    _, s0, _ = e202.build(0.1)
    hou.setFrame(3)
    s0.geometry()
    geo, solver, made = e202.build(VOX)
    # 実験202 で build に焚き火の設定（寿命・浮力・冷め方・揺れ）を足したので、この実験を取ったときの
    # Houdini の既定値に戻す（点検 210 で、戻さないと記録と合わないことに気づいた）
    for k in ("flames_lifespan", "buoyancylift", "tempcooling", "enable_turbulence", "turbulence", "turbulence_usecontrol"):
        solver.parm(k).revertToDefaults()
    defaults = {k: solver.parm(k).eval() for k in ("flames_lifespan", "buoyancylift", "tempcooling", "enable_disturbance", "disturbance", "enable_turbulence", "turbulence")}
    for k, v in CASES[name].items():
        solver.parm(k).set(v)
    rec = {"case": name, "set": CASES[name], "defaults": defaults, "per_frame": []}
    t0 = time.perf_counter()
    for f in range(1, FRAMES + 1):
        hou.setFrame(f)
        g = solver.geometry()
        fl = e202.field(g, "flame")
        rec["per_frame"].append({"f": f, "flame": e202.measure(fl, 0.1)})
        if f in SHOTS:
            np.save(os.path.join(OUT, f"201_{name}_flame_{f}.npy"), e202.project(fl))
    rec["sec"] = round(time.perf_counter() - t0, 2)
    with open(os.path.join(OUT, f"201_part_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump(rec, fp)
    hs = [x["flame"]["height"] for x in rec["per_frame"] if x["f"] >= 36]
    print(name, rec["sec"], round(float(np.mean(hs)), 3), round(float(np.std(hs)), 3), flush=True)


def combine():
    import sop_bench
    rows = []
    for name in CASES:
        with open(os.path.join(OUT, f"201_part_{name}.json"), encoding="utf-8") as fp:
            r = json.load(fp)
        pf = r["per_frame"]
        hs = [x["flame"]["height"] for x in pf if x["f"] >= 36]
        r["height_mean"] = round(float(np.mean(hs)), 4)
        r["height_std"] = round(float(np.std(hs)), 4)
        r["height_trend"] = round(float(np.polyfit([x["f"] for x in pf if x["f"] >= 36], hs, 1)[0] * 24), 4)  # 1 秒あたり
        r["amount_mean"] = round(float(np.mean([x["flame"]["amount"] for x in pf if x["f"] >= 36])), 5)
        early = [x for x in pf if 6 <= x["f"] <= 14]
        r["rise_speed"] = round(float(np.polyfit([x["f"] for x in early], [x["flame"]["height"] for x in early], 1)[0] * 24), 3)
        rows.append(r)
    sop_bench.save(201, rows, {"voxel": VOX, "frames": FRAMES, "shots": SHOTS})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run_one(sys.argv[1])
