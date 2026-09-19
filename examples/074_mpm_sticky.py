"""実験074 — コライダの sticky は、地面の sticky と同じか。天井にぶら下がれるか。

<a href="#exp067">実験067</a>で、組み込みの地面の sticky（粘着）は「離れるとき」にだけ効くと分かった。
落として跳ねさせると、戻る高さが sticky 1.0 でちょうど半分になった。
<a href="#exp069">実験069</a>で、コライダの摩擦は組み込みの地面と同じものだった。
<strong>では sticky も同じか。</strong>

  A. 落として跳ねさせる。組み込みの地面とコライダの板で、sticky を同じ値に振って並べる
  B. 天井にぶら下げる。塊を天井の板の真下に接して置き、sticky を上げていく。
     離れるときに引き止めるなら、重さで離れようとする塊を引き止めて、ぶら下がれるはず

    hython examples/074_mpm_sticky.py a
    hython examples/074_mpm_sticky.py b
    hython examples/074_mpm_sticky.py shot
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

LAST = 40
FPS = 24.0
SEP = 0.12
CEILING = 3.0          # 天井の板の下面
STICKY = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 20.0)


def build(kind, sticky, friction=0.25, gap=0.06):
    """kind: "ground"（組み込みの地面）/ "collider"（床の板）/ "ceiling"（天井の板）"""
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "sticky")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    y = CEILING - 0.5 - gap if kind == "ceiling" else 2.5
    box.parmTuple("t").set((0.0, y, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(SEP)
    container.parm("sizex").set(8.0)
    container.parm("sizey").set(8.0)
    container.parm("sizez").set(8.0)
    container.parm("centery").set(0.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)
    if kind == "ground":
        solver.parm("groundactive").set(1)
        solver.parm("groundfriction").set(friction)
        solver.parm("groundsticky").set(sticky)
    else:
        solver.parm("groundactive").set(0)
        plate = geo.createNode("box", "plate")
        plate.parmTuple("size").set((6.0, 0.4, 6.0))
        plate.parm("ty").set(CEILING + 0.2 if kind == "ceiling" else -0.2)
        collider = geo.createNode("mpmcollider", "collider")
        collider.setInput(0, plate)
        collider.setInput(1, container)
        collider.parm("friction").set(friction)
        collider.parm("sticky").set(sticky)
        solver.setInput(1, collider)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver


def heights(node):
    import numpy
    pts = numpy.asarray([p.position() for p in node.geometry().points()], dtype=float)
    return float(pts[:, 1].mean()), float(pts[:, 1].max()), int(len(pts))


def bounce(kind, sticky):
    import hou
    geo, solver = build(kind, sticky)
    track = []
    start = time.perf_counter()
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        y, top, n = heights(solver)
        track.append((frame, y))
    seconds = time.perf_counter() - start
    low = min(range(1, len(track)), key=lambda i: track[i][1])
    rebound = max(t[1] for t in track[low:]) - track[low][1]
    return {"kind": kind, "sticky": sticky, "y_low": track[low][1],
            "low_frame": track[low][0], "rebound": rebound, "y_last": track[-1][1],
            "seconds": seconds}


def hang(sticky, gap=0.06):
    import hou
    geo, solver = build("ceiling", sticky, gap=gap)
    hou.setFrame(1)
    y0, top0, n = heights(solver)
    rows = []
    start = time.perf_counter()
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        if frame in (6, 12, 24, 40):
            y, top, n = heights(solver)
            rows.append({"frame": frame, "drop": y0 - y, "gap": CEILING - top})
    seconds = time.perf_counter() - start
    t = (LAST - 1) / FPS
    return {"sticky": sticky, "gap_set": gap, "y0": y0, "top0": top0, "gap0": CEILING - top0,
            "frames": rows, "drop": rows[-1]["drop"], "free_fall": 0.5 * 9.81 * t * t,
            "count": n, "seconds": seconds}


def part_a():
    print("A. y = 2.5 から落として跳ねさせる（摩擦 0.25）。地面とコライダの板で sticky を並べる")
    rows = []
    for s in STICKY:
        for kind in ("ground", "collider"):
            r = bounce(kind, s)
            rows.append(r)
            print(f"   sticky {s:>5} {kind:>8} | いちばん低い {r['y_low']:.6f}（F{r['low_frame']}）"
                  f" 戻った高さ {r['rebound']:.6f} | 40フレーム目 {r['y_last']:.6f} | {r['seconds']:.2f}秒")
    with open(os.path.join(OUT, "074_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/074_a.json")


def part_b():
    print("B. 天井の板の真下に塊を置いて、sticky を上げる（摩擦 0.25）")
    rows = []
    for s in (0.0, 1.0, 5.0, 20.0, 100.0, 1000.0):
        r = hang(s)
        rows.append(r)
        steps = " / ".join(f"F{f['frame']} {f['drop']:.4f}" for f in r["frames"])
        print(f"   sticky {s:>7} | 最初のすき間 {r['gap0']:.4f} | 下がった量 {steps}"
              f"（自由落下なら {r['free_fall']:.4f}） | {r['count']}粒 {r['seconds']:.2f}秒")
    with open(os.path.join(OUT, "074_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/074_b.json")


def part_c():
    print("C. すき間を詰める・食い込ませる（sticky 0 と 1000）")
    rows = []
    for gap in (0.0, -0.05, -0.1, -0.2):
        for s in (0.0, 1000.0):
            r = hang(s, gap)
            rows.append(r)
            steps = " / ".join(f"F{f['frame']} {f['drop']:.4f}" for f in r["frames"])
            print(f"   置いたすき間 {gap:>5} sticky {s:>7} | 最初のすき間 {r['gap0']:+.4f} | "
                  f"下がった量 {steps} | {r['seconds']:.2f}秒")
    with open(os.path.join(OUT, "074_c.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/074_c.json")


def shot(sticky="0"):
    import hou
    import hou_tools
    geo, solver = build("ceiling", float(sticky))
    hou.setFrame(12)                         # 0.46秒後。自由落下なら 1.03 下がっている
    bbox = hou.BoundingBox(-1.5, 0.8, -1.0, 1.5, CEILING + 0.5, 1.0)
    plate = geo.node("plate")
    merge = geo.createNode("merge", "show")
    merge.setInput(0, plate)
    merge.setInput(1, solver)
    png = os.path.join(OUT, f"074_ceiling_{int(float(sticky))}.png")
    hou_tools.render_preview(merge.path(), png, res=(360, 420),
                             direction=(0.35, 0.15, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    if float(sticky) > 0:
        hou_tools.save_hip(os.path.join(OUT, "074_sticky.hipnc"))
    print(f"保存: {png}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part_a()
    elif arg == "b":
        part_b()
    elif arg == "c":
        part_c()
    elif arg == "shot":
        shot(sys.argv[2] if len(sys.argv) > 2 else "0")
