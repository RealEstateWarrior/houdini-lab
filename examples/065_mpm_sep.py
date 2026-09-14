"""実験065 — MPM の粒を細かくすると、結果はどこへ落ち着くか。

実験064では「1フレームを何回に分けるか」（substep）を変えた。
今回は「物を何粒で表すか」（粒の間隔）を変える。

<strong>どちらも「細かくすれば正しくなる」はずの数字だが、効き方は同じだろうか。</strong>

  A. 粒の間隔を 0.20 から 0.07 まで変えて、結果がどう動くか
  B. いちばん細かいものを正として、どれだけずれるか
  C. 時間との引き換え。substep のときと比べてどうか

    hython examples/065_mpm_sep.py
    hython examples/065_mpm_sep.py shot coarse
    hython examples/065_mpm_sep.py shot fine
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "065_stats.json")

START_Y = 3.0
LAST = 30
SEPS = (0.20, 0.16, 0.12, 0.10, 0.08, 0.07)


def build(sep):
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
    stats = {"seps": list(SEPS), "last": LAST}

    print("A・C. 粒の間隔を変えて、結果と時間を測る")
    print(f"   {'間隔':>7} {'粒':>8} {'高さの平均':>12} {'いちばん上':>12} "
          f"{'広がり':>10} {'Je × Jp':>10} {'かかった時間':>14} "
          f"{'粒1つあたり':>14}")
    rows = []
    for sep in SEPS:
        geo, box, container, source, collider, solver = build(sep)
        hou.setFrame(1)
        solver.geometry()
        start = time.perf_counter()
        for frame in range(2, LAST + 1):
            hou.setFrame(frame)
            solver.geometry()
        seconds = time.perf_counter() - start
        info = stats_of(solver)
        info["sep"] = sep
        info["seconds"] = seconds
        info["per_point_ms"] = seconds / info["count"] * 1000
        rows.append(info)
        print(f"   {sep:>7} {info['count']:>8,} {info['y_mean']:>12.6f} "
              f"{info['y_max']:>12.6f} {info['spread']:>10.5f} "
              f"{info.get('J', 0):>10.6f} {seconds:>13.2f}秒 "
              f"{info['per_point_ms']:>13.3f}ms")
    stats["rows"] = rows

    print("\nB. いちばん細かい 0.07 を正として、どれだけずれるか")
    ref = rows[-1]
    print(f"   {'間隔':>7} {'高さのずれ':>14} {'広がりのずれ':>14} "
          f"{'Je × Jp のずれ':>16} {'時間 ÷ 0.07の時間':>18}")
    for r in rows:
        r["dy"] = abs(r["y_mean"] - ref["y_mean"])
        r["ds"] = abs(r["spread"] - ref["spread"])
        r["dj"] = abs(r.get("J", 0) - ref.get("J", 0))
        print(f"   {r['sep']:>7} {r['dy']:>14.6f} {r['ds']:>14.6f} "
              f"{r['dj']:>16.6f} {r['seconds'] / ref['seconds']:>18.3f}")

    print("\n   粒の数と時間の関係")
    print(f"   {'間隔':>7} {'粒':>8} {'粒の比':>9} {'時間の比':>10} "
          f"{'時間の比 ÷ 粒の比':>18}")
    base = rows[0]
    for r in rows:
        pr = r["count"] / base["count"]
        tr = r["seconds"] / base["seconds"]
        print(f"   {r['sep']:>7} {r['count']:>8,} {pr:>9.2f} {tr:>10.2f} "
              f"{tr / pr:>18.3f}")

    worst = max(r["ds"] for r in rows[:-1])
    print(f"\n   広がりのずれの最大: {worst:.6f}")
    print(f"   いちばん細かいのは、いちばん粗いのの "
          f"{ref['seconds'] / rows[0]['seconds']:.1f}倍の時間")

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/065_stats.json")


def shot(case):
    import hou
    import hou_tools
    sep = 0.20 if case == "coarse" else 0.07
    geo, box, container, source, collider, solver = build(sep)
    hou.setFrame(LAST)
    merged = geo.createNode("merge", f"shot_{case}")
    merged.setInput(0, solver)
    merged.setInput(1, geo.node("ground"))
    merged.setDisplayFlag(True)
    merged.setRenderFlag(True)
    bbox = hou.BoundingBox(-1.6, -0.5, -1.6, 1.6, 1.6, 1.6)
    png = os.path.join(OUT, f"065_{case}.png")
    hou_tools.render_preview(merged.path(), png, res=(620, 620),
                             direction=(0.35, 0.3, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/065_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
