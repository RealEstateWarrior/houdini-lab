"""実験078 — 液体の暴れは、粒の細かさで変わるか。

<a href="#exp073">実験073</a>で、Liquid を摩擦のある地面に置くと、しばらくして数粒だけが飛び始めた
（粒の間隔 0.12 で、摩擦 0.25 は F46、0.5 は F30、1.0 は F28 から）。substep 8 で消えたが、5倍前後かかった。
<a href="#exp075">実験075</a>では、摩擦の上限は substep では動かず、粒の細かさで動いた。
<strong>では液体の暴れはどうか。</strong>

  A. 摩擦 0.5 と 1.0 で、粒の間隔を 0.16 / 0.12 / 0.08 / 0.06 と変え、120フレームまで回す。
     暴れ始めのフレーム（いちばん高い粒が 1.0 を超えた最初のフレーム）と、飛んだ粒の数を見る

値は hou_tools.point_array でまとめて読む（実験077）。

    hython examples/078_liquid_resolution.py
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
LAST = 120


def run(sep, friction):
    import hou
    import hou_tools
    exp068.SEP = sep
    geo, solver = exp068.build("liquid", friction)
    hou.playbar.setFrameRange(1, LAST)
    onset = None
    most = 0
    top_max = 0.0
    cook = 0.0
    trace = []
    empty = []
    y = None
    for frame in range(1, LAST + 1):
        hou.setFrame(frame)
        start = time.perf_counter()
        g = solver.geometry()
        cook += time.perf_counter() - start
        if g is None or len(g.points()) == 0:
            empty.append(frame)
            continue
        y = hou_tools.point_array(g)[:, 1]
        top = float(y.max())
        flying = int((y > 0.5).sum())
        most = max(most, flying)
        top_max = max(top_max, top)
        if onset is None and frame > 5 and top > 1.0:
            onset = frame
        if frame % 10 == 0:
            trace.append({"frame": frame, "top": top, "mean": float(y.mean()), "flying": flying})
    if y is None:
        return {"sep": sep, "friction": friction, "count": 0, "onset": None, "top_max": 0.0,
                "most_flying": 0, "mean_last": 0.0, "cook": cook, "trace": trace,
                "empty": empty, "errors": list(solver.errors())}
    return {"sep": sep, "friction": friction, "count": int(len(y)), "onset": onset, "empty": empty,
            "top_max": top_max, "most_flying": most, "mean_last": float(y.mean()),
            "cook": cook, "trace": trace}


def main():
    rows = []
    for friction in (1.0, 0.5):
        for sep in (0.16, 0.12, 0.08, 0.06):
            r = run(sep, friction)
            rows.append(r)
            print(f"   摩擦 {friction:<4} 間隔 {sep:<5} | {r['count']}粒 | 始まり F{r['onset']} | "
                  f"いちばん高い {r['top_max']:.3f} | 0.5 より上 最大 {r['most_flying']}粒 | "
                  f"最後の平均 {r['mean_last']:.4f} | 計算 {r['cook']:.2f}秒"
                  + (f" | 空のフレーム {len(r['empty'])} {r.get('errors', '')}" if r["empty"] else ""))
    with open(os.path.join(OUT, "078_stats.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/078_stats.json")


if __name__ == "__main__":
    main()
