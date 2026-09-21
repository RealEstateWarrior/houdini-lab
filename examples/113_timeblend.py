# -*- coding: utf-8 -*-
"""実験113 — timeblend は、フレームの間をどうつなぐのか。

点を1つ、高さ y = F²（F はフレーム番号）で動かす。
timeblend は整数フレームの形しか見ないはずなので、1.5 フレームでは
  直線でつなぐなら (1² + 2²)/2 = 2.5（本当の値は 2.25）
になる。速度 v を持たせて Use Velocity When Interpolating Position を入れると、
速度を使ったなめらかなつなぎ方（3次のエルミート補間なら2次式は誤差0）になるはず。
v は1秒あたりの速さなので、dy/dt = 2F × 24（fps）を入れる。

    hython examples/113_timeblend.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

FRAMES = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.3, 3.9]


def main():
    import hou
    geo = sop_bench.fresh()
    fps = hou.fps()
    wr = geo.createNode("attribwrangle", "mover")
    wr.parm("class").set(0)
    wr.parm("snippet").set(
        'float f = @Frame;\n'
        'int p = addpoint(0, set(0, f * f, 0));\n'
        'setpointattrib(0, "v", p, set(0, 2 * f * %g, 0));\n'
        'setpointattrib(0, "id", p, 0);\n' % fps)
    plain = geo.createNode("timeblend::2.0", "blend")
    plain.setInput(0, wr)
    plain.parm("holdfirst").set(False)
    withv = geo.createNode("timeblend::2.0", "blend_v")
    withv.setInput(0, wr)
    withv.parm("holdfirst").set(False)
    withv.parm("usevforpinterp").set(True)

    # わざと v を「1フレームあたり」で入れた版（fps を掛け忘れた場合）
    wr2 = geo.createNode("attribwrangle", "mover_perframe")
    wr2.parm("class").set(0)
    wr2.parm("snippet").set(
        'float f = @Frame;\n'
        'int p = addpoint(0, set(0, f * f, 0));\n'
        'setpointattrib(0, "v", p, set(0, 2 * f, 0));\n'
        'setpointattrib(0, "id", p, 0);\n')
    wrongv = geo.createNode("timeblend::2.0", "blend_wrongv")
    wrongv.setInput(0, wr2)
    wrongv.parm("holdfirst").set(False)
    wrongv.parm("usevforpinterp").set(True)

    rows = []
    for f in FRAMES:
        hou.setFrame(f)
        direct = wr.geometry().points()[0].position()[1]
        a = plain.geometry().points()[0].position()[1]
        b = withv.geometry().points()[0].position()[1]
        lo, hi = int(f // 1), int(f // 1) + 1
        u = f - lo
        linear = (1 - u) * lo * lo + u * hi * hi
        rows.append({"frame": f, "direct": round(direct, 6), "true": round(f * f, 6),
                     "blend": round(a, 6), "linear": round(linear, 6),
                     "blend_v": round(b, 6),
                     "blend_wrongv": round(wrongv.geometry().points()[0].position()[1], 6)})
        print(rows[-1])
    path = os.path.join(sop_bench.OUT, "113_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"fps": fps, "rows": rows}, fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
