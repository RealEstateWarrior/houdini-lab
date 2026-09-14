"""実験064 — MPM の刻みを細かくすると、結果はどこへ落ち着くか。

シミュレーションは1フレームを何回かに分けて解く。その回数が substep。
細かくするほど正しくなるはずだが、そのぶん時間がかかる。

<strong>では、どこまで細かくすれば「落ち着いた」と言えるのか。</strong>

実験018で、煙のサンプル数とノイズの関係を測ったときと同じ問いになる。
あのときは「4倍にすればノイズは半分」という式を立てて、
<strong>当たったのは狭い範囲だけ</strong>だった。今回はどうか。

  A. 刻みを 1 / 2 / 4 / 8 / 16 と変えて、結果がどう動くか
  B. いちばん細かいものを正として、どれだけずれるか
  C. 時間との引き換え

    hython examples/064_mpm_substeps.py
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "064_stats.json")

START_Y = 3.0
SEP = 0.12
LAST = 30
SUBSTEPS = (1, 2, 4, 8, 16)


def build(substeps=None, sep=SEP):
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
    if substeps is not None:
        solver.parm("doglobalsubsteps").set(1)
        solver.parm("globalsubsteps").set(substeps)
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
           "y_max": float(pts[:, 1].max()),
           "spread": float(max(pts[:, 0].max() - pts[:, 0].min(),
                               pts[:, 2].max() - pts[:, 2].min()))}
    if g.findPointAttrib("Je") and g.findPointAttrib("Jp"):
        je = numpy.asarray([p.attribValue("Je") for p in g.points()])
        jp = numpy.asarray([p.attribValue("Jp") for p in g.points()])
        out["J"] = float((je * jp).mean())
    return out


def main():
    import hou
    stats = {"substeps": list(SUBSTEPS), "last": LAST, "sep": SEP}

    print("A・C. 刻みを変えて、結果と時間を測る")
    print(f"   {'substep':>8} {'粒':>7} {'高さの平均':>12} {'いちばん上':>12} "
          f"{'広がり':>10} {'Je × Jp':>10} {'かかった時間':>14} "
          f"{'1刻みあたり':>14}")
    rows = []
    for sub in SUBSTEPS:
        geo, box, container, source, collider, solver = build(sub)
        hou.setFrame(1)
        solver.geometry()
        start = time.perf_counter()
        for frame in range(2, LAST + 1):
            hou.setFrame(frame)
            solver.geometry()
        seconds = time.perf_counter() - start
        info = stats_of(solver)
        info["substeps"] = sub
        info["seconds"] = seconds
        info["per_substep"] = seconds / sub
        rows.append(info)
        print(f"   {sub:>8} {info['count']:>7,} {info['y_mean']:>12.6f} "
              f"{info['y_max']:>12.6f} {info['spread']:>10.5f} "
              f"{info.get('J', 0):>10.6f} {seconds:>13.2f}秒 "
              f"{seconds / sub:>13.3f}秒")
    stats["rows"] = rows

    print("\nB. いちばん細かい 16 を正として、どれだけずれるか")
    ref = rows[-1]
    print(f"   {'substep':>8} {'高さのずれ':>14} {'広がりのずれ':>14} "
          f"{'Je × Jp のずれ':>16} {'時間 ÷ 16の時間':>16}")
    for r in rows:
        dy = abs(r["y_mean"] - ref["y_mean"])
        ds = abs(r["spread"] - ref["spread"])
        dj = abs(r.get("J", 0) - ref.get("J", 0))
        r["dy"] = dy
        r["ds"] = ds
        r["dj"] = dj
        print(f"   {r['substeps']:>8} {dy:>14.6f} {ds:>14.6f} "
              f"{dj:>16.6f} {r['seconds'] / ref['seconds']:>16.3f}")

    print("\n   刻みを2倍にすると、ずれはどうなるか")
    print(f"   {'比べる組':>12} {'高さのずれの比':>16} {'広がりのずれの比':>18}")
    for a, b in zip(rows[:-2], rows[1:-1]):
        ry = a["dy"] / b["dy"] if b["dy"] else float("inf")
        rs = a["ds"] / b["ds"] if b["ds"] else float("inf")
        print(f"   {a['substeps']:>5} → {b['substeps']:<5} "
              f"{ry:>16.3f} {rs:>18.3f}")

    worst = max(r["dy"] for r in rows[:-1])
    print(f"\n   16 との高さのずれの最大: {worst:.6f}")
    settled = [r for r in rows if r["dy"] < 0.01 and r["substeps"] < 16]
    if settled:
        print(f"   高さのずれが 0.01 未満になるのは substep "
              f"{settled[0]['substeps']} から")
        stats["settled_at"] = settled[0]["substeps"]
    else:
        print("   substep 8 以下では、どれも 0.01 未満にならない")
        stats["settled_at"] = None
    print(f"   16 は 1 の {ref['seconds'] / rows[0]['seconds']:.1f}倍の時間")

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/064_stats.json")


def shot(sub):
    import hou
    import hou_tools
    geo, box, container, source, collider, solver = build(int(sub))
    hou.setFrame(LAST)
    merged = geo.createNode("merge", f"shot_{sub}")
    merged.setInput(0, solver)
    merged.setInput(1, geo.node("ground"))
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    bbox = hou.BoundingBox(-1.6, -0.5, -1.6, 1.6, 1.6, 1.6)
    png = os.path.join(OUT, f"064_sub{sub}.png")
    hou_tools.render_preview(merged.path(), png, res=(620, 620),
                             direction=(0.35, 0.3, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/064_sub{sub}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
