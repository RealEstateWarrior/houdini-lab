"""実験020 — POP パーティクル。生まれる数と落ち方を式で確かめる。

013で「パーティクルはSOPに0種、DOPに67種」と分かってから保留にしていた題材。
SOPだけでは組めず、DOPネットワークを作る必要がある。

配線（019と同じく、総当たりではなく役割から組んだ）
    popobject ──→ popsolver 入力1      粒の入れ物
    popsource ──→ popsolver 入力2      粒を生む部品
    popforce  ──→ popsolver 入力3      力を加える部品
    dopnet ──→ dopimport(SOP)          結果をSOP側へ戻す

測るもの
  A. 生まれる数。毎秒200個と指定したら、1フレームあたり 200/24 = 8.333 個のはず
  B. 落ち方。初速0で落ちる粒の高さは y = y0 − ½ g t² のはず（g = 9.80665）

どちらも式が先にあるので、外れたら分かる。

    hython examples/020_pop_particles.py
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

RATE = 200.0
FPS = 24.0
G = 9.80665
EMIT_Y = 3.0
FRAMES = [1, 2, 5, 10, 20, 30, 40, 50, 60]


def build(rate=RATE, gravity=True):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "pop_test")

    emitter = geo.createNode("grid", "emitter")
    emitter.parmTuple("size").set((1.0, 1.0))
    emitter.parm("rows").set(10)
    emitter.parm("cols").set(10)
    emitter.parmTuple("t").set((0.0, EMIT_Y, 0.0))

    dop = geo.createNode("dopnet", "popnet")
    obj = dop.createNode("popobject", "particles")
    solver = dop.createNode("popsolver", "solver")
    source = dop.createNode("popsource", "source")
    force = dop.createNode("popforce", "gravity")

    source.parm("soppath").set(emitter.path())
    source.parm("constantactivate").set(True)
    source.parm("constantrate").set(rate)
    source.parm("impulseactiveate").set(False)
    source.parm("impulserate").set(0.0)
    force.parmTuple("force").set((0.0, -G if gravity else 0.0, 0.0))

    solver.setInput(0, obj)
    solver.setInput(1, source)
    solver.setInput(2, force)
    solver.setDisplayFlag(True)

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")       # 名前が違うと何も読めない
    imp.setDisplayFlag(True)
    imp.setRenderFlag(True)
    return geo, dop, imp, emitter


def sample(imp, frame):
    hou.setFrame(frame)
    geo = imp.geometry()
    if geo is None:
        return None
    points = geo.points()
    if not points:
        return {"count": 0}
    age_attrib = geo.findPointAttrib("age")
    ys = [p.position()[1] for p in points]
    row = {"count": len(points), "lowest": min(ys), "highest": max(ys)}
    if age_attrib is not None:
        ages = [p.attribValue("age") for p in points]
        oldest = max(range(len(points)), key=lambda i: ages[i])
        row["oldest_age"] = ages[oldest]
        row["oldest_y"] = points[oldest].position()[1]
    return row


def main():
    stats = {"rate": RATE, "fps": FPS, "g": G, "emit_y": EMIT_Y}

    # ---------- A. 生まれる数 ----------
    print("A. 毎秒200個と指定したとき、1フレームあたり何個生まれるか")
    geo, dop, imp, emitter = build()
    rows = []
    print(f"{'フレーム':>8} {'粒の数':>8} {'経過秒':>8} {'式の予測':>9} {'差':>8}")
    for frame in FRAMES:
        row = sample(imp, frame)
        seconds = (frame - 1) / FPS
        predicted = RATE * seconds
        rows.append({"frame": frame, "count": row["count"], "seconds": seconds,
                     "predicted": predicted, "gap": row["count"] - predicted})
        print(f"{frame:8d} {row['count']:8d} {seconds:8.4f} {predicted:9.2f} "
              f"{row['count'] - predicted:+8.2f}")
    stats["birth"] = rows

    # 直線に当てはめて、1秒あたりの本当の数を出す
    n = len(rows)
    sx = sum(r["seconds"] for r in rows)
    sy = sum(r["count"] for r in rows)
    sxx = sum(r["seconds"] ** 2 for r in rows)
    sxy = sum(r["seconds"] * r["count"] for r in rows)
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    intercept = (sy - slope * sx) / n
    print(f"\n  直線に当てはめる: 粒の数 = {slope:.2f} × 秒 {intercept:+.2f}")
    print(f"  指定は毎秒 {RATE:.0f} 個。実測 {slope:.2f} 個 "
          f"（ずれ {100.0 * (slope - RATE) / RATE:+.2f}%）")
    stats["birth_fit"] = {"slope": slope, "intercept": intercept,
                          "gap_pct": 100.0 * (slope - RATE) / RATE}

    # ---------- B. 落ち方 ----------
    print("\nB. 初速0で落ちる粒の高さ（最も古い粒を追う）")
    print(f"{'フレーム':>8} {'最古の齢':>9} {'実測の高さ':>11} {'式の予測':>10} "
          f"{'差':>9} {'ずれ%':>8}")
    fall = []
    for frame in FRAMES:
        row = sample(imp, frame)
        if "oldest_y" not in row:
            print(f"{frame:8d}  age アトリビュートがない")
            continue
        t = row["oldest_age"]
        predicted = EMIT_Y - 0.5 * G * t * t
        drop_measured = EMIT_Y - row["oldest_y"]
        drop_predicted = EMIT_Y - predicted
        gap_pct = (100.0 * (drop_measured - drop_predicted) / drop_predicted
                   if drop_predicted > 1e-9 else 0.0)
        fall.append({"frame": frame, "age": t, "y": row["oldest_y"],
                     "predicted": predicted, "gap": row["oldest_y"] - predicted,
                     "gap_pct": gap_pct})
        print(f"{frame:8d} {t:9.4f} {row['oldest_y']:11.5f} {predicted:10.5f} "
              f"{row['oldest_y'] - predicted:+9.5f} {gap_pct:+8.2f}")
    stats["fall"] = fall

    # 重力なしとの比較。ツマミが効いていることの確認
    print("\n  重力を0にしたときの最も古い粒の高さ（効いていることの確認）")
    _, _, imp0, _ = build(gravity=False)
    for frame in (10, 30, 60):
        row = sample(imp0, frame)
        print(f"    フレーム{frame:3d}: {row.get('oldest_y', float('nan')):.5f}"
              f"（重力ありでは "
              f"{[f['y'] for f in fall if f['frame'] == frame][0]:.5f}）")

    # ---------- 絵 ----------
    print("\n連番を書き出す")
    geo, dop, imp, emitter = build()
    frames = list(range(1, 61, 4))
    bbox = hou.BoundingBox(-1.6, -4.5, -1.6, 1.6, EMIT_Y + 0.4, 1.6)
    paths = hou_tools.render_sequence(imp.path(), OUT, "020_pop", frames,
                                      res=(420, 320), shading="smooth",
                                      frame_bbox=bbox)
    print(f"  {len(paths)} 枚")

    hou_tools.write_graph(dop.path(), os.path.join(OUT, "020_graph.json"),
                          title="実験020 — POP パーティクル（DOPネットワークの中身）")
    hou_tools.save_hip(os.path.join(OUT, "020_pop.hipnc"))
    with open(os.path.join(OUT, "020_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)
    print("保存: out/020_stats.json, out/020_graph.json, out/020_pop.hipnc")


if __name__ == "__main__":
    main()
