# -*- coding: utf-8 -*-
"""実験139 — attribblur のぼかしは、どんな計算を何回くり返しているのか。

401点の線（間隔 0.01）に、段差の値（x < 0 で 0、x ≥ 0 で 1）を入れて attribblur にかける。
1回のぼかしが「となり2点の平均へ、Step Size の割合だけ近づける」なら
    v ← v + s·((左 + 右)/2 − v)
これを Python でも同じ回数くり返して、1点ずつ比べる。
また、回数 N で段差のぼけ幅（標準偏差）は √(s·N/1) 点ぶん…ではなく、1回で分散が s/… ずつ増えるので、
ぼけ幅が回数の平方根で広がるかも見る。

    hython examples/139_attribblur.py
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))

import sop_bench  # noqa: E402

N_PTS = 401
STEP = 0.5


def simulate(vals, iters, s, pin=True):
    v = list(vals)
    for _ in range(iters):
        nxt = list(v)
        for i in range(1, len(v) - 1):
            nxt[i] = v[i] + s * ((v[i - 1] + v[i + 1]) / 2 - v[i])
        if not pin:
            nxt[0] = v[0] + s * (v[1] - v[0])
            nxt[-1] = v[-1] + s * (v[-2] - v[-1])
        v = nxt
    return v


def width(vals, dx):
    """段差の傾き（隣との差）を分布とみなして、その標準偏差を出す。"""
    d = [max(0.0, vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
    tot = sum(d)
    xs = [(i + 0.5) * dx for i in range(len(d))]
    m = sum(x * w for x, w in zip(xs, d)) / tot
    return math.sqrt(sum((x - m) ** 2 * w for x, w in zip(xs, d)) / tot)


def main():
    geo = sop_bench.fresh()
    line = geo.createNode("line", "l")
    line.parmTuple("origin").set((-2.0, 0.0, 0.0))
    line.parmTuple("dir").set((1.0, 0.0, 0.0))
    line.parm("dist").set(4.0)
    line.parm("points").set(N_PTS)
    step = geo.createNode("attribwrangle", "step")
    step.setInput(0, line)
    step.parm("snippet").set("f@v = @P.x >= -1e-6 ? 1.0 : 0.0;")
    start = list(step.geometry().pointFloatAttribValues("v"))
    # 既定（Pin Border 入）では線の点が全部「縁」とみなされて動かなかった。その記録を残す
    pinned = geo.createNode("attribblur", "pinned")
    pinned.setInput(0, step)
    pinned.parm("attributes").set("v")
    pinned.parm("iterations").set(100)
    pinned_changed = sum(1 for a, b in zip(start, pinned.geometry().pointFloatAttribValues("v"))
                         if abs(a - b) > 1e-9)
    print("Pin Border 入で値が変わった点:", pinned_changed)
    rows = []
    for iters in (1, 10, 100, 1000):
        bl = geo.createNode("attribblur", f"b{iters}")
        bl.setInput(0, step)
        bl.parm("attributes").set("v")
        bl.parm("iterations").set(iters)
        bl.parm("stepsize").set(STEP)
        bl.parm("pinborder").set(False)
        t0 = time.perf_counter()
        got = list(bl.geometry().pointFloatAttribValues("v"))
        sec = time.perf_counter() - t0
        want = simulate(start, iters, STEP)
        err = max(abs(a - b) for a, b in zip(got, want))
        # 1回の中で2度（奇数・偶数の段）ぼかしているなら、こちらと合うはず
        want2 = simulate(start, 2 * iters, STEP, pin=False)
        err2 = max(abs(a - b) for a, b in zip(got, want2))
        rows.append({"iters": iters, "max_err_vs_rule": round(err, 7),
                     "max_err_vs_2pass": round(err2, 7),
                     "width_pts": round(width(got, 1.0), 4),
                     "width_rule": round(width(want, 1.0), 4),
                     # 1回で、となりへ s/2 ずつ配る → 分散は1回あたり s（点の間隔²）増える
                     "sqrt_rule": round(math.sqrt(STEP * iters), 4),
                     "sec": round(sec, 4),
                     "profile": [round(x, 5) for x in got[150:251:5]]})
        print({k: v for k, v in rows[-1].items() if k != "profile"})
    path = os.path.join(sop_bench.OUT, "139_stats.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"step": STEP, "pinned_changed": pinned_changed, "rows": rows},
                  fp, ensure_ascii=False, indent=1)
    print("書いた:", path)


if __name__ == "__main__":
    main()
