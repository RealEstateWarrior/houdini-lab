"""実験076 — 粒を細かくすれば、摩擦の式に戻るか。

<a href="#exp067">実験067</a>で、塊を地面に滑らせると、摩擦 0.25 までは式「止まるまでの距離 = v² ÷ (2 μ g)」
に 0.04% で乗ったが、摩擦を上げるほど式より遠くまで滑った（摩擦 1.0 で 1.46倍、2.0 で 2.82倍）。
<a href="#exp070">実験070</a>の動く板でも、強い摩擦ほど式より短くしか運ばれなかった。
どちらも粒の間隔は 0.12 だった。

<a href="#exp075">実験075</a>で、回る台の摩擦の上限は、粒を細かくすると上がると分かった。
<strong>では067・070の「外れ」も、細かくすれば縮むか。</strong>

  A. 067の滑る塊（初速 4）。摩擦 0.25 / 0.5 / 1.0 / 2.0 × 粒の間隔 0.12 / 0.08 / 0.06 / 0.04
  B. 070の動く板（板の速さ 4・摩擦 1.0）。粒の間隔 0.12 / 0.08 / 0.06 / 0.04

    hython examples/076_mpm_fine_friction.py a
    hython examples/076_mpm_fine_friction.py b
"""

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

G = 9.81
SEPS = (0.12, 0.08, 0.06, 0.04)


def part_a():
    ground = importlib.import_module("067_mpm_ground")
    print("A. 滑る塊（初速 4・40フレーム）。実測 ÷ 式")
    rows = []
    for sep in SEPS:
        ground.SEP = sep
        for mu in (0.25, 0.5, 1.0, 2.0):
            info = ground.run(mu)
            want = 16.0 / (2 * mu * G)
            row = {"sep": sep, "friction": mu, "slid": info["slid"], "want": want,
                   "ratio": info["slid"] / want, "stop_sec": info["stop_sec"],
                   "y_mean": info["y_mean"], "count": info["count"],
                   "seconds": info["seconds"]}
            rows.append(row)
            print(f"   間隔 {sep:<5} 摩擦 {mu:<5} | 滑った {row['slid']:.6f} 式 {want:.6f} "
                  f"比 {row['ratio']:.6f} | 止まった {row['stop_sec']} 秒 | 高さ {row['y_mean']:.4f} | "
                  f"{row['count']}粒 {row['seconds']:.2f}秒")
    with open(os.path.join(OUT, "076_a.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/076_a.json")


def part_b():
    moving = importlib.import_module("070_mpm_moving")
    print("B. 動く板（板の速さ 4・摩擦 1.0・40フレーム）。式の距離 5.684506")
    t = (moving.LAST - 1) / moving.FPS
    want = 4.0 * t - 16.0 / (2 * 1.0 * G)
    rows = []
    for sep in SEPS:
        moving.SEP = sep
        info = moving.run(speed=4.0)
        row = {"sep": sep, "carried": info["carried"], "want": want,
               "ratio": info["carried"] / want, "vx": info.get("vx_mean"),
               "y_mean": info["y_mean"], "count": info["count"], "seconds": info["seconds"]}
        rows.append(row)
        print(f"   間隔 {sep:<5} | 運ばれた {row['carried']:.6f} 比 {row['ratio']:.6f} | "
              f"最後の vx {row['vx']:.6f} | 高さ {row['y_mean']:.4f} | {row['count']}粒 {row['seconds']:.2f}秒")
    with open(os.path.join(OUT, "076_b.json"), "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    print("保存: out/076_b.json")


if __name__ == "__main__":
    {"a": part_a, "b": part_b}[sys.argv[1] if len(sys.argv) > 1 else "a"]()
