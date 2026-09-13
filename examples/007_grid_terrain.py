"""平面（grid）で地形を作り、指標を作り直す。

これまでの指標は「中心からの距離の差」で、球体でしか使えず、点数をまたいだ
比較もできなかった。平面なら高さの差をそのまま測れるうえ、点の間隔で割れば
勾配（傾き）になる。勾配は点数によらない量なので、解像度をまたいで比較できる。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

SIZE = 10.0
ELEMENTSIZE = 2.0
HEIGHT = 1.0

geo = hou.node("/obj").createNode("geo", "grid_terrain")

probe = geo.createNode("grid", "probe")
print("== grid SOP の既定値 ==")
for name in ("sizex", "sizey", "rows", "cols", "orient", "type"):
    parm = probe.parm(name)
    if parm is None:
        print(f"  {name}: (なし)")
        continue
    try:
        menu = dict(zip(parm.menuItems(), parm.menuLabels()))
    except hou.OperationFailed:
        menu = None
    print(f"  {name}: {parm.eval()!r}" + (f" menu={menu}" if menu else ""))
probe.destroy()


def make_grid(name, divisions):
    node = geo.createNode("grid", name)
    node.parm("sizex").set(SIZE)
    node.parm("sizey").set(SIZE)
    node.parm("rows").set(divisions)
    node.parm("cols").set(divisions)
    return node


def make_mountain(name, parent, **overrides):
    node = geo.createNode("mountain", name)
    node.setFirstInput(parent)
    node.parm("height").set(HEIGHT)
    node.parm("elementsize").set(ELEMENTSIZE)
    for parm_name, value in overrides.items():
        node.parm(parm_name).set(value)
    return node


def analyse(noisy, flat):
    """高さの差をそのまま測る。辺の長さで割ると勾配になり、点数によらない量になる。"""
    a = [p.position() for p in noisy.geometry().points()]
    b = [p.position() for p in flat.geometry().points()]
    dy = [pa[1] - pb[1] for pa, pb in zip(a, b)]

    slopes = []
    for prim in flat.geometry().prims():
        idx = [v.point().number() for v in prim.vertices()]
        for i in range(len(idx)):
            j = idx[(i + 1) % len(idx)]
            k = idx[i]
            length = (b[k] - b[j]).length()
            if length > 1e-9:
                slopes.append(abs(dy[k] - dy[j]) / length)

    absolute = [abs(v) for v in dy]
    return {
        "points": len(dy),
        "mean": sum(absolute) / len(absolute),
        "max": max(absolute),
        "slope": sum(slopes) / len(slopes),
        "upward": sum(1 for v in dy if v > 0) / len(dy),
        "spacing": SIZE / (len(flat.geometry().prims()) ** 0.5),
    }


# --- 1. 解像度を変えて、勾配が点数によらない量になっているかを確かめる
DIVISIONS = (20, 40, 80, 160)
print("\n== 解像度を変える（elementsize %.1f 固定）==" % ELEMENTSIZE)
print("%8s %8s %10s %10s %10s %10s"
      % ("分割数", "点数", "点の間隔", "平均の高さ", "最大", "平均勾配"))
resolution_rows = []
grids = {}
for divisions in DIVISIONS:
    flat = make_grid(f"grid_{divisions}", divisions)
    noisy = make_mountain(f"mt_{divisions}", flat)
    grids[divisions] = (flat, noisy)
    stats = analyse(noisy, flat)
    resolution_rows.append({"divisions": divisions, **{
        k: round(v, 5) for k, v in stats.items() if k != "points"}},)
    resolution_rows[-1]["points"] = stats["points"]
    print("%8d %8d %10.4f %10.5f %10.5f %10.5f"
          % (divisions, stats["points"], stats["spacing"],
             stats["mean"], stats["max"], stats["slope"]))

# --- 2. oct を変える。004では点数が足りず 3 以上で効かなかった。
# 勾配で測れば、解像度の影響を除いて比較できるはず。
print("\n== oct を変える（勾配で比較）==")
print("%8s %8s %8s %8s %8s" % ("分割数", "oct=1", "oct=2", "oct=4", "oct=8"))
oct_rows = []
for divisions in DIVISIONS:
    flat = grids[divisions][0]
    values = []
    for octaves in (1, 2, 4, 8):
        node = make_mountain(f"oct_{divisions}_{octaves}", flat, oct=octaves)
        values.append(analyse(node, flat)["slope"])
        node.destroy()
    oct_rows.append({"divisions": divisions,
                     "slopes": [round(v, 5) for v in values]})
    print("%8d %8.5f %8.5f %8.5f %8.5f" % (divisions, *values))

# --- 3. 地形としての見た目。fractal の4種類を平面で比べる
FRACTALS = ("none", "fBm", "mfT", "hmfT")
flat = grids[80][0]
fractal_rows = []
print("\n== fractal の4種類（分割数80）==")
print("%-10s %10s %10s %10s %10s" % ("fractal", "平均の高さ", "最大", "平均勾配", "上向き率"))
labels = dict(zip(probe_items := ("none", "fBm", "mfT", "hmfT"),
                  ("None", "Standard (fBm)", "Terrain", "Hybrid Terrain")))
for mode in FRACTALS:
    node = make_mountain(f"frac_{mode}", flat, fractal=mode)
    stats = analyse(node, flat)
    fractal_rows.append({"fractal": mode, "label": labels[mode],
                         "mean": round(stats["mean"], 5),
                         "max": round(stats["max"], 5),
                         "slope": round(stats["slope"], 5),
                         "upward": round(stats["upward"], 4),
                         "image": f"007_frac_{mode}.png"})
    hou_tools.render_preview(node.path(), os.path.join(OUT, f"007_frac_{mode}.png"),
                             res=(460, 330), direction=(0.9, 0.45, 1.0))
    print("%-10s %10.5f %10.5f %10.5f %9.1f%%"
          % (labels[mode], stats["mean"], stats["max"], stats["slope"],
             stats["upward"] * 100))

hou_tools.render_preview(flat.path(), os.path.join(OUT, "007_flat.png"),
                         res=(460, 330), direction=(0.9, 0.45, 1.0))

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/grid_terrain",
                              os.path.join(OUT, "007_graph.json"),
                              title="grid で地形を作り、勾配で測る")
with open(os.path.join(OUT, "007_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"resolution": resolution_rows, "oct": oct_rows,
               "fractal": fractal_rows}, fp, ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "007_grid_terrain.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
