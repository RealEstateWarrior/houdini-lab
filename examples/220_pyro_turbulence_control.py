# -*- coding: utf-8 -*-
"""実験220 — 焚き火の Turbulence は、Use Control Field を入れたまま（既定）でも効くのか。実験201 の結論の確かめ直し。

制作の問い: 焚き火の炎を揺らしたい。pyrosolver の Turbulence を入れるとき、Use Control Field は切らないといけないのか。
実験201 は「Use Control Field を切らないと Turbulence は効かない」と書いた。その根拠の 2 条件（Use Control Field 入り）の記録は、
揺らぎなしの条件とすべてのフレームで同じ値だった。ところが点検（実験210）で流し直すと、2 条件とも炎が高く出て、記録と合わなかった。

  実験201 と同じ焚き火（実験202 の組み立て、Voxel Size 0.04、72 フレーム。寿命 0.25・浮力 0.25・冷め方 1）で、
    base … 揺らぎなし
    ctrl … Turbulence 1、Use Control Field 入り（既定）
    free … Turbulence 1、Use Control Field 切り
  を、条件ごとに別の Houdini（hython）で 2 回ずつ回す。フレーム 36〜72 の炎の高さの平均と、フレームごとの高さを比べる。
  Use Control Field にかかわるつまみ（名前に turbulence を含むもの）の値も書き出す。

    hython examples/220_pyro_turbulence_control.py base 1
    python examples/220_pyro_turbulence_control.py combine    （Houdini なしでまとめる）
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")
VOX, FRAMES = 0.04, 72
FIRE = {"flames_lifespan": 0.25, "buoyancylift": 0.25, "tempcooling": 1.0}
CASES = {"base": {},
         "ctrl": {"enable_turbulence": 1, "turbulence": 1.0},
         "free": {"enable_turbulence": 1, "turbulence": 1.0, "turbulence_usecontrol": 0},
         # ctrl は既定のまま（Use Control Field の既定は「切り」だった）。明示的に入れた条件を足す
         "ctrl_on": {"enable_turbulence": 1, "turbulence": 1.0, "turbulence_usecontrol": 1}}


def run_one(name, rep):
    import hou
    import numpy as np
    spec = importlib.util.spec_from_file_location("e202", os.path.join(HERE, "examples", "202_pyro_campfire_cost.py"))
    e202 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e202)
    _, s0, _ = e202.build(0.1)      # 実験201 と同じく、先に粗い組み立てを 1 度作る
    hou.setFrame(3)
    s0.geometry()
    geo, solver, _ = e202.build(VOX)
    for k in ("flames_lifespan", "buoyancylift", "tempcooling", "enable_turbulence", "turbulence", "turbulence_usecontrol"):
        solver.parm(k).revertToDefaults()
    for k, v in {**FIRE, **CASES[name]}.items():
        solver.parm(k).set(v)
    turb_parms = {p.name(): (p.evalAsString() if p.parmTemplate().type().name() in ("String", "Menu") else p.eval())
                  for p in solver.parms() if "turbulence" in p.name() and p.parmTemplate().type().name() != "Ramp"}
    hs = []
    t0 = time.perf_counter()
    for f in range(1, FRAMES + 1):
        hou.setFrame(f)
        g = solver.geometry()
        hs.append(e202.measure(e202.field(g, "flame"), 0.1)["height"])
    rec = {"case": name, "rep": rep, "set": {**FIRE, **CASES[name]}, "turb_parms": turb_parms,
           "heights": hs, "height_mean": round(float(np.mean(hs[35:])), 4), "sec": round(time.perf_counter() - t0, 2)}
    if os.environ.get("SAVE"):
        import hou_tools
        geo.layoutChildren()
        hou_tools.save_hip(os.path.join(OUT, "220_scene.hipnc"))
        hou_tools.write_graph(geo.path(), os.path.join(OUT, "220_graph.json"), title="実験220")
    with open(os.path.join(OUT, f"220_part_{name}_{rep}.json"), "w", encoding="utf-8") as fp:
        json.dump(rec, fp, ensure_ascii=False)
    print(name, rep, rec["height_mean"], rec["sec"], hs[8:14], flush=True)


def combine():
    sys.path.insert(0, os.path.join(HERE, "examples"))
    import sop_bench
    rows = []
    for name in CASES:
        for rep in (1, 2):
            with open(os.path.join(OUT, f"220_part_{name}_{rep}.json"), encoding="utf-8") as fp:
                rows.append(json.load(fp))
    sop_bench.save(220, rows, {"voxel": VOX, "frames": FRAMES})


if __name__ == "__main__":
    if sys.argv[1] == "combine":
        combine()
    else:
        run_one(sys.argv[1], int(sys.argv[2]))
