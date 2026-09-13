"""落下が式からずれた分の正体を突き止める。

y = y0 − ½ g t² に対して、実測はいつも「まだ落ちていない」側にずれていた。
ずれは齢に比例して増えていたので、速度のずれではなく<時間の原点のずれ>を疑う。

    y = y0 − ½ g (t − δ)²

と置いて δ を逆算すると、どのフレームでも同じ値になるはず。
さらに δ が計算の刻み（substeps）で変わるなら、積分のやり方が原因だと言える。

否定できる形: substeps を8倍にしても δ が変わらなければ、原因は積分ではない。
"""

import json
import math
import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

G = 9.80665
EMIT_Y = 3.0
FRAMES = [10, 20, 30, 40, 50, 60]


def build(substeps=1):
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
    source.parm("constantrate").set(200)
    source.parm("impulseactiveate").set(False)
    force.parmTuple("force").set((0.0, -G, 0.0))

    solver.setInput(0, obj)
    solver.setInput(1, source)
    solver.setInput(2, force)
    solver.setDisplayFlag(True)

    # DOPネットワーク側の刻み
    if dop.parm("substep") is not None:
        dop.parm("substep").set(substeps)

    imp = geo.createNode("dopimport", "import")
    imp.parm("doppath").set(dop.path())
    imp.parm("objpattern").set("*")
    imp.setDisplayFlag(True)
    return imp


def oldest(imp, frame):
    hou.setFrame(frame)
    geo = imp.geometry()
    points = geo.points()
    ages = [p.attribValue("age") for p in points]
    index = max(range(len(points)), key=lambda i: ages[i])
    return ages[index], points[index].position()[1]


def delays(imp):
    out = []
    for frame in FRAMES:
        age, y = oldest(imp, frame)
        drop = EMIT_Y - y
        if drop <= 0:
            continue
        effective = math.sqrt(2.0 * drop / G)     # 実際に落ちていた時間
        out.append({"frame": frame, "age": age, "y": y,
                    "effective_t": effective, "delay": age - effective})
    return out


print("substeps 1 での δ（時間の原点のずれ）")
imp = build(1)
rows = delays(imp)
print(f"{'フレーム':>8} {'齢':>9} {'高さ':>11} {'実際に落ちた時間':>16} {'δ':>9}")
for r in rows:
    print(f"{r['frame']:8d} {r['age']:9.4f} {r['y']:11.5f} "
          f"{r['effective_t']:16.5f} {r['delay']:9.5f}")
ds = [r["delay"] for r in rows]
print(f"  δ = {min(ds):.5f}〜{max(ds):.5f}（幅 "
      f"{100.0 * (max(ds) - min(ds)) / (sum(ds) / len(ds)):.2f}%）")
print(f"  24fps で {sum(ds) / len(ds) * 24.0:.3f} フレーム分")

print("\nδ は計算の刻みで変わるか")
print(f"{'substeps':>9} {'δ の平均':>10} {'1刻みの長さ(秒)':>16} {'δ / 1刻み':>11}")
table = []
for substeps in (1, 2, 4, 8):
    imp = build(substeps)
    rows = delays(imp)
    mean = sum(r["delay"] for r in rows) / len(rows)
    step = 1.0 / 24.0 / substeps
    table.append({"substeps": substeps, "delay": mean, "step": step,
                  "ratio": mean / step})
    print(f"{substeps:9d} {mean:10.5f} {step:16.6f} {mean / step:11.3f}")

with open(os.path.join(OUT, "020_delay.json"), "w", encoding="utf-8") as fp:
    json.dump({"g": G, "emit_y": EMIT_Y, "rows": rows, "substeps": table},
              fp, ensure_ascii=False, indent=2)
print("\n保存: out/020_delay.json")
