"""for-each ループと VEX で同じことをやり、結果と速さを比べる。

「まとめて処理できないときは for-each」とよく言われるが、実際に VEX で書ける
場面でどれだけ差が出るのかは測ってみないと分からない。まったく同じ結果になる
2つの作り方を用意して、結果が一致することを確かめてから時間を比べる。
"""

import json
import os
import sys
import time

import hou

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hou_tools

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

geo = hou.node("/obj").createNode("geo", "foreach_vs_vex")


def make_grid(name, divisions):
    node = geo.createNode("grid", name)
    node.parm("sizex").set(10.0)
    node.parm("sizey").set(10.0)
    node.parm("rows").set(divisions)
    node.parm("cols").set(divisions)
    return node


def build_foreach(name, source):
    """プリミティブごとに1回ずつ処理する、教科書どおりの組み方。"""
    begin = geo.createNode("block_begin", f"{name}_begin")
    begin.parm("method").set("piece")        # 1個ずつ取り出す

    meta = geo.createNode("block_begin", f"{name}_meta")
    meta.parm("method").set("metadata")      # 何回目かを教えてくれるノード

    inner = geo.createNode("attribwrangle", f"{name}_inner")
    inner.setFirstInput(begin)
    # detail() のパスには op: が要る。付けないとファイルパスとして扱われ、
    # エラーも警告も出さずに 0 を返す。ループが動いていないように見える原因。
    # また、取り出した1個だけを見ているので @primnum は常に 0 になる。
    # 何回目かを知るにはメタデータノードを読むしかない。
    inner.parm("snippet").set(
        f'@P.y += detail("op:../{name}_meta", "iteration", 0) * 0.001;')

    end = geo.createNode("block_end", f"{name}_end")
    end.setFirstInput(inner)
    end.parm("itermethod").set("pieces")
    end.parm("class").set("primitive")
    end.parm("method").set("merge")
    end.parm("blockpath").set(f"../{name}_begin")
    # 何を何回繰り返すかは templatepath が指すノードから決まる。
    # これが空だと "Missing template geometry" で止まる。
    end.parm("templatepath").set(f"../{name}_begin")

    begin.parm("blockpath").set(f"../{name}_end")
    meta.parm("blockpath").set(f"../{name}_end")
    begin.setFirstInput(source)
    return end


def build_vex(name, source):
    """同じことを1回のVEXで書く。プリミティブごとに走らせ、その面の点を動かす。"""
    node = geo.createNode("attribwrangle", name)
    node.setFirstInput(source)
    node.parm("class").set("primitive")
    node.parm("snippet").set(
        "int pts[] = primpoints(0, @primnum);\n"
        "foreach (int pt; pts) {\n"
        "    vector p = point(0, \"P\", pt);\n"
        "    p.y += @primnum * 0.001;\n"
        "    setpointattrib(0, \"P\", pt, p);\n"
        "}")
    return node


def positions(node):
    return [tuple(round(v, 6) for v in p.position())
            for p in node.geometry().points()]


def prim_heights(node):
    """面ごとの「平面上の位置 → 高さ」の対応。

    for-each は面を1枚ずつ取り出して最後に合流させるので、隣り合う面が共有して
    いた点が複製され、面の並び順も変わる。そのため水平位置（x と z）を鍵にして
    対応を取り、比べたい量（y）だけを値にする。
    比べたい量をソートの鍵に含めてしまうと、対応がずれて必ず食い違う。"""
    out = {}
    for prim in node.geometry().prims():
        centroid = hou.Vector3(0, 0, 0)
        vertices = prim.vertices()
        for vertex in vertices:
            centroid += vertex.point().position()
        centroid /= len(vertices)
        out[(round(centroid[0], 4), round(centroid[2], 4))] = round(centroid[1], 6)
    return out


def time_fresh(builder, source, label, runs=3):
    """毎回新しいノードを作って初回のクックを測る（009で確立した方法）。

    同じノードを焼き直す方法では、キャッシュが効いて実際の計算が走らない。"""
    samples = []
    for run in range(runs):
        node = builder(f"{label}_{run}", source)
        start = time.perf_counter()
        node.geometry().boundingBox()
        samples.append((time.perf_counter() - start) * 1000.0)
        for victim in list(geo.children()):
            if victim.name().startswith(f"{label}_{run}"):
                victim.destroy()
    samples.sort()
    return samples[len(samples) // 2]


# --- まず小さい例で、2つの作り方が同じ結果になるか確かめる
check_grid = make_grid("check_grid", 8)
check_fe = build_foreach("check_fe", check_grid)
check_vex = build_vex("check_vex", check_grid)

prims = len(check_grid.geometry().prims())

for node in (check_fe, check_vex):
    if node.geometry() is None:
        print(f"== {node.name()} がジオメトリを返さない ==")
        for candidate in geo.children():
            errors = candidate.errors()
            warnings = candidate.warnings()
            if errors or warnings:
                print(f"  {candidate.name()} ({candidate.type().name()}):")
                for message in list(errors) + list(warnings):
                    print(f"    {message}")
        raise SystemExit("for-each の組み方が正しくない")

source_points = len(check_grid.geometry().points())
fe_points = len(check_fe.geometry().points())
vex_points = len(check_vex.geometry().points())
fe_heights = prim_heights(check_fe)
vex_heights = prim_heights(check_vex)
same = fe_heights == vex_heights

print("== 2つの作り方の結果を比べる ==")
print(f"  元のグリッド: {source_points}点 / {prims}面")
print(f"  for-each の出力: {fe_points}点 / "
      f"{len(check_fe.geometry().prims())}面")
print(f"  VEX の出力:     {vex_points}点 / "
      f"{len(check_vex.geometry().prims())}面")
print(f"  面ごとの中心が完全一致: {same}")
if not same:
    diff = [(key, fe_heights[key], vex_heights.get(key))
            for key in sorted(fe_heights) if fe_heights[key] != vex_heights.get(key)]
    print(f"  食い違った面の数: {len(diff)} / {len(fe_heights)}")
    for row in diff[:3]:
        print("    水平位置 %s: for-each %.4f / VEX %s" % row)

check_fe.setDisplayFlag(True)
hou_tools.render_preview(check_fe.path(), os.path.join(OUT, "010_result.png"),
                         res=(460, 330), direction=(0.9, 0.5, 1.0))

# --- 速さを比べる
print("\n== 同じ結果を出すのにかかる時間（3回の中央値）==")
print("%10s %12s %14s %14s %10s"
      % ("分割数", "プリミティブ", "for-each(ms)", "VEX(ms)", "何倍"))
rows = []
for divisions in (8, 16, 32, 64):
    grid = make_grid(f"grid_{divisions}", divisions)
    count = len(grid.geometry().prims())
    fe_ms = time_fresh(build_foreach, grid, f"t_fe_{divisions}")
    vex_ms = time_fresh(build_vex, grid, f"t_vex_{divisions}")
    ratio = fe_ms / vex_ms if vex_ms else float("nan")
    rows.append({"divisions": divisions, "prims": count,
                 "foreach_ms": round(fe_ms, 2), "vex_ms": round(vex_ms, 3),
                 "ratio": round(ratio, 1)})
    print("%10d %12d %14.2f %14.3f %9.1f倍"
          % (divisions, count, fe_ms, vex_ms, ratio))
    grid.destroy()

# --- なぜ一致しないのか。VEX 側は点を共有しているので、隣り合う面が
# 同じ点に書き込んで取り合いになっているのではないか。
print("\n== 検証1: VEX の結果は毎回同じか（共有された点のまま）==")
runs = []
for run in range(3):
    node = build_vex(f"race_{run}", check_grid)
    runs.append(prim_heights(node))
    node.destroy()
stable = all(r == runs[0] for r in runs[1:])
print(f"  3回とも同じ結果: {stable}")
if not stable:
    mismatches = sum(1 for key in runs[0] if runs[1].get(key) != runs[0][key])
    print(f"  1回目と2回目で食い違った面: {mismatches} / {len(runs[0])}")

# --- 点を共有しないようにすれば一致するはず
print("\n== 検証2: 点を共有しない形にしてから比べる ==")
unique = geo.createNode("facet", "make_unique")
unique.setFirstInput(check_grid)
unique.parm("unique").set(True)
print(f"  共有をほどいた後: {len(unique.geometry().points())}点 /"
      f" {len(unique.geometry().prims())}面")

u_fe = build_foreach("u_fe", unique)
u_vex = build_vex("u_vex", unique)
u_same = prim_heights(u_fe) == prim_heights(u_vex)
print(f"  for-each と VEX が一致: {u_same}")
if not u_same:
    a, b = prim_heights(u_fe), prim_heights(u_vex)
    diff = [(k, a[k], b.get(k)) for k in sorted(a) if a[k] != b.get(k)]
    print(f"  食い違った面: {len(diff)} / {len(a)}")
    for row in diff[:3]:
        print("    水平位置 %s: for-each %.4f / VEX %s" % row)

geo.layoutChildren()
graph = hou_tools.write_graph("/obj/foreach_vs_vex",
                              os.path.join(OUT, "010_graph.json"),
                              title="for-each と VEX の比較")
with open(os.path.join(OUT, "010_stats.json"), "w", encoding="utf-8") as fp:
    json.dump({"identical": same, "check_prims": prims,
               "vex_stable": stable, "unique_identical": u_same,
               "unique_points": len(unique.geometry().points()),
               "points": {"source": source_points, "foreach": fe_points,
                          "vex": vex_points},
               "timing": rows}, fp,
              ensure_ascii=False, indent=2)
hou_tools.save_hip(os.path.join(OUT, "010_foreach.hipnc"))
print(f"\nnodes: {len(graph['nodes'])}")
