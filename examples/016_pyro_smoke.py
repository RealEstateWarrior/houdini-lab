"""Pyro で煙を出す。ボリュームで保存されるべき量は何か。

剛体は体積、布は辺の長さが保たれた。煙はボリューム（空間を格子で区切って
各マスに値を持たせたもの）なので、測るのは「密度の合計」になる。

ただし煙は消えていくのが普通で、その速さを決めるのが dissipation という
パラメータ。既定は 0.1。これを 0 にすれば密度は保たれ、大きくすれば
指数的に減るはず。減り方を測れば、パラメータの意味を数値で確かめられる。
"""

import json
import math
import os
import sys
import time

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
FRAMES = list(range(1, 49, 3))
CHECK_FRAMES = (1, 5, 10, 20, 30, 46)

geo = hou.node("/obj").createNode("geo", "pyro_test")

emitter = geo.createNode("sphere", "emitter")
emitter.parm("type").set(1)
emitter.parmTuple("rad").set((0.5, 0.5, 0.5))
emitter.parmTuple("t").set((0, 0.6, 0))

source = geo.createNode("pyrosource", "source")
source.setFirstInput(emitter)
source.parm("mode").set(2)               # Volume Scatter: 中を点で埋める
# 既定では P と pscale しか作られない。density を作るよう明示しないと、
# 次のラスタライズが「変換する属性が無い」として空を返す。
# ここの attributes は「作る属性の個数」で、中身は attribute1 で選ぶ。
# 同じ名前でも、次のノードの attributes は「名前を並べた文字列」で意味が違う。
source.parm("attributes").set(1)
source.parm("attribute1").set("density")

rasterize = geo.createNode("volumerasterizeattributes", "rasterize")
rasterize.setFirstInput(source)
rasterize.parm("attributes").set("density")
rasterize.parm("voxelsize").set(0.08)

print("== 発生源 ==")
src_geo = rasterize.geometry()
print(f"  {len(src_geo.points())}点 / {len(src_geo.prims())}プリミティブ")
print("  プリミティブの種類:",
      {p.type().name() for p in src_geo.prims()} if src_geo.prims() else "なし")
vol_names = [p.attribValue("name") for p in src_geo.prims()
             if src_geo.findPrimAttrib("name")]
print("  ボリュームの名前:", vol_names)


def total_density(geometry):
    """密度ボリュームの全マスの合計。煙の総量にあたる。"""
    if geometry is None:
        return None
    name_attrib = geometry.findPrimAttrib("name")
    for prim in geometry.prims():
        if not isinstance(prim, hou.Volume):
            continue
        if name_attrib and prim.attribValue("name") != "density":
            continue
        return sum(prim.allVoxels())
    return None


def build(name, dissipation):
    solver = geo.createNode("pyrosolver", f"solve_{name}")
    solver.setFirstInput(rasterize)
    solver.parm("divsize").set(0.15)
    solver.parm("startframe").set(1)
    if solver.parm("enable_dissipation") is not None:
        solver.parm("enable_dissipation").set(dissipation > 0)
    solver.parm("dissipation").set(dissipation)
    return solver


runs = []
for label, dissipation in (("散逸なし", 0.0), ("既定 0.1", 0.1), ("強め 0.3", 0.3)):
    name = f"d{str(dissipation).replace('.', '_')}"
    solver = build(name, dissipation)

    print(f"\n== {label}（dissipation = {dissipation}）==")
    print("%8s %16s %12s %12s %10s"
          % ("フレーム", "密度の合計", "最初との比", "高さ", "計算秒"))
    rows = []
    first_total = None
    for frame in CHECK_FRAMES:
        started = time.perf_counter()
        hou.setFrame(frame)
        g = solver.geometry()
        elapsed = time.perf_counter() - started
        total = total_density(g)
        if total is None:
            print(f"{frame:8d}  密度ボリュームが見つからない")
            continue
        if first_total is None:
            first_total = total or 1.0
        top = g.boundingBox().maxvec()[1]
        rows.append({"frame": frame, "total": round(total, 3),
                     "ratio": round(total / first_total, 5),
                     "top": round(top, 3), "seconds": round(elapsed, 2)})
        print("%8d %16.3f %12.5f %12.3f %10.2f"
              % (frame, total, total / first_total, top, elapsed))
    runs.append({"label": label, "dissipation": dissipation, "rows": rows,
                 "node": solver})
    hou.setFrame(1)

# --- 密度は減るどころか増えた。発生源が毎フレーム供給し続けるため。
# 供給が一定で、毎フレーム (1 - d) 倍に減衰するとすれば、
# t フレーム後の合計は (1 - (1-d)^t) / d 倍になるはず。これと突き合わせる。
print("\n== 検証: 供給と減衰の釣り合いの式と一致するか ==")
print("%-12s %8s %14s %14s %14s"
      % ("条件", "フレーム", "実測の比", "式の予測", "差"))
fit_rows = []
for run in runs:
    d = run["dissipation"]
    for row in run["rows"]:
        t = row["frame"]
        if d == 0:
            predicted = float(t)          # 減らないので毎フレーム積み上がるだけ
        else:
            predicted = (1.0 - (1.0 - d) ** t) / d
        fit_rows.append({"label": run["label"], "dissipation": d,
                         "frame": t, "measured": row["ratio"],
                         "predicted": round(predicted, 5),
                         "diff": round(row["ratio"] - predicted, 6)})
        print("%-12s %8d %14.5f %14.5f %14.6f"
              % (run["label"], t, row["ratio"], predicted,
                 row["ratio"] - predicted))

print("\n== 行き着く先（釣り合いの値）==")
print("%-12s %16s %16s" % ("条件", "最後の実測", "1 / dissipation"))
for run in runs:
    if not run["rows"] or not run["dissipation"]:
        continue
    print("%-12s %16.5f %16.5f"
          % (run["label"], run["rows"][-1]["ratio"], 1.0 / run["dissipation"]))

show = runs[1]["node"]
started = time.perf_counter()
paths = hou_tools.render_sequence(show.path(), OUT, "016_pyro", FRAMES,
                                  res=(360, 340), direction=(1.0, 0.3, 1.15),
                                  shading="smooth")
render_seconds = time.perf_counter() - started
print(f"\n  {len(paths)}枚を {render_seconds:.1f}秒で書き出した")

hou.setFrame(1)
geo.layoutChildren()
graph = hou_tools.write_graph("/obj/pyro_test",
                              os.path.join(OUT, "016_graph.json"),
                              title="Pyro 煙")
with open(os.path.join(OUT, "016_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"runs": [{"label": r["label"], "dissipation": r["dissipation"],
                         "rows": r["rows"]} for r in runs],
               "fit": fit_rows, "render_seconds": round(render_seconds, 1)},
              fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "016_pyro.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
