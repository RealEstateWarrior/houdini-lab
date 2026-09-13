"""mountain SOP の basis（ノイズの種類）14通りを並べる。

004で basis が14種類あることが分かった。見た目が大きく変わるはずなので、
同じ条件で全種類を描き出し、004で作った指標で性質を数値化する。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

SUBDIV = 4
ELEMENTSIZE = 0.25
HEIGHT = 0.35

geo = hou.node("/obj").createNode("geo", "noise_basis")
box = geo.createNode("box", "box1")
base = geo.createNode("subdivide", "base_subdiv")
base.setFirstInput(box)
base.parm("iterations").set(SUBDIV)

probe = geo.createNode("mountain", "probe")
basis_menu = list(zip(probe.parm("basis").menuItems(),
                      probe.parm("basis").menuLabels()))
default_basis = probe.parm("basis").eval()
probe.destroy()

print(f"== basis {len(basis_menu)} 種類（既定: {default_basis}）==")
for item, label in basis_menu:
    print(f"  {item:12s} {label}")


def _edges(geometry):
    pairs = []
    for prim in geometry.prims():
        indices = [v.point().number() for v in prim.vertices()]
        for i in range(len(indices)):
            pairs.append((indices[i], indices[(i + 1) % len(indices)]))
    return pairs


def measure(noisy, reference, edges):
    a = [p.position() for p in noisy.geometry().points()]
    b = [p.position() for p in reference.geometry().points()]
    signed = [pa.length() - pb.length() for pa, pb in zip(a, b)]
    absolute = [abs(v) for v in signed]
    return {
        "mean": sum(absolute) / len(absolute),
        "max": max(absolute),
        "variation": sum(abs(signed[i] - signed[j]) for i, j in edges) / len(edges),
        # 外に出た点と内にへこんだ点の割合。ノイズの偏りを見る
        "outward": sum(1 for v in signed if v > 0) / len(signed),
    }


edges = _edges(base.geometry())
hou_tools.render_preview(base.path(), os.path.join(OUT, "005_base.png"),
                         res=(360, 360))

results = []
for item, label in basis_menu:
    node = geo.createNode("mountain", f"basis_{item}")
    node.setFirstInput(base)
    node.parm("height").set(HEIGHT)
    node.parm("elementsize").set(ELEMENTSIZE)
    node.parm("basis").set(item)
    try:
        stats = measure(node, base, edges)
    except hou.Error as exc:
        print(f"  {item}: エラー {exc}")
        continue
    hou_tools.render_preview(node.path(), os.path.join(OUT, f"005_{item}.png"),
                            res=(360, 360))
    results.append({"basis": item, "label": label,
                    "mean": round(stats["mean"], 5),
                    "max": round(stats["max"], 5),
                    "variation": round(stats["variation"], 5),
                    "outward": round(stats["outward"], 4),
                    "image": f"005_{item}.png",
                    "default": item == default_basis})

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/noise_basis",
                              os.path.join(OUT, "005_graph.json"),
                              title="mountain の basis 14種類の比較")
with open(os.path.join(OUT, "005_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"default": default_basis, "results": results}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "005_noise_basis.hipnc"))

print(f"\n== 実測（subdivide {SUBDIV}回 / 1538点、height {HEIGHT}、"
      f"elementsize {ELEMENTSIZE} 固定）==")
print("%-14s %-28s %8s %8s %10s %8s"
      % ("basis", "表示名", "平均", "最大", "細かさ", "外向き率"))
for r in sorted(results, key=lambda x: x["variation"]):
    mark = " *" if r["default"] else "  "
    print("%-14s %-28s %8.5f %8.5f %10.5f %8.1f%%%s"
          % (r["basis"], r["label"], r["mean"], r["max"],
             r["variation"], r["outward"] * 100, mark))
print("\n* = 既定値")
