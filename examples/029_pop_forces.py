"""実験029 — 粒に力をかける。風は「押す」のではなく「追いつかせる」。

実験020では粒を落としただけだった。今回は横から力をかける。

POP の力のノードは67種あるが、入口になるのは2つ。

  <code>popforce</code> … 決まった向きに押し続ける。重力と同じ考え方
  <code>popwind</code>  … 指定した速さに<strong>近づけていく</strong>。空気抵抗の考え方

名前は似ているが中身は違うはずである。押し続ければ速さは増え続け、
近づけるなら風速で頭打ちになる。<strong>どちらなのかを、速さの数字で決める。</strong>

最初の見立ては外れた。空気抵抗といえば速さに比例する抵抗（線形抵抗）だと思い、

    v(t) = 風速 × (1 − e^(−airresist × t))        ← 線形抵抗（外れた）

を予測した。この式なら t = 1/airresist のとき必ず 63.2% になる。
測ったら 75.00% で、しかも airresist を変えても 75.00% のまま動かない。
式が違う。風速を 1・3・6 と変えて測り直し、正しい式を決めた。

    dv/dt = airresist × (風速 − v)²               ← 二乗抵抗（合った）
    v(t)  = 風速 × (風速·a·t) / (風速·a·t + 1)

さらに <code>popaxisforce</code>（渦）も試す。これは最初まったく動かなかった。

    hython examples/029_pop_forces.py
    hython examples/029_pop_forces.py shot wind
"""

import json
import math
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

import hou_tools  # noqa: E402

FPS = 24.0
LAST = 72
TARGET = 3.0            # 風速。x 方向
SAMPLES = (2, 5, 10, 17, 25, 37, 49, 61, 72)


def build(kind, target=TARGET, airresist=1.0, orbitspeed=2.0,
          axis_region=True, last=LAST):
    """1フレーム目だけ粒を出し、あとは力だけで動かす。

    全部の粒が同い年になるので、速さを時間の関数として素直に読める。
    """
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, last)
    geo = hou.node("/obj").createNode("geo", "forces")

    emitter = geo.createNode("grid", "emitter")
    emitter.parmTuple("size").set((1.0, 1.0))
    emitter.parm("rows").set(12)
    emitter.parm("cols").set(12)
    emitter.parmTuple("t").set((0.0, 3.0, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")

    source.parm("soppath").set(emitter.path())
    # 1フレーム目だけ出す。式にしないと毎フレーム出続ける。
    source.parm("constantactivate").setExpression("$FF < 2")
    source.parm("constantrate").set(3456.0)     # 144点 × 24fps
    source.parm("impulseactiveate").set(False)
    source.parm("impulserate").set(0.0)
    # 初速をゼロにする。力の効き方だけを見たい。
    for name in ("velocity1", "velocity2", "velocity3",
                 "varianceamount1", "varianceamount2", "varianceamount3"):
        parm = source.parm(name)
        if parm is not None:
            parm.set(0.0)

    if kind == "force":
        node = dop.createNode("popforce", "push")
        node.parmTuple("force").set((target, 0.0, 0.0))
    elif kind == "wind":
        node = dop.createNode("popwind", "wind")
        node.parmTuple("wind").set((target, 0.0, 0.0))
        node.parm("windspeed").set(1.0)
        node.parm("airresist").set(airresist)
    elif kind == "axis":
        node = dop.createNode("popaxisforce", "vortex")
        node.parmTuple("dir").set((0.0, 1.0, 0.0))
        node.parm("orbitspeed").set(orbitspeed)
        node.parm("airresist").set(airresist)
        if axis_region:
            # 既定は原点を中心とした半径1の球。粒は y=3 にいるので範囲の外。
            node.parmTuple("t").set((0.0, 3.0, 0.0))
            node.parm("r").set(5.0)
            node.parm("height").set(5.0)
    else:
        raise ValueError(kind)

    solver.setInput(0, obj)
    solver.setInput(1, source)
    solver.setInput(2, node)
    solver.setDisplayFlag(True)

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")       # 空にすると何も読めない
    imp.setDisplayFlag(True)
    imp.setRenderFlag(True)
    geo.layoutChildren()
    return geo, imp, node


def read(imp, frame):
    hou.setFrame(frame)
    geometry = imp.geometry()
    if geometry is None:
        return None
    points = geometry.points()
    if not points:
        return {"count": 0}
    vs = [p.attribValue("v") for p in points]
    ps = [p.position() for p in points]
    return {
        "count": len(points),
        "vx": sum(v[0] for v in vs) / len(vs),
        "x": sum(p[0] for p in ps) / len(ps),
        "points": ps,
        "vels": vs,
    }


def swirl(row):
    """Y軸まわりの接線速度と半径。正なら、上から見て反時計回り。"""
    tangential, radii = [], []
    for position, velocity in zip(row["points"], row["vels"]):
        x, z = position[0], position[2]
        radius = math.hypot(x, z)
        radii.append(radius)
        if radius < 1e-6:
            continue
        tangential.append((-z * velocity[0] + x * velocity[2]) / radius)
    return {
        "tangential": sum(tangential) / len(tangential) if tangential else 0.0,
        "radius": sum(radii) / len(radii) if radii else 0.0,
    }


def sweep(kind, **kwargs):
    geo, imp, node = build(kind, **kwargs)
    rows = []
    for frame in SAMPLES:
        row = read(imp, frame)
        if not row or row["count"] == 0:
            continue
        entry = {"frame": frame, "seconds": (frame - 1) / FPS,
                 "count": row["count"], "vx": row["vx"], "x": row["x"]}
        if kind == "axis":
            entry.update(swirl(row))
        rows.append(entry)
    return geo, imp, rows


def linear_model(target, airresist, seconds):
    """線形抵抗（最初の見立て）。dv/dt = a(W − v)"""
    return target * (1.0 - math.exp(-airresist * seconds))


def square_model(target, airresist, seconds):
    """二乗抵抗。dv/dt = a(W − v)²"""
    s = target * airresist * seconds
    return target * s / (s + 1.0)


def main():
    stats = {"fps": FPS, "target": TARGET, "last": LAST}

    print("1. popforce（押し続ける）と popwind（追いつかせる）")
    print(f"   どちらも x 方向に {TARGET}")
    _, _, push = sweep("force")
    _, _, wind = sweep("wind", airresist=1.0)
    print(f"{'経過秒':>8} {'popforce の vx':>16} {'速さ÷時間':>12} "
          f"{'popwind の vx':>16} {'風速に対する割合':>16}")
    for a, b in zip(push, wind):
        ratio = a["vx"] / a["seconds"] if a["seconds"] else float("nan")
        print(f"{a['seconds']:8.4f} {a['vx']:16.4f} {ratio:12.4f} "
              f"{b['vx']:16.4f} {b['vx'] / TARGET * 100:15.2f}%")
    stats["force"] = push
    stats["wind"] = wind

    accel = [a["vx"] / a["seconds"] for a in push if a["seconds"]]
    constant_accel = max(accel) - min(accel) < 1e-6
    capped = wind[-1]["vx"] <= TARGET * 1.001
    print(f"\n   popforce は一定の加速度か（速さ÷時間が同じ）: "
          f"{'はい' if constant_accel else 'いいえ'} "
          f"（{min(accel):.4f}〜{max(accel):.4f}）")
    print(f"   popwind は風速を超えなかったか: {'はい' if capped else 'いいえ'}")
    stats["force_constant_accel"] = constant_accel
    stats["force_accel"] = [min(accel), max(accel)]
    stats["wind_capped"] = capped

    print("\n2. popwind の式を決める。風速を変えて2つの式と比べる")
    print("   線形抵抗 v = W(1 − e^(−a t))   /   二乗抵抗 v = W·(Wat)/(Wat + 1)")
    laws = []
    for target in (1.0, 3.0, 6.0):
        _, imp, _ = sweep("wind", target=target, airresist=1.0)
        print(f"   風速 {target}")
        for row in _rows_at(imp, (2, 5, 10, 25, 49)):
            seconds = row["seconds"]
            lin = linear_model(target, 1.0, seconds)
            sqr = square_model(target, 1.0, seconds)
            laws.append({"target": target, "frame": row["frame"],
                         "seconds": seconds, "measured": row["vx"],
                         "linear": lin, "square": sqr})
            print(f"     F{row['frame']:3d} t={seconds:.4f} "
                  f"実測 {row['vx']:8.4f} / 線形 {lin:8.4f} "
                  f"(差 {row['vx'] - lin:+8.4f}) / 二乗 {sqr:8.4f} "
                  f"(差 {row['vx'] - sqr:+8.4f})")
    stats["laws"] = laws
    lin_gap = max(abs(r["measured"] - r["linear"]) for r in laws)
    sqr_gap = max(abs(r["measured"] - r["square"]) for r in laws)
    print(f"\n   線形抵抗との最大のずれ: {lin_gap:.6f}")
    print(f"   二乗抵抗との最大のずれ: {sqr_gap:.6f}")
    stats["linear_gap"] = lin_gap
    stats["square_gap"] = sqr_gap

    print("\n3. 二乗抵抗なら、t = 1/(airresist × 風速) でちょうど 50% になる")
    checks = []
    for airresist, target in ((1.0, 1.0), (1.0, 6.0), (2.0, 3.0), (4.0, 3.0)):
        _, imp, _ = sweep("wind", target=target, airresist=airresist)
        seconds = 1.0 / (airresist * target)
        frame = int(round(1 + seconds * FPS))
        row = read(imp, frame)
        actual_seconds = (frame - 1) / FPS
        ratio = row["vx"] / target * 100
        expected = square_model(target, airresist, actual_seconds) / target * 100
        checks.append({"airresist": airresist, "target": target,
                       "frame": frame, "ratio": ratio, "expected": expected})
        print(f"   airresist {airresist} 風速 {target} → F{frame} で "
              f"{ratio:6.2f}%（式 {expected:6.2f}%）")
    stats["half_checks"] = checks
    worst = max(abs(c["ratio"] - c["expected"]) for c in checks)
    print(f"   最大のずれ: {worst:.2f} ポイント")
    stats["half_worst"] = worst

    print("\n4. popaxisforce（渦）。既定の範囲は原点の半径1の球")
    _, _, outside = sweep("axis", axis_region=False)
    print(f"   範囲の外に粒を置いたとき（既定のまま）: "
          f"接線速度 {outside[-1]['tangential']:.4f} / "
          f"平均半径 {outside[-1]['radius']:.4f}")
    geo, imp, axis = sweep("axis", axis_region=True)
    print(f"{'経過秒':>8} {'接線速度':>12} {'平均半径':>12}")
    for row in axis:
        print(f"{row['seconds']:8.4f} {row['tangential']:12.4f} "
              f"{row['radius']:12.4f}")
    stats["axis_outside"] = outside
    stats["axis"] = axis
    stats["axis_ccw"] = axis[-1]["tangential"] > 0
    stats["axis_spreads"] = axis[-1]["radius"] > axis[0]["radius"]
    print(f"\n   範囲の外では動いたか: "
          f"{'はい' if abs(outside[-1]['tangential']) > 1e-6 else 'いいえ'}")
    print(f"   上から見て反時計回りか: "
          f"{'はい' if stats['axis_ccw'] else 'いいえ（時計回り）'}")
    print(f"   外へ広がったか: {'はい' if stats['axis_spreads'] else 'いいえ'}"
          f"（{axis[0]['radius']:.4f} → {axis[-1]['radius']:.4f}）")

    with open(os.path.join(OUT, "029_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "029_graph.json"),
                          title="実験029 — 粒に力をかける")
    hou_tools.save_hip(os.path.join(OUT, "029_forces.hipnc"))
    print("\n保存: out/029_stats.json, out/029_graph.json, out/029_forces.hipnc")


def _rows_at(imp, frames):
    rows = []
    for frame in frames:
        row = read(imp, frame)
        if row and row["count"]:
            rows.append({"frame": frame, "seconds": (frame - 1) / FPS,
                         "vx": row["vx"]})
    return rows


BBOX_PATH = os.path.join(OUT, "029_bbox.json")


def shot(kind):
    """最終フレームを1枚撮る。レンダはプロセスの最後に1枚だけ。

    粒は点のままだと画に写らないほど小さいので、小さな球を被せて撮る。
    popforce と popwind は同じカメラで撮る（進んだ距離を比べたいため）。
    """
    geo, imp, node = build(kind)
    hou.setFrame(LAST)

    dot = geo.createNode("sphere", "dot")
    dot.parm("type").set(2)
    dot.parmTuple("rad").set((0.06, 0.06, 0.06))
    dot.parm("rows").set(6)
    dot.parm("cols").set(8)

    dots = geo.createNode("copytopoints::2.0", "dots")
    dots.setInput(0, dot)
    dots.setInput(1, imp)
    dots.setDisplayFlag(True)
    dots.setRenderFlag(True)

    shared = kind in ("force", "wind")
    if shared and os.path.exists(BBOX_PATH):
        with open(BBOX_PATH, encoding="utf-8") as fp:
            (x0, y0, z0), (x1, y1, z1) = json.load(fp)
        bbox = hou.BoundingBox(x0, y0, z0, x1, y1, z1)
    else:
        bbox = dots.geometry().boundingBox()
        if shared:
            # 出発点（放出面）も枠に入れる。そうしないと、進みの少ないほうが
            # 枠の外に出てしまい、同じカメラで比べられない。
            bbox.enlargeToContain(hou.BoundingBox(-0.6, 2.4, -0.6, 0.6, 3.6, 0.6))
            with open(BBOX_PATH, "w", encoding="utf-8") as fp:
                json.dump([list(bbox.minvec()), list(bbox.maxvec())], fp)

    png = os.path.join(OUT, f"029_{kind}.png")
    hou_tools.render_preview(dots.path(), png, res=(560, 420), shading="smooth",
                             direction=(0.25, 0.85, 1.0), frame_bbox=bbox,
                             margin=1.1)
    print(f"保存: out/029_{kind}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
