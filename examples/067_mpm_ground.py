"""実験067 — MPM の地面。摩擦と粘着は、滑る距離をどう決めるか。

<a href="#exp066">実験066</a>で、mpmsolver が既定で y = 0 に地面を持っていると分かった。
その地面には Friction（既定 1.0）と Sticky（既定 0.0）が付いている。

  A. 摩擦を変えて、横に投げた塊がどこまで滑るか
  B. 「止まるまでの距離 = v0² ÷ (2 μ g)」という教科書の式に乗るか
  C. 粘着を変えると何が起きるか
  D. 初速を変えて、距離が初速の2乗に比例するか

一度に何度も組み直すと hython が止まるので、A / C / D を別々に走らせて
最後に足し合わせる。

    hython examples/067_mpm_ground.py a
    hython examples/067_mpm_ground.py c
    hython examples/067_mpm_ground.py d
    python  examples/067_mpm_ground.py merge
    hython examples/067_mpm_ground.py shot slip
    hython examples/067_mpm_ground.py shot grip
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

START_Y = 0.52
LAST = 40
FPS = 24.0
SEP = 0.12
G = 9.81
V0 = 4.0


def build(friction, sticky=0.0, v0=V0, y0=START_Y):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "mpm")

    box = geo.createNode("box", "box")
    box.parmTuple("size").set((1.0, 1.0, 1.0))
    box.parmTuple("t").set((0.0, y0, 0.0))

    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(SEP)
    container.parm("sizex").set(40.0)
    container.parm("sizey").set(8.0)
    container.parm("sizez").set(8.0)
    container.parm("centerx").set(14.0)
    container.parm("centery").set(2.0)

    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)
    source.parm("initialvelocityx").set(v0)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)
    # 組み込みの地面（実験066）。コライダは置かない
    solver.parm("groundactive").set(1)
    solver.parm("groundfriction").set(friction)
    solver.parm("groundsticky").set(sticky)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, solver


def stats_of(node):
    import numpy
    g = node.geometry()
    pts = numpy.asarray([[p.position()[0], p.position()[1], p.position()[2]]
                         for p in g.points()])
    out = {"count": int(len(pts)),
           "x_mean": float(pts[:, 0].mean()),
           "y_mean": float(pts[:, 1].mean()),
           "x_spread": float(pts[:, 0].max() - pts[:, 0].min())}
    if g.findPointAttrib("v"):
        vel = numpy.asarray([p.attribValue("v") for p in g.points()])
        out["vx_mean"] = float(vel[:, 0].mean())
        out["vy_mean"] = float(vel[:, 1].mean())
    return out


def bounce(friction, sticky, y0=2.5):
    """落として跳ねさせる。粘着は横滑りより、離れるときに効くはず。"""
    import hou
    geo, solver = build(friction, sticky, v0=0.0, y0=y0)
    hou.setFrame(1)
    stats_of(solver)
    track = []
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        info = stats_of(solver)
        track.append({"frame": frame, "y": info["y_mean"],
                      "vy": info.get("vy_mean", 0.0)})
    # いちばん下まで行ったあと、どこまで戻るか
    low = min(range(len(track)), key=lambda i: track[i]["y"])
    after = track[low:]
    rebound = max(t["y"] for t in after) - track[low]["y"]
    last = stats_of(solver)
    return {"friction": friction, "sticky": sticky, "y0": y0,
            "y_low": track[low]["y"], "low_frame": track[low]["frame"],
            "rebound": rebound, "y_last": last["y_mean"],
            "x_spread": last["x_spread"],
            "vy_last": last.get("vy_mean", 0.0)}


def run(friction, sticky=0.0, v0=V0):
    import hou
    geo, solver = build(friction, sticky, v0)
    hou.setFrame(1)
    first = stats_of(solver)
    start = time.perf_counter()
    stop_frame = None
    track = []
    for frame in range(2, LAST + 1):
        hou.setFrame(frame)
        info = stats_of(solver)
        track.append({"frame": frame, "x": info["x_mean"],
                      "vx": info.get("vx_mean", 0.0)})
        if stop_frame is None and abs(info.get("vx_mean", 0.0)) < 0.02:
            stop_frame = frame
    last = stats_of(solver)
    last["friction"] = friction
    last["sticky"] = sticky
    last["v0"] = v0
    last["x0"] = first["x_mean"]
    last["slid"] = last["x_mean"] - first["x_mean"]
    last["stop_frame"] = stop_frame
    last["stop_sec"] = (stop_frame - 1) / FPS if stop_frame else None
    last["seconds"] = time.perf_counter() - start
    last["track"] = track
    return last


def part(name, cases, title, labels):
    print(title)
    print(f"   {labels:>0}")
    rows = []
    for kw in cases:
        info = run(**kw)
        rows.append(info)
        stop = (f"{info['stop_frame']:>6}" if info["stop_frame"] else "  止まらず")
        print(f"   {info['friction']:>8} {info['sticky']:>8} {info['v0']:>6} "
              f"{info['slid']:>12.6f} {info.get('vx_mean', 0):>12.6f} "
              f"{info['y_mean']:>10.6f} {info['x_spread']:>10.6f} {stop}")
    path = os.path.join(OUT, f"067_{name}.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"\n保存: out/067_{name}.json")


HEAD = (f"{'摩擦':>8} {'粘着':>8} {'初速':>6} {'滑った距離':>12} "
        f"{'最後の vx':>12} {'高さ':>10} {'横の広がり':>10} {'止まった frame':>8}")


def merge():
    rows = {}
    for name in ("a", "c", "d", "e"):
        with open(os.path.join(OUT, f"067_{name}.json"), encoding="utf-8") as fp:
            rows[name] = json.load(fp)
    t = (LAST - 1) / FPS

    print("A. 摩擦を変えて、横に投げた塊がどこまで滑るか")
    print(f"   {'摩擦':>8} {'滑った距離':>12} {'最後の vx':>12} {'高さ':>10} "
          f"{'横の広がり':>10} {'止まった秒':>12}")
    for r in rows["a"]:
        stop = f"{r['stop_sec']:.4f}" if r["stop_sec"] else "止まらず"
        print(f"   {r['friction']:>8} {r['slid']:>12.6f} "
              f"{r.get('vx_mean', 0):>12.6f} {r['y_mean']:>10.6f} "
              f"{r['x_spread']:>10.6f} {stop:>12}")

    print("\nB. 教科書の式「止まるまでの距離 = v0² ÷ (2 μ g)」に乗るか")
    print(f"   {'摩擦 μ':>8} {'実測の距離':>12} {'式の距離':>12} {'実測 ÷ 式':>12} "
          f"{'実測の時間':>12} {'式の時間 v0÷(μg)':>16}")
    for r in rows["a"]:
        mu = r["friction"]
        if mu == 0:
            print(f"   {mu:>8} {r['slid']:>12.6f} {'∞':>12} {'—':>12} "
                  f"{'止まらず':>12} {'∞':>16}")
            continue
        want_d = r["v0"] ** 2 / (2 * mu * G)
        want_t = r["v0"] / (mu * G)
        got_t = r["stop_sec"] if r["stop_sec"] else float("nan")
        print(f"   {mu:>8} {r['slid']:>12.6f} {want_d:>12.6f} "
              f"{r['slid'] / want_d:>12.6f} {got_t:>12.6f} {want_t:>16.6f}")

    print("\nB2. 止まる前の減速そのもの。μg と合うか")
    print(f"   {'摩擦 μ':>8} {'vx の減り':>12} {'÷ 経過秒':>12} {'μ × g':>12} "
          f"{'実測 ÷ μg':>12}")
    for r in rows["a"]:
        mu = r["friction"]
        if r["stop_frame"] or abs(r.get("vx_mean", 0)) < 0.05:
            continue  # 途中で止まったものは平均に止まった時間が混ざる
        drop = r["v0"] - r.get("vx_mean", 0)
        acc = drop / t
        want = mu * G
        got = acc / want if want else float("nan")
        print(f"   {mu:>8} {drop:>12.6f} {acc:>12.6f} {want:>12.6f} "
              f"{got:>12.6f}")

    print("\nC. 粘着を変える（摩擦は 0.25 に固定）")
    print(f"   {'粘着':>8} {'滑った距離':>12} {'最後の vx':>12} {'高さ':>10} "
          f"{'横の広がり':>10}")
    for r in rows["c"]:
        print(f"   {r['sticky']:>8} {r['slid']:>12.6f} "
              f"{r.get('vx_mean', 0):>12.6f} {r['y_mean']:>10.6f} "
              f"{r['x_spread']:>10.6f}")

    print("\nD. 初速を変える（摩擦 0.25・粘着 0）。距離は初速の2乗に比例するか")
    print(f"   {'初速':>8} {'滑った距離':>12} {'距離 ÷ 初速²':>14} {'式の距離':>12} "
          f"{'実測 ÷ 式':>12}")
    for r in rows["d"]:
        want = r["v0"] ** 2 / (2 * r["friction"] * G)
        print(f"   {r['v0']:>8} {r['slid']:>12.6f} "
              f"{r['slid'] / r['v0'] ** 2:>14.6f} {want:>12.6f} "
              f"{r['slid'] / want:>12.6f}")

    print("\nE. 落として跳ねさせる（摩擦 0.25）。粘着は跳ね返りを止めるか")
    print(f"   {'粘着':>8} {'いちばん低い高さ':>16} {'戻った高さ':>12} "
          f"{'粘着0との比':>12} {'40frameの高さ':>14}")
    base = rows["e"][0]["rebound"]
    for r in rows["e"]:
        print(f"   {r['sticky']:>8} {r['y_low']:>16.6f} {r['rebound']:>12.6f} "
              f"{r['rebound'] / base:>12.6f} {r['y_last']:>14.6f}")

    with open(os.path.join(OUT, "067_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("\n保存: out/067_stats.json")


def shot(case):
    """通った跡を1枚に重ねる。"""
    import hou
    import hou_tools
    friction = 0.1 if case == "slip" else 2.0
    geo, solver = build(friction)

    trail = hou.Geometry()
    trail.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    for frame in range(1, LAST + 1, 2):
        hou.setFrame(frame)
        src = solver.geometry()
        u = (frame - 1) / float(LAST - 1)
        col = (0.15 + 0.75 * u, 0.25 + 0.45 * u, 0.55 + 0.35 * u)
        for p in src.points():
            q = trail.createPoint()
            q.setPosition(p.position())
            q.setAttribValue("Cd", col)

    bgeo = os.path.join(OUT, f"067_{case}_trail.bgeo.sc")
    trail.saveToFile(bgeo)

    hou.hipFile.clear(suppress_save_prompt=True)
    show = hou.node("/obj").createNode("geo", "trail")
    fnode = show.createNode("file", "trail")
    fnode.parm("file").set(bgeo)
    fnode.setDisplayFlag(True)
    fnode.setRenderFlag(True)
    bbox = hou.BoundingBox(-0.8, -0.15, -1.0, 6.4, 1.35, 1.0)
    png = os.path.join(OUT, f"067_{case}.png")
    hou_tools.render_preview(fnode.path(), png, res=(760, 260),
                             direction=(0.0, 0.10, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    print(f"保存: out/067_{case}.png")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    if arg == "a":
        part("a", [{"friction": f} for f in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0)],
             "A. 摩擦を変える", HEAD)
    elif arg == "c":
        part("c", [{"friction": 0.25, "sticky": s}
                   for s in (0.0, 0.25, 0.5, 1.0)],
             "C. 粘着を変える（摩擦 0.25）", HEAD)
    elif arg == "d":
        part("d", [{"friction": 0.25, "v0": v} for v in (2.0, 3.0, 4.0)],
             "D. 初速を変える（摩擦 0.25）", HEAD)
    elif arg == "e":
        print("E. 落として跳ねさせる（摩擦 0.25）。粘着は跳ね返りを止めるか")
        print(f"   {'粘着':>8} {'いちばん低い高さ':>16} {'その frame':>10} "
              f"{'戻った高さ':>12} {'40frameの高さ':>14} {'横の広がり':>12}")
        rows = []
        import json as _json
        for s in (0.0, 0.25, 0.5, 1.0):
            r = bounce(0.25, s)
            rows.append(r)
            print(f"   {s:>8} {r['y_low']:>16.6f} {r['low_frame']:>10} "
                  f"{r['rebound']:>12.6f} {r['y_last']:>14.6f} "
                  f"{r['x_spread']:>12.6f}")
        with open(os.path.join(OUT, "067_e.json"), "w",
                  encoding="utf-8") as fp:
            _json.dump(rows, fp, ensure_ascii=False, indent=2)
        print("\n保存: out/067_e.json")
    elif arg == "merge":
        merge()
    elif arg == "shot":
        shot(sys.argv[2])
