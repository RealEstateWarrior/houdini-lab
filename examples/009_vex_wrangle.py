"""attribute wrangle で VEX を書く。何が何回動くのかを数える。

VEX は「ノードを並べる代わりに数行書く」ための言語。ただし初心者が最初に
つまずくのは文法ではなく「このコードは何に対して何回走るのか」という点。
それを実測で確かめる。あわせて、予測を立ててから結果を測る形で正しさを検証する。
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

geo = hou.node("/obj").createNode("geo", "vex_intro")

probe = geo.createNode("attribwrangle", "probe")
class_parm = probe.parm("class")
class_menu = list(zip(class_parm.menuItems(), class_parm.menuLabels()))
print("== attribute wrangle の「実行対象」==")
print(f"  class の既定: {class_parm.eval()!r}")
for item, label in class_menu:
    print(f"    {item} = {label}")
probe.destroy()

grid = geo.createNode("grid", "grid")
grid.parm("sizex").set(10.0)
grid.parm("sizey").set(10.0)
grid.parm("rows").set(20)
grid.parm("cols").set(20)
base_geo = grid.geometry()
COUNTS = {
    "point": len(base_geo.points()),
    "prim": len(base_geo.prims()),
    "vertex": sum(len(p.vertices()) for p in base_geo.prims()),
    "detail": 1,
}
print(f"\n  grid: ポイント {COUNTS['point']} / プリミティブ {COUNTS['prim']} /"
      f" バーテックス {COUNTS['vertex']}")


def wrangle(name, snippet, run_over=None, parent=None):
    node = geo.createNode("attribwrangle", name)
    node.setFirstInput(parent or grid)
    node.parm("snippet").set(snippet)
    if run_over is not None:
        node.parm("class").set(run_over)
    return node


# --- 1. 実行対象を変えると、作られるアトリビュートの種類が変わるはず
print("\n== 同じコードを実行対象だけ変えて走らせる ==")
print("%-14s %-38s %s" % ("実行対象", "作られたアトリビュート", "要素数"))
class_rows = []
for item, label in class_menu:
    node = wrangle(f"cls_{item}", "@marker = 1.0;", run_over=item)
    g = node.geometry()
    found = []
    for kind, attribs in (("ディテール", g.globalAttribs()),
                          ("ポイント", g.pointAttribs()),
                          ("プリミティブ", g.primAttribs()),
                          ("バーテックス", g.vertexAttribs())):
        if any(a.name() == "marker" for a in attribs):
            found.append(kind)
    class_rows.append({"class": item, "label": label,
                       "created": found or ["（なし）"]})
    print("%-14s %-38s" % (label, " / ".join(found) or "（なし）"))
    node.destroy()

# --- 2. 予測を立ててから測る
# grid は 10×10 で原点中心なので x は -5 〜 +5。
# @P.y = sin(@P.x * 2) * 0.5 なら、y の範囲はちょうど -0.5 〜 +0.5 になるはず。
print("\n== 予測の検証: @P.y = sin(@P.x * 2.0) * 0.5 ==")
wave = wrangle("wave", "@P.y = sin(@P.x * 2.0) * 0.5;")
ys = [p.position()[1] for p in wave.geometry().points()]
print(f"  予測: y の範囲は -0.5 〜 +0.5")
print(f"  実測: {min(ys):+.6f} 〜 {max(ys):+.6f}")
xs = [p.position()[0] for p in wave.geometry().points()]
print(f"  （x の範囲は {min(xs):+.2f} 〜 {max(xs):+.2f}）")
wave_result = {"predicted": [-0.5, 0.5], "measured": [round(min(ys), 6),
                                                      round(max(ys), 6)]}
hou_tools.render_preview(wave.path(), os.path.join(OUT, "009_wave.png"),
                         res=(460, 330), direction=(0.9, 0.5, 1.0))

# --- 3. rand は毎回同じ結果になるのか
print("\n== rand(@ptnum) の性質 ==")
rand_a = wrangle("rand_a", "@P.y = rand(@ptnum) * 2.0;")
rand_b = wrangle("rand_b", "@P.y = rand(@ptnum) * 2.0;")
ys_a = [p.position()[1] for p in rand_a.geometry().points()]
ys_b = [p.position()[1] for p in rand_b.geometry().points()]
identical = all(abs(a - b) < 1e-9 for a, b in zip(ys_a, ys_b))
mean_a = sum(ys_a) / len(ys_a)
print(f"  同じコードを別ノードで2回: 完全一致 = {identical}")
print(f"  平均 {mean_a:.5f}（0〜2 の一様乱数なら理論値は 1.0）")
print(f"  範囲 {min(ys_a):.5f} 〜 {max(ys_a):.5f}")
rand_result = {"identical": identical, "mean": round(mean_a, 5),
               "min": round(min(ys_a), 5), "max": round(max(ys_a), 5)}
rand_a.destroy()
rand_b.destroy()

# --- 4. 点数を増やすと処理時間はどう伸びるか
print("\n== 点数と処理時間（5回測って中央値）==")
print("%10s %12s %12s %16s" % ("分割数", "点数", "中央値(ミリ秒)", "1秒あたりの点数"))
timing_rows = []
for divisions in (200, 400, 800, 1600):
    big_grid = geo.createNode("grid", f"big_{divisions}")
    big_grid.parm("sizex").set(10.0)
    big_grid.parm("sizey").set(10.0)
    big_grid.parm("rows").set(divisions)
    big_grid.parm("cols").set(divisions)
    # 同じノードを焼き直す方式は実際の計算を捉えられなかったので、
    # 毎回新しいノードを作って初回のクックを測る。
    points = len(big_grid.geometry().points())
    samples = []
    for run in range(5):
        node = wrangle(f"time_{divisions}_{run}",
                       "@P.y = sin(@P.x * 2.0) * cos(@P.z * 2.0) * 0.5;",
                       parent=big_grid)
        start = time.perf_counter()
        node.geometry().boundingBox()
        samples.append((time.perf_counter() - start) * 1000.0)
        node.destroy()
    samples.sort()
    elapsed = samples[len(samples) // 2]

    per_second = points / (elapsed / 1000.0)
    timing_rows.append({"divisions": divisions, "points": points,
                        "ms": round(elapsed, 3),
                        "points_per_second": round(per_second)})
    print("%10d %12d %12.3f %16s"
          % (divisions, points, elapsed, f"{per_second:,.0f}"))
    big_grid.destroy()

# --- 5. その計測は本物か。同じ点数で計算量だけを増やして比例するか見る
print("\n== 計測の妥当性: 同じ点数で計算量を増やす（64万点）==")
heavy_grid = geo.createNode("grid", "heavy_grid")
heavy_grid.parm("sizex").set(10.0)
heavy_grid.parm("sizey").set(10.0)
heavy_grid.parm("rows").set(800)
heavy_grid.parm("cols").set(800)

SNIPPETS = (
    ("軽い（1回）", "@P.y = sin(@P.x * 2.0) * cos(@P.z * 2.0) * 0.5;"),
    ("重い（100回の繰り返し）",
     "float s = 0;\n"
     "for (int i = 1; i <= 100; i++) { s += sin(@P.x * i) * cos(@P.z * i); }\n"
     "@P.y = s * 0.005;"),
)
def measure_with_perfmon(node, label):
    """Houdini の性能計測機能で、実際のクック時間を取る。

    time.perf_counter で cook() を挟む方法は、計測区間の中で実際の計算が
    走っていないため使えなかった（計算量を100倍にしても時間が変わらなかった）。"""
    profile = hou.perfMon.startProfile(f"prof_{label}")
    node.cook(force=True)
    node.geometry().boundingBox()
    profile.stop()

    csv_path = os.path.join(OUT, f"009_perf_{label}.csv")
    profile.exportAsCSV(csv_path)

    total = 0.0
    with open(csv_path, encoding="utf-8", errors="replace") as fp:
        header = fp.readline().strip().split(",")
        try:
            time_column = next(i for i, name in enumerate(header)
                               if "time" in name.lower())
        except StopIteration:
            return None, header
        for line in fp:
            cells = line.rstrip("\n").split(",")
            if len(cells) <= time_column or node.name() not in line:
                continue
            try:
                total += float(cells[time_column])
            except ValueError:
                continue
    return total, header


# 同じノードを cook(force=True) で焼き直す方法では、実際の計算が走らなかった
# （計算量を100倍にしても時間が変わらない）。毎回新しいノードを作れば、
# キャッシュが存在しないので初回のジオメトリ要求で必ず計算される。
print("%-26s %14s %12s %14s"
      % ("処理", "中央値(ミリ秒)", "軽いものとの比", "結果の最大y"))
weight_rows = []
light_ms = None
for index, (label, snippet) in enumerate(SNIPPETS):
    samples = []
    peak = None
    for run in range(5):
        node = wrangle(f"w_{index}_{run}", snippet, parent=heavy_grid)
        start = time.perf_counter()
        bbox = node.geometry().boundingBox()
        samples.append((time.perf_counter() - start) * 1000.0)
        peak = bbox.maxvec()[1]
        node.destroy()
    samples.sort()
    median = samples[len(samples) // 2]
    if light_ms is None:
        light_ms = median
    weight_rows.append({"label": label, "ms": round(median, 2),
                        "ratio": round(median / light_ms, 1),
                        "peak_y": round(peak, 5)})
    print("%-26s %14.2f %11.1f倍 %14.5f"
          % (label, median, median / light_ms, peak))
heavy_grid.destroy()

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/vex_intro",
                              os.path.join(OUT, "009_graph.json"),
                              title="attribute wrangle で VEX を書く")
with open(os.path.join(OUT, "009_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"classes": class_rows, "counts": COUNTS, "wave": wave_result,
               "rand": rand_result, "timing": timing_rows,
               "weight": weight_rows}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "009_vex.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
