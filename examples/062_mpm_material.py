"""実験062 — MPM でぶつける。材質で何が変わるか、10種類ぜんぶ測る。

実験061で、MPM の粒は自由落下の式に乗ることを確かめた。
今回は地面にぶつける。<code>mpmsource</code> には材質の見本が10種類ある。

  Concrete / Honey / Jello / Metal / Mud / Rubber / Sand / Snow / Soil / Water

粒は <code>Je</code> と <code>Jp</code> というアトリビュートを持っている。
これは<strong>体積の比</strong>で、Je が弾性（戻る）、Jp が塑性（戻らない）ぶん。
<strong>掛けた Je × Jp が 1 なら、体積が保たれている</strong>ことになる。

  A. ぶつけたあと、粒の数は保たれるか
  B. 体積比 Je × Jp はどうなるか
  C. 材質10種で、広がり方と体積比はどう違うか

    hython examples/062_mpm_material.py
    hython examples/062_mpm_material.py shot water
    hython examples/062_mpm_material.py shot concrete
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "062_stats.json")

RES = (620, 620)
START_Y = 3.0
SEP = 0.12
LAST = 40
PRESET = "sidefx::recipe::sop/mpmsource::material_{}"
MATERIALS = ("concrete", "honey", "jello", "metal", "mud",
             "rubber", "sand", "snow", "soil", "water")
TYPES = ("elastic", "chunky", "liquid", "viscous", "sandy")
TYPE_LABEL = {"elastic": "Elastic（弾む）", "chunky": "Chunky（既定・塊）",
              "liquid": "Liquid（液体）", "viscous": "Viscous（粘る）",
              "sandy": "Sandy（砂）"}


def build(material=None, sep=SEP, mtype=None):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "mpm")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    box.parmTuple("t").set((0.0, START_Y, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(sep)
    container.parm("sizex").set(8.0)
    container.parm("sizey").set(6.0)
    container.parm("sizez").set(8.0)
    container.parm("centery").set(2.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)
    if material:
        source.parm("materialpreset").set(PRESET.format(material))
    if mtype:
        source.parm("materialtype").set(mtype)

    # 地面
    ground = geo.createNode("box", "ground")
    ground.parmTuple("size").set((6.0, 0.4, 6.0))
    ground.parmTuple("t").set((0.0, -0.2, 0.0))
    collider = geo.createNode("mpmcollider", "collider")
    collider.setInput(0, ground)
    collider.setInput(1, container)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(1, collider)
    solver.setInput(2, container)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, box, container, source, collider, solver


def stats_of(node):
    import numpy
    g = node.geometry()
    if g is None:
        return None
    pts = numpy.asarray([[p.position()[0], p.position()[1],
                          p.position()[2]] for p in g.points()])
    out = {"count": int(len(pts)),
           "y_mean": float(pts[:, 1].mean()),
           "y_min": float(pts[:, 1].min()),
           "y_max": float(pts[:, 1].max()),
           "spread": float(max(pts[:, 0].max() - pts[:, 0].min(),
                               pts[:, 2].max() - pts[:, 2].min()))}
    if g.findPointAttrib("Je") and g.findPointAttrib("Jp"):
        je = numpy.asarray([p.attribValue("Je") for p in g.points()])
        jp = numpy.asarray([p.attribValue("Jp") for p in g.points()])
        j = je * jp
        out.update({"Je": float(je.mean()), "Jp": float(jp.mean()),
                    "J": float(j.mean()), "J_min": float(j.min()),
                    "J_max": float(j.max())})
    return out


def main():
    import hou
    stats = {}

    print("A・B. 既定（Snow）で地面にぶつける")
    geo, box, container, source, collider, solver = build()
    print(f"   {'frame':>6} {'粒の数':>8} {'高さの平均':>12} "
          f"{'いちばん下':>12} {'広がり':>10} {'Je':>10} {'Jp':>10} "
          f"{'Je × Jp':>10}")
    rows = []
    for frame in (1, 5, 10, 15, 20, 30, 40):
        hou.setFrame(frame)
        info = stats_of(solver)
        info["frame"] = frame
        rows.append(info)
        print(f"   {frame:>6} {info['count']:>8,} {info['y_mean']:>12.6f} "
              f"{info['y_min']:>12.6f} {info['spread']:>10.5f} "
              f"{info.get('Je', 0):>10.6f} {info.get('Jp', 0):>10.6f} "
              f"{info.get('J', 0):>10.6f}")
    counts = [r["count"] for r in rows]
    print(f"\n   粒の数の幅: {max(counts) - min(counts)}")
    print(f"   数は保たれたか: "
          f"{'はい' if max(counts) == min(counts) else 'いいえ'}")
    js = [r.get("J", 1.0) for r in rows]
    print(f"   体積比 Je × Jp: {min(js):.6f} 〜 {max(js):.6f}"
          f"（幅 {max(js) - min(js):.6f}）")
    stats["snow"] = rows
    stats["count_spread"] = max(counts) - min(counts)

    print("\nC. 材質10種で比べる（40フレーム目）")
    print(f"   {'材質':>10} {'粒の数':>8} {'高さの平均':>12} "
          f"{'いちばん上':>12} {'広がり':>10} {'Je':>10} {'Jp':>10} "
          f"{'Je × Jp':>10}")
    mats = []
    for material in MATERIALS:
        geo, box, container, source, collider, solver = build(material)
        hou.setFrame(LAST)
        info = stats_of(solver)
        info["material"] = material
        mats.append(info)
        print(f"   {material:>10} {info['count']:>8,} "
              f"{info['y_mean']:>12.6f} {info['y_max']:>12.6f} "
              f"{info['spread']:>10.5f} {info.get('Je', 0):>10.6f} "
              f"{info.get('Jp', 0):>10.6f} {info.get('J', 0):>10.6f}")
    stats["materials"] = mats

    same = all(abs(m["spread"] - mats[0]["spread"]) < 1e-9 for m in mats)
    print(f"   10種すべて同じ結果か: {'はい' if same else 'いいえ'}")
    if same:
        print("   → materialpreset は、スクリプトから入れても効いていない")
    stats["preset_ignored"] = bool(same)

    print("\nD. materialtype の5種で比べる（40フレーム目）")
    print(f"   {'種類':>18} {'粒の数':>8} {'高さの平均':>12} "
          f"{'いちばん上':>12} {'広がり':>10} {'Je':>10} {'Jp':>10} "
          f"{'Je × Jp':>10}")
    types = []
    for mtype in TYPES:
        geo, box, container, source, collider, solver = build(mtype=mtype)
        hou.setFrame(LAST)
        info = stats_of(solver)
        info["type"] = mtype
        types.append(info)
        print(f"   {TYPE_LABEL[mtype]:>18} {info['count']:>8,} "
              f"{info['y_mean']:>12.6f} {info['y_max']:>12.6f} "
              f"{info['spread']:>10.5f} {info.get('Je', 0):>10.6f} "
              f"{info.get('Jp', 0):>10.6f} {info.get('J', 0):>10.6f}")
    stats["types"] = types

    spreads = sorted(types, key=lambda r: r["spread"])
    print(f"\n   いちばん広がったのは {spreads[-1]['type']}"
          f"（{spreads[-1]['spread']:.5f}）")
    print(f"   いちばん広がらなかったのは {spreads[0]['type']}"
          f"（{spreads[0]['spread']:.5f}）")
    js = sorted(types, key=lambda r: r.get("J", 1.0))
    print(f"   体積比がいちばん小さいのは {js[0]['type']}"
          f"（{js[0].get('J', 0):.6f}）")
    print(f"   体積比がいちばん大きいのは {js[-1]['type']}"
          f"（{js[-1].get('J', 0):.6f}）")

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    import hou_tools
    geo, box, container, source, collider, solver = build("water")
    hou.setFrame(LAST)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "062_graph.json"),
                          title="実験062 — MPM でぶつける")
    hou_tools.save_hip(os.path.join(OUT, "062_mpm.hipnc"))
    print("\n保存: out/062_stats.json, out/062_graph.json, out/062_mpm.hipnc")


def shot(case):
    import hou
    import hou_tools
    geo, box, container, source, collider, solver = build(mtype=case)
    hou.setFrame(LAST)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, solver)
    merged.setInput(1, geo.node("ground"))
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    bbox = hou.BoundingBox(-2.6, -0.5, -2.6, 2.6, 3.4, 2.6)
    png = os.path.join(OUT, f"062_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=RES,
                             direction=(0.35, 0.28, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/062_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
