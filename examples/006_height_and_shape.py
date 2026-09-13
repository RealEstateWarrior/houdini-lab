"""height は純粋な倍率なのか。gain / bias は何に効くのか。

005でセル系の最大のずれが 0.164〜0.175 に揃っていたので、何らかの上限が
効いている可能性を疑った。height を変えて比例するかどうかで確かめる。
あわせて未調査だった gain / bias / clipmin / clipmax も測る。
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
BASE_HEIGHT = 0.35

geo = hou.node("/obj").createNode("geo", "height_shape")
box = geo.createNode("box", "box1")
base = geo.createNode("subdivide", "base_subdiv")
base.setFirstInput(box)
base.parm("iterations").set(SUBDIV)

probe = geo.createNode("mountain", "probe")
print("== 上限に関係しそうなパラメータの既定値 ==")
for name in ("clipmin", "clipmax", "dogain", "gain", "dobias", "bias",
             "complement", "fold"):
    parm = probe.parm(name)
    print(f"  {name}: " + ("(なし)" if parm is None else repr(parm.eval())))
probe.destroy()


def edges_of(geometry):
    pairs = []
    for prim in geometry.prims():
        idx = [v.point().number() for v in prim.vertices()]
        for i in range(len(idx)):
            pairs.append((idx[i], idx[(i + 1) % len(idx)]))
    return pairs


EDGES = edges_of(base.geometry())
BASE_POS = [p.position() for p in base.geometry().points()]


def measure(node):
    a = [p.position() for p in node.geometry().points()]
    signed = [pa.length() - pb.length() for pa, pb in zip(a, BASE_POS)]
    absolute = [abs(v) for v in signed]
    return {
        "mean": sum(absolute) / len(absolute),
        "max": max(absolute),
        "variation": sum(abs(signed[i] - signed[j]) for i, j in EDGES) / len(EDGES),
        "outward": sum(1 for v in signed if v > 0) / len(signed),
    }


def make(name, basis="simplex", height=BASE_HEIGHT, **overrides):
    node = geo.createNode("mountain", name)
    node.setFirstInput(base)
    node.parm("height").set(height)
    node.parm("elementsize").set(ELEMENTSIZE)
    node.parm("basis").set(basis)
    for parm_name, value in overrides.items():
        node.parm(parm_name).set(value)
    return node


# --- 1. height を変えて比例するか
HEIGHTS = (0.0875, 0.175, 0.35, 0.7, 1.4)
print("\n== height を変えたときの最大のずれ ==")
print("%-10s %10s %10s %12s %10s %12s"
      % ("basis", "height", "平均", "最大", "最大/height", "細かさ"))
height_rows = []
for basis in ("simplex", "worleyFA"):
    for height in HEIGHTS:
        node = make(f"h_{basis}_{str(height).replace('.', '')}", basis, height)
        stats = measure(node)
        ratio = stats["max"] / height
        height_rows.append({"basis": basis, "height": height,
                            "mean": round(stats["mean"], 5),
                            "max": round(stats["max"], 5),
                            "ratio": round(ratio, 5),
                            "variation": round(stats["variation"], 5)})
        print("%-10s %10.4f %10.5f %12.5f %10.5f %12.5f"
              % (basis, height, stats["mean"], stats["max"], ratio,
                 stats["variation"]))
        if height != BASE_HEIGHT:
            node.destroy()

# --- 2. gain と bias
GAINS = (0.25, 0.5, 0.75)
BIASES = (0.25, 0.5, 0.75)
shape_rows = []
print("\n== gain（dogain を有効にして変化させる）==")
print("%-10s %10s %10s %10s %10s" % ("gain", "平均", "最大", "細かさ", "外向き率"))
for value in GAINS:
    node = make(f"gain_{str(value).replace('.', '')}", dogain=True, gain=value)
    stats = measure(node)
    shape_rows.append({"kind": "gain", "value": value,
                       "mean": round(stats["mean"], 5),
                       "max": round(stats["max"], 5),
                       "variation": round(stats["variation"], 5),
                       "outward": round(stats["outward"], 4),
                       "image": f"006_gain_{str(value).replace('.', '')}.png"})
    hou_tools.render_preview(
        node.path(),
        os.path.join(OUT, f"006_gain_{str(value).replace('.', '')}.png"),
        res=(400, 400))
    print("%-10.2f %10.5f %10.5f %10.5f %9.1f%%"
          % (value, stats["mean"], stats["max"], stats["variation"],
             stats["outward"] * 100))

print("\n== bias（dobias を有効にして変化させる）==")
print("%-10s %10s %10s %10s %10s" % ("bias", "平均", "最大", "細かさ", "外向き率"))
for value in BIASES:
    node = make(f"bias_{str(value).replace('.', '')}", dobias=True, bias=value)
    stats = measure(node)
    shape_rows.append({"kind": "bias", "value": value,
                       "mean": round(stats["mean"], 5),
                       "max": round(stats["max"], 5),
                       "variation": round(stats["variation"], 5),
                       "outward": round(stats["outward"], 4),
                       "image": f"006_bias_{str(value).replace('.', '')}.png"})
    hou_tools.render_preview(
        node.path(),
        os.path.join(OUT, f"006_bias_{str(value).replace('.', '')}.png"),
        res=(400, 400))
    print("%-10.2f %10.5f %10.5f %10.5f %9.1f%%"
          % (value, stats["mean"], stats["max"], stats["variation"],
             stats["outward"] * 100))

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/height_shape",
                              os.path.join(OUT, "006_graph.json"),
                              title="height の線形性と gain / bias の効果")
with open(os.path.join(OUT, "006_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"heights": height_rows, "shape": shape_rows}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "006_height_shape.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
