"""実験077 — 測る処理は、計算の時間にどれだけ乗るか。

<a href="#exp076">実験076</a>で、同じ 15,591粒の MPM が、片方では 4.05秒、もう片方では 20秒かかった。
違いは「毎フレーム、全部の粒の位置を Python で読んでいたかどうか」だけだった。
<strong>測るための処理が、測りたい計算より重くなっていた。</strong>

読み方は何通りもある。どれがどれだけ重いかを測る。

  none    … 読まない（geometry() で計算させるだけ）
  loop    … for p in geo.points(): p.position()        ← これまでの実験のやり方
  loop_v  … 位置と速さ（v）を1粒ずつ読む                    ← 実験067・070のやり方
  bulk    … geo.pointFloatAttribValues("P")          ← 全部を1回で受け取る
  numpy   … numpy.frombuffer(geo.pointFloatAttribValuesAsString("P"))

場面は実験070の動く板（板の速さ 4・摩擦 1.0・40フレーム）。粒の間隔を 0.12 / 0.06 / 0.04 と変える。
読み方ごとに毎回組み直す（前の計算の結果を使い回させないため）。

    hython examples/077_read_cost.py
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

moving = importlib.import_module("070_mpm_moving")
MODES = ("none", "loop", "loop_v", "bulk", "numpy")


def read(geo, mode):
    import numpy
    if mode == "none":
        return 0.0
    if mode == "loop":
        return sum(p.position()[1] for p in geo.points())
    if mode == "loop_v":
        total = 0.0
        for p in geo.points():
            total += p.position()[1] + p.attribValue("v")[0]
        return total
    if mode == "bulk":
        values = geo.pointFloatAttribValues("P")
        return sum(values[1::3])
    if mode == "numpy":
        arr = numpy.frombuffer(geo.pointFloatAttribValuesAsString("P"), dtype=numpy.float32)
        return float(arr.reshape(-1, 3)[:, 1].sum())
    raise ValueError(mode)


def run(sep, mode):
    import hou
    moving.SEP = sep
    geo, solver = moving.build(4.0)
    cook = 0.0
    reading = 0.0
    check = None
    for frame in range(1, moving.LAST + 1):
        hou.setFrame(frame)
        start = time.perf_counter()
        g = solver.geometry()
        mid = time.perf_counter()
        value = read(g, mode)
        end = time.perf_counter()
        cook += mid - start
        reading += end - mid
        check = value
    count = len(solver.geometry().points())
    mean_y = None
    if mode != "none":
        mean_y = (check / count) if mode != "loop_v" else None
    return {"sep": sep, "mode": mode, "count": count, "cook": cook, "read": reading,
            "total": cook + reading, "mean_y": mean_y}


def main():
    rows = []
    for sep in (0.12, 0.06, 0.04):
        for mode in MODES:
            r = run(sep, mode)
            rows.append(r)
            per = r["read"] / moving.LAST * 1000
            print(f"   間隔 {sep:<5} {mode:>7} | {r['count']}粒 | 計算 {r['cook']:.3f}秒 "
                  f"読む {r['read']:.3f}秒（1フレーム {per:.2f}ms） 合計 {r['total']:.3f}秒"
                  + (f" | 最後の高さの平均 {r['mean_y']:.6f}" if r["mean_y"] is not None else ""))
    with open(os.path.join(OUT, "077_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/077_stats.json")


if __name__ == "__main__":
    main()
