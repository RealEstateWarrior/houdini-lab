"""実験073 — 液体は、どこまで摩擦を上げると暴れ出すか。

<a href="#exp068">実験068</a>で、Liquid を摩擦 1.0 の地面で滑らせたら計算が暴れた。
高さの平均は 0.05 前後で止まっているのに、いちばん高い粒だけが 3.8 まで上がり続けた。
摩擦 0.25 では暴れなかった。<strong>境目はこの間のどこかにある。</strong>

「暴れた」の判定は068と同じ考え方で、平均と最大を両方見る。

    高さの平均が 0.2 未満（液は地面に広がっている）なのに、
    いちばん高い粒が 1.0 を超えている  →  暴れた

  A. 摩擦を 0.25〜1.0 で振って、暴れるかどうかを見る
  B. 120フレームまで回して、暴れ始めるフレームを見る
  C. 摩擦 1.0 のまま substep を増やすと、暴れは収まるか
  D. 摩擦 0.25 で substep を増やし、120フレームまで回す

組み方は実験068と同じ（1辺 1.0 の箱を初速 4 で地面に滑らせる。組み込みの地面を使う）。

    hython examples/073_mpm_liquid_wild.py a
    hython examples/073_mpm_liquid_wild.py b
    hython examples/073_mpm_liquid_wild.py c
    hython examples/073_mpm_liquid_wild.py shot
"""

import importlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

exp068 = importlib.import_module("068_mpm_material")
LAST = 60
CHECK = (10, 20, 25, 30, 40, 50, 60)


def build(friction, substeps=None):
    import hou
    geo, solver = exp068.build("liquid", friction)
    hou.playbar.setFrameRange(1, LAST)
    if substeps is not None:
        solver.parm("doglobalsubsteps").set(1)
        solver.parm("globalsubsteps").set(substeps)
    return geo, solver


def stats_of(node):
    import numpy
    pts = numpy.asarray([p.position() for p in node.geometry().points()], dtype=float)
    ys = pts[:, 1]
    return {"count": int(len(pts)), "y_mean": float(ys.mean()), "y_top": float(ys.max()),
            "above_05": int((ys > 0.5).sum()), "x_mean": float(pts[:, 0].mean())}


def run(friction, substeps=None, last=LAST):
    import hou
    geo, solver = build(friction, substeps)
    hou.playbar.setFrameRange(1, last)
    rows = []
    onset = None
    start = time.perf_counter()
    for frame in range(1, last + 1):
        hou.setFrame(frame)
        solver.geometry()
        if frame in CHECK or frame % 20 == 0 or onset is None:
            s = stats_of(solver)
            if onset is None and frame > 5 and s["y_top"] > 1.0:
                onset = frame
            if frame in CHECK or frame % 20 == 0:
                s["frame"] = frame
                rows.append(s)
    seconds = time.perf_counter() - start
    last = rows[-1]
    wild = last["y_mean"] < 0.2 and last["y_top"] > 1.0
    return {"friction": friction, "substeps": substeps, "wild": wild, "onset": onset,
            "last": last,
            "y_mean": last["y_mean"], "y_top": last["y_top"],
            "above_05": last["above_05"], "count": last["count"],
            "x_mean": last["x_mean"], "seconds": seconds, "frames": rows,
            "default_substeps": solver.parm("globalsubsteps").eval()}


def show(info):
    tops = " → ".join(f"{r['y_top']:.3f}" for r in info["frames"])
    print(f"   摩擦 {info['friction']:<6} substep {str(info['substeps'] or '既定'):>4} | "
          f"{'暴れた' if info['wild'] else '静か  '} 始まり F{info.get('onset')} | 平均 {info['y_mean']:.4f} "
          f"最大 {info['y_top']:.4f}（0.5 より上 {info['above_05']}粒 / {info['count']}） | "
          f"最大の推移 {tops} | {info['seconds']:.2f}秒")


def save(name, rows):
    with open(os.path.join(OUT, f"073_{name}.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print(f"保存: out/073_{name}.json")


def part_a():
    print("A. 摩擦を振る（Liquid・初速 4・60フレーム）")
    rows = []
    for mu in (0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.5):
        info = run(mu)
        rows.append(info)
        show(info)
    print("   既定の substep:", rows[0]["default_substeps"])
    save("a", rows)


def part_b():
    print("B. 120フレームまで回して、暴れ始めるフレームを見る（既定の substep）")
    rows = []
    for mu in (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
        info = run(mu, last=120)
        rows.append(info)
        show(info)
    save("b", rows)


def part_d():
    print("D. 摩擦 0.25 で substep を変えて、120フレームまで回す")
    rows = []
    for sub in (1, 8, 16):
        info = run(0.25, sub, last=120)
        rows.append(info)
        show(info)
    save("d", rows)


def part_c():
    print("C. 摩擦 1.0 のまま substep を変える")
    rows = []
    for sub in (1, 2, 4, 8):
        info = run(1.0, sub)
        rows.append(info)
        show(info)
    save("c", rows)


def shot():
    """摩擦 1.0 の最後のフレームを横から撮る。飛び上がった粒が見えるように。"""
    import hou
    import hou_tools
    geo, solver = build(1.0)
    hou.setFrame(LAST)
    bbox = solver.geometry().boundingBox()      # 飛んだ粒まで入れる
    png = os.path.join(OUT, "073_wild.png")
    hou_tools.render_preview(solver.path(), png, res=(560, 480),
                             direction=(0.0, 0.15, 1.0), shading="smooth",
                             frame_bbox=bbox, margin=1.03)
    hou_tools.save_hip(os.path.join(OUT, "073_liquid.hipnc"))
    print("保存: out/073_wild.png, out/073_liquid.hipnc")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    {"a": part_a, "b": part_b, "c": part_c, "d": part_d, "shot": shot}[arg]()
