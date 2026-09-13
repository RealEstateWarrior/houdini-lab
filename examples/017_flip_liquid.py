"""FLIP で液体を落とす。液体で保存されるべき量は何か。

剛体は体積、布は辺の長さ、煙は「供給と減衰の釣り合い」で説明できた。
液体は押し縮められないので、体積が保たれるはず。

FLIP は液体を粒で表す方式なので、粒1つが一定の体積を担うなら
「粒の数」がそのまま体積にあたる。ところが FLIP には reseeding という、
粒が偏ったときに足したり間引いたりする仕組みがある。これが入ると
粒の数は保たれないはず。両方試して確かめる。
"""

import json
import os
import sys
import time

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
FRAMES = list(range(1, 49, 3))
CHECK_FRAMES = (1, 5, 10, 20, 30, 46)
SEPARATION = 0.15

geo = hou.node("/obj").createNode("geo", "flip_test")

tank = geo.createNode("particlefluidtank", "liquid")
for parm, value in (("sizex", 2.0), ("sizey", 2.0), ("sizez", 2.0)):
    tank.parm(parm).set(value)
tank.parm("particlesep").set(SEPARATION)
# タンクを上に動かすと「水位より上」と判断されて中身が空になる。
# 落下させたいので、タンクは原点のままにして地面のほうを下げる。

start_geo = tank.geometry()
start_count = len(start_geo.points())
print("== 液体の初期状態 ==")
print(f"  {start_count}粒 / 粒の間隔 {SEPARATION}")
print(f"  1粒あたりの体積 {SEPARATION ** 3:.6f}")
print(f"  粒から見積もった体積 {start_count * SEPARATION ** 3:.5f}"
      f"（箱は 2×2×2 = 8.0）")


def build(name, reseeding):
    solver = geo.createNode("flipsolver", f"solve_{name}")
    solver.setFirstInput(tank)
    solver.parm("particlesep").set(SEPARATION)
    solver.parm("startframe").set(1)
    solver.parm("useground").set(True)
    if solver.parm("ground_posy") is not None:
        solver.parm("ground_posy").set(-3.0)
    if solver.parm("doreseeding") is not None:
        solver.parm("doreseeding").set(reseeding)
    return solver


probe = geo.createNode("flipsolver", "probe")
print("\n== ソルバの既定値 ==")
for name in ("doreseeding", "reseeding", "substeps", "particlesep", "useground"):
    parm = probe.parm(name)
    if parm is not None:
        print(f"  {name} = {parm.eval()!r}")
probe.destroy()

runs = []
for label, reseeding in (("再配置あり（既定）", True), ("再配置なし", False)):
    name = "on" if reseeding else "off"
    solver = build(name, reseeding)

    print(f"\n== {label} ==")
    print("%8s %10s %12s %14s %12s %10s"
          % ("フレーム", "粒の数", "最初との比", "見積もり体積", "最下点", "計算秒"))
    rows = []
    for frame in CHECK_FRAMES:
        started = time.perf_counter()
        hou.setFrame(frame)
        g = solver.geometry()
        elapsed = time.perf_counter() - started
        if g is None:
            print(f"{frame:8d}  ジオメトリが無い")
            continue
        count = len(g.points())
        volume = count * SEPARATION ** 3
        lowest = g.boundingBox().minvec()[1] if count else 0.0
        spread = max(g.boundingBox().sizevec()[0],
                     g.boundingBox().sizevec()[2]) if count else 0.0
        rows.append({"frame": frame, "count": count,
                     "ratio": round(count / start_count, 5),
                     "volume": round(volume, 5), "lowest": round(lowest, 4),
                     "spread": round(spread, 4), "seconds": round(elapsed, 2)})
        print("%8d %10d %12.5f %14.5f %12.4f %10.2f"
              % (frame, count, count / start_count, volume, lowest, elapsed))
    runs.append({"label": label, "reseeding": reseeding, "rows": rows,
                 "node": solver})
    hou.setFrame(1)

print("\n== 検証: 粒の数は保たれるか ==")
print("%-20s %12s %12s %12s" % ("条件", "最小", "最大", "振れ幅"))
for run in runs:
    if not run["rows"]:
        continue
    ratios = [r["ratio"] for r in run["rows"]]
    print("%-20s %12.5f %12.5f %12.5f"
          % (run["label"], min(ratios), max(ratios), max(ratios) - min(ratios)))

show = runs[0]["node"]
started = time.perf_counter()
paths = hou_tools.render_sequence(show.path(), OUT, "017_flip", FRAMES,
                                  res=(380, 320), direction=(1.0, 0.3, 1.15),
                                  shading="smooth")
render_seconds = time.perf_counter() - started
print(f"\n  {len(paths)}枚を {render_seconds:.1f}秒で書き出した")

hou.setFrame(1)
geo.layoutChildren()
graph = hou_tools.write_graph("/obj/flip_test",
                              os.path.join(OUT, "017_graph.json"),
                              title="FLIP 液体")
with open(os.path.join(OUT, "017_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"start_count": start_count, "separation": SEPARATION,
               "runs": [{"label": r["label"], "reseeding": r["reseeding"],
                         "rows": r["rows"]} for r in runs],
               "render_seconds": round(render_seconds, 1)},
              fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "017_flip.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
