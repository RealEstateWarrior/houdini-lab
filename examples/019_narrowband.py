"""粒の数が水位に反応しなかった理由を確かめる。

水位を −1.0 から 1.0 まで動かして水の体積を5倍にしても、粒の数は約19,500でほぼ一定だった。

ヘルプに narrow band の説明がある。
「既定では、ある厚みの水の層しか見えない。narrow band は計算を速くしメモリを減らす方法で、
　水位より下の水はボリュームと場で表される」

つまり<粒は水面付近の帯にしか置かれていない>。だから深さを変えても粒の数が変わらない。

仮説: donarrowband を切れば、粒は水全体に置かれ、数は体積に比例するはず。
否定できる形: 切っても数が変わらなければ、narrow band は原因ではない。
"""

import os
import sys

import hou

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")

SEP = 0.08
BOX = 3.0
HEIGHTS = [-1.0, -0.5, 0.0, 0.5, 1.0]


def count_at(waterline, narrowband, reseeding=True):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "flip")
    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)
    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    solver.parm("dowaterline").set(True)
    solver.parm("waterline").set(waterline)
    solver.parm("donarrowband").set(narrowband)
    solver.parm("doreseeding").set(reseeding)
    for channel in range(3):
        solver.setInput(channel, container, channel)
    hou.setFrame(1)
    g = solver.geometry(0)
    return 0 if g is None else len(g.points())


print(f"{'水位':>7} {'水の体積':>10} {'帯あり':>9} {'帯なし':>9} "
      f"{'帯なし/体積':>12} {'粒1つ分/sep³':>14}")
ideal = SEP ** 3
rows = []
for height in HEIGHTS:
    volume = BOX * BOX * (height + BOX / 2.0)
    on = count_at(height, True)
    off = count_at(height, False)
    per = off / volume
    rows.append((height, volume, on, off, per))
    print(f"{height:7.2f} {volume:10.4f} {on:9d} {off:9d} {per:12.2f} "
          f"{(volume / off) / ideal if off else 0:14.4f}")

print("\n帯なしのときの「体積あたりの粒の数」のばらつき")
pers = [r[4] for r in rows]
print(f"  最小 {min(pers):.2f} / 最大 {max(pers):.2f} / "
      f"幅 {100.0 * (max(pers) - min(pers)) / (sum(pers) / len(pers)):.2f}%")

print("\n帯ありのときの同じ指標（比較用）")
pers_on = [r[2] / r[1] for r in rows]
print(f"  最小 {min(pers_on):.2f} / 最大 {max(pers_on):.2f} / "
      f"幅 {100.0 * (max(pers_on) - min(pers_on)) / (sum(pers_on) / len(pers_on)):.2f}%")

print("\nreseeding の効果（水位0.0、帯なし、40フレーム）")
for reseeding in (True, False):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "flip")
    container = geo.createNode("flipcontainer", "container")
    container.parmTuple("size").set((BOX, BOX, BOX))
    container.parm("particlesep").set(SEP)
    solver = geo.createNode("flipsolver", "solver")
    solver.parm("particlesep").set(SEP)
    solver.parm("dowaterline").set(True)
    solver.parm("donarrowband").set(False)
    solver.parm("doreseeding").set(reseeding)
    for channel in range(3):
        solver.setInput(channel, container, channel)
    counts = []
    for frame in (1, 5, 10, 20, 30, 40):
        hou.setFrame(frame)
        g = solver.geometry(0)
        counts.append(0 if g is None else len(g.points()))
    spread = max(counts) - min(counts)
    print(f"  reseeding {'あり' if reseeding else 'なし'}: "
          + " ".join(f"F{f}:{c}" for f, c in zip((1, 5, 10, 20, 30, 40), counts))
          + f"  幅 {spread} ({100.0 * spread / counts[0]:.2f}%)")
