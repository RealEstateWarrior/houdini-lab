"""実験075 — 摩擦の上限は、粒の細かさや substep で動くか。

<a href="#exp071">実験071</a>で、回る台に塊を乗せたとき、滑り出す境目の ω² r が 3.1〜3.7 にしかならなかった。
摩擦 1.0 なら 9.81 のはずで、摩擦が 0.3〜0.4 ぶんしか効いていない。摩擦を 2.0 に上げても変わらなかった。

この上限はどこから来るのか。<strong>計算の粗さから来るなら、細かくすれば上がるはず。</strong>

  A. 粒の間隔 particlesep を 0.18 / 0.12 / 0.08 / 0.06 と変えて、境目を挟み撃ちで探す
  B. particlesep 0.12 のまま、substep を 1 / 4 / 8 と変えて、境目を探す

条件は071の B（半径 2・摩擦 1.0）と同じ。塊の大きさ（1辺 0.6）は変えない。

    hython examples/075_mpm_friction_cap.py a
    hython examples/075_mpm_friction_cap.py b
"""

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

spin = importlib.import_module("071_mpm_spin")
_build = spin.build
SETTINGS = {"substeps": None}


def build(*args, **kwargs):
    geo, solver = _build(*args, **kwargs)
    if SETTINGS["substeps"] is not None:
        solver.parm("doglobalsubsteps").set(1)
        solver.parm("globalsubsteps").set(SETTINGS["substeps"])
    return geo, solver


spin.build = build        # 071の run() がこちらを使うようにする


def edge(label):
    print(f"   {label}")
    row = spin.find_edge(2.0, 1.0, 0.6, 2.2, steps=6)
    tried = row["tried"]
    row["seconds_mean"] = sum(t["seconds"] for t in tried) / len(tried)
    print(f"   → 境目 ω {row['lo']:.4f}〜{row['hi']:.4f}  ω²r = {row['w2r']:.4f}  "
          f"実効の摩擦 {row['mu_eff']:.4f}  1回平均 {row['seconds_mean']:.2f}秒")
    return row


def count_particles(sep):
    import hou
    spin.SEP = sep
    geo, solver = spin.build(1.0)
    hou.setFrame(1)
    return len(solver.geometry().points())


def part_a():
    print("A. 粒の間隔を変えて境目を探す（半径 2・摩擦 1.0・substep 既定）")
    rows = []
    for sep in (0.18, 0.12, 0.08, 0.06):
        n = count_particles(sep)
        spin.SEP = sep
        row = edge(f"particlesep {sep}（塊の粒 {n}）")
        row.update({"sep": sep, "particles": n})
        rows.append(row)
    with open(os.path.join(OUT, "075_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/075_a.json")


def part_b():
    print("B. substep を変えて境目を探す（particlesep 0.12・半径 2・摩擦 1.0）")
    rows = []
    spin.SEP = 0.12
    for sub in (1, 4, 8):
        SETTINGS["substeps"] = sub
        row = edge(f"substep {sub}")
        row.update({"substeps": sub})
        rows.append(row)
    with open(os.path.join(OUT, "075_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/075_b.json")


def part_c():
    print("C. さらに細かく（particlesep 0.04）")
    n = count_particles(0.04)
    spin.SEP = 0.04
    row = edge(f"particlesep 0.04（塊の粒 {n}）")
    row.update({"sep": 0.04, "particles": n})
    with open(os.path.join(OUT, "075_c.json"), "w", encoding="utf-8") as fp:
        json.dump([row], fp, ensure_ascii=False, indent=2)
    print("保存: out/075_c.json")


if __name__ == "__main__":
    {"a": part_a, "b": part_b, "c": part_c}[sys.argv[1] if len(sys.argv) > 1 else "a"]()
