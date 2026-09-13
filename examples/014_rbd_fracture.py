"""最初の本物のシミュレーション。箱を砕いて落とす。

実験013で、剛体（RBD）は SOP レベルのノードが47種あり、パーティクルより
入口が易しいと分かった。012 で boolean の Shatter が体積を保つことも測った。

シミュレーションが正しく動いているかは「体積が保たれているか」で検証できる。
剛体は変形しないので、砕けても落ちても、全部の破片の体積の合計は変わらないはず。
"""

import json
import os
import sys
import time

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
FRAMES = list(range(1, 49, 3))          # 1〜46 を3コマおき、16枚
DROP_HEIGHT = 4.0

geo = hou.node("/obj").createNode("geo", "rbd_test")

box = geo.createNode("box", "block")
box.parm("scale").set(2.0)
box.parmTuple("t").set((0, DROP_HEIGHT, 0))

fracture = geo.createNode("rbdmaterialfracture", "fracture")
fracture.setFirstInput(box)
fracture.parm("materialtype").set("concrete")

fractured = fracture.geometry()
print("== 砕いた結果 ==")
print(f"  {len(fractured.points())}点 / {len(fractured.prims())}面")
names = [a.name() for a in fractured.primAttribs()]
print(f"  プリミティブ属性: {', '.join(names)}")
if "name" in names:
    pieces = {p.attribValue("name") for p in fractured.prims()}
    print(f"  破片の数: {len(pieces)}")

solver = geo.createNode("rbdbulletsolver", "solver")
solver.setFirstInput(fracture)
solver.parm("useground").set(True)
solver.parm("startframe").set(1)
print("\n== ソルバの設定 ==")
for name in ("startframe", "substeps", "useground", "cacheenabled"):
    parm = solver.parm(name)
    if parm is not None:
        print(f"  {name} = {parm.eval()!r}")

unpack = geo.createNode("unpack", "unpack")
unpack.setFirstInput(solver)


def volume_of(geometry):
    return sum(p.intrinsicValue("measuredvolume") for p in geometry.prims())


print("\n== フレームごとの状態 ==")
print("%8s %14s %12s %12s %12s %10s"
      % ("フレーム", "体積の合計", "最下点", "横の広がり", "高さ", "計算秒"))
rows = []
for frame in (1, 4, 10, 20, 30, 46):
    started = time.perf_counter()
    hou.setFrame(frame)
    g = unpack.geometry()
    elapsed = time.perf_counter() - started
    if g is None or not len(g.points()):
        print(f"{frame:8d}  ジオメトリが無い")
        continue
    volume = volume_of(g)
    box_now = g.boundingBox()
    lowest = box_now.minvec()[1]
    spread = max(box_now.sizevec()[0], box_now.sizevec()[2])
    height = box_now.sizevec()[1]
    rows.append({"frame": frame, "points": len(g.points()),
                 "volume": round(volume, 5), "lowest": round(lowest, 4),
                 "spread": round(spread, 4), "height": round(height, 4),
                 "seconds": round(elapsed, 2)})
    print("%8d %14.5f %12.4f %12.4f %12.4f %10.2f"
          % (frame, volume, lowest, spread, height, elapsed))

hou.setFrame(1)
print("\n== 検証: 体積は保たれているか ==")
if rows:
    volumes = [r["volume"] for r in rows]
    first, last = volumes[0], volumes[-1]
    spread = max(volumes) - min(volumes)
    print(f"  最初 {first:.5f} / 最後 {last:.5f}")
    print(f"  全フレームでの振れ幅 {spread:.7f}"
          f"（{spread / first * 100:.4f}%）")
    print(f"  元の箱（2×2×2）の体積は 8.0 なので、砕いた合計との差は"
          f" {abs(first - 8.0):.5f}")

started = time.perf_counter()
paths = hou_tools.render_sequence(unpack.path(), OUT, "014_rbd", FRAMES,
                                  res=(400, 340), direction=(1.0, 0.28, 1.15))
render_seconds = time.perf_counter() - started
print(f"\n  {len(paths)}枚を {render_seconds:.1f}秒で書き出した")

hou.setFrame(1)
geo.layoutChildren()
graph = hou_tools.write_graph("/obj/rbd_test",
                              os.path.join(OUT, "014_graph.json"),
                              title="RBD 破壊")
with open(os.path.join(OUT, "014_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"fracture_points": len(fractured.points()),
               "fracture_prims": len(fractured.prims()),
               "frames": rows, "render_seconds": round(render_seconds, 1)},
              fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "014_rbd.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
