"""実験061 — MPM に入る。いちばん小さい落下で、保存量を測る。

MPM（Material Point Method）は Houdini 21 で入った新しいソルバ。
砂・雪・泥・パンのような「固体と流体の中間」を扱える。

新しい分野なので、実験042（グルーム）や実験050（APEX）と同じ順番で入る。
<strong>部品の数を数える・いちばん小さいものを動かす・保たれるはずの量を測る。</strong>

いちばん小さい落下を作る。箱を粒に変えて、重力だけで落とす。
<strong>何かにぶつかるまでは、自由落下の式に乗るはずだ。</strong>

    y = y0 − ½ g t²

  A. MPM の部品は何種類あるか。いちばん小さい構成は何個か
  B. 粒の数はフレーム間で保たれるか
  C. 落ち方は自由落下の式に乗るか
  D. 粒の数と、かかる時間

    hython examples/061_mpm.py
    hython examples/061_mpm.py shot start
    hython examples/061_mpm.py shot fall
"""

import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")
STATS = os.path.join(OUT, "061_stats.json")

RES = (620, 620)
START_Y = 6.0
SEP = 0.08
LAST = 30
FPS = 24.0
GRAVITY = 9.80665


def build(sep=SEP, size=1.0, gravity=-GRAVITY):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.playbar.setFrameRange(1, LAST)
    geo = hou.node("/obj").createNode("geo", "mpm")

    # 落とすもの
    box = geo.createNode("box", "box")
    box.parmTuple("size").set((size, size, size))
    box.parmTuple("t").set((0.0, START_Y, 0.0))

    # 計算する範囲
    container = geo.createNode("mpmcontainer", "container")
    container.parm("particlesep").set(sep)
    container.parm("sizex").set(6.0)
    container.parm("sizey").set(12.0)
    container.parm("sizez").set(6.0)
    container.parm("centery").set(4.0)

    # 箱を粒に変える
    source = geo.createNode("mpmsource", "source")
    source.setInput(0, box)
    source.setInput(1, container)

    solver = geo.createNode("mpmsolver", "solve")
    solver.setInput(0, source)
    solver.setInput(2, container)
    solver.parm("gravityy").set(gravity)
    solver.setDisplayFlag(True)
    solver.setRenderFlag(True)
    geo.layoutChildren()
    return geo, box, container, source, solver


def stats_of(node):
    import numpy
    g = node.geometry()
    if g is None:
        return None
    pts = numpy.asarray([[p.position()[0], p.position()[1],
                          p.position()[2]] for p in g.points()])
    return {"count": int(len(pts)),
            "y_mean": float(pts[:, 1].mean()),
            "y_min": float(pts[:, 1].min()),
            "y_max": float(pts[:, 1].max()),
            "x_spread": float(pts[:, 0].max() - pts[:, 0].min()),
            "z_spread": float(pts[:, 2].max() - pts[:, 2].min())}


def main():
    import hou
    stats = {}

    print("A. MPM の部品と、いちばん小さい構成")
    sops = sorted(hou.sopNodeTypeCategory().nodeTypes().keys())
    mpm_sops = [n for n in sops if n.startswith("mpm")]
    dops = sorted(hou.dopNodeTypeCategory().nodeTypes().keys())
    mpm_dops = [n for n in dops if n.startswith("mpm")]
    print(f"   mpm で始まる SOP: {len(mpm_sops)}種 {mpm_sops}")
    print(f"   mpm で始まる DOP: {len(mpm_dops)}種 {mpm_dops}")
    stats["sops"] = mpm_sops
    stats["dops"] = mpm_dops

    geo, box, container, source, solver = build()
    print(f"   いちばん小さい構成: box → mpmsource → mpmsolver "
          f"（範囲は mpmcontainer）＝ 4ノード")
    print(f"   入力の順番: mpmsolver は 0=源 / 1=ぶつかるもの / 2=範囲")

    hou.setFrame(1)
    first = stats_of(solver)
    print(f"\n   1辺 1.0 の箱（粒の間隔 {SEP}）→ 粒 {first['count']:,}個")
    stats["first"] = first

    print("\nB・C. 落ち方は自由落下の式に乗るか")
    print(f"   {'frame':>6} {'秒':>7} {'粒の数':>8} {'高さの平均':>12} "
          f"{'式の高さ':>12} {'ずれ':>12} {'横の広がり':>12}")
    rows = []
    y0 = first["y_mean"]
    for frame in (1, 3, 5, 7, 9, 11, 13):
        hou.setFrame(frame)
        info = stats_of(solver)
        t = (frame - 1) / FPS
        want = y0 - 0.5 * GRAVITY * t * t
        info.update({"frame": frame, "t": t, "expected": want,
                     "diff": info["y_mean"] - want})
        rows.append(info)
        print(f"   {frame:>6} {t:>7.4f} {info['count']:>8,} "
              f"{info['y_mean']:>12.6f} {want:>12.6f} "
              f"{info['y_mean'] - want:>+12.6f} "
              f"{info['x_spread']:>12.6f}")
    counts = [r["count"] for r in rows]
    same = max(counts) - min(counts)
    worst = max(abs(r["diff"]) for r in rows)
    print(f"\n   粒の数の幅: {same}")
    print(f"   数は保たれたか: {'はい' if same == 0 else 'いいえ'}")
    print(f"   式とのずれの最大: {worst:.6f}")
    print(f"   自由落下の式に乗るか: {'はい' if worst < 0.01 else 'いいえ'}")
    stats["fall"] = rows
    stats["count_spread"] = same
    stats["fall_worst"] = worst

    # ずれが時間に比例しているので、「時刻が少し先に進んでいる」と考えてみる。
    # y = y0 − ½g(t + δ)² の δ を、いちばん遠い点から出して全部に当てる。
    last = rows[-1]
    delta = (math.sqrt(2 * (y0 - last["y_mean"]) / GRAVITY)
             - last["t"])
    print(f"\n   ずれを「時刻の先走り」で説明できるか")
    print(f"   いちばん遠い点から出した δ: {delta:.6f} 秒"
          f"（{delta * FPS:.4f} フレーム）")
    print(f"   {'frame':>6} {'式（δなし）':>14} {'式（δ入り）':>14} "
          f"{'ずれ（δなし）':>14} {'ずれ（δ入り）':>14}")
    fitted = []
    for r in rows:
        t2 = r["t"] + delta
        want2 = y0 - 0.5 * GRAVITY * t2 * t2
        d2 = r["y_mean"] - want2
        fitted.append({"frame": r["frame"], "expected2": want2,
                       "diff2": d2})
        print(f"   {r['frame']:>6} {r['expected']:>14.6f} "
              f"{want2:>14.6f} {r['diff']:>+14.6f} {d2:>+14.6f}")
    worst2 = max(abs(f["diff2"]) for f in fitted)
    print(f"   δ を入れたときのずれの最大: {worst2:.6f}"
          f"（{worst / worst2:.0f}分の1）")
    stats["delta"] = delta
    stats["fitted"] = fitted
    stats["fall_worst_fitted"] = worst2

    print("\nD. 粒の数と、かかる時間")
    print(f"   {'間隔':>8} {'粒の数':>10} {'1フレーム進める時間':>20} "
          f"{'粒1つあたり':>14}")
    speed = []
    # 1回目は準備の分が乗るので、捨てる
    geo, box, container, source, solver = build(sep=0.2)
    hou.setFrame(1)
    solver.geometry()
    hou.setFrame(2)
    solver.geometry()
    for sep in (0.16, 0.12, 0.08, 0.06):
        geo, box, container, source, solver = build(sep=sep)
        hou.setFrame(1)
        count = stats_of(solver)["count"]
        start = time.perf_counter()
        hou.setFrame(2)
        solver.geometry()
        seconds = time.perf_counter() - start
        speed.append({"sep": sep, "count": count, "seconds": seconds,
                      "per_point_us": seconds / count * 1e6})
        print(f"   {sep:>8} {count:>10,} {seconds:>19.3f}秒 "
              f"{seconds / count * 1e6:>13.2f}µs")
    stats["speed"] = speed

    with open(STATS, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, ensure_ascii=False, indent=2)

    import hou_tools
    geo, box, container, source, solver = build()
    hou.setFrame(LAST)
    hou_tools.write_graph(geo.path(), os.path.join(OUT, "061_graph.json"),
                          title="実験061 — MPM に入る")
    hou_tools.save_hip(os.path.join(OUT, "061_mpm.hipnc"))
    print("\n保存: out/061_stats.json, out/061_graph.json, out/061_mpm.hipnc")


def shot(case):
    import hou
    import hou_tools
    geo, box, container, source, solver = build()
    hou.setFrame(1 if case == "start" else 13)
    bbox = hou.BoundingBox(-1.6, -0.2, -1.6, 1.6, 7.0, 1.6)
    png = os.path.join(OUT, f"061_{case}.png")
    hou_tools.render_preview(solver.path(), png, res=RES,
                             direction=(0.3, 0.15, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.04)
    print(f"保存: out/061_{case}.png")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "shot":
        shot(sys.argv[2])
    else:
        main()
