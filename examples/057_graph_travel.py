"""実験057 — APEX のグラフを持ち歩く。ネットワークがジオメトリになる。

APEX のいちばんの特徴は、<strong>ノードのネットワークそのものをデータとして
持ち歩けること</strong>だと実験050で書いた。今回それを確かめる。

グラフを <code>saveToGeometry</code> でジオメトリに落とすと、
<strong>ノード1つが点1つ、配線1本がプリミティブ1つ</strong>になる。
そのままファイルに保存でき、別のプロセスで読み直して実行できる。

  A. ノードの数・配線の数と、点・プリミティブの数の対応
  B. 点には何が入っているか
  C. ファイルに保存して、別のプロセスで読んでも同じ答えが出るか
  D. グラフの大きさとファイルの大きさ

    hython examples/057_graph_travel.py save
    hython examples/057_graph_travel.py load
    python  examples/057_graph_travel.py report
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "057_stats.json")
GEO_FILE = os.path.join(OUT, "057_graph.bgeo.sc")

SIZES = (2, 4, 8, 16, 32, 64)


def build_chain(count):
    """1 + 2 + … + count を足すグラフ。ノードは count + 1 個。"""
    import apex
    import hou
    g = apex.Graph()
    add = g.addNode("add", "Add<Float>")
    port_a, port_b = g.getInputPorts(add)

    # 置き場所も決めておく。ジオメトリにしたとき、これが点の位置になる。
    g.setNodePosition(add, hou.Vector3(0.0, 0.0, 0.0))

    first = g.addNode("v0", "Value<Float>")
    g.setNodeParm(first, "parm", 1.0)
    g.setNodePosition(first, hou.Vector3(-0.5 * count, 2.0, 0.0))
    g.addWire(g.getOutputPorts(first)[0], port_a)

    for i in range(1, count):
        node = g.addNode(f"v{i}", "Value<Float>")
        g.setNodeParm(node, "parm", float(i + 1))
        g.setNodePosition(node,
                          hou.Vector3(-0.5 * count + i, 2.0, 0.0))
        sub = g.addSubPort(port_b, f"b{i}")
        g.addWire(g.getOutputPorts(node)[0], sub)

    g.addGraphOutput(add, "result")
    return g, sum(range(1, count + 1))


def run(graph):
    graph.compileProgram()
    graph.executeProgram()
    return float(graph.getNodeOutputData("add", "result"))


def save():
    import apex
    import hou

    stats = {"sizes": list(SIZES)}
    print("A. ノードの数・配線の数と、ジオメトリの大きさ")
    print(f"   {'足す数':>7} {'ノード':>7} {'配線':>6} {'点':>6} "
          f"{'プリミティブ':>12} {'答え':>10} {'合っているか':>12}")
    rows = []
    for count in SIZES:
        g, want = build_chain(count)
        nodes = len(list(g.allNodes()))
        wires = count
        geo = hou.Geometry()
        g.saveToGeometry(geo)
        got = run(g)
        rows.append({"count": count, "nodes": nodes, "wires": wires,
                     "points": len(geo.points()),
                     "prims": len(geo.prims()),
                     "value": got, "expected": want,
                     "ok": abs(got - want) < 1e-9})
        print(f"   {count:>7} {nodes:>7} {wires:>6} {len(geo.points()):>6} "
              f"{len(geo.prims()):>12} {got:>10.1f} "
              f"{'はい' if abs(got - want) < 1e-9 else 'いいえ':>12}")
    stats["sizes_table"] = rows
    same_nodes = all(r["points"] == r["nodes"] for r in rows)
    same_wires = all(r["prims"] == r["wires"] for r in rows)
    print(f"   点の数＝ノードの数か: {'はい' if same_nodes else 'いいえ'}")
    print(f"   プリミティブの数＝配線の数か: "
          f"{'はい' if same_wires else 'いいえ'}")
    stats["points_equal_nodes"] = same_nodes
    stats["prims_equal_wires"] = same_wires

    print("\nB. 点には何が入っているか")
    g, want = build_chain(3)
    geo = hou.Geometry()
    g.saveToGeometry(geo)
    point_attribs = sorted(a.name() for a in geo.pointAttribs())
    detail_attribs = sorted(a.name() for a in geo.globalAttribs())
    print(f"   点のアトリビュート: {point_attribs}")
    print(f"   ディテールのアトリビュート: {detail_attribs}")
    print(f"   {'点':>4} {'name':>8} {'callback':>18}")
    nodes_seen = []
    for pt in geo.points():
        nodes_seen.append({"name": pt.attribValue("name"),
                           "callback": pt.attribValue("callback")})
        print(f"   {pt.number():>4} {pt.attribValue('name'):>8} "
              f"{pt.attribValue('callback'):>18}")
    stats["point_attribs"] = point_attribs
    stats["detail_attribs"] = detail_attribs
    stats["nodes_seen"] = nodes_seen

    print("\nC・D. ファイルに保存する")
    g, want = build_chain(10)
    geo = hou.Geometry()
    g.saveToGeometry(geo)
    geo.saveToFile(GEO_FILE)
    size = os.path.getsize(GEO_FILE)
    print(f"   {os.path.basename(GEO_FILE)}: {size:,} バイト")
    print(f"   この中の答えは {want}（1 + 2 + … + 10）")
    stats["file"] = {"path": os.path.basename(GEO_FILE), "bytes": size,
                     "expected": want, "count": 10}

    print("\n   大きさとファイルの重さ")
    print(f"   {'ノード':>7} {'点':>6} {'バイト':>10} {'1ノードあたり':>14}")
    file_rows = []
    for count in SIZES:
        g2, _ = build_chain(count)
        geo2 = hou.Geometry()
        g2.saveToGeometry(geo2)
        path = os.path.join(OUT, f"057_tmp_{count}.bgeo.sc")
        geo2.saveToFile(path)
        nbytes = os.path.getsize(path)
        nodes = len(list(g2.allNodes()))
        file_rows.append({"count": count, "nodes": nodes, "bytes": nbytes,
                          "per_node": nbytes / nodes})
        print(f"   {nodes:>7} {len(geo2.points()):>6} {nbytes:>10,} "
              f"{nbytes / nodes:>13.1f}B")
        os.remove(path)
    stats["file_sizes"] = file_rows

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print(f"\n保存: {os.path.basename(GEO_FILE)}, out/057_stats.json")
    print("   別のプロセスで読むには: hython examples/057_graph_travel.py load")


def load():
    """別のプロセスで、ファイルから読んで実行する。"""
    import apex
    import hou

    geo = hou.Geometry()
    geo.loadFromFile(GEO_FILE)
    print(f"読んだジオメトリ: {len(geo.points())}点 / "
          f"{len(geo.prims())}プリミティブ")

    g = apex.Graph()
    ok = g.loadFromGeometry(geo)
    print(f"グラフとして読めたか: {'はい' if ok else 'いいえ'}")
    print(f"ノード: {len(list(g.allNodes()))}個 / "
          f"ポート: {len(list(g.allPorts()))}個")
    value = run(g)
    want = sum(range(1, 11))
    print(f"実行した答え: {value}（期待は {want}）")
    print(f"一致するか: {'はい' if abs(value - want) < 1e-9 else 'いいえ'}")

    stats = {}
    if os.path.exists(STATS):
        with open(STATS, encoding="utf-8") as fp:
            stats = json.load(fp)
    stats["reload"] = {"points": len(geo.points()),
                       "prims": len(geo.prims()),
                       "nodes": len(list(g.allNodes())),
                       "value": value, "expected": want,
                       "ok": abs(value - want) < 1e-9}
    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("追記: out/057_stats.json")


def shot():
    """ジオメトリになったグラフを、そのまま絵にする。"""
    import hou
    import hou_tools

    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "graphgeo")
    read = geo.createNode("file", "read")
    read.parm("file").set(GEO_FILE.replace("\\", "/"))

    g = read.geometry()
    xs = [p.position()[0] for p in g.points()]
    ys = [p.position()[1] for p in g.points()]
    zs = [p.position()[2] for p in g.points()]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    print(f"点の広がり: x {min(xs):.2f}〜{max(xs):.2f} / "
          f"y {min(ys):.2f}〜{max(ys):.2f} / z {min(zs):.2f}〜{max(zs):.2f}")

    wire = geo.createNode("polywire", "wires")
    wire.setFirstInput(read)
    wire.parm("radius").set(span * 0.006)

    ball = geo.createNode("sphere", "nodeball")
    ball.parm("type").set(2)
    ball.parm("rows").set(12)
    ball.parm("cols").set(12)
    r = span * 0.022
    ball.parmTuple("rad").set((r, r, r))
    show = geo.createNode("copytopoints::2.0", "show")
    show.setInput(0, ball)
    show.setInput(1, read)

    merged = geo.createNode("merge", "out")
    merged.setInput(0, wire)
    merged.setInput(1, show)
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    geo.layoutChildren()

    bbox = merged.geometry().boundingBox()
    png = os.path.join(OUT, "057_graphgeo.png")
    hou_tools.render_preview(merged.path(), png, res=(820, 520),
                             direction=(0.0, 0.0, 1.0), shading="smoothwire",
                             frame_bbox=bbox, margin=1.12)
    print(f"保存: out/057_graphgeo.png")


def report():
    with open(STATS, encoding="utf-8") as fp:
        stats = json.load(fp)
    print("A. ノードの数と、ジオメトリの大きさ")
    print(f"   {'足す数':>7} {'ノード':>7} {'配線':>6} {'点':>6} "
          f"{'プリミティブ':>12} {'答え':>10}")
    for r in stats["sizes_table"]:
        print(f"   {r['count']:>7} {r['nodes']:>7} {r['wires']:>6} "
              f"{r['points']:>6} {r['prims']:>12} {r['value']:>10.1f}")
    if "reload" in stats:
        r = stats["reload"]
        print(f"\nC. 別のプロセスで読み直した結果: {r['value']}"
              f"（期待 {r['expected']}）→ "
              f"{'一致' if r['ok'] else '不一致'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "save":
        save()
    elif cmd == "load":
        load()
    elif cmd == "shot":
        shot()
    else:
        report()
