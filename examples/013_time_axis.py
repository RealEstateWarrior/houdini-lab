"""時間軸への対応。フレームを進めながら記録する仕組みを作る。

ここまでの実験はすべて1フレームだけを見ていた。エフェクトは時間変化そのものが
結果なので、フレームを進めて連番で書き出し、1枚のコンタクトシートとGIFに
まとめる仕組みが要る。

仕組みが正しく動くかは、答えが分かっている動き（自由落下の式）を使って確かめる。
あわせて、この先のシミュレーションで使うノードがどこにあるのかも調べた。
"""

import json
import os
import sys
import time

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
FRAMES = list(range(1, 61, 3))
GRAVITY = 9.8
START_HEIGHT = 20.0
FPS = 24.0

geo = hou.node("/obj").createNode("geo", "time_axis")

# --- 1. 動きのある形を作る
grid = geo.createNode("grid", "wave_grid")
grid.parm("sizex").set(10.0)
grid.parm("sizey").set(10.0)
grid.parm("rows").set(40)
grid.parm("cols").set(40)

wave = geo.createNode("attribwrangle", "wave")
wave.setFirstInput(grid)
wave.parm("snippet").set(
    "@P.y = sin(@P.x * 0.8 + @Frame * 0.2) * cos(@P.z * 0.8) * 1.5;")

print("== 検証1: フレームごとに結果が変わるか ==")
wave_rows = []
for frame in (1, 10, 20, 30):
    hou.setFrame(frame)
    box = wave.geometry().boundingBox()
    wave_rows.append({"frame": frame, "max_y": round(box.maxvec()[1], 5)})
    print(f"  フレーム {frame:3d}: 最大の高さ {box.maxvec()[1]:.5f}")
hou.setFrame(1)

# --- 2. 答えが分かっている動きで、書き出しの仕組みを検証する
point = geo.createNode("add", "falling_point")
point.parm("points").set(1)

fall = geo.createNode("attribwrangle", "free_fall")
fall.setFirstInput(point)
fall.parm("snippet").set(
    f"float t = (@Frame - 1) / {FPS};\n"
    f"@P.y = {START_HEIGHT} - 0.5 * {GRAVITY} * t * t;")

print("\n== 検証2: 自由落下の式と一致するか ==")
print("%8s %10s %14s %14s %12s"
      % ("フレーム", "経過秒", "測った高さ", "理論値", "差"))
fall_rows = []
for frame in (1, 10, 20, 30, 40):
    hou.setFrame(frame)
    measured = fall.geometry().points()[0].position()[1]
    seconds = (frame - 1) / FPS
    ideal = START_HEIGHT - 0.5 * GRAVITY * seconds * seconds
    fall_rows.append({"frame": frame, "seconds": round(seconds, 4),
                      "measured": round(measured, 5), "ideal": round(ideal, 5),
                      "diff": round(measured - ideal, 7)})
    print("%8d %10.4f %14.5f %14.5f %12.7f"
          % (frame, seconds, measured, ideal, measured - ideal))
hou.setFrame(1)

# --- 3. 連番の書き出しと、かかる時間
print("\n== 連番の書き出し ==")
started = time.perf_counter()
paths = hou_tools.render_sequence(wave.path(), OUT, "013_wave", FRAMES,
                                  res=(360, 260), direction=(0.9, 0.5, 1.0))
elapsed = time.perf_counter() - started
print(f"  {len(paths)} 枚を {elapsed:.2f} 秒で書き出した"
      f"（1枚あたり {elapsed / len(paths) * 1000:.0f} ミリ秒）")

# --- 4. カメラを固定しないとどうなるか
print("\n== 検証3: カメラを固定する意味 ==")
box_all = hou_tools.bbox_over_frames(wave.path(), FRAMES)
print(f"  全フレームを覆う範囲: 高さ {box_all.sizevec()[1]:.5f}")
hou.setFrame(1)
box_one = hou.node(wave.path()).geometry().boundingBox()
print(f"  1フレーム目だけの範囲: 高さ {box_one.sizevec()[1]:.5f}")
print(f"  差: {box_all.sizevec()[1] - box_one.sizevec()[1]:.5f}")

# --- 5. この先のシミュレーションで使うノードはどこにあるか
print("\n== シミュレーション関連ノードの所在 ==")
sop_types = set(hou.sopNodeTypeCategory().nodeTypes())
dop_types = set(hou.dopNodeTypeCategory().nodeTypes())
landscape = []
for label, keyword in (("パーティクル", "pop"), ("剛体", "rbd"),
                       ("布", "vellum"), ("煙・炎", "pyro"), ("液体", "flip")):
    in_sop = sorted(t for t in sop_types if keyword in t.lower())
    in_dop = sorted(t for t in dop_types if keyword in t.lower())
    landscape.append({"label": label, "keyword": keyword,
                      "sop": len(in_sop), "dop": len(in_dop),
                      "sop_examples": in_sop[:3], "dop_examples": in_dop[:3]})
    print(f"  {label:8s}（{keyword}）: SOP {len(in_sop):3d}種 / DOP {len(in_dop):3d}種")

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/time_axis",
                              os.path.join(OUT, "013_graph.json"),
                              title="時間軸への対応")
with open(os.path.join(OUT, "013_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"wave": wave_rows, "fall": fall_rows, "frames": len(paths),
               "render_seconds": round(elapsed, 2),
               "bbox_all": round(box_all.sizevec()[1], 5),
               "bbox_one": round(box_one.sizevec()[1], 5),
               "landscape": landscape}, fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "013_time.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
