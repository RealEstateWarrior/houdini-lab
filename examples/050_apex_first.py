"""実験050 — APEX に入る。いちばん小さいグラフを組んで動かす。

APEX は Houdini 20 から入ったリグ（骨組み）の仕組みで、
<strong>ノードのネットワークそのものをデータとして持ち歩ける</strong>のが特徴。
SOP のネットワークのようにシーンの中に置かれるのではなく、
ジオメトリの中に入って流れていく。

新しい分野なので、まず大きさを測るところから始める。

  A. APEX で使える部品は何種類あるか
  B. いちばん小さいグラフ（3 + 4）を組んで、7 が出るか
  C. グラフの実行はどれくらい速いか
  D. SOP 側から触れる APEX / KineFX のノードは何種類か

    hython examples/050_apex_first.py
"""

import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import apex  # noqa: E402
import hou  # noqa: E402

RUNS = 10000


def count_parts():
    reg = apex.Registry()
    names = list(reg.findMatchingNames("*"))
    groups = collections.Counter(
        n.split("::")[0] for n in names if "::" in n)
    plain = [n for n in names if "::" not in n]
    return names, groups, plain


def add_graph(values):
    """Value ノードを並べて Add につなぐ。values の数だけ枝を生やす。"""
    g = apex.Graph()
    add = g.addNode("add", "Add<Float>")
    port_a, port_b = g.getInputPorts(add)

    first = g.addNode("v0", "Value<Float>")
    g.setNodeParm(first, "parm", values[0])
    g.addWire(g.getOutputPorts(first)[0], port_a)

    for i, value in enumerate(values[1:], start=1):
        node = g.addNode(f"v{i}", "Value<Float>")
        g.setNodeParm(node, "parm", value)
        # 2つ目の入力は可変長。枝（サブポート）を生やしてからつなぐ
        sub = g.addSubPort(port_b, f"b{i}")
        g.addWire(g.getOutputPorts(node)[0], sub)

    g.addGraphOutput(add, "result")
    return g, add, port_a, port_b


def main():
    stats = {}

    print("A. APEX で使える部品を数える")
    names, groups, plain = count_parts()
    print(f"   部品の総数: {len(names):,}")
    print(f"   名前空間の付いていないもの（算数・比較など）: {len(plain):,}")
    print(f"   {'名前空間':<14} {'数':>6}")
    rows = []
    for key, value in groups.most_common(12):
        rows.append({"group": key, "count": value})
        print(f"   {key:<14} {value:>6}")
    stats["total_parts"] = len(names)
    stats["plain_parts"] = len(plain)
    stats["groups"] = rows

    print("\nB. いちばん小さいグラフを組んで動かす")
    g, add, port_a, port_b = add_graph([3.0, 4.0])
    print(f"   ノード {len(list(g.allNodes()))}個 / "
          f"ポート {len(list(g.allPorts()))}個")
    print(f"   1つ目の入力の型: {g.portTypeName(port_a)}")
    print(f"   2つ目の入力の型: {g.portTypeName(port_b)}")
    g.compileProgram()
    g.executeProgram()
    value = g.getNodeOutputData("add", "result")
    ok = abs(float(value) - 7.0) < 1e-9
    print(f"   3 + 4 = {value}")
    print(f"   正しいか: {'はい' if ok else 'いいえ'}")
    stats["tiny"] = {"nodes": len(list(g.allNodes())),
                     "ports": len(list(g.allPorts())),
                     "type_a": g.portTypeName(port_a),
                     "type_b": g.portTypeName(port_b),
                     "value": float(value), "ok": ok}

    print("\n   2つ目の入力は可変長なので、いくつでも足せる")
    print(f"   {'足す数':>8} {'式':<24} {'答え':>10} {'正しいか':>10}")
    variadic = []
    for count in (2, 3, 5, 10):
        vals = [float(i + 1) for i in range(count)]
        gg, node, pa, pb = add_graph(vals)
        gg.compileProgram()
        gg.executeProgram()
        got = float(gg.getNodeOutputData("add", "result"))
        want = sum(vals)
        variadic.append({"count": count, "sum": got, "expected": want,
                         "ok": abs(got - want) < 1e-9})
        expr = " + ".join(str(int(v)) for v in vals)
        if len(expr) > 22:
            expr = expr[:19] + "..."
        print(f"   {count:>8} {expr:<24} {got:>10.1f} "
              f"{'はい' if abs(got - want) < 1e-9 else 'いいえ':>10}")
    stats["variadic"] = variadic

    print("\n   枝を生やさずに parm だけ入れたらどうなるか")
    bad = apex.Graph()
    bad_add = bad.addNode("add", "Add<Float>")
    bad.setNodeParm(bad_add, "a", 3.0)
    bad.setNodeParm(bad_add, "b", 4.0)
    bad.addGraphOutput(bad_add, "result")
    bad.compileProgram()
    bad.executeProgram()
    bad_value = float(bad.getNodeOutputData("add", "result"))
    print(f"   parm に a=3 / b=4 を入れた結果: {bad_value}")
    print(f"   パラメータの中身: {dict(bad.getNodeParms(bad_add))}")
    print(f"   b は効いているか: "
          f"{'はい' if abs(bad_value - 7.0) < 1e-9 else 'いいえ'}")
    stats["parm_only"] = {"value": bad_value,
                          "parms": dict(bad.getNodeParms(bad_add))}

    print("\nC. グラフの実行はどれくらい速いか")
    g2, add2, pa2, pb2 = add_graph([1.0, 2.0])
    start = time.perf_counter()
    g2.compileProgram()
    compile_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(RUNS):
        g2.executeProgram()
    run_time = time.perf_counter() - start
    print(f"   組み立て（compile）: {compile_time * 1000:.4f} ミリ秒")
    print(f"   {RUNS:,}回の実行: {run_time:.4f} 秒")
    print(f"   1回あたり: {run_time / RUNS * 1e6:.3f} マイクロ秒")
    print(f"   組み立ては実行 {compile_time / (run_time / RUNS):.0f}回分")
    stats["speed"] = {"runs": RUNS, "compile_ms": compile_time * 1000,
                      "total_s": run_time,
                      "per_run_us": run_time / RUNS * 1e6,
                      "compile_in_runs": compile_time / (run_time / RUNS)}

    print("\nD. SOP 側から触れるノード")
    sops = sorted(hou.sopNodeTypeCategory().nodeTypes().keys())
    apex_sops = [n for n in sops if n.startswith("apex")]
    kine_sops = [n for n in sops if n.startswith("kinefx")]
    print(f"   apex:: で始まる SOP: {len(apex_sops)}種")
    print(f"   kinefx:: で始まる SOP: {len(kine_sops)}種")
    print(f"   SOP 全体: {len(sops)}種")
    print(f"   合わせて SOP 全体の "
          f"{(len(apex_sops) + len(kine_sops)) / len(sops) * 100:.1f}%")
    stats["sops"] = {"apex": len(apex_sops), "kinefx": len(kine_sops),
                     "all": len(sops),
                     "apex_names": apex_sops[:10],
                     "kinefx_names": kine_sops[:10]}

    with open(os.path.join(OUT, "050_stats.json"), "w",
              encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    # 組んだ APEX グラフを、SOP と同じ形式の図に落とす
    graph = {
        "title": "実験050 — APEX のいちばん小さいグラフ",
        "network": "apex::Graph（シーンの中ではなくデータの中にある）",
        "houdini_version": hou.applicationVersionString(),
        "nodes": [
            {"name": "v0", "type": "Value<Float>", "pos": [-1.2, 3.0],
             "flags": {"display": False}, "params": {"parm": 3.0}},
            {"name": "v1", "type": "Value<Float>", "pos": [1.2, 3.0],
             "flags": {"display": False}, "params": {"parm": 4.0}},
            {"name": "add", "type": "Add<Float>", "pos": [0.0, 1.4],
             "flags": {"display": True},
             "params": {"a": "Float", "b": "VariadicArg<Float>"}},
        ],
        "edges": [
            {"from": "v0", "from_output": 0, "to": "add", "to_input": 0},
            {"from": "v1", "from_output": 0, "to": "add", "to_input": 1},
        ],
    }
    with open(os.path.join(OUT, "050_graph.json"), "w",
              encoding="utf-8") as fp:
        json.dump(graph, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/050_stats.json, out/050_graph.json")


if __name__ == "__main__":
    main()
