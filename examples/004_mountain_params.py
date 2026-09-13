"""mountain SOP のノイズパラメータは何に効くのか。

実験003で「点数は解像度、elementsize は振幅」と分かった。では残りのパラメータは
どちらに効くのか。003と同じ「基準形との点ごとの差」で分離する。

注意: パラメータ名は roughness / octaves ではなく rough / oct / lac。
実際に mountain::2.0 が持っている名前を確認してから使っている。
"""

import json
import os
import sys

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

SUBDIV = 4          # 1538点。003で「この特徴サイズならこれくらい要る」と分かった水準
ELEMENTSIZE = 0.25
HEIGHT = 0.35

geo = hou.node("/obj").createNode("geo", "mountain_params")
box = geo.createNode("box", "box1")

base = geo.createNode("subdivide", "base_subdiv")
base.setFirstInput(box)
base.parm("iterations").set(SUBDIV)

# mountain::2.0 が実際に持っているパラメータを確認する
probe = geo.createNode("mountain", "probe")
print("== mountain SOP のノイズ関連パラメータ ==")
defaults = {}
for name in ("height", "elementsize", "rough", "oct", "lac", "fractal", "basis",
             "gain", "bias", "pulselength"):
    parm = probe.parm(name)
    if parm is None:
        print(f"  {name}: (なし)")
        continue
    defaults[name] = parm.eval()
    try:
        items = parm.menuItems()
        labels = parm.menuLabels()
        menu = dict(zip(items, labels))
    except hou.OperationFailed:
        menu = None
    print(f"  {name}: default={defaults[name]!r}"
          + (f" menu={menu}" if menu else ""))
probe.destroy()

FRACTAL_MODES = ("hmfT", "fBm", "mfT", "none")


def make(name, **overrides):
    node = geo.createNode("mountain", name)
    node.setFirstInput(base)
    node.parm("height").set(HEIGHT)
    node.parm("elementsize").set(ELEMENTSIZE)
    for parm_name, value in overrides.items():
        parm = node.parm(parm_name)
        if parm is None:
            raise ValueError(f"mountain に {parm_name} がない")
        parm.set(value)
    return node


def _edges(geometry):
    """基準形の辺リスト。隣り合う点の組を作るために使う。"""
    pairs = []
    for prim in geometry.prims():
        indices = [v.point().number() for v in prim.vertices()]
        for i in range(len(indices)):
            pairs.append((indices[i], indices[(i + 1) % len(indices)]))
    return pairs


def measure(noisy, reference, edges):
    """振幅と細かさを別々に測る。

    - 振幅: 基準形からのずれの大きさ（平均・最大）
    - 細かさ: 隣り合う点どうしで、ずれの向きと量がどれだけ食い違うか。
      なめらかな起伏なら隣の点も同じように動くので小さく、細かい凹凸なら大きくなる。
    基準形は原点中心なので、中心からの距離の差を符号付きのずれとして使う
    （外に出たら正、内にへこんだら負）。"""
    a = [p.position() for p in noisy.geometry().points()]
    b = [p.position() for p in reference.geometry().points()]
    signed = [pa.length() - pb.length() for pa, pb in zip(a, b)]
    absolute = [abs(v) for v in signed]

    variation = sum(abs(signed[i] - signed[j]) for i, j in edges) / len(edges)
    return {
        "mean": sum(absolute) / len(absolute),
        "max": max(absolute),
        "variation": variation,
    }


groups = []

groups.append(("rough", "rough（粗さ）", [
    (f"rough_{str(v).replace('.', '')}", f"rough = {v}",
     make(f"rough_{str(v).replace('.', '')}", rough=v, oct=defaults["oct"]))
    for v in (0.0, 0.5, 1.0)
]))

groups.append(("oct", "oct（オクターブ数）", [
    (f"oct_{v}", f"oct = {v}",
     make(f"oct_{v}", oct=v, rough=defaults["rough"]))
    for v in (1, 3, 8)
]))

groups.append(("lac", "lac（ラキュナリティ）", [
    (f"lac_{str(v).replace('.', '')}", f"lac = {v}",
     make(f"lac_{str(v).replace('.', '')}", lac=v))
    for v in (1.5, 2.0, 4.0)
]))

fractal_menu = {}
probe2 = geo.createNode("mountain", "probe2")
fractal_menu = dict(zip(probe2.parm("fractal").menuItems(),
                        probe2.parm("fractal").menuLabels()))
probe2.destroy()

groups.append(("fractal", "fractal（フラクタルの種類）", [
    (f"fractal_{mode}", f"{fractal_menu.get(mode, mode)}",
     make(f"fractal_{mode}", fractal=mode))
    for mode in FRACTAL_MODES
]))

all_nodes = [node for _, _, items in groups for _, _, node in items]
all_nodes[0].setDisplayFlag(True)
geo.layoutChildren()

bbox = hou_tools.bbox_union([n.path() for n in all_nodes] + [base.path()])
hou_tools.render_preview(base.path(), os.path.join(OUT, "004_base.png"),
                         res=(420, 420), frame_bbox=bbox)

edges = _edges(base.geometry())

report = []
for group_id, group_label, items in groups:
    rows = []
    for key, label, node in items:
        stats = measure(node, base, edges)
        hou_tools.render_preview(node.path(), os.path.join(OUT, f"004_{key}.png"),
                                 res=(420, 420), frame_bbox=bbox)
        rows.append({"key": key, "label": label,
                     "mean": round(stats["mean"], 5),
                     "max": round(stats["max"], 5),
                     "variation": round(stats["variation"], 5)})
    report.append({"id": group_id, "label": group_label, "rows": rows})

graph = hou_tools.write_graph(
    "/obj/mountain_params",
    os.path.join(OUT, "004_graph.json"),
    title="mountain のノイズパラメータの切り分け",
)
with open(os.path.join(OUT, "004_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"defaults": defaults, "groups": report}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "004_mountain_params.hipnc"))

print(f"\n== 固定条件 ==")
print(f"  subdivide {SUBDIV}回（{len(base.geometry().points())}点）"
      f" / height {HEIGHT} / elementsize {ELEMENTSIZE}")

print(f"  辺の数 {len(edges)}")

for group in report:
    print(f"\n== {group['label']} ==")
    print("%-24s %10s %10s %12s" % ("", "平均ずれ", "最大ずれ", "隣との食い違い"))
    for row in group["rows"]:
        print("%-24s %10.5f %10.5f %12.5f"
              % (row["label"], row["mean"], row["max"], row["variation"]))
print(f"\nnodes: {len(graph['nodes'])}")

# --- 予測の検証: oct が 3 以上で効かなくなるのは、点数が足りず細かいオクターブを
# 表現できていないためか。もしそうなら、点数を増やせば oct=8 が oct=3 を上回るはず。
print("\n== 予測の検証: 点数を変えて oct の効き方を見る ==")
print("%-12s %8s %12s %12s %12s"
      % ("subdivide", "点数", "oct=1", "oct=3", "oct=8"))
for iterations in (3, 4, 5):
    reference = geo.createNode("subdivide", f"pred_base_{iterations}")
    reference.setFirstInput(box)
    reference.parm("iterations").set(iterations)
    ref_geo = reference.geometry()
    ref_edges = _edges(ref_geo)

    values = []
    for octaves in (1, 3, 8):
        node = geo.createNode("mountain", f"pred_{iterations}_{octaves}")
        node.setFirstInput(reference)
        node.parm("height").set(HEIGHT)
        node.parm("elementsize").set(ELEMENTSIZE)
        node.parm("oct").set(octaves)
        node.parm("rough").set(defaults["rough"])
        values.append(measure(node, reference, ref_edges)["variation"])
        node.destroy()

    print("%-12d %8d %12.5f %12.5f %12.5f"
          % (iterations, len(ref_geo.points()), values[0], values[1], values[2]))
    reference.destroy()
